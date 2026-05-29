"""
tests/gates/test_v681_pre_phase_c_exit_gate.py
================================================
V681-PRE: Phase C Exit Gate G79 Wrapper 테스트 (D-M-13)

TC-01 ~ TC-24: 기본 동작, 체크포인트, 경계값, 오버라이드
"""
from __future__ import annotations

import pytest

from literary_system.gates.phase_c_exit_gate import (
    PhaseCCheckpoint,
    PhaseCExitReport,
    run_phase_c_exit_gate,
    run_g79_gate,
    MIN_GATES,
    MIN_TESTS,
    GATE_ID,
)


# ---------------------------------------------------------------------------
# 픽스처
# ---------------------------------------------------------------------------

def _mock_rg(gates: int = 80, tests: int = 8845, extra: dict | None = None) -> dict:
    """테스트용 release_gate 결과 mock."""
    base: dict = {
        "gates_passed": gates,
        "results": {
            "auto_promotion_g62": {"pass": True},
            "coordinator_g64": {"pass": True},
            "evaluator_g65": {"pass": True},
            "mae_multiwork_g66": {"pass": True},
            "suite_registration_g67": {"pass": True},
            "reader_feedback_g68": {"pass": True},
            "feedback_loop_g69": {"pass": True},
            "sdk_stability_g70": {"pass": True},
            "b2b_partner_g71": {"pass": True},
            "phase_b_exit_g61": {"pass": True},
        },
    }
    if extra:
        base["results"].update(extra)
    return base


# ---------------------------------------------------------------------------
# TC-01 ~ TC-03: 기본 구조 검증
# ---------------------------------------------------------------------------

class TestPhaseCExitGateConstants:
    def test_gate_id(self):
        """TC-01: GATE_ID = 'G79'."""
        assert GATE_ID == "G79"

    def test_min_gates(self):
        """TC-02: MIN_GATES = 80."""
        assert MIN_GATES == 80

    def test_min_tests(self):
        """TC-03: MIN_TESTS = 8845."""
        assert MIN_TESTS == 8845


# ---------------------------------------------------------------------------
# TC-04 ~ TC-07b: PhaseCExitReport 데이터클래스
# ---------------------------------------------------------------------------

class TestPhaseCExitReport:
    def test_passed_true(self):
        """TC-04: gate_passed=True → passed=True."""
        r = PhaseCExitReport(gate_passed=True)
        assert r.passed is True

    def test_passed_false(self):
        """TC-05: gate_passed=False → passed=False."""
        r = PhaseCExitReport(gate_passed=False)
        assert r.passed is False

    def test_all_checkpoints_passed_true(self):
        """TC-06: 모든 체크포인트 PASS."""
        r = PhaseCExitReport(
            checkpoints=[PhaseCCheckpoint("A", True), PhaseCCheckpoint("B", True)],
            gate_passed=True,
        )
        assert r.all_checkpoints_passed is True

    def test_all_checkpoints_passed_false(self):
        """TC-07: 하나라도 FAIL → all_checkpoints_passed=False."""
        r = PhaseCExitReport(
            checkpoints=[PhaseCCheckpoint("A", True), PhaseCCheckpoint("B", False)],
            gate_passed=False,
        )
        assert r.all_checkpoints_passed is False

    def test_summary_contains_g79(self):
        """TC-07b: summary()에 G79 포함."""
        r = PhaseCExitReport(gate_passed=True, gates_total=80, tests_total=8845)
        assert "G79" in r.summary()


# ---------------------------------------------------------------------------
# TC-08 ~ TC-10: run_phase_c_exit_gate() 핵심 경로
# ---------------------------------------------------------------------------

class TestRunPhaseCExitGate:
    def test_pass_valid_params(self):
        """TC-08: gates=80, tests=8845 → PASS."""
        r = run_phase_c_exit_gate(
            gates_passed=80, tests_passed=8845,
            _rg_results_override=_mock_rg(80, 8845),
        )
        assert r.gate_passed is True
        assert r.gates_total == 80
        assert r.tests_total == 8845

    def test_fail_insufficient_gates(self):
        """TC-09: gates=79 → FAIL."""
        r = run_phase_c_exit_gate(
            gates_passed=79, tests_passed=8845,
            _rg_results_override=_mock_rg(79, 8845),
        )
        assert r.gate_passed is False

    def test_fail_insufficient_tests(self):
        """TC-10: tests=8844 → FAIL."""
        r = run_phase_c_exit_gate(
            gates_passed=80, tests_passed=8844,
            _rg_results_override=_mock_rg(80, 8844),
        )
        assert r.gate_passed is False


# ---------------------------------------------------------------------------
# TC-11 ~ TC-12: run_g79_gate() 딕셔너리 인터페이스
# ---------------------------------------------------------------------------

class TestRunG79Gate:
    def test_returns_dict_with_pass(self):
        """TC-11: 딕셔너리에 'pass' 키 존재."""
        result = run_g79_gate()
        assert "pass" in result
        assert isinstance(result["pass"], bool)

    def test_dict_required_keys(self):
        """TC-12: 필수 키 모두 존재."""
        result = run_g79_gate()
        for key in ("gates_total", "tests_total", "checkpoints", "checkpoints_passed"):
            assert key in result


# ---------------------------------------------------------------------------
# TC-13 ~ TC-15: 8축 체크포인트 구성
# ---------------------------------------------------------------------------

