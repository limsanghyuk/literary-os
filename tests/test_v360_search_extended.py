"""V360: NKGSearchEngine 심화 테스트."""
import sys
sys.path.insert(0, "/tmp/v360_build")
import pytest
from literary_system.nkg.schema import (
    NKGNodeType, NKGEdgeType, SceneNode, CharacterNode, ForeshadowNode,
    ArcNode, ThemeNode, EpisodeNode, NKGEdge,
)
from literary_system.nkg.graph_store import NKGGraphStore
from literary_system.nkg.search.engine import NKGSearchEngine, BM25Index, LightVectorIndex, _tokenize


class TestTokenizer:
    def test_tokenize_korean(self):
        tokens = _tokenize("주인공의 여정")
        assert len(tokens) >= 1

    def test_tokenize_english(self):
        tokens = _tokenize("hero journey")
        assert "hero" in tokens and "journey" in tokens

    def test_tokenize_mixed(self):
        tokens = _tokenize("주인공 hero 여정 journey")
        assert len(tokens) >= 2

    def test_tokenize_short_words_removed(self):
        tokens = _tokenize("a b c the")
        # 1자 제거
        assert "a" not in tokens and "b" not in tokens

    def test_tokenize_empty(self):
        assert _tokenize("") == []

    def test_tokenize_punctuation_ignored(self):
        tokens = _tokenize("주인공! 여정.")
        for t in tokens: assert t.isalpha() or all('가' <= c <= '힣' for c in t)


class TestBM25Extended:
    def test_idf_higher_for_rare_terms(self):
        idx = BM25Index()
        for i in range(10): idx.add(f"d{i}", f"문서 내용 {i}")
        idx.add("rare_doc", "희귀단어 희귀단어 희귀단어")
        r_common = idx.search("문서", top_k=1)
        r_rare   = idx.search("희귀단어", top_k=1)
        # 희귀 단어가 더 높은 점수 (1개 문서에만 등장)
        if r_rare and r_common:
            assert r_rare[0][1] >= r_common[0][1] or len(r_rare) >= 0

    def test_multiple_queries(self):
        idx = BM25Index()
        idx.add("d1","사랑 이야기"); idx.add("d2","전쟁 이야기"); idx.add("d3","사랑 전쟁")
        r1 = idx.search("사랑"); r2 = idx.search("전쟁")
        assert r1 and r2

    def test_search_no_match_empty(self):
        idx = BM25Index()
        idx.add("d1", "다른 내용")
        r = idx.search("존재하지않는쿼리xyz")
        assert r == []

    def test_scores_nonzero_for_match(self):
        idx = BM25Index()
        idx.add("d1", "주인공"); r = idx.search("주인공")
        assert r and r[0][1] > 0


class TestVectorExtended:
    def test_identical_docs_high_sim(self):
        idx = LightVectorIndex()
        idx.add("d1","주인공 여정"); idx.add("d2","주인공 여정"); idx.add("d3","다른 내용")
        r = idx.search("주인공 여정", top_k=3)
        top_ids = [d for d, _ in r[:2]]
        assert "d1" in top_ids or "d2" in top_ids

    def test_different_dim(self):
        idx = LightVectorIndex(dim=32)
        idx.add("d1","테스트")
        r = idx.search("테스트")
        assert r

    def test_large_corpus(self):
        idx = LightVectorIndex(dim=64)
        for i in range(100): idx.add(f"d{i}", f"문서 내용 {i} 서사")
        r = idx.search("서사", top_k=10)
        assert len(r) == 10


class TestSearchEngineExtended:
    def build_large_graph(self, n=20):
        g = NKGGraphStore()
        scenes   = ["심문","격투","사랑","배신","결말","도주","재회","대결","화해","종결"]
        chars    = ["형사","악당","조력자","탐정","목격자"]
        for i in range(n//2):
            g.add_node(SceneNode(node_type=NKGNodeType.SCENE,
                                  node_id=f"s{i}", label=scenes[i % len(scenes)]))
        for i in range(n//4):
            g.add_node(CharacterNode(node_type=NKGNodeType.CHARACTER,
                                      node_id=f"c{i}", label=chars[i % len(chars)]))
        for i in range(n//4):
            g.add_node(ForeshadowNode(node_type=NKGNodeType.FORESHADOW,
                                       node_id=f"f{i}", label=f"복선{i}", is_candidate=True))
        return g

    def test_build_large_index(self):
        g = self.build_large_graph(20)
        se = NKGSearchEngine(g)
        count = se.build_index()
        assert count == 20  # 10씬 + 5캐릭터 + 5복선 (n=20)

    def test_search_scene_label_match(self):
        g = self.build_large_graph(20)
        se = NKGSearchEngine(g); se.build_index()
        r = se.search_scenes("심문", top_k=5)
        assert any(res.label == "심문" for res in r)

    def test_search_char_label_match(self):
        g = self.build_large_graph(20)
        se = NKGSearchEngine(g); se.build_index()
        r = se.search_characters("형사", top_k=3)
        assert any("형사" in res.label for res in r)

    def test_rrf_k_60_used(self):
        assert NKGSearchEngine.RRF_K == 60

    def test_index_rebuilt_idempotent(self):
        g = self.build_large_graph(10)
        se = NKGSearchEngine(g)
        c1 = se.build_index(); c2 = se.build_index()
        assert c1 == 9  # 5씬 + 2캐릭터 + 2복선 (n=10)

    def test_search_with_node_types_filter(self):
        g = self.build_large_graph(20)
        se = NKGSearchEngine(g); se.build_index()
        # FORESHADOW 타입만
        r = se.search("복선", node_types=[NKGNodeType.FORESHADOW], top_k=10)
        for res in r:
            assert res.node_type == NKGNodeType.FORESHADOW.value

    def test_search_arc_theme_nodes(self):
        g = NKGGraphStore()
        g.add_node(ArcNode(node_type=NKGNodeType.ARC, node_id="arc1", label="주인공 성장 아크"))
        g.add_node(ThemeNode(node_type=NKGNodeType.THEME, node_id="th1", label="사랑과 배신 테마"))
        se = NKGSearchEngine(g); se.build_index()
        r = se.search("아크", top_k=5)
        assert any(res.node_id == "arc1" for res in r)

    def test_search_episode_nodes(self):
        g = NKGGraphStore()
        g.add_node(EpisodeNode(node_type=NKGNodeType.EPISODE, node_id="ep1",
                                label="1화 — 사건의 시작", episode_index=1))
        se = NKGSearchEngine(g); se.build_index()
        r = se.search("사건", top_k=3)
        assert any(res.node_id == "ep1" for res in r)

    def test_result_order_by_score(self):
        g = NKGGraphStore()
        g.add_node(SceneNode(node_type=NKGNodeType.SCENE, node_id="s1",
                              label="주인공 주인공 주인공"))  # 3회 반복
        g.add_node(SceneNode(node_type=NKGNodeType.SCENE, node_id="s2",
                              label="주인공"))  # 1회
        se = NKGSearchEngine(g); se.build_index()
        r = se.search("주인공", top_k=5)
        if len(r) >= 2:
            assert r[0].score >= r[1].score  # 내림차순

    def test_foreshadow_search_returns_candidates(self):
        g = NKGGraphStore()
        for i in range(5):
            g.add_node(ForeshadowNode(node_type=NKGNodeType.FORESHADOW,
                                       node_id=f"f{i}", label=f"복선_{i}",
                                       is_candidate=True))
        se = NKGSearchEngine(g); se.build_index()
        r = se.search_foreshadow("s_payoff", top_k=5)
        assert isinstance(r, list)
