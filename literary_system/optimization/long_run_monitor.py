"""
LongRunMonitor v1.0 — Literary OS SP-B.4 (V617)

MemoryLeakDetector + StressTester를 통합한 장기 실행 모니터.
설정 가능한 반복 횟수(epoch) 단위로 메모리·레이턴시 SLO를 검증한다.

주요 클래스:
  - LongRunConfig    : 실행 파라미터 (epochs, epoch_iters, memory/latency SLO)
  - EpochResult      : 단일 epoch 결과 (stress + leak 리포트)
  - LongRunReport    : 전체 실행 결과 (all_pass, epochs, peak_memory_mb)
  - LongRunMonitor   : 공개 API (run / run_epoch / summary)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

from literary_system.optimization.memory_leak_detector import (
    LeakReport,
    MemoryLeakDetector,
    MemorySnapshot,
)
from literary_system.optimization.stress_tester import (
    PhaseResult,
    StressConfig,
    StressResult,
    StressTester,
)

__all__ = [
    "LongRunConfig",
    "EpochResult",
    "LongRunReport",
    "LongRunMonitor",
]

_log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class LongRunConfig:
    """
    LongRunMonitor 실행 설정.

    Attributes:
        epochs              : 반복 epoch 수 (각 epoch = 1회 stress run + 1회 leak 체크)
        warmup_iters        : StressTester warmup 반복 수
        sustained_iters     : StressTester sustained 반복 수 (SLO 판정 기준)
        cooldown_iters      : StressTester cooldown 반복 수
        target_p95_ms       : 레이턴시 P95 SLO (ms). None = 체크 생략
        leak_threshold_mb   : 메모리 누수 임계값 (MB). None = 체크 생략
        memory_budget_mb    : 절대 피크 메모리 한도 (MB). None = 체크 생략
        sleep_between_epochs_s : epoch 사이 대기 시간 (초)
    """
    epochs: int = 3
    warmup_iters: int = 2
    sustained_iters: int = 10
    cooldown_iters: int = 2
    target_p95_ms: Optional[float] = 1500.0
    leak_threshold_mb: Optional[float] = 10.0
    memory_budget_mb: Optional[float] = None
    sleep_between_epochs_s: float = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 결과 클래스
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class EpochResult:
    """단일 epoch 실행 결과."""
    epoch: int
    stress: StressResult
    leak: LeakReport
    duration_s: float

    @property
    def pass_stress(self) -> bool:
        return self.stress.all_pass

    @property
    def pass_leak(self) -> bool:
        return not self.leak.is_leaking

    @property
    def all_pass(self) -> bool:
        return self.pass_stress and self.pass_leak

    def to_dict(self) -> dict:
        return {
            "epoch": self.epoch,
            "all_pass": self.all_pass,
            "pass_stress": self.pass_stress,
            "pass_leak": self.pass_leak,
            "duration_s": round(self.duration_s, 3),
            "stress": self.stress.to_dict(),
            "leak": self.leak.to_dict(),
        }


@dataclass
class LongRunReport:
    """LongRunMonitor 전체 실행 결과."""
    config: LongRunConfig
    epochs: List[EpochResult] = field(default_factory=list)
    total_duration_s: float = 0.0
    peak_memory_mb: float = 0.0

    @property
    def all_pass(self) -> bool:
        return all(e.all_pass for e in self.epochs)

    @property
    def failed_epochs(self) -> List[int]:
        return [e.epoch for e in self.epochs if not e.all_pass]

    @property
    def p95_trend(self) -> List[float]:
        """epoch별 sustained P95 레이턴시 추세."""
        return [e.stress.sustained.p95_ms for e in self.epochs]

    @property
    def leak_delta_trend(self) -> List[float]:
        """epoch별 메모리 delta_mb 추세."""
        return [e.leak.delta_mb for e in self.epochs]

    def to_dict(self) -> dict:
        return {
            "all_pass": self.all_pass,
            "total_epochs": len(self.epochs),
            "failed_epochs": self.failed_epochs,
            "total_duration_s": round(self.total_duration_s, 3),
            "peak_memory_mb": round(self.peak_memory_mb, 3),
            "p95_trend_ms": [round(v, 2) for v in self.p95_trend],
            "leak_delta_trend_mb": [round(v, 3) for v in self.leak_delta_trend],
            "epochs": [e.to_dict() for e in self.epochs],
        }


# ─────────────────────────────────────────────────────────────────────────────
# LongRunMonitor
# ─────────────────────────────────────────────────────────────────────────────

class LongRunMonitor:
    """
    MemoryLeakDetector + StressTester 통합 장기 실행 모니터.

    각 epoch에서:
      1. StressTester로 warm-up → sustained → cooldown 실행 (레이턴시 SLO 검증)
      2. MemoryLeakDetector로 baseline 대비 메모리 증가량 측정 (누수 검증)

    사용 예:
        cfg = LongRunConfig(epochs=5, target_p95_ms=1500.0, leak_threshold_mb=10.0)
        monitor = LongRunMonitor(cfg)
        report = monitor.run(lambda: my_workload())
        assert report.all_pass, f"장기 실행 실패: {report.failed_epochs}"
    """

    def __init__(self, config: Optional[LongRunConfig] = None) -> None:
        self.config = config or LongRunConfig()

    # ── 공개 API ─────────────────────────────────────────────────────────────

    def run(
        self,
        fn: Callable[[], Any],
        memory_sampler: Optional[Callable[[], float]] = None,
    ) -> LongRunReport:
        """
        fn을 config.epochs 회 반복 실행하며 메모리·레이턴시를 모니터링한다.

        Args:
            fn              : 모니터링 대상 callable
            memory_sampler  : 현재 메모리(MB)를 반환하는 callable (옵션)
        """
        cfg = self.config
        report = LongRunReport(config=cfg)
        t_start = time.perf_counter()

        # 메모리 탐지기 — 전체 실행에 걸쳐 tracemalloc 유지
        detector = MemoryLeakDetector(
            threshold_mb=cfg.leak_threshold_mb if cfg.leak_threshold_mb else 10.0
        )
        detector.start()
        global_baseline = detector.baseline()
        peak_memory: float = 0.0

        _log.info(
            "LongRunMonitor 시작 — epochs=%d, p95_slo=%.0fms, leak=%.0fMB",
            cfg.epochs,
            cfg.target_p95_ms or 0,
            cfg.leak_threshold_mb or 0,
        )

        for epoch_idx in range(cfg.epochs):
            epoch_result = self.run_epoch(
                epoch=epoch_idx + 1,
                fn=fn,
                detector=detector,
                global_baseline=global_baseline,
                memory_sampler=memory_sampler,
            )
            report.epochs.append(epoch_result)

            # 피크 메모리 추적
            epoch_mem = epoch_result.stress.peak_memory_mb
            if epoch_mem > peak_memory:
                peak_memory = epoch_mem

            _log.info(
                "Epoch %d/%d — %s | P95=%.1fms | ΔMem=%.2fMB",
                epoch_idx + 1, cfg.epochs,
                "PASS" if epoch_result.all_pass else "FAIL",
                epoch_result.stress.sustained.p95_ms,
                epoch_result.leak.delta_mb,
            )

            # epoch 사이 대기
            if cfg.sleep_between_epochs_s > 0 and epoch_idx < cfg.epochs - 1:
                time.sleep(cfg.sleep_between_epochs_s)

        detector.stop()
        report.total_duration_s = time.perf_counter() - t_start
        report.peak_memory_mb = peak_memory

        _log.info(
            "LongRunMonitor 완료 — all_pass=%s, %d/%d epochs PASS, %.1fs",
            report.all_pass,
            len(report.epochs) - len(report.failed_epochs),
            cfg.epochs,
            report.total_duration_s,
        )
        return report

    def run_epoch(
        self,
        epoch: int,
        fn: Callable[[], Any],
        detector: MemoryLeakDetector,
        global_baseline: MemorySnapshot,
        memory_sampler: Optional[Callable[[], float]] = None,
    ) -> EpochResult:
        """단일 epoch를 실행한다."""
        cfg = self.config
        t0 = time.perf_counter()

        # 1. 스트레스 테스트
        stress_cfg = StressConfig(
            warmup_iters=cfg.warmup_iters,
            sustained_iters=cfg.sustained_iters,
            cooldown_iters=cfg.cooldown_iters,
            target_p95_ms=cfg.target_p95_ms,
            target_memory_mb=cfg.memory_budget_mb,
        )
        tester = StressTester(stress_cfg)
        stress_result = tester.run(fn, memory_sampler=memory_sampler)

        # 2. 누수 체크 (global_baseline 기준 누적 증가)
        leak_report = detector.check(global_baseline)

        duration_s = time.perf_counter() - t0
        return EpochResult(
            epoch=epoch,
            stress=stress_result,
            leak=leak_report,
            duration_s=duration_s,
        )

    # ── 편의 메서드 ──────────────────────────────────────────────────────────

    @classmethod
    def quick_monitor(
        cls,
        fn: Callable[[], Any],
        epochs: int = 3,
        target_p95_ms: float = 1500.0,
        leak_threshold_mb: float = 10.0,
    ) -> LongRunReport:
        """빠른 장기 실행 모니터 (소규모 파라미터)."""
        cfg = LongRunConfig(
            epochs=epochs,
            warmup_iters=2,
            sustained_iters=5,
            cooldown_iters=1,
            target_p95_ms=target_p95_ms,
            leak_threshold_mb=leak_threshold_mb,
        )
        return cls(cfg).run(fn)

    def summary(self, report: LongRunReport) -> str:
        """LongRunReport의 텍스트 요약을 반환한다."""
        status = "PASS" if report.all_pass else "FAIL"
        lines = [
            f"LongRunMonitor {status}: {len(report.epochs) - len(report.failed_epochs)}/{len(report.epochs)} epochs PASS",
            f"  총 실행 시간: {report.total_duration_s:.1f}s",
            f"  P95 추세 (ms): {[f'{v:.1f}' for v in report.p95_trend]}",
            f"  메모리 Δ 추세 (MB): {[f'{v:.2f}' for v in report.leak_delta_trend]}",
        ]
        if report.failed_epochs:
            lines.append(f"  실패 epoch: {report.failed_epochs}")
        return "\n".join(lines)
