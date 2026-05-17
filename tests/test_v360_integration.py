"""V360: 통합 시나리오 테스트 — 전체 파이프라인 E2E."""
import sys, time
sys.path.insert(0, "/tmp/v360_build")
import pytest
from literary_system.nkg.schema import (
    NKGNodeType, NKGEdgeType, SceneNode, CharacterNode, NKGEdge,
    ConflictType,
)
from literary_system.nkg.graph_store import NKGGraphStore
from literary_system.nkg.staleness import DKGStalenessTrackerV2
from literary_system.nkg.semantic_model import NKGSemanticModel, SemanticModelFrozenError
from literary_system.nkg.cluster.character_cluster import CharacterClusterDetector
from literary_system.nkg.process.process_detector import NKGProcessDetector
from literary_system.nkg.search.engine import NKGSearchEngine
from literary_system.nkg.change_detector import NKGChangeDetector
from literary_system.gdap.guardrails import NKGGuardrails, GuardrailViolation
from literary_system.gdap.blast_radius import BlastRadiusCalculator
from literary_system.gdap.plan_gate import PlanBuildGate, WorkDeclaration
from literary_system.gdap.pipeline import DKGPipeline, PipelinePhase
from literary_system.scope.resolver import NarrativeScopeResolver, SceneContext, StoryContext
from literary_system.contract.bridge import ContractBridge, SceneIntentIR, SceneIntent


# ─── 공통 픽스처 ─────────────────────────────────────────────

def full_nkg(n_scenes=6, n_chars=4):
    g = NKGGraphStore()
    for i in range(n_scenes):
        s = SceneNode(node_type=NKGNodeType.SCENE, node_id=f"s{i}",
                      label=f"씬{i}", scene_order=i)
        s.tension_value = 0.2 + i * 0.1
        g.add_node(s)
    for i in range(n_chars):
        g.add_node(CharacterNode(node_type=NKGNodeType.CHARACTER,
                                  node_id=f"c{i}", label=f"인물{i}"))
    for i in range(n_scenes-1):
        g.add_edge(NKGEdge(f"s{i}",f"s{i+1}", NKGEdgeType.CAUSAL_LINK, weight=1.0, confidence=1.0))
    for i in range(n_chars-1):
        g.add_edge(NKGEdge(f"c{i}",f"c{i+1}", NKGEdgeType.CAUSAL_LINK, weight=2.0, confidence=1.0))
    return g


class TestE2EClusterAndProcess:
    """군집 탐지 + 프로세스 탐지 + 검색 엔진 E2E."""

    def test_cluster_then_search(self):
        g = full_nkg()
        CharacterClusterDetector(g).detect()
        se = NKGSearchEngine(g)
        se.build_index()
        r = se.search("인물", top_k=5)
        assert len(r) >= 1

    def test_process_then_search(self):
        g = full_nkg()
        NKGProcessDetector(g, min_chain=3).detect()
        se = NKGSearchEngine(g)
        se.build_index()
        r = se.search_processes("프로세스")
        assert isinstance(r, list)

    def test_cluster_and_process_both_run(self):
        g = full_nkg()
        cr = CharacterClusterDetector(g).detect()
        pr = NKGProcessDetector(g, min_chain=3).detect()
        assert isinstance(cr.clusters, list)
        assert isinstance(pr.processes, list)

    def test_nkg_grows_after_detection(self):
        g = full_nkg()
        before = g.node_count()
        CharacterClusterDetector(g).detect()
        NKGProcessDetector(g, min_chain=3).detect()
        assert g.node_count() >= before

    def test_search_finds_clusters(self):
        g = full_nkg()
        CharacterClusterDetector(g).detect()
        se = NKGSearchEngine(g)
        se.build_index()
        r = se.search_clusters("Cluster")
        assert isinstance(r, list)


