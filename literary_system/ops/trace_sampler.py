"""literary_system/ops/trace_sampler.py

V691: TraceSamplingController — OTel span 샘플링 레이트 동적 제어.

설계 원칙:
  LLM-0: 외부 LLM 호출 없음.
  G32: print() 금지 — logger 전용.
  D-M-02: TraceContext.flags(SAMPLED) 기반 샘플링 결정.

컴포넌트:
  SamplingRate      — 0.0~1.0 샘플링 비율 값 객체
  SamplingStrategy  — 샘플링 전략 Enum (ALWAYS / NEVER / RATIO / ADAPTIVE)
  SamplingDecision  — SAMPLED / NOT_SAMPLED 결정 dataclass
  TraceSampler      — 전략별 샘플링 결정 + 통계 수집
  AdaptiveSampler   — 에러율·레이턴시 기반 자동 비율 조정
"""

from __future__ import annotations

import logging
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from literary_system.ops.trace_context import TraceContext, TraceFlags, new_trace_context

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# 상수
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_RATE: float = 0.1       # 기본 10% 샘플링
MAX_RATE: float = 1.0
MIN_RATE: float = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# SamplingRate 값 객체
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SamplingRate:
    """0.0~1.0 사이 샘플링 비율 값 객체."""

    value: float = DEFAULT_RATE

    def __post_init__(self) -> None:
        if not (MIN_RATE <= self.value <= MAX_RATE):
            raise ValueError(
                f"SamplingRate.value={self.value!r} must be in [0.0, 1.0]"
            )

    def __mul__(self, other: float) -> "SamplingRate":
        return SamplingRate(max(MIN_RATE, min(MAX_RATE, self.value * other)))

    @classmethod
    def always(cls) -> "SamplingRate":
        return cls(1.0)

    @classmethod
    def never(cls) -> "SamplingRate":
        return cls(0.0)

    def is_always(self) -> bool:
        return self.value >= 1.0

    def is_never(self) -> bool:
        return self.value <= 0.0


# ─────────────────────────────────────────────────────────────────────────────
# SamplingStrategy Enum
# ─────────────────────────────────────────────────────────────────────────────

class SamplingStrategy(str, Enum):
    ALWAYS   = "always"    # 항상 샘플링
    NEVER    = "never"     # 항상 스킵
    RATIO    = "ratio"     # 고정 비율 샘플링
    ADAPTIVE = "adaptive"  # 에러율·지연시간 기반 자동 조정


# ─────────────────────────────────────────────────────────────────────────────
# SamplingDecision
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SamplingDecision:
    """샘플링 결정 결과."""

    sampled: bool
    rate: SamplingRate
    strategy: SamplingStrategy
    trace_context: Optional[TraceContext] = None

    @property
    def flags(self) -> TraceFlags:
        return TraceFlags.SAMPLED if self.sampled else TraceFlags.NONE


# ─────────────────────────────────────────────────────────────────────────────
# TraceSampler
# ─────────────────────────────────────────────────────────────────────────────

class TraceSampler:
    """전략별 샘플링 결정 + 통계 수집.

    사용 예::

        sampler = TraceSampler(
            strategy=SamplingStrategy.RATIO,
            rate=SamplingRate(0.1),
        )
        decision = sampler.should_sample("generate_chapter")
        if decision.sampled:
            # span 생성
            ...
    """

    def __init__(
        self,
        strategy: SamplingStrategy = SamplingStrategy.RATIO,
        rate: Optional[SamplingRate] = None,
    ) -> None:
        self.strategy = strategy
        self.rate = rate or SamplingRate(DEFAULT_RATE)
        self._total: int = 0
        self._sampled_count: int = 0
        self._skipped_count: int = 0
        logger.info(
            "[TraceSampler] 초기화 — strategy=%s rate=%.3f",
            strategy.value, self.rate.value,
        )

    # ── 공개 API ──────────────────────────────────────────────────────────────

    def should_sample(
        self,
        operation_name: str = "",
        parent_ctx: Optional[TraceContext] = None,
    ) -> SamplingDecision:
        """샘플링 여부 결정.

        Args:
            operation_name: 작업 이름 (힌트용, 현재는 미사용)
            parent_ctx: 부모 TraceContext (ALWAYS/NEVER 상속 가능)

        Returns:
            SamplingDecision
        """
        self._total += 1

        # 부모 컨텍스트가 있으면 부모 결정 상속 (tail sampling 방지)
        if parent_ctx is not None and parent_ctx.is_valid():
            sampled = parent_ctx.is_sampled()
            ctx = parent_ctx
        else:
            sampled = self._decide()
            flags = TraceFlags.SAMPLED if sampled else TraceFlags.NONE
            ctx = new_trace_context(sampled=sampled)

        if sampled:
            self._sampled_count += 1
        else:
            self._skipped_count += 1

        decision = SamplingDecision(
            sampled=sampled,
            rate=self.rate,
            strategy=self.strategy,
            trace_context=ctx,
        )
        logger.debug(
            "[TraceSampler] %s → %s (rate=%.3f)",
            operation_name or "?", "SAMPLED" if sampled else "SKIP", self.rate.value,
        )
        return decision

    def update_rate(self, new_rate: SamplingRate) -> None:
        """샘플링 비율 동적 갱신."""
        old = self.rate
        self.rate = new_rate
        logger.info(
            "[TraceSampler] rate 갱신 %.3f → %.3f", old.value, new_rate.value
        )

    # ── 통계 ─────────────────────────────────────────────────────────────────

    @property
    def total_decisions(self) -> int:
        return self._total

    @property
    def sampled_count(self) -> int:
        return self._sampled_count

    @property
    def skipped_count(self) -> int:
        return self._skipped_count

    @property
    def effective_rate(self) -> float:
        """실제 샘플링 비율 (0이면 0.0)."""
        if self._total == 0:
            return 0.0
        return self._sampled_count / self._total

    def reset_stats(self) -> None:
        self._total = 0
        self._sampled_count = 0
        self._skipped_count = 0

    # ── 내부 ─────────────────────────────────────────────────────────────────

    def _decide(self) -> bool:
        if self.strategy == SamplingStrategy.ALWAYS:
            return True
        if self.strategy == SamplingStrategy.NEVER:
            return False
        # RATIO: 0~1 uniform 랜덤과 비교
        rand_bytes = secrets.token_bytes(4)
        rand_val = int.from_bytes(rand_bytes, "big") / 0xFFFFFFFF
        return rand_val < self.rate.value