class TestCheckpointStructure:
    def test_exactly_8_checkpoints(self):
        """TC-13: 체크포인트 정확히 8개."""
        r = run_phase_c_exit_gate(
            gates_passed=80, tests_passed=8845,
            _rg_results_override=_mock_rg(),
        )
        assert len(r.checkpoints) == 8

    def test_cc5_checkpoint_exists(self):
        """TC-14: CC-5 (Gate 수) 체크포인트 존재."""
        r = run_phase_c_exit_gate(
            gates_passed=80, tests_passed=8845,
            _rg_results_override=_mock_rg(),
        )
        names = [c.name for c in r.checkpoints]
        assert any("CC-5" in n or "Gates" in n for n in names)

    def test_cc6_checkpoint_exists(self):
        """TC-15: CC-6 (TC 수) 체크포인트 존재."""
        r = run_phase_c_exit_gate(
            gates_passed=80, tests_passed=8845,
            _rg_results_override=_mock_rg(),
        )
        names = [c.name for c in r.checkpoints]
        assert any("CC-6" in n or "Tests" in n for n in names)


# ---------------------------------------------------------------------------
# TC-16 ~ TC-18: 경계값 검증
# ---------------------------------------------------------------------------

class TestBoundaryValues:
    def test_exactly_min_gates(self):
        """TC-16: gates=MIN_GATES → CC-5 PASS."""
        r = run_phase_c_exit_gate(
            gates_passed=MIN_GATES, tests_passed=MIN_TESTS,
            _rg_results_override=_mock_rg(MIN_GATES, MIN_TESTS),
        )
        cc5 = next(c for c in r.checkpoints if "CC-5" in c.name or "Gates" in c.name)
        assert cc5.passed is True

    def test_below_min_gates(self):
        """TC-17: gates=MIN_GATES-1 → CC-5 FAIL."""
        r = run_phase_c_exit_gate(
            gates_passed=MIN_GATES - 1, tests_passed=MIN_TESTS,
            _rg_results_override=_mock_rg(MIN_GATES - 1, MIN_TESTS),
        )
        cc5 = next(c for c in r.checkpoints if "CC-5" in c.name or "Gates" in c.name)
        assert cc5.passed is False

    def test_below_min_tests(self):
        """TC-18: tests=MIN_TESTS-1 → CC-6 FAIL."""
        r = run_phase_c_exit_gate(
            gates_passed=MIN_GATES, tests_passed=MIN_TESTS - 1,
            _rg_results_override=_mock_rg(MIN_GATES, MIN_TESTS - 1),
        )
        cc6 = next(c for c in r.checkpoints if "CC-6" in c.name or "Tests" in c.name)
        assert cc6.passed is False


# ---------------------------------------------------------------------------
# TC-19 ~ TC-20: CC-1 AutoPromotion
# ---------------------------------------------------------------------------

class TestCC1AutoPromotion:
    def test_cc1_pass(self):
        """TC-19: G62 pass=True → CC-1 PASS."""
        rg = _mock_rg()
        rg["results"]["auto_promotion_g62"] = {"pass": True}
        r = run_phase_c_exit_gate(
            gates_passed=80, tests_passed=8845, _rg_results_override=rg,
        )
        cc1 = next(c for c in r.checkpoints if "CC-1" in c.name)
        assert cc1.passed is True

    def test_cc1_fail(self):
        """TC-20: G62 pass=False → CC-1 FAIL."""
        rg = _mock_rg()
        rg["results"]["auto_promotion_g62"] = {"pass": False}
        r = run_phase_c_exit_gate(
            gates_passed=80, tests_passed=8845, _rg_results_override=rg,
        )
        cc1 = next(c for c in r.checkpoints if "CC-1" in c.name)
        assert cc1.passed is False


# ---------------------------------------------------------------------------
# TC-21 ~ TC-22: CC-8 Phase B 하위호환
# ---------------------------------------------------------------------------

class TestCC8PhaseBCompat:
    def test_cc8_pass(self):
        """TC-21: G61 pass=True → CC-8 PASS."""
        rg = _mock_rg()
        rg["results"]["phase_b_exit_g61"] = {"pass": True}
        r = run_phase_c_exit_gate(
            gates_passed=80, tests_passed=8845, _rg_results_override=rg,
        )
        cc8 = next(c for c in r.checkpoints if "CC-8" in c.name)
        assert cc8.passed is True

    def test_cc8_fail_nonfatal(self):
        """TC-22: CC-8 FAIL이어도 게이트 총수는 유지."""
        rg = _mock_rg()
        rg["results"]["phase_b_exit_g61"] = {"pass": False}
        r = run_phase_c_exit_gate(
            gates_passed=80, tests_passed=8845, _rg_results_override=rg,
        )
        assert r.gates_total == 80


# ---------------------------------------------------------------------------
# TC-23 ~ TC-24: summary() 출력
# ---------------------------------------------------------------------------

class TestSummaryOutput:
    def test_summary_pass_contains_pass(self):
        """TC-23: PASS 시 summary에 'PASS' 포함."""
        r = run_phase_c_exit_gate(
            gates_passed=80, tests_passed=8845,
            _rg_results_override=_mock_rg(),
        )
        if r.gate_passed:
            assert "PASS" in r.summary()

    def test_summary_contains_numbers(self):
        """TC-24: summary에 gates, tests 수치 포함."""
        r = run_phase_c_exit_gate(
            gates_passed=80, tests_passed=8845,
            _rg_results_override=_mock_rg(),
        )
        s = r.summary()
        assert "80" in s and "8845" in s
