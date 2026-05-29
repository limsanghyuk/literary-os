"""
V380 테스트 — arc/causal_plot_graph.py
CausalPlotGraph: 노드/엣지 CRUD, 자동 추론, 텐션 곡선, 검증
"""
import pytest
from literary_system.arc.schema import ArcAct, ArcPlotEdgeType, ArcPlotNode, ArcPlotEdge
from literary_system.arc.causal_plot_graph import CausalPlotGraph


@pytest.fixture
def empty_graph():
    return CausalPlotGraph()


@pytest.fixture
def simple_graph():
    """4화 단순 그래프 (기기승결)"""
    g = CausalPlotGraph()
    g.add_node(ArcPlotNode("ep_01", 1, act=ArcAct.GI,   tension_level=0.2, reveal_budget=0.1))
    g.add_node(ArcPlotNode("ep_02", 2, act=ArcAct.GI,   tension_level=0.3, reveal_budget=0.1))
    g.add_node(ArcPlotNode("ep_03", 3, act=ArcAct.SEUNG,tension_level=0.6, reveal_budget=0.2,
                            causal_inputs=["ep_02"]))
    g.add_node(ArcPlotNode("ep_04", 4, act=ArcAct.GYEOL,tension_level=0.4, reveal_budget=0.8,
                            causal_inputs=["ep_03"]))
    return g


class TestCausalPlotGraphCRUD:
    def test_add_and_get_node(self, empty_graph):
        node = ArcPlotNode("ep_01", 1)
        empty_graph.add_node(node)
        assert empty_graph.get_node("ep_01") is node

    def test_get_nonexistent_node(self, empty_graph):
        assert empty_graph.get_node("ep_99") is None

    def test_remove_node(self, empty_graph):
        empty_graph.add_node(ArcPlotNode("ep_01", 1))
        empty_graph.remove_node("ep_01")
        assert empty_graph.get_node("ep_01") is None

    def test_all_nodes_sorted_by_index(self, simple_graph):
        nodes = simple_graph.all_nodes()
        indices = [n.episode_index for n in nodes]
        assert indices == sorted(indices)

    def test_nodes_by_act(self, simple_graph):
        gi_nodes = simple_graph.nodes_by_act(ArcAct.GI)
        assert len(gi_nodes) == 2
        seung_nodes = simple_graph.nodes_by_act(ArcAct.SEUNG)
        assert len(seung_nodes) == 1

    def test_add_and_get_edge(self, empty_graph):
        empty_graph.add_node(ArcPlotNode("ep_01", 1))
        empty_graph.add_node(ArcPlotNode("ep_02", 2))
        edge = ArcPlotEdge("ep_01", "ep_02", ArcPlotEdgeType.CAUSAL)
        empty_graph.add_edge(edge)
        assert len(empty_graph.all_edges()) == 1

    def test_edges_from(self, empty_graph):
        empty_graph.add_node(ArcPlotNode("ep_01", 1))
        empty_graph.add_node(ArcPlotNode("ep_02", 2))
        empty_graph.add_node(ArcPlotNode("ep_03", 3))
        empty_graph.add_edge(ArcPlotEdge("ep_01", "ep_02", ArcPlotEdgeType.CAUSAL))
        empty_graph.add_edge(ArcPlotEdge("ep_01", "ep_03", ArcPlotEdgeType.FORESHADOW))
        assert len(empty_graph.edges_from("ep_01")) == 2
        assert len(empty_graph.edges_from("ep_01", ArcPlotEdgeType.CAUSAL)) == 1

    def test_edges_to(self, empty_graph):
        empty_graph.add_node(ArcPlotNode("ep_01", 1))
        empty_graph.add_node(ArcPlotNode("ep_03", 3))
        empty_graph.add_edge(ArcPlotEdge("ep_01", "ep_03", ArcPlotEdgeType.FORESHADOW))
        assert len(empty_graph.edges_to("ep_03")) == 1
        assert len(empty_graph.edges_to("ep_03", ArcPlotEdgeType.FORESHADOW)) == 1
        assert len(empty_graph.edges_to("ep_03", ArcPlotEdgeType.CAUSAL)) == 0

    def test_remove_node_clears_edges(self, empty_graph):
        empty_graph.add_node(ArcPlotNode("ep_01", 1))
        empty_graph.add_node(ArcPlotNode("ep_02", 2))
        empty_graph.add_edge(ArcPlotEdge("ep_01", "ep_02", ArcPlotEdgeType.CAUSAL))
        empty_graph.remove_node("ep_01")
        assert len(empty_graph.all_edges()) == 0


