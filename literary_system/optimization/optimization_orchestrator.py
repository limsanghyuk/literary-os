"""
OptimizationOrchestrator v1.0 — SP-B.4 최적화 통합 오케스트레이터 (V619)

PerformanceOptimizer · MemoryLeakDetector · StressTester ·
LongRunMonitor · AdaptiveThrottler 를 단일 파이프라인으로 연결하여
종합 OptimizationReport 를 생성한다.

실행 단계
----------
1. BASELINE  : MemoryLeakDetector 기준선 캡처
2. STRESS    : StressTester 3-페이즈 실행
3. LEAK      : MemoryLeakDetector 누수 점검
4. LONGRUN   : LongRunMonitor 에포크 내구성 검증
5. THROTTLE  : AdaptiveThrottler 동시성 조정 실행
6. REPORT    : 종합 판정 + OptimizationReport 반환
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from literary_system.optimization.memory_leak_detector import (
    LeakReport,
    MemoryLeakDetector,
)
from literary_system.optimization.stress_tester import (
    StressConfig,
    StressResult,
    StressTester,
)
from literary_system.optimization.long_run_monitor import (
    LongRunConfig,
    LongRunMonitor,
    LongRunReport,
)
from literary_system.optimization.adaptive_throttler import (
    AdaptiveThrottler,
    ThrottleConfig,
    ThrottleReport,
)

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 파이프라인 설정
# ---------------------------------------------------------------------------

@dataclass
class OptOrchestratorConfig:
    """OptimizationOrchestrator 전체 설정."""

    # StressTester
    warmup_iters: int = 2
    sustained_iters: int = 10
    cooldown_iters: int = 2
    target_p95_ms: float = 1500.0

    # MemoryLeakDetector
    leak_threshold_mb: float = 10.0

    # LongRunMonitor
    epochs: int = 3

    # AdaptiveThrottler
    initial_concurrency: int = 4
    warn_threshold_ms: float = 1200.0
    recover_threshold_ms: float = 800.0
    throttle_calls: int = 20

    # 메모리 예산 (비상 제동용)
    memory_budget_mb: Optional[float] = None

    def to_stress_config(self) -> StressConfig:
        from literary_system.optimization.stress_tester import StressConfig
        return StressConfig(
            warmup_iters=self.warmup_iters,
            sustained_iters=self.sustained_iters,
            cooldown_iters=self.cooldown_iters,
            target_p95_ms=self.target_p95_ms,
        )

    def to_longrun_config(self) -> LongRunConfig:
        return LongRunConfig(
            epochs=self.epochs,
            warmup_iters=self.warmup_iters,
            sustained_iters=self.sustained_iters,
            cooldown_iters=self.cooldown_iters,
            target_p95_ms=self.target_p95_ms,
            leak_threshold_mb=self.leak_threshold_mb,
            memory_budget_mb=self.memory_budget_mb,
        )

    def to_throttle_config(self) -> ThrottleConfig:
        return ThrottleConfig(
            initial_concurrency=self.initial_concurrency,
            warn_threshold_ms=self.warn_threshold_ms,
            recover_threshold_ms=self.recover_threshold_ms,
            memory_budget_mb=self.memory_budget_mb,
        )


# ---------------------------------------------------------------------------
# 단계별 결과
# ---------------------------------------------------------------------------

@dataclass
class StageResult:
    """단일 파이프라인 단계 결과."""

    stage: str
    passed: bool
    duration_s: float
    detail: str = ""

    def to_dict(self) -> dict:
        return {
            "stage": self.stage,
            "passed": self.passed,
            "duration_s": round(self.duration_s, 4),
            "detail": self.detail,
        }


# ---------------------------------------------------------------------------
# 종합 보고서
# ---------------------------------------------------------------------------

@dataclass
class OptimizationReport:
    """OptimizationOrchestrator 전체 실행 보고서."""

    config: OptOrchestratorConfig
    stages: List[StageResult] = field(default_factory=list)
    stress_result: Optional[StressResult] = None
    leak_report: Optional[LeakReport] = None
    longrun_report: Optional[LongRunReport] = None
    throttle_report: Optional[ThrottleReport] = None
    total_duration_s: float = 0.0

    @property
    def all_pass(self) -> bool:
        return all(s.passed for s in self.stages)

    @property
    def failed_stages(self) -> List[str]:
        return [s.stage for s in self.stages if not s.passed]

    @property
    def passed_count(self) -> int:
        return sum(1 for s in self.stages if s.passed)

    @property
    def total_count(self) -> int:
        return len(self.stages)

    def summary(self) -> str:
        status = "PASS" if self.all_pass else "FAIL"
        return (
            f"OptimizationOrchestrator {status} | "
            f"단계 {self.passed_count}/{self.total_count} | "
            f"소요 {self.total_duration_s:.2f}s"
        )

    def to_dict(self) -> dict:
        return {
            "all_pass": self.all_pass,
            "passed_count": self.passed_count,
            "total_count": self.total_count,
            "total_duration_s": round(self.total_duration_s, 4),
            "failed_stages": self.failed_stages,
            "stages": [s.to_dict() for s in self.stages],
            "stress_p95_ms": (
                self.stress_result.sustained.p95_ms
                if self.stress_result and self.stress_result.sustained
                else None
            ),
            "leak_delta_mb": (
                self.leak_report.delta_mb if self.leak_report else None
            ),
            "longrun_all_pass": (
                self.longrun_report.all_pass if self.longrun_report else None
            ),
            "throttle_reduce_count": (
                self.throttle_report.reduce_count if self.throttle_report else None
            ),
        }


# ---------------------------------------------------------------------------
# 메인 클래스
# ---------------------------------------------------------------------------

class OptimizationOrchestrator:
    """
    SP-B.4 최적화 통합 오케스트레이터.

    사용 예::

        orch = OptimizationOrchestrator()
        report = orch.run(fn=my_scene_fn)
        _log.info(report.summary())

    ``fn`` 은 인수 없이 호출 가능한 callable 이어야 한다.
    지연 측정은 내부에서 수행하므로 반환값은 사용하지 않는다.
    """

    def __init__(self, config: Optional[OptOrchestratorConfig] = None) -> None:
        self.config: OptOrchestratorConfig = config or OptOrchestratorConfig()

    def run(
        self,
        fn: Callable[[], object],
        memory_sampler: Optional[Callable[[], float]] = None,
    ) -> OptimizationReport:
        """
        6단계 파이프라인을 순서대로 실행하고 OptimizationReport 를 반환한다.

        Parameters
        ----------
        fn:
            측정 대상 callable. 인수 없이 호출된다.
        memory_sampler:
            현재 메모리 사용량(MB)을 반환하는 callable. None 이면 스킵.
        """
        cfg = self.config
        report = OptimizationReport(config=cfg)
        pipeline_start = time.monotonic()

        _log.info("OptimizationOrchestrator 시작 (%d 에포크)", cfg.epochs)

        # ── Stage 1: BASELINE ──────────────────────────────────────────
        t0 = time.monotonic()
        detector = MemoryLeakDetector(threshold_mb=cfg.leak_threshold_mb)
        try:
            detector.start()
            detector.baseline()
            stage1 = StageResult(
                stage="BASELINE",
                passed=True,
                duration_s=time.monotonic() - t0,
                detail="tracemalloc 기준선 캡처 완료",
            )
        except Exception as exc:  # noqa: BLE001
            stage1 = StageResult(
                stage="BASELINE",
                passed=False,
                duration_s=time.monotonic() - t0,
                detail=f"기준선 실패: {exc}",
            )
        report.stages.append(stage1)

        # ── Stage 2: STRESS ───────────────────────────────────────────
        t0 = time.monotonic()
        stress_cfg = cfg.to_stress_config()
        tester = StressTester(stress_cfg)

        def _timed_fn() -> float:
            start = time.monotonic()
            fn()
            return (time.monotonic() - start) * 1000.0

        try:
            stress_result = tester.run(_timed_fn, memory_sampler)
            report.stress_result = stress_result
            stage2 = StageResult(
                stage="STRESS",
                passed=stress_result.slo_p95_pass,
                duration_s=time.monotonic() - t0,
                detail=(
                    f"P95={stress_result.sustained.p95_ms:.1f}ms "
                    f"(SLO={cfg.target_p95_ms}ms)"
                    if stress_result.sustained else "sustained 없음"
                ),
            )
        except Exception as exc:  # noqa: BLE001
            stage2 = StageResult(
                stage="STRESS",
                passed=False,
                duration_s=time.monotonic() - t0,
                detail=f"스트레스 실패: {exc}",
            )
        report.stages.append(stage2)

        # ── Stage 3: LEAK ─────────────────────────────────────────────
        t0 = time.monotonic()
        try:
            snap = detector.capture()
            leak_report = detector.check(snap)
            detector.stop()
            report.leak_report = leak_report
            stage3 = StageResult(
                stage="LEAK",
                passed=not leak_report.is_leaking,
                duration_s=time.monotonic() - t0,
                detail=f"delta={leak_report.delta_mb:.2f}MB (임계={cfg.leak_threshold_mb}MB)",
            )
        except Exception as exc:  # noqa: BLE001
            stage3 = StageResult(
                stage="LEAK",
                passed=False,
                duration_s=time.monotonic() - t0,
                detail=f"누수 점검 실패: {exc}",
            )
        report.stages.append(stage3)

        # ── Stage 4: LONGRUN ──────────────────────────────────────────
        t0 = time.monotonic()
        lr_cfg = cfg.to_longrun_config()
        monitor = LongRunMonitor(lr_cfg)
        try:
            lr_report = monitor.run(_timed_fn, memory_sampler)
            report.longrun_report = lr_report
            stage4 = StageResult(
                stage="LONGRUN",
                passed=lr_report.all_pass,
                duration_s=time.monotonic() - t0,
                detail=(
                    f"{len(lr_report.epochs) - len(lr_report.failed_epochs)}/{len(lr_report.epochs)} 에포크 PASS | "
                    f"실패={lr_report.failed_epochs}"
                ),
            )
        except Exception as exc:  # noqa: BLE001
            stage4 = StageResult(
                stage="LONGRUN",
                passed=False,
                duration_s=time.monotonic() - t0,
                detail=f"장기 실행 실패: {exc}",
            )
        report.stages.append(stage4)

        # ── Stage 5: THROTTLE ─────────────────────────────────────────
        t0 = time.monotonic()
        th_cfg = cfg.to_throttle_config()
        throttler = AdaptiveThrottler(th_cfg)
        try:
            for _ in range(cfg.throttle_calls):
                with throttler.slot():
                    lat = _timed_fn()
                    mem = memory_sampler() if memory_sampler else None
                    throttler.record(lat, mem)
            th_report = throttler.get_report()
            report.throttle_report = th_report
            stage5 = StageResult(
                stage="THROTTLE",
                passed=True,
                duration_s=time.monotonic() - t0,
                detail=(
                    f"avg={th_report.avg_latency_ms:.1f}ms | "
                    f"감속={th_report.reduce_count} 가속={th_report.increase_count}"
                ),
            )
        except Exception as exc:  # noqa: BLE001
            stage5 = StageResult(
                stage="THROTTLE",
                passed=False,
                duration_s=time.monotonic() - t0,
                detail=f"조절 실패: {exc}",
            )
        report.stages.append(stage5)

        # ── Stage 6: REPORT ───────────────────────────────────────────
        report.total_duration_s = time.monotonic() - pipeline_start
        status = "PASS" if report.all_pass else "FAIL"
        _log.info("OptimizationOrchestrator %s — %s", status, report.summary())

        return report

    # ------------------------------------------------------------------
    # 편의 클래스메서드
    # ------------------------------------------------------------------

    @classmethod
    def quick_run(
        cls,
        fn: Callable[[], object],
        target_p95_ms: float = 1500.0,
        epochs: int = 2,
    ) -> OptimizationReport:
        """경량 설정으로 빠르게 파이프라인을 실행한다."""
        cfg = OptOrchestratorConfig(
            warmup_iters=1,
            sustained_iters=5,
            cooldown_iters=1,
            target_p95_ms=target_p95_ms,
            epochs=epochs,
            throttle_calls=10,
        )
        return cls(cfg).run(fn)
