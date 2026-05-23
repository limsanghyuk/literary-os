"""
StressTester v1.0 — Literary OS SP-B.4 (V616)

SLO 조건 하에서 임의 callable을 반복 실행하는 스트레스 테스트 프레임워크.
warm-up → sustained → cooldown 3단계 구조.

주요 클래스:
  - StressConfig  : 테스트 파라미터 설정
  - PhaseResult   : 단일 페이즈 실행 결과 (latencies, p50/p95/p99, pass 여부)
  - StressResult  : 전체 3단계 결과 집계
  - StressTester  : 공개 API (run / run_phase)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

__all__ = [
    "StressConfig",
    "PhaseResult",
    "StressResult",
    "StressTester",
]

_log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 설정 클래스
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class StressConfig:
    """
    StressTester 설정.

    Attributes:
        warmup_iters      : 워밍업 반복 횟수 (SLO 판정 제외)
        sustained_iters   : 본 실행 반복 횟수 (SLO 판정 포함)
        cooldown_iters    : 쿨다운 반복 횟수 (SLO 판정 제외)
        target_p95_ms     : P95 레이턴시 SLO (ms). None이면 체크 생략
        target_p99_ms     : P99 레이턴시 SLO (ms). None이면 체크 생략
        target_memory_mb  : 피크 메모리 SLO (MB). None이면 체크 생략
        sleep_between_ms  : 반복 사이 대기 시간 (ms). 0 = 대기 없음
    """
    warmup_iters: int = 5
    sustained_iters: int = 20
    cooldown_iters: int = 3
    target_p95_ms: Optional[float] = 1500.0
    target_p99_ms: Optional[float] = None
    target_memory_mb: Optional[float] = None
    sleep_between_ms: float = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 결과 클래스
# ─────────────────────────────────────────────────────────────────────────────

def _percentile(data: List[float], pct: float) -> float:
    """정렬된 리스트에서 백분위수를 반환한다 (선형 보간)."""
    if not data:
        return 0.0
    sorted_d = sorted(data)
    idx = (len(sorted_d) - 1) * pct / 100.0
    lo = int(idx)
    hi = lo + 1
    if hi >= len(sorted_d):
        return sorted_d[-1]
    frac = idx - lo
    return sorted_d[lo] * (1 - frac) + sorted_d[hi] * frac


@dataclass
class PhaseResult:
    """단일 페이즈 실행 결과."""
    phase: str                          # "warmup" | "sustained" | "cooldown"
    iterations: int
    latencies_ms: List[float] = field(default_factory=list)
    errors: int = 0

    @property
    def p50_ms(self) -> float:
        return _percentile(self.latencies_ms, 50)

    @property
    def p95_ms(self) -> float:
        return _percentile(self.latencies_ms, 95)

    @property
    def p99_ms(self) -> float:
        return _percentile(self.latencies_ms, 99)

    @property
    def mean_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        return sum(self.latencies_ms) / len(self.latencies_ms)

    @property
    def success_rate(self) -> float:
        total = len(self.latencies_ms) + self.errors
        if total == 0:
            return 1.0
        return len(self.latencies_ms) / total

    def meets_p95_slo(self, target_ms: float) -> bool:
        return self.p95_ms <= target_ms

    def meets_p99_slo(self, target_ms: float) -> bool:
        return self.p99_ms <= target_ms

    def to_dict(self) -> dict:
        return {
            "phase": self.phase,
            "iterations": self.iterations,
            "success_count": len(self.latencies_ms),
            "error_count": self.errors,
            "success_rate": round(self.success_rate, 4),
            "p50_ms": round(self.p50_ms, 2),
            "p95_ms": round(self.p95_ms, 2),
            "p99_ms": round(self.p99_ms, 2),
            "mean_ms": round(self.mean_ms, 2),
        }


@dataclass
class StressResult:
    """3단계 스트레스 테스트 전체 결과."""
    config: StressConfig
    warmup: PhaseResult
    sustained: PhaseResult
    cooldown: PhaseResult
    peak_memory_mb: float = 0.0
    slo_p95_pass: bool = True
    slo_p99_pass: bool = True
    slo_memory_pass: bool = True

    @property
    def all_pass(self) -> bool:
        return self.slo_p95_pass and self.slo_p99_pass and self.slo_memory_pass

    def to_dict(self) -> dict:
        return {
            "all_pass": self.all_pass,
            "slo_p95_pass": self.slo_p95_pass,
            "slo_p99_pass": self.slo_p99_pass,
            "slo_memory_pass": self.slo_memory_pass,
            "peak_memory_mb": round(self.peak_memory_mb, 3),
            "warmup": self.warmup.to_dict(),
            "sustained": self.sustained.to_dict(),
            "cooldown": self.cooldown.to_dict(),
            "target_p95_ms": self.config.target_p95_ms,
            "target_p99_ms": self.config.target_p99_ms,
            "target_memory_mb": self.config.target_memory_mb,
        }


# ─────────────────────────────────────────────────────────────────────────────
# StressTester
# ─────────────────────────────────────────────────────────────────────────────

class StressTester:
    """
    SLO 기반 스트레스 테스트 실행기.

    사용 예:
        config = StressConfig(sustained_iters=50, target_p95_ms=1500.0)
        tester = StressTester(config)
        result = tester.run(lambda: my_function())
        assert result.all_pass, f"SLO 위반: {result.to_dict()}"
    """

    def __init__(self, config: Optional[StressConfig] = None) -> None:
        self.config = config or StressConfig()

    # ── 공개 API ─────────────────────────────────────────────────────────────

    def run(
        self,
        fn: Callable[[], Any],
        memory_sampler: Optional[Callable[[], float]] = None,
    ) -> StressResult:
        """
        fn을 warm-up → sustained → cooldown 3단계로 반복 실행한다.

        Args:
            fn              : 스트레스 테스트 대상 callable
            memory_sampler  : 현재 메모리 사용량(MB)을 반환하는 callable.
                              None이면 피크 메모리 = 0 으로 기록.
        """
        cfg = self.config
        peak_memory: float = 0.0

        def _sample_memory() -> float:
            if memory_sampler:
                mb = memory_sampler()
                return mb if isinstance(mb, (int, float)) else 0.0
            return 0.0

        _log.info(
            "StressTester 시작 — warm=%d / sustained=%d / cooldown=%d",
            cfg.warmup_iters, cfg.sustained_iters, cfg.cooldown_iters,
        )

        warmup = self.run_phase("warmup", fn, cfg.warmup_iters, cfg.sleep_between_ms)
        peak_memory = max(peak_memory, _sample_memory())

        sustained = self.run_phase("sustained", fn, cfg.sustained_iters, cfg.sleep_between_ms)
        peak_memory = max(peak_memory, _sample_memory())

        cooldown = self.run_phase("cooldown", fn, cfg.cooldown_iters, cfg.sleep_between_ms)
        peak_memory = max(peak_memory, _sample_memory())

        # SLO 판정 (sustained 단계 기준)
        slo_p95_pass = True
        if cfg.target_p95_ms is not None:
            slo_p95_pass = sustained.meets_p95_slo(cfg.target_p95_ms)

        slo_p99_pass = True
        if cfg.target_p99_ms is not None:
            slo_p99_pass = sustained.meets_p99_slo(cfg.target_p99_ms)

        slo_memory_pass = True
        if cfg.target_memory_mb is not None:
            slo_memory_pass = peak_memory <= cfg.target_memory_mb

        result = StressResult(
            config=cfg,
            warmup=warmup,
            sustained=sustained,
            cooldown=cooldown,
            peak_memory_mb=peak_memory,
            slo_p95_pass=slo_p95_pass,
            slo_p99_pass=slo_p99_pass,
            slo_memory_pass=slo_memory_pass,
        )

        _log.info(
            "StressTester 완료 — all_pass=%s, P95=%.1fms, peak_mem=%.2fMB",
            result.all_pass, sustained.p95_ms, peak_memory,
        )
        return result

    def run_phase(
        self,
        phase: str,
        fn: Callable[[], Any],
        iters: int,
        sleep_ms: float = 0.0,
    ) -> PhaseResult:
        """단일 페이즈를 실행하고 PhaseResult를 반환한다."""
        result = PhaseResult(phase=phase, iterations=iters)
        sleep_s = sleep_ms / 1000.0

        for i in range(iters):
            try:
                t0 = time.perf_counter()
                fn()
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                result.latencies_ms.append(elapsed_ms)
            except Exception as exc:  # noqa: BLE001
                result.errors += 1
                _log.warning("[%s] iter %d 실패: %s", phase, i, exc)

            if sleep_s > 0 and i < iters - 1:
                time.sleep(sleep_s)

        _log.debug(
            "[%s] 완료 — p95=%.1fms, p99=%.1fms, errors=%d",
            phase, result.p95_ms, result.p99_ms, result.errors,
        )
        return result

    # ── 편의 메서드 ──────────────────────────────────────────────────────────

    @classmethod
    def quick_stress(
        cls,
        fn: Callable[[], Any],
        warmup: int = 3,
        iters: int = 10,
        target_p95_ms: float = 1500.0,
    ) -> StressResult:
        """빠른 스트레스 테스트 (기본 파라미터)."""
        cfg = StressConfig(
            warmup_iters=warmup,
            sustained_iters=iters,
            cooldown_iters=2,
            target_p95_ms=target_p95_ms,
        )
        return cls(cfg).run(fn)
