"""
V450 테스트: ExternalConstraintMonitor + SubPhase 4 통합 테스트
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from literary_system.quality.external_constraint_monitor import (
    ExternalConstraintMonitor,
    ConstraintEvent,
    ConstraintCheckResult,
    DEFAULT_CONSTRAINTS,
)


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture
def monitor():
    return ExternalConstraintMonitor()


@pytest.fixture
def strict_monitor():
    return ExternalConstraintMonitor(constraints={"token_limit": 1000, "cost_budget": 0.1})


# ──────────────────────────────────────────────
# TestExternalConstraintMonitorInit
# ──────────────────────────────────────────────

class TestExternalConstraintMonitorInit:
    def test_default_constraints(self, monitor):
        assert "token_limit" in monitor.constraints
        assert "cost_budget" in monitor.constraints
        assert "response_time" in monitor.constraints

    def test_custom_constraints(self):
        mon = ExternalConstraintMonitor(constraints={"custom": 5.0})
        assert "custom" in mon.constraints
        assert mon.constraints["custom"] == 5.0

    def test_alert_fn_none_by_default(self, monitor):
        assert monitor.alert_fn is None

    def test_alert_fn_injectable(self):
        fn  = lambda e: None
        mon = ExternalConstraintMonitor(alert_fn=fn)
        assert mon.alert_fn is fn

    def test_initial_events_empty(self, monitor):
        assert monitor._events == []


# ──────────────────────────────────────────────
# TestConstraintCheck
# ──────────────────────────────────────────────

class TestConstraintCheck:
    def test_all_within_limits_passes(self, monitor):
        result = monitor.check({"token_limit": 1000, "cost_budget": 0.5})
        assert result.passed is True
        assert len(result.events) == 0

    def test_token_limit_exceeded_fails(self, monitor):
        result = monitor.check({"token_limit": 5000})
        assert result.passed is False
        assert len(result.events) == 1
        assert result.events[0].constraint_type == "token_limit"

    def test_cost_budget_exceeded_fails(self, monitor):
        result = monitor.check({"cost_budget": 5.0})
        assert result.passed is False

    def test_multiple_violations(self, monitor):
        result = monitor.check({"token_limit": 5000, "cost_budget": 5.0})
        assert len(result.events) == 2

    def test_warning_severity_below_1_5x(self, monitor):
        # 한도=4096, 관측=5000 (1.22x) → warning
        result = monitor.check({"token_limit": 5000})
        assert result.events[0].severity == "warning"

    def test_critical_severity_above_1_5x(self, monitor):
        # 한도=4096, 관측=7000 (1.71x) → critical
        result = monitor.check({"token_limit": 7000})
        assert result.events[0].severity == "critical"

    def test_result_is_constraint_check_result(self, monitor):
        result = monitor.check({"token_limit": 1000})
        assert isinstance(result, ConstraintCheckResult)

    def test_events_are_immutable(self, monitor):
        monitor.check({"token_limit": 9000})
        for e in monitor._events:
            assert isinstance(e, ConstraintEvent)
            with pytest.raises((AttributeError, TypeError)):
                e.severity = "changed"

    def test_unknown_metric_ignored(self, monitor):
        result = monitor.check({"nonexistent_metric": 99999})
        assert result.passed is True

    def test_context_passed_to_event(self, monitor):
        ctx = {"model": "gpt-4", "request_id": "abc"}
        result = monitor.check({"token_limit": 5000}, context=ctx)
        assert result.events[0].context["model"] == "gpt-4"

    def test_result_to_dict(self, monitor):
        result = monitor.check({"token_limit": 1000})
        d = result.to_dict()
        assert "passed" in d
        assert "event_count" in d
        assert "events" in d
        assert "checked_at" in d


# ──────────────────────────────────────────────
# TestAlertFunction
# ──────────────────────────────────────────────

class TestAlertFunction:
    def test_alert_called_on_violation(self):
        alerts = []
        mon = ExternalConstraintMonitor(alert_fn=lambda e: alerts.append(e))
        mon.check({"token_limit": 5000})
        assert len(alerts) == 1

    def test_alert_not_called_when_passing(self):
        alerts = []
        mon = ExternalConstraintMonitor(alert_fn=lambda e: alerts.append(e))
        mon.check({"token_limit": 1000})
        assert len(alerts) == 0

    def test_alert_called_for_each_violation(self):
        alerts = []
        mon = ExternalConstraintMonitor(alert_fn=lambda e: alerts.append(e))
        mon.check({"token_limit": 5000, "cost_budget": 5.0})
        assert len(alerts) == 2

    def test_alert_fn_exception_does_not_propagate(self):
        def bad_fn(e):
            raise RuntimeError("alert failed")
        mon = ExternalConstraintMonitor(alert_fn=bad_fn)
        result = mon.check({"token_limit": 5000})
        assert result is not None  # 예외 전파 없이 결과 반환


# ──────────────────────────────────────────────
# TestConstraintManagement
# ──────────────────────────────────────────────

class TestConstraintManagement:
    def test_add_constraint(self, monitor):
        monitor.add_constraint("custom_metric", 100.0, "ms")
        assert "custom_metric" in monitor.constraints
        assert monitor.constraints["custom_metric"] == 100.0
        assert monitor.units["custom_metric"] == "ms"

    def test_remove_existing_constraint(self, monitor):
        removed = monitor.remove_constraint("token_limit")
        assert removed is True
        assert "token_limit" not in monitor.constraints

    def test_remove_nonexistent_returns_false(self, monitor):
        removed = monitor.remove_constraint("nonexistent")
        assert removed is False

    def test_removed_constraint_not_checked(self, monitor):
        monitor.remove_constraint("token_limit")
        result = monitor.check({"token_limit": 99999})
        assert result.passed is True  # 제거된 제약은 무시


# ──────────────────────────────────────────────
# TestMonitorStats
# ──────────────────────────────────────────────

class TestMonitorStats:
    def test_stats_keys(self, monitor):
        monitor.check({"token_limit": 1000})
        s = monitor.stats()
        assert "total_events" in s
        assert "critical_count" in s
        assert "warning_count" in s
        assert "constraint_types_violated" in s

    def test_stats_zero_on_empty(self, monitor):
        s = monitor.stats()
        assert s["total_events"] == 0
        assert s["critical_count"] == 0

    def test_stats_counts_correctly(self, monitor):
        monitor.check({"token_limit": 5000})   # warning
        monitor.check({"token_limit": 9000})   # critical
        s = monitor.stats()
        assert s["total_events"] == 2
        assert s["warning_count"] == 1
        assert s["critical_count"] == 1

    def test_critical_events_filter(self, monitor):
        monitor.check({"token_limit": 9000})
        critical = monitor.critical_events()
        assert len(critical) == 1
        assert critical[0].severity == "critical"

    def test_all_events_accumulated(self, monitor):
        monitor.check({"token_limit": 5000})
        monitor.check({"cost_budget": 5.0})
        assert len(monitor.all_events()) == 2


# ──────────────────────────────────────────────
# TestSubPhase4Integration
# ──────────────────────────────────────────────

class TestSubPhase4Integration:
    """SubPhase 4 전체 Quality 모듈 통합 테스트."""

    def test_llm_judge_available(self):
        from literary_system.quality.llm_judge import LLMJudge
        j = LLMJudge()
        assert hasattr(j, "evaluate_one")
        assert hasattr(j, "evaluate")
        assert hasattr(j, "stats")

    def test_rubric_calibrator_available(self):
        from literary_system.quality.llm_judge import LLMJudge, RubricCalibrator
        j   = LLMJudge()
        cal = RubricCalibrator(judge=j)
        assert hasattr(cal, "calibrate")
        assert hasattr(cal, "summary")

    def test_hallucination_detector_available(self):
        from literary_system.quality.hallucination_safety import HallucinationDetector
        det = HallucinationDetector()
        assert hasattr(det, "detect")
        assert hasattr(det, "detect_batch")
        assert hasattr(det, "stats")

    def test_safety_gate_available(self):
        from literary_system.quality.hallucination_safety import SafetyGate
        g = SafetyGate()
        assert hasattr(g, "check")
        assert hasattr(g, "check_batch")
        assert hasattr(g, "stats")

    def test_gate9v2_available(self):
        from literary_system.gates.gate9_quality_v2 import Gate9v2
        g = Gate9v2()
        r = g.run()
        assert r.passed is True

    def test_gate10v2_available(self):
        from literary_system.gates.gate10_quality_v2 import Gate10v2
        g = Gate10v2()
        r = g.run(adapters=None)
        assert r.quality_modules_passed is True

    def test_consistency_checker_available(self):
        from literary_system.quality.consistency_checker import ConsistencyChecker
        cc = ConsistencyChecker()
        assert hasattr(cc, "check")
        assert hasattr(cc, "stats")

    def test_ecm_available(self):
        mon = ExternalConstraintMonitor()
        r   = mon.check({"token_limit": 1000})
        assert r.passed is True

    def test_gate14_survival_passes(self):
        from literary_system.gates.gate14_quality_subphase4 import _gate_quality_subphase4_survival
        result = _gate_quality_subphase4_survival()
        assert result["pass"] is True
        assert result["modules_verified"] == 8

    def test_release_gate_v450(self):
        from literary_system.gates.release_gate import run_release_gate
        result = run_release_gate()
        assert result["version"] in ("V450", "V456", "V462", "V467", "V468", "V474", "V480", "V481", "V485", "V491", "V497", "V546", "V555")
        assert result["gates_checked"] >= 12
        assert result["status"] == "pass"
        assert result["gates_passed"] >= 12

    def test_quality_pipeline_full_flow(self):
        """LLMJudge -> HallucinationDetector -> SafetyGate -> ConsistencyChecker 순차 파이프라인."""
        from literary_system.quality.llm_judge import LLMJudge
        from literary_system.quality.hallucination_safety import HallucinationDetector, SafetyGate
        from literary_system.quality.consistency_checker import ConsistencyChecker

        class _Rec:
            def __init__(self, i):
                self.trace_id      = f"pipe_{i}"
                self.render_output = {"scene": f"형사가 단서를 수집했다. 씬 {i}"}
                self.seed_contract = {"user_prompt": f"씬 {i}을 써라"}
                self.metadata      = {"episode_number": i + 1}

        records = [_Rec(i) for i in range(5)]

        # 1. LLMJudge
        judge   = LLMJudge(sampling_rate=1.0)
        session = judge.evaluate(records)
        assert session.pass_rate == 1.0

        # 2. HallucinationDetector
        det     = HallucinationDetector()
        h_reps  = det.detect_batch(records)
        assert all(not r.flagged for r in h_reps)

        # 3. SafetyGate
        gate    = SafetyGate()
        s_reps  = gate.check_batch(records)
        assert all(not r.blocked for r in s_reps)

        # 4. ConsistencyChecker
        cc      = ConsistencyChecker()
        c_rep   = cc.check(records)
        assert c_rep.consistent is True

        # 5. Gate9v2 통합
        from literary_system.gates.gate9_quality_v2 import Gate9v2
        g9      = Gate9v2()
        r9      = g9.run(
            judge_session=session,
            hallucination_reports=h_reps,
        )
        assert r9.passed is True

    def test_ecm_integration_with_pipeline_metrics(self):
        """파이프라인 메트릭을 ECM으로 검사하는 시나리오."""
        mon = ExternalConstraintMonitor()
        metrics = {
            "token_limit":        2048,
            "cost_budget":        0.05,
            "response_time":      3.5,
            "hallucination_rate": 0.02,
            "safety_block_rate":  0.01,
        }
        result = mon.check(metrics, context={"pipeline_run": "test_run_001"})
        assert result.passed is True
        assert len(result.events) == 0