# ─────────────────────────────────────────────────────────────────────────────
# AdaptiveSampler
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SpanObservation:
    """Span 완료 후 관찰 데이터."""
    duration_ms: float
    is_error: bool
    timestamp: float = field(default_factory=time.monotonic)


class AdaptiveSampler(TraceSampler):
    """에러율·레이턴시 기반 자동 샘플링 비율 조정.

    - 에러율 > error_threshold → rate 증가 (더 많이 샘플링)
    - P99 latency > latency_threshold_ms → rate 증가
    - 정상 조건 → rate 감소 (비용 절감)
    """

    def __init__(
        self,
        initial_rate: float = DEFAULT_RATE,
        error_threshold: float = 0.05,        # 5% 에러율 초과 시 rate 증가
        latency_threshold_ms: float = 200.0,  # 200ms 초과 시 rate 증가
        min_rate: float = 0.01,
        max_rate: float = 1.0,
        window_size: int = 100,               # 최근 N개 span 기반 조정
    ) -> None:
        super().__init__(
            strategy=SamplingStrategy.ADAPTIVE,
            rate=SamplingRate(initial_rate),
        )
        self.error_threshold = error_threshold
        self.latency_threshold_ms = latency_threshold_ms
        self._min_rate = min_rate
        self._max_rate = max_rate
        self._window_size = window_size
        self._observations: List[SpanObservation] = []

    def observe(self, obs: SpanObservation) -> None:
        """Span 결과를 관찰하고 샘플링 비율을 자동 조정."""
        self._observations.append(obs)
        if len(self._observations) > self._window_size:
            self._observations = self._observations[-self._window_size:]
        self._adjust_rate()

    def _adjust_rate(self) -> None:
        """에러율 + P99 레이턴시 기반 rate 조정."""
        if not self._observations:
            return

        n = len(self._observations)
        error_count = sum(1 for o in self._observations if o.is_error)
        error_rate = error_count / n

        durations = sorted(o.duration_ms for o in self._observations)
        p99_idx = max(0, int(n * 0.99) - 1)
        p99_ms = durations[p99_idx]

        if error_rate > self.error_threshold or p99_ms > self.latency_threshold_ms:
            # 문제 감지 → rate 증가 (최대 두 배, max_rate 상한)
            new_val = min(self._max_rate, self.rate.value * 2.0)
            logger.warning(
                "[AdaptiveSampler] 이상 감지 — error_rate=%.2f%% p99=%.1fms → rate %.3f→%.3f",
                error_rate * 100, p99_ms, self.rate.value, new_val,
            )
        else:
            # 정상 → rate 감소 (90%, min_rate 하한)
            new_val = max(self._min_rate, self.rate.value * 0.9)
            logger.debug(
                "[AdaptiveSampler] 정상 → rate %.3f→%.3f",
                self.rate.value, new_val,
            )
        self.update_rate(SamplingRate(new_val))

    @property
    def current_error_rate(self) -> float:
        if not self._observations:
            return 0.0
        return sum(1 for o in self._observations if o.is_error) / len(self._observations)

    @property
    def window_p99_ms(self) -> float:
        if not self._observations:
            return 0.0
        durations = sorted(o.duration_ms for o in self._observations)
        n = len(durations)
        idx = max(0, int(n * 0.99) - 1)
        return durations[idx]


# ─────────────────────────────────────────────────────────────────────────────
# 팩토리
# ─────────────────────────────────────────────────────────────────────────────

def create_sampler(
    strategy: str = "ratio",
    rate: float = DEFAULT_RATE,
) -> TraceSampler:
    """TraceSampler 팩토리."""
    strat = SamplingStrategy(strategy)
    if strat == SamplingStrategy.ADAPTIVE:
        return AdaptiveSampler(initial_rate=rate)
    return TraceSampler(strategy=strat, rate=SamplingRate(rate))
