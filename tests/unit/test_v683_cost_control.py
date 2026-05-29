"""
tests/unit/test_v683_cost_control.py
V683 — TD-3: is_blocking → gate_passed 연결 검증 (ADR-145)

TC-01~TC-20: EnterpriseCostAlert.is_blocking / EnterpriseCostReport.is_blocking /
             CostAlertSummary / _evaluate_alerts / demo_run gate_passed 전체 검증
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from literary_system.enterprise.cost_control import (
    CostAlertLevel,
    CostCategory,
    CostEntry,
    EnterpriseCostAlert,
    EnterpriseCostBudget,
    EnterpriseCostControlGate,
    EnterpriseCostReport,
    EnterpriseCostSuiteReport,
    EnterpriseCostTracker,
    CostAlertSummary,
)


# ─── TC-01~TC-05: EnterpriseCostAlert.is_blocking ────────────────────────────

def _make_alert(level: CostAlertLevel) -> EnterpriseCostAlert:
    return EnterpriseCostAlert(
        tenant_id="T-test",
        level=level,
        current_usd=1000.0,
        limit_usd=900.0,
        usage_pct=1.11,
        message="test",
    )


def test_tc01_alert_is_blocking_exceeded():
    """TC-01: EXCEEDED → is_blocking True"""
    alert = _make_alert(CostAlertLevel.EXCEEDED)
    assert alert.is_blocking is True


def test_tc02_alert_is_blocking_critical_false():
    """TC-02: CRITICAL → is_blocking False"""
    alert = _make_alert(CostAlertLevel.CRITICAL)
    assert alert.is_blocking is False


def test_tc03_alert_is_blocking_warning_false():
    """TC-03: WARNING → is_blocking False"""
    alert = _make_alert(CostAlertLevel.WARNING)
    assert alert.is_blocking is False


def test_tc04_alert_is_blocking_ok_false():
    """TC-04: OK → is_blocking False"""
    alert = _make_alert(CostAlertLevel.OK)
    assert alert.is_blocking is False


# ─── TC-05~TC-09: EnterpriseCostReport.is_blocking ───────────────────────────

def _make_report(alert: EnterpriseCostAlert | None) -> EnterpriseCostReport:
    return EnterpriseCostReport(
        tenant_id="T-test",
        total_usd=500.0,
        budget=None,
        alert=alert,
    )


def test_tc05_report_is_blocking_no_alert():
    """TC-05: alert=None → report.is_blocking False"""
    report = _make_report(None)
    assert report.is_blocking is False


def test_tc06_report_is_blocking_exceeded():
    """TC-06: EXCEEDED alert → report.is_blocking True"""
    report = _make_report(_make_alert(CostAlertLevel.EXCEEDED))
    assert report.is_blocking is True


def test_tc07_report_is_blocking_critical_false():
    """TC-07: CRITICAL alert → report.is_blocking False"""
    report = _make_report(_make_alert(CostAlertLevel.CRITICAL))
    assert report.is_blocking is False


def test_tc08_report_is_blocking_warning_false():
    """TC-08: WARNING alert → report.is_blocking False"""
    report = _make_report(_make_alert(CostAlertLevel.WARNING))
    assert report.is_blocking is False


def test_tc09_report_is_blocking_delegates_to_alert():
    """TC-09: report.is_blocking == report.alert.is_blocking"""
    alert = _make_alert(CostAlertLevel.EXCEEDED)
    report = _make_report(alert)
    assert report.is_blocking == alert.is_blocking


# ─── TC-10~TC-14: CostAlertSummary & _evaluate_alerts ───────────────────────

def test_tc10_cost_alert_summary_fields():
    """TC-10: CostAlertSummary 필드 정확성"""
    s = CostAlertSummary(blocking=2, exceeded=2, critical=1, gate_passed=False)
    assert s.blocking == 2
    assert s.exceeded == 2
    assert s.critical == 1
    assert s.gate_passed is False


def test_tc11_evaluate_alerts_no_blocking():
    """TC-11: blocking 0 → gate_passed True"""
    gate = EnterpriseCostControlGate()
    reports = [
        _make_report(_make_alert(CostAlertLevel.WARNING)),
        _make_report(_make_alert(CostAlertLevel.CRITICAL)),
        _make_report(None),
    ]
    summary = gate._evaluate_alerts(reports)
    assert summary.gate_passed is True
    assert summary.blocking == 0


def test_tc12_evaluate_alerts_one_blocking():
    """TC-12: blocking 1 → gate_passed False"""
    gate = EnterpriseCostControlGate()
    reports = [
        _make_report(_make_alert(CostAlertLevel.EXCEEDED)),
        _make_report(None),
    ]
    summary = gate._evaluate_alerts(reports)
    assert summary.gate_passed is False
    assert summary.blocking == 1


def test_tc13_evaluate_alerts_counts_exceeded():
    """TC-13: exceeded 카운트 정확성"""
    gate = EnterpriseCostControlGate()
    reports = [
        _make_report(_make_alert(CostAlertLevel.EXCEEDED)),
        _make_report(_make_alert(CostAlertLevel.EXCEEDED)),
        _make_report(_make_alert(CostAlertLevel.CRITICAL)),
    ]
    summary = gate._evaluate_alerts(reports)
    assert summary.exceeded == 2
    assert summary.critical == 1


def test_tc14_evaluate_alerts_empty():
    """TC-14: 빈 리스트 → gate_passed True, all counts 0"""
    gate = EnterpriseCostControlGate()
    summary = gate._evaluate_alerts([])
    assert summary.gate_passed is True
    assert summary.blocking == 0
    assert summary.exceeded == 0
    assert summary.critical == 0


# ─── TC-15~TC-20: demo_run gate_passed 동작 검증 ─────────────────────────────

def test_tc15_demo_run_gate_passed_false():
    """TC-15: demo_run — T4-Jenova EXCEEDED → gate_passed False"""
    gate = EnterpriseCostControlGate()
    result = gate.demo_run()
    assert result.gate_passed is False, "T4-Jenova(110% 초과)로 gate가 실패해야 함"


def test_tc16_demo_run_tenants_exceeded_one():
    """TC-16: demo_run — tenants_exceeded == 1"""
    gate = EnterpriseCostControlGate()
    result = gate.demo_run()
    assert result.tenants_exceeded == 1


def test_tc17_demo_run_reports_count():
    """TC-17: demo_run — 4개 테넌트 리포트 생성"""
    gate = EnterpriseCostControlGate()
    result = gate.demo_run()
    assert len(result.reports) == 4


def test_tc18_demo_run_t4_is_blocking():
    """TC-18: demo_run — T4-Jenova report.is_blocking True"""
    gate = EnterpriseCostControlGate()
    result = gate.demo_run()
    t4 = next(r for r in result.reports if r.tenant_id == "T4-Jenova")
    assert t4.is_blocking is True


def test_tc19_demo_run_t1_not_blocking():
    """TC-19: demo_run — T1-NovelAI(60%) is_blocking False"""
    gate = EnterpriseCostControlGate()
    result = gate.demo_run()
    t1 = next(r for r in result.reports if r.tenant_id == "T1-NovelAI")
    assert t1.is_blocking is False


def test_tc20_demo_run_total_suite_usd():
    """TC-20: demo_run — total_suite_usd 정확성 (300+656+600+330=1886)"""
    gate = EnterpriseCostControlGate()
    result = gate.demo_run()
    # T1: 6*50=300, T2: 8*82=656, T3: 5*120=600, T4: 11*30=330 → 1886
    assert abs(result.total_suite_usd - 1886.0) < 0.01
