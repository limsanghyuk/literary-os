"""
tests/unit/test_v678_cost_control.py
V678 — Enterprise 비용 제어 레이어 단위 테스트 (30 TC)
"""
import pytest
from literary_system.enterprise.cost_control import (
    CostAlertLevel, CostCategory,
    EnterpriseCostBudget, CostEntry,
    EnterpriseCostAlert, EnterpriseCostReport, EnterpriseCostSuiteReport,
    EnterpriseCostTracker, EnterpriseCostControlGate,
)


# ─── CostAlertLevel ───────────────────────────────────────────────────────────

def test_alert_level_ok():
    assert CostAlertLevel.OK == "ok"

def test_alert_level_warning():
    assert CostAlertLevel.WARNING == "warning"

def test_alert_level_critical():
    assert CostAlertLevel.CRITICAL == "critical"

def test_alert_level_exceeded():
    assert CostAlertLevel.EXCEEDED == "exceeded"


# ─── EnterpriseCostBudget ─────────────────────────────────────────────────────

def test_budget_warning_usd():
    b = EnterpriseCostBudget("T1", 1000.0)
    assert b.warning_usd == 800.0

def test_budget_critical_usd():
    b = EnterpriseCostBudget("T1", 1000.0)
    assert b.critical_usd == 950.0

def test_budget_custom_thresholds():
    b = EnterpriseCostBudget("T1", 500.0, warning_threshold=0.70, critical_threshold=0.90)
    assert b.warning_usd == 350.0
    assert b.critical_usd == 450.0


# ─── EnterpriseCostTracker ────────────────────────────────────────────────────

def test_tracker_total_zero_initially():
    t = EnterpriseCostTracker()
    assert t.total_for("T1") == 0.0

def test_tracker_record_and_total():
    t = EnterpriseCostTracker()
    t.record(CostEntry("T1", CostCategory.LLM_INFERENCE, 50.0))
    t.record(CostEntry("T1", CostCategory.EMBEDDING, 30.0))
    assert t.total_for("T1") == 80.0

def test_tracker_breakdown():
    t = EnterpriseCostTracker()
    t.record(CostEntry("T1", CostCategory.LLM_INFERENCE, 100.0))
    t.record(CostEntry("T1", CostCategory.STORAGE, 20.0))
    bd = t.breakdown_for("T1")
    assert bd["llm_inference"] == 100.0
    assert bd["storage"] == 20.0

def test_tracker_no_alert_below_threshold():
    t = EnterpriseCostTracker()
    t.set_budget(EnterpriseCostBudget("T1", 1000.0))
    t.record(CostEntry("T1", CostCategory.LLM_INFERENCE, 500.0))
    assert t.build_alert("T1") is None

def test_tracker_warning_alert():
    t = EnterpriseCostTracker()
    t.set_budget(EnterpriseCostBudget("T1", 1000.0))
    t.record(CostEntry("T1", CostCategory.LLM_INFERENCE, 850.0))
    alert = t.build_alert("T1")
    assert alert is not None
    assert alert.level == CostAlertLevel.WARNING

def test_tracker_critical_alert():
    t = EnterpriseCostTracker()
    t.set_budget(EnterpriseCostBudget("T1", 1000.0))
    t.record(CostEntry("T1", CostCategory.LLM_INFERENCE, 970.0))
    alert = t.build_alert("T1")
    assert alert is not None
    assert alert.level == CostAlertLevel.CRITICAL

def test_tracker_exceeded_alert():
    t = EnterpriseCostTracker()
    t.set_budget(EnterpriseCostBudget("T1", 1000.0))
    t.record(CostEntry("T1", CostCategory.LLM_INFERENCE, 1100.0))
    alert = t.build_alert("T1")
    assert alert is not None
    assert alert.level == CostAlertLevel.EXCEEDED
    assert alert.is_blocking is True

def test_tracker_no_budget_no_alert():
    t = EnterpriseCostTracker()
    t.record(CostEntry("T1", CostCategory.LLM_INFERENCE, 999.0))
    assert t.build_alert("T1") is None

