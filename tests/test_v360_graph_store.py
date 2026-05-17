"""V360: NKGGraphStore 확장 기능 테스트."""
import sys
sys.path.insert(0, "/tmp/v360_build")
import pytest
from literary_system.nkg.schema import (
    NKGNodeType, NKGEdgeType, SceneNode, CharacterNode, ForeshadowNode,
    NKGEdge, ConflictClusterNode, NarrativeProcessNode, ConflictType,
    make_cluster_id, make_process_id,
)
from literary_system.nkg.graph_store import NKGGraphStore


def make_scene(sid, order=0):
    return SceneNode(node_type=NKGNodeType.SCENE, node_id=sid, label=f"씬{sid}", scene_order=order)

def make_char(cid, label="인물"):
    return CharacterNode(node_type=NKGNodeType.CHARACTER, node_id=cid, label=label)


class TestGraphStoreBasic:
    def test_add_get_node(self):
        g = NKGGraphStore(); g.add_node(make_scene("s1"))
        assert g.get_node("s1") is not None

    def test_remove_node(self):
        g = NKGGraphStore(); g.add_node(make_scene("s1"))
        g.remove_node("s1")
        assert g.get_node("s1") is None

    def test_get_nonexistent_none(self):
        assert NKGGraphStore().get_node("nope") is None

    def test_node_count(self):
        g = NKGGraphStore()
        for i in range(5): g.add_node(make_scene(f"s{i}"))
        assert g.node_count() == 5

    def test_edge_count(self):
        g = NKGGraphStore()
        g.add_node(make_scene("s0")); g.add_node(make_scene("s1"))
        g.add_edge(NKGEdge("s0","s1", NKGEdgeType.CAUSAL_LINK, weight=1.0, confidence=1.0))
        assert g.edge_count() == 1

    def test_all_nodes(self):
        g = NKGGraphStore()
        for i in range(3): g.add_node(make_scene(f"s{i}"))
        assert len(g.all_nodes()) == 3

    def test_nodes_by_type_scene(self):
        g = NKGGraphStore()
        g.add_node(make_scene("s1")); g.add_node(make_char("c1"))
        scenes = g.nodes_by_type(NKGNodeType.SCENE)
        assert len(scenes) == 1 and scenes[0].node_id == "s1"

    def test_edges_from(self):
        g = NKGGraphStore()
        g.add_node(make_scene("s0")); g.add_node(make_scene("s1"))
        g.add_edge(NKGEdge("s0","s1", NKGEdgeType.CAUSAL_LINK, weight=1.0, confidence=1.0))
        assert len(g.edges_from("s0")) == 1

    def test_edges_to(self):
        g = NKGGraphStore()
        g.add_node(make_scene("s0")); g.add_node(make_scene("s1"))
        g.add_edge(NKGEdge("s0","s1", NKGEdgeType.CAUSAL_LINK, weight=1.0, confidence=1.0))
        assert len(g.edges_to("s1")) == 1

    def test_edges_from_with_type_filter(self):
        g = NKGGraphStore()
        g.add_node(make_scene("s0")); g.add_node(make_scene("s1")); g.add_node(make_scene("s2"))
        g.add_edge(NKGEdge("s0","s1", NKGEdgeType.CAUSAL_LINK, weight=1.0, confidence=1.0))
        g.add_edge(NKGEdge("s0","s2", NKGEdgeType.ENABLES, weight=1.0, confidence=1.0))
        assert len(g.edges_from("s0", NKGEdgeType.CAUSAL_LINK)) == 1

    def test_all_edges(self):
        g = NKGGraphStore()
        g.add_node(make_scene("s0")); g.add_node(make_scene("s1"))
        g.add_edge(NKGEdge("s0","s1", NKGEdgeType.CAUSAL_LINK, weight=1.0, confidence=1.0))
        assert len(g.all_edges()) == 1


class TestGraphStoreV360Queries:
    def test_clusters_empty(self):
        assert NKGGraphStore().clusters() == []

    def test_clusters_returns_cluster_nodes(self):
        g = NKGGraphStore()
        cn = ConflictClusterNode(node_type=NKGNodeType.CONFLICT_CLUSTER,
                                  node_id="cl1", label="군집1",
                                  cluster_id="cl1", conflict_type=ConflictType.RIVAL)
        g.add_node(cn)
        assert len(g.clusters()) == 1

    def test_processes_empty(self):
        assert NKGGraphStore().processes() == []

    def test_processes_returns_process_nodes(self):
        g = NKGGraphStore()
        pn = NarrativeProcessNode(node_type=NKGNodeType.NARRATIVE_PROCESS,
                                   node_id="p1", label="프로세스1",
                                   process_id="p1")
        g.add_node(pn)
        assert len(g.processes()) == 1

    def test_cluster_members_query(self):
        g = NKGGraphStore()
        g.add_node(make_char("c0","A")); g.add_node(make_char("c1","B"))
        cn = ConflictClusterNode(node_type=NKGNodeType.CONFLICT_CLUSTER,
                                  node_id="cl1", label="군집",
                                  cluster_id="cl1", member_ids=["c0","c1"],
                                  conflict_type=ConflictType.RIVAL)
        g.add_node(cn)
        members = g.cluster_members("cl1")
        assert len(members) == 2

    def test_process_steps_query(self):
        g = NKGGraphStore()
        g.add_node(make_scene("s0")); g.add_node(make_scene("s1"))
        pn = NarrativeProcessNode(node_type=NKGNodeType.NARRATIVE_PROCESS,
                                   node_id="p1", label="프로세스",
                                   process_id="p1", steps=["s0","s1"])
        g.add_node(pn)
        steps = g.process_steps("p1")
        assert len(steps) == 2

    def test_foreshadow_candidates(self):
        g = NKGGraphStore()
        fn = ForeshadowNode(node_type=NKGNodeType.FORESHADOW,
                             node_id="f1", label="복선1", is_candidate=True)
        fn2 = ForeshadowNode(node_type=NKGNodeType.FORESHADOW,
                              node_id="f2", label="복선2", is_candidate=False)
        g.add_node(fn); g.add_node(fn2)
        candidates = g.foreshadow_candidates()
        assert len(candidates) == 1 and candidates[0].node_id == "f1"

    def test_snapshot_keys(self):
        g = NKGGraphStore()
        for i in range(3): g.add_node(make_scene(f"s{i}"))
        snap = g.snapshot()
        assert "node_count" in snap and snap["node_count"] == 3

    def test_make_cluster_id(self):
        assert make_cluster_id(0) == "cluster_0000"
        assert make_cluster_id(5) == "cluster_0005"

    def test_make_process_id(self):
        assert make_process_id(0) == "process_0000"
        assert make_process_id(3) == "process_0003"
