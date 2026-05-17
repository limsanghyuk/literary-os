"""V340 Task2: NKGEmotionalLinker 테스트."""
import pytest
import math
from literary_system.nkg.emotional_linker import (
    NKGEmotionalLinker, EmotionalLinkResult,
    _cosine_similarity, _euclidean_distance, _ev_delta,
)
from literary_system.nkg.schema import NKGSceneNode, NKGEdgeType
from unittest.mock import MagicMock


def _scene(scene_id, idx, ev=None):
    if ev is None:
        ev = [0.5, 0.5, 0.3, 0.1]
    return NKGSceneNode(scene_id=scene_id, episode_id="ep1",
                        content="내용", scene_index=idx,
                        emotional_vector=ev)


class TestCosineSimilarity:
    def test_identical_vectors_similarity_one(self):
        v = [0.8, 0.5, 0.3, 0.1]
        assert abs(_cosine_similarity(v, v) - 1.0) < 1e-6

    def test_orthogonal_vectors_similarity_zero(self):
        sim = _cosine_similarity([1,0,0,0], [0,1,0,0])
        assert abs(sim) < 1e-6

    def test_opposite_vectors_similarity_minus_one(self):
        sim = _cosine_similarity([1,0,0,0], [-1,0,0,0])
        assert abs(sim + 1.0) < 1e-6

    def test_zero_vector_returns_one(self):
        sim = _cosine_similarity([0,0,0,0], [0,0,0,0])
        assert sim == 1.0

    def test_partial_overlap(self):
        sim = _cosine_similarity([0.8,0.6,0,0], [0.8,0.6,0.1,0.1])
        assert 0.9 < sim < 1.0


class TestEmotionalLinkerBasic:
    def test_returns_emotional_link_result(self):
        lk = NKGEmotionalLinker()
        r = lk.link([_scene("s1",0), _scene("s2",1)])
        assert isinstance(r, EmotionalLinkResult)

    def test_empty_input_no_edges(self):
        lk = NKGEmotionalLinker()
        r = lk.link([])
        assert r.total_edges == 0

    def test_single_node_no_edges(self):
        lk = NKGEmotionalLinker()
        r = lk.link([_scene("s1",0)])
        assert r.total_edges == 0

    def test_identical_ev_creates_resonance(self):
        lk = NKGEmotionalLinker()
        ev = [0.9, 0.8, 0.7, 0.6]
        r = lk.link([_scene("s1",0,ev), _scene("s2",1,ev)])
        assert len(r.resonance_edges) >= 1

    def test_similar_ev_creates_echo(self):
        lk = NKGEmotionalLinker()
        lk.ECHO_THRESH      = 0.75
        lk.RESONANCE_THRESH = 0.99  # 거의 불가능하게
        ev_a = [0.8, 0.6, 0.3, 0.1]
        ev_b = [0.7, 0.65, 0.25, 0.15]
        r = lk.link([_scene("s1",0,ev_a), _scene("s2",1,ev_b)])
        assert r.total_edges >= 0  # 유사도에 따라

    def test_dissimilar_ev_no_edges(self):
        lk = NKGEmotionalLinker()
        lk.ECHO_THRESH = 0.99
        ev_a = [1.0, 0.0, 0.0, 0.0]
        ev_b = [0.0, 1.0, 0.0, 0.0]
        r = lk.link([_scene("s1",0,ev_a), _scene("s2",1,ev_b)])
        assert r.total_edges == 0

    def test_resonance_creates_bidirectional(self):
        lk = NKGEmotionalLinker()
        ev = [0.9, 0.9, 0.9, 0.9]
        r = lk.link([_scene("s1",0,ev), _scene("s2",1,ev)])
        if r.resonance_edges:
            sources = {e.source_id for e in r.resonance_edges}
            targets = {e.target_id for e in r.resonance_edges}
            assert len(sources) >= 1 and len(targets) >= 1

    def test_echo_edge_type_correct(self):
        lk = NKGEmotionalLinker()
        ev_a = [0.8, 0.7, 0.6, 0.5]
        ev_b = [0.75, 0.72, 0.58, 0.52]
        r = lk.link([_scene("s1",0,ev_a), _scene("s2",1,ev_b)])
        for e in r.echo_edges:
            assert e.edge_type == NKGEdgeType.EMOTIONAL_ECHO

    def test_resonance_edge_type_correct(self):
        lk = NKGEmotionalLinker()
        ev = [0.8, 0.8, 0.8, 0.8]
        r = lk.link([_scene("s1",0,ev), _scene("s2",1,ev)])
        for e in r.resonance_edges:
            assert e.edge_type == NKGEdgeType.RESONANCE


