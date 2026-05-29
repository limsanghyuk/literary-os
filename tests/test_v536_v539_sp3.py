"""V536~V539 SP3 테스트 (28종)
Covers: NILGraphBridge (V536), SceneBlastRadiusReport (V537),
        NILGraphOrchestrator (V538~V539)
"""
import pytest
from literary_system.graph_intelligence.sp3 import (
    NILGraphBridge, NILGraphBridgeConfig,
    SceneBlastRadiusReport, BlastRadiusReportBuilder,
    NILGraphOrchestrator, NILGraphResult,
)
from literary_system.graph_intelligence import NarrativeGraphStore
from literary_system.graph_intelligence.narrative_graph_indexer import NarrativeGraphIndexer
from literary_system.graph_intelligence.sp2 import (
    CodeDependencyGraph, SceneProfile, SceneDependencyKey, PatchType,
)
from literary_system.nie.nil_orchestrator import NILOrchestrator, SceneInput


# ══════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════

@pytest.fixture
def empty_store():
    return NarrativeGraphStore()


@pytest.fixture
def simple_cdg():
    cdg = CodeDependencyGraph()
    for sid, chars, loc in [
        ("sc01", frozenset(["c1","c2"]), "palace"),
        ("sc02", frozenset(["c1"]),      "palace"),
        ("sc03", frozenset(["c3"]),      "dungeon"),
    ]:
        cdg.register(SceneProfile(
            key=SceneDependencyKey(episode=1, scene_id=sid),
            character_ids=chars,
            location_id=loc,
        ))
    cdg.build()
    return cdg


@pytest.fixture
def nil_bridge(empty_store):
    indexer = NarrativeGraphIndexer(empty_store)
    return NILGraphBridge(indexer), empty_store


@pytest.fixture
def nil_scene():
    return SceneInput(
        scene_id="sc01", episode_idx=0, total_scenes=10,
        metrics={"tension": 0.8, "sympathy": 0.5},
        char_updates=[("c1","c2", 0.3)],
    )


@pytest.fixture
def nil_orch_instance():
    return NILOrchestrator()


@pytest.fixture
def orchestrator(nil_orch_instance, empty_store, simple_cdg):
    return NILGraphOrchestrator(nil_orch_instance, empty_store, simple_cdg)


# ══════════════════════════════════════════════════════════════════════
# V536 — NILGraphBridge (10종)
# ══════════════════════════════════════════════════════════════════════

