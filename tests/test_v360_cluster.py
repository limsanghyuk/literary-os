"""V360 T11-1: CharacterClusterDetector — Leiden 군집 탐지 테스트."""
import sys, time
sys.path.insert(0, "/tmp/v360_build")
import pytest
from literary_system.nkg.schema import (
    NKGNodeType, NKGEdgeType, CharacterNode, SceneNode, NKGEdge, ConflictType, ConflictClusterNode,
)
from literary_system.nkg.graph_store import NKGGraphStore
from literary_system.nkg.cluster.character_cluster import CharacterClusterDetector, ClusterResult

def make_char(gid, label, role="protagonist"):
    return CharacterNode(node_type=NKGNodeType.CHARACTER, node_id=gid, label=label, role=role)

def make_edge(src, tgt, etype=NKGEdgeType.CAUSAL_LINK, w=1.0):
    return NKGEdge(source=src, target=tgt, edge_type=etype, weight=w, confidence=0.9)

def chain_graph(n, etype=NKGEdgeType.CAUSAL_LINK, w=2.0):
    g = NKGGraphStore()
    for i in range(n):
        g.add_node(make_char(f"c{i}", f"인물{i}"))
    for i in range(n-1):
        g.add_edge(NKGEdge(f"c{i}", f"c{i+1}", etype, weight=w, confidence=1.0))
    return g


class TestClusterBasic:
    def test_empty_graph(self):
        r = CharacterClusterDetector(NKGGraphStore()).detect()
        assert r.clusters == [] and r.partition == {} and r.modularity == 0.0

    def test_single_char(self):
        g = NKGGraphStore(); g.add_node(make_char("c0", "A"))
        r = CharacterClusterDetector(g).detect()
        assert len(r.clusters) == 1 and "c0" in r.partition

    def test_connected_pair_same_cluster(self):
        g = NKGGraphStore()
        g.add_node(make_char("c0", "A")); g.add_node(make_char("c1", "B"))
        g.add_edge(NKGEdge("c0","c1", NKGEdgeType.CAUSAL_LINK, weight=5.0, confidence=1.0))
        r = CharacterClusterDetector(g).detect()
        assert r.partition["c0"] == r.partition["c1"]

    def test_isolated_chars_separate(self):
        g = NKGGraphStore()
        for i in range(4): g.add_node(make_char(f"c{i}", f"인물{i}"))
        r = CharacterClusterDetector(g).detect()
        assert len(set(r.partition.values())) == 4

    def test_result_type(self):
        r = CharacterClusterDetector(chain_graph(3)).detect()
        assert isinstance(r, ClusterResult)
        assert isinstance(r.modularity, float) and isinstance(r.duration_ms, float)

    def test_partition_contiguous(self):
        r = CharacterClusterDetector(chain_graph(5)).detect()
        idx = set(r.partition.values())
        assert idx == set(range(len(idx)))

    def test_partition_covers_all_chars(self):
        n = 6
        g = chain_graph(n)
        r = CharacterClusterDetector(g).detect()
        char_ids = {nd.node_id for nd in g.nodes_by_type(NKGNodeType.CHARACTER)}
        assert char_ids == set(r.partition.keys())

    def test_total_members_equals_char_count(self):
        n = 7; g = chain_graph(n)
        r = CharacterClusterDetector(g).detect()
        assert sum(len(cn.member_ids) for cn in r.clusters) == n

    def test_clusters_added_to_graph(self):
        g = chain_graph(4)
        CharacterClusterDetector(g).detect()
        assert len(g.nodes_by_type(NKGNodeType.CONFLICT_CLUSTER)) >= 1

    def test_character_cluster_id_updated(self):
        g = chain_graph(3)
        CharacterClusterDetector(g).detect()
        cids = {n.node_id for n in g.nodes_by_type(NKGNodeType.CONFLICT_CLUSTER)}
        for c in g.nodes_by_type(NKGNodeType.CHARACTER):
            assert c.cluster_id in cids


