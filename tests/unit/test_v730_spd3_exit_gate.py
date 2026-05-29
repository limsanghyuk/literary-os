"""
tests/unit/test_v730_spd3_exit_gate.py
V730 — SP-D.3 Exit Gate 테스트 (TC01~TC33, 33개)
ADR-191
"""
import pytest
from pathlib import Path


# ── TC01~TC06: ExitAxisResult / SPD3ExitReport ────────────────────────────────

class TestDataClasses:
    def test_tc01_exit_axis_result_frozen(self):
        from literary_system.gates.spd3_exit_gate import ExitAxisResult
        r = ExitAxisResult("E1", True, "ok")
        with pytest.raises((AttributeError, TypeError)):
            r.passed = False  # type: ignore

    def test_tc02_report_initial(self):
        from literary_system.gates.spd3_exit_gate import SPD3ExitReport
        rpt = SPD3ExitReport()
        assert rpt.gate == "SP-D3-EXIT"
        assert rpt.total_count == 6
        assert not rpt.passed

    def test_tc03_report_to_dict_keys(self):
        from literary_system.gates.spd3_exit_gate import SPD3ExitReport
        d = SPD3ExitReport().to_dict()
        for k in ("gate", "pass", "passed", "passed_count", "total_count", "version", "axes", "errors"):
            assert k in d

    def test_tc04_ax_helper_passed(self):
        from literary_system.gates.spd3_exit_gate import _ax
        r = _ax("E1", True, "good")
        assert r.passed and r.axis == "E1"

    def test_tc05_ax_helper_failed(self):
        from literary_system.gates.spd3_exit_gate import _ax
        r = _ax("E2", False, "bad")
        assert not r.passed

    def test_tc06_survival_symbols_count(self):
        from literary_system.gates.spd3_exit_gate import _SPD3_SURVIVAL_SYMBOLS
        assert len(_SPD3_SURVIVAL_SYMBOLS) >= 9


# ── TC07~TC12: E1 Plugin Registry ─────────────────────────────────────────────

class TestE1PluginRegistry:
    def test_tc07_g87_importable(self):
        from literary_system.gates.plugin_registry_gate import run_g87_gate
        assert callable(run_g87_gate)

    def test_tc08_g87_returns_dict(self):
        from literary_system.gates.plugin_registry_gate import run_g87_gate
        result = run_g87_gate()
        assert isinstance(result, dict)

    def test_tc09_g87_has_gate_key(self):
        from literary_system.gates.plugin_registry_gate import run_g87_gate
        result = run_g87_gate()
        assert "gate" in result or "passed" in result

    def test_tc10_e1_check_returns_axis(self):
        from literary_system.gates.spd3_exit_gate import _check_e1_plugin_registry
        r = _check_e1_plugin_registry()
        assert r.axis == "E1"

    def test_tc11_e1_axis_bool(self):
        from literary_system.gates.spd3_exit_gate import _check_e1_plugin_registry
        r = _check_e1_plugin_registry()
        assert isinstance(r.passed, bool)

    def test_tc12_e1_detail_not_empty(self):
        from literary_system.gates.spd3_exit_gate import _check_e1_plugin_registry
        r = _check_e1_plugin_registry()
        assert len(r.detail) > 0


# ── TC13~TC16: E2 ZeroTrust ───────────────────────────────────────────────────

class TestE2ZeroTrust:
    def test_tc13_g88_importable(self):
        from literary_system.gates.zero_trust_security_gate import run_zero_trust_security_gate
        assert callable(run_zero_trust_security_gate)

    def test_tc14_e2_returns_axis(self):
        from literary_system.gates.spd3_exit_gate import _check_e2_zerotrust
        r = _check_e2_zerotrust()
        assert r.axis == "E2"

    def test_tc15_e2_has_bool(self):
        from literary_system.gates.spd3_exit_gate import _check_e2_zerotrust
        r = _check_e2_zerotrust()
        assert isinstance(r.passed, bool)

    def test_tc16_e2_detail_str(self):
        from literary_system.gates.spd3_exit_gate import _check_e2_zerotrust
        r = _check_e2_zerotrust()
        assert isinstance(r.detail, str)


