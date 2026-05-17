"""V360 T11-9: DKGPipeline v2 — 7단계 통합 테스트."""
import sys
sys.path.insert(0, "/tmp/v360_build")
import pytest
from literary_system.nkg.schema import (
    NKGNodeType, NKGEdgeType, SceneNode, CharacterNode, NKGEdge,
)
from literary_system.nkg.graph_store import NKGGraphStore
from literary_system.nkg.semantic_model import SemanticModelState
from literary_system.gdap.pipeline import DKGPipeline, PipelinePhase, DKGPhaseResult
from literary_system.gdap.plan_gate import WorkDeclaration


def make_populated_nkg(n_scenes=4, n_chars=3):
    g = NKGGraphStore()
    for i in range(n_scenes):
        s = SceneNode(node_type=NKGNodeType.SCENE, node_id=f"s{i}", label=f"씬{i}",
                      scene_order=i)
        s.tension_value = 0.3 + 0.1 * i
        g.add_node(s)
    for i in range(n_chars):
        g.add_node(CharacterNode(node_type=NKGNodeType.CHARACTER,
                                  node_id=f"c{i}", label=f"인물{i}"))
    for i in range(n_scenes-1):
        g.add_edge(NKGEdge(f"s{i}",f"s{i+1}", NKGEdgeType.CAUSAL_LINK, weight=1.0, confidence=1.0))
    for i in range(n_chars-1):
        g.add_edge(NKGEdge(f"c{i}",f"c{i+1}", NKGEdgeType.CAUSAL_LINK, weight=1.0, confidence=1.0))
    return g


class TestPipelineInit:
    def test_init_phase_success(self):
        p = DKGPipeline(make_populated_nkg())
        r = p.init(file_list=["f1","f2"])
        assert r.success and r.phase == PipelinePhase.INIT

    def test_init_metadata(self):
        p = DKGPipeline(make_populated_nkg())
        r = p.init(file_list=["f1","f2"])
        assert r.metadata.get("files") == 2

    def test_init_duration_nonneg(self):
        p = DKGPipeline(make_populated_nkg())
        r = p.init()
        assert r.duration_ms >= 0


class TestPipelineBuildGraph:
    def test_build_graph_adds_nodes(self):
        p = DKGPipeline()
        extra_nodes = [SceneNode(node_type=NKGNodeType.SCENE, node_id="sx", label="추가씬")]
        r = p.build_graph(nkg_nodes=extra_nodes)
        assert r.success
        assert p.nkg.get_node("sx") is not None

    def test_build_graph_adds_edges(self):
        p = DKGPipeline()
        p.build_graph(nkg_nodes=[
            SceneNode(node_type=NKGNodeType.SCENE, node_id="s0", label="씬0"),
            SceneNode(node_type=NKGNodeType.SCENE, node_id="s1", label="씬1"),
        ])
        r2 = p.build_graph(nkg_edges=[
            NKGEdge("s0","s1", NKGEdgeType.CAUSAL_LINK, weight=1.0, confidence=1.0)
        ])
        assert r2.success

    def test_build_graph_empty_ok(self):
        p = DKGPipeline()
        r = p.build_graph()
        assert r.success


class TestPipelineCommunities:
    def test_communities_phase_success(self):
        p = DKGPipeline(make_populated_nkg())
        r = p.communities()
        assert r.success and r.phase == PipelinePhase.COMMUNITIES

    def test_communities_metadata_keys(self):
        p = DKGPipeline(make_populated_nkg())
        r = p.communities()
        assert "clusters" in r.metadata

    def test_communities_empty_graph_ok(self):
        p = DKGPipeline(NKGGraphStore())
        r = p.communities()
        assert r.success and r.metadata["clusters"] == 0


class TestPipelineProcesses:
    def test_processes_phase_success(self):
        p = DKGPipeline(make_populated_nkg(n_scenes=5))
        r = p.processes()
        assert r.success and r.phase == PipelinePhase.PROCESSES

    def test_processes_metadata_keys(self):
        p = DKGPipeline(make_populated_nkg(n_scenes=5))
        r = p.processes()
        assert "processes" in r.metadata and "foreshadows" in r.metadata

    def test_processes_empty_graph_ok(self):
        p = DKGPipeline(NKGGraphStore())
        r = p.processes()
        assert r.success


