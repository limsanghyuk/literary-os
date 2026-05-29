"""
long_run_scenario.py — V624 24h 장기 시나리오 시뮬레이션 (ADR-091).

실제 24시간 실행 대신, 시간 단계(epoch)를 압축하여
메모리·성능·안정성을 검증한다.

설계 원칙
----------
- LLM-0: 이 모듈은 외부 LLM 호출을 하지 않는다.
- 24개 epoch = 24시간 압축 (epoch당 약 1초 이내)
- 각 epoch에서 핵심 컴포넌트를 순환 실행하고 스냅샷을 기록한다.
- 임계값 초과 시 WARN/FAIL 판정을 내린다.
"""
from __future__ import annotations

import gc
import logging
import time
import tracemalloc
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------
EPOCH_COUNT: int = 24           # 24 epoch = 24시간 압축
MAX_MEMORY_GROWTH_MB: float = 50.0   # epoch간 메모리 증가 허용 한계 (MB)
MAX_EPOCH_LATENCY_MS: float = 2000.0  # epoch 처리 최대 허용 시간 (ms)
WARN_MEMORY_GROWTH_MB: float = 20.0   # 경고 임계값 (MB)


# ---------------------------------------------------------------------------
# 데이터 클래스
# ---------------------------------------------------------------------------

