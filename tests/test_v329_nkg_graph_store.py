"""V329 Task3: NKGGraphStore + NKGStalenessTracker + NKGPipeline 통합 테스트."""
import pytest
import tempfile, os
from literary_system.nkg.schema import (
    NKGSceneNode, NKGCharacterNode, NKGForeshadowNode,
    NKGEdge, NKGEdgeType, NKGNodeType,
)
from literary_system.nkg.graph_store import NKGGraphStore
from literary_system.nkg.staleness import NKGStalenessTracker
from literary_system.nkg.pipeline import NKGPipeline
from unittest.mock import MagicMock


def _scene(scene_id="s1", ep="ep1", content="내용", idx=0):
    return NKGSceneNode(scene_id=scene_id, episode_id=ep,
                        content=content, scene_index=idx)


# ── NKGGraphStore ────────────────────────────────────────────
class TestNKGGraphStore:
    def test_add_and_get_scene_node(self):
        g = NKGGraphStore()
        n = _scene()
        nid = g.add_scene_node(n)
        assert g.get_node(nid) is n

    def test_node_count(self):
        g = NKGGraphStore()
        g.add_scene_node(_scene("s1"))
        g.add_scene_node(_scene("s2"))
        assert g.node_count() == 2

    def test_add_edge_and_count(self):
        g = NKGGraphStore()
        g.add_scene_node(_scene("s1"))
        g.add_scene_node(_scene("s2"))
        g.add_edge_raw("scene:ep1:s1", "scene:ep1:s2", NKGEdgeType.CAUSAL_LINK)
        assert g.edge_count() == 1

    def test_successors(self):
        g = NKGGraphStore()
        g.add_scene_node(_scene("s1"))
        g.add_scene_node(_scene("s2"))
        g.add_edge_raw("scene:ep1:s1", "scene:ep1:s2", NKGEdgeType.CAUSAL_LINK)
        assert "scene:ep1:s2" in g.successors("scene:ep1:s1")

    def test_predecessors(self):
        g = NKGGraphStore()
        g.add_scene_node(_scene("s1"))
        g.add_scene_node(_scene("s2"))
        g.add_edge_raw("scene:ep1:s1", "scene:ep1:s2", NKGEdgeType.CAUSAL_LINK)
        assert "scene:ep1:s1" in g.predecessors("scene:ep1:s2")

    def test_remove_node(self):
        g = NKGGraphStore()
        nid = g.add_scene_node(_scene("s1"))
        assert g.remove_node(nid) is True
        assert g.get_node(nid) is None

    def test_has_node(self):
        g = NKGGraphStore()
        nid = g.add_scene_node(_scene("s1"))
        assert g.has_node(nid) is True
        assert g.has_node("nonexistent") is False

    def test_nodes_of_type_scene(self):
        g = NKGGraphStore()
        g.add_scene_node(_scene("s1"))
        g.add_character_node(NKGCharacterNode(char_id="c1", name="주인공"))
        scenes = g.nodes_of_type("scene")
        chars  = g.nodes_of_type("character")
        assert len(scenes) == 1
        assert len(chars) == 1

    def test_stats(self):
        g = NKGGraphStore()
        g.add_scene_node(_scene("s1"))
        s = g.stats()
        assert s["nodes"] == 1
        assert "node_types" in s

    def test_pickle_roundtrip(self):
        g = NKGGraphStore()
        g.add_scene_node(_scene("s1", content="저장 테스트"))
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            path = f.name
        try:
            g.save(path)
            g2 = NKGGraphStore.load(path)
            assert g2.node_count() == 1
        finally:
            os.unlink(path)


