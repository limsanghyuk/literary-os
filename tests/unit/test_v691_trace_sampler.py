"""tests/unit/test_v691_trace_sampler.py

V691: TraceSamplingController 테스트 (33 TC).

TC-01~08: SamplingRate 값 객체
TC-09~14: SamplingStrategy + SamplingDecision
TC-15~21: TraceSampler (ALWAYS / NEVER / RATIO)
TC-22~27: AdaptiveSampler (에러율/레이턴시 기반 조정)
TC-28~33: 통합 (통계 누적, create_sampler 팩토리, 부모 컨텍스트 상속)
"""

from __future__ import annotations

import pytest

from literary_system.ops.trace_sampler import (
    SamplingRate,
    SamplingStrategy,
    SamplingDecision,
    TraceSampler,
    AdaptiveSampler,
    SpanObservation,
    create_sampler,
    DEFAULT_RATE,
)
from literary_system.ops.trace_context import TraceFlags, new_trace_context


class TestSamplingRate:

    def test_tc01_default_rate(self):
        """TC-01: 기본 샘플링 비율 DEFAULT_RATE."""
        r = SamplingRate()
        assert r.value == DEFAULT_RATE

    def test_tc02_custom_rate(self):
        """TC-02: 커스텀 비율 설정."""
        r = SamplingRate(0.5)
        assert r.value == 0.5

    def test_tc03_always(self):
        """TC-03: always() → 1.0."""
        r = SamplingRate.always()
        assert r.is_always()
        assert r.value == 1.0

    def test_tc04_never(self):
        """TC-04: never() → 0.0."""
        r = SamplingRate.never()
        assert r.is_never()
        assert r.value == 0.0

    def test_tc05_invalid_rate_negative(self):
        """TC-05: 음수 비율 → ValueError."""
        with pytest.raises(ValueError):
            SamplingRate(-0.1)

    def test_tc06_invalid_rate_above_one(self):
        """TC-06: 1.0 초과 → ValueError."""
        with pytest.raises(ValueError):
            SamplingRate(1.1)

    def test_tc07_mul_clamped(self):
        """TC-07: __mul__ 결과 0~1 범위 클램핑."""
        r = SamplingRate(0.8)
        result = r * 2.0
        assert result.value == 1.0

    def test_tc08_frozen(self):
        """TC-08: SamplingRate는 frozen dataclass — 재할당 불가."""
        r = SamplingRate(0.5)
        with pytest.raises(Exception):
            r.value = 0.9  # type: ignore


class TestSamplingStrategyAndDecision:

    def test_tc09_strategy_values(self):
        """TC-09: SamplingStrategy Enum 4종."""
        assert SamplingStrategy.ALWAYS.value == "always"
        assert SamplingStrategy.NEVER.value == "never"
        assert SamplingStrategy.RATIO.value == "ratio"
        assert SamplingStrategy.ADAPTIVE.value == "adaptive"

    def test_tc10_decision_sampled_flags(self):
        """TC-10: sampled=True → flags=SAMPLED."""
        d = SamplingDecision(
            sampled=True, rate=SamplingRate(1.0), strategy=SamplingStrategy.ALWAYS
        )
        assert d.flags == TraceFlags.SAMPLED

    def test_tc11_decision_not_sampled_flags(self):
        """TC-11: sampled=False → flags=NONE."""
        d = SamplingDecision(
            sampled=False, rate=SamplingRate(0.0), strategy=SamplingStrategy.NEVER
        )
        assert d.flags == TraceFlags.NONE

    def test_tc12_decision_has_trace_context(self):
        """TC-12: trace_context 필드 있음."""
        ctx = new_trace_context()
        d = SamplingDecision(
            sampled=True, rate=SamplingRate(1.0),
            strategy=SamplingStrategy.ALWAYS, trace_context=ctx
        )
        assert d.trace_context is ctx

    def test_tc13_decision_default_no_context(self):
        """TC-13: trace_context 기본값 None."""
        d = SamplingDecision(
            sampled=True, rate=SamplingRate(1.0), strategy=SamplingStrategy.ALWAYS
        )
        assert d.trace_context is None

    def test_tc14_sampling_strategy_from_string(self):
        """TC-14: 문자열로 SamplingStrategy 생성."""
        s = SamplingStrategy("ratio")
        assert s == SamplingStrategy.RATIO


