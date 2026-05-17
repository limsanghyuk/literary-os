"""tests/test_gdap_pipeline.py — DKGPipeline 5단계 통합 테스트 (30 tests)."""
import pytest
from literary_system.gdap.pipeline import (
    DKGPipeline, DKGPhaseResult,
    DKGInitPhase, DKGGraphPhase, DKGPlanPhase, DKGBuildPhase, DKGVerifyPhase,
)
from literary_system.gdap.graph_store import DKGGraphStore
from literary_system.gdap.staleness import DKGStalenessTracker
from literary_system.gdap.plan_gate import WorkDeclaration
from literary_system.gdap.schema import DKGEdgeType


# ──────────────────────────────────────────────────────────────
# DKGPhaseResult
# ──────────────────────────────────────────────────────────────

class TestDKGPhaseResult:
    def test_phase_result_defaults(self):
        r = DKGPhaseResult("init", True)
        assert r.success
        assert r.duration_ms == 0.0
        assert r.nodes_added == 0
        assert r.error is None

    def test_phase_result_with_error(self):
        r = DKGPhaseResult("build", False, error="fail")
        assert not r.success
        assert r.error == "fail"


# ──────────────────────────────────────────────────────────────
# Phase 1: INIT
# ──────────────────────────────────────────────────────────────

class TestInitPhase:
    def test_init_with_file_list(self):
        g = DKGGraphStore()
        t = DKGStalenessTracker()
        phase = DKGInitPhase(g, t)
        r = phase.run(".", file_list=["a.py", "b.py", "c.py"])
        assert r.success
        assert r.nodes_added == 3

    def test_init_marks_dirty_on_first_scan(self):
        g = DKGGraphStore()
        t = DKGStalenessTracker()
        phase = DKGInitPhase(g, t)
        phase.run(".", file_list=["a.py"])
        # 처음 등록 → 새로운 해시 → dirty 마킹 후 register로 해제
        assert t.is_registered("file:a.py")

    def test_init_registers_nodes(self):
        g = DKGGraphStore()
        t = DKGStalenessTracker()
        phase = DKGInitPhase(g, t)
        phase.run(".", file_list=["x.py"])
        assert g.get_node("file:x.py") is not None

    def test_init_empty_file_list(self):
        g = DKGGraphStore()
        t = DKGStalenessTracker()
        phase = DKGInitPhase(g, t)
        r = phase.run(".", file_list=[])
        assert r.success
        assert r.nodes_added == 0

    def test_init_data_contains_source_count(self):
        g = DKGGraphStore()
        t = DKGStalenessTracker()
        phase = DKGInitPhase(g, t)
        r = phase.run(".", file_list=["a.py", "b.py"])
        assert r.data["source_count"] == 2


# ──────────────────────────────────────────────────────────────
# Phase 2: GRAPH
# ──────────────────────────────────────────────────────────────

class TestGraphPhase:
    def _make(self):
        g = DKGGraphStore()
        t = DKGStalenessTracker()
        for f in ["a.py", "b.py", "c.py"]:
            g.add_file_node(f)
        return g, t

    def test_graph_adds_edges(self):
        g, t = self._make()
        phase = DKGGraphPhase(g, t)
        r = phase.run(edges=[
            ("file:a.py", "file:b.py", DKGEdgeType.IMPORTS),
            ("file:b.py", "file:c.py", DKGEdgeType.IMPORTS),
        ])
        assert r.success
        assert r.edges_added == 2

    def test_graph_no_duplicate_edges(self):
        g, t = self._make()
        phase = DKGGraphPhase(g, t)
        phase.run(edges=[("file:a.py", "file:b.py", DKGEdgeType.IMPORTS)])
        r2 = phase.run(edges=[("file:a.py", "file:b.py", DKGEdgeType.IMPORTS)])
        assert r2.edges_added == 0

    def test_graph_extended_tuple(self):
        g, t = self._make()
        phase = DKGGraphPhase(g, t)
        r = phase.run(edges=[("file:a.py", "file:b.py", DKGEdgeType.CALLS, 0.9, 0.8)])
        assert r.edges_added == 1

    def test_graph_empty_edges(self):
        g, t = self._make()
        phase = DKGGraphPhase(g, t)
        r = phase.run(edges=[])
        assert r.success and r.edges_added == 0


