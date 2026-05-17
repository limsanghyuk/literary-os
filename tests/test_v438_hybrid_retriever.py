"""
V438 tests -- HybridRetriever (BM25 + Dense + RRF + CrossEncoder)
"""
import pytest
from literary_system.rag.hybrid_retriever import (
    Document, RankedResult,
    BM25Retriever, DenseRetriever, RRFMerger,
    CrossEncoderReRanker, HybridRetriever,
)
from literary_system.rag.qdrant_bridge import (
    QdrantBridge, EmbeddingService, TenantIsolation,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_docs():
    return [
        Document("d1", "the cat sat on the mat", {"topic": "animals"}),
        Document("d2", "dogs are loyal companions to humans", {"topic": "animals"}),
        Document("d3", "machine learning transforms data into insight", {"topic": "tech"}),
        Document("d4", "neural networks learn from examples", {"topic": "tech"}),
        Document("d5", "the cat and dog played together happily", {"topic": "animals"}),
    ]


def make_bridge():
    svc = EmbeddingService(provider="mock")
    tenant = TenantIsolation()
    return QdrantBridge(host="localhost", port=6333, tenant=tenant, embedding_svc=svc, fallback=True)


# ---------------------------------------------------------------------------
# TestDocument
# ---------------------------------------------------------------------------

class TestDocument:
    def test_fields(self):
        d = Document("id1", "hello world", {"k": "v"})
        assert d.doc_id == "id1"
        assert d.text == "hello world"
        assert d.metadata["k"] == "v"

    def test_default_metadata(self):
        d = Document("id2", "text")
        assert d.metadata == {}


# ---------------------------------------------------------------------------
# TestBM25Retriever
# ---------------------------------------------------------------------------

class TestBM25Retriever:
    def test_empty_index(self):
        b = BM25Retriever()
        assert b.doc_count == 0
        assert b.search("cat") == []

    def test_single_doc(self):
        b = BM25Retriever()
        b.index(Document("d1", "cat sat on mat"))
        hits = b.search("cat")
        assert len(hits) == 1
        assert hits[0][0] == "d1"
        assert hits[0][1] > 0

    def test_multi_doc_ranking(self):
        b = BM25Retriever()
        b.index(Document("d1", "cat cat cat"))
        b.index(Document("d2", "cat dog bird"))
        hits = b.search("cat", top_k=2)
        assert hits[0][0] == "d1"  # higher TF

    def test_top_k_limit(self):
        b = BM25Retriever()
        b.index_batch(make_docs())
        hits = b.search("cat", top_k=2)
        assert len(hits) <= 2

    def test_no_match_returns_empty(self):
        b = BM25Retriever()
        b.index(Document("d1", "cat sat on mat"))
        hits = b.search("zzzyyyxxx")
        assert hits == []

    def test_batch_index(self):
        b = BM25Retriever()
        b.index_batch(make_docs())
        assert b.doc_count == 5

    def test_korean_tokenize(self):
        b = BM25Retriever()
        b.index(Document("k1", "고양이 방석 위에 앉다"))
        hits = b.search("고양이")
        assert hits[0][0] == "k1"


# ---------------------------------------------------------------------------
# TestRRFMerger
# ---------------------------------------------------------------------------

class TestRRFMerger:
    def test_single_list(self):
        m = RRFMerger(k=60)
        lst = [("d1", 1.0), ("d2", 0.8)]
        fused = m.merge([lst])
        ids = [x[0] for x in fused]
        assert ids == ["d1", "d2"]

    def test_two_lists_agree(self):
        m = RRFMerger(k=60)
        a = [("d1", 1.0), ("d2", 0.5)]
        b = [("d1", 0.9), ("d2", 0.4)]
        fused = m.merge([a, b])
        assert fused[0][0] == "d1"

    def test_two_lists_disagree_boost(self):
        m = RRFMerger(k=60)
        # d1 rank1 in list A, rank2 in list B
        # d2 rank2 in list A, rank1 in list B
        a = [("d1", 1.0), ("d2", 0.5)]
        b = [("d2", 1.0), ("d1", 0.5)]
        fused = m.merge([a, b])
        # Both appear in both lists -- scores should be equal
        assert fused[0][1] == pytest.approx(fused[1][1], abs=1e-9)

    def test_empty_lists(self):
        m = RRFMerger()
        assert m.merge([]) == []

    def test_weighted_merge(self):
        m = RRFMerger(k=60)
        a = [("d1", 1.0)]
        b = [("d2", 1.0)]
        fused = m.merge([a, b], weights=[2.0, 1.0])
        assert fused[0][0] == "d1"  # higher weight

    def test_scores_positive(self):
        m = RRFMerger()
        lst = [("d1", 0.9), ("d2", 0.7), ("d3", 0.5)]
        fused = m.merge([lst])
        for _, score in fused:
            assert score > 0


# ---------------------------------------------------------------------------
# TestCrossEncoderReRanker
# ---------------------------------------------------------------------------

class TestCrossEncoderReRanker:
    def test_mock_provider(self):
        r = CrossEncoderReRanker(provider="mock")
        candidates = [("d1", "cat sat on mat", 0.8), ("d2", "dog and cat", 0.6)]
        result = r.rerank("cat", candidates)
        assert len(result) == 2
        ids = [x[0] for x in result]
        assert "d1" in ids and "d2" in ids

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError):
            CrossEncoderReRanker(provider="unknown")

    def test_empty_candidates(self):
        r = CrossEncoderReRanker(provider="mock")
        assert r.rerank("query", []) == []

    def test_top_k_limit(self):
        r = CrossEncoderReRanker(provider="mock")
        candidates = [(f"d{i}", f"text {i}", 0.5) for i in range(10)]
        result = r.rerank("text", candidates, top_k=3)
        assert len(result) == 3

    def test_sorted_desc(self):
        r = CrossEncoderReRanker(provider="mock")
        candidates = [
            ("d1", "cat cat cat", 0.9),
            ("d2", "dog", 0.1),
        ]
        result = r.rerank("cat", candidates)
        assert result[0][1] >= result[1][1]

    def test_deterministic(self):
        r = CrossEncoderReRanker(provider="mock")
        c = [("d1", "hello world query", 0.5)]
        r1 = r.rerank("hello query", c)
        r2 = r.rerank("hello query", c)
        assert r1[0][1] == pytest.approx(r2[0][1])


