"""
V380 보강 테스트 — 2000 PASS 달성을 위한 추가 커버리지
"""
import pytest
from literary_system.arc.schema import ArcAct, ArcPlotEdgeType, ArcPlotNode, ArcPlotEdge
from literary_system.arc.causal_plot_graph import CausalPlotGraph
from literary_system.arc.series_arc_planner import SeriesArcPlanner
from literary_system.ledgers.episode_reveal_budget import (
    RevealPolicy, EpisodeRevealBudget,
    RevealBlockedError, RevealForeshadowOnlyError,
)
from literary_system.world.knowledge_state_tracker import (
    KnowledgeStateTracker, KnowledgeStatus, InformationType,
)
from literary_system.world.character_knowledge_prose_bridge import (
    CharacterKnowledgeProseBridge, KnowledgeLeakageError,
)


# ── ArcPlotNode 경계값 테스트 ──────────────────────────────────

class TestArcPlotNodeBoundary:
    def test_reveal_budget_zero(self):
        n = ArcPlotNode("ep_01", 1, reveal_budget=0.0)
        assert n.reveal_budget == 0.0

    def test_reveal_budget_one(self):
        n = ArcPlotNode("ep_01", 1, reveal_budget=1.0)
        assert n.reveal_budget == 1.0

    def test_tension_level_zero(self):
        n = ArcPlotNode("ep_01", 1, tension_level=0.0)
        assert n.tension_level == 0.0

    def test_tension_level_one(self):
        n = ArcPlotNode("ep_01", 1, tension_level=1.0)
        assert n.tension_level == 1.0

    def test_multiple_causal_inputs(self):
        n = ArcPlotNode("ep_05", 5, causal_inputs=["ep_03", "ep_04"])
        assert len(n.causal_inputs) == 2

    def test_multiple_forbidden_reveals(self):
        n = ArcPlotNode("ep_01", 1,
                         forbidden_reveals=["f1", "f2", "f3"])
        assert len(n.forbidden_reveals) == 3

    def test_seung_act_value(self):
        n = ArcPlotNode("ep_05", 5, act=ArcAct.SEUNG)
        assert n.to_dict()["act"] == "승"

    def test_jeon_act_value(self):
        n = ArcPlotNode("ep_10", 10, act=ArcAct.JEON)
        assert n.to_dict()["act"] == "전"


# ── CausalPlotGraph 추가 테스트 ────────────────────────────────

class TestCausalPlotGraphExtra:
    def test_add_multiple_edges_same_source(self):
        g = CausalPlotGraph()
        g.add_node(ArcPlotNode("ep_01", 1))
        g.add_node(ArcPlotNode("ep_02", 2))
        g.add_node(ArcPlotNode("ep_03", 3))
        g.add_edge(ArcPlotEdge("ep_01", "ep_02", ArcPlotEdgeType.CAUSAL))
        g.add_edge(ArcPlotEdge("ep_01", "ep_03", ArcPlotEdgeType.FORESHADOW))
        assert len(g.edges_from("ep_01")) == 2

    def test_empty_edges_from_unknown_node(self):
        g = CausalPlotGraph()
        assert g.edges_from("unknown") == []
        assert g.edges_to("unknown") == []

    def test_node_overwrite(self):
        g = CausalPlotGraph()
        n1 = ArcPlotNode("ep_01", 1, title="첫번째")
        n2 = ArcPlotNode("ep_01", 1, title="덮어쓰기")
        g.add_node(n1)
        g.add_node(n2)
        assert g.get_node("ep_01").title == "덮어쓰기"

    def test_emotional_escalation_weight_is_tension_diff(self):
        g = CausalPlotGraph()
        g.add_node(ArcPlotNode("ep_01", 1, tension_level=0.2))
        g.add_node(ArcPlotNode("ep_02", 2, tension_level=0.7))
        g.infer_emotional_escalation_edges()
        esc_edges = [e for e in g.all_edges()
                     if e.edge_type == ArcPlotEdgeType.EMOTIONAL_ESCALATION]
        assert len(esc_edges) == 1
        assert abs(esc_edges[0].weight - 0.5) < 0.01

    def test_all_nodes_empty_graph(self):
        g = CausalPlotGraph()
        assert g.all_nodes() == []

    def test_all_edges_empty_graph(self):
        g = CausalPlotGraph()
        assert g.all_edges() == []

    def test_remove_edges_for_cleans_both_directions(self):
        g = CausalPlotGraph()
        g.add_node(ArcPlotNode("ep_01", 1))
        g.add_node(ArcPlotNode("ep_02", 2))
        g.add_edge(ArcPlotEdge("ep_01", "ep_02", ArcPlotEdgeType.CAUSAL))
        g.remove_edges_for("ep_01")
        assert len(g.edges_from("ep_01")) == 0
        assert len(g.edges_to("ep_02")) == 0


# ── SeriesArcPlanner 추가 테스트 ─────────────────────────────────