def test_tracker_all_tenant_ids():
    t = EnterpriseCostTracker()
    t.set_budget(EnterpriseCostBudget("T1", 100.0))
    t.record(CostEntry("T2", CostCategory.EMBEDDING, 10.0))
    ids = t.all_tenant_ids()
    assert "T1" in ids
    assert "T2" in ids

def test_tracker_report_for_no_alert():
    t = EnterpriseCostTracker()
    t.set_budget(EnterpriseCostBudget("T1", 1000.0))
    t.record(CostEntry("T1", CostCategory.LLM_INFERENCE, 100.0))
    report = t.report_for("T1")
    assert report.total_usd == 100.0
    assert report.alert is None
    assert report.alert_level == CostAlertLevel.OK


# ─── EnterpriseCostReport ─────────────────────────────────────────────────────

def test_report_usage_pct():
    t = EnterpriseCostTracker()
    t.set_budget(EnterpriseCostBudget("T1", 1000.0))
    t.record(CostEntry("T1", CostCategory.LLM_INFERENCE, 400.0))
    r = t.report_for("T1")
    assert abs(r.usage_pct - 0.4) < 1e-6

def test_report_no_budget_usage_pct_zero():
    t = EnterpriseCostTracker()
    t.record(CostEntry("T1", CostCategory.LLM_INFERENCE, 100.0))
    r = t.report_for("T1")
    assert r.usage_pct == 0.0


# ─── EnterpriseCostAlert ─────────────────────────────────────────────────────

def test_alert_is_blocking_exceeded():
    alert = EnterpriseCostAlert("T1", CostAlertLevel.EXCEEDED, 1100.0, 1000.0, 1.1, "exceeded")
    assert alert.is_blocking is True

def test_alert_not_blocking_warning():
    alert = EnterpriseCostAlert("T1", CostAlertLevel.WARNING, 850.0, 1000.0, 0.85, "warning")
    assert alert.is_blocking is False


# ─── EnterpriseCostControlGate ───────────────────────────────────────────────

def test_gate_id():
    assert EnterpriseCostControlGate.GATE_ID == "G77"

def test_gate_demo_returns_suite():
    gate = EnterpriseCostControlGate()
    suite = gate.demo_run()
    assert isinstance(suite, EnterpriseCostSuiteReport)

def test_gate_demo_4_tenants():
    suite = EnterpriseCostControlGate().demo_run()
    assert len(suite.reports) == 4

def test_gate_demo_gate_passed():
    # ADR-145/TD-3: demo includes an over-budget tenant (T4-Jenova 110%), so the
    # cost-control gate correctly blocks -> gate_passed is False (violation detected).
    suite = EnterpriseCostControlGate().demo_run()
    assert suite.gate_passed is False

def test_gate_demo_one_exceeded():
    suite = EnterpriseCostControlGate().demo_run()
    assert suite.tenants_exceeded == 1

def test_gate_demo_total_positive():
    suite = EnterpriseCostControlGate().demo_run()
    assert suite.total_suite_usd > 0

def test_gate_demo_all_within_budget_false():
    suite = EnterpriseCostControlGate().demo_run()
    # T4 exceeded, so not all within budget
    assert suite.all_within_budget is False

def test_gate_demo_t4_jenova_exceeded():
    suite = EnterpriseCostControlGate().demo_run()
    jenova = next(r for r in suite.reports if "Jenova" in r.tenant_id)
    assert jenova.alert_level == CostAlertLevel.EXCEEDED

def test_gate_demo_t1_ok():
    suite = EnterpriseCostControlGate().demo_run()
    novel = next(r for r in suite.reports if "NovelAI" in r.tenant_id)
    assert novel.alert_level == CostAlertLevel.OK

def test_enterprise_exports():
    from literary_system.enterprise import EnterpriseCostControlGate as ECG
    assert ECG.GATE_ID == "G77"

def test_release_gate_g77():
    from literary_system.gates.release_gate import _gate_enterprise_cost_control_g77
    result = _gate_enterprise_cost_control_g77()
    assert result["passed"] is True
    assert result["gate"] == "G77"
