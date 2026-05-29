"""
test_v620_phase_b_exit_gate.py
V620 Phase B Exit Gate G61 단위·통합 테스트 (34 TC)

클래스 구성
-----------
TestCheckpointResult        (4 TC) — 필드, to_dict
TestPhaseBExitReport        (8 TC) — 집계 프로퍼티, summary, to_dict (+ 빈 리스트 방어)
TestPhaseBExitGateRun       (8 TC) — run_phase_b_exit_gate (mock 주입)
TestG61GateInterface        (3 TC) — run_g61_gate() 인터페이스 (mock 주입)
TestEdgeCases               (3 TC) — 경계값 + 실패 경로
TestCheckpointIndividualFails (8 TC) — C1~C4 단독 실패 + 복합 실패 (아키텍처·컴파일러 검증 보강)
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

_MOCK_RG_C2_FAIL = {
    "gates_passed": 60,
    "results": {
        "lora_finetuning_g54":    {"pass": True,  "gate": "G54"},
        "rlhf_reward_g56":        {"pass": False, "gate": "G56"},  # G56 단독 실패
        "constitution_axis_g57":  {"pass": True,  "gate": "G57"},
        "sp_b3_exit_g59":         {"pass": True,  "gate": "G59"},
        "performance_slo_g60":    {"pass": True,  "gate": "G60"},
    },
}

_MOCK_RG_C2_G57_FAIL = {
    "gates_passed": 60,
    "results": {
        "lora_finetuning_g54":    {"pass": True,  "gate": "G54"},
        "rlhf_reward_g56":        {"pass": True,  "gate": "G56"},
        "constitution_axis_g57":  {"pass": False, "gate": "G57"},  # G57 단독 실패
        "sp_b3_exit_g59":         {"pass": True,  "gate": "G59"},
        "performance_slo_g60":    {"pass": True,  "gate": "G60"},
    },
}

_MOCK_RG_C3_FAIL = {
    "gates_passed": 60,
    "results": {
        "lora_finetuning_g54":    {"pass": True,  "gate": "G54"},
        "rlhf_reward_g56":        {"pass": True,  "gate": "G56"},
        "constitution_axis_g57":  {"pass": True,  "gate": "G57"},
        "sp_b3_exit_g59":         {"pass": False, "gate": "G59"},  # G59 단독 실패
        "performance_slo_g60":    {"pass": True,  "gate": "G60"},
    },
}

_MOCK_RG_C4_FAIL = {
    "gates_passed": 60,
    "results": {
        "lora_finetuning_g54":    {"pass": True,  "gate": "G54"},
        "rlhf_reward_g56":        {"pass": True,  "gate": "G56"},
        "constitution_axis_g57":  {"pass": True,  "gate": "G57"},
        "sp_b3_exit_g59":         {"pass": True,  "gate": "G59"},
        "performance_slo_g60":    {"pass": False, "gate": "G60"},  # G60 단독 실패
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


# ===========================================================================
# TestCheckpointIndividualFails  (8 TC) — 아키텍처·컴파일러 검증 보강 2026-05-23
# C1~C4 각각의 단독 실패 + 복합 실패 시나리오
# ===========================================================================

class TestCheckpointIndividualFails:

    def test_c1_fail_when_g54_fails(self):
        """C1(G54 LoRA) 단독 실패 — all_pass=False, failed_checkpoints에 C1 포함."""
        r = run_phase_b_exit_gate(
            gates_passed=60, tests_passed=6728,
            _rg_results_override=_MOCK_RG_C1_FAIL,
        )
        c1 = next(cp for cp in r.checkpoints if "C1" in cp.name)
        assert c1.passed is False
        assert r.all_pass is False
        assert any("C1" in fc for fc in r.failed_checkpoints)

    def test_c2_fail_when_g56_fails(self):
        """C2(G56+G57 RLHF) — G56 단독 실패 시 C2 FAIL."""
        r = run_phase_b_exit_gate(
            gates_passed=60, tests_passed=6728,
            _rg_results_override=_MOCK_RG_C2_FAIL,
        )
        c2 = next(cp for cp in r.checkpoints if "C2" in cp.name)
        assert c2.passed is False
        assert r.all_pass is False

    def test_c2_fail_when_g57_fails(self):
        """C2(G56+G57 RLHF) — G57 단독 실패 시 C2 FAIL (AND 조건 검증)."""
        r = run_phase_b_exit_gate(
            gates_passed=60, tests_passed=6728,
            _rg_results_override=_MOCK_RG_C2_G57_FAIL,
        )
        c2 = next(cp for cp in r.checkpoints if "C2" in cp.name)
        assert c2.passed is False
        assert r.all_pass is False

    def test_c3_fail_when_g59_fails(self):
        """C3(G59 SP-B.3 Exit) 단독 실패."""
        r = run_phase_b_exit_gate(
            gates_passed=60, tests_passed=6728,
            _rg_results_override=_MOCK_RG_C3_FAIL,
        )
        c3 = next(cp for cp in r.checkpoints if "C3" in cp.name)
        assert c3.passed is False
        assert r.all_pass is False

    def test_c4_fail_when_g60_fails(self):
        """C4(G60 PerformanceSLO) 단독 실패."""
        r = run_phase_b_exit_gate(
            gates_passed=60, tests_passed=6728,
            _rg_results_override=_MOCK_RG_C4_FAIL,
        )
        c4 = next(cp for cp in r.checkpoints if "C4" in cp.name)
        assert c4.passed is False
        assert r.all_pass is False

    def test_empty_results_all_c1_c4_fail(self):
        """빈 results dict — C1~C4 모두 FAIL, C5/C6은 gates/tests 값에 따라 결정."""
        r = run_phase_b_exit_gate(
            gates_passed=0, tests_passed=0,
            _rg_results_override={"gates_passed": 0, "results": {}},
        )
        assert r.all_pass is False
        assert r.passed_count == 0

    def test_all_pass_false_for_empty_checkpoints(self):
        """BUG-C4-1 수정 검증: 빈 checkpoints 시 all_pass=False (all([]) 방어)."""
        report = PhaseBExitReport()
        assert report.all_pass is False  # all([]) = True 방어 확인

    def test_partial_fail_failed_checkpoints_list_accuracy(self):
        """복합 실패 시 failed_checkpoints 목록이 정확히 수집되는지 검증."""
        r = run_phase_b_exit_gate(
            gates_passed=59, tests_passed=6699,  # C5+C6 모두 실패
            _rg_results_override=_MOCK_RG_ALL_PASS,
        )
        assert len(r.failed_checkpoints) == 2
        assert any("C5" in fc for fc in r.failed_checkpoints)
        assert any("C6" in fc for fc in r.failed_checkpoints)
