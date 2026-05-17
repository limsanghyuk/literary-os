"""
V380 테스트 — ledgers/episode_reveal_budget.py
EpisodeRevealBudget: 4단계 정책, 게이트 검사, 요약, arc 연동
"""
import pytest
from literary_system.ledgers.episode_reveal_budget import (
    RevealPolicy, EpisodeRevealPolicy, EpisodeRevealBudget,
    RevealBlockedError, RevealForeshadowOnlyError, RevealBudgetViolationError,
)


@pytest.fixture
def budget():
    return EpisodeRevealBudget()


@pytest.fixture
def configured_budget():
    b = EpisodeRevealBudget()
    b.set_policy("ep_01", "fact_killer", RevealPolicy.BLOCK)
    b.set_policy("ep_08", "fact_killer", RevealPolicy.FORESHADOW_ONLY)
    b.set_policy("ep_14", "fact_killer", RevealPolicy.ALLOW)
    b.set_policy("ep_10", "fact_alibi", RevealPolicy.DELAY, delay_to="ep_11")
    return b


class TestRevealPolicy:
    def test_all_four_policies(self):
        policies = {p.value for p in RevealPolicy}
        assert "ALLOW" in policies
        assert "FORESHADOW_ONLY" in policies
        assert "DELAY" in policies
        assert "BLOCK" in policies

    def test_policy_from_value(self):
        assert RevealPolicy("BLOCK") == RevealPolicy.BLOCK
        assert RevealPolicy("ALLOW") == RevealPolicy.ALLOW


class TestEpisodeRevealPolicy:
    def test_creation(self):
        ep = EpisodeRevealPolicy(
            episode_id="ep_01", fact_id="fact_x",
            policy=RevealPolicy.BLOCK, reason="테스트"
        )
        assert ep.episode_id == "ep_01"
        assert ep.policy == RevealPolicy.BLOCK

    def test_to_dict(self):
        ep = EpisodeRevealPolicy("ep_01", "fact_x", RevealPolicy.FORESHADOW_ONLY)
        d = ep.to_dict()
        assert d["episode_id"] == "ep_01"
        assert d["fact_id"] == "fact_x"
        assert d["policy"] == "FORESHADOW_ONLY"


class TestSetPolicy:
    def test_set_and_get(self, budget):
        budget.set_policy("ep_01", "fact_x", RevealPolicy.BLOCK)
        assert budget.get_policy("ep_01", "fact_x") == RevealPolicy.BLOCK

    def test_default_policy_is_allow(self, budget):
        assert budget.get_policy("ep_99", "unknown_fact") == RevealPolicy.ALLOW

    def test_overwrite_policy(self, budget):
        budget.set_policy("ep_01", "fact_x", RevealPolicy.BLOCK)
        budget.set_policy("ep_01", "fact_x", RevealPolicy.ALLOW)
        assert budget.get_policy("ep_01", "fact_x") == RevealPolicy.ALLOW

    def test_global_block(self, budget):
        budget.set_global_block("fact_secret")
        assert budget.get_policy("ep_01", "fact_secret") == RevealPolicy.BLOCK
        assert budget.get_policy("ep_16", "fact_secret") == RevealPolicy.BLOCK

    def test_remove_global_block(self, budget):
        budget.set_global_block("fact_secret")
        budget.remove_global_block("fact_secret")
        assert budget.get_policy("ep_01", "fact_secret") == RevealPolicy.ALLOW

    def test_delay_policy_with_delay_to(self, budget):
        budget.set_policy("ep_05", "fact_y", RevealPolicy.DELAY, delay_to="ep_06")
        assert budget.get_policy("ep_05", "fact_y") == RevealPolicy.DELAY


class TestCheck:
    def test_allow_policy_passes(self, configured_budget):
        configured_budget.check("ep_14", "fact_killer")  # should not raise

    def test_block_raises_blocked_error(self, configured_budget):
        with pytest.raises(RevealBlockedError):
            configured_budget.check("ep_01", "fact_killer")

    def test_foreshadow_only_direct_reveal_blocked(self, configured_budget):
        with pytest.raises(RevealForeshadowOnlyError):
            configured_budget.check("ep_08", "fact_killer", direct_reveal=True)

    def test_foreshadow_only_indirect_passes(self, configured_budget):
        configured_budget.check("ep_08", "fact_killer", direct_reveal=False)

    def test_delay_policy_passes_check(self, configured_budget):
        configured_budget.check("ep_10", "fact_alibi")  # DELAY → 통과

    def test_unknown_episode_allows(self, configured_budget):
        configured_budget.check("ep_99", "fact_killer")  # 미설정 → ALLOW

    def test_blocked_error_has_episode_and_fact(self, configured_budget):
        try:
            configured_budget.check("ep_01", "fact_killer")
        except RevealBlockedError as e:
            assert e.episode_id == "ep_01"
            assert e.fact_id == "fact_killer"

    def test_foreshadow_error_has_episode_and_fact(self, configured_budget):
        try:
            configured_budget.check("ep_08", "fact_killer")
        except RevealForeshadowOnlyError as e:
            assert e.episode_id == "ep_08"
            assert e.fact_id == "fact_killer"


