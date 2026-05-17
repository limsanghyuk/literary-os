"""V401 — NKGSemanticAdapter 테스트 (15 tests)"""
import pytest
from literary_system.nkg.graph_store import NKGGraphStore
from literary_system.nkg.schema import NKGNodeType, NKGSceneNode
from literary_system.nkg.adapters.nkg_semantic_adapter import NKGSemanticAdapter, _simple_tokenize


def _make_scene_node(nkg, node_id, label):
    node = NKGSceneNode(node_type=NKGNodeType.SCENE, node_id=node_id, label=label)
    nkg.add_node(node)
    return node


class TestNKGSemanticAdapterBasic:
    def test_import(self):
        assert NKGSemanticAdapter is not None

    def test_empty_nkg_not_ready(self):
        nkg = NKGGraphStore()
        adapter = NKGSemanticAdapter(nkg)
        assert adapter.is_ready() is False

    def test_empty_nkg_score_zero(self):
        nkg = NKGGraphStore()
        adapter = NKGSemanticAdapter(nkg)
        assert adapter.score("형사 수사", "살인 사건") == 0.0

    def test_ready_after_node_added(self):
        nkg = NKGGraphStore()
        adapter = NKGSemanticAdapter(nkg)
        _make_scene_node(nkg, "s1", "형사 수사 씬")
        assert adapter.is_ready() is True

    def test_score_returns_float(self):
        nkg = NKGGraphStore()
        _make_scene_node(nkg, "s1", "형사 수사 씬")
        adapter = NKGSemanticAdapter(nkg)
        result = adapter.score("형사 수사", "살인 사건")
        assert isinstance(result, float)

    def test_score_in_range(self):
        nkg = NKGGraphStore()
        _make_scene_node(nkg, "s1", "형사 수사 씬")
        _make_scene_node(nkg, "s2", "탐정 단서 발견")
        adapter = NKGSemanticAdapter(nkg)
        s = adapter.score("형사 수사 단서", "형사 수사")
        assert 0.0 <= s <= 1.0

    def test_rebuild_index(self):
        nkg = NKGGraphStore()
        _make_scene_node(nkg, "s1", "씬1")
        adapter = NKGSemanticAdapter(nkg)
        count = adapter.rebuild_index()
        assert count >= 1

    def test_engine_lazy_init(self):
        nkg = NKGGraphStore()
        _make_scene_node(nkg, "s1", "씬1")
        adapter = NKGSemanticAdapter(nkg)
        assert adapter._engine is None
        adapter.score("test", "goal")
        assert adapter._engine is not None


class TestNKGSemanticAdapterScoring:
    def setup_method(self):
        self.nkg = NKGGraphStore()
        _make_scene_node(self.nkg, "s1", "형사 살인 사건 수사")
        _make_scene_node(self.nkg, "s2", "탐정 단서 발견 현장")
        _make_scene_node(self.nkg, "s3", "용의자 심문 경찰서")
        self.adapter = NKGSemanticAdapter(self.nkg)

    def test_multiple_nodes_score(self):
        s = self.adapter.score("형사 수사", "살인 수사")
        assert 0.0 <= s <= 1.0

    def test_empty_texts_score_safely(self):
        s = self.adapter.score("", "")
        assert isinstance(s, float)

    def test_no_crash_on_empty_query(self):
        s = self.adapter.score("node text", "")
        assert isinstance(s, float)


class TestSimpleTokenize:
    def test_korean_tokenize(self):
        tokens = _simple_tokenize("형사 살인사건 수사")
        assert "형사" in tokens
        assert "수사" in tokens

    def test_english_tokenize(self):
        tokens = _simple_tokenize("detective murder case")
        assert "detective" in tokens

    def test_short_tokens_filtered(self):
        tokens = _simple_tokenize("a 형사 b")
        assert "a" not in tokens
        assert "b" not in tokens
        assert "형사" in tokens