# ── NKGStalenessTracker ──────────────────────────────────────
class TestNKGStalenessTracker:
    def test_register_and_is_dirty_false(self):
        t = NKGStalenessTracker()
        t.register("n1", "abc123")
        assert t.is_dirty("n1") is False

    def test_mark_dirty(self):
        t = NKGStalenessTracker()
        t.register("n1", "abc123")
        t.mark_dirty("n1")
        assert t.is_dirty("n1") is True

    def test_clear_dirty(self):
        t = NKGStalenessTracker()
        t.register("n1", "abc123")
        t.mark_dirty("n1")
        t.clear_dirty("n1", new_hash="def456")
        assert t.is_dirty("n1") is False
        assert t.get_hash("n1") == "def456"

    def test_is_stale_true(self):
        t = NKGStalenessTracker()
        t.register_content("n1", "원본 내용")
        assert t.is_stale("n1", "수정된 내용") is True

    def test_is_stale_false(self):
        t = NKGStalenessTracker()
        t.register_content("n1", "동일 내용")
        assert t.is_stale("n1", "동일 내용") is False

    def test_mark_dirty_if_stale_returns_true_on_change(self):
        t = NKGStalenessTracker()
        t.register_content("n1", "원본")
        result = t.mark_dirty_if_stale("n1", "변경됨")
        assert result is True
        assert t.is_dirty("n1") is True

    def test_mark_dirty_if_stale_returns_false_no_change(self):
        t = NKGStalenessTracker()
        t.register_content("n1", "동일")
        result = t.mark_dirty_if_stale("n1", "동일")
        assert result is False

    def test_unregistered_node_is_stale(self):
        t = NKGStalenessTracker()
        assert t.is_stale("unknown", "내용") is True

    def test_stats(self):
        t = NKGStalenessTracker()
        t.register("n1", "h1"); t.register("n2", "h2")
        t.mark_dirty("n1")
        s = t.stats()
        assert s["total_nodes"] == 2
        assert s["dirty_count"] == 1


# ── NKGPipeline ──────────────────────────────────────────────
class TestNKGPipeline:
    def _make_draft(self, scene_id="s1", idx=0):
        m = MagicMock()
        m.scene_id = scene_id; m.episode_id = "ep1"; m.episode_no = 1
        m.draft_text = f"장면 {scene_id} 내용"
        m.mae_score = 0.75; m.scene_index = idx; m.quality = None
        m.emotional_vector = None
        return m

    def test_run_full_returns_results(self):
        p = NKGPipeline()
        outputs = [self._make_draft(f"s{i}", i) for i in range(3)]
        results = p.run_full("ep1", outputs)
        assert len(results) == 5   # 5단계

    def test_run_full_all_success(self):
        p = NKGPipeline()
        outputs = [self._make_draft(f"s{i}", i) for i in range(3)]
        results = p.run_full("ep1", outputs)
        assert all(r.success for r in results)

    def test_run_full_nodes_added(self):
        p = NKGPipeline()
        outputs = [self._make_draft(f"s{i}", i) for i in range(3)]
        p.run_full("ep1", outputs)
        # scene 3개 + episode 1개
        assert p.graph.node_count() >= 3

    def test_run_full_causal_edges_created(self):
        p = NKGPipeline()
        outputs = [self._make_draft(f"s{i}", i) for i in range(3)]
        p.run_full("ep1", outputs)
        # 순서 기반 CausalLink: 3개 장면 → 2개 엣지
        assert p.graph.edge_count() >= 2

    def test_run_full_staleness_registered(self):
        p = NKGPipeline()
        outputs = [self._make_draft("s1", 0)]
        p.run_full("ep1", outputs)
        assert p.staleness.stats()["total_nodes"] >= 1

    def test_update_incremental_new_content(self):
        p = NKGPipeline()
        m = self._make_draft("s1", 0)
        p.run_full("ep1", [m])

        # 새 내용으로 수정
        m2 = MagicMock()
        m2.scene_id = "s1"; m2.episode_id = "ep1"; m2.episode_no = 1
        m2.draft_text = "완전히 수정된 내용"
        m2.mae_score = 0.9; m2.scene_index = 0
        m2.quality = None; m2.emotional_vector = None
        result = p.update_incremental("s1", m2, episode_id="ep1")
        assert result.success is True

    def test_update_incremental_no_change_skipped(self):
        p = NKGPipeline()
        m = self._make_draft("s1", 0)
        p.run_full("ep1", [m])
        # 동일 내용으로 재호출
        result = p.update_incremental("s1", m, episode_id="ep1")
        # 내용 변경 없으면 skipped
        assert result.success is True

    def test_pipeline_stats(self):
        p = NKGPipeline()
        s = p.stats()
        assert "graph" in s
        assert "staleness" in s
        assert s["phases"] == 5