class TestCheckAll:
    def test_check_all_no_violations(self, configured_budget):
        violations = configured_budget.check_all("ep_14", ["fact_killer", "fact_alibi"])
        assert violations == []

    def test_check_all_with_violations(self, configured_budget):
        violations = configured_budget.check_all("ep_01", ["fact_killer", "fact_alibi"])
        assert "fact_killer" in violations

    def test_check_all_empty_list(self, configured_budget):
        assert configured_budget.check_all("ep_01", []) == []

    def test_check_all_multiple_blocks(self, budget):
        budget.set_policy("ep_01", "fact_a", RevealPolicy.BLOCK)
        budget.set_policy("ep_01", "fact_b", RevealPolicy.BLOCK)
        violations = budget.check_all("ep_01", ["fact_a", "fact_b", "fact_c"])
        assert len(violations) == 2
        assert "fact_c" not in violations


class TestGlobalBlock:
    def test_global_block_overrides_episode_policy(self, budget):
        budget.set_policy("ep_01", "fact_x", RevealPolicy.ALLOW)
        budget.set_global_block("fact_x")
        assert budget.get_policy("ep_01", "fact_x") == RevealPolicy.BLOCK

    def test_global_block_raises_error_on_check(self, budget):
        budget.set_global_block("fact_secret")
        with pytest.raises(RevealBlockedError):
            budget.check("ep_05", "fact_secret")


class TestEpisodeSummary:
    def test_summary_has_episode_id(self, configured_budget):
        s = configured_budget.episode_summary("ep_01")
        assert s["episode_id"] == "ep_01"

    def test_summary_has_policies(self, configured_budget):
        s = configured_budget.episode_summary("ep_01")
        assert "policies" in s
        assert s["policy_count"] >= 1

    def test_summary_empty_episode(self, budget):
        s = budget.episode_summary("ep_99")
        assert s["policy_count"] == 0


class TestFactJourney:
    def test_fact_journey(self, configured_budget):
        journey = configured_budget.fact_journey("fact_killer")
        assert len(journey) == 3

    def test_fact_journey_sorted(self, configured_budget):
        journey = configured_budget.fact_journey("fact_killer")
        ep_ids = [j["episode_id"] for j in journey]
        assert ep_ids == sorted(ep_ids)

    def test_fact_journey_empty_unknown(self, budget):
        assert budget.fact_journey("unknown_fact") == []


class TestFromArcGraph:
    def test_from_arc_graph_basic(self):
        from literary_system.arc.series_arc_planner import SeriesArcPlanner
        from literary_system.arc.schema import ArcPlotNode, ArcAct
        planner = SeriesArcPlanner(total_episodes=4)
        graph = planner.plan()
        # ep_01에 forbidden_reveals 추가
        node = graph.get_node("ep_01")
        node.forbidden_reveals.append("fact_killer")
        budget = EpisodeRevealBudget.from_arc_graph(graph)
        assert budget.get_policy("ep_01", "fact_killer") == RevealPolicy.BLOCK

    def test_from_arc_graph_returns_budget(self):
        from literary_system.arc.series_arc_planner import SeriesArcPlanner
        planner = SeriesArcPlanner(total_episodes=4)
        graph = planner.plan()
        budget = EpisodeRevealBudget.from_arc_graph(graph)
        assert isinstance(budget, EpisodeRevealBudget)


class TestTotalPolicyCount:
    def test_count_increases_with_policies(self, budget):
        assert budget.total_policy_count() == 0
        budget.set_policy("ep_01", "fact_x", RevealPolicy.BLOCK)
        assert budget.total_policy_count() == 1
        budget.set_policy("ep_02", "fact_y", RevealPolicy.ALLOW)
        assert budget.total_policy_count() == 2