# ──────────────────────────────────────────────────────────────
# Phase 3: PLAN
# ──────────────────────────────────────────────────────────────

class TestPlanPhase:
    def _setup(self):
        g = DKGGraphStore()
        t = DKGStalenessTracker()
        for f in ["a.py", "b.py", "c.py"]:
            g.add_file_node(f)
        return g, t

    def test_plan_approved(self):
        g, t = self._setup()
        phase = DKGPlanPhase(g, t)
        decl = WorkDeclaration(target_files=["a.py"], reason="fix")
        r = phase.run(decl)
        assert r.success
        assert r.data["gate_approved"]

    def test_plan_rejected_empty_target(self):
        g, t = self._setup()
        phase = DKGPlanPhase(g, t)
        decl = WorkDeclaration(target_files=[])
        r = phase.run(decl)
        assert not r.success
        assert r.error is not None

    def test_plan_data_has_blast_ratio(self):
        g, t = self._setup()
        phase = DKGPlanPhase(g, t)
        decl = WorkDeclaration(target_files=["a.py"], reason="fix")
        r = phase.run(decl)
        assert "blast_ratio" in r.data

    def test_plan_data_has_blast_radius_summary(self):
        g, t = self._setup()
        phase = DKGPlanPhase(g, t)
        decl = WorkDeclaration(target_files=["a.py"], reason="fix")
        r = phase.run(decl)
        assert "blast_radius" in r.data


# ──────────────────────────────────────────────────────────────
# Phase 4: BUILD
# ──────────────────────────────────────────────────────────────

class TestBuildPhase:
    def _setup(self):
        g = DKGGraphStore()
        t = DKGStalenessTracker()
        for f in ["a.py", "b.py"]:
            g.add_file_node(f)
            t.register(f"file:{f}", "old_hash")
        g.add_edge_raw("file:a.py", "file:b.py", DKGEdgeType.IMPORTS)
        return g, t

    def test_build_modifies_target(self):
        g, t = self._setup()
        phase = DKGBuildPhase(g, t)
        decl = WorkDeclaration(target_files=["a.py"], preserved_files=["b.py"])
        r = phase.run(decl)
        assert r.success
        assert r.nodes_added == 1

    def test_build_propagates_dirty_to_neighbors(self):
        g, t = self._setup()
        phase = DKGBuildPhase(g, t)
        decl = WorkDeclaration(target_files=["a.py"])
        phase.run(decl)
        # a.py → b.py (IMPORTS) → b.py 는 dirty 전파 대상
        assert t.is_dirty("file:b.py")

    def test_build_rejects_preserved_file_invasion(self):
        g, t = self._setup()
        phase = DKGBuildPhase(g, t)
        decl = WorkDeclaration(
            target_files    = ["b.py"],  # target
            preserved_files = ["b.py"],  # 동시에 preserved → 거부
        )
        r = phase.run(decl)
        assert not r.success
        assert "보존 파일 침범" in r.error

    def test_build_with_apply_fn(self):
        g, t = self._setup()
        phase = DKGBuildPhase(g, t)
        hashes = {}
        def apply(path):
            hashes[path] = "newhash_" + path
            return hashes[path]
        decl = WorkDeclaration(target_files=["a.py"])
        r = phase.run(decl, apply_fn=apply)
        assert r.success
        assert "a.py" in hashes


# ──────────────────────────────────────────────────────────────
# Phase 5: VERIFY
# ──────────────────────────────────────────────────────────────

