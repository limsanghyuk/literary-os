"""
tests/test_v479_gate20_production_launch.py
V479 — ProductionLaunchGate + Gate20 통합 테스트
"""
import pytest
from literary_system.ops.production_launch_gate import (
    ProductionLaunchGate, LaunchReport, SLAAxis,
)
from literary_system.gates.gate20_sp5_ops import _gate_sp5_ops


# ──────────────────────────────────────────────────────────────────────────────
# SLAAxis
# ──────────────────────────────────────────────────────────────────────────────
class TestSLAAxis:
    def test_lt_pass(self):
        ax = SLAAxis("test", metric=1.0, target=2.0, pass_if="lt")
        assert ax.passed is True

    def test_lt_fail(self):
        ax = SLAAxis("test", metric=3.0, target=2.0, pass_if="lt")
        assert ax.passed is False

    def test_lte_boundary(self):
        ax = SLAAxis("test", metric=2.0, target=2.0, pass_if="lte")
        assert ax.passed is True

    def test_gte_pass(self):
        ax = SLAAxis("test", metric=99.5, target=99.0, pass_if="gte")
        assert ax.passed is True

    def test_gte_fail(self):
        ax = SLAAxis("test", metric=98.0, target=99.0, pass_if="gte")
        assert ax.passed is False

    def test_to_dict_keys(self):
        ax = SLAAxis("p95", metric=1000.0, target=3000.0, pass_if="lt", unit="ms")
        d = ax.to_dict()
        assert "name" in d
        assert "metric" in d
        assert "target" in d
        assert "passed" in d


# ──────────────────────────────────────────────────────────────────────────────
# ProductionLaunchGate
# ──────────────────────────────────────────────────────────────────────────────
class TestProductionLaunchGate:
    def test_run_full_check_returns_report(self):
        gate = ProductionLaunchGate()
        r = gate.run_full_check()
        assert isinstance(r, LaunchReport)

    def test_default_mock_all_pass(self):
        gate = ProductionLaunchGate()
        r = gate.run_full_check()
        assert r.all_passed is True

    def test_approve_launch_default(self):
        gate = ProductionLaunchGate()
        assert gate.approve_launch() is True

    def test_run_full_check_five_axes(self):
        gate = ProductionLaunchGate()
        r = gate.run_full_check()
        assert len(r.axes) == 5

    def test_sla_targets_present(self):
        assert "p95_ms" in ProductionLaunchGate.SLA_TARGETS
        assert "availability_pct" in ProductionLaunchGate.SLA_TARGETS
        assert "rpo_s" in ProductionLaunchGate.SLA_TARGETS
        assert "rto_s" in ProductionLaunchGate.SLA_TARGETS
        assert "hallucination_rate" in ProductionLaunchGate.SLA_TARGETS

    def test_custom_metric_fail(self):
        gate = ProductionLaunchGate(metric_fn=lambda: {
            "p95_ms": 9999.0,        # FAIL: > 3000
            "availability_pct": 99.5,
            "rpo_s": 900.0,
            "rto_s": 7200.0,
            "hallucination_rate": 0.02,
        })
        r = gate.run_full_check()
        assert r.all_passed is False
        assert len(r.notes) > 0

    def test_notes_empty_on_pass(self):
        gate = ProductionLaunchGate()
        r = gate.run_full_check()
        assert r.notes == []

    def test_summary_contains_pass(self):
        gate = ProductionLaunchGate()
        r = gate.run_full_check()
        assert "PASS" in r.summary()

    def test_gate_check_injection(self):
        gate = ProductionLaunchGate(
            gate_check_fns={"custom_check": lambda: True}
        )
        r = gate.run_full_check()
        assert "custom_check" in r.gate_checks
        assert r.gate_checks["custom_check"] is True

    def test_gate_check_fail_overrides_launch(self):
        gate = ProductionLaunchGate(
            gate_check_fns={"blocker": lambda: False}
        )
        r = gate.run_full_check()
        assert r.all_passed is False

    def test_sla_p95_target_3000(self):
        target, pass_if, _, _ = ProductionLaunchGate.SLA_TARGETS["p95_ms"]
        assert target == pytest.approx(3000.0)
        assert pass_if == "lt"

    def test_sla_availability_target_99(self):
        target, pass_if, _, _ = ProductionLaunchGate.SLA_TARGETS["availability_pct"]
        assert target == pytest.approx(99.0)
        assert pass_if == "gte"


# ──────────────────────────────────────────────────────────────────────────────
# Gate20 통합
# ──────────────────────────────────────────────────────────────────────────────
class TestGate20Integration:
    def test_gate20_passes_all_7_symbols(self):
        result = _gate_sp5_ops()
        assert result["pass"] is True

    def test_gate20_symbols_checked_7(self):
        result = _gate_sp5_ops()
        assert result["symbols_checked"] == 7

    def test_gate20_symbols_passed_7(self):
        result = _gate_sp5_ops()
        assert result["symbols_passed"] == 7

    def test_gate20_no_issues(self):
        result = _gate_sp5_ops()
        assert result["issues"] == []

    def test_gate20_load_balancer_ok(self):
        result = _gate_sp5_ops()
        assert result["results"]["LoadBalancer"] == "ok"

    def test_gate20_circuit_breaker_ok(self):
        result = _gate_sp5_ops()
        assert result["results"]["CircuitBreaker"] == "ok"

    def test_gate20_observability_ok(self):
        result = _gate_sp5_ops()
        assert result["results"]["ObservabilityStack"] == "ok"

    def test_gate20_dr_controller_ok(self):
        result = _gate_sp5_ops()
        assert result["results"]["DRController"] == "ok"

    def test_gate20_production_launch_ok(self):
        result = _gate_sp5_ops()
        assert result["results"]["ProductionLaunchGate"] == "ok"

    def test_gate20_user_onboarding_ok(self):
        result = _gate_sp5_ops()
        assert result["results"]["UserOnboarding"] == "ok"

    def test_gate20_analytics_dashboard_ok(self):
        result = _gate_sp5_ops()
        assert result["results"]["AnalyticsDashboard"] == "ok"
