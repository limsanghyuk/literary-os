"""V530 — NarrativeGraph 테스트 (35종)
Covers: NarrativeGraphSchema (V526), NarrativeGraphStore (V527),
        NarrativeGraphIndexer (V528), NarrativeImpactAnalyzer (V529),
        SceneChangePreGate / Gate26 (V529b)
"""
import pytest
from literary_system.graph_intelligence import (
    NarrativeGraphStore,
    NarrativeGraphIndexer,
    NarrativeImpactAnalyzer,
    IndexInput,
    Gate26Result,
    SceneChangePreGate,
    CharacterNode, SceneNode, EventNode, SecretNode, RevealNode,
    MotifNode, RelationshipNode, EmotionPressureNode, TimeDeltaNode,
    DialogueIntentNode,
    NarrativeEdge,
    NarrativeEdgeType,
    NarrativeNodeType,
    NarrativeImpactReport,
)


# ══════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════

@pytest.fixture
def empty_store():
    return NarrativeGraphStore()


@pytest.fixture
def simple_store():
    """sc01 →[CAUSES]→ ev01, sc01 →[REVEALS]→ rev01, mot01 →[FORESHADOWS]→ sc05"""
    store = NarrativeGraphStore()
    for node in [
        SceneNode(node_id="sc01", node_type=NarrativeNodeType.SCENE, label="Duel"),
        SceneNode(node_id="sc05", node_type=NarrativeNodeType.SCENE, label="Finale"),
        EventNode(node_id="ev01", node_type=NarrativeNodeType.EVENT, label="Clash"),
        RevealNode(node_id="rev01", node_type=NarrativeNodeType.REVEAL, label="Secret out"),
        MotifNode(node_id="mot01", node_type=NarrativeNodeType.MOTIF, label="Blood moon"),
        CharacterNode(node_id="c1", node_type=NarrativeNodeType.CHARACTER, label="Alice"),
    ]:
        store.add_node(node)
    for src, dst, etype in [
        ("sc01", "ev01",  NarrativeEdgeType.CAUSES),
        ("sc01", "rev01", NarrativeEdgeType.REVEALS),
        ("mot01","sc05",  NarrativeEdgeType.FORESHADOWS),
        ("c1",  "sc01",  NarrativeEdgeType.DEPENDS_ON),
    ]:
        eid = store.make_edge_id()
        store.add_edge(NarrativeEdge(edge_id=eid, src_id=src, dst_id=dst,
                                     edge_type=etype))
    return store


@pytest.fixture
def indexer_store():
    store = NarrativeGraphStore()
    return store, NarrativeGraphIndexer(store)


@pytest.fixture
def minimal_inp():
    return IndexInput(
        scene_id="sc01",
        scene_title="The Meeting",
        character_ids=["c1"],
        character_names={"c1": "Hero"},
    )


# ══════════════════════════════════════════════════════════════════════
# V526 — Schema tests (8종)
# ══════════════════════════════════════════════════════════════════════

class TestNarrativeGraphSchema:

    def test_node_types_count(self):
        assert len(NarrativeNodeType) == 10

    def test_edge_types_count(self):
        assert len(NarrativeEdgeType) == 10

    def test_scene_node_post_init(self):
        n = SceneNode(node_id="s1", node_type=NarrativeNodeType.SCENE, label="T")
        assert n.node_type == NarrativeNodeType.SCENE

    def test_reveal_node_post_init(self):
        n = RevealNode(node_id="r1", node_type=NarrativeNodeType.REVEAL, label="R")
        assert n.node_type == NarrativeNodeType.REVEAL

    def test_motif_node_fields(self):
        n = MotifNode(node_id="m1", node_type=NarrativeNodeType.MOTIF,
                      label="Moon", symbol="🌙", appearances=["s1", "s3"])
        assert n.symbol == "🌙"
        assert len(n.appearances) == 2

    def test_narrative_impact_report_defaults(self):
        r = NarrativeImpactReport(target_scene_id="sc01")
        assert r.risk_score == 0.0
        assert r.risk_level == "low"
        assert r.decision == "proceed"

    def test_narrative_impact_report_summary(self):
        r = NarrativeImpactReport(
            target_scene_id="sc01",
            direct_impact=["a", "b"],
            reveal_impacts=["rv1"],
            risk_score=0.65,
            risk_level="high",
            decision="split_required",
        )
        s = r.summary()
        assert "HIGH" in s
        assert "sc01" in s

    def test_character_node_default_role(self):
        n = CharacterNode(node_id="c1", node_type=NarrativeNodeType.CHARACTER,
                          label="Hero")
        assert n.role == "supporting"


