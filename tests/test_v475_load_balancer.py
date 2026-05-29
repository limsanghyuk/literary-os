"""
tests/test_v475_load_balancer.py
V475 — LoadBalancer(WRR-Cost) + CircuitBreaker(LLM) 테스트
"""
import pytest
from literary_system.ops.load_balancer import (
    LoadBalancer, AdapterRef, RouteResult, _compute_weight, weighted_round_robin,
)
from literary_system.ops.circuit_breaker_llm import (
    CircuitBreaker, CircuitState, CircuitBreakerOpenError,
)


# ──────────────────────────────────────────────────────────────────────────────
# AdapterRef
# ──────────────────────────────────────────────────────────────────────────────
class TestAdapterRef:
    def test_default_healthy(self):
        a = AdapterRef("ada")
        assert a.is_healthy() is True

    def test_default_cost(self):
        a = AdapterRef("ada")
        assert a.cost_estimate(None) == pytest.approx(0.01)

    def test_default_score(self):
        a = AdapterRef("ada")
        assert a.last_judge_score() == pytest.approx(1.0)

    def test_custom_health_false(self):
        a = AdapterRef("ada", health_fn=lambda: False)
        assert a.is_healthy() is False

    def test_custom_cost(self):
        a = AdapterRef("ada", cost_fn=lambda ctx: 0.05)
        assert a.cost_estimate(None) == pytest.approx(0.05)

    def test_custom_score(self):
        a = AdapterRef("ada", score_fn=lambda: 0.8)
        assert a.last_judge_score() == pytest.approx(0.8)

    def test_score_clamp_upper(self):
        a = AdapterRef("ada", score_fn=lambda: 9.9)
        assert a.last_judge_score() == pytest.approx(1.0)

    def test_score_clamp_lower(self):
        a = AdapterRef("ada", score_fn=lambda: -5.0)
        assert a.last_judge_score() == pytest.approx(0.0)

    def test_health_exception_returns_false(self):
        a = AdapterRef("ada", health_fn=lambda: 1 / 0)
        assert a.is_healthy() is False

    def test_cost_exception_returns_sentinel(self):
        a = AdapterRef("ada", cost_fn=lambda ctx: 1 / 0)
        assert a.cost_estimate(None) == pytest.approx(999.0)

    def test_hash_by_name(self):
        a1 = AdapterRef("x")
        a2 = AdapterRef("x")
        assert hash(a1) == hash(a2)
        assert a1 == a2

    def test_hash_different_names(self):
        a1 = AdapterRef("x")
        a2 = AdapterRef("y")
        assert a1 != a2


# ──────────────────────────────────────────────────────────────────────────────
# WRR-Cost 알고리즘
# ──────────────────────────────────────────────────────────────────────────────
class TestWRRCostAlgorithm:
    def test_compute_weight_high_quality_low_cost(self):
        a = AdapterRef("a", score_fn=lambda: 1.0, cost_fn=lambda ctx: 0.01)
        w = _compute_weight(a, None)
        assert w > 50  # quality²/cost ≈ 100

    def test_compute_weight_zero_quality(self):
        a = AdapterRef("a", score_fn=lambda: 0.0, cost_fn=lambda ctx: 0.01)
        w = _compute_weight(a, None)
        assert w == pytest.approx(0.0, abs=1e-5)

    def test_wrr_selects_max(self):
        items = [("a", 10.0), ("b", 50.0), ("c", 5.0)]
        assert weighted_round_robin(items) == "b"

    def test_wrr_empty_raises(self):
        with pytest.raises(ValueError):
            weighted_round_robin([])

    def test_wrr_zero_total_returns_first(self):
        items = [("a", 0.0), ("b", 0.0)]
        assert weighted_round_robin(items) == "a"