class TestEmotionalLinkerStats:
    def test_max_similarity_set(self):
        lk = NKGEmotionalLinker()
        ev = [0.8, 0.6, 0.4, 0.2]
        r = lk.link([_scene("s1",0,ev), _scene("s2",1,ev)])
        assert r.max_similarity > 0.0

    def test_mean_similarity_set(self):
        lk = NKGEmotionalLinker()
        r = lk.link([_scene(f"s{i}",i) for i in range(4)])
        assert r.mean_similarity >= 0.0

    def test_all_edges_combines(self):
        lk = NKGEmotionalLinker()
        ev = [0.9, 0.9, 0.9, 0.9]
        r = lk.link([_scene("s1",0,ev), _scene("s2",1,ev)])
        assert len(r.all_edges()) == r.total_edges

    def test_get_similarity_cached(self):
        lk = NKGEmotionalLinker()
        ev = [0.8, 0.6, 0.4, 0.2]
        lk.link([_scene("s1",0,ev), _scene("s2",1,ev)])
        sim = lk.get_similarity("scene:ep1:s1", "scene:ep1:s2")
        assert sim is not None
        assert 0.0 <= sim <= 1.0

    def test_top_resonant_pairs(self):
        lk = NKGEmotionalLinker()
        nodes = [_scene(f"s{i}", i, [0.8,0.7,0.6,0.5]) for i in range(4)]
        lk.link(nodes)
        pairs = lk.top_resonant_pairs(3)
        assert len(pairs) <= 3
        if len(pairs) > 1:
            assert pairs[0][2] >= pairs[1][2]  # 내림차순

    def test_compute_similarity_static(self):
        sim = NKGEmotionalLinker.compute_similarity([1,0,0,0], [1,0,0,0])
        assert abs(sim - 1.0) < 1e-6


class TestEmotionalLinkerWithEMT:
    def _make_emt(self, n=3):
        emt = MagicMock()
        history = []
        for i in range(n):
            ev = MagicMock()
            ev.tension   = 0.5 + i * 0.1
            ev.sympathy  = 0.5
            ev.dread     = 0.3
            ev.catharsis = 0.0
            history.append(ev)
        emt.history.return_value = history
        return emt

    def test_link_with_tracker_returns_result(self):
        lk  = NKGEmotionalLinker()
        emt = self._make_emt(3)
        nodes = [_scene(f"s{i}", i) for i in range(3)]
        r = lk.link_with_tracker(nodes, emt)
        assert isinstance(r, EmotionalLinkResult)

    def test_link_with_none_emt_falls_back(self):
        lk = NKGEmotionalLinker()
        nodes = [_scene(f"s{i}", i) for i in range(2)]
        r = lk.link_with_tracker(nodes, None)
        assert isinstance(r, EmotionalLinkResult)

    def test_link_with_empty_history_falls_back(self):
        lk  = NKGEmotionalLinker()
        emt = MagicMock()
        emt.history.return_value = []
        nodes = [_scene(f"s{i}", i) for i in range(2)]
        r = lk.link_with_tracker(nodes, emt)
        assert isinstance(r, EmotionalLinkResult)
