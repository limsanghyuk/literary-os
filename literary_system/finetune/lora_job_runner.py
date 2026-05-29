"""
SP-B.1 (V597) — LoRAJobRunner: GPUAdapter 연동 LoRA 학습 작업 실행기

Phase B 본안 보강 D6 / B-M-06:
- GPUAdapterContract (V590) 연동
- 격주 풀 학습($48) / 주간 미세조정($48) 자동 스케줄 판단
- 월 SLO $96 (soft=$90 경보, hard=$120 차단, emergency=$150 즉시 중단)
- 학습 이력 JSONL 영속화

ADR-057 참조.

LLM-0 원칙: 이 모듈은 외부 LLM API를 직접 호출하지 않음.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from literary_system.finetune.gpu_adapter import (
    DEFAULT_COST_SLO,
    CostSLO,
    GPUAdapterContract,
    GPUJobRequest,
    GPUJobResult,
    GPUJobStatus,
    GPUProvider,
    get_adapter,
)
from literary_system.finetune.lora_training_config import (
    MONTHLY_SLO_USD,
    LoRAScheduleType,
    LoRATrainingConfig,
)

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

BIWEEKLY_INTERVAL_DAYS: int = 14      # 격주 풀 학습 주기
WEEKLY_INTERVAL_DAYS: int = 7         # 주간 미세조정 주기

# 격주 풀 학습 예상 시간 (Llama-3.1-8B, 2K샘플, A100 기준 ~6h)
DEFAULT_FULL_TRAINING_HOURS: float = 6.0
# 주간 미세조정 예상 시간
DEFAULT_FINE_TUNING_HOURS: float = 2.0


# ---------------------------------------------------------------------------
# JobRunRecord
# ---------------------------------------------------------------------------

@dataclass
class JobRunRecord:
    """
    단일 LoRA 학습 작업 실행 기록.

    Attributes:
        run_id:          고유 실행 ID
        schedule_type:   학습 스케줄 유형
        provider:        GPU 프로바이더
        job_id:          GPUJobRequest job_id
        status:          GPUJobStatus
        cost_usd:        발생 비용 (USD)
        hours:           실제 학습 시간
        artifact_path:   출력 아티팩트 경로
        dataset_path:    학습 데이터셋 경로
        config_snapshot: LoRATrainingConfig.to_dict() 스냅샷
        started_at:      시작 UTC ISO 타임스탬프
        finished_at:     완료 UTC ISO 타임스탬프 (진행중이면 "")
        dry_run:         dry_run 여부
        error:           오류 메시지 (없으면 "")
    """
    run_id: str
    schedule_type: LoRAScheduleType
    provider: GPUProvider
    job_id: str
    status: GPUJobStatus
    cost_usd: float
    hours: float
    artifact_path: str
    dataset_path: str
    config_snapshot: Dict[str, Any]
    started_at: str
    finished_at: str = ""
    dry_run: bool = True
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "schedule_type": self.schedule_type.value,
            "provider": self.provider.value,
            "job_id": self.job_id,
            "status": self.status.value,
            "cost_usd": round(self.cost_usd, 4),
            "hours": round(self.hours, 4),
            "artifact_path": self.artifact_path,
            "dataset_path": self.dataset_path,
            "config_snapshot": self.config_snapshot,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "dry_run": self.dry_run,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "JobRunRecord":
        d = dict(d)
        d["schedule_type"] = LoRAScheduleType(d["schedule_type"])
        d["provider"] = GPUProvider(d["provider"])
        d["status"] = GPUJobStatus(d["status"])
        return cls(**d)


# ---------------------------------------------------------------------------
# BiweeklyScheduler
# ---------------------------------------------------------------------------

class BiweeklyScheduler:
    """
    격주 학습 / 주간 미세조정 스케줄 판단기.

    마지막 실행 타임스탬프(epoch 초)를 기반으로
    현재 시점에 어떤 유형의 학습이 필요한지 결정.
    """

    def __init__(
        self,
        full_interval_days: int = BIWEEKLY_INTERVAL_DAYS,
        fine_interval_days: int = WEEKLY_INTERVAL_DAYS,
    ) -> None:
        self.full_interval_sec: float = full_interval_days * 86_400
        self.fine_interval_sec: float = fine_interval_days * 86_400

    def is_full_training_due(
        self,
        last_full_ts: Optional[float],
        now: Optional[float] = None,
    ) -> bool:
        """
        격주 풀 학습이 도래했는지 확인.

        Args:
            last_full_ts: 마지막 풀 학습 완료 epoch초. None이면 즉시 due.
            now:          현재 epoch초 (None이면 time.time() 사용).
        """
        if last_full_ts is None:
            return True
        now = now or time.time()
        return (now - last_full_ts) >= self.full_interval_sec

    def is_fine_tuning_due(
        self,
        last_fine_ts: Optional[float],
        now: Optional[float] = None,
    ) -> bool:
        """
        주간 미세조정이 도래했는지 확인.

        Args:
            last_fine_ts: 마지막 미세조정 완료 epoch초. None이면 즉시 due.
            now:          현재 epoch초 (None이면 time.time() 사용).
        """
        if last_fine_ts is None:
            return True
        now = now or time.time()
        return (now - last_fine_ts) >= self.fine_interval_sec

    def next_schedule_type(
        self,
        last_full_ts: Optional[float],
        last_fine_ts: Optional[float],
        now: Optional[float] = None,
    ) -> Optional[LoRAScheduleType]:
        """
        다음에 실행해야 할 스케줄 유형 반환.

        풀 학습이 도래했으면 FULL_BIWEEKLY 우선.
        아니면 미세조정 도래 시 FINE_WEEKLY.
        둘 다 아니면 None (아직 시기 아님).
        """
        now = now or time.time()
        if self.is_full_training_due(last_full_ts, now):
            return LoRAScheduleType.FULL_BIWEEKLY
        if self.is_fine_tuning_due(last_fine_ts, now):
            return LoRAScheduleType.FINE_WEEKLY
        return None


# ---------------------------------------------------------------------------
# LoRAJobRunner
# ---------------------------------------------------------------------------

class LoRAJobRunner:
    """
    LoRA 학습 작업 실행기.

    GPUAdapterContract를 통해 실제(또는 dry_run) GPU 작업을 제출하고
    JobRunRecord를 JSONL 파일에 영속화한다.

    Usage:
        runner = LoRAJobRunner(provider=GPUProvider.RUNPOD, dry_run=True)
        record = runner.run(config, dataset_path="data/train.jsonl")
    """

    def __init__(
        self,
        provider: GPUProvider = GPUProvider.RUNPOD,
        dry_run: bool = True,
        cost_slo: CostSLO = DEFAULT_COST_SLO,
        history_path: Optional[str] = None,
    ) -> None:
        """
        Args:
            provider:      GPU 클라우드 프로바이더
            dry_run:       True이면 실제 GPU 기동 없이 비용 추정만 수행
            cost_slo:      월간 비용 SLO (soft/hard/emergency)
            history_path:  실행 이력 JSONL 저장 경로 (None이면 영속화 안 함)
        """
        self._provider_id = provider
        self._adapter: GPUAdapterContract = get_adapter(provider)
        self._dry_run = dry_run
        self._cost_slo = cost_slo
        self._history_path = Path(history_path) if history_path else None
        self._scheduler = BiweeklyScheduler()

        # 메모리 내 이력 (영속화 파일이 없어도 관리)
        self._history: List[JobRunRecord] = []
        if self._history_path and self._history_path.exists():
            self._load_history()

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def run(
        self,
        config: LoRATrainingConfig,
        dataset_path: str,
        hours_estimate: Optional[float] = None,
    ) -> JobRunRecord:
        """
        LoRA 학습 작업 실행.

        1. 월간 누적 비용 SLO 점검 → HALT/BLOCK 시 예외 발생
        2. GPUAdapterContract.launch_job() 또는 dry_run() 호출
        3. JobRunRecord 생성 후 이력에 추가

        Args:
            config:         LoRA 학습 설정
            dataset_path:   Alpaca JSONL 데이터셋 경로
            hours_estimate: 예상 학습 시간 (None이면 schedule_type별 기본값)

        Returns:
            JobRunRecord
        """
        if hours_estimate is None:
            hours_estimate = (
                DEFAULT_FULL_TRAINING_HOURS
                if config.schedule_type == LoRAScheduleType.FULL_BIWEEKLY
                else DEFAULT_FINE_TUNING_HOURS
            )

        # SLO 점검
        self._check_slo_before_run(config, hours_estimate)

        run_id = str(uuid.uuid4())[:8]
        started_at = datetime.now(timezone.utc).isoformat()

        request = GPUJobRequest(
            model_name=config.base_model,
            dataset_path=dataset_path,
            hours_estimate=hours_estimate,
            dry_run=self._dry_run,
            extra=config.extra,
        )

        if self._dry_run:
            result: GPUJobResult = self._adapter.dry_run(request)
        else:
            result = self._adapter.launch_job(request)

        finished_at = datetime.now(timezone.utc).isoformat()

        record = JobRunRecord(
            run_id=run_id,
            schedule_type=config.schedule_type,
            provider=self._provider_id,
            job_id=result.job_id,
            status=result.status,
            cost_usd=result.cost_usd,
            hours=result.actual_hours,
            artifact_path=result.artifact_path,
            dataset_path=dataset_path,
            config_snapshot=config.to_dict(),
            started_at=started_at,
            finished_at=finished_at,
            dry_run=self._dry_run,
            error=result.error,
        )

        self._history.append(record)
        if self._history_path:
            self._append_record(record)

        return record

    def monthly_spend(self, year: Optional[int] = None, month: Optional[int] = None) -> float:
        """
        특정 연/월의 누적 비용 (USD) 반환.
        year/month가 None이면 현재 연/월 기준.
        """
        now = datetime.now(timezone.utc)
        y = year or now.year
        m = month or now.month

        return sum(
            r.cost_usd
            for r in self._history
            if r.started_at.startswith(f"{y:04d}-{m:02d}")
        )

    def slo_status(self) -> str:
        """
        현재 월 누적 비용에 대한 SLO 상태 문자열 반환.
        "OK" | "WARN" | "BLOCK" | "HALT"
        """
        return self._cost_slo.assess(self.monthly_spend())

    def history(self) -> List[JobRunRecord]:
        """실행 이력 반환 (복사본)."""
        return list(self._history)

    def last_run_by_type(
        self, schedule_type: LoRAScheduleType
    ) -> Optional[JobRunRecord]:
        """특정 스케줄 유형의 마지막 실행 기록 반환."""
        matches = [r for r in self._history if r.schedule_type == schedule_type]
        return matches[-1] if matches else None

    def next_due(self, now: Optional[float] = None) -> Optional[LoRAScheduleType]:
        """
        현재 시점 기준으로 다음에 실행해야 할 스케줄 유형 반환.
        None이면 아직 시기가 아님.
        """
        last_full = self.last_run_by_type(LoRAScheduleType.FULL_BIWEEKLY)
        last_fine = self.last_run_by_type(LoRAScheduleType.FINE_WEEKLY)

        last_full_ts = (
            datetime.fromisoformat(last_full.finished_at).timestamp()
            if last_full and last_full.finished_at
            else None
        )
        last_fine_ts = (
            datetime.fromisoformat(last_fine.finished_at).timestamp()
            if last_fine and last_fine.finished_at
            else None
        )

        return self._scheduler.next_schedule_type(last_full_ts, last_fine_ts, now)

    # ------------------------------------------------------------------
    # 내부 메서드
    # ------------------------------------------------------------------

    def _check_slo_before_run(
        self, config: LoRATrainingConfig, hours_estimate: float
    ) -> None:
        """
        월간 SLO 점검.

        HALT: 즉시 중단 → RuntimeError
        BLOCK: 신규 차단 → RuntimeError
        WARN: 경보 발령 → UserWarning (계속 허용)
        """
        projected_cost = self._adapter.estimate_cost(hours_estimate)
        current_spend = self.monthly_spend()
        total_projected = current_spend + projected_cost
        status = self._cost_slo.assess(total_projected)

        if status == "HALT":
            raise RuntimeError(
                f"LoRAJobRunner: GPU SLO HALT — 월 누적 비용 ${total_projected:.2f} "
                f"≥ emergency ${self._cost_slo.emergency:.2f}. 모든 작업 즉시 중단."
            )
        if status == "BLOCK":
            raise RuntimeError(
                f"LoRAJobRunner: GPU SLO BLOCK — 월 누적 비용 ${total_projected:.2f} "
                f"≥ hard ${self._cost_slo.hard:.2f}. 신규 작업 차단."
            )
        if status == "WARN":
            warnings.warn(
                f"LoRAJobRunner: GPU SLO WARN — 월 누적 비용 ${total_projected:.2f} "
                f"≥ soft ${self._cost_slo.soft:.2f}.",
                UserWarning,
                stacklevel=3,
            )

    def _append_record(self, record: JobRunRecord) -> None:
        """이력 파일에 레코드 한 줄 추가 (JSONL)."""
        self._history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._history_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    def _load_history(self) -> None:
        """기존 이력 파일 로드."""
        with open(self._history_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        self._history.append(JobRunRecord.from_dict(json.loads(line)))
                    except (KeyError, ValueError):
                        # 손상된 레코드 무시 (경고만)
                        warnings.warn(
                            f"LoRAJobRunner: corrupted history record skipped: {line[:80]}",
                            UserWarning,
                            stacklevel=1,
                        )


# ============================================================
# V625 추가: AutoRecoveryScheduler + CLI 진입점
# ============================================================

class AutoRecoveryScheduler:
    """
    biweekly_train CI가 실패했을 때 자동 복구를 조율하는 스케줄러.

    복구 전략:
    1. RunPod 가용 확인 (check_runpod_availability 연동)
    2. 가용 없음 → Lambda 폴백 지시
    3. 최대 재시도 횟수 초과 → Slack 에스컬레이션

    VERSION = "1.0.0"
    """

    VERSION = "1.0.0"
    MAX_RETRIES: int = 3
    RETRY_INTERVAL_SEC: int = 300  # 5분

    BACKEND_RUNPOD = "runpod"
    BACKEND_LAMBDA = "lambda_h100"

    def __init__(
        self,
        max_retries: int = MAX_RETRIES,
        retry_interval_sec: int = RETRY_INTERVAL_SEC,
        dry_run: bool = True,
    ) -> None:
        self._max_retries = max_retries
        self._retry_interval_sec = retry_interval_sec
        self._dry_run = dry_run
        self._attempt_log: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def decide_backend(self, runpod_available: bool) -> str:
        """RunPod 가용 여부에 따라 백엔드 결정."""
        return self.BACKEND_RUNPOD if runpod_available else self.BACKEND_LAMBDA

    def record_attempt(
        self,
        backend: str,
        success: bool,
        reason: str = "",
    ) -> Dict[str, Any]:
        """
        실행 시도 기록.

        Returns:
            {"attempt": int, "backend": str, "success": bool, "reason": str}
        """
        attempt_no = len(self._attempt_log) + 1
        record = {
            "attempt": attempt_no,
            "backend": backend,
            "success": success,
            "reason": reason,
        }
        self._attempt_log.append(record)
        return record

    def should_escalate(self) -> bool:
        """재시도 한도 초과 여부."""
        return len(self._attempt_log) >= self._max_retries and not any(
            r["success"] for r in self._attempt_log
        )

    def recovery_summary(self) -> Dict[str, Any]:
        """복구 시도 요약."""
        attempts = len(self._attempt_log)
        succeeded = sum(1 for r in self._attempt_log if r["success"])
        return {
            "version": self.VERSION,
            "attempts": attempts,
            "succeeded": succeeded,
            "escalate": self.should_escalate(),
            "log": list(self._attempt_log),
        }

    def reset(self) -> None:
        """시도 이력 초기화."""
        self._attempt_log.clear()


# ── CLI 진입점 ─────────────────────────────────────────────────────────

def _main_cli() -> None:  # pragma: no cover
    """biweekly_train.yml에서 직접 호출하는 CLI."""
    import argparse as _argparse

    parser = _argparse.ArgumentParser(description="LoRA Job Runner CLI (V625)")
    parser.add_argument("--base", default="llama-3.1-8b", help="기반 모델 이름")
    parser.add_argument(
        "--backend",
        default="runpod",
        choices=["runpod", "lambda_h100", "auto"],
        help="GPU 백엔드",
    )
    parser.add_argument(
        "--dry-run",
        default="true",
        help="true/false (기본 true)",
    )
    args = parser.parse_args()

    dry_run = args.dry_run.lower() in ("true", "1", "yes")
    provider_map = {
        "runpod": GPUProvider.RUNPOD,
        "lambda_h100": GPUProvider.LAMBDA_LABS,
        "auto": GPUProvider.RUNPOD,  # auto는 check_runpod_availability가 결정
    }
    provider = provider_map.get(args.backend, GPUProvider.RUNPOD)

    runner = LoRAJobRunner(provider=provider, dry_run=dry_run)

    config = LoRATrainingConfig(
        base_model=args.base,
        dataset_version="latest",
        schedule_type=LoRAScheduleType.FULL_TRAINING,
    )

    import sys as _sys
    try:
        record = runner.run(config, dataset_path="data/train.jsonl")
        logger.info("[LoRAJobRunner] 완료: %s | 상태: %s", record.job_id, record.status)
        _sys.exit(0)
    except RuntimeError as exc:
        logger.error("[LoRAJobRunner] SLO BLOCK: %s", exc)
        _sys.exit(1)


if __name__ == "__main__":
    _main_cli()