@dataclass
class LongRunSnapshot:
    """단일 epoch 실행 결과 스냅샷."""

    epoch: int
    elapsed_ms: float
    memory_mb: float
    memory_delta_mb: float      # 직전 epoch 대비 증가량
    component_results: Dict[str, bool] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def pass_(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict:
        return {
            "epoch": self.epoch,
            "elapsed_ms": round(self.elapsed_ms, 2),
            "memory_mb": round(self.memory_mb, 3),
            "memory_delta_mb": round(self.memory_delta_mb, 3),
            "component_results": self.component_results,
            "warnings": self.warnings,
            "errors": self.errors,
            "pass": self.pass_,
        }


@dataclass
class LongRunScenarioReport:
    """전체 24h 장기 실행 리포트."""

    VERSION: str = "1.0.0"
    snapshots: List[LongRunSnapshot] = field(default_factory=list)
    total_elapsed_ms: float = 0.0
    peak_memory_mb: float = 0.0
    base_memory_mb: float = 0.0

    @property
    def all_pass(self) -> bool:
        return bool(self.snapshots) and all(s.pass_ for s in self.snapshots)

    @property
    def epoch_count(self) -> int:
        return len(self.snapshots)

    @property
    def memory_growth_mb(self) -> float:
        return self.peak_memory_mb - self.base_memory_mb

    @property
    def failed_epochs(self) -> List[int]:
        return [s.epoch for s in self.snapshots if not s.pass_]

    @property
    def warn_epochs(self) -> List[int]:
        return [s.epoch for s in self.snapshots if s.warnings]

    def summary(self) -> str:
        status = "PASS" if self.all_pass else "FAIL"
        return (
            f"LongRunScenario {status} | "
            f"epochs={self.epoch_count}/{EPOCH_COUNT} | "
            f"memory_growth={self.memory_growth_mb:.1f}MB | "
            f"peak={self.peak_memory_mb:.1f}MB | "
            f"elapsed={self.total_elapsed_ms:.0f}ms"
        )

    def to_dict(self) -> dict:
        return {
            "VERSION": self.VERSION,
            "all_pass": self.all_pass,
            "epoch_count": self.epoch_count,
            "total_elapsed_ms": round(self.total_elapsed_ms, 2),
            "base_memory_mb": round(self.base_memory_mb, 3),
            "peak_memory_mb": round(self.peak_memory_mb, 3),
            "memory_growth_mb": round(self.memory_growth_mb, 3),
            "failed_epochs": self.failed_epochs,
            "warn_epochs": self.warn_epochs,
            "snapshots": [s.to_dict() for s in self.snapshots],
            "summary": self.summary(),
        }


# ---------------------------------------------------------------------------
# LongRunScenario
# ---------------------------------------------------------------------------

class LongRunScenario:
    """
    24h 압축 시나리오 실행기 (V624 ADR-091).

    Parameters
    ----------
    epoch_count:
        실행할 epoch 수 (기본 24). 테스트에서는 소수로 설정 가능.
    custom_hooks:
        epoch마다 호출할 추가 콜백 {이름: callable}.
        callable은 (epoch: int) -> bool 서명.
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        epoch_count: int = EPOCH_COUNT,
        custom_hooks: Optional[Dict[str, Callable[[int], bool]]] = None,
    ) -> None:
        self._epoch_count = epoch_count
        self._hooks: Dict[str, Callable[[int], bool]] = custom_hooks or {}
        self._report: Optional[LongRunScenarioReport] = None

    # ── 공개 API ────────────────────────────────────────────────────────────

    def run(self) -> LongRunScenarioReport:
        """전체 장기 시나리오를 실행하고 LongRunReport를 반환한다."""
        _log.info("LongRunScenario 시작 — %d epochs", self._epoch_count)
        report = LongRunScenarioReport()

        tracemalloc.start()
        prev_mem = self._current_mem_mb()
        report.base_memory_mb = prev_mem
        total_start = time.monotonic()

        for epoch in range(1, self._epoch_count + 1):
            snap = self._run_epoch(epoch, prev_mem)
            report.snapshots.append(snap)
            report.peak_memory_mb = max(report.peak_memory_mb, snap.memory_mb)
            prev_mem = snap.memory_mb
            _log.debug("Epoch %d: %s", epoch, "PASS" if snap.pass_ else "FAIL")

        report.total_elapsed_ms = (time.monotonic() - total_start) * 1000
        tracemalloc.stop()

        self._report = report
        status = "PASS" if report.all_pass else "FAIL"
        _log.info("LongRunScenario %s — %s", status, report.summary())
        return report

    def last_report(self) -> Optional[LongRunScenarioReport]:
        return self._report

    def is_stable(self) -> bool:
        """직전 run() 결과가 안정적인지 여부 (PASS + 메모리 증가 < 임계값)."""
        if self._report is None:
            return False
        return (
            self._report.all_pass
            and self._report.memory_growth_mb < MAX_MEMORY_GROWTH_MB
        )

    # ── 내부 메서드 ─────────────────────────────────────────────────────────

    def _run_epoch(self, epoch: int, prev_mem: float) -> LongRunSnapshot:
        """단일 epoch 실행 — 핵심 컴포넌트 순환 + 메모리 측정."""
        t0 = time.monotonic()
        results: Dict[str, bool] = {}
        warnings: List[str] = []
        errors: List[str] = []

        # ── 핵심 컴포넌트 순환 실행 ──────────────────────────────────────
        component_checks = [
            ("cim_v2_cycle",       self._check_cim_v2),
            ("shared_char_cycle",  self._check_shared_char),
            ("reward_model_cycle", self._check_reward_model),
            ("reader_feedback",    self._check_reader_feedback),
            ("agent_routing",      self._check_agent_routing),
        ]
        for name, fn in component_checks:
            try:
                results[name] = fn(epoch)
                if not results[name]:
                    errors.append(f"epoch={epoch} component={name} FAIL")
            except Exception as exc:  # noqa: BLE001
                results[name] = False
                errors.append(f"epoch={epoch} component={name} ERROR: {exc}")

        # ── 커스텀 훅 실행 ───────────────────────────────────────────────
        for hook_name, hook_fn in self._hooks.items():
            try:
                results[f"hook:{hook_name}"] = hook_fn(epoch)
            except Exception as exc:  # noqa: BLE001
                results[f"hook:{hook_name}"] = False
                errors.append(f"epoch={epoch} hook={hook_name} ERROR: {exc}")

        # ── 메모리 측정 ──────────────────────────────────────────────────
        gc.collect()
        cur_mem = self._current_mem_mb()
        delta = cur_mem - prev_mem
        elapsed = (time.monotonic() - t0) * 1000

        # ── 임계값 판정 ──────────────────────────────────────────────────
        if delta > MAX_MEMORY_GROWTH_MB:
            errors.append(
                f"epoch={epoch} 메모리 증가 {delta:.1f}MB > 허용 {MAX_MEMORY_GROWTH_MB}MB"
            )
        elif delta > WARN_MEMORY_GROWTH_MB:
            warnings.append(
                f"epoch={epoch} 메모리 증가 경고 {delta:.1f}MB > {WARN_MEMORY_GROWTH_MB}MB"
            )

        if elapsed > MAX_EPOCH_LATENCY_MS:
            warnings.append(
                f"epoch={epoch} 지연 {elapsed:.0f}ms > 허용 {MAX_EPOCH_LATENCY_MS:.0f}ms"
            )

        return LongRunSnapshot(
            epoch=epoch,
            elapsed_ms=elapsed,
            memory_mb=cur_mem,
            memory_delta_mb=delta,
            component_results=results,
            warnings=warnings,
            errors=errors,
        )

    # ── 컴포넌트 체크 (LLM-0: 외부 호출 없음) ────────────────────────────

    @staticmethod
    def _check_cim_v2(epoch: int) -> bool:
        from literary_system.multiwork.multi_work_cim_v2 import MultiWorkCIMV2
        cim = MultiWorkCIMV2()
        cim.init_project(f"lr-epoch-{epoch}")
        cim.record_v2(f"lr-epoch-{epoch}", f"char_a_{epoch}", f"char_b_{epoch}", reward=0.7)
        return True

    @staticmethod
    def _check_shared_char(epoch: int) -> bool:
        from literary_system.multiwork.shared_character_db_v2 import SharedCharacterDBV2
        db = SharedCharacterDBV2()
        char_id = f"lr-char-{epoch}"
        db.add_character(char_id, name=f"캐릭터{epoch}", role="supporting")
        return db.get_character(char_id) is not None

    @staticmethod
    def _check_reward_model(epoch: int) -> bool:
        from literary_system.rlhf.reward_model import RewardModelV2
        m = RewardModelV2()
        text = f"희준은 {epoch}화에서 지수를 만났다."
        result = m.score_with_adv_seeds(text)
        return "baseline" in result

    @staticmethod
    def _check_reader_feedback(epoch: int) -> bool:
        from literary_system.multiwork.reader_feedback_ingest import ReaderFeedbackIngest
        ingest = ReaderFeedbackIngest()
        return not ingest.is_phase_c_active()  # Phase B 기간: False가 정상

    @staticmethod
    def _check_agent_routing(epoch: int) -> bool:
        from literary_system.llm_bridge.agent_envelope import AgentEnvelope, AgentRoutingPolicy, AgentRole
        policy = AgentRoutingPolicy(
            cost_weight=0.3, latency_weight=0.3,
            quality_weight=0.3, role_weight=0.1,
        )
        env = AgentEnvelope(
            agent_id=f"lr-agent-{epoch}",
            role=AgentRole.SCENE_WRITER,
            prompt=f"epoch {epoch} 시나리오",
        )
        return env is not None and abs(
            policy.cost_weight + policy.latency_weight
            + policy.quality_weight + policy.role_weight - 1.0
        ) < 1e-6

    @staticmethod
    def _current_mem_mb() -> float:
        """현재 프로세스 tracemalloc 기준 메모리 사용량 (MB)."""
        if tracemalloc.is_tracing():
            cur, _ = tracemalloc.get_traced_memory()
            return cur / (1024 * 1024)
        # fallback: psutil 없으면 0
        try:
            import psutil, os
            proc = psutil.Process(os.getpid())
            return proc.memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0
