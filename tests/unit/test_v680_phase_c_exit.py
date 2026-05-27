"""
tests/unit/test_v680_phase_c_exit.py
=====================================
V680: EnterprisePhaseCExitGate G79 단위 테스트 (ADR-142)
"""
import pytest
from literary_system.enterprise.phase_c_exit_gate import (
    PhaseCExitStatus,
    EnterprisePhaseCGateResult,
    EnterprisePhaseCExitReport,
    EnterprisePhaseCExitGate,
)


# ── 픽스처 ──────────────────────────────────────────────────────────────────

def _make_gate_result(gate_id: str, passed: bool) -> EnterprisePhaseCGateResult:
    return EnterprisePhaseCGateResult(
        gate_id=gate_id,
        description=f"Test {gate_id}",
        passed=passed,
    )


def _make_report(
    all_pass: bool = True,
    total_tc: int = 9000,
    min_tc: int = 8500,
) -> EnterprisePhaseCExitReport:
    results = [
        _make_gate_result(f"G{73 + i}", all_pass) for i in range(6)
    ]
    status = (
        PhaseCExitStatus.PASS
        if all_pass and total_tc >= min_tc
        else PhaseCExitStatus.FAIL
    )
    return EnterprisePhaseCExitReport(
        gate_results=results,
        total_tc=total_tc,
        min_tc_required=min_tc,
        overall_status=status,
    )


# ── PhaseCExitStatus 테스트 ──────────────────────────────────────────────────

class TestPhaseCExitStatus:
    def test_pass_value(self):
        assert PhaseCExitStatus.PASS.value == "PASS"

    def test_fail_value(self):
        assert PhaseCExitStatus.FAIL.value == "FAIL"

    def test_enum_members(self):
        members = {s.value for s in PhaseCExitStatus}
        assert members == {"PASS", "FAIL"}


# ── EnterprisePhaseCGateResult 테스트 ─────────────────────────────────────

class TestEnterprisePhaseCGateResult:
    def test_passed_status_str(self):
        r = _make_gate_result("G73", True)
        assert r.status_str == "PASS"

    def test_failed_status_str(self):
        r = _make_gate_result("G73", False)
        assert r.status_str == "FAIL"

    def test_default_details_empty(self):
        r = _make_gate_result("G73", True)
        assert r.details == {}

    def test_default_error_empty(self):
        r = _make_gate_result("G73", True)
        assert r.error == ""

    def test_error_stored(self):
        r = EnterprisePhaseCGateResult(
            gate_id="G73", description="x", passed=False, error="boom"
        )
        assert r.error == "boom"


# ── EnterprisePhaseCExitReport 테스트 ─────────────────────────────────────

class TestEnterprisePhaseCExitReport:
    def test_all_pass_true(self):
        report = _make_report(all_pass=True)
        assert report.all_gates_passed is True

    def test_all_pass_false_when_one_fails(self):
        results = [_make_gate_result("G73", True)] * 5 + [
            _make_gate_result("G78", False)
        ]
        report = EnterprisePhaseCExitReport(
            gate_results=results,
            total_tc=9000,
            min_tc_required=8500,
            overall_status=PhaseCExitStatus.FAIL,
        )
        assert report.all_gates_passed is False

    def test_tc_satisfied_true(self):
        report = _make_report(total_tc=9000, min_tc=8500)
        assert report.tc_satisfied is True

    def test_tc_satisfied_false(self):
        report = _make_report(all_pass=True, total_tc=8000, min_tc=8500)
        assert report.tc_satisfied is False

    def test_gate_passed_true(self):
        report = _make_report(all_pass=True)
        assert report.gate_passed is True

    def test_gate_passed_false_on_fail(self):
        report = _make_report(all_pass=False)
        assert report.gate_passed is False

    def test_passed_count(self):
        report = _make_report(all_pass=True)
        assert report.passed_count == 6

    def test_total_count(self):
        report = _make_report()
        assert report.total_count == 6

    def test_summary_contains_version(self):
        report = _make_report()
        summary = report.summary()
        assert "12.0.0" in summary

    def test_summary_contains_pass(self):
        report = _make_report(all_pass=True)
        assert "PASS" in report.summary()

    def test_summary_contains_fail(self):
        report = _make_report(all_pass=False)
        assert "FAIL" in report.summary()

    def test_default_version(self):
        report = _make_report()
        assert report.version == "12.0.0"


# ── EnterprisePhaseCExitGate 테스트 ─────────────────────────────────────────

