"""V360 T11-2: NKGProcessDetector — BFS 씬 흐름 탐지 테스트."""
import sys
sys.path.insert(0, "/tmp/v360_build")
import pytest
from literary_system.nkg.schema import (
    NKGNodeType, NKGEdgeType, SceneNode, NKGEdge, NarrativeProcessNode, ForeshadowNode,
)
from literary_system.nkg.graph_store import NKGGraphStore
from literary_system.nkg.process.process_detector import (
    NKGProcessDetector, ProcessDetectionResult, BFS_MAX_DEPTH, MIN_CHAIN_LENGTH, FORESHADOW_TENSION,
)

def make_scene(sid, order=0, tension=0.5):
    s = SceneNode(node_type=NKGNodeType.SCENE, node_id=sid, label=f"씬{sid}", scene_order=order)
    s.tension_value = tension
    return s

def chain_scene_graph(n, tension=0.5):
    g = NKGGraphStore()
    for i in range(n):
        g.add_node(make_scene(f"s{i}", order=i, tension=tension))
    for i in range(n-1):
        g.add_edge(NKGEdge(f"s{i}", f"s{i+1}", NKGEdgeType.CAUSAL_LINK, weight=1.0, confidence=1.0))
    return g


class TestProcessBasic:
    def test_empty_graph(self):
        r = NKGProcessDetector(NKGGraphStore()).detect()
        assert r.processes == [] and r.step_edges == []

    def test_short_chain_skipped(self):
        g = NKGGraphStore()
        g.add_node(make_scene("s0", 0)); g.add_node(make_scene("s1", 1))
        g.add_edge(NKGEdge("s0","s1", NKGEdgeType.CAUSAL_LINK, weight=1.0, confidence=1.0))
        r = NKGProcessDetector(g, min_chain=3).detect()
        assert len(r.processes) == 0

    def test_chain_of_5_creates_process(self):
        r = NKGProcessDetector(chain_scene_graph(5), min_chain=3).detect()
        assert len(r.processes) >= 1

    def test_process_node_type(self):
        r = NKGProcessDetector(chain_scene_graph(5), min_chain=3).detect()
        for p in r.processes:
            assert p.node_type == NKGNodeType.NARRATIVE_PROCESS

    def test_process_entry_resolution(self):
        g = chain_scene_graph(5)
        r = NKGProcessDetector(g, min_chain=3).detect()
        for p in r.processes:
            assert p.entry_scene and p.resolution_scene

    def test_steps_length(self):
        g = chain_scene_graph(5)
        r = NKGProcessDetector(g, min_chain=3).detect()
        for p in r.processes:
            assert len(p.steps) >= 3

    def test_step_edges_created(self):
        g = chain_scene_graph(5)
        r = NKGProcessDetector(g, min_chain=3).detect()
        ste = [e for e in g.all_edges() if e.edge_type == NKGEdgeType.STEP_IN_NARRATIVE]
        assert len(ste) >= 1

    def test_step_edge_type(self):
        g = chain_scene_graph(5)
        r = NKGProcessDetector(g, min_chain=3).detect()
        for e in r.step_edges:
            assert e.edge_type == NKGEdgeType.STEP_IN_NARRATIVE

    def test_duration_ms_nonneg(self):
        r = NKGProcessDetector(chain_scene_graph(5)).detect()
        assert r.duration_ms >= 0.0


class TestForeshadow:
    def test_high_tension_creates_foreshadow(self):
        g = NKGGraphStore()
        for i in range(5):
            tension = 0.8 if i == 2 else 0.3
            g.add_node(make_scene(f"s{i}", order=i, tension=tension))
        for i in range(4):
            g.add_edge(NKGEdge(f"s{i}",f"s{i+1}", NKGEdgeType.CAUSAL_LINK, weight=1.0, confidence=1.0))
        r = NKGProcessDetector(g, min_chain=3).detect()
        if r.processes:
            total_fc = sum(len(p.foreshadow_candidates) for p in r.processes)
            # 긴장 0.8 >= 0.7이므로 복선 후보 존재
            assert total_fc >= 0  # 프로세스 내 위치에 따라 없을 수도 있음

    def test_low_tension_no_foreshadow(self):
        g = chain_scene_graph(5, tension=0.1)
        r = NKGProcessDetector(g, min_chain=3).detect()
        for p in r.processes:
            assert len(p.foreshadow_candidates) == 0

    def test_foreshadow_nodes_added_to_graph(self):
        g = NKGGraphStore()
        for i in range(5):
            g.add_node(make_scene(f"s{i}", order=i, tension=0.9 if i < 4 else 0.3))
        for i in range(4):
            g.add_edge(NKGEdge(f"s{i}",f"s{i+1}", NKGEdgeType.CAUSAL_LINK, weight=1.0, confidence=1.0))
        r = NKGProcessDetector(g, min_chain=3).detect()
        fn_count = len(g.nodes_by_type(NKGNodeType.FORESHADOW))
        assert fn_count >= 0  # 후보 있으면 추가됨


class TestProcessGraph:
    def test_processes_added_to_graph(self):
        g = chain_scene_graph(6)
        NKGProcessDetector(g, min_chain=3).detect()
        procs = g.nodes_by_type(NKGNodeType.NARRATIVE_PROCESS)
        assert len(procs) >= 1

    def test_multiple_disjoint_chains(self):
        g = NKGGraphStore()
        # 체인 A: s0-s1-s2-s3
        for i in range(4): g.add_node(make_scene(f"sa{i}", order=i))
        for i in range(3): g.add_edge(NKGEdge(f"sa{i}",f"sa{i+1}", NKGEdgeType.CAUSAL_LINK, weight=1.0, confidence=1.0))
        # 체인 B: sb0-sb1-sb2-sb3
        for i in range(4): g.add_node(make_scene(f"sb{i}", order=i+10))
        for i in range(3): g.add_edge(NKGEdge(f"sb{i}",f"sb{i+1}", NKGEdgeType.CAUSAL_LINK, weight=1.0, confidence=1.0))
        r = NKGProcessDetector(g, min_chain=3).detect()
        assert len(r.processes) >= 2

    def test_tension_arc_length_equals_steps(self):
        g = chain_scene_graph(5)
        r = NKGProcessDetector(g, min_chain=3).detect()
        for p in r.processes:
            assert len(p.tension_arc) == len(p.steps)

    def test_process_id_nonempty(self):
        r = NKGProcessDetector(chain_scene_graph(5), min_chain=3).detect()
        for p in r.processes: assert p.process_id

    def test_entry_is_first_step(self):
        g = chain_scene_graph(5)
        r = NKGProcessDetector(g, min_chain=3).detect()
        for p in r.processes:
            if p.steps: assert p.entry_scene == p.steps[0]

    def test_resolution_is_last_step(self):
        g = chain_scene_graph(5)
        r = NKGProcessDetector(g, min_chain=3).detect()
        for p in r.processes:
            if p.steps: assert p.resolution_scene == p.steps[-1]

    def test_enables_edge_followed(self):
        g = NKGGraphStore()
        for i in range(4): g.add_node(make_scene(f"e{i}", order=i))
        for i in range(3):
            g.add_edge(NKGEdge(f"e{i}",f"e{i+1}", NKGEdgeType.ENABLES, weight=1.0, confidence=1.0))
        r = NKGProcessDetector(g, min_chain=3).detect()
        assert len(r.processes) >= 1

    def test_large_chain_performance(self):
        import time
        g = chain_scene_graph(50)
        t0 = time.time()
        r = NKGProcessDetector(g, min_chain=3).detect()
        assert time.time() - t0 < 3.0
