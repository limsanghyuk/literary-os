"""
test_v645_self_learning_gate.py
V645 — SelfLearningGate G63 + SP-C.1 완료 (ADR-105)
33 Test Cases
"""
import math
import pytest
from literary_system.gates.self_learning_gate import (
    SelfLearningGate,
    SelfLearningGateReport,
    SLGAxisResult,
    _kl_divergence_from_uniform,
    run_g63_gate,
    KL_MAX,
    ALPHA_MIN,
    CONTAMINATION_MAX,
    N_CONSTITUTION_AXES,
)

# 모든 Gate 테스트는 in-memory 모드 사용 (파일 I/O 격리)
_MEM = ":memory:"


# ──────────────────────────────────────────────
# TC-001~005  Constants
# ──────────────────────────────────────────────
class TestConstants:
    def test_kl_max(self):
        """TC-001 KL_MAX == 0.05"""
        assert KL_MAX == 0.05

    def test_alpha_min(self):
        """TC-002 ALPHA_MIN == 0.70"""
        assert ALPHA_MIN == 0.70

    def test_contamination_max(self):
        """TC-003 CONTAMINATION_MAX == 0.0"""
        assert CONTAMINATION_MAX == 0.0

    def test_n_constitution_axes(self):
        """TC-004 N_CONSTITUTION_AXES == 5"""
        assert N_CONSTITUTION_AXES == 5

    def test_constants_types(self):
        """TC-005 constants are float/int"""
        assert isinstance(KL_MAX, float)
        assert isinstance(ALPHA_MIN, float)
        assert isinstance(CONTAMINATION_MAX, float)
        assert isinstance(N_CONSTITUTION_AXES, int)


# ──────────────────────────────────────────────
# TC-006~012  _kl_divergence_from_uniform
# ──────────────────────────────────────────────
class TestKLDivergence:
    def test_uniform_weights_kl_zero(self):
        """TC-006 uniform weights → KL == 0.0"""
        weights = [0.2, 0.2, 0.2, 0.2, 0.2]
        kl = _kl_divergence_from_uniform(weights)
        assert abs(kl) < 1e-10

    def test_standard_constitution_weights(self):
        """TC-007 standard ConstitutionWeights → KL < 0.05"""
        weights = [0.30, 0.20, 0.20, 0.15, 0.15]
        kl = _kl_divergence_from_uniform(weights)
        assert kl < KL_MAX

    def test_standard_constitution_weights_value(self):
        """TC-008 standard weights KL ≈ 0.03533"""
        weights = [0.30, 0.20, 0.20, 0.15, 0.15]
        kl = _kl_divergence_from_uniform(weights)
        assert abs(kl - 0.03533) < 0.001

    def test_extreme_concentration_kl_high(self):
        """TC-009 extreme weights → KL > 0.05"""
        weights = [0.80, 0.05, 0.05, 0.05, 0.05]
        kl = _kl_divergence_from_uniform(weights)
        assert kl > KL_MAX

    def test_kl_non_negative(self):
        """TC-010 KL divergence is always ≥ 0"""
        for weights in [
            [0.2, 0.2, 0.2, 0.2, 0.2],
            [0.30, 0.20, 0.20, 0.15, 0.15],
            [0.5, 0.25, 0.15, 0.05, 0.05],
        ]:
            assert _kl_divergence_from_uniform(weights) >= 0.0

    def test_kl_empty_weights(self):
        """TC-011 empty list → KL == 0.0"""
        assert _kl_divergence_from_uniform([]) == 0.0

    def test_kl_single_weight(self):
        """TC-012 single weight [1.0] → KL == 0.0 (trivially uniform)"""
        kl = _kl_divergence_from_uniform([1.0])
        assert kl == 0.0


# ──────────────────────────────────────────────
# TC-013~018  SLGAxisResult dataclass
# ──────────────────────────────────────────────
class TestAxisResult:
    def test_axis_result_creation(self):
        """TC-013 SLGAxisResult instantiation with correct fields"""
        ar = SLGAxisResult(axis_name="contamination", value=0.0, threshold=0.0, passed=True, detail="ok")
        assert ar.axis_name == "contamination"
        assert ar.value == 0.0
        assert ar.passed is True

    def test_axis_result_failed(self):
        """TC-014 SLGAxisResult with passed=False"""
        ar = SLGAxisResult(axis_name="kl_divergence", value=0.06, threshold=0.05, passed=False, detail="KL too high")
        assert ar.passed is False

    def test_axis_result_default_detail(self):
        """TC-015 SLGAxisResult detail defaults to empty string"""
        ar = SLGAxisResult(axis_name="alpha", value=0.75, threshold=0.70, passed=True)
        assert ar.detail == ""

    def test_axis_result_to_dict(self):
        """TC-016 SLGAxisResult.to_dict returns correct keys"""
        ar = SLGAxisResult(axis_name="contamination", value=0.0, threshold=0.0, passed=True, detail="clean")
        d = ar.to_dict()
        assert "axis_name" in d and "value" in d and "threshold" in d
        assert "passed" in d and "detail" in d

    def test_axis_result_from_dict_roundtrip(self):
        """TC-017 SLGAxisResult from_dict roundtrip"""
        ar = SLGAxisResult(axis_name="alpha", value=0.75, threshold=0.70, passed=True, detail="ok")
        ar2 = SLGAxisResult.from_dict(ar.to_dict())
        assert ar2.axis_name == ar.axis_name
        assert abs(ar2.value - ar.value) < 1e-9
        assert ar2.passed == ar.passed

    def test_axis_three_axes_from_evaluate(self):
        """TC-018 evaluate produces 3 axes (contamination, kl, alpha)"""
        gate = SelfLearningGate(store_path=_MEM)
        report = gate.evaluate(0.0, [0.30, 0.20, 0.20, 0.15, 0.15], 0.75)
        axis_names = [a.axis_name for a in report.axes]
        assert "contamination" in axis_names
        assert "kl_divergence" in axis_names
        assert "alpha" in axis_names


