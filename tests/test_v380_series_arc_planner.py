"""
V380 테스트 — arc/series_arc_planner.py
SeriesArcPlanner: 16부작 자동 생성, 4막 분배, 텐션 곡선, 커스텀 플랜
"""
import pytest
from literary_system.arc.schema import ArcAct, ArcPlotEdgeType
from literary_system.arc.causal_plot_graph import CausalPlotGraph
from literary_system.arc.series_arc_planner import SeriesArcPlanner


@pytest.fixture
def planner_16():
    return SeriesArcPlanner(total_episodes=16, series_title="비밀의 숲")


@pytest.fixture
def graph_16(planner_16):
    return planner_16.plan()


class TestSeriesArcPlannerInit:
    def test_default_init(self):
        p = SeriesArcPlanner()
        assert p.total_episodes == 16

    def test_custom_episode_count(self):
        p = SeriesArcPlanner(total_episodes=8)
        assert p.total_episodes == 8

    def test_invalid_episode_count(self):
        with pytest.raises(ValueError):
            SeriesArcPlanner(total_episodes=1)

    def test_tension_mode_linear(self):
        p = SeriesArcPlanner(total_episodes=4, tension_mode="linear")
        assert p.tension_mode == "linear"


class TestPlan16Episodes:
    def test_creates_16_nodes(self, graph_16):
        assert len(graph_16.all_nodes()) == 16

    def test_episode_ids_sequential(self, graph_16):
        ids = [n.episode_id for n in graph_16.all_nodes()]
        for i in range(1, 17):
            assert f"ep_{i:02d}" in ids

    def test_episode_indices_1_to_16(self, graph_16):
        indices = sorted(n.episode_index for n in graph_16.all_nodes())
        assert indices == list(range(1, 17))

    def test_all_four_acts_present(self, graph_16):
        acts = {n.act for n in graph_16.all_nodes()}
        assert ArcAct.GI in acts
        assert ArcAct.SEUNG in acts
        assert ArcAct.JEON in acts
        assert ArcAct.GYEOL in acts

    def test_gi_act_first_episodes(self, graph_16):
        gi_nodes = graph_16.nodes_by_act(ArcAct.GI)
        assert len(gi_nodes) >= 1
        for n in gi_nodes:
            assert n.episode_index <= 8  # 기 막은 전반부에

    def test_gyeol_act_last_episodes(self, graph_16):
        gyeol_nodes = graph_16.nodes_by_act(ArcAct.GYEOL)
        for n in gyeol_nodes:
            assert n.episode_index >= 13  # 결 막은 후반부에

    def test_tension_all_in_range(self, graph_16):
        for node in graph_16.all_nodes():
            assert 0.0 <= node.tension_level <= 1.0

    def test_reveal_budget_all_in_range(self, graph_16):
        for node in graph_16.all_nodes():
            assert 0.0 <= node.reveal_budget <= 1.0

    def test_emotional_target_non_empty(self, graph_16):
        for node in graph_16.all_nodes():
            assert len(node.emotional_target) > 0

    def test_title_contains_series_name(self, graph_16):
        for node in graph_16.all_nodes():
            assert "비밀의 숲" in node.title

    def test_edges_generated(self, graph_16):
        assert len(graph_16.all_edges()) > 0

    def test_causal_edges_exist(self, graph_16):
        causal = [e for e in graph_16.all_edges()
                  if e.edge_type == ArcPlotEdgeType.CAUSAL]
        assert len(causal) > 0

    def test_foreshadow_edges_exist(self, graph_16):
        foreshadow = [e for e in graph_16.all_edges()
                      if e.edge_type == ArcPlotEdgeType.FORESHADOW]
        assert len(foreshadow) > 0

    def test_act_structure_valid(self, graph_16):
        result = graph_16.validate_act_structure()
        assert result["valid"] is True

    def test_summary_total_episodes(self, graph_16):
        s = graph_16.summary()
        assert s["total_episodes"] == 16

    def test_plan_with_existing_graph(self, planner_16):
        existing = CausalPlotGraph()
        result = planner_16.plan(graph=existing)
        assert result is existing
        assert len(existing.all_nodes()) == 16