# ── TC17~TC20: E3 Chaos Resilience ────────────────────────────────────────────

class TestE3ChaosResilience:
    def test_tc17_g89_importable(self):
        from literary_system.gates.chaos_resilience_gate import run_g89_gate
        assert callable(run_g89_gate)

    def test_tc18_e3_returns_axis(self):
        from literary_system.gates.spd3_exit_gate import _check_e3_chaos_resilience
        r = _check_e3_chaos_resilience()
        assert r.axis == "E3"

    def test_tc19_e3_bool(self):
        from literary_system.gates.spd3_exit_gate import _check_e3_chaos_resilience
        r = _check_e3_chaos_resilience()
        assert isinstance(r.passed, bool)

    def test_tc20_e3_detail_not_empty(self):
        from literary_system.gates.spd3_exit_gate import _check_e3_chaos_resilience
        r = _check_e3_chaos_resilience()
        assert r.detail


# ── TC21~TC24: E4 Connectivity ────────────────────────────────────────────────

class TestE4Connectivity:
    def test_tc21_e4_returns_axis(self):
        from literary_system.gates.spd3_exit_gate import _check_e4_connectivity
        r = _check_e4_connectivity()
        assert r.axis == "E4"

    def test_tc22_e4_bool(self):
        from literary_system.gates.spd3_exit_gate import _check_e4_connectivity
        r = _check_e4_connectivity()
        assert isinstance(r.passed, bool)

    def test_tc23_security_importable_from_plugins(self):
        """plugins/ → security/ 의존 확인 (고립 해소 핵심)"""
        from literary_system.plugins.plugin_auth import PluginAuthAdapter
        assert PluginAuthAdapter is not None

    def test_tc24_chaos_importable(self):
        from literary_system.chaos import ChaosEngine, ChaosRunner
        assert ChaosEngine and ChaosRunner


# ── TC25~TC28: E5 Survival Matrix ─────────────────────────────────────────────

class TestE5SurvivalMatrix:
    def test_tc25_e5_returns_axis(self):
        from literary_system.gates.spd3_exit_gate import _check_e5_survival_matrix
        r = _check_e5_survival_matrix()
        assert r.axis == "E5"

    def test_tc26_zerotrust_token_service_alive(self):
        from literary_system.security import ZeroTrustTokenService
        assert ZeroTrustTokenService

    def test_tc27_plugin_manifest_alive(self):
        from literary_system.plugins.plugin_manifest import PluginManifest
        assert PluginManifest

    def test_tc28_chaos_engine_alive(self):
        from literary_system.chaos.chaos_engine import ChaosEngine
        assert ChaosEngine


# ── TC29~TC33: run_spd3_exit_gate() 통합 ─────────────────────────────────────

class TestRunSPD3ExitGate:
    def test_tc29_returns_dict(self):
        from literary_system.gates.spd3_exit_gate import run_spd3_exit_gate
        result = run_spd3_exit_gate()
        assert isinstance(result, dict)

    def test_tc30_gate_name(self):
        from literary_system.gates.spd3_exit_gate import run_spd3_exit_gate
        result = run_spd3_exit_gate()
        assert result["gate"] == "SP-D3-EXIT"

    def test_tc31_six_axes(self):
        from literary_system.gates.spd3_exit_gate import run_spd3_exit_gate
        result = run_spd3_exit_gate()
        assert result["total_count"] == 6
        assert len(result["axes"]) == 6

    def test_tc32_axes_labels(self):
        from literary_system.gates.spd3_exit_gate import run_spd3_exit_gate
        result = run_spd3_exit_gate()
        labels = {a["axis"] for a in result["axes"]}
        for lbl in ("E1", "E2", "E3", "E4", "E5", "E6"):
            assert lbl in labels

    def test_tc33_class_interface(self):
        from literary_system.gates.spd3_exit_gate import SPD3ExitGate
        gate = SPD3ExitGate()
        result = gate.run()
        assert "gate" in result
        assert len(gate.survival_symbols) >= 9