class TestTraceSampler:

    def test_tc15_always_sampler(self):
        """TC-15: ALWAYS 전략 → 항상 sampled=True."""
        sampler = TraceSampler(strategy=SamplingStrategy.ALWAYS)
        for _ in range(10):
            d = sampler.should_sample("op")
            assert d.sampled

    def test_tc16_never_sampler(self):
        """TC-16: NEVER 전략 → 항상 sampled=False."""
        sampler = TraceSampler(strategy=SamplingStrategy.NEVER)
        for _ in range(10):
            d = sampler.should_sample("op")
            assert not d.sampled

    def test_tc17_ratio_sampler_returns_decision(self):
        """TC-17: RATIO 전략 → SamplingDecision 반환."""
        sampler = TraceSampler(strategy=SamplingStrategy.RATIO, rate=SamplingRate(0.5))
        d = sampler.should_sample("test_op")
        assert isinstance(d, SamplingDecision)

    def test_tc18_ratio_100pct(self):
        """TC-18: RATIO 1.0 → 모두 sampled."""
        sampler = TraceSampler(strategy=SamplingStrategy.RATIO, rate=SamplingRate(1.0))
        results = [sampler.should_sample() for _ in range(20)]
        assert all(r.sampled for r in results)

    def test_tc19_ratio_0pct(self):
        """TC-19: RATIO 0.0 → 모두 skip."""
        sampler = TraceSampler(strategy=SamplingStrategy.RATIO, rate=SamplingRate(0.0))
        results = [sampler.should_sample() for _ in range(20)]
        assert all(not r.sampled for r in results)

    def test_tc20_total_decisions_count(self):
        """TC-20: total_decisions 카운터 정확."""
        sampler = TraceSampler(strategy=SamplingStrategy.ALWAYS)
        for _ in range(7):
            sampler.should_sample()
        assert sampler.total_decisions == 7

    def test_tc21_update_rate(self):
        """TC-21: update_rate() 후 rate 변경."""
        sampler = TraceSampler(rate=SamplingRate(0.1))
        sampler.update_rate(SamplingRate(0.9))
        assert sampler.rate.value == 0.9


class TestAdaptiveSampler:

    def test_tc22_adaptive_init(self):
        """TC-22: AdaptiveSampler 초기화."""
        s = AdaptiveSampler(initial_rate=0.1)
        assert s.strategy == SamplingStrategy.ADAPTIVE
        assert s.rate.value == 0.1

    def test_tc23_error_increases_rate(self):
        """TC-23: 에러율 초과 → rate 증가."""
        s = AdaptiveSampler(initial_rate=0.1, error_threshold=0.05)
        init_rate = s.rate.value
        # 에러 관찰 주입 (6/10 = 60% 에러)
        for _ in range(10):
            s.observe(SpanObservation(duration_ms=10.0, is_error=True))
        assert s.rate.value > init_rate

    def test_tc24_normal_decreases_rate(self):
        """TC-24: 정상 조건 → rate 감소."""
        s = AdaptiveSampler(initial_rate=0.5, error_threshold=0.05)
        for _ in range(10):
            s.observe(SpanObservation(duration_ms=5.0, is_error=False))
        assert s.rate.value < 0.5

    def test_tc25_latency_increases_rate(self):
        """TC-25: P99 레이턴시 초과 → rate 증가."""
        s = AdaptiveSampler(initial_rate=0.1, latency_threshold_ms=100.0)
        init_rate = s.rate.value
        for _ in range(20):
            s.observe(SpanObservation(duration_ms=500.0, is_error=False))
        assert s.rate.value > init_rate

    def test_tc26_rate_clamped_by_min(self):
        """TC-26: 감소 시 min_rate 하한 유지."""
        s = AdaptiveSampler(initial_rate=0.01, min_rate=0.01)
        for _ in range(100):
            s.observe(SpanObservation(duration_ms=1.0, is_error=False))
        assert s.rate.value >= 0.01

    def test_tc27_current_error_rate(self):
        """TC-27: current_error_rate 계산."""
        s = AdaptiveSampler()
        for _ in range(5):
            s.observe(SpanObservation(duration_ms=10.0, is_error=True))
        for _ in range(5):
            s.observe(SpanObservation(duration_ms=10.0, is_error=False))
        assert abs(s.current_error_rate - 0.5) < 0.01


class TestIntegration:

    def test_tc28_stats_always_sampler(self):
        """TC-28: ALWAYS sampler — sampled_count == total."""
        s = TraceSampler(strategy=SamplingStrategy.ALWAYS)
        for _ in range(10):
            s.should_sample()
        assert s.sampled_count == 10
        assert s.skipped_count == 0

    def test_tc29_stats_never_sampler(self):
        """TC-29: NEVER sampler — skipped_count == total."""
        s = TraceSampler(strategy=SamplingStrategy.NEVER)
        for _ in range(10):
            s.should_sample()
        assert s.skipped_count == 10
        assert s.sampled_count == 0

    def test_tc30_reset_stats(self):
        """TC-30: reset_stats() 후 카운터 0."""
        s = TraceSampler(strategy=SamplingStrategy.ALWAYS)
        for _ in range(5):
            s.should_sample()
        s.reset_stats()
        assert s.total_decisions == 0

    def test_tc31_create_sampler_ratio(self):
        """TC-31: create_sampler("ratio") → TraceSampler."""
        s = create_sampler("ratio", 0.5)
        assert isinstance(s, TraceSampler)
        assert s.rate.value == 0.5

    def test_tc32_create_sampler_adaptive(self):
        """TC-32: create_sampler("adaptive") → AdaptiveSampler."""
        s = create_sampler("adaptive", 0.1)
        assert isinstance(s, AdaptiveSampler)

    def test_tc33_parent_context_sampled_inherit(self):
        """TC-33: 부모 SAMPLED 컨텍스트 → 자식도 sampled=True (상속)."""
        sampler = TraceSampler(strategy=SamplingStrategy.NEVER)  # NEVER지만 부모가 SAMPLED
        parent = new_trace_context(sampled=True)
        d = sampler.should_sample("child_op", parent_ctx=parent)
        assert d.sampled  # 부모 컨텍스트 상속으로 SAMPLED