# ---------------------------------------------------------------------------
# TestHybridRetriever
# ---------------------------------------------------------------------------

class TestHybridRetriever:
    def _make(self, use_reranker=True):
        bm25 = BM25Retriever()
        dense = DenseRetriever(make_bridge(), collection="test")
        reranker = CrossEncoderReRanker(provider="mock") if use_reranker else None
        return HybridRetriever(bm25, dense, reranker=reranker)

    def test_index_and_count(self):
        h = self._make()
        h.index_batch(make_docs())
        assert h.indexed_count == 5

    def test_search_returns_results(self):
        h = self._make()
        h.index_batch(make_docs())
        results = h.search("cat", top_k=3)
        assert len(results) <= 3
        assert all(isinstance(r, RankedResult) for r in results)

    def test_search_ranks_ascending(self):
        h = self._make()
        h.index_batch(make_docs())
        results = h.search("cat", top_k=5)
        ranks = [r.rank for r in results]
        assert ranks == list(range(1, len(ranks) + 1))

    def test_search_scores_desc(self):
        h = self._make()
        h.index_batch(make_docs())
        results = h.search("cat", top_k=5)
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score

    def test_no_reranker(self):
        h = self._make(use_reranker=False)
        h.index_batch(make_docs())
        results = h.search("machine learning", top_k=3, use_rerank=False)
        assert isinstance(results, list)

    def test_source_label(self):
        h = self._make()
        h.index_batch(make_docs())
        results = h.search("neural networks", top_k=2)
        for r in results:
            assert r.source == "hybrid"

    def test_empty_index_returns_empty(self):
        h = self._make()
        results = h.search("cat", top_k=5)
        assert results == []

    def test_stats(self):
        h = self._make()
        h.index_batch(make_docs())
        s = h.stats()
        assert s["indexed_docs"] == 5
        assert s["reranker"] is True
        assert s["rrf_k"] == RRFMerger.DEFAULT_K

    def test_metadata_propagated(self):
        h = self._make()
        h.index_batch(make_docs())
        results = h.search("cat", top_k=5)
        for r in results:
            if r.doc_id == "d1":
                assert r.metadata.get("topic") == "animals"
                break
