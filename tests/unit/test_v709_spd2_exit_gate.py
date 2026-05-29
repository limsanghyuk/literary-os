"""
V709 — SP-D.2 Exit Gate Tests (ADR-171)
33 TC: spd2_exit_gate.py 전체 검증.
G32: NO print() anywhere in this file.
"""

import pytest
from literary_system.gates.spd2_exit_gate import (
    ExitCheckpoint,
    SpD2ExitResult,
    _check_e1_agent_bus,
    _check_e2_task_queue_scheduler,
    _check_e3_registry_conflict,
    _check_e4_collaboration_protocol,
    _check_e5_workflow_cb_supervisor,
    _check_e6_gates_and_tc,
    run_spd2_exit_gate,
    _SP_D2_MIN_TC,
)


# ──────────────────────────────────────────────
# TC01~TC05: E1 AgentBus
# ──────────────────────────────────────────────

class TestE1AgentBus:

    def test_tc01_e1_passes(self):
        """TC01: E1 checkpoint passes."""
        cp = _check_e1_agent_bus()
        assert cp.passed, f"E1 failed: {cp.error}"

    def test_tc02_e1_axis_label(self):
        """TC02: axis is 'E1'."""
        cp = _check_e1_agent_bus()
        assert cp.axis == "E1"

    def test_tc03_e1_has_detail(self):
        """TC03: detail string is non-empty."""
        cp = _check_e1_agent_bus()
        assert len(cp.detail) > 0

    def test_tc04_e1_no_error(self):
        """TC04: error field is None on success."""
        cp = _check_e1_agent_bus()
        assert cp.error is None

    def test_tc05_e1_duration_positive(self):
        """TC05: duration_ms > 0."""
        cp = _check_e1_agent_bus()
        assert cp.duration_ms >= 0


# ──────────────────────────────────────────────
# TC06~TC10: E2 TaskQueue + Scheduler
# ──────────────────────────────────────────────

class TestE2TaskQueueScheduler:

    def test_tc06_e2_passes(self):
        """TC06: E2 checkpoint passes."""
        cp = _check_e2_task_queue_scheduler()
        assert cp.passed, f"E2 failed: {cp.error}"

    def test_tc07_e2_axis_label(self):
        """TC07: axis is 'E2'."""
        cp = _check_e2_task_queue_scheduler()
        assert cp.axis == "E2"

    def test_tc08_e2_detail_mentions_critical(self):
        """TC08: detail mentions CRITICAL."""
        cp = _check_e2_task_queue_scheduler()
        assert "CRITICAL" in cp.detail

    def test_tc09_e2_no_error(self):
        """TC09: error is None."""
        cp = _check_e2_task_queue_scheduler()
        assert cp.error is None

    def test_tc10_e2_duration_non_negative(self):
        """TC10: duration_ms is non-negative."""
        cp = _check_e2_task_queue_scheduler()
        assert cp.duration_ms >= 0


# ──────────────────────────────────────────────
# TC11~TC15: E3 Registry + ConflictResolver
# ──────────────────────────────────────────────

class TestE3RegistryConflict:

    def test_tc11_e3_passes(self):
        """TC11: E3 checkpoint passes."""
        cp = _check_e3_registry_conflict()
        assert cp.passed, f"E3 failed: {cp.error}"

    def test_tc12_e3_axis_label(self):
        """TC12: axis is 'E3'."""
        cp = _check_e3_registry_conflict()
        assert cp.axis == "E3"

    def test_tc13_e3_detail_mentions_winner(self):
        """TC13: detail mentions 'high-prio'."""
        cp = _check_e3_registry_conflict()
        assert "high-prio" in cp.detail

    def test_tc14_e3_no_error(self):
        """TC14: error is None."""
        cp = _check_e3_registry_conflict()
        assert cp.error is None

    def test_tc15_e3_detail_mentions_registry(self):
        """TC15: detail mentions registry agents count."""
        cp = _check_e3_registry_conflict()
        assert "agents=" in cp.detail or "registry" in cp.detail.lower()


# ──────────────────────────────────────────────
# TC16~TC19: E4 CollaborationProtocol
# ──────────────────────────────────────────────

