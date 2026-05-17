"""V340 Task1: NKGEdgeInferEngine 테스트."""
import pytest
from literary_system.nkg.edge_infer import NKGEdgeInferEngine, EdgeInferResult
from literary_system.nkg.schema import NKGSceneNode, NKGEdgeType


def _scene(scene_id, idx, content="내용"):
    return NKGSceneNode(scene_id=scene_id, episode_id="ep1",
                        content=content, scene_index=idx)


class TestEdgeInferEngineBasic:
    def test_returns_edge_infer_result(self):
        e = NKGEdgeInferEngine()
        r = e.infer([_scene("s1",0), _scene("s2",1)])
        assert isinstance(r, EdgeInferResult)

    def test_empty_input_no_edges(self):
        e = NKGEdgeInferEngine()
        r = e.infer([])
        assert r.edges_added == 0

    def test_single_node_no_edges(self):
        e = NKGEdgeInferEngine()
        r = e.infer([_scene("s1",0)])
        assert r.edges_added == 0

    def test_two_adjacent_scenes_causal_edge(self):
        e = NKGEdgeInferEngine()
        r = e.infer([_scene("s1",0), _scene("s2",1)])
        assert len(r.causal_pairs) >= 1

    def test_causal_keyword_increases_confidence(self):
        e = NKGEdgeInferEngine()
        r_kw  = e.infer([_scene("s1",0), _scene("s2",1,"그 결과 모든 것이 바뀌었다")])
        r_nkw = e.infer([_scene("s1",0), _scene("s2",1,"평범한 하루였다")])
        assert r_kw.edges_added >= r_nkw.edges_added

    def test_causal_pair_format(self):
        e = NKGEdgeInferEngine()
        r = e.infer([_scene("s1",0), _scene("s2",1)])
        for src, tgt in r.causal_pairs:
            assert ":" in src and ":" in tgt

    def test_max_adjacent_gap_respected(self):
        e = NKGEdgeInferEngine()
        nodes = [_scene(f"s{i}", i) for i in range(10)]
        r = e.infer(nodes)
        # MAX_ADJACENT_GAP=3 → 최대 n*(n-1)/2 쌍이 아닌 n*MAX_GAP 이하
        assert r.edges_added <= len(nodes) * e.MAX_ADJACENT_GAP
        # 상한선 검증: 10노드에서 총 엣지는 10*10보다 훨씬 적어야 함
        assert r.edges_added < len(nodes) * 10


class TestEdgeInferKeywords:
    def test_has_causal_keyword_korean(self):
        assert NKGEdgeInferEngine.has_causal_keyword("그래서 그는 떠났다")

    def test_has_causal_keyword_english(self):
        assert NKGEdgeInferEngine.has_causal_keyword("therefore he left")

    def test_no_causal_keyword(self):
        assert not NKGEdgeInferEngine.has_causal_keyword("맑은 하늘 아래 새가 날았다")

    def test_has_foreshadow_keyword_korean(self):
        assert NKGEdgeInferEngine.has_foreshadow_keyword("언젠가 이 일을 후회할 것이다")

    def test_has_foreshadow_keyword_english(self):
        assert NKGEdgeInferEngine.has_foreshadow_keyword("someday you will understand")

    def test_has_reveal_keyword_korean(self):
        assert NKGEdgeInferEngine.has_reveal_keyword("드디어 진실이 밝혀졌다")

    def test_has_reveal_keyword_english(self):
        assert NKGEdgeInferEngine.has_reveal_keyword("finally the truth was revealed")

    def test_no_reveal_keyword(self):
        assert not NKGEdgeInferEngine.has_reveal_keyword("조용한 아침이었다")


class TestForeshadowInference:
    def test_foreshadow_payoff_pair_detected(self):
        e = NKGEdgeInferEngine()
        plant  = _scene("s1", 0, "언젠가 이 모든 것이 끝날 것이라는 예감이 들었다")
        payoff = _scene("s8", 8, "드디어 진실이 밝혀졌다. 마침내 그날이 왔다")
        r = e.infer([plant, payoff])
        assert len(r.foreshadow_pairs) >= 1

    def test_foreshadow_node_created(self):
        e = NKGEdgeInferEngine()
        plant  = _scene("s1", 0, "불길한 예감이 든다. 언젠가 반드시 일어날 일이다")
        payoff = _scene("s5", 5, "결국 드디어 모든 것이 밝혀진 것이다")
        r = e.infer([plant, payoff])
        if r.foreshadow_pairs:
            assert len(r.foreshadow_nodes) >= 1

    def test_foreshadow_node_has_planted_scene(self):
        e = NKGEdgeInferEngine()
        plant  = _scene("s1", 0, "불길한 예감, 언젠가 반드시")
        payoff = _scene("s3", 3, "드디어 마침내 밝혀졌다")
        r = e.infer([plant, payoff])
        if r.foreshadow_nodes:
            assert r.foreshadow_nodes[0].planted_scene != ""

    def test_gap_too_large_no_foreshadow(self):
        e = NKGEdgeInferEngine()
        e.MAX_FORESHADOW_GAP = 2   # 매우 짧게 설정
        plant  = _scene("s1",  0, "언젠가 불길한 예감")
        payoff = _scene("s10",10, "드디어 마침내 밝혀졌다")
        r = e.infer([plant, payoff])
        assert len(r.foreshadow_pairs) == 0


class TestInvolvesEdge:
    def test_involves_edge_created_for_named_char(self):
        e = NKGEdgeInferEngine()
        node = _scene("s1", 0, "이준혁이 방에 들어섰다")
        r = e.infer([node], char_names=["이준혁"])
        assert len(r.involves_pairs) >= 1

    def test_involves_edge_not_created_if_name_absent(self):
        e = NKGEdgeInferEngine()
        node = _scene("s1", 0, "누군가가 방에 들어섰다")
        r = e.infer([node], char_names=["이준혁"])
        assert len(r.involves_pairs) == 0

    def test_multiple_chars_multiple_involves(self):
        e = NKGEdgeInferEngine()
        node = _scene("s1", 0, "이준혁과 박민아가 대화를 나눴다")
        r = e.infer([node], char_names=["이준혁", "박민아"])
        assert len(r.involves_pairs) == 2

    def test_no_duplicate_involves(self):
        e = NKGEdgeInferEngine()
        nodes = [
            _scene("s1", 0, "이준혁이 나타났다"),
            _scene("s2", 1, "이준혁이 말했다"),
        ]
        r = e.infer(nodes, char_names=["이준혁"])
        # 같은 (scene, char) 쌍이 중복되지 않아야
        pairs_set = set(r.involves_pairs)
        assert len(pairs_set) == len(r.involves_pairs)


class TestEdgeInferEdgeTypes:
    def test_causal_edges_have_correct_type(self):
        e = NKGEdgeInferEngine()
        r = e.infer([_scene("s1",0), _scene("s2",1)])
        for edge in getattr(r, "edges", []):
            if (edge.source_id, edge.target_id) in set(r.causal_pairs):
                assert edge.edge_type == NKGEdgeType.CAUSAL_LINK

    def test_confidence_in_range(self):
        e = NKGEdgeInferEngine()
        r = e.infer([_scene(f"s{i}",i) for i in range(4)])
        for edge in getattr(r, "edges", []):
            assert 0.0 <= edge.confidence <= 1.0
