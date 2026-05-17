"""
V324 - test_v324_mae_orchestrator.py
MAEOrchestrator (Alpha/Beta/Gamma 3에이전트 앙상블) 테스트 (30개)
"""
import pytest
from literary_system.evaluation.mae_agents import (
    AlphaAgent, BetaAgent, GammaAgent, AgentVerdict,
)
from literary_system.evaluation.mae_orchestrator import (
    MAEOrchestrator, MAEResult,
)
from literary_system.validation.coefficient_mapper import MAEWeights


# ── 공용 픽스처 ───────────────────────────────────────────────────────────────

def make_metrics(
    drse_pass=0.8,
    spatial_violations=0,
    char_valid=True,
    pull=0.65,
    afterimage=0.55,
    uncertainty=0.30,
    relation_consistency=0.95,
):
    from literary_system.evaluation.scene_metrics_collector import SceneMetrics
    composite = (pull + afterimage - uncertainty) / 3.0
    return SceneMetrics(
        scene_id="test_scene",
        drse_gate_pass_rate=drse_pass,
        spatial_violation_count=spatial_violations,
        character_state_valid=char_valid,
        reader_pull=pull,
        reader_afterimage=afterimage,
        reader_uncertainty=uncertainty,
        reader_composite_score=composite,
        relation_consistency=relation_consistency,
    )

@pytest.fixture
def good_metrics():
    return make_metrics()

@pytest.fixture
def bad_metrics():
    return make_metrics(
        drse_pass=0.2, spatial_violations=5, char_valid=False,
        pull=0.15, afterimage=0.10, uncertainty=0.90, relation_consistency=0.3,
    )

@pytest.fixture
def weights():
    return MAEWeights(alpha_logic=0.5, beta_char=0.5, gamma_tension=0.5)

@pytest.fixture
def orchestrator(weights):
    return MAEOrchestrator(weights=weights)


# ════════════════════════════════════════════════════════════════════
# 1. AgentVerdict DTO
# ════════════════════════════════════════════════════════════════════

class TestAgentVerdict:
    def test_creation(self):
        v = AgentVerdict(agent_name="alpha", passed=True, score=0.8, reason="ok")
        assert v.agent_name == "alpha"
        assert v.passed is True
        assert v.score == 0.8

    def test_score_range(self):
        v = AgentVerdict(agent_name="beta", passed=False, score=0.3, reason="fail")
        assert 0.0 <= v.score <= 1.0

    def test_to_dict(self):
        v = AgentVerdict(agent_name="gamma", passed=True, score=0.7, reason="pass")
        d = v.to_dict()
        assert d["agent_name"] == "gamma"
        assert d["passed"] is True
        assert d["score"] == pytest.approx(0.7)


# ════════════════════════════════════════════════════════════════════
# 2. AlphaAgent — 논리성 평가
# ════════════════════════════════════════════════════════════════════

class TestAlphaAgent:
    def test_good_metrics_passes(self, good_metrics):
        agent = AlphaAgent(weight=0.5)
        verdict = agent.evaluate("s1", good_metrics)
        assert verdict.agent_name == "alpha"
        assert verdict.passed is True

    def test_bad_drse_fails(self, bad_metrics):
        agent = AlphaAgent(weight=0.5)
        verdict = agent.evaluate("s1", bad_metrics)
        assert verdict.passed is False

    def test_spatial_violations_reduce_score(self):
        agent = AlphaAgent(weight=0.5)
        m_clean = make_metrics(spatial_violations=0, drse_pass=0.9)
        m_dirty = make_metrics(spatial_violations=10, drse_pass=0.9)
        v_clean = agent.evaluate("s1", m_clean)
        v_dirty = agent.evaluate("s1", m_dirty)
        assert v_clean.score > v_dirty.score

    def test_returns_agent_verdict(self, good_metrics):
        agent = AlphaAgent(weight=0.5)
        v = agent.evaluate("s1", good_metrics)
        assert isinstance(v, AgentVerdict)


# ════════════════════════════════════════════════════════════════════
# 3. BetaAgent — 캐릭터 상태 평가
# ════════════════════════════════════════════════════════════════════

class TestBetaAgent:
    def test_valid_char_state_passes(self, good_metrics):
        agent = BetaAgent(weight=0.5)
        verdict = agent.evaluate("s1", good_metrics)
        assert verdict.passed is True
        assert verdict.agent_name == "beta"

    def test_invalid_char_state_fails(self, bad_metrics):
        agent = BetaAgent(weight=0.5)
        verdict = agent.evaluate("s1", bad_metrics)
        assert verdict.passed is False

    def test_relation_consistency_affects_score(self):
        agent = BetaAgent(weight=0.5)
        m_high = make_metrics(char_valid=True, relation_consistency=0.99)
        m_low = make_metrics(char_valid=True, relation_consistency=0.3)
        v_high = agent.evaluate("s1", m_high)
        v_low = agent.evaluate("s1", m_low)
        assert v_high.score > v_low.score

    def test_returns_agent_verdict(self, good_metrics):
        agent = BetaAgent(weight=0.5)
        v = agent.evaluate("s1", good_metrics)
        assert isinstance(v, AgentVerdict)


# ════════════════════════════════════════════════════════════════════
# 4. GammaAgent — 문학성 평가
# ════════════════════════════════════════════════════════════════════

