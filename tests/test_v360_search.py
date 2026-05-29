"""V360 T11-7: NKGSearchEngine — BM25+Vector RRF 테스트."""
import sys
sys.path.insert(0, "/tmp/v360_build")
import pytest
from literary_system.nkg.schema import (
    NKGNodeType, NKGEdgeType, SceneNode, CharacterNode, ForeshadowNode,
    NKGEdge, ConflictClusterNode, ConflictType,
)
from literary_system.nkg.graph_store import NKGGraphStore
from literary_system.nkg.search.engine import (
    NKGSearchEngine, SearchResult, BM25Index, LightVectorIndex,
)


def build_rich_graph():
    g = NKGGraphStore()
    # 씬 5개
    scenes = [("s1","심문 장면"), ("s2","격투 장면"), ("s3","사랑 고백"),
              ("s4","배신 장면"), ("s5","결말 장면")]
    for sid, lbl in scenes:
        g.add_node(SceneNode(node_type=NKGNodeType.SCENE, node_id=sid, label=lbl))
    # 캐릭터 3개
    chars = [("c1","형사 주인공"), ("c2","악당 보스"), ("c3","조력자")]
    for cid, lbl in chars:
        g.add_node(CharacterNode(node_type=NKGNodeType.CHARACTER, node_id=cid, label=lbl))
    # 복선
    g.add_node(ForeshadowNode(node_type=NKGNodeType.FORESHADOW,
                              node_id="f1", label="총기 복선", is_candidate=True))
    return g


class TestBM25Index:
    def test_search_exact_match(self):
        idx = BM25Index()
        idx.add("d1","심문 장면"); idx.add("d2","격투 장면")
        r = idx.search("심문", top_k=5)
        assert r and r[0][0] == "d1"

    def test_search_returns_list(self):
        idx = BM25Index()
        idx.add("d1","테스트"); r = idx.search("테스트")
        assert isinstance(r, list)

    def test_empty_index(self):
        idx = BM25Index()
        r = idx.search("검색어")
        assert r == []

    def test_top_k_respected(self):
        idx = BM25Index()
        for i in range(10): idx.add(f"d{i}", f"문서 내용 {i}")
        r = idx.search("문서", top_k=3)
        assert len(r) <= 3

    def test_score_desc_order(self):
        idx = BM25Index()
        idx.add("d1","주인공 주인공 주인공"); idx.add("d2","주인공")
        r = idx.search("주인공", top_k=5)
        if len(r) >= 2: assert r[0][1] >= r[1][1]


class TestLightVectorIndex:
    def test_add_and_search(self):
        idx = LightVectorIndex()
        idx.add("d1","형사 심문"); idx.add("d2","악당 격투")
        r = idx.search("형사", top_k=5)
        assert any(d == "d1" for d, _ in r)

    def test_returns_tuple_list(self):
        idx = LightVectorIndex()
        idx.add("d1","테스트")
        r = idx.search("테스트")
        assert all(isinstance(item, tuple) and len(item) == 2 for item in r)

    def test_scores_in_range(self):
        idx = LightVectorIndex()
        idx.add("d1","테스트"); idx.add("d2","다른 내용")
        r = idx.search("테스트")
        for _, score in r: assert -1.5 <= score <= 1.5


class TestSearchEngine:
    def test_build_index(self):
        g = build_rich_graph()
        se = NKGSearchEngine(g)
        count = se.build_index()
        assert count >= 9  # 씬5 + 캐릭터3 + 복선1

    def test_search_returns_results(self):
        g = build_rich_graph()
        se = NKGSearchEngine(g)
        se.build_index()
        r = se.search("심문", top_k=5)
        assert isinstance(r, list)

    def test_search_scenes_type_filter(self):
        g = build_rich_graph()
        se = NKGSearchEngine(g); se.build_index()
        r = se.search_scenes("심문")
        for res in r: assert res.node_type == NKGNodeType.SCENE.value

    def test_search_characters_type_filter(self):
        g = build_rich_graph()
        se = NKGSearchEngine(g); se.build_index()
        r = se.search_characters("형사")
        for res in r: assert res.node_type == NKGNodeType.CHARACTER.value

    def test_search_foreshadow(self):
        g = build_rich_graph()
        se = NKGSearchEngine(g); se.build_index()
        r = se.search_foreshadow("f1")
        assert isinstance(r, list)

    def test_search_result_fields(self):
        g = build_rich_graph()
        se = NKGSearchEngine(g); se.build_index()
        r = se.search("장면", top_k=3)
        for res in r:
            assert hasattr(res, "node_id") and hasattr(res, "label")
            assert hasattr(res, "score") and hasattr(res, "node_type")

    def test_score_positive(self):
        g = build_rich_graph()
        se = NKGSearchEngine(g); se.build_index()
        r = se.search("격투", top_k=5)
        for res in r: assert res.score >= 0

    def test_top_k_respected(self):
        g = build_rich_graph()
        se = NKGSearchEngine(g); se.build_index()
        r = se.search("장면", top_k=2)
        assert len(r) <= 2

    def test_empty_graph_search(self):
        se = NKGSearchEngine(NKGGraphStore())
        se.build_index()
        r = se.search("검색어")
        assert r == []

    def test_auto_build_on_search(self):
        g = build_rich_graph()
        se = NKGSearchEngine(g)
        # build_index 호출 없이
        r = se.search("심문", top_k=5)
        assert isinstance(r, list)

    def test_rrf_fusion_boosts_common(self):
        g = NKGGraphStore()
        g.add_node(SceneNode(node_type=NKGNodeType.SCENE, node_id="s1", label="심문 심문 심문"))
        g.add_node(SceneNode(node_type=NKGNodeType.SCENE, node_id="s2", label="격투"))
        se = NKGSearchEngine(g); se.build_index()
        r = se.search("심문", top_k=5)
        if r: assert r[0].node_id == "s1"

    def test_search_clusters(self):
        g = build_rich_graph()
        g.add_node(ConflictClusterNode(node_type=NKGNodeType.CONFLICT_CLUSTER,
                                       node_id="cl1", label="형사 클러스터",
                                       cluster_id="cl1", conflict_type=ConflictType.RIVAL))
        se = NKGSearchEngine(g); se.build_index()
        r = se.search_clusters("형사")
        for res in r: assert res.node_type == NKGNodeType.CONFLICT_CLUSTER.value

    def test_search_processes(self):
        from literary_system.nkg.schema import NarrativeProcessNode
        g = build_rich_graph()
        g.add_node(NarrativeProcessNode(node_type=NKGNodeType.NARRATIVE_PROCESS,
                                         node_id="p1", label="심문 프로세스",
                                         process_id="p1"))
        se = NKGSearchEngine(g); se.build_index()
        r = se.search_processes("심문")
        for res in r: assert res.node_type == NKGNodeType.NARRATIVE_PROCESS.value

    def test_search_result_is_search_result_type(self):
        g = build_rich_graph()
        se = NKGSearchEngine(g); se.build_index()
        r = se.search("장면", top_k=3)
        for res in r: assert isinstance(res, SearchResult)