# ──────────────────────────────────────────────
# TC-019~025  SelfLearningGateReport
# ──────────────────────────────────────────────
class TestSelfLearningGateReport:
    def _make_gate_report(self, contamination=0.0, weights=None, alpha=0.75):
        if weights is None:
            weights = [0.30, 0.20, 0.20, 0.15, 0.15]
        gate = SelfLearningGate(store_path=_MEM)
        return gate.evaluate(contamination, weights, alpha)

    def test_report_passed(self):
        """TC-019 report.passed == True when all conditions met"""
        report = self._make_gate_report(0.0, [0.30, 0.20, 0.20, 0.15, 0.15], 0.80)
        assert report.passed is True

    def test_report_failed_contamination(self):
        """TC-020 report.passed == False when contamination > 0"""
        report = self._make_gate_report(0.1, [0.30, 0.20, 0.20, 0.15, 0.15], 0.80)
        assert report.passed is False

    def test_report_has_notes_default(self):
        """TC-021 report.notes is list"""
        report = self._make_gate_report()
        assert isinstance(report.notes, list)

    def test_report_has_report_id(self):
        """TC-022 report.report_id is non-empty string"""
        report = self._make_gate_report()
        assert isinstance(report.report_id, str) and len(report.report_id) > 0

    def test_report_has_evaluated_at(self):
        """TC-023 report.evaluated_at is non-empty string"""
        report = self._make_gate_report()
        assert isinstance(report.evaluated_at, str) and len(report.evaluated_at) > 0

    def test_report_contamination_rate(self):
        """TC-024 report stores contamination_rate correctly"""
        report = self._make_gate_report(contamination=0.0)
        assert report.contamination_rate == 0.0

    def test_report_kl_divergence_stored(self):
        """TC-025 report stores kl_divergence"""
        report = self._make_gate_report()
        assert isinstance(report.kl_divergence, float)
        assert report.kl_divergence >= 0.0


# ──────────────────────────────────────────────
# TC-026~031  SelfLearningGate class
# ──────────────────────────────────────────────
class TestSelfLearningGate:
    def _w(self):
        return [0.30, 0.20, 0.20, 0.15, 0.15]

    def test_gate_pass_all_conditions(self):
        """TC-026 evaluate passes when contamination=0, KL<0.05, alpha>=0.70"""
        gate = SelfLearningGate(store_path=_MEM)
        report = gate.evaluate(0.0, self._w(), 0.75)
        assert report.passed is True

    def test_gate_fail_kl_high(self):
        """TC-027 evaluate fails when KL >= 0.05"""
        gate = SelfLearningGate(store_path=_MEM)
        report = gate.evaluate(0.0, [0.80, 0.05, 0.05, 0.05, 0.05], 0.75)
        assert report.passed is False

    def test_gate_fail_alpha_low(self):
        """TC-028 evaluate fails when alpha < 0.70"""
        gate = SelfLearningGate(store_path=_MEM)
        report = gate.evaluate(0.0, self._w(), 0.65)
        assert report.passed is False

    def test_gate_history_accumulates(self):
        """TC-029 multiple evaluations accumulate in history"""
        gate = SelfLearningGate(store_path=_MEM)
        gate.evaluate(0.0, self._w(), 0.75)
        gate.evaluate(0.0, self._w(), 0.80)
        assert gate.count() == 2

    def test_gate_last_report(self):
        """TC-030 last_report returns most recent"""
        gate = SelfLearningGate(store_path=_MEM)
        gate.evaluate(0.0, self._w(), 0.75)
        gate.evaluate(0.0, self._w(), 0.80)
        last = gate.last_report()
        assert last is not None
        assert abs(last.alpha - 0.80) < 1e-9

    def test_gate_empty_history(self):
        """TC-031 fresh in-memory gate has empty history"""
        gate = SelfLearningGate(store_path=_MEM)
        assert gate.count() == 0
        assert gate.last_report() is None


# ──────────────────────────────────────────────
# TC-032~033  run_g63_gate integration
# ──────────────────────────────────────────────
class TestRunG63Gate:
    def test_run_g63_passes(self):
        """TC-032 run_g63_gate passes (7/7 checkpoints)"""
        result = run_g63_gate()
        assert result["pass"] is True
        assert result["passed_count"] == 7
        assert result["total_count"] == 7

    def test_run_g63_gate_name(self):
        """TC-033 run_g63_gate gate_name contains G63 or SelfLearning"""
        result = run_g63_gate()
        assert "G63" in result["gate_name"] or "SelfLearning" in result["gate_name"]