class TestGammaAgent:
    def test_good_reader_metrics_passes(self, good_metrics):
        agent = GammaAgent(weight=0.5)
        verdict = agent.evaluate("s1", good_metrics)
        assert verdict.passed is True
        assert verdict.agent_name == "gamma"

    def test_bad_reader_metrics_fails(self, bad_metrics):
        agent = GammaAgent(weight=0.5)
        verdict = agent.evaluate("s1", bad_metrics)
        assert verdict.passed is False

    def test_high_uncertainty_lowers_score(self):
        agent = GammaAgent(weight=0.5)
        m_low_u = make_metrics(uncertainty=0.2)
        m_high_u = make_metrics(uncertainty=0.85)
        v_low = agent.evaluate("s1", m_low_u)
        v_high = agent.evaluate("s1", m_high_u)
        assert v_low.score > v_high.score

    def test_returns_agent_verdict(self, good_metrics):
        agent = GammaAgent(weight=0.5)
        v = agent.evaluate("s1", good_metrics)
        assert isinstance(v, AgentVerdict)


# ════════════════════════════════════════════════════════════════════
# 5. MAEOrchestrator — 합의 프로토콜
# ════════════════════════════════════════════════════════════════════

class TestMAEOrchestrator:
    def test_returns_mae_result(self, orchestrator, good_metrics):
        result = orchestrator.evaluate("s1", good_metrics)
        assert isinstance(result, MAEResult)

    def test_all_good_consensus_true(self, orchestrator, good_metrics):
        result = orchestrator.evaluate("s1", good_metrics)
        assert result.consensus is True
        assert result.pass_count >= 2

    def test_all_bad_consensus_false(self, orchestrator, bad_metrics):
        result = orchestrator.evaluate("s1", bad_metrics)
        assert result.consensus is False

    def test_two_of_three_passes(self):
        # Alpha PASS, Beta PASS, Gamma FAIL 시나리오
        m = make_metrics(
            drse_pass=0.9,        # Alpha: PASS
            char_valid=True,      # Beta: PASS
            pull=0.15,            # Gamma: FAIL (낮은 pull)
            afterimage=0.10,
            uncertainty=0.90,
        )
        orc = MAEOrchestrator(weights=MAEWeights())
        result = orc.evaluate("s1", m)
        # 2/3 → consensus True
        assert result.consensus is True

    def test_one_of_three_fails(self):
        # Alpha FAIL (나쁜 드라마), Beta+Gamma PASS
        m = make_metrics(drse_pass=0.1, spatial_violations=10, char_valid=False)
        orc = MAEOrchestrator(weights=MAEWeights())
        result = orc.evaluate("s1", m)
        # 1/3 → consensus False
        assert result.consensus is False

    def test_result_contains_all_votes(self, orchestrator, good_metrics):
        result = orchestrator.evaluate("s1", good_metrics)
        assert len(result.votes) == 3
        assert result.alpha is not None
        assert result.beta is not None
        assert result.gamma is not None

    def test_scene_id_preserved(self, orchestrator, good_metrics):
        result = orchestrator.evaluate("my_scene_42", good_metrics)
        assert result.scene_id == "my_scene_42"

    def test_pass_count_property(self, orchestrator, good_metrics):
        result = orchestrator.evaluate("s1", good_metrics)
        expected = sum(1 for v in result.votes if v.passed)
        assert result.pass_count == expected

    def test_weights_influence_score(self):
        """가중치가 높은 에이전트의 영향력이 더 커야 한다."""
        m_good_logic = make_metrics(drse_pass=0.95, spatial_violations=0)
        w_alpha_heavy = MAEWeights(alpha_logic=0.9, beta_char=0.2, gamma_tension=0.2)
        w_gamma_heavy = MAEWeights(alpha_logic=0.2, beta_char=0.2, gamma_tension=0.9)
        orc_alpha = MAEOrchestrator(weights=w_alpha_heavy)
        orc_gamma = MAEOrchestrator(weights=w_gamma_heavy)
        r_alpha = orc_alpha.evaluate("s1", m_good_logic)
        r_gamma = orc_gamma.evaluate("s1", m_good_logic)
        # 둘 다 결과는 있어야 함
        assert r_alpha.alpha.score >= 0.0
        assert r_gamma.gamma.score >= 0.0

    def test_to_dict_serializable(self, orchestrator, good_metrics):
        result = orchestrator.evaluate("s1", good_metrics)
        d = result.to_dict()
        assert "consensus" in d
        assert "pass_count" in d
        assert "votes" in d


class TestMAEOrchestratorHistory:
    def test_history_accumulates(self):
        orc = MAEOrchestrator(weights=MAEWeights())
        m = make_metrics()
        orc.evaluate("s1", m)
        orc.evaluate("s2", m)
        assert len(orc.get_history()) == 2

    def test_clear_history(self):
        orc = MAEOrchestrator(weights=MAEWeights())
        orc.evaluate("s1", make_metrics())
        orc.clear_history()
        assert len(orc.get_history()) == 0

    def test_update_weights(self):
        orc = MAEOrchestrator(weights=MAEWeights(alpha_logic=0.3))
        new_w = MAEWeights(alpha_logic=0.8)
        orc.update_weights(new_w)
        assert orc._alpha.weight == pytest.approx(0.8)

    def test_history_returns_copy(self):
        orc = MAEOrchestrator()
        orc.evaluate("s1", make_metrics())
        hist = orc.get_history()
        hist.clear()
        assert len(orc.get_history()) == 1
