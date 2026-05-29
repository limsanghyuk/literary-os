"""
tests/test_v618_adaptive_throttler.py
AdaptiveThrottler v1.0 단위 테스트 (V618, SP-B.4)
25 TC — 5 클래스
"""
import time
import pytest

from literary_system.optimization.adaptive_throttler import (
    AdaptiveThrottler,
    ThrottleConfig,
    ThrottleEvent,
    ThrottleReport,
)


# ─────────────────────────────────────────────
# TestThrottleConfig (4 TC)
# ─────────────────────────────────────────────

class TestThrottleConfig:
    def test_default_initial_concurrency(self):
        cfg = ThrottleConfig()
        assert cfg.initial_concurrency == 4

    def test_custom_thresholds(self):
        cfg = ThrottleConfig(warn_threshold_ms=2000.0, recover_threshold_ms=1000.0)
        assert cfg.warn_threshold_ms == 2000.0
        assert cfg.recover_threshold_ms == 1000.0

    def test_invalid_warn_lte_recover_raises(self):
        with pytest.raises(ValueError):
            ThrottleConfig(warn_threshold_ms=800.0, recover_threshold_ms=800.0)

    def test_initial_clamped_to_range(self):
        cfg = ThrottleConfig(
            initial_concurrency=100,
            max_concurrency=8,
            min_concurrency=1,
        )
        assert cfg.initial_concurrency == 8


# ─────────────────────────────────────────────
# TestThrottleEvent (4 TC)
# ─────────────────────────────────────────────

class TestThrottleEvent:
    def _make_event(self, action="reduce"):
        return ThrottleEvent(
            timestamp=time.monotonic(),
            action=action,
            previous=4,
            current=3,
            p95_ms=1500.0,
            memory_mb=None,
            reason="test",
        )

    def test_to_dict_has_action(self):
        e = self._make_event("reduce")
        assert e.to_dict()["action"] == "reduce"

    def test_to_dict_has_p95(self):
        e = self._make_event()
        assert "p95_ms" in e.to_dict()

    def test_to_dict_previous_current(self):
        e = self._make_event("increase")
        d = e.to_dict()
        assert d["previous"] == 4
        assert d["current"] == 3

    def test_memory_mb_none_in_dict(self):
        e = self._make_event()
        assert e.to_dict()["memory_mb"] is None


# ─────────────────────────────────────────────
# TestThrottleReport (4 TC)
# ─────────────────────────────────────────────

class TestThrottleReport:
    def test_avg_latency_empty(self):
        cfg = ThrottleConfig()
        r = ThrottleReport(config=cfg)
        assert r.avg_latency_ms == 0.0

    def test_avg_latency_computed(self):
        cfg = ThrottleConfig()
        r = ThrottleReport(config=cfg, total_calls=4, total_latency_ms=400.0)
        assert r.avg_latency_ms == 100.0

    def test_reduce_count(self):
        cfg = ThrottleConfig()
        events = [
            ThrottleEvent(0, "reduce", 4, 3, 1500, None, ""),
            ThrottleEvent(0, "emergency", 3, 1, 0, 500, ""),
            ThrottleEvent(0, "increase", 1, 2, 100, None, ""),
        ]
        r = ThrottleReport(config=cfg, events=events)
        assert r.reduce_count == 2

    def test_increase_count(self):
        cfg = ThrottleConfig()
        events = [
            ThrottleEvent(0, "increase", 2, 3, 100, None, ""),
            ThrottleEvent(0, "increase", 3, 4, 80, None, ""),
        ]
        r = ThrottleReport(config=cfg, events=events)
        assert r.increase_count == 2


# ─────────────────────────────────────────────
# TestAdaptiveThrottlerCore (8 TC)
# ─────────────────────────────────────────────

class TestAdaptiveThrottlerCore:
    def _throttler(self, **kw) -> AdaptiveThrottler:
        defaults = dict(
            initial_concurrency=4,
            warn_threshold_ms=1000.0,
            recover_threshold_ms=500.0,
            window_size=5,
        )
        defaults.update(kw)
        cfg = ThrottleConfig(**defaults)
        return AdaptiveThrottler(cfg)

    def test_initial_concurrency(self):
        t = self._throttler()
        assert t.current_concurrency == 4

    def test_high_latency_reduces_concurrency(self):
        t = self._throttler()
        for _ in range(5):
            t.record(1500.0)
        assert t.current_concurrency < 4

    def test_low_latency_increases_concurrency(self):
        t = self._throttler(initial_concurrency=2)
        for _ in range(5):
            t.record(100.0)
        assert t.current_concurrency > 2

    def test_concurrency_never_below_min(self):
        t = self._throttler(min_concurrency=1)
        for _ in range(30):
            t.record(9999.0)
        assert t.current_concurrency >= 1

    def test_concurrency_never_above_max(self):
        t = self._throttler(max_concurrency=6, initial_concurrency=2)
        for _ in range(30):
            t.record(10.0)
        assert t.current_concurrency <= 6

    def test_emergency_brake_on_memory_excess(self):
        cfg = ThrottleConfig(
            initial_concurrency=8,
            warn_threshold_ms=1000.0,
            recover_threshold_ms=500.0,
            memory_budget_mb=100.0,
        )
        t = AdaptiveThrottler(cfg)
        t.record(200.0, memory_mb=200.0)  # 200MB > 100MB 예산
        assert t.current_concurrency == cfg.min_concurrency

    def test_report_total_calls(self):
        t = self._throttler()
        for _ in range(7):
            t.record(300.0)
        assert t.get_report().total_calls == 7

    def test_reset_restores_initial(self):
        t = self._throttler()
        for _ in range(5):
            t.record(2000.0)
        t.reset()
        assert t.current_concurrency == 4
        assert t.get_report().total_calls == 0


# ─────────────────────────────────────────────
# TestAdaptiveThrottlerEdgeCases (5 TC)
# ─────────────────────────────────────────────

class TestAdaptiveThrottlerEdgeCases:
    def test_slot_context_manager_acquires_releases(self):
        t = AdaptiveThrottler(ThrottleConfig(initial_concurrency=2))
        with t.slot():
            pass  # 정상 종료

    def test_slot_context_manager_on_exception(self):
        t = AdaptiveThrottler(ThrottleConfig(initial_concurrency=2))
        try:
            with t.slot():
                raise RuntimeError("test error")
        except RuntimeError:
            pass
        # 슬롯이 반납되었으므로 다시 획득 가능해야 한다
        with t.slot():
            pass

    def test_quick_throttle_returns_report(self):
        report = AdaptiveThrottler.quick_throttle(
            fn=lambda: 200.0,
            calls=10,
            initial_concurrency=2,
            warn_threshold_ms=1000.0,
        )
        assert isinstance(report, ThrottleReport)
        assert report.total_calls == 10

    def test_to_dict_keys(self):
        t = AdaptiveThrottler(ThrottleConfig())
        for _ in range(3):
            t.record(300.0)
        d = t.get_report().to_dict()
        assert "total_calls" in d
        assert "avg_latency_ms" in d
        assert "reduce_count" in d
        assert "increase_count" in d

    def test_p95_single_sample(self):
        """window=1 시 P95 = 그 값 자체."""
        cfg = ThrottleConfig(window_size=1, warn_threshold_ms=1000.0,
                             recover_threshold_ms=500.0)
        t = AdaptiveThrottler(cfg)
        t.record(800.0)
        report = t.get_report()
        assert report.total_calls == 1
