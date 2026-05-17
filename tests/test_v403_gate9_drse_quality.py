"""V403 — Gate 9 DRSEQualityGate 테스트 (17 tests)"""
import pytest
from literary_system.gates.gate9_drse_quality import (
    DRSEQualityGate, DRSEQualityResult, _gate_drse_quality
)


def _make_node_score(s_val, is_residue_min=False):
    """테스트용 NodeScore 더미 생성"""
    class FakeNodeScore:
        def __init__(self, s):
            residue_min = 0.15
            actual_s = residue_min if is_residue_min else s
            self.breakdown = {"S_semantic": actual_s}
            self.score = actual_s
            self.gate_blocked = False
    return FakeNodeScore(s_val)


class TestDRSEQualityGateBasic:
    def test_import(self):
        assert DRSEQualityGate is not None

    def test_empty_nodes_passes(self):
        gate = DRSEQualityGate()
        result = gate.run([])
        assert result.passed is True
        assert result.reason == "no_nodes_to_score"

    def test_good_scores_pass(self):
        gate = DRSEQualityGate()
        nodes = [_make_node_score(0.3) for _ in range(5)]
        result = gate.run(nodes)
        assert result.passed is True
        assert result.mean_s_score >= 0.10

    def test_low_mean_fails(self):
        gate = DRSEQualityGate()
        # 모두 0.0 — mean_s < 0.10
        nodes = [_make_node_score(0.0) for _ in range(5)]
        result = gate.run(nodes)
        assert result.passed is False
        assert "mean_s" in result.reason

    def test_high_correction_ratio_fails(self):
        gate = DRSEQualityGate()
        # 모두 RESIDUE_MIN_S(0.15) 보정값 — correction_ratio > 0.50
        nodes = [_make_node_score(0.15, is_residue_min=True) for _ in range(6)]
        result = gate.run(nodes)
        assert result.residue_correction_ratio > 0.50
        assert result.passed is False

    def test_result_fields(self):
        gate = DRSEQualityGate()
        nodes = [_make_node_score(0.25) for _ in range(3)]
        result = gate.run(nodes)
        assert isinstance(result.mean_s_score, float)
        assert isinstance(result.residue_correction_ratio, float)
        assert isinstance(result.sample_count, int)
        assert result.sample_count == 3

    def test_to_dict(self):
        gate = DRSEQualityGate()
        nodes = [_make_node_score(0.25)]
        result = gate.run(nodes)
        d = result.to_dict()
        assert "passed" in d
        assert "mean_s_score" in d
        assert "residue_correction_ratio" in d
        assert "sample_count" in d

    def test_mixed_scores(self):
        gate = DRSEQualityGate()
        # 일부 좋음, 일부 0 — 평균이 0.10 이상이면 통과
        nodes = ([_make_node_score(0.4) for _ in range(4)]
                 + [_make_node_score(0.0) for _ in range(2)])
        result = gate.run(nodes)
        expected_mean = (0.4 * 4) / 6
        assert abs(result.mean_s_score - expected_mean) < 1e-6


class TestDRSEQualityGateThresholds:
    def test_exact_threshold_passes(self):
        gate = DRSEQualityGate()
        # mean = 0.10 exactly
        nodes = [_make_node_score(0.10) for _ in range(4)]
        result = gate.run(nodes)
        assert result.passed is True

    def test_just_below_threshold_fails(self):
        gate = DRSEQualityGate()
        nodes = [_make_node_score(0.09) for _ in range(4)]
        result = gate.run(nodes)
        assert result.passed is False

    def test_correction_ratio_boundary(self):
        gate = DRSEQualityGate()
        # 50% correction — 경계값 (≤ 0.50 통과)
        nodes = ([_make_node_score(0.15, is_residue_min=True) for _ in range(2)]
                 + [_make_node_score(0.30) for _ in range(2)])
        result = gate.run(nodes)
        assert result.residue_correction_ratio == 0.50
        assert result.passed is True  # 경계값은 통과

    def test_no_breakdown_passes_vacuously(self):
        """breakdown 없는 NodeScore — no_s_breakdown 처리"""
        class NoBreakdown:
            breakdown = {}
            score = 0.5
            gate_blocked = False
        gate = DRSEQualityGate()
        result = gate.run([NoBreakdown()])
        assert result.passed is True
        assert result.reason == "no_s_breakdown_available"


class TestGate9Integration:
    def test_gate9_function_returns_dict(self):
        result = _gate_drse_quality()
        assert isinstance(result, dict)
        assert "pass" in result

    def test_gate9_passes(self):
        """실제 DRSEScorer로 Gate 9 실행 — 통과해야 함"""
        result = _gate_drse_quality()
        assert result["pass"] is True, f"Gate 9 failed: {result.get('reason')}"

    def test_gate9_has_metrics(self):
        result = _gate_drse_quality()
        if result["pass"]:
            assert "mean_s_score" in result
            assert "sample_count" in result

    def test_gate9_in_release_gate(self):
        """release_gate.py GATES 목록에 drse_quality 포함 확인"""
        import literary_system.gates.release_gate as rg
        src = open(rg.__file__).read()
        assert "drse_quality" in src
        gate_names = [g[0] for g in rg.GATES]
        assert "drse_quality" in gate_names
