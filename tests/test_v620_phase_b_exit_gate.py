"""
test_v620_phase_b_exit_gate.py
V620 Phase B Exit Gate G61 단위·통합 테스트 (25 TC)

클래스 구성
-----------
TestCheckpointResult        (4 TC) — 필드, to_dict
TestPhaseBExitReport        (7 TC) — 집계 프로퍼티, summary, to_dict
TestPhaseBExitGateRun       (8 TC) — run_phase_b_exit_gate (mock 주입)
TestG61GateInterface        (3 TC) — run_g61_gate() 인터페이스 (mock 주입)
TestEdgeCases               (3 TC) — 경계값 + 실패 경로
"""
from __future__ import annotations

import pytest

from literary_system.gates.phase_b_exit_gate import (
    MIN_GATES,
    MIN_TESTS,
    PhaseBCheckpoint,
    PhaseBExitReport,
    run_g61_gate,
    run_phase_b_exit_gate,
)

# ---------------------------------------------------------------------------
# 공통 Mock RG 결과 픽스처
# ---------------------------------------------------------------------------

_MOCK_RG_ALL_PASS = {
    "gates_passed": 60,
    "results": {
        "lora_finetuning_g54":    {"pass": True, "gate": "G54"},
        "rlhf_reward_g56":        {"pass": True, "gate": "G56"},
        "constitution_axis_g57":  {"pass": True, "gate": "G57"},
        "sp_b3_exit_g59":         {"pass": True, "gate": "G59"},
        "performance_slo_g60":    {"pass": True, "gate": "G60"},
    },
}

_MOCK_RG_C1_FAIL = {
    "gates_passed": 60,
    "results": {
        "lora_finetuning_g54":    {"pass": False, "gate": "G54"},
        "rlhf_reward_g56":        {"pass": True,  "gate": "G56"},
        "constitution_axis_g57":  {"pass": True,  "gate": "G57"},
        "sp_b3_exit_g59":         {"pass": True,  "gate": "G59"},
        "performance_slo_g60":    {"pass": True,  "gate": "G60"},
    },
}


# ===========================================================================
# TestCheckpointResult  (4 TC)
# ===========================================================================

class TestCheckpointResult:

    def test_pass_checkpoint(self):
        cp = PhaseBCheckpoint(name="C1-G54-LoRA", passed=True, detail="ok")
        assert cp.name == "C1-G54-LoRA"
        assert cp.passed is True
        assert cp.detail == "ok"

    def test_fail_checkpoint(self):
        cp = PhaseBCheckpoint(name="C5-TotalGates", passed=False, detail="gates=59 < 60")
        assert cp.passed is False

    def test_to_dict_keys(self):
        cp = PhaseBCheckpoint(name="C2-G56+G57-RLHF", passed=True)
        d = cp.to_dict()
        assert set(d.keys()) == {"name", "passed", "detail"}

    def test_default_detail_empty(self):
        cp = PhaseBCheckpoint(name="C6-TotalTests", passed=True)
        assert cp.detail == ""


# ===========================================================================
# TestPhaseBExitReport  (7 TC)
# ===========================================================================

class TestPhaseBExitReport:

    def _report(self, results, gates=60, tests=6703) -> PhaseBExitReport:
        r = PhaseBExitReport(gates_total=gates, tests_total=tests)
        for name, passed in results:
            r.checkpoints.append(PhaseBCheckpoint(name=name, passed=passed))
        return r

    def test_all_pass_true(self):
        r = self._report([("C1", True), ("C2", True), ("C3", True)])
        assert r.all_pass is True

    def test_all_pass_false(self):
        r = self._report([("C1", True), ("C2", False)])
        assert r.all_pass is False

    def test_passed_count(self):
        r = self._report([("C1", True), ("C2", False), ("C3", True)])
        assert r.passed_count == 2
        assert r.total_count == 3

    def test_failed_checkpoints(self):
        r = self._report([("C1", True), ("C4", False), ("C5", False)])
        assert set(r.failed_checkpoints) == {"C4", "C5"}

    def test_summary_pass(self):
        r = self._report([("C1", True), ("C2", True)])
        s = r.summary()
        assert "PASS" in s
        assert "2/2" in s

    def test_summary_fail(self):
        r = self._report([("C1", False)])
        assert "FAIL" in r.summary()

    def test_to_dict_structure(self):
        r = self._report([("C1", True)], gates=60, tests=6703)
        d = r.to_dict()
        assert d["gate"] == "G61"
        assert "all_pass" in d
        assert "gates_total" in d
        assert "tests_total" in d
        assert "checkpoints" in d
        assert isinstance(d["checkpoints"], list)


# ===========================================================================
# TestPhaseBExitGateRun  (8 TC)  — _rg_results_override 주입
# ===========================================================================