class TestNILGraphBridge:

    def test_ingest_adds_scene_node(self, nil_bridge, nil_scene):
        bridge, store = nil_bridge
        nil_result = NILOrchestrator().process_scene(nil_scene)
        result = bridge.ingest(nil_result, nil_scene)
        assert store.get_node("sc01") is not None
        assert result.nodes_added > 0

    def test_ingest_adds_character_nodes(self, nil_bridge, nil_scene):
        bridge, store = nil_bridge
        nil_result = NILOrchestrator().process_scene(nil_scene)
        bridge.ingest(nil_result, nil_scene)
        # c1, c2 should be present
        assert store.get_node("c1") is not None
        assert store.get_node("c2") is not None

    def test_ingest_idempotent(self, nil_bridge, nil_scene):
        bridge, store = nil_bridge
        nil_result = NILOrchestrator().process_scene(nil_scene)
        r1 = bridge.ingest(nil_result, nil_scene)
        r2 = bridge.ingest(nil_result, nil_scene)
        assert r2.nodes_added == 0
        assert r2.edges_added == 0

    def test_high_tension_creates_emotion_peak(self, nil_bridge):
        bridge, store = nil_bridge
        scene = SceneInput(
            scene_id="sc_t", episode_idx=0, total_scenes=5,
            metrics={"tension": 0.9},
            char_updates=[("cA","cB",0.1)],
        )
        nil_result = NILOrchestrator().process_scene(scene)
        bridge.ingest(nil_result, scene)
        from literary_system.graph_intelligence.narrative_graph_schema import NarrativeNodeType
        ep_nodes = store.nodes_by_type(NarrativeNodeType.EMOTION_PRESSURE)
        assert len(ep_nodes) > 0

    def test_low_tension_no_emotion_peak(self, nil_bridge):
        bridge, store = nil_bridge
        scene = SceneInput(
            scene_id="sc_low", episode_idx=0, total_scenes=5,
            metrics={"tension": 0.1},
        )
        nil_result = NILOrchestrator().process_scene(scene)
        bridge.ingest(nil_result, scene)
        from literary_system.graph_intelligence.narrative_graph_schema import NarrativeNodeType
        ep_nodes = store.nodes_by_type(NarrativeNodeType.EMOTION_PRESSURE)
        assert len(ep_nodes) == 0

    def test_time_delta_node_created(self, nil_bridge, nil_scene):
        bridge, store = nil_bridge
        nil_result = NILOrchestrator().process_scene(nil_scene)
        bridge.ingest(nil_result, nil_scene)
        from literary_system.graph_intelligence.narrative_graph_schema import NarrativeNodeType
        td_nodes = store.nodes_by_type(NarrativeNodeType.TIME_DELTA)
        assert len(td_nodes) > 0

    def test_no_time_delta_when_disabled(self, empty_store, nil_scene):
        indexer = NarrativeGraphIndexer(empty_store)
        bridge  = NILGraphBridge(indexer, NILGraphBridgeConfig(record_time_delta=False))
        nil_result = NILOrchestrator().process_scene(nil_scene)
        bridge.ingest(nil_result, nil_scene)
        from literary_system.graph_intelligence.narrative_graph_schema import NarrativeNodeType
        td_nodes = empty_store.nodes_by_type(NarrativeNodeType.TIME_DELTA)
        assert len(td_nodes) == 0

    def test_ingest_batch(self, nil_bridge):
        bridge, store = nil_bridge
        scenes = [
            SceneInput(scene_id=f"sc{i:02d}", episode_idx=i,
                       total_scenes=3, metrics={"tension": 0.5})
            for i in range(3)
        ]
        pairs = [(NILOrchestrator().process_scene(s), s) for s in scenes]
        result = bridge.ingest_batch(pairs)
        assert result.nodes_added >= 3  # at least 3 scene nodes

    def test_relationship_node_from_char_updates(self, nil_bridge, nil_scene):
        bridge, store = nil_bridge
        nil_result = NILOrchestrator().process_scene(nil_scene)
        bridge.ingest(nil_result, nil_scene)
        from literary_system.graph_intelligence.narrative_graph_schema import NarrativeNodeType
        rel_nodes = store.nodes_by_type(NarrativeNodeType.RELATIONSHIP)
        assert len(rel_nodes) >= 1

    def test_rag_intent_creates_dialogue_intent(self, nil_bridge):
        bridge, store = nil_bridge
        scene = SceneInput(
            scene_id="sc_di", episode_idx=0, total_scenes=5,
            metrics={"tension": 0.4},
        )
        from unittest.mock import MagicMock
        nil_result = NILOrchestrator().process_scene(scene)
        nil_result.step6_rag_intent = "deception"
        bridge.ingest(nil_result, scene)
        from literary_system.graph_intelligence.narrative_graph_schema import NarrativeNodeType
        di_nodes = store.nodes_by_type(NarrativeNodeType.DIALOGUE_INTENT)
        assert len(di_nodes) >= 1


# ══════════════════════════════════════════════════════════════════════
# V537 — SceneBlastRadiusReport (8종)
# ══════════════════════════════════════════════════════════════════════