class TestClusterEdges:
    def test_in_cluster_edges_count(self):
        g = chain_graph(3)
        CharacterClusterDetector(g).detect()
        ics = [e for e in g.all_edges() if e.edge_type == NKGEdgeType.IN_CLUSTER]
        assert len(ics) == 3

    def test_in_cluster_sources_are_chars(self):
        g = chain_graph(4)
        CharacterClusterDetector(g).detect()
        cids = {n.node_id for n in g.nodes_by_type(NKGNodeType.CHARACTER)}
        for e in g.all_edges():
            if e.edge_type == NKGEdgeType.IN_CLUSTER:
                assert e.source in cids

    def test_in_cluster_targets_are_clusters(self):
        g = chain_graph(4)
        CharacterClusterDetector(g).detect()
        ccids = {n.node_id for n in g.nodes_by_type(NKGNodeType.CONFLICT_CLUSTER)}
        for e in g.all_edges():
            if e.edge_type == NKGEdgeType.IN_CLUSTER:
                assert e.target in ccids

    def test_no_duplicate_in_cluster_edges(self):
        g = chain_graph(5)
        CharacterClusterDetector(g).detect()
        ics = [(e.source, e.target) for e in g.all_edges() if e.edge_type == NKGEdgeType.IN_CLUSTER]
        assert len(ics) == len(set(ics))

    def test_cluster_node_type(self):
        r = CharacterClusterDetector(chain_graph(4)).detect()
        for cn in r.clusters:
            assert cn.node_type == NKGNodeType.CONFLICT_CLUSTER

    def test_cohesion_score_range(self):
        r = CharacterClusterDetector(chain_graph(6)).detect()
        for cn in r.clusters: assert 0.0 <= cn.cohesion_score <= 1.0

    def test_cluster_id_nonempty(self):
        r = CharacterClusterDetector(chain_graph(4)).detect()
        for cn in r.clusters: assert cn.cluster_id


class TestConflictType:
    def test_single_neutral(self):
        g = NKGGraphStore(); g.add_node(make_char("c0", "단독"))
        r = CharacterClusterDetector(g).detect()
        singles = [cn for cn in r.clusters if len(cn.member_ids) == 1]
        assert all(cn.conflict_type == ConflictType.NEUTRAL for cn in singles)

    def test_two_members_rival(self):
        g = NKGGraphStore()
        g.add_node(make_char("c0", "A")); g.add_node(make_char("c1", "B"))
        g.add_edge(NKGEdge("c0","c1", NKGEdgeType.CAUSAL_LINK, weight=5.0, confidence=1.0))
        r = CharacterClusterDetector(g).detect()
        two = [cn for cn in r.clusters if len(cn.member_ids) == 2]
        if two: assert two[0].conflict_type == ConflictType.RIVAL

    def test_antagonist_role(self):
        g = NKGGraphStore()
        for i, role in enumerate(["protagonist","antagonist","ally"]):
            g.add_node(make_char(f"c{i}", f"인물{i}", role))
        for s, t in [("c0","c1"),("c1","c2"),("c0","c2")]:
            g.add_edge(NKGEdge(s, t, NKGEdgeType.CAUSAL_LINK, weight=3.0, confidence=1.0))
        r = CharacterClusterDetector(g).detect()
        big = [cn for cn in r.clusters if len(cn.member_ids) >= 3]
        if big: assert big[0].conflict_type == ConflictType.ANTAGONIST

    def test_conflict_type_not_none(self):
        r = CharacterClusterDetector(chain_graph(5)).detect()
        for cn in r.clusters: assert isinstance(cn.conflict_type, ConflictType)


class TestPerformance:
    def test_large_graph_50_chars(self):
        g = chain_graph(50)
        t0 = time.time()
        r = CharacterClusterDetector(g).detect()
        assert time.time() - t0 < 5.0 and len(r.clusters) >= 1

    def test_two_isolated_groups(self):
        g = NKGGraphStore()
        for i in range(2):
            g.add_node(make_char(f"a{i}", f"A{i}"))
            g.add_node(make_char(f"b{i}", f"B{i}"))
        g.add_edge(NKGEdge("a0","a1", NKGEdgeType.CAUSAL_LINK, weight=5.0, confidence=1.0))
        g.add_edge(NKGEdge("b0","b1", NKGEdgeType.CAUSAL_LINK, weight=5.0, confidence=1.0))
        r = CharacterClusterDetector(g).detect()
        assert r.partition["a0"] == r.partition["a1"]
        assert r.partition["b0"] == r.partition["b1"]
        assert r.partition["a0"] != r.partition["b0"]

    def test_fully_connected_clique(self):
        n = 4; g = NKGGraphStore()
        for i in range(n): g.add_node(make_char(f"c{i}", f"인물{i}"))
        for i in range(n):
            for j in range(i+1, n):
                g.add_edge(NKGEdge(f"c{i}",f"c{j}", NKGEdgeType.CAUSAL_LINK, weight=3.0, confidence=1.0))
        r = CharacterClusterDetector(g).detect()
        assert len(set(r.partition.values())) <= 2

    def test_seed_reproducibility(self):
        results = []
        for _ in range(2):
            g = chain_graph(6)
            results.append(len(CharacterClusterDetector(g, seed=42).detect().clusters))
        assert results[0] == results[1]

    def test_duration_ms_nonnegative(self):
        r = CharacterClusterDetector(chain_graph(10)).detect()
        assert r.duration_ms >= 0.0

    def test_scene_nodes_unaffected(self):
        g = chain_graph(3)
        g.add_node(SceneNode(node_type=NKGNodeType.SCENE, node_id="s1", label="씬1"))
        before = len(g.nodes_by_type(NKGNodeType.SCENE))
        CharacterClusterDetector(g).detect()
        assert len(g.nodes_by_type(NKGNodeType.SCENE)) == before