# ──────────────────────────────────────────────────────────────────────────────
# LoadBalancer
# ──────────────────────────────────────────────────────────────────────────────
class TestLoadBalancer:
    def test_register_and_count(self):
        lb = LoadBalancer()
        lb.register(AdapterRef("a"))
        assert lb.adapter_count() == 1

    def test_register_duplicate_raises(self):
        lb = LoadBalancer()
        lb.register(AdapterRef("a"))
        with pytest.raises(ValueError):
            lb.register(AdapterRef("a"))

    def test_deregister(self):
        lb = LoadBalancer()
        lb.register(AdapterRef("a"))
        assert lb.deregister("a") is True
        assert lb.adapter_count() == 0

    def test_deregister_nonexistent(self):
        lb = LoadBalancer()
        assert lb.deregister("ghost") is False

    def test_route_returns_result(self):
        lb = LoadBalancer()
        lb.register(AdapterRef("a"))
        r = lb.route()
        assert isinstance(r, RouteResult)
        assert r.adapter.name == "a"

    def test_route_no_adapters_raises(self):
        lb = LoadBalancer()
        with pytest.raises(RuntimeError):
            lb.route()

    def test_route_all_unhealthy_raises(self):
        lb = LoadBalancer()
        lb.register(AdapterRef("a", health_fn=lambda: False))
        with pytest.raises(RuntimeError):
            lb.route()

    def test_route_selects_best_weight(self):
        lb = LoadBalancer()
        lb.register(AdapterRef("cheap", score_fn=lambda: 1.0, cost_fn=lambda ctx: 0.001))
        lb.register(AdapterRef("expensive", score_fn=lambda: 1.0, cost_fn=lambda ctx: 10.0))
        r = lb.route()
        assert r.adapter.name == "cheap"

    def test_manual_weight_override(self):
        lb = LoadBalancer()
        lb.register(AdapterRef("a"))
        lb.register(AdapterRef("b"))
        lb.set_weights({"b": 9999.0})
        r = lb.route()
        assert r.adapter.name == "b"

    def test_manual_weight_zero_excluded(self):
        lb = LoadBalancer()
        lb.register(AdapterRef("a"))
        lb.register(AdapterRef("b"))
        lb.set_weights({"a": 0.0, "b": 5.0})
        r = lb.route()
        assert r.adapter.name == "b"

    def test_clear_weights_restores_wrr(self):
        lb = LoadBalancer()
        lb.register(AdapterRef("a", score_fn=lambda: 1.0, cost_fn=lambda ctx: 0.001))
        lb.register(AdapterRef("b", score_fn=lambda: 0.1, cost_fn=lambda ctx: 0.001))
        lb.set_weights({"b": 9999.0})
        lb.clear_weights()
        r = lb.route()
        assert r.adapter.name == "a"

    def test_route_count_increments(self):
        lb = LoadBalancer()
        lb.register(AdapterRef("a"))
        lb.route()
        lb.route()
        assert lb.get_stats()["route_count"]["a"] == 2

    def test_get_stats_structure(self):
        lb = LoadBalancer()
        lb.register(AdapterRef("a"))
        s = lb.get_stats()
        assert "adapters" in s
        assert "healthy" in s
        assert "route_count" in s

    def test_healthy_count(self):
        lb = LoadBalancer()
        lb.register(AdapterRef("a"))
        lb.register(AdapterRef("b", health_fn=lambda: False))
        assert lb.healthy_count() == 1


# ──────────────────────────────────────────────────────────────────────────────
# CircuitBreaker
# ──────────────────────────────────────────────────────────────────────────────
class TestCircuitBreaker:
    def test_initial_closed(self):
        cb = CircuitBreaker("cb")
        assert cb.get_state() == CircuitState.CLOSED

    def test_call_success(self):
        cb = CircuitBreaker("cb")
        assert cb.call(lambda: 42) == 42

    def test_force_open(self):
        cb = CircuitBreaker("cb")
        cb.force_open()
        assert cb.get_state() == CircuitState.OPEN

    def test_open_blocks_call(self):
        cb = CircuitBreaker("cb")
        cb.force_open()
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: 1)

    def test_force_close(self):
        cb = CircuitBreaker("cb")
        cb.force_open()
        cb.force_close()
        assert cb.get_state() == CircuitState.CLOSED

    def test_reset(self):
        cb = CircuitBreaker("cb")
        cb.force_open()
        cb.reset()
        assert cb.get_state() == CircuitState.CLOSED

    def test_failure_opens_circuit(self):
        cb = CircuitBreaker("cb", fail_rate_threshold=0.5, min_calls=4)
        for _ in range(4):
            try:
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
            except RuntimeError:
                pass
        assert cb.get_state() == CircuitState.OPEN

    def test_llm_recovery_timeout(self):
        cb = CircuitBreaker("cb", llm_recovery_timeout_s=120.0, is_llm_dependent=True)
        assert cb.llm_recovery_timeout_s == pytest.approx(120.0)
