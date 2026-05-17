"""V328 Task13: SceneGraphQueryEngine 테스트."""
import sys; sys.path.insert(0,"/tmp/literary_os_v328")
import pytest
from literary_system.retrieval.scene_graph_query_engine import SceneGraphQueryEngine, GraphDoc

class TestGraphDoc:
    def test_defaults(self):
        d = GraphDoc()
        assert d.relevance == 0.0
        assert d.node_type == ""

    def test_fields(self):
        d = GraphDoc(node_id="n1", node_type="character", text="홍길동", relevance=0.9)
        assert d.node_id == "n1"

class TestSceneGraphQueryEngine:
    def test_no_store_returns_empty(self):
        e = SceneGraphQueryEngine()
        docs = e.query(["A","B"], "목표")
        assert docs == []

    def test_with_mock_store(self):
        class MockStore:
            def get_node(self, name):
                return f"node:{name}"
            def get_edges(self, a, b):
                return [{"edge":f"{a}-{b}"}]
        e = SceneGraphQueryEngine(relation_store=MockStore())
        docs = e.query(["A","B"], "목표", top_k=5)
        assert len(docs) >= 1
        assert any(d.node_type == "character" for d in docs)

    def test_top_k_respected(self):
        class MockStore:
            def get_node(self, name): return f"node:{name}"
            def get_edges(self, a, b): return []
        e = SceneGraphQueryEngine(relation_store=MockStore())
        docs = e.query(["A","B","C","D"], "목표", top_k=2)
        assert len(docs) <= 2

    def test_to_retrieved_docs(self):
        docs = [GraphDoc(node_id="n1",node_type="character",text="홍길동",relevance=0.8)]
        strs = SceneGraphQueryEngine.to_retrieved_docs(docs)
        assert isinstance(strs, list)
        assert "GraphRAG" in strs[0]
        assert "홍길동" in strs[0]

    def test_store_exception_returns_partial(self):
        class BrokenStore:
            def get_node(self, name): raise RuntimeError("fail")
            def get_edges(self, a, b): return []
        e = SceneGraphQueryEngine(relation_store=BrokenStore())
        docs = e.query(["A"], "목표")
        assert isinstance(docs, list)

    def test_empty_characters(self):
        e = SceneGraphQueryEngine()
        docs = e.query([], "목표")
        assert docs == []