class TestInferCausalEdges:
    def test_infer_from_causal_inputs(self, simple_graph):
        new_edges = simple_graph.infer_causal_edges()
        # ep_03.causal_inputs=["ep_02"], ep_04.causal_inputs=["ep_03"]
        causal_edges = simple_graph.edges_from("ep_02", ArcPlotEdgeType.CAUSAL)
        assert len(causal_edges) >= 1

    def test_no_duplicate_causal_edges(self, simple_graph):
        simple_graph.infer_causal_edges()
        count_before = len(simple_graph.all_edges())
        simple_graph.infer_causal_edges()  # 재호출
        count_after = len(simple_graph.all_edges())
        assert count_before == count_after

    def test_infer_returns_list(self, simple_graph):
        result = simple_graph.infer_causal_edges()
        assert isinstance(result, list)

    def test_causal_edge_source_in_graph(self, simple_graph):
        simple_graph.infer_causal_edges()
        for edge in simple_graph.all_edges():
            if edge.edge_type == ArcPlotEdgeType.CAUSAL:
                assert simple_graph.get_node(edge.source) is not None


class TestInferForeshadowEdges:
    def test_foreshadow_edges_generated(self):
        g = CausalPlotGraph()
        for i in range(1, 9):
            act = ArcAct.GI if i <= 2 else (ArcAct.SEUNG if i <= 4 else
                   (ArcAct.JEON if i <= 6 else ArcAct.GYEOL))
            g.add_node(ArcPlotNode(f"ep_{i:02d}", i, act=act,
                                    reveal_budget=0.8 if act in (ArcAct.JEON, ArcAct.GYEOL) else 0.1,
                                    tension_level=0.3 + i * 0.07))
        foreshadow_edges = g.infer_foreshadow_edges()
        assert len(foreshadow_edges) > 0

    def test_foreshadow_and_callback_pair(self):
        g = CausalPlotGraph()
        g.add_node(ArcPlotNode("ep_01", 1, act=ArcAct.GI, reveal_budget=0.1))
        g.add_node(ArcPlotNode("ep_02", 2, act=ArcAct.GI, reveal_budget=0.1))
        g.add_node(ArcPlotNode("ep_07", 7, act=ArcAct.JEON, reveal_budget=0.8))
        g.infer_foreshadow_edges()
        foreshadow = [e for e in g.all_edges() if e.edge_type == ArcPlotEdgeType.FORESHADOW]
        callback = [e for e in g.all_edges() if e.edge_type == ArcPlotEdgeType.CALLBACK]
        assert len(foreshadow) > 0
        assert len(callback) > 0

    def test_no_foreshadow_if_no_jeon_gyeol(self):
        g = CausalPlotGraph()
        g.add_node(ArcPlotNode("ep_01", 1, act=ArcAct.GI, reveal_budget=0.1))
        g.add_node(ArcPlotNode("ep_02", 2, act=ArcAct.GI, reveal_budget=0.1))
        result = g.infer_foreshadow_edges()
        assert result == []


class TestInferEmotionalEscalationEdges:
    def test_escalation_on_rising_tension(self):
        g = CausalPlotGraph()
        g.add_node(ArcPlotNode("ep_01", 1, tension_level=0.2))
        g.add_node(ArcPlotNode("ep_02", 2, tension_level=0.5))
        g.add_node(ArcPlotNode("ep_03", 3, tension_level=0.8))
        result = g.infer_emotional_escalation_edges()
        assert len(result) == 2

    def test_no_escalation_on_flat_tension(self):
        g = CausalPlotGraph()
        g.add_node(ArcPlotNode("ep_01", 1, tension_level=0.5))
        g.add_node(ArcPlotNode("ep_02", 2, tension_level=0.5))
        result = g.infer_emotional_escalation_edges()
        assert result == []

    def test_no_escalation_on_descending_tension(self):
        g = CausalPlotGraph()
        g.add_node(ArcPlotNode("ep_01", 1, tension_level=0.9))
        g.add_node(ArcPlotNode("ep_02", 2, tension_level=0.4))
        result = g.infer_emotional_escalation_edges()
        assert result == []