class TestPhaseBExitGateRun:

    def test_run_returns_report(self):
        r = run_phase_b_exit_gate(
            gates_passed=60, tests_passed=6703,
            _rg_results_override=_MOCK_RG_ALL_PASS,
        )
        assert isinstance(r, PhaseBExitReport)

    def test_run_six_checkpoints(self):
        r = run_phase_b_exit_gate(
            gates_passed=60, tests_passed=6703,
            _rg_results_override=_MOCK_RG_ALL_PASS,
        )
        assert r.total_count == 6

    def test_run_checkpoint_names(self):
        r = run_phase_b_exit_gate(
            gates_passed=60, tests_passed=6703,
            _rg_results_override=_MOCK_RG_ALL_PASS,
        )
        names = [cp.name for cp in r.checkpoints]
        assert "C1-G54-LoRA" in names
        assert "C2-G56+G57-RLHF" in names
        assert "C3-G59-MultiWork" in names
        assert "C4-G60-PerfSLO" in names
        assert "C5-TotalGates" in names
        assert "C6-TotalTests" in names

    def test_run_c1_g54_pass(self):
        r = run_phase_b_exit_gate(
            gates_passed=60, tests_passed=6703,
            _rg_results_override=_MOCK_RG_ALL_PASS,
        )
        c1 = next(cp for cp in r.checkpoints if cp.name == "C1-G54-LoRA")
        assert c1.passed is True

    def test_run_c2_rlhf_pass(self):
        r = run_phase_b_exit_gate(
            gates_passed=60, tests_passed=6703,
            _rg_results_override=_MOCK_RG_ALL_PASS,
        )
        c2 = next(cp for cp in r.checkpoints if cp.name == "C2-G56+G57-RLHF")
        assert c2.passed is True

    def test_run_c3_multiwork_pass(self):
        r = run_phase_b_exit_gate(
            gates_passed=60, tests_passed=6703,
            _rg_results_override=_MOCK_RG_ALL_PASS,
        )
        c3 = next(cp for cp in r.checkpoints if cp.name == "C3-G59-MultiWork")
        assert c3.passed is True

    def test_run_all_pass(self):
        r = run_phase_b_exit_gate(
            gates_passed=60, tests_passed=6703,
            _rg_results_override=_MOCK_RG_ALL_PASS,
        )
        assert r.all_pass, f"실패: {r.failed_checkpoints}"

    def test_run_gates_total_positive(self):
        r = run_phase_b_exit_gate(
            gates_passed=60, tests_passed=6703,
            _rg_results_override=_MOCK_RG_ALL_PASS,
        )
        assert r.gates_total > 0


# ===========================================================================
# TestG61GateInterface  (3 TC)  — _rg_results_override 주입 (monkeypatch)
# ===========================================================================

class TestG61GateInterface:

    def test_run_g61_returns_dict(self, monkeypatch):
        monkeypatch.setattr(
            "literary_system.gates.phase_b_exit_gate.run_phase_b_exit_gate",
            lambda **kw: run_phase_b_exit_gate(
                gates_passed=60, tests_passed=6703,
                _rg_results_override=_MOCK_RG_ALL_PASS,
            ),
        )
        result = run_g61_gate()
        assert isinstance(result, dict)

    def test_run_g61_has_required_keys(self, monkeypatch):
        monkeypatch.setattr(
            "literary_system.gates.phase_b_exit_gate.run_phase_b_exit_gate",
            lambda **kw: run_phase_b_exit_gate(
                gates_passed=60, tests_passed=6703,
                _rg_results_override=_MOCK_RG_ALL_PASS,
            ),
        )
        result = run_g61_gate()
        for key in ["gate", "pass", "passed_count", "total_count", "summary"]:
            assert key in result, f"누락 키: {key}"

    def test_run_g61_gate_id(self, monkeypatch):
        monkeypatch.setattr(
            "literary_system.gates.phase_b_exit_gate.run_phase_b_exit_gate",
            lambda **kw: run_phase_b_exit_gate(
                gates_passed=60, tests_passed=6703,
                _rg_results_override=_MOCK_RG_ALL_PASS,
            ),
        )
        result = run_g61_gate()
        assert result["gate"] == "G61"


# ===========================================================================
# TestEdgeCases  (3 TC)
# ===========================================================================

class TestEdgeCases:

    def test_c5_fail_when_gates_below_threshold(self):
        """gates_passed=59 이면 C5 실패해야 한다."""
        r = run_phase_b_exit_gate(
            gates_passed=59, tests_passed=7000,
            _rg_results_override=_MOCK_RG_ALL_PASS,
        )
        c5 = next(cp for cp in r.checkpoints if cp.name == "C5-TotalGates")
        assert c5.passed is False
        assert r.all_pass is False

    def test_c6_fail_when_tests_below_threshold(self):
        """tests_passed=6699 이면 C6 실패해야 한다."""
        r = run_phase_b_exit_gate(
            gates_passed=60, tests_passed=6699,
            _rg_results_override=_MOCK_RG_ALL_PASS,
        )
        c6 = next(cp for cp in r.checkpoints if cp.name == "C6-TotalTests")
        assert c6.passed is False

    def test_min_constants_sane(self):
        assert MIN_GATES == 60
        assert MIN_TESTS >= 6700