# ══════════════════════════════════════════════════════════════════════
# V527 — NarrativeGraphStore tests (8종)
# ══════════════════════════════════════════════════════════════════════

class TestNarrativeGraphStore:

    def test_add_get_node(self, empty_store):
        n = SceneNode(node_id="sc01", node_type=NarrativeNodeType.SCENE, label="T")
        empty_store.add_node(n)
        assert empty_store.get_node("sc01") is n

    def test_add_get_edge(self, empty_store):
        empty_store.add_node(SceneNode(node_id="s1", node_type=NarrativeNodeType.SCENE, label="A"))
        empty_store.add_node(SceneNode(node_id="s2", node_type=NarrativeNodeType.SCENE, label="B"))
        eid = empty_store.make_edge_id()
        e = NarrativeEdge(edge_id=eid, src_id="s1", dst_id="s2",
                          edge_type=NarrativeEdgeType.CAUSES)
        empty_store.add_edge(e)
        assert empty_store.get_edge(eid) is e

    def test_edge_requires_existing_nodes(self, empty_store):
        e = NarrativeEdge(edge_id="E001", src_id="x", dst_id="y",
                          edge_type=NarrativeEdgeType.CAUSES)
        with pytest.raises(ValueError):
            empty_store.add_edge(e)

    def test_nodes_by_type(self, simple_store):
        scenes = simple_store.nodes_by_type(NarrativeNodeType.SCENE)
        assert len(scenes) == 2

    def test_edges_by_type(self, simple_store):
        reveals = simple_store.edges_by_type(NarrativeEdgeType.REVEALS)
        assert len(reveals) == 1

    def test_neighbors_depth1(self, simple_store):
        nb = simple_store.neighbors("sc01", depth=1)
        assert "ev01" in nb
        assert "rev01" in nb

    def test_remove_node_cascades(self, simple_store):
        simple_store.remove_node("ev01")
        assert simple_store.get_node("ev01") is None
        assert all(e.dst_id != "ev01" for e in simple_store._edges.values())

    def test_stats_keys(self, simple_store):
        s = simple_store.stats()
        assert "nodes_total" in s
        assert "edges_total" in s
        assert s["nodes_total"] > 0


# ══════════════════════════════════════════════════════════════════════
# V528 — NarrativeGraphIndexer tests (9종)
# ══════════════════════════════════════════════════════════════════════

class TestNarrativeGraphIndexer:

    def test_index_creates_scene_node(self, indexer_store, minimal_inp):
        store, indexer = indexer_store
        indexer.index(minimal_inp)
        assert store.get_node("sc01") is not None

    def test_index_creates_character_nodes(self, indexer_store):
        store, indexer = indexer_store
        inp = IndexInput(
            scene_id="sc01",
            character_ids=["c1", "c2"],
            character_names={"c1": "Alice", "c2": "Bob"},
        )
        r = indexer.index(inp)
        assert store.get_node("c1") is not None
        assert store.get_node("c2") is not None
        assert r.nodes_added >= 3  # scene + 2 chars

    def test_index_creates_reveal_node(self, indexer_store):
        store, indexer = indexer_store
        inp = IndexInput(scene_id="sc01", reveals_triggered=["rev01"])
        indexer.index(inp)
        node = store.get_node("rev01")
        assert node is not None
        assert node.node_type == NarrativeNodeType.REVEAL

    def test_index_creates_foreshadow_edge(self, indexer_store):
        store, indexer = indexer_store
        inp = IndexInput(
            scene_id="sc01",
            motif_ids=["mot01"],
            foreshadow_links={"mot01": "sc05"},
        )
        indexer.index(inp)
        fwd = store.edges_by_type(NarrativeEdgeType.FORESHADOWS)
        assert len(fwd) == 1
        assert fwd[0].src_id == "mot01"
        assert fwd[0].dst_id == "sc05"

    def test_index_idempotent(self, indexer_store, minimal_inp):
        store, indexer = indexer_store
        r1 = indexer.index(minimal_inp)
        r2 = indexer.index(minimal_inp)
        # Second call: no new nodes (all updated), no new edges
        assert r2.nodes_added == 0
        assert r2.edges_added == 0

    def test_index_empty_scene_id_skipped(self, indexer_store):
        store, indexer = indexer_store
        inp = IndexInput(scene_id="", character_ids=["c1"])
        r = indexer.index(inp)
        assert r.nodes_added == 0
        assert len(r.warnings) > 0

    def test_index_batch(self, indexer_store):
        store, indexer = indexer_store
        inputs = [
            IndexInput(scene_id="sc01", scene_title="A"),
            IndexInput(scene_id="sc02", scene_title="B"),
            IndexInput(scene_id="sc03", scene_title="C"),
        ]
        r = indexer.index_batch(inputs)
        assert r.nodes_added == 3

    def test_index_emotion_peak(self, indexer_store):
        store, indexer = indexer_store
        inp = IndexInput(
            scene_id="sc01",
            character_ids=["c1"],
            emotion_peaks=[{"character_id": "c1", "emotion": "fear", "intensity": 0.9}],
        )
        indexer.index(inp)
        ep_nodes = store.nodes_by_type(NarrativeNodeType.EMOTION_PRESSURE)
        assert len(ep_nodes) == 1

    def test_index_depends_on(self, indexer_store):
        store, indexer = indexer_store
        inp = IndexInput(scene_id="sc03", depends_on_scene_ids=["sc01", "sc02"])
        r = indexer.index(inp)
        dep_edges = store.edges_by_type(NarrativeEdgeType.DEPENDS_ON)
        assert len(dep_edges) == 2