class TestPlanVariousEpisodeCounts:
    def test_4_episodes(self):
        p = SeriesArcPlanner(total_episodes=4)
        g = p.plan()
        assert len(g.all_nodes()) == 4
        assert g.validate_act_structure()["valid"] is True

    def test_8_episodes(self):
        p = SeriesArcPlanner(total_episodes=8)
        g = p.plan()
        assert len(g.all_nodes()) == 8
        assert g.validate_act_structure()["valid"] is True

    def test_20_episodes(self):
        p = SeriesArcPlanner(total_episodes=20)
        g = p.plan()
        assert len(g.all_nodes()) == 20

    def test_2_episodes_minimum(self):
        p = SeriesArcPlanner(total_episodes=2)
        g = p.plan()
        assert len(g.all_nodes()) == 2


class TestTensionModes:
    def test_sigmoid_tension_increases_mid(self):
        p = SeriesArcPlanner(total_episodes=16, tension_mode="sigmoid")
        g = p.plan()
        nodes = g.all_nodes()
        # 8~12화 구간 텐션이 1화보다 높아야
        early = nodes[0].tension_level
        peak_region = max(n.tension_level for n in nodes[7:12])
        assert peak_region > early

    def test_linear_tension_increases(self):
        p = SeriesArcPlanner(total_episodes=8, tension_mode="linear")
        g = p.plan()
        nodes = g.all_nodes()
        assert nodes[-1].tension_level > nodes[0].tension_level

    def test_tension_curve_length(self):
        p = SeriesArcPlanner(total_episodes=12)
        g = p.plan()
        curve = g.tension_curve()
        assert len(curve) == 12


class TestPlanCustom:
    def test_plan_custom_basic(self):
        p = SeriesArcPlanner()
        specs = [
            {"episode_id": "ep_01", "episode_index": 1, "act": "기",
             "reveal_budget": 0.1, "tension_level": 0.2},
            {"episode_id": "ep_02", "episode_index": 2, "act": "승",
             "reveal_budget": 0.3, "tension_level": 0.5,
             "causal_inputs": ["ep_01"]},
            {"episode_id": "ep_03", "episode_index": 3, "act": "전",
             "reveal_budget": 0.7, "tension_level": 0.8,
             "causal_inputs": ["ep_02"]},
            {"episode_id": "ep_04", "episode_index": 4, "act": "결",
             "reveal_budget": 0.9, "tension_level": 0.4},
        ]
        g = p.plan_custom(specs)
        assert len(g.all_nodes()) == 4

    def test_plan_custom_invalid_act_fallback(self):
        p = SeriesArcPlanner()
        specs = [
            {"episode_id": "ep_01", "episode_index": 1, "act": "unknown_act"}
        ]
        g = p.plan_custom(specs)
        node = g.get_node("ep_01")
        assert node.act == ArcAct.GI  # fallback

    def test_plan_custom_forbidden_reveals(self):
        p = SeriesArcPlanner()
        specs = [
            {"episode_id": "ep_01", "episode_index": 1, "act": "기",
             "forbidden_reveals": ["fact_killer"], "reveal_budget": 0.0,
             "tension_level": 0.2},
        ]
        g = p.plan_custom(specs)
        node = g.get_node("ep_01")
        assert "fact_killer" in node.forbidden_reveals


class TestActAssignment:
    def test_act_ratios_sum_to_total(self):
        for n in [4, 8, 12, 16, 20]:
            p = SeriesArcPlanner(total_episodes=n)
            acts = p._assign_acts()
            assert len(acts) == n

    def test_gi_comes_before_gyeol(self):
        p = SeriesArcPlanner(total_episodes=16)
        acts = p._assign_acts()
        gi_last = max(i for i, a in enumerate(acts) if a == ArcAct.GI)
        gyeol_first = min(i for i, a in enumerate(acts) if a == ArcAct.GYEOL)
        assert gi_last < gyeol_first