class TestTensionCurve:
    def test_tension_curve_returns_tuples(self, simple_graph):
        curve = simple_graph.tension_curve()
        assert isinstance(curve, list)
        for ep_id, level in curve:
            assert isinstance(ep_id, str)
            assert isinstance(level, float)

    def test_tension_curve_ordered(self, simple_graph):
        curve = simple_graph.tension_curve()
        indices = [simple_graph.get_node(ep_id).episode_index for ep_id, _ in curve]
        assert indices == sorted(indices)

    def test_tension_curve_empty_graph(self, empty_graph):
        assert empty_graph.tension_curve() == []


class TestValidateActStructure:
    def test_valid_structure(self):
        g = CausalPlotGraph()
        for i, act in enumerate([ArcAct.GI, ArcAct.SEUNG, ArcAct.JEON, ArcAct.GYEOL], 1):
            g.add_node(ArcPlotNode(f"ep_{i:02d}", i, act=act))
        result = g.validate_act_structure()
        assert result["valid"] is True
        assert len(result["issues"]) == 0

    def test_missing_act(self):
        g = CausalPlotGraph()
        g.add_node(ArcPlotNode("ep_01", 1, act=ArcAct.GI))
        g.add_node(ArcPlotNode("ep_02", 2, act=ArcAct.SEUNG))
        result = g.validate_act_structure()
        assert result["valid"] is False
        assert any("전" in issue or "결" in issue for issue in result["issues"])

    def test_empty_graph_invalid(self, empty_graph):
        result = empty_graph.validate_act_structure()
        assert result["valid"] is False

    def test_act_counts_accurate(self):
        g = CausalPlotGraph()
        for act in [ArcAct.GI, ArcAct.GI, ArcAct.SEUNG, ArcAct.JEON, ArcAct.GYEOL]:
            n = len(g._nodes)
            g.add_node(ArcPlotNode(f"ep_{n+1:02d}", n+1, act=act))
        result = g.validate_act_structure()
        assert result["act_counts"]["기"] == 2
        assert result["act_counts"]["승"] == 1


class TestSummary:
    def test_summary_keys(self, simple_graph):
        s = simple_graph.summary()
        assert "total_episodes" in s
        assert "total_edges" in s
        assert "edge_types" in s
        assert "act_structure" in s

    def test_summary_episode_count(self, simple_graph):
        assert simple_graph.summary()["total_episodes"] == 4


class TestSyncToNkg:
    def test_sync_creates_nkg_nodes(self, simple_graph):
        from literary_system.nkg.graph_store import NKGGraphStore
        from literary_system.nkg.schema import NKGNodeType
        nkg = NKGGraphStore()
        count = simple_graph.sync_to_nkg(nkg)
        assert count == 4
        ep_nodes = nkg.nodes_by_type(NKGNodeType.EPISODE)
        assert len(ep_nodes) == 4

    def test_sync_causal_edges_to_nkg(self):
        from literary_system.nkg.graph_store import NKGGraphStore
        from literary_system.nkg.schema import NKGEdgeType
        g = CausalPlotGraph()
        g.add_node(ArcPlotNode("ep_01", 1, act=ArcAct.GI))
        g.add_node(ArcPlotNode("ep_02", 2, act=ArcAct.SEUNG, causal_inputs=["ep_01"]))
        g.infer_causal_edges()
        nkg = NKGGraphStore()
        g.sync_to_nkg(nkg)
        causal = [e for e in nkg.all_edges()
                  if e.edge_type == NKGEdgeType.CAUSAL_LINK]
        assert len(causal) >= 1
