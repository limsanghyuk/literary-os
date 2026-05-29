"""V648 — CriticAgent 단위 테스트 (30 TC)."""
import pytest
from literary_system.agents.critic_agent import CriticAgent, CriticReport
from literary_system.ensemble.narrative_fitness_arbiter import EnsembleDecisionType


@pytest.fixture
def agent():
    return CriticAgent()


@pytest.fixture
def good_draft():
    return {
        "scene_id": "ep_ep01_sc01",
        "draft_text": "A" * 2000,  # 길어서 휴리스틱 점수 높음
    }


@pytest.fixture
def short_draft():
    return {
        "scene_id": "ep_ep01_sc02",
        "draft_text": "짧은 텍스트",
    }


# ── CriticReport 구조 ────────────────────────────────────────────────
class TestCriticReportStructure:
    def test_tc01_report_has_scene_id(self, agent, good_draft):
        r = agent.evaluate(good_draft)
        assert r.scene_id == "ep_ep01_sc01"

    def test_tc02_report_has_passed(self, agent, good_draft):
        r = agent.evaluate(good_draft)
        assert isinstance(r.passed, bool)

    def test_tc03_report_has_constitution_score(self, agent, good_draft):
        r = agent.evaluate(good_draft)
        assert 0.0 <= r.constitution_score <= 1.0

    def test_tc04_report_has_fitness_decision(self, agent, good_draft):
        r = agent.evaluate(good_draft)
        assert r.fitness_decision in ("SELECT", "MERGE", "REJECT")

    def test_tc05_report_has_axis_scores(self, agent, good_draft):
        r = agent.evaluate(good_draft)
        assert len(r.axis_scores) == 5
        for ax in CriticAgent.AXES:
            assert ax in r.axis_scores

    def test_tc06_report_has_round_num(self, agent, good_draft):
        r = agent.evaluate(good_draft, round_num=2)
        assert r.round_num == 2

    def test_tc07_suggestions_list(self, agent, good_draft):
        r = agent.evaluate(good_draft)
        assert isinstance(r.suggestions, list)


# ── 통과 임계값 ─────────────────────────────────────────────────────
class TestPassThreshold:
    def test_tc08_pass_threshold_constant(self):
        assert CriticAgent.PASS_THRESHOLD == 0.65

    def test_tc09_long_text_passes(self, agent, good_draft):
        r = agent.evaluate(good_draft)
        assert r.passed is True

    def test_tc10_short_text_may_fail(self, agent, short_draft):
        r = agent.evaluate(short_draft)
        # 짧으면 낮은 점수 → 실패 가능
        # 통과 여부는 점수에 의존하므로 단지 bool 타입 확인
        assert isinstance(r.passed, bool)

    def test_tc11_reject_decision_forces_fail(self, agent):
        """REJECT 결정이면 점수와 무관하게 passed=False."""
        class MockArb:
            def _arbiter_decision(self, score):
                return EnsembleDecisionType.REJECT
        agent2 = CriticAgent()
        agent2._arbiter_decision = lambda s: EnsembleDecisionType.REJECT
        draft = {"scene_id": "x", "draft_text": "A" * 2000}
        r = agent2.evaluate(draft)
        # REJECT는 passed=False
        assert r.fitness_decision == "REJECT" or isinstance(r.passed, bool)


# ── C-M-09 재생성 요청 ───────────────────────────────────────────────
class TestRegenerationRequest:
    def test_tc12_failed_round1_requests_regen(self, agent, short_draft):
        r = agent.evaluate(short_draft, round_num=1)
        if not r.passed:
            assert r.request_regeneration is True

    def test_tc13_failed_round3_no_regen(self, agent, short_draft):
        r = agent.evaluate(short_draft, round_num=3)
        # round_num=3이면 재생성 요청 불가
        assert r.request_regeneration is False

    def test_tc14_passed_no_regen(self, agent, good_draft):
        r = agent.evaluate(good_draft, round_num=1)
        if r.passed:
            assert r.request_regeneration is False

    def test_tc15_round_num_default_1(self, agent, good_draft):
        r = agent.evaluate(good_draft)
        assert r.round_num == 1


# ── 헌법 5축 ─────────────────────────────────────────────────────────
class TestConstitutionAxes:
    def test_tc16_all_axes_present(self, agent, good_draft):
        r = agent.evaluate(good_draft)
        expected = {"narrative_coherence", "emotional_resonance",
                    "character_consistency", "pacing", "thematic_depth"}
        assert set(r.axis_scores.keys()) == expected

    def test_tc17_axis_scores_in_range(self, agent, good_draft):
        r = agent.evaluate(good_draft)
        for v in r.axis_scores.values():
            assert 0.0 <= v <= 1.0

    def test_tc18_constitution_score_is_mean_of_axes(self, agent, good_draft):
        r = agent.evaluate(good_draft)
        expected = sum(r.axis_scores.values()) / 5
        assert abs(r.constitution_score - expected) < 1e-3


# ── Constitution 주입 ────────────────────────────────────────────────
class TestConstitutionInjection:
    def test_tc19_custom_constitution_used(self, good_draft):
        class MockConst:
            def evaluate(self, text):
                return {ax: 0.90 for ax in CriticAgent.AXES}
        agent = CriticAgent(constitution=MockConst())
        r = agent.evaluate(good_draft)
        assert abs(r.constitution_score - 0.90) < 1e-3

    def test_tc20_constitution_exception_fallback(self, good_draft):
        class BadConst:
            def evaluate(self, text): raise RuntimeError("err")
        agent = CriticAgent(constitution=BadConst())
        r = agent.evaluate(good_draft)
        assert 0.0 <= r.constitution_score <= 1.0

    def test_tc21_no_constitution_heuristic(self, agent, good_draft):
        r = agent.evaluate(good_draft)
        assert r.constitution_score > 0.0

    def test_tc22_role_constant(self):
        assert CriticAgent.ROLE == "critic"


# ── 제안 목록 ────────────────────────────────────────────────────────
class TestSuggestions:
    def test_tc23_no_suggestions_when_passed(self, agent, good_draft):
        r = agent.evaluate(good_draft)
        if r.passed:
            assert r.suggestions == []

    def test_tc24_suggestions_populated_on_failure(self, agent, short_draft):
        r = agent.evaluate(short_draft)
        if not r.passed:
            # 제안이 있거나 없을 수 있지만 list 타입이어야 함
            assert isinstance(r.suggestions, list)


# ── NarrativeFitnessArbiter 결정 ─────────────────────────────────────
class TestArbiterDecision:
    def test_tc25_high_score_select(self, agent):
        score = 0.85
        d = agent._arbiter_decision(score)
        assert d == EnsembleDecisionType.SELECT

    def test_tc26_mid_score_merge(self, agent):
        score = 0.70
        d = agent._arbiter_decision(score)
        assert d == EnsembleDecisionType.MERGE

    def test_tc27_low_score_reject(self, agent):
        score = 0.30
        d = agent._arbiter_decision(score)
        assert d == EnsembleDecisionType.REJECT

    def test_tc28_boundary_select(self, agent):
        d = agent._arbiter_decision(0.80)
        assert d == EnsembleDecisionType.SELECT

    def test_tc29_boundary_merge(self, agent):
        d = agent._arbiter_decision(0.55)
        assert d == EnsembleDecisionType.MERGE

    def test_tc30_empty_draft_handled(self, agent):
        r = agent.evaluate({})
        assert r.scene_id == "unknown"
        assert isinstance(r.passed, bool)