class TestEnterprisePhaseCExitGate:
    def test_gate_id(self):
        gate = EnterprisePhaseCExitGate()
        assert gate.GATE_ID == "G79"

    def test_version(self):
        gate = EnterprisePhaseCExitGate()
        assert gate.VERSION == "12.0.0"

    def test_min_tc(self):
        gate = EnterprisePhaseCExitGate()
        assert gate.MIN_TC == 8500

    def test_enterprise_gates_count(self):
        gate = EnterprisePhaseCExitGate()
        assert len(gate.ENTERPRISE_GATES) == 6

    def test_enterprise_gate_ids(self):
        gate = EnterprisePhaseCExitGate()
        ids = [g[0] for g in gate.ENTERPRISE_GATES]
        assert ids == ["G73", "G74", "G75-BM", "G76", "G77", "G78"]

    def test_run_with_injected_tc_pass(self):
        gate = EnterprisePhaseCExitGate()
        report = gate.run(total_tc=9000)
        assert report.gate_passed is True

    def test_run_with_injected_tc_fail_below_min(self):
        gate = EnterprisePhaseCExitGate()
        report = gate.run(total_tc=8000)
        assert report.gate_passed is False

    def test_run_returns_report_type(self):
        gate = EnterprisePhaseCExitGate()
        report = gate.run(total_tc=9000)
        assert isinstance(report, EnterprisePhaseCExitReport)

    def test_run_6_gate_results(self):
        gate = EnterprisePhaseCExitGate()
        report = gate.run(total_tc=9000)
        assert len(report.gate_results) == 6

    def test_demo_run_pass(self):
        gate = EnterprisePhaseCExitGate()
        report = gate.demo_run()
        # demo_run은 실제 TC를 읽어 8500 이상이면 PASS
        assert isinstance(report, EnterprisePhaseCExitReport)

    def test_run_status_pass(self):
        gate = EnterprisePhaseCExitGate()
        report = gate.run(total_tc=9000)
        assert report.overall_status == PhaseCExitStatus.PASS

    def test_run_status_fail_low_tc(self):
        gate = EnterprisePhaseCExitGate()
        report = gate.run(total_tc=1000)
        assert report.overall_status == PhaseCExitStatus.FAIL

    def test_run_total_tc_stored(self):
        gate = EnterprisePhaseCExitGate()
        report = gate.run(total_tc=9500)
        assert report.total_tc == 9500

    def test_run_min_tc_stored(self):
        gate = EnterprisePhaseCExitGate()
        report = gate.run(total_tc=9000)
        assert report.min_tc_required == 8500

    def test_g73_result_passed(self):
        gate = EnterprisePhaseCExitGate()
        report = gate.run(total_tc=9000)
        g73 = next(r for r in report.gate_results if r.gate_id == "G73")
        assert g73.passed is True

    def test_g74_result_passed(self):
        gate = EnterprisePhaseCExitGate()
        report = gate.run(total_tc=9000)
        g74 = next(r for r in report.gate_results if r.gate_id == "G74")
        assert g74.passed is True

    def test_g76_result_passed(self):
        gate = EnterprisePhaseCExitGate()
        report = gate.run(total_tc=9000)
        g76 = next(r for r in report.gate_results if r.gate_id == "G76")
        assert g76.passed is True

    def test_g77_result_passed(self):
        gate = EnterprisePhaseCExitGate()
        report = gate.run(total_tc=9000)
        g77 = next(r for r in report.gate_results if r.gate_id == "G77")
        assert g77.passed is True

    def test_g78_result_passed(self):
        gate = EnterprisePhaseCExitGate()
        report = gate.run(total_tc=9000)
        g78 = next(r for r in report.gate_results if r.gate_id == "G78")
        assert g78.passed is True

    def test_single_gate_error_stored(self):
        gate = EnterprisePhaseCExitGate()
        # 존재하지 않는 모듈로 직접 호출하면 error 필드가 채워져야 함
        result = gate._run_single_gate(
            "G99", "BadGate",
            "literary_system.enterprise.nonexistent_module",
            "SomeClass"
        )
        assert result.passed is False
        assert result.error != ""

    def test_summary_has_gate_ids(self):
        gate = EnterprisePhaseCExitGate()
        report = gate.run(total_tc=9000)
        summary = report.summary()
        for gid in ["G73", "G74", "G75-BM", "G76", "G77", "G78"]:
            assert gid in summary
