"""V360 T11-6: NKGSemanticModel — 3단계 상태 머신 테스트."""
import sys
sys.path.insert(0, "/tmp/v360_build")
import pytest
from literary_system.nkg.schema import (
    NKGNodeType, NKGEdgeType, CharacterNode, SceneNode, NKGEdge,
    SemanticModelState,
)
from literary_system.nkg.graph_store import NKGGraphStore
from literary_system.nkg.semantic_model import (
    NKGSemanticModel, ReconcileReport,
    SemanticModelFrozenError, SemanticModelNotFrozenError,
)
from literary_system.nkg.change_detector import NKGChangeDetector, ChangeDetectionResult


def make_graph_with_chars(labels):
    import time
    g = NKGGraphStore()
    for i, lbl in enumerate(labels):
        g.add_node(CharacterNode(node_type=NKGNodeType.CHARACTER,
                                  node_id=f"c{i}", label=lbl,
                                  created_at=time.time() + i))
    return g

def make_scene_graph(n=4):
    g = NKGGraphStore()
    for i in range(n):
        g.add_node(SceneNode(node_type=NKGNodeType.SCENE, node_id=f"s{i}", label=f"씬{i}"))
    return g


class TestInitialState:
    def test_initial_write_state(self):
        m = NKGSemanticModel(NKGGraphStore())
        assert m.state == SemanticModelState.WRITE

    def test_not_frozen_initially(self):
        m = NKGSemanticModel(NKGGraphStore())
        assert not m.is_frozen()

    def test_assert_frozen_raises_when_write(self):
        m = NKGSemanticModel(NKGGraphStore())
        with pytest.raises(SemanticModelNotFrozenError):
            m.assert_frozen()


class TestReconcile:
    def test_reconcile_returns_report(self):
        g = make_graph_with_chars(["주인공","조력자"])
        m = NKGSemanticModel(g)
        r = m.reconcile()
        assert isinstance(r, ReconcileReport)

    def test_reconcile_changes_state(self):
        g = NKGGraphStore()
        m = NKGSemanticModel(g)
        m.reconcile()
        assert m.state == SemanticModelState.RECONCILE

    def test_duplicate_chars_merged(self):
        import time
        g = NKGGraphStore()
        g.add_node(CharacterNode(node_type=NKGNodeType.CHARACTER,
                                  node_id="c0", label="주인공", created_at=1.0))
        g.add_node(CharacterNode(node_type=NKGNodeType.CHARACTER,
                                  node_id="c1", label="주인공", created_at=2.0))
        m = NKGSemanticModel(g)
        r = m.reconcile()
        assert len(r.merged_nodes) == 1
        assert g.get_node("c0") is not None  # keeper
        assert g.get_node("c1") is None     # removed

    def test_no_duplicates_no_merge(self):
        g = make_graph_with_chars(["A","B","C"])
        m = NKGSemanticModel(g)
        r = m.reconcile()
        assert len(r.merged_nodes) == 0

    def test_duration_ms_present(self):
        g = NKGGraphStore()
        m = NKGSemanticModel(g)
        r = m.reconcile()
        assert r.duration_ms >= 0

    def test_reconcile_on_frozen_raises(self):
        g = NKGGraphStore()
        m = NKGSemanticModel(g)
        m.reconcile(); m.freeze()
        with pytest.raises(SemanticModelFrozenError):
            m.reconcile()


class TestFreeze:
    def test_freeze_changes_state(self):
        g = NKGGraphStore()
        m = NKGSemanticModel(g)
        m.reconcile(); m.freeze()
        assert m.state == SemanticModelState.FROZEN

    def test_freeze_returns_snapshot(self):
        g = make_scene_graph(3)
        m = NKGSemanticModel(g)
        m.reconcile()
        snap = m.freeze()
        assert isinstance(snap, dict) and "frozen_at" in snap

    def test_is_frozen_after_freeze(self):
        m = NKGSemanticModel(NKGGraphStore())
        m.reconcile(); m.freeze()
        assert m.is_frozen()

    def test_assert_frozen_ok_after_freeze(self):
        m = NKGSemanticModel(NKGGraphStore())
        m.reconcile(); m.freeze()
        m.assert_frozen()  # 예외 없음

    def test_snapshot_has_node_count(self):
        g = make_scene_graph(3)
        m = NKGSemanticModel(g)
        m.reconcile()
        snap = m.freeze()
        assert "node_count" in snap and snap["node_count"] == 3

    def test_freeze_without_reconcile_ok(self):
        g = NKGGraphStore()
        m = NKGSemanticModel(g)
        snap = m.freeze()
        assert m.is_frozen()


class TestGuardWrite:
    def test_guard_write_ok_when_not_frozen(self):
        m = NKGSemanticModel(NKGGraphStore())
        m.guard_write("test")  # 예외 없음

    def test_guard_write_raises_when_frozen(self):
        m = NKGSemanticModel(NKGGraphStore())
        m.reconcile(); m.freeze()
        with pytest.raises(SemanticModelFrozenError):
            m.guard_write("forbidden op")


class TestChangeDetector:
    def test_snapshot_all_returns_count(self):
        g = make_scene_graph(4)
        det = NKGChangeDetector(g)
        assert det.snapshot_all() == 4

    def test_scan_no_changes(self):
        g = make_scene_graph(3)
        det = NKGChangeDetector(g)
        det.snapshot_all()
        r = det.scan_changes()
        assert isinstance(r, ChangeDetectionResult)
        assert len(r.changed_ids) == 0

    def test_scan_detects_new(self):
        g = make_scene_graph(3)
        det = NKGChangeDetector(g)
        det.snapshot_all()
        g.add_node(SceneNode(node_type=NKGNodeType.SCENE, node_id="s_new", label="신규씬"))
        r = det.scan_changes(["s_new"])
        assert "s_new" in r.new_ids

    def test_rename_dry_run(self):
        g = make_scene_graph(2)
        g.add_edge(NKGEdge("s0","s1", NKGEdgeType.CAUSAL_LINK, weight=1.0, confidence=1.0))
        det = NKGChangeDetector(g)
        result = det.rename_dry_run("s0","s0_renamed")
        assert result["old_id"] == "s0"
        assert result["new_id"] == "s0_renamed"
        assert result["affected_edges"] >= 1
        assert result["safe"] is True

    def test_rename_dry_run_no_edges(self):
        g = make_scene_graph(2)
        det = NKGChangeDetector(g)
        result = det.rename_dry_run("s0","s0_new")
        assert result["affected_edges"] == 0

    def test_duration_ms(self):
        g = make_scene_graph(3)
        det = NKGChangeDetector(g)
        det.snapshot_all()
        r = det.scan_changes()
        assert r.duration_ms >= 0