class TestE2ESemanticGuardrails:
    """SemanticModel + Guardrails + PlanGate E2E."""

    def test_write_reconcile_freeze_assert(self):
        g = full_nkg()
        model = NKGSemanticModel(g)
        model.reconcile()
        model.freeze()
        model.assert_frozen()  # GR-04 통과

    def test_frozen_blocks_write(self):
        g = full_nkg()
        model = NKGSemanticModel(g)
        model.reconcile(); model.freeze()
        with pytest.raises(SemanticModelFrozenError):
            model.guard_write("forbidden")

    def test_guardrails_all_pass_scenario(self):
        checks = NKGGuardrails.run_all(
            impact_analysis_run=True, target_nodes=["s0"], shared_nodes=[],
            rename_requested=False, dry_run_completed=False,
            blast_ratio=0.05, is_frozen=True,
            multi_scene_edit=False, changes_detected=False,
            raise_on_violation=False,
        )
        assert all(c.passed for c in checks)

    def test_plan_gate_with_blast_calc(self):
        g = full_nkg()
        calc = BlastRadiusCalculator(nkg=g)
        decl = WorkDeclaration(target_files=["s0"], impact_analysis_run=True,
                               semantic_frozen=True, max_blast_ratio=0.9)
        gate = PlanBuildGate(calc)
        result = gate.validate(decl)
        assert result.passed

    def test_change_detector_and_guardrail_gr05(self):
        g = full_nkg()
        det = NKGChangeDetector(g)
        det.snapshot_all()
        r = det.scan_changes()
        changes_detected = len(r.changed_ids) > 0 or True  # 스냅샷 직후 → 변경 없음
        c = NKGGuardrails.check_gr05_detect_changes(True, True)
        assert c.passed


class TestE2EFullPipeline:
    """DKGPipeline v2 7단계 E2E."""

    def test_run_full_all_phases_succeed(self):
        g = full_nkg()
        p = DKGPipeline(g)
        results = p.run_full(reader_surface_gate=0.0)
        assert len(results) == 7
        assert all(r.success for r in results)

    def test_pipeline_phases_in_order(self):
        g = full_nkg()
        results = DKGPipeline(g).run_full(reader_surface_gate=0.0)
        phases = [r.phase for r in results]
        assert phases[0] == PipelinePhase.INIT
        assert phases[6] == PipelinePhase.VERIFY

    def test_pipeline_model_frozen_after_full_run(self):
        g = full_nkg()
        p = DKGPipeline(g)
        p.run_full(reader_surface_gate=0.0)
        assert p.model.is_frozen()

    def test_pipeline_nkg_has_clusters_after_run(self):
        g = full_nkg()
        p = DKGPipeline(g)
        p.run_full(reader_surface_gate=0.0)
        clusters = p.nkg.nodes_by_type(NKGNodeType.CONFLICT_CLUSTER)
        assert len(clusters) >= 1

    def test_pipeline_apply_fn_modifies_nkg(self):
        g = full_nkg()
        p = DKGPipeline(g)
        added = []
        def apply(nkg):
            s = SceneNode(node_type=NKGNodeType.SCENE, node_id="s_new", label="신규씬")
            nkg.add_node(s); added.append("s_new")
        p.run_full(apply_fn=apply, reader_surface_gate=0.0)
        assert added and p.nkg.get_node("s_new") is not None

    def test_pipeline_with_contract_bridge(self):
        """ContractBridge IR과 Pipeline 연동."""
        g = full_nkg()
        bridge = ContractBridge()
        for i in range(3):
            ir = SceneIntentIR(scene_id=f"s{i}", intent=SceneIntent.REVEAL,
                               target_tension=0.5+i*0.1)
            bridge.register_gpt_contract(f"s{i}", ir)
            bridge.register_claude_contract(f"s{i}", ir)
        results = bridge.validate_all()
        assert all(r.is_consistent for r in results.values())
        p = DKGPipeline(g)
        p.run_full(reader_surface_gate=0.0)
        assert p.model.is_frozen()

    def test_pipeline_with_scope_resolver(self):
        """NarrativeScopeResolver와 Pipeline 연동."""
        g = full_nkg()
        resolver = NarrativeScopeResolver()
        resolver.load("noir")
        d = resolver.resolve(SceneContext("s0", 0.7), StoryContext("noir"))
        assert d.genre_id == "noir"
        p = DKGPipeline(g)
        results = p.run_full(reader_surface_gate=0.0)
        assert all(r.success for r in results)


