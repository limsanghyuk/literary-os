"""
tests/gates/test_v684_pre_flight_fix_gate.py
V684 — G81: Pre-flight Fix Gate 검증 (ADR-146)

TC-01~TC-32: FX-1(TD-1)/FX-2(TD-2)/FX-3(TD-3)/FX-4(D-M-13)/FX-5(통합) + run_g81_gate()
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from literary_system.gates.pre_flight_fix_gate import (
    FixCheckpoint,
    PreFlightFixReport,
    GATE_ID,
    run_pre_flight_fix_gate,
    run_g81_gate,
    _check_fx1_benchmark_percentile,
    _check_fx2_revenue_is_contiguous,
    _check_fx3_cost_control_is_blocking,
    _check_fx4_phase_c_exit_gate_wrapper,
    _check_fx5_all_pass,
)


# ─── TC-01~TC-04: FixCheckpoint 데이터클래스 ──────────────────────────────────

def test_tc01_fix_checkpoint_pass():
    """TC-01: FixCheckpoint.passed=True 생성"""
    cp = FixCheckpoint("test", True, "detail")
    assert cp.passed is True
    assert cp.name == "test"


def test_tc02_fix_checkpoint_fail():
    """TC-02: FixCheckpoint.passed=False 생성"""
    cp = FixCheckpoint("test", False, "error")
    assert cp.passed is False


def test_tc03_pre_flight_fix_report_add():
    """TC-03: PreFlightFixReport.add() 체크포인트 누적"""
    report = PreFlightFixReport()
    report.add(FixCheckpoint("a", True))
    report.add(FixCheckpoint("b", False))
    assert len(report.checkpoints) == 2


def test_tc04_pre_flight_fix_report_counts():
    """TC-04: passed_count / failed_count 정확성"""
    report = PreFlightFixReport()
    report.add(FixCheckpoint("a", True))
    report.add(FixCheckpoint("b", True))
    report.add(FixCheckpoint("c", False))
    assert report.passed_count == 2
    assert report.failed_count == 1


# ─── TC-05~TC-10: FX-1 TD-1 benchmark.percentile ────────────────────────────

def test_tc05_fx1_passes():
    """TC-05: FX-1 체크포인트 PASS"""
    cp = _check_fx1_benchmark_percentile()
    assert cp.passed is True, cp.detail


def test_tc06_fx1_name():
    """TC-06: FX-1 체크포인트 이름 확인"""
    cp = _check_fx1_benchmark_percentile()
    assert "TD-1" in cp.name


def test_tc07_benchmark_percentile_nist_r7():
    """TC-07: benchmark.percentile() NIST R-7 n=100 정확성"""
    from literary_system.enterprise.benchmark import percentile
    data = list(range(1, 101))
    result = percentile(data, 0.99)
    assert abs(result - 99.01) < 1e-6


def test_tc08_benchmark_percentile_empty():
    """TC-08: percentile([]) → 0.0"""
    from literary_system.enterprise.benchmark import percentile
    assert percentile([], 0.5) == 0.0


def test_tc09_benchmark_percentile_single():
    """TC-09: percentile([x]) → x"""
    from literary_system.enterprise.benchmark import percentile
    assert percentile([77.0], 0.99) == 77.0


def test_tc10_benchmark_percentile_midpoint():
    """TC-10: percentile([0,100], 0.5) → 50.0"""
    from literary_system.enterprise.benchmark import percentile
    assert abs(percentile([0.0, 100.0], 0.5) - 50.0) < 1e-6


# ─── TC-11~TC-17: FX-2 TD-2 is_contiguous + calculate_tiered ────────────────

def test_tc11_fx2_passes():
    """TC-11: FX-2 체크포인트 PASS"""
    cp = _check_fx2_revenue_is_contiguous()
    assert cp.passed is True, cp.detail


def test_tc12_fx2_name():
    """TC-12: FX-2 체크포인트 이름 확인"""
    cp = _check_fx2_revenue_is_contiguous()
    assert "TD-2" in cp.name


def test_tc13_is_contiguous_true():
    """TC-13: 연속 티어 → is_contiguous True"""
    from literary_system.enterprise.revenue import RevenueCalculator, RevenueTier
    tiers = [
        RevenueTier(0.0, 1000.0, 0.15),
        RevenueTier(1000.0, 5000.0, 0.12),
        RevenueTier(5000.0, -1, 0.10),
    ]
    assert RevenueCalculator.is_contiguous(tiers) is True


def test_tc14_is_contiguous_false_gap():
    """TC-14: 갭 있는 티어 → is_contiguous False"""
    from literary_system.enterprise.revenue import RevenueCalculator, RevenueTier
    tiers = [
        RevenueTier(0.0, 1000.0, 0.15),
        RevenueTier(1500.0, 5000.0, 0.12),  # 갭
    ]
    assert RevenueCalculator.is_contiguous(tiers) is False


def test_tc15_calculate_tiered_correct():
    """TC-15: calculate_tiered(2000) = 1000*0.15 + 1000*0.12 = 270"""
    from literary_system.enterprise.revenue import (
        PartnerRevenueContract, RevenueCalculator, RevenueModel, RevenueTier,
    )
    contract = PartnerRevenueContract(
        contract_id="T", partner_id="P", partner_name="N",
        model=RevenueModel.TIERED,
        tiers=[RevenueTier(0.0, 1000.0, 0.15), RevenueTier(1000.0, 5000.0, 0.12)],
    )
    assert abs(RevenueCalculator.calculate_tiered(contract, 2000.0) - 270.0) < 0.01


def test_tc16_calculate_tiered_non_contiguous_raises():
    """TC-16: 비연속 티어 calculate_tiered → ValueError"""
    import pytest
    from literary_system.enterprise.revenue import (
        PartnerRevenueContract, RevenueCalculator, RevenueModel, RevenueTier,
    )
    contract = PartnerRevenueContract(
        contract_id="T", partner_id="P", partner_name="N",
        model=RevenueModel.TIERED,
        tiers=[RevenueTier(0.0, 1000.0, 0.15), RevenueTier(1500.0, 5000.0, 0.12)],
    )
    with pytest.raises(ValueError):
        RevenueCalculator.calculate_tiered(contract, 2000.0)


def test_tc17_is_contiguous_single_tier():
    """TC-17: 단일 티어 → is_contiguous True"""
    from literary_system.enterprise.revenue import RevenueCalculator, RevenueTier
    assert RevenueCalculator.is_contiguous([RevenueTier(0.0, -1, 0.15)]) is True


# ─── TC-18~TC-23: FX-3 TD-3 is_blocking → gate_passed ───────────────────────

def test_tc18_fx3_passes():
    """TC-18: FX-3 체크포인트 PASS"""
    cp = _check_fx3_cost_control_is_blocking()
    assert cp.passed is True, cp.detail


def test_tc19_fx3_name():
    """TC-19: FX-3 체크포인트 이름 확인"""
    cp = _check_fx3_cost_control_is_blocking()
    assert "TD-3" in cp.name


def test_tc20_cost_report_is_blocking_exceeded():
    """TC-20: EnterpriseCostReport EXCEEDED → is_blocking True"""
    from literary_system.enterprise.cost_control import (
        CostAlertLevel, EnterpriseCostAlert, EnterpriseCostReport,
    )
    alert = EnterpriseCostAlert("T", CostAlertLevel.EXCEEDED, 110.0, 100.0, 1.1, "test")
    report = EnterpriseCostReport("T", 110.0, None, alert=alert)
    assert report.is_blocking is True


def test_tc21_cost_report_is_blocking_none_alert():
    """TC-21: alert=None → is_blocking False"""
    from literary_system.enterprise.cost_control import EnterpriseCostReport
    report = EnterpriseCostReport("T", 50.0, None, alert=None)
    assert report.is_blocking is False


def test_tc22_evaluate_alerts_gate_passed_false():
    """TC-22: blocking 1건 → _evaluate_alerts gate_passed False"""
    from literary_system.enterprise.cost_control import (
        CostAlertLevel, EnterpriseCostAlert, EnterpriseCostControlGate, EnterpriseCostReport,
    )
    alert = EnterpriseCostAlert("T", CostAlertLevel.EXCEEDED, 110.0, 100.0, 1.1, "x")
    r = EnterpriseCostReport("T", 110.0, None, alert=alert)
    gate = EnterpriseCostControlGate()
    summary = gate._evaluate_alerts([r])
    assert summary.gate_passed is False


def test_tc23_demo_run_gate_passed_false():
    """TC-23: demo_run() T4-Jenova EXCEEDED → gate_passed False"""
    from literary_system.enterprise.cost_control import EnterpriseCostControlGate
    result = EnterpriseCostControlGate().demo_run()
    assert result.gate_passed is False


# ─── TC-24~TC-27: FX-4 D-M-13 phase_c_exit_gate Wrapper ─────────────────────

def test_tc24_fx4_passes():
    """TC-24: FX-4 체크포인트 PASS"""
    cp = _check_fx4_phase_c_exit_gate_wrapper()
    assert cp.passed is True, cp.detail


def test_tc25_fx4_name():
    """TC-25: FX-4 체크포인트 이름 확인"""
    cp = _check_fx4_phase_c_exit_gate_wrapper()
    assert "D-M-13" in cp.name


def test_tc26_phase_c_exit_gate_constants():
    """TC-26: phase_c_exit_gate.py 상수 — MIN_GATES=80, MIN_TESTS=8845"""
    from literary_system.gates.phase_c_exit_gate import MIN_GATES, MIN_TESTS, GATE_ID as G79
    assert MIN_GATES == 80
    assert MIN_TESTS == 8845
    assert G79 == "G79"


def test_tc27_phase_c_exit_gate_checkpoint_count():
    """TC-27: run_phase_c_exit_gate() 체크포인트 ≥ 8개"""
    from literary_system.gates.phase_c_exit_gate import run_phase_c_exit_gate
    report = run_phase_c_exit_gate(
        gates_passed=80, tests_passed=8845,
        _rg_results_override={"pass": True, "gates_total": 80, "tests_total": 8845, "gate_passed": True},
    )
    assert len(report.checkpoints) >= 8


# ─── TC-28~TC-30: FX-5 통합 및 run_pre_flight_fix_gate() ─────────────────────

def test_tc28_fx5_all_pass():
    """TC-28: 4개 모두 PASS → FX-5 gate_passed True"""
    cps = [FixCheckpoint("a", True), FixCheckpoint("b", True),
           FixCheckpoint("c", True), FixCheckpoint("d", True)]
    fx5 = _check_fx5_all_pass(cps)
    assert fx5.passed is True


def test_tc29_fx5_any_fail():
    """TC-29: 1개 FAIL → FX-5 gate_passed False"""
    cps = [FixCheckpoint("a", True), FixCheckpoint("b", False),
           FixCheckpoint("c", True), FixCheckpoint("d", True)]
    fx5 = _check_fx5_all_pass(cps)
    assert fx5.passed is False


def test_tc30_run_pre_flight_fix_gate_all_pass():
    """TC-30: run_pre_flight_fix_gate() gate_passed True + 5 checkpoints"""
    report = run_pre_flight_fix_gate()
    assert report.gate_passed is True, str([(c.name, c.detail) for c in report.checkpoints if not c.passed])
    assert len(report.checkpoints) == 5


# ─── TC-31~TC-32: run_g81_gate() 딕셔너리 인터페이스 ─────────────────────────

def test_tc31_run_g81_gate_pass():
    """TC-31: run_g81_gate() 반환값 pass=True"""
    result = run_g81_gate()
    assert result["pass"] is True


def test_tc32_run_g81_gate_structure():
    """TC-32: run_g81_gate() 딕셔너리 필드 구조 검증"""
    result = run_g81_gate()
    for key in ("pass", "gate_id", "passed_count", "failed_count", "checkpoints"):
        assert key in result, "missing key: {}".format(key)
    assert result["gate_id"] == "G81"
    assert result["passed_count"] == 5
    assert result["failed_count"] == 0