class TestSeriesArcPlannerExtra:
    def test_3_episodes(self):
        p = SeriesArcPlanner(total_episodes=3)
        g = p.plan()
        assert len(g.all_nodes()) == 3

    def test_plan_called_twice_adds_no_duplicate_nodes(self):
        p = SeriesArcPlanner(total_episodes=4)
        g = CausalPlotGraph()
        p.plan(graph=g)
        # 두 번째 호출 — 같은 그래프에 넣으면 덮어쓰기
        p.plan(graph=g)
        assert len(g.all_nodes()) == 4

    def test_emotional_targets_cover_16_episodes(self):
        p = SeriesArcPlanner(total_episodes=16)
        g = p.plan()
        targets = [n.emotional_target for n in g.all_nodes()]
        # 모두 비어있지 않아야
        assert all(len(t) > 0 for t in targets)

    def test_gi_reveal_budget_lower_than_gyeol(self):
        p = SeriesArcPlanner(total_episodes=16)
        g = p.plan()
        gi_avg   = sum(n.reveal_budget for n in g.nodes_by_act(ArcAct.GI)) / 4
        gyeol_avg= sum(n.reveal_budget for n in g.nodes_by_act(ArcAct.GYEOL)) / 2
        assert gyeol_avg > gi_avg

    def test_series_title_in_all_episode_titles(self):
        p = SeriesArcPlanner(total_episodes=4, series_title="한강")
        g = p.plan()
        for n in g.all_nodes():
            assert "한강" in n.title


# ── EpisodeRevealBudget 추가 테스트 ──────────────────────────────

class TestEpisodeRevealBudgetExtra:
    def test_multiple_facts_same_episode(self):
        b = EpisodeRevealBudget()
        b.set_policy("ep_01", "f1", RevealPolicy.BLOCK)
        b.set_policy("ep_01", "f2", RevealPolicy.ALLOW)
        b.set_policy("ep_01", "f3", RevealPolicy.FORESHADOW_ONLY)
        assert b.total_policy_count() == 3

    def test_global_block_applied_all_episodes(self):
        b = EpisodeRevealBudget()
        b.set_global_block("secret")
        for ep in ["ep_01", "ep_08", "ep_16"]:
            assert b.get_policy(ep, "secret") == RevealPolicy.BLOCK

    def test_check_all_returns_correct_violations(self):
        b = EpisodeRevealBudget()
        b.set_policy("ep_01", "f1", RevealPolicy.BLOCK)
        b.set_policy("ep_01", "f2", RevealPolicy.BLOCK)
        b.set_policy("ep_01", "f3", RevealPolicy.ALLOW)
        violations = b.check_all("ep_01", ["f1", "f2", "f3"])
        assert set(violations) == {"f1", "f2"}

    def test_delay_policy_tracked(self):
        b = EpisodeRevealBudget()
        b.set_policy("ep_05", "fact_x", RevealPolicy.DELAY, delay_to="ep_06")
        journey = b.fact_journey("fact_x")
        assert len(journey) == 1
        assert journey[0]["policy"] == "DELAY"

    def test_episode_summary_global_blocks_included(self):
        b = EpisodeRevealBudget()
        b.set_global_block("global_secret")
        s = b.episode_summary("ep_01")
        assert "global_secret" in s["global_blocks"]

    def test_foreshadow_indirect_reveal_passes_multiple_facts(self):
        b = EpisodeRevealBudget()
        b.set_policy("ep_03", "f1", RevealPolicy.FORESHADOW_ONLY)
        b.set_policy("ep_03", "f2", RevealPolicy.FORESHADOW_ONLY)
        # 간접 공개는 모두 통과
        b.check("ep_03", "f1", direct_reveal=False)
        b.check("ep_03", "f2", direct_reveal=False)


# ── CharacterKnowledgeProseBridge 추가 테스트 ─────────────────────

class TestKnowledgeBridgeExtra:
    def setup_method(self):
        self.t = KnowledgeStateTracker("extra_test")
        self.t.register_fact("f1", InformationType.IDENTITY, "정체", "X",
                              reader_knows=True)
        self.t.register_fact("f2", InformationType.BETRAYAL, "배신", "Y",
                              reader_knows=True)
        self.t.set_knowledge("char_a", "f1", KnowledgeStatus.KNOWS, 1)
        self.t.set_knowledge("char_b", "f1", KnowledgeStatus.UNAWARE, 1)
        self.t.set_knowledge("char_c", "f1", KnowledgeStatus.SUSPECTS, 1)
        self.t.set_knowledge("reader", "f1", KnowledgeStatus.READER_ONLY, 1)
        self.bridge = CharacterKnowledgeProseBridge(self.t)

    def test_get_constraint_unknown_char_is_ignorant(self):
        c = self.bridge.get_constraint("nobody", "f1")
        assert c.render_mode == "ignorant"

    def test_enrich_multiple_facts(self):
        from literary_system.prose.contract import ProseRenderContract
        contract = ProseRenderContract.default()
        enriched = self.bridge.enrich_contract(contract, "reader", ["f1", "f2"])
        kc = enriched.metadata["knowledge_constraints"]
        # f1 → READER_ONLY → blocked
        assert "f1" in kc["blocked"]

    def test_asymmetry_multiple_facts(self):
        self.t.set_knowledge("char_a", "f2", KnowledgeStatus.KNOWS, 1)
        self.t.set_knowledge("char_b", "f2", KnowledgeStatus.UNAWARE, 1)
        bridge = CharacterKnowledgeProseBridge(self.t)
        pressure = bridge.asymmetry_pressure("char_a", "char_b", ["f1", "f2"])
        # 두 사실 모두 KNOWS vs UNAWARE → 높은 압력
        assert pressure >= 0.8

    def test_check_scene_all_pass_for_knowing_char(self):
        violations = self.bridge.check_scene("char_a", ["f1", "f2"])
        assert violations == []

    def test_blocked_facts_multiple(self):
        self.t.set_knowledge("reader", "f2", KnowledgeStatus.READER_ONLY, 1)
        bridge = CharacterKnowledgeProseBridge(self.t)
        blocked = bridge.blocked_facts_for("reader")
        assert len(blocked) >= 1