class TestPipelinePlan:
    def test_plan_phase_freezes_model(self):
        p = DKGPipeline(make_populated_nkg())
        p.plan()
        assert p.model.is_frozen()

    def test_plan_phase_success(self):
        p = DKGPipeline(make_populated_nkg())
        r = p.plan()
        assert r.success and r.phase == PipelinePhase.PLAN

    def test_plan_metadata_has_frozen(self):
        p = DKGPipeline(make_populated_nkg())
        r = p.plan()
        assert "frozen" in r.metadata and r.metadata["frozen"]

    def test_plan_with_declaration(self):
        p = DKGPipeline(make_populated_nkg())
        decl = WorkDeclaration(impact_analysis_run=True, semantic_frozen=True)
        r = p.plan(decl)
        assert r.success


class TestPipelineBuild:
    def test_build_phase_ok(self):
        p = DKGPipeline(make_populated_nkg())
        r = p.build()
        assert r.success and r.phase == PipelinePhase.BUILD

    def test_build_apply_fn_called(self):
        p = DKGPipeline(make_populated_nkg())
        p.plan()
        called = []
        def apply(nkg): called.append(True)
        r = p.build(apply_fn=apply)
        assert r.success and called

    def test_build_without_apply_ok(self):
        p = DKGPipeline(make_populated_nkg())
        r = p.build()
        assert r.success


class TestPipelineVerify:
    def test_verify_after_plan_ok(self):
        p = DKGPipeline(make_populated_nkg())
        p.plan()
        r = p.verify(reader_surface_gate=9.0)
        assert r.success and r.phase == PipelinePhase.VERIFY

    def test_verify_score_above_gate(self):
        p = DKGPipeline(make_populated_nkg())
        p.plan()
        r = p.verify(test_runner_fn=lambda: 9.5, reader_surface_gate=9.0)
        assert r.metadata["passed"] is True

    def test_verify_score_below_gate(self):
        p = DKGPipeline(make_populated_nkg())
        p.plan()
        r = p.verify(test_runner_fn=lambda: 7.0, reader_surface_gate=9.0)
        assert r.metadata["passed"] is False

    def test_verify_without_plan_fails(self):
        p = DKGPipeline(make_populated_nkg())
        r = p.verify()
        assert not r.success  # frozen 아니면 실패


class TestRunFull:
    def test_run_full_returns_7_phases(self):
        p = DKGPipeline(make_populated_nkg())
        results = p.run_full()
        assert len(results) == 7

    def test_run_full_phase_order(self):
        p = DKGPipeline(make_populated_nkg())
        results = p.run_full()
        expected = [PipelinePhase.INIT, PipelinePhase.GRAPH, PipelinePhase.COMMUNITIES,
                    PipelinePhase.PROCESSES, PipelinePhase.PLAN, PipelinePhase.BUILD,
                    PipelinePhase.VERIFY]
        assert [r.phase for r in results] == expected

    def test_run_full_all_success(self):
        p = DKGPipeline(make_populated_nkg())
        results = p.run_full(reader_surface_gate=0.0)
        assert all(r.success for r in results)

    def test_run_full_model_frozen(self):
        p = DKGPipeline(make_populated_nkg())
        p.run_full()
        assert p.model.is_frozen()

    def test_run_full_with_nodes(self):
        p = DKGPipeline()
        extra = [SceneNode(node_type=NKGNodeType.SCENE, node_id=f"s{i}", label=f"씬{i}",
                           scene_order=i)
                 for i in range(4)]
        results = p.run_full(nkg_nodes=extra, reader_surface_gate=0.0)
        assert len(results) == 7 and all(r.success for r in results)

    def test_phase_results_accumulated(self):
        p = DKGPipeline(make_populated_nkg())
        p.init(); p.communities(); p.processes()
        assert len(p.phase_results()) == 3

    def test_dkg_phase_result_fields(self):
        p = DKGPipeline(make_populated_nkg())
        r = p.init()
        assert isinstance(r, DKGPhaseResult)
        assert hasattr(r, "phase") and hasattr(r, "success")
        assert hasattr(r, "duration_ms") and hasattr(r, "metadata")
