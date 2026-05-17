"""
FineTuneJobManager — LoRA/QLoRA 자체호스팅 파인튜닝 잡 관리 (V469)

ADR-014: Training Data Hygiene + Fine-tune Lifecycle
  - 1순위: LoRA/QLoRA 자체호스팅 (peft 라이브러리 시뮬레이션)
  - Tier-2: OpenAI fine-tuning (사용자 명시적 동의 시에만)
  - 체크포인트 폴링 / 잡 상태 관리
  - LLM-0: 잡 관리 로직 전체 규칙 기반 (외부 LLM 없음)

설계:
  submit(dataset_id) → JobID
  status(job_id) → JobStatus
  cancel(job_id) → bool
  list_jobs() → list[FineTuneJob]
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# 열거형
# ---------------------------------------------------------------------------

class FineTuneMethod(str, Enum):
    LORA = "lora"               # LoRA 자체호스팅 (1순위)
    QLORA = "qlora"             # QLoRA 4-bit 양자화
    OPENAI_TIER2 = "openai_t2"  # OpenAI fine-tuning (동의 시 Tier-2)
    MOCK = "mock"               # 테스트용 mock


class JobStatus(str, Enum):
    QUEUED = "queued"
    PREPARING = "preparing"       # 데이터셋 검증·전처리
    TRAINING = "training"         # 학습 중
    EVALUATING = "evaluating"     # 평가 중
    COMPLETED = "completed"       # 완료
    FAILED = "failed"             # 실패
    CANCELLED = "cancelled"       # 취소


# ---------------------------------------------------------------------------
# 데이터 클래스
# ---------------------------------------------------------------------------

@dataclass
class CheckpointInfo:
    checkpoint_id: str
    step: int
    loss: float
    saved_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "step": self.step,
            "loss": self.loss,
            "saved_at": self.saved_at,
        }


@dataclass
class FineTuneJob:
    job_id: str
    dataset_id: str
    method: FineTuneMethod
    base_model: str
    status: JobStatus
    created_at: str
    updated_at: str
    completed_at: str | None = None
    model_artifact_id: str | None = None     # 완료 후 등록 모델 ID
    total_steps: int = 1000
    current_step: int = 0
    current_loss: float = 0.0
    checkpoints: list[CheckpointInfo] = field(default_factory=list)
    error_message: str | None = None
    hyperparams: dict[str, Any] = field(default_factory=dict)
    consent_verified: bool = False           # Tier-2 동의 확인

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "dataset_id": self.dataset_id,
            "method": self.method.value,
            "base_model": self.base_model,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "model_artifact_id": self.model_artifact_id,
            "total_steps": self.total_steps,
            "current_step": self.current_step,
            "current_loss": self.current_loss,
            "checkpoints": [c.to_dict() for c in self.checkpoints],
            "error_message": self.error_message,
            "hyperparams": self.hyperparams,
            "consent_verified": self.consent_verified,
        }

    @property
    def progress_pct(self) -> float:
        if self.total_steps == 0:
            return 0.0
        return round(self.current_step / self.total_steps * 100, 1)

    @property
    def is_terminal(self) -> bool:
        return self.status in (
            JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED
        )


# ---------------------------------------------------------------------------
# 기본 하이퍼파라미터
# ---------------------------------------------------------------------------

_DEFAULT_LORA_PARAMS: dict[str, Any] = {
    "r": 16,                  # LoRA rank
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "target_modules": ["q_proj", "v_proj"],
    "learning_rate": 2e-4,
    "num_epochs": 3,
    "batch_size": 4,
    "gradient_accumulation_steps": 4,
    "fp16": True,
    "max_seq_length": 2048,
}

_DEFAULT_QLORA_PARAMS: dict[str, Any] = {
    **_DEFAULT_LORA_PARAMS,
    "load_in_4bit": True,
    "bnb_4bit_compute_dtype": "float16",
    "bnb_4bit_use_double_quant": True,
    "bnb_4bit_quant_type": "nf4",
}

_DEFAULT_OPENAI_PARAMS: dict[str, Any] = {
    "model": "gpt-4o-mini-2024-07-18",
    "n_epochs": 3,
    "batch_size": "auto",
    "learning_rate_multiplier": "auto",
}


# ---------------------------------------------------------------------------
# FineTuneJobManager
# ---------------------------------------------------------------------------

class FineTuneJobManager:
    """
    ADR-014 파인튜닝 잡 관리자.

    - LoRA/QLoRA 자체호스팅 1순위 (LLM-0: 잡 관리 로직은 규칙 기반)
    - OpenAI Tier-2: 사용자 명시 동의(consent_verified=True) 필요
    - 체크포인트 자동 저장 (500스텝마다)
    - 잡 취소: QUEUED/PREPARING/TRAINING 상태만 가능

    simulate_training(): 테스트용 학습 진행 시뮬레이션
    """

    CHECKPOINT_INTERVAL = 500     # 스텝당 체크포인트
    MAX_CONCURRENT_JOBS = 3       # 동시 실행 최대
    SUPPORTED_BASE_MODELS = {
        "lora": ["mistral-7b", "llama-3-8b", "gemma-2b", "literary-base-v1"],
        "qlora": ["mistral-7b-4bit", "llama-3-8b-4bit"],
        "openai_t2": ["gpt-4o-mini-2024-07-18", "gpt-3.5-turbo"],
        "mock": ["mock-model-v1"],
    }

    def __init__(self) -> None:
        self._jobs: dict[str, FineTuneJob] = {}

    # ------------------------------------------------------------------
    # 잡 제출
    # ------------------------------------------------------------------

    def submit(
        self,
        dataset_id: str,
        method: FineTuneMethod = FineTuneMethod.LORA,
        base_model: str | None = None,
        hyperparams: dict[str, Any] | None = None,
        consent_verified: bool = False,
    ) -> str:
        """
        파인튜닝 잡 제출.
        Returns: job_id
        Raises:
          ValueError: Tier-2 동의 없음, 모델 미지원, 동시 잡 초과
        """
        # Tier-2 동의 확인
        if method == FineTuneMethod.OPENAI_TIER2 and not consent_verified:
            raise ValueError(
                "ADR-014 위반: OpenAI Tier-2 fine-tuning은 사용자 명시 동의 필요 "
                "(consent_verified=True)"
            )

        # 동시 실행 한도
        active = sum(
            1 for j in self._jobs.values()
            if not j.is_terminal
        )
        if active >= self.MAX_CONCURRENT_JOBS:
            raise ValueError(
                f"동시 실행 한도 초과 ({self.MAX_CONCURRENT_JOBS}개). "
                "실행 중인 잡이 완료된 후 재시도하세요."
            )

        # 기본 모델 결정
        if base_model is None:
            if method == FineTuneMethod.OPENAI_TIER2:
                base_model = "gpt-4o-mini-2024-07-18"
            elif method == FineTuneMethod.QLORA:
                base_model = "mistral-7b-4bit"
            elif method == FineTuneMethod.MOCK:
                base_model = "mock-model-v1"
            else:
                base_model = "mistral-7b"

        # 모델 지원 여부 확인
        supported = self.SUPPORTED_BASE_MODELS.get(method.value, [])
        if base_model not in supported:
            raise ValueError(
                f"미지원 모델: {base_model} (method={method.value}). "
                f"지원 모델: {supported}"
            )

        # 하이퍼파라미터
        if method == FineTuneMethod.QLORA:
            default_hp = dict(_DEFAULT_QLORA_PARAMS)
        elif method == FineTuneMethod.OPENAI_TIER2:
            default_hp = dict(_DEFAULT_OPENAI_PARAMS)
        else:
            default_hp = dict(_DEFAULT_LORA_PARAMS)
        if hyperparams:
            default_hp.update(hyperparams)

        now = datetime.now(timezone.utc).isoformat()
        job_id = f"ftjob-{str(uuid.uuid4())[:8]}"

        job = FineTuneJob(
            job_id=job_id,
            dataset_id=dataset_id,
            method=method,
            base_model=base_model,
            status=JobStatus.QUEUED,
            created_at=now,
            updated_at=now,
            total_steps=default_hp.get("num_epochs", 3) * 333,
            hyperparams=default_hp,
            consent_verified=consent_verified,
        )
        self._jobs[job_id] = job
        return job_id

    # ------------------------------------------------------------------
    # 상태 조회
    # ------------------------------------------------------------------

    def status(self, job_id: str) -> JobStatus:
        job = self._get_or_raise(job_id)
        return job.status

    def get_job(self, job_id: str) -> FineTuneJob:
        return self._get_or_raise(job_id)

    def list_jobs(
        self,
        status_filter: JobStatus | None = None,
    ) -> list[FineTuneJob]:
        jobs = list(self._jobs.values())
        if status_filter:
            jobs = [j for j in jobs if j.status == status_filter]
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)

    # ------------------------------------------------------------------
    # 잡 취소
    # ------------------------------------------------------------------

    def cancel(self, job_id: str) -> bool:
        """
        QUEUED/PREPARING/TRAINING 상태의 잡 취소.
        Returns: True if cancelled, False if already terminal
        """
        job = self._get_or_raise(job_id)
        if job.is_terminal:
            return False
        cancellable = (JobStatus.QUEUED, JobStatus.PREPARING, JobStatus.TRAINING)
        if job.status not in cancellable:
            return False
        now = datetime.now(timezone.utc).isoformat()
        job.status = JobStatus.CANCELLED
        job.updated_at = now
        return True

    # ------------------------------------------------------------------
    # 학습 진행 시뮬레이션 (테스트·개발용)
    # LLM-0: 실제 GPU 학습 없음, 상태 전이 시뮬레이션만
    # ------------------------------------------------------------------

    def simulate_training(
        self,
        job_id: str,
        steps: int = 100,
        loss_start: float = 2.5,
        loss_end: float = 0.8,
    ) -> FineTuneJob:
        """
        잡 학습 진행 시뮬레이션 (LLM-0: 실제 GPU 없음).

        steps만큼 진행하여 상태를 PREPARING → TRAINING → COMPLETED로 전이.
        체크포인트는 CHECKPOINT_INTERVAL마다 자동 저장.
        """
        job = self._get_or_raise(job_id)
        if job.is_terminal:
            raise ValueError(f"잡 {job_id}는 이미 종료 상태: {job.status.value}")

        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat()

        # QUEUED → PREPARING
        if job.status == JobStatus.QUEUED:
            job.status = JobStatus.PREPARING
            job.updated_at = now

        # PREPARING → TRAINING
        if job.status == JobStatus.PREPARING:
            job.status = JobStatus.TRAINING
            job.updated_at = now

        # TRAINING: 스텝 진행
        target_step = min(job.current_step + steps, job.total_steps)
        loss_range = loss_start - loss_end

        for step in range(job.current_step + 1, target_step + 1):
            progress = step / job.total_steps
            # 지수 감소 loss 시뮬레이션
            current_loss = loss_end + loss_range * (1 - progress) ** 1.5
            job.current_step = step
            job.current_loss = round(current_loss, 4)

            # 체크포인트 저장
            if step % self.CHECKPOINT_INTERVAL == 0:
                ckpt = CheckpointInfo(
                    checkpoint_id=f"ckpt-{job_id}-step{step}",
                    step=step,
                    loss=job.current_loss,
                    saved_at=datetime.now(timezone.utc).isoformat(),
                )
                job.checkpoints.append(ckpt)

        job.updated_at = datetime.now(timezone.utc).isoformat()

        # 완료 여부 — TRAINING 상태 잔류 방지 (Bug-Fix: is_terminal 보장)
        if job.current_step >= job.total_steps:
            job.status = JobStatus.EVALUATING
            job.updated_at = datetime.now(timezone.utc).isoformat()
            # EVALUATING → COMPLETED (원자적 전이 — cancel 경합 차단)
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc).isoformat()
            job.model_artifact_id = f"model-artifact-{job_id}"
            job.updated_at = job.completed_at
            # 불변식 검증: COMPLETED는 반드시 terminal이어야 한다
            assert job.is_terminal, "BUG: COMPLETED job is not terminal"

        return job

    # ------------------------------------------------------------------
    # 내부 유틸
    # ------------------------------------------------------------------

    def _get_or_raise(self, job_id: str) -> FineTuneJob:
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(f"잡 미발견: {job_id}")
        return job

    # ------------------------------------------------------------------
    # 통계
    # ------------------------------------------------------------------

    def get_stats(self) -> dict[str, Any]:
        jobs = list(self._jobs.values())
        by_status: dict[str, int] = {}
        for j in jobs:
            by_status[j.status.value] = by_status.get(j.status.value, 0) + 1
        return {
            "total_jobs": len(jobs),
            "by_status": by_status,
            "active_jobs": sum(1 for j in jobs if not j.is_terminal),
            "completed_jobs": sum(1 for j in jobs if j.status == JobStatus.COMPLETED),
        }