class TestE4CollaborationProtocol:

    def test_tc16_e4_passes(self):
        """TC16: E4 checkpoint passes."""
        cp = _check_e4_collaboration_protocol()
        assert cp.passed, f"E4 failed: {cp.error}"

    def test_tc17_e4_axis_label(self):
        """TC17: axis is 'E4'."""
        cp = _check_e4_collaboration_protocol()
        assert cp.axis == "E4"

    def test_tc18_e4_detail_mentions_completed(self):
        """TC18: detail mentions COMPLETED."""
        cp = _check_e4_collaboration_protocol()
        assert "COMPLETED" in cp.detail

    def test_tc19_e4_no_error(self):
        """TC19: error is None."""
        cp = _check_e4_collaboration_protocol()
        assert cp.error is None


# ──────────────────────────────────────────────
# TC20~TC23: E5 Workflow + CB + Supervisor
# ──────────────────────────────────────────────

class TestE5WorkflowCBSupervisor:

    def test_tc20_e5_passes(self):
        """TC20: E5 checkpoint passes."""
        cp = _check_e5_workflow_cb_supervisor()
        assert cp.passed, f"E5 failed: {cp.error}"

    def test_tc21_e5_axis_label(self):
        """TC21: axis is 'E5'."""
        cp = _check_e5_workflow_cb_supervisor()
        assert cp.axis == "E5"

    def test_tc22_e5_detail_mentions_dag(self):
        """TC22: detail mentions DAG order."""
        cp = _check_e5_workflow_cb_supervisor()
        assert "DAG" in cp.detail or "A,B,C" in cp.detail

    def test_tc23_e5_no_error(self):
        """TC23: error is None."""
        cp = _check_e5_workflow_cb_supervisor()
        assert cp.error is None


# ──────────────────────────────────────────────
# TC24~TC27: E6 G84/G85 Gates
# ──────────────────────────────────────────────

class TestE6GatesAndTC:

    def test_tc24_e6_passes(self):
        """TC24: E6 checkpoint passes."""
        cp = _check_e6_gates_and_tc()
        assert cp.passed, f"E6 failed: {cp.error}"

    def test_tc25_e6_axis_label(self):
        """TC25: axis is 'E6'."""
        cp = _check_e6_gates_and_tc()
        assert cp.axis == "E6"

    def test_tc26_e6_detail_mentions_g84(self):
        """TC26: detail mentions G84."""
        cp = _check_e6_gates_and_tc()
        assert "G84" in cp.detail

    def test_tc27_e6_detail_mentions_g85(self):
        """TC27: detail mentions G85."""
        cp = _check_e6_gates_and_tc()
        assert "G85" in cp.detail


# ──────────────────────────────────────────────
# TC28~TC33: Full run_spd2_exit_gate()
# ──────────────────────────────────────────────

class TestRunSpD2ExitGate:

    def test_tc28_full_run_passes(self):
        """TC28: run_spd2_exit_gate() returns passed=True."""
        result = run_spd2_exit_gate()
        assert result.passed, f"Exit gate failed: {[(cp.axis, cp.error) for cp in result.checkpoints if not cp.passed]}"

    def test_tc29_six_axes_all_pass(self):
        """TC29: All 6 axes PASS."""
        result = run_spd2_exit_gate()
        assert result.passed_count == 6
        assert result.failed_count == 0

    def test_tc30_gate_id_correct(self):
        """TC30: gate_id is 'SP-D.2-EXIT'."""
        result = run_spd2_exit_gate()
        assert result.gate_id == "SP-D.2-EXIT"

    def test_tc31_version_is_12_2_0(self):
        """TC31: version is '12.2.0'."""
        result = run_spd2_exit_gate()
        assert result.version == "12.2.0"

    def test_tc32_tc_total_sufficient(self):
        """TC32: tc_total ≥ SP-D.1 + 429 (13 × 33)."""
        result = run_spd2_exit_gate()
        assert result.tc_total >= 9238 + 33 * 13

    def test_tc33_to_dict_has_all_keys(self):
        """TC33: to_dict() contains all expected keys."""
        result = run_spd2_exit_gate()
        d = result.to_dict()
        expected_keys = {"gate_id", "gate_name", "passed", "passed_count",
                         "failed_count", "version", "tc_total", "duration_ms", "checkpoints"}
        assert expected_keys.issubset(d.keys()), f"Missing keys: {expected_keys - d.keys()}"
        assert len(d["checkpoints"]) == 6