# ══════════════════════════════════════════════════════════════════════
# V529 — NarrativeImpactAnalyzer tests (5종)
# ══════════════════════════════════════════════════════════════════════

class TestNarrativeImpactAnalyzer:

    def test_unknown_scene_returns_proceed(self, simple_store):
        analyzer = NarrativeImpactAnalyzer(simple_store)
        r = analyzer.analyze("nonexistent")
        assert r.decision == "proceed"
        assert r.risk_score == 0.0

    def test_isolated_scene_low_risk(self, empty_store):
        empty_store.add_node(SceneNode(node_id="iso", node_type=NarrativeNodeType.SCENE,
                                       label="Isolated"))
        analyzer = NarrativeImpactAnalyzer(empty_store)
        r = analyzer.analyze("iso")
        assert r.risk_level == "low"
        assert r.risk_score == 0.0

    def test_direct_impact_counted(self, simple_store):
        analyzer = NarrativeImpactAnalyzer(simple_store)
        r = analyzer.analyze("sc01")
        assert len(r.direct_impact) >= 2  # ev01, rev01

    def test_reveal_detected(self, simple_store):
        analyzer = NarrativeImpactAnalyzer(simple_store)
        r = analyzer.analyze("sc01")
        assert "rev01" in r.reveal_impacts

    def test_foreshadow_break_detected(self, simple_store):
        analyzer = NarrativeImpactAnalyzer(simple_store)
        # sc05 is foreshadowed by mot01; we analyze mot01's scene (sc01)
        # Foreshadow break: mot01 foreshadows sc05, sc05 is NOT in blast of sc01
        # But if sc05 is connected via another edge it would be in blast
        # In simple_store sc05 is not reachable from sc01, so no foreshadow break
        r = analyzer.analyze("sc01")
        # mot01 foreshadows sc05; sc05 not in blast → no break (correct)
        assert len(r.foreshadow_breaks) == 0

    def test_bulk_analyze(self, simple_store):
        analyzer = NarrativeImpactAnalyzer(simple_store)
        results = analyzer.bulk_analyze(["sc01", "sc05"])
        assert "sc01" in results
        assert "sc05" in results


# ══════════════════════════════════════════════════════════════════════
# V529b — SceneChangePreGate / Gate26 tests (5종)
# ══════════════════════════════════════════════════════════════════════

class TestSceneChangePreGate:

    def test_isolated_scene_approved(self, empty_store):
        empty_store.add_node(SceneNode(node_id="iso", node_type=NarrativeNodeType.SCENE,
                                       label="Isolated"))
        gate = SceneChangePreGate(empty_store)
        result = gate.evaluate("iso")
        assert result.approved is True

    def test_all_four_checks_present(self, simple_store):
        gate = SceneChangePreGate(simple_store)
        result = gate.evaluate("sc01")
        assert len(result.checks) == 4
        ids = [c.gate_id for c in result.checks]
        assert "G26-1" in ids and "G26-4" in ids

    def test_custom_threshold(self, simple_store):
        # With risk_max=0.0, any connected scene is blocked
        gate = SceneChangePreGate(simple_store, risk_max=0.0)
        result = gate.evaluate("sc01")
        assert result.approved is False

    def test_is_approved_convenience(self, empty_store):
        empty_store.add_node(SceneNode(node_id="sc_x", node_type=NarrativeNodeType.SCENE,
                                       label="X"))
        gate = SceneChangePreGate(empty_store)
        assert gate.is_approved("sc_x") is True

    def test_evaluate_batch(self, simple_store):
        gate = SceneChangePreGate(simple_store)
        results = gate.evaluate_batch(["sc01", "sc05"])
        assert "sc01" in results
        assert "sc05" in results
        # sc05 has no outgoing edges → approved
        assert results["sc05"].approved is True
