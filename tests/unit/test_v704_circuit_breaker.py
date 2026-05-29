"""V704 — AgentCircuitBreaker 테스트 (33 TC)."""
import time, pytest
from literary_system.agents.circuit_breaker import (
    AgentCircuitBreaker, CircuitState, CircuitBreakerConfig,
    CircuitBreakerError, ADR_166,
)


def make_cb(failure_threshold=3, success_threshold=2, timeout=30.0) -> AgentCircuitBreaker:
    cfg = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        success_threshold=success_threshold,
        timeout_seconds=timeout,
    )
    return AgentCircuitBreaker(name="test-cb", config=cfg)


def ok() -> str:
    return "ok"


def fail() -> None:
    raise ValueError("fail")


# ══════════════════════════════════════════════════════════════════════
class TestCircuitBreakerBasics:
    def test_tc01_initial_state_closed(self):
        cb = make_cb()
        assert cb.state == CircuitState.CLOSED
        assert cb.is_closed()

    def test_tc02_successful_call_returns_value(self):
        cb = make_cb()
        result = cb.call(ok)
        assert result == "ok"

    def test_tc03_failure_increments_count(self):
        cb = make_cb(failure_threshold=5)
        try: cb.call(fail)
        except ValueError: pass
        assert cb._consecutive_failures == 1

    def test_tc04_trips_after_threshold(self):
        cb = make_cb(failure_threshold=3)
        for _ in range(3):
            try: cb.call(fail)
            except ValueError: pass
        assert cb.state == CircuitState.OPEN

    def test_tc05_open_rejects_immediately(self):
        cb = make_cb(failure_threshold=1)
        try: cb.call(fail)
        except ValueError: pass
        with pytest.raises(CircuitBreakerError):
            cb.call(ok)

    def test_tc06_stats_rejected(self):
        cb = make_cb(failure_threshold=1)
        try: cb.call(fail)
        except ValueError: pass
        try: cb.call(ok)
        except CircuitBreakerError: pass
        st = cb.stats()
        assert st["rejected_calls"] == 1

    def test_tc07_open_to_half_open_after_timeout(self):
        cb = make_cb(failure_threshold=1, timeout=0.01)
        try: cb.call(fail)
        except ValueError: pass
        assert cb._state == CircuitState.OPEN
        time.sleep(0.02)
        # 다음 state 접근 시 HALF_OPEN으로 전환
        assert cb.state == CircuitState.HALF_OPEN

    def test_tc08_half_open_success_counts(self):
        cb = make_cb(failure_threshold=1, success_threshold=2, timeout=0.01)
        try: cb.call(fail)
        except ValueError: pass
        time.sleep(0.02)
        cb.call(ok)  # HALF_OPEN에서 성공 1
        assert cb.state == CircuitState.HALF_OPEN  # 아직 1개 성공 부족
        cb.call(ok)  # 성공 2 → CLOSED
        assert cb.state == CircuitState.CLOSED

    def test_tc09_half_open_failure_reopens(self):
        cb = make_cb(failure_threshold=1, success_threshold=2, timeout=0.01)
        try: cb.call(fail)
        except ValueError: pass
        time.sleep(0.02)
        # HALF_OPEN에서 실패
        try: cb.call(fail)
        except ValueError: pass
        assert cb._state == CircuitState.OPEN

    def test_tc10_reset_closes_immediately(self):
        cb = make_cb(failure_threshold=1)
        try: cb.call(fail)
        except ValueError: pass
        assert cb._state == CircuitState.OPEN
        cb.reset()
        assert cb.state == CircuitState.CLOSED

    def test_tc11_trip_opens_immediately(self):
        cb = make_cb()
        cb.trip()
        assert cb._state == CircuitState.OPEN

    def test_tc12_success_resets_failure_count(self):
        cb = make_cb(failure_threshold=3)
        try: cb.call(fail)
        except ValueError: pass
        assert cb._consecutive_failures == 1
        cb.call(ok)
        assert cb._consecutive_failures == 0

    def test_tc13_stats_failure_rate(self):
        cb = make_cb(failure_threshold=10)
        cb.call(ok); cb.call(ok)
        try: cb.call(fail)
        except ValueError: pass
        st = cb.stats()
        assert abs(st["failure_rate"] - 1/3) < 0.01

    def test_tc14_stats_state_changes(self):
        cb = make_cb(failure_threshold=1, timeout=0.01)
        try: cb.call(fail)
        except ValueError: pass
        assert cb.stats()["state_changes"] >= 1

    def test_tc15_is_open_helper(self):
        cb = make_cb(failure_threshold=1)
        try: cb.call(fail)
        except ValueError: pass
        assert cb.is_open()

    def test_tc16_is_half_open_helper(self):
        cb = make_cb(failure_threshold=1, timeout=0.01)
        try: cb.call(fail)
        except ValueError: pass
        time.sleep(0.02)
        _ = cb.state  # trigger transition
        assert cb.is_half_open()

    def test_tc17_state_changed_hook(self):
        cb = make_cb(failure_threshold=1)
        transitions = []
        cb.on("state_changed", lambda p: transitions.append((p["from"], p["to"])))
        try: cb.call(fail)
        except ValueError: pass
        assert len(transitions) >= 1

    def test_tc18_success_hook(self):
        cb = make_cb()
        fired = []
        cb.on("success", lambda _: fired.append(True))
        cb.call(ok)
        assert fired == [True]

    def test_tc19_failure_hook(self):
        cb = make_cb(failure_threshold=10)
        fired = []
        cb.on("failure", lambda _: fired.append(True))
        try: cb.call(fail)
        except ValueError: pass
        assert fired == [True]

    def test_tc20_circuit_breaker_error_not_counted_as_failure(self):
        cb = make_cb(failure_threshold=1)
        try: cb.call(fail)
        except ValueError: pass
        initial_failures = cb._stats.failure_calls
        try: cb.call(ok)  # rejected
        except CircuitBreakerError: pass
        assert cb._stats.failure_calls == initial_failures

    def test_tc21_multiple_successes_in_half_open(self):
        cb = make_cb(failure_threshold=1, success_threshold=3, timeout=0.01)
        try: cb.call(fail)
        except ValueError: pass
        time.sleep(0.02)
        cb.call(ok); cb.call(ok)  # 2 successes
        assert cb.is_half_open()  # still needs 1 more
        cb.call(ok)               # 3rd success
        assert cb.is_closed()

    def test_tc22_no_trip_below_threshold(self):
        cb = make_cb(failure_threshold=5)
        for _ in range(4):
            try: cb.call(fail)
            except ValueError: pass
        assert cb.is_closed()

    def test_tc23_stats_total_calls(self):
        cb = make_cb()
        cb.call(ok); cb.call(ok)
        try: cb.call(fail)
        except ValueError: pass
        assert cb.stats()["total_calls"] == 3

    def test_tc24_name_preserved(self):
        cb = AgentCircuitBreaker(name="my-cb")
        assert cb.name == "my-cb"
        assert cb.stats()["name"] == "my-cb"

    def test_tc25_default_config(self):
        cb = AgentCircuitBreaker()
        cfg = cb._config
        assert cfg.failure_threshold == 5
        assert cfg.success_threshold == 2
        assert cfg.timeout_seconds == 30.0

    def test_tc26_rapid_open_close_cycle(self):
        cb = make_cb(failure_threshold=1, success_threshold=1, timeout=0.01)
        # Trip
        try: cb.call(fail)
        except ValueError: pass
        time.sleep(0.02)
        # Recover
        cb.call(ok)
        assert cb.is_closed()
        # Trip again
        try: cb.call(fail)
        except ValueError: pass
        assert cb.is_open()

    def test_tc27_stats_in_closed_state(self):
        cb = make_cb()
        st = cb.stats()
        assert st["state"] == "closed"
        assert st["total_calls"] == 0

    def test_tc28_manual_trip_then_reset(self):
        cb = make_cb()
        cb.trip()
        assert cb.is_open()
        cb.reset()
        assert cb.is_closed()
        assert cb._consecutive_failures == 0

    def test_tc29_consecutive_resets_safe(self):
        cb = make_cb()
        cb.reset(); cb.reset()
        assert cb.is_closed()

    def test_tc30_exceptions_propagate(self):
        cb = make_cb(failure_threshold=10)
        with pytest.raises(ValueError, match="fail"):
            cb.call(fail)

    def test_tc31_circuit_closed_after_consecutive_success_threshold(self):
        cb = make_cb(failure_threshold=2, success_threshold=2, timeout=0.01)
        # Open
        try: cb.call(fail)
        except: pass
        try: cb.call(fail)
        except: pass
        time.sleep(0.02)
        # 2 successes in HALF_OPEN → CLOSED
        cb.call(ok); cb.call(ok)
        assert cb.is_closed()

    def test_tc32_failure_rate_zero_initially(self):
        cb = make_cb()
        assert cb._stats.failure_rate() == 0.0

    def test_tc33_adr_166(self):
        assert ADR_166["id"] == "ADR-166"
        assert ADR_166["status"] == "accepted"
        assert "CircuitBreaker" in ADR_166["title"]