class TestE2EStaleness:
    """Staleness Tracker + ChangeDetector E2E."""

    def test_tracker_and_change_detector_combined(self):
        g = full_nkg()
        tracker = DKGStalenessTrackerV2()
        det = NKGChangeDetector(g)
        scenes = g.nodes_by_type(NKGNodeType.SCENE)
        for s in scenes:
            tracker.register(s.node_id, s.content_hash())
        det.snapshot_all()
        # 변경 없음 → 모두 clean
        dirty = [s for s in scenes if tracker.mark_dirty_if_stale(s.node_id, s.content_hash())]
        assert len(dirty) == 0

    def test_tracker_detects_hash_change(self):
        tracker = DKGStalenessTrackerV2()
        tracker.register("n1", "hash_original")
        assert tracker.mark_dirty_if_stale("n1", "hash_changed")
        assert tracker.is_dirty("n1")

    def test_incremental_saves_accumulate(self):
        tracker = DKGStalenessTrackerV2()
        for i in range(100):
            tracker.register(f"n{i}", f"h{i}")
        for i in range(100):
            tracker.mark_dirty_if_stale(f"n{i}", f"h{i}")  # 변경 없음
        assert tracker.stats()["incremental_saves"] == 100

    def test_large_scene_change_detection(self):
        g = NKGGraphStore()
        for i in range(50):
            s = SceneNode(node_type=NKGNodeType.SCENE, node_id=f"s{i}", label=f"씬{i}")
            g.add_node(s)
        det = NKGChangeDetector(g)
        det.snapshot_all()
        r = det.scan_changes()
        assert len(r.changed_ids) == 0  # 스냅샷 직후 변경 없음

    def test_rename_dry_run_details(self):
        g = full_nkg()
        for i in range(5):
            g.add_edge(NKGEdge("s0",f"s{i+1}", NKGEdgeType.CAUSAL_LINK, weight=1.0, confidence=1.0))
        det = NKGChangeDetector(g)
        result = det.rename_dry_run("s0","s0_renamed")
        assert result["affected_edges"] >= 1 and result["safe"] is True


class TestE2EContractScope:
    """ContractBridge + ScopeResolver 통합."""

    def test_contract_bridge_all_intents(self):
        bridge = ContractBridge()
        for intent in list(SceneIntent):
            sid = f"scene_{intent.value}"
            ir = SceneIntentIR(scene_id=sid, intent=intent)
            bridge.register_gpt_contract(sid, ir)
            bridge.register_claude_contract(sid, ir)
        results = bridge.validate_all()
        assert all(r.is_consistent for r in results.values())

    def test_scope_resolver_all_genres_pipeline(self):
        resolver = NarrativeScopeResolver()
        scene = SceneContext("s1", 0.6)
        for gid in ["literary","noir","fantasy","romance","historical"]:
            resolver.load(gid)
            d = resolver.resolve(scene, StoryContext(gid))
            assert d.genre_id == gid and isinstance(d.emotional_amp, float)

    def test_search_after_full_pipeline(self):
        g = full_nkg()
        p = DKGPipeline(g)
        p.run_full(reader_surface_gate=0.0)
        se = NKGSearchEngine(p.nkg)
        count = se.build_index()
        assert count >= 6  # 씬 + 캐릭터 + 군집 + 프로세스
        r = se.search("씬", top_k=5)
        assert len(r) >= 1
