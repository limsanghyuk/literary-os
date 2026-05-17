"""V400 Endurance Gate + Production Proof Tests"""
import pytest
import json
from literary_system.proof.production_proof import ProductionProof, ProofPack
from literary_system.gates.endurance_gate import EnduranceGate, GateResult

class TestProofPack:
    def setup_method(self):
        self.proof = ProductionProof()
        self.pack = self.proof.generate(episode_count=16, genre="korean_drama")

    def test_generate_returns_proof_pack(self):
        assert isinstance(self.pack, ProofPack)

    def test_episode_count_matches(self):
        assert self.pack.episode_count == 16

    def test_has_series_title(self):
        assert isinstance(self.pack.series_title, str)

    def test_has_summary(self):
        assert isinstance(self.pack.summary, dict)

    def test_microplot_matrix_csv_is_string(self):
        assert isinstance(self.pack.microplot_matrix_csv, str)
        assert len(self.pack.microplot_matrix_csv) > 0

    def test_fractal_report_is_dict(self):
        assert isinstance(self.pack.fractal_report, dict)
        assert "orphan_microplot_count" in self.pack.fractal_report

    def test_load_curve_length(self):
        assert len(self.pack.load_curve) == 16

    def test_agency_curves_has_characters(self):
        assert isinstance(self.pack.agency_curves, dict)
        assert len(self.pack.agency_curves) > 0

    def test_debt_summary_keys(self):
        for k in ["total", "paid", "defaulted", "critical_defaults", "open"]:
            assert k in self.pack.debt_summary

    def test_necessity_weak_ratio_is_float(self):
        assert isinstance(self.pack.necessity_weak_ratio, float)
        assert 0.0 <= self.pack.necessity_weak_ratio <= 1.0

    def test_dialogue_consistent_is_bool(self):
        assert isinstance(self.pack.dialogue_consistent, bool)

    def test_voice_drift_blocked_is_int(self):
        assert isinstance(self.pack.voice_drift_blocked, int)

    def test_fatigue_risks_are_floats(self):
        assert 0.0 <= self.pack.fatigue_mid_risk <= 1.0
        assert 0.0 <= self.pack.fatigue_finale_risk <= 1.0

    def test_overall_pass_is_bool(self):
        assert isinstance(self.pack.overall_pass, bool)

    def test_gate_results_is_dict(self):
        assert isinstance(self.pack.gate_results, dict)

    def test_gate_results_has_all_modules(self):
        expected = [
            "fractal_topology", "load_balancing", "agency_conservation",
            "payoff_debt", "scene_necessity", "dialogue_pragmatics",
            "voice_manifold", "attention_economy"
        ]
        for k in expected:
            assert k in self.pack.gate_results

    def test_synthetic_16ep_overall_pass(self):
        assert self.pack.overall_pass is True

    def test_to_json_returns_valid_json(self):
        j = self.pack.to_json()
        assert isinstance(j, str)
        parsed = json.loads(j)
        assert isinstance(parsed, dict)
        assert parsed["episode_count"] == 16

    def test_to_json_has_gate_results(self):
        parsed = json.loads(self.pack.to_json())
        assert "gate_results" in parsed

class TestEnduranceGate:
    def setup_method(self):
        self.gate = EnduranceGate()
        self.pack = ProductionProof().generate(episode_count=16)

    def test_run_returns_gate_result(self):
        result = self.gate.run(self.pack)
        assert isinstance(result, GateResult)

    def test_14_checks_run(self):
        result = self.gate.run(self.pack)
        assert len(result.checks) == 14

    def test_all_check_names_present(self):
        result = self.gate.run(self.pack)
        expected = [
            "episode_layer", "fractal_topology", "dramatic_load_balancing",
            "agency_conservation", "payoff_debt_ledger", "scene_necessity",
            "dialogue_pragmatics", "voice_manifold", "attention_economy",
            "production_proof", "node2_surface_guard", "provider_zero",
            "branchpoint_survival", "v390_baseline"
        ]
        for check in expected:
            assert check in result.checks, f"Missing check: {check}"

    def test_synthetic_16ep_passes_all_gates(self):
        result = self.gate.run(self.pack)
        assert result.passed is True

    def test_no_failures_on_pass(self):
        result = self.gate.run(self.pack)
        assert len(result.failures) == 0

    def test_provider_zero_check(self):
        result = self.gate.run(self.pack)
        assert result.checks["provider_zero"] is True

    def test_node2_surface_guard(self):
        result = self.gate.run(self.pack)
        assert result.checks["node2_surface_guard"] is True

    def test_v390_baseline_passes(self):
        result = self.gate.run(self.pack)
        assert result.checks["v390_baseline"] is True

    def test_gate_result_passed_is_bool(self):
        result = self.gate.run(self.pack)
        assert isinstance(result.passed, bool)

    def test_to_dict_method(self):
        result = self.gate.run(self.pack)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "passed" in d
        assert "checks" in d
        assert "failures" in d
        assert "pass_count" in d
        assert "total_checks" in d

    def test_to_dict_total_checks_14(self):
        result = self.gate.run(self.pack)
        d = result.to_dict()
        assert d["total_checks"] == 14

    def test_to_dict_pass_count_14_on_pass(self):
        result = self.gate.run(self.pack)
        d = result.to_dict()
        assert d["pass_count"] == 14

    def test_fractal_topology_check(self):
        result = self.gate.run(self.pack)
        assert result.checks["fractal_topology"] is True

    def test_agency_conservation_check(self):
        result = self.gate.run(self.pack)
        assert result.checks["agency_conservation"] is True

    def test_scene_necessity_check(self):
        result = self.gate.run(self.pack)
        assert result.checks["scene_necessity"] is True

    def test_payoff_debt_check(self):
        result = self.gate.run(self.pack)
        assert result.checks["payoff_debt_ledger"] is True

    def test_voice_manifold_check(self):
        result = self.gate.run(self.pack)
        assert result.checks["voice_manifold"] is True

    def test_attention_economy_check(self):
        result = self.gate.run(self.pack)
        assert result.checks["attention_economy"] is True

    def test_production_proof_check(self):
        result = self.gate.run(self.pack)
        assert result.checks["production_proof"] is True