class TestSceneBlastRadiusReport:

    def test_build_returns_report(self, empty_store, simple_cdg):
        builder = BlastRadiusReportBuilder(empty_store, simple_cdg)
        report  = builder.build("sc01")
        assert isinstance(report, SceneBlastRadiusReport)

    def test_unknown_scene_low_risk(self, empty_store, simple_cdg):
        builder = BlastRadiusReportBuilder(empty_store, simple_cdg)
        report  = builder.build("nonexistent")
        assert report.combined_risk == 0.0 or report.risk_level in {"low"}

    def test_coupled_scene_in_affected(self, empty_store, simple_cdg):
        # Index sc01 into store first
        indexer = NarrativeGraphIndexer(empty_store)
        bridge  = NILGraphBridge(indexer)
        scene = SceneInput(scene_id="sc01", episode_idx=0, total_scenes=3,
                           metrics={"tension":0.5}, char_updates=[("c1","c2",0.1)])
        nil_result = NILOrchestrator().process_scene(scene)
        bridge.ingest(nil_result, scene)

        builder = BlastRadiusReportBuilder(empty_store, simple_cdg)
        report  = builder.build("sc01")
        # sc02 is coupled via shared character + location
        assert "sc02" in report.affected_scenes or report.top_coupled

    def test_to_dict_keys(self, empty_store, simple_cdg):
        builder = BlastRadiusReportBuilder(empty_store, simple_cdg)
        report  = builder.build("sc01")
        d = report.to_dict()
        assert "combined_risk" in d and "recommendation" in d

    def test_summary_contains_scene_id(self, empty_store, simple_cdg):
        builder = BlastRadiusReportBuilder(empty_store, simple_cdg)
        report  = builder.build("sc01")
        assert "sc01" in report.summary()

    def test_delete_higher_risk_than_edit(self, empty_store, simple_cdg):
        # Index sc01
        indexer = NarrativeGraphIndexer(empty_store)
        bridge  = NILGraphBridge(indexer)
        scene = SceneInput(scene_id="sc01", episode_idx=0, total_scenes=3,
                           metrics={"tension":0.5}, char_updates=[("c1","c2",0.1)])
        nil_result = NILOrchestrator().process_scene(scene)
        bridge.ingest(nil_result, scene)

        builder = BlastRadiusReportBuilder(empty_store, simple_cdg)
        edit_r   = builder.build("sc01", PatchType.EDIT)
        delete_r = builder.build("sc01", PatchType.DELETE)
        assert delete_r.combined_risk >= edit_r.combined_risk

    def test_build_batch(self, empty_store, simple_cdg):
        builder = BlastRadiusReportBuilder(empty_store, simple_cdg)
        results = builder.build_batch(["sc01","sc03"])
        assert "sc01" in results and "sc03" in results

    def test_risk_levels_valid(self, empty_store, simple_cdg):
        builder = BlastRadiusReportBuilder(empty_store, simple_cdg)
        report  = builder.build("sc01")
        assert report.risk_level in {"low","medium","high","critical"}


# ══════════════════════════════════════════════════════════════════════
# V538~V539 — NILGraphOrchestrator (10종)
# ══════════════════════════════════════════════════════════════════════

class TestNILGraphOrchestrator:

    def test_process_scene_returns_result(self, orchestrator, nil_scene):
        result = orchestrator.process_scene(nil_scene)
        assert isinstance(result, NILGraphResult)
        assert result.scene_id == "sc01"

    def test_process_scene_populates_graph(self, orchestrator, nil_scene):
        orchestrator.process_scene(nil_scene)
        assert orchestrator.store.get_node("sc01") is not None

    def test_index_result_attached(self, orchestrator, nil_scene):
        result = orchestrator.process_scene(nil_scene)
        assert result.index_result.nodes_added > 0

    def test_blast_report_attached_on_look_ahead(self, orchestrator, nil_scene):
        result = orchestrator.process_scene(nil_scene)
        assert result.blast_report is not None

    def test_no_blast_report_when_disabled(self, nil_orch_instance, empty_store, simple_cdg, nil_scene):
        orch = NILGraphOrchestrator(nil_orch_instance, empty_store, simple_cdg, look_ahead=False)
        result = orch.process_scene(nil_scene)
        assert result.blast_report is None

    def test_history_grows(self, orchestrator):
        for i in range(3):
            scene = SceneInput(scene_id=f"sc{i:02d}", episode_idx=i,
                               total_scenes=3, metrics={"tension": 0.5})
            orchestrator.process_scene(scene)
        assert len(orchestrator.history) == 3

    def test_process_episode(self, orchestrator):
        scenes = [
            SceneInput(scene_id=f"ep{i}", episode_idx=i,
                       total_scenes=3, metrics={"tension": 0.4})
            for i in range(3)
        ]
        results = orchestrator.process_episode(scenes)
        assert len(results) == 3

    def test_blast_radius_query(self, orchestrator, nil_scene):
        orchestrator.process_scene(nil_scene)
        report = orchestrator.blast_radius("sc01")
        assert isinstance(report, SceneBlastRadiusReport)

    def test_without_code_dep(self, nil_orch_instance, empty_store):
        orch = NILGraphOrchestrator(nil_orch_instance, empty_store)
        scene = SceneInput(scene_id="s1", episode_idx=0, total_scenes=1,
                           metrics={"tension": 0.3})
        result = orch.process_scene(scene)
        assert result.scene_id == "s1"

    def test_complete_episode_delegated(self, orchestrator, nil_scene):
        orchestrator.process_scene(nil_scene)
        # Should not raise
        orchestrator.complete_episode()
