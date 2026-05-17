"""
V499~V500 테스트 — MAEOrchestratorV2 (4종 에이전트) + AMW (α 학습)
ADR-017: 에이전트 가중치, 샘플링, σ 계산
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
sys.path.insert(0, ".")

from literary_system.nie.mae_agents_v2 import (
    MAEOrchestratorV2, MAEResultV2, ReaderAgentV2, WriterAgentV2,
    EditorAgentV2, CulturalAgentV2, AGENT_WEIGHTS, WeightedVerdict,
)
from literary_system.nie.adaptive_momentum_weights import (
    AdaptiveMomentumWeights, AMWState, ALPHA_MIN, ALPHA_MAX,
    DIMS, LR_AMW, GENRE_ALPHA_INIT,
)
from literary_system.evaluation.scene_metrics_collector import SceneMetrics


def _metrics(reader=0.7, char_valid=True, consistency=0.6, drse=0.8, spatial=0.1) -> SceneMetrics:
    m = MagicMock(spec=SceneMetrics)
    m.reader_composite_score = reader
    m.character_state_valid = char_valid
    m.relation_consistency = consistency
    m.drse_gate_pass_rate = drse
    m.spatial_redundancy_ratio = spatial
    return m


# ── MAEOrchestratorV2 테스트 ────────────────────────────────────────

class TestMAEOrchestratorV2:
    def test_evaluate_returns_result_v2(self):
        orch = MAEOrchestratorV2(sample_rate=1.0)  # 항상 샘플링
        result = orch.evaluate("s001", _metrics())
        assert isinstance(result, MAEResultV2)
        assert result.scene_id == "s001"

    def test_four_agents_in_verdicts(self):
        orch = MAEOrchestratorV2(sample_rate=1.0)
        result = orch.evaluate("s001", _metrics())
        names = {v.agent_name for v in result.verdicts}
        assert "reader_v2" in names
        assert "writer_v2" in names
        assert "editor_v2" in names
        assert "cultural_v2" in names

    def test_weight_sum_approx_1(self):
        assert sum(AGENT_WEIGHTS.values()) == pytest.approx(1.0)

    def test_weighted_score_range(self):
        orch = MAEOrchestratorV2(sample_rate=1.0)
        result = orch.evaluate("s001", _metrics())
        assert 0.0 <= result.weighted_score <= 1.0

    def test_sigma_computed(self):
        orch = MAEOrchestratorV2(sample_rate=1.0)
        result = orch.evaluate("s001", _metrics())
        assert result.sigma >= 0.0

    def test_pass_threshold(self):
        orch = MAEOrchestratorV2(sample_rate=1.0)
        result = orch.evaluate("s001", _metrics(reader=0.9, char_valid=True, consistency=0.9))
        assert result.passed is True

    def test_fail_threshold(self):
        orch = MAEOrchestratorV2(sample_rate=1.0)
        result = orch.evaluate("s001", _metrics(reader=0.0, char_valid=False, consistency=0.0, drse=0.0))
        assert result.passed is False

    def test_history_accumulates_on_sample(self):
        orch = MAEOrchestratorV2(sample_rate=1.0)
        for i in range(3):
            orch.evaluate(f"s{i:03d}", _metrics(), force_sample=True)
        assert len(orch.get_history()) == 3

    def test_update_weights_applies(self):
        orch = MAEOrchestratorV2(sample_rate=1.0)
        orch.update_weights({"reader": 0.40, "writer": 0.20, "editor": 0.25, "cultural": 0.15})
        assert orch._weights["reader"] == pytest.approx(0.40)

    def test_pass_count_property(self):
        orch = MAEOrchestratorV2(sample_rate=1.0)
        result = orch.evaluate("s001", _metrics())
        assert 0 <= result.pass_count <= 4

    def test_consensus_equals_passed(self):
        orch = MAEOrchestratorV2(sample_rate=1.0)
        result = orch.evaluate("s001", _metrics())
        assert result.consensus == result.passed

    def test_to_dict_serializable(self):
        orch = MAEOrchestratorV2(sample_rate=1.0)
        result = orch.evaluate("s001", _metrics())
        d = result.to_dict()
        assert "scene_id" in d
        assert "weighted_score" in d
        assert "verdicts" in d
        assert len(d["verdicts"]) == 4


class TestReaderAgentV2:
    def test_three_persona_in_reason(self):
        agent = ReaderAgentV2()
        v = agent.evaluate("s001", _metrics())
        assert "F30" in v.reason and "M60" in v.reason and "T20" in v.reason

    def test_persona_field(self):
        agent = ReaderAgentV2()
        v = agent.evaluate("s001", _metrics())
        assert v.persona == "ensemble_3"

    def test_weight_correct(self):
        agent = ReaderAgentV2()
        assert agent.WEIGHT == pytest.approx(0.35)


# ── AdaptiveMomentumWeights 테스트 ──────────────────────────────────

class TestAdaptiveMomentumWeights:
    def _scene(self):
        r = MagicMock()
        r.draft_text = "긴장감 넘치는 위기 상황"
        r.mae_score = 0.7
        return r

    def test_init_alpha_in_range(self):
        amw = AdaptiveMomentumWeights(genre="melodrama")
        for dim, val in amw.get_alpha().items():
            assert ALPHA_MIN <= val <= ALPHA_MAX, f"{dim}={val}"

    def test_all_genres_valid(self):
        for genre in GENRE_ALPHA_INIT:
            amw = AdaptiveMomentumWeights(genre=genre)
            for val in amw.get_alpha().values():
                assert ALPHA_MIN <= val <= ALPHA_MAX

    def test_update_returns_emotional_vector(self):
        from literary_system.emotion.emotional_momentum_tracker import EmotionalVector
        amw = AdaptiveMomentumWeights()
        vec = amw.update(self._scene(), advantage=0.2)
        assert isinstance(vec, EmotionalVector)

    def test_alpha_changes_after_positive_advantage(self):
        amw = AdaptiveMomentumWeights(genre="thriller")
        old = amw.get_alpha().copy()
        amw.update(self._scene(), advantage=0.5)
        new = amw.get_alpha()
        changed = any(abs(new[d] - old[d]) > 1e-9 for d in DIMS)
        assert changed

    def test_alpha_clamp_min(self):
        amw = AdaptiveMomentumWeights()
        # 극단적 음수 advantage → α가 ALPHA_MIN 이하로 내려가지 않음
        for _ in range(100):
            amw.update(self._scene(), advantage=-10.0)
        for val in amw.get_alpha().values():
            assert val >= ALPHA_MIN

    def test_alpha_clamp_max(self):
        amw = AdaptiveMomentumWeights()
        for _ in range(100):
            amw.update(self._scene(), advantage=10.0)
        for val in amw.get_alpha().values():
            assert val <= ALPHA_MAX

    def test_history_accumulates(self):
        amw = AdaptiveMomentumWeights()
        for _ in range(5):
            amw.update(self._scene(), advantage=0.1)
        assert len(amw.get_history()) == 5

    def test_get_state_structure(self):
        amw = AdaptiveMomentumWeights()
        amw.update(self._scene(), advantage=0.1)
        state = amw.get_state()
        assert isinstance(state, AMWState)
        assert state.update_count == 1
        assert all(d in state.alpha for d in DIMS)

    def test_reset_restores_default(self):
        amw = AdaptiveMomentumWeights(genre="thriller")
        for _ in range(10):
            amw.update(self._scene(), advantage=0.8)
        amw.reset(genre="thriller")
        expected = GENRE_ALPHA_INIT["thriller"]
        for dim in DIMS:
            assert amw.get_alpha()[dim] == pytest.approx(expected[dim])

    def test_stability_module_lr_applied(self):
        stability = MagicMock()
        stability.get_effective_lr.return_value = 0.001
        stability.check_divergence.return_value = False
        amw = AdaptiveMomentumWeights(stability_module=stability)
        amw.update(self._scene(), advantage=0.3)
        stability.get_effective_lr.assert_called_once_with("amw", LR_AMW)

    def test_pagerank_weights_adjust_init(self):
        pr = {"char_A": 0.85, "char_B": 0.60}
        amw = AdaptiveMomentumWeights(genre="melodrama", pagerank_weights=pr)
        # PR이 높으면 α가 상향 조정될 수 있음 (clamp 범위 내)
        for val in amw.get_alpha().values():
            assert ALPHA_MIN <= val <= ALPHA_MAX

    def test_to_dict_state(self):
        amw = AdaptiveMomentumWeights()
        amw.update(self._scene(), advantage=0.2)
        d = amw.get_state().to_dict()
        assert "alpha" in d
        assert "update_count" in d


# 샘플링 테스트 보완 (random 고정)
class TestMAESampling:
    def test_no_history_always_samples(self):
        """히스토리 없을 때 force_sample=False여도 첫 씬은 반드시 평가"""
        orch = MAEOrchestratorV2(sample_rate=0.0)  # 샘플율 0
        result = orch.evaluate("s001", _metrics(), force_sample=False)
        # 히스토리 없으면 샘플링 실행
        assert isinstance(result, MAEResultV2)

    def test_force_sample_true_always_evaluates(self):
        orch = MAEOrchestratorV2(sample_rate=0.0)
        result = orch.evaluate("s001", _metrics(), force_sample=True)
        assert result.sampled is True

    def test_zero_sample_rate_returns_cached(self):
        orch = MAEOrchestratorV2(sample_rate=1.0)
        first = orch.evaluate("s001", _metrics(), force_sample=True)
        # sample_rate=0으로 두 번째 호출 — 캐시 반환
        orch._sample_rate = 0.0
        second = orch.evaluate("s002", _metrics(), force_sample=False)
        assert second.sampled is False