class TestVerifyPhase:
    def test_verify_clears_dirty_on_pass(self):
        g = DKGGraphStore()
        t = DKGStalenessTracker()
        t.mark_dirty("file:a.py")
        t.mark_dirty("test:tests/t.py:test_x")
        phase = DKGVerifyPhase(g, t)
        r = phase.run()
        assert r.success
        assert len(t.dirty_nodes()) == 0

    def test_verify_fails_on_test_failure(self):
        g = DKGGraphStore()
        t = DKGStalenessTracker()
        phase = DKGVerifyPhase(g, t)
        def failing_runner():
            return {"passed": 5, "failed": 1, "failures": ["test_foo"]}
        r = phase.run(failing_runner)
        assert not r.success
        assert r.data["failed"] == 1

    def test_verify_dirty_cleared_only_on_pass(self):
        g = DKGGraphStore()
        t = DKGStalenessTracker()
        t.mark_dirty("file:a.py")
        phase = DKGVerifyPhase(g, t)
        def failing_runner():
            return {"passed": 0, "failed": 1, "failures": ["x"]}
        phase.run(failing_runner)
        # 실패 시 dirty 유지
        assert t.is_dirty("file:a.py")


# ──────────────────────────────────────────────────────────────
# DKGPipeline — 통합
# ──────────────────────────────────────────────────────────────

class TestDKGPipelineIntegration:
    def test_pipeline_init_and_build_graph(self):
        pipe = DKGPipeline()
        r1 = pipe.init(file_list=["a.py", "b.py"])
        r2 = pipe.build_graph(edges=[
            ("file:a.py", "file:b.py", DKGEdgeType.IMPORTS)
        ])
        assert r1.success and r2.success

    def test_pipeline_plan_approved(self):
        pipe = DKGPipeline()
        pipe.init(file_list=["a.py", "b.py"])
        decl = WorkDeclaration(target_files=["a.py"], reason="fix")
        r = pipe.plan(decl)
        assert r.success

    def test_pipeline_build_after_plan(self):
        pipe = DKGPipeline()
        pipe.init(file_list=["a.py", "b.py"])
        decl = WorkDeclaration(target_files=["a.py"], reason="fix")
        pipe.plan(decl)
        r = pipe.build()
        assert r.success

    def test_pipeline_build_no_plan_fails(self):
        pipe = DKGPipeline()
        r = pipe.build()
        assert not r.success

    def test_pipeline_verify_clears_dirty(self):
        pipe = DKGPipeline()
        pipe.init(file_list=["a.py"])
        decl = WorkDeclaration(target_files=["a.py"], reason="fix")
        pipe.plan(decl)
        pipe.build()
        r = pipe.verify()
        assert r.success
        assert len(pipe.tracker.dirty_nodes()) == 0

    def test_pipeline_run_full_success(self):
        pipe = DKGPipeline()
        decl = WorkDeclaration(target_files=["a.py"], reason="integration test")
        results = pipe.run_full(
            declaration = decl,
            file_list   = ["a.py", "b.py"],
            edges       = [("file:a.py", "file:b.py", DKGEdgeType.IMPORTS)],
        )
        assert all(r.success for r in results)
        assert len(results) == 5

    def test_pipeline_run_full_stops_at_gate_reject(self):
        pipe = DKGPipeline()
        decl = WorkDeclaration(target_files=[])  # 거부 조건
        results = pipe.run_full(
            declaration = decl,
            file_list   = ["a.py"],
        )
        phases = [r.phase_name for r in results]
        assert "plan" in phases
        assert "build" not in phases

    def test_pipeline_stats_keys(self):
        pipe = DKGPipeline()
        pipe.init(file_list=["a.py"])
        s = pipe.stats()
        assert "graph" in s
        assert "tracker" in s
        assert "phases_run" in s

    def test_pipeline_blast_radius_for(self):
        pipe = DKGPipeline()
        pipe.init(file_list=["a.py", "b.py"])
        pipe.build_graph(edges=[("file:a.py", "file:b.py", DKGEdgeType.IMPORTS)])
        br = pipe.blast_radius_for(["file:a.py"])
        assert "file:a.py" in br.affected_nodes

    def test_pipeline_last_results(self):
        pipe = DKGPipeline()
        pipe.init(file_list=["a.py"])
        pipe.build_graph(edges=[])
        results = pipe.last_results()
        assert len(results) == 2
        assert results[0].phase_name == "init"
        assert results[1].phase_name == "graph"
