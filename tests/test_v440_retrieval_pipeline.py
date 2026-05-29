"""
V440 tests -- RetrievalPipeline + Provenance (ADR-007)
"""
import pytest
from literary_system.rag.retrieval_pipeline import (
    SourceEntry, ProvenanceRecord, ProvenanceLedger,
    RetrievalResult, RetrievalPipeline, PIPELINE_VERSION,
)
from literary_system.rag.hybrid_retriever import (
    BM25Retriever, DenseRetriever, HybridRetriever,
    CrossEncoderReRanker, RRFMerger, Document,
)
from literary_system.rag.qdrant_bridge import (
    QdrantBridge, EmbeddingService, TenantIsolation,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_pipeline(max_tokens=2048, top_k=5):
    bm25 = BM25Retriever()
    svc = EmbeddingService(provider="mock")
    tenant = TenantIsolation()
    bridge = QdrantBridge(host="localhost", port=6333, tenant=tenant, embedding_svc=svc, fallback=True)
    dense = DenseRetriever(bridge, collection="pipe_test")
    reranker = CrossEncoderReRanker(provider="mock")
    retriever = HybridRetriever(bm25, dense, reranker=reranker)
    return RetrievalPipeline(retriever, max_context_tokens=max_tokens, top_k=top_k)


SAMPLE_DOCS = [
    Document("d1", "the hero confronts the villain in a dark alley"),
    Document("d2", "the princess discovers a hidden map to the treasure"),
    Document("d3", "machine learning algorithms learn from training data"),
    Document("d4", "the knight rides through the enchanted forest"),
    Document("d5", "neural networks process information in layers"),
]


# ---------------------------------------------------------------------------
# TestSourceEntry
# ---------------------------------------------------------------------------

class TestSourceEntry:
    def test_fields(self):
        s = SourceEntry(doc_id="d1", score=0.9, retriever_type="hybrid", rank=1)
        assert s.doc_id == "d1"
        assert s.score == 0.9
        assert s.rank == 1


# ---------------------------------------------------------------------------
# TestProvenanceRecord
# ---------------------------------------------------------------------------

class TestProvenanceRecord:
    def _make_results(self):
        from literary_system.rag.hybrid_retriever import RankedResult
        return [
            RankedResult("d1", "text1", 0.9, 1, "hybrid"),
            RankedResult("d2", "text2", 0.7, 2, "hybrid"),
        ]

    def test_create(self):
        prov = ProvenanceRecord.create("hello", self._make_results(), context_tokens=100)
        assert prov.retrieval_id
        assert prov.query_hash
        assert prov.pipeline_version == PIPELINE_VERSION
        assert prov.context_tokens == 100

    def test_query_hash_deterministic_prefix(self):
        import hashlib
        query = "hello world"
        expected = hashlib.sha256(query.encode()).hexdigest()[:16]
        prov = ProvenanceRecord.create(query, [], context_tokens=0)
        assert prov.query_hash == expected

    def test_sources_populated(self):
        prov = ProvenanceRecord.create("q", self._make_results(), context_tokens=50)
        assert len(prov.sources) == 2
        assert prov.sources[0].doc_id == "d1"

    def test_frozen(self):
        prov = ProvenanceRecord.create("q", [], context_tokens=0)
        with pytest.raises(Exception):
            prov.retrieval_id = "changed"

    def test_to_dict(self):
        prov = ProvenanceRecord.create("q", self._make_results(), context_tokens=42)
        d = prov.to_dict()
        assert "retrieval_id" in d
        assert "query_hash" in d
        assert "sources" in d
        assert len(d["sources"]) == 2

    def test_unique_ids(self):
        p1 = ProvenanceRecord.create("q", [], context_tokens=0)
        p2 = ProvenanceRecord.create("q", [], context_tokens=0)
        assert p1.retrieval_id != p2.retrieval_id

    def test_timestamp_format(self):
        prov = ProvenanceRecord.create("q", [], context_tokens=0)
        # ISO-8601 timestamps contain "T" and "+00:00"
        assert "T" in prov.timestamp


# ---------------------------------------------------------------------------
# TestProvenanceLedger
# ---------------------------------------------------------------------------

class TestProvenanceLedger:
    def _prov(self):
        return ProvenanceRecord.create("q", [], context_tokens=0)

    def test_append_and_count(self):
        led = ProvenanceLedger()
        led.append(self._prov())
        assert led.count == 1

    def test_get_by_id(self):
        led = ProvenanceLedger()
        p = self._prov()
        led.append(p)
        assert led.get(p.retrieval_id) is p

    def test_get_missing(self):
        led = ProvenanceLedger()
        assert led.get("nonexistent") is None

    def test_all_records(self):
        led = ProvenanceLedger()
        led.append(self._prov())
        led.append(self._prov())
        assert len(led.all_records()) == 2

    def test_export(self):
        led = ProvenanceLedger()
        led.append(self._prov())
        exported = led.export()
        assert len(exported) == 1
        assert "retrieval_id" in exported[0]


# ---------------------------------------------------------------------------
# TestRetrievalPipeline
# ---------------------------------------------------------------------------

class TestRetrievalPipeline:
    def test_index_and_stats(self):
        p = make_pipeline()
        p.index(SAMPLE_DOCS)
        s = p.stats()
        assert s["indexed_docs"] == 5
        assert s["pipeline_version"] == PIPELINE_VERSION

    def test_run_returns_result(self):
        p = make_pipeline()
        p.index(SAMPLE_DOCS)
        result = p.run("hero villain")
        assert isinstance(result, RetrievalResult)
        assert result.query == "hero villain"

    def test_run_context_has_header(self):
        p = make_pipeline()
        p.index(SAMPLE_DOCS)
        result = p.run("knight forest")
        assert "=== NKG CONTEXT ===" in result.context

    def test_run_provenance_logged(self):
        p = make_pipeline()
        p.index(SAMPLE_DOCS)
        result = p.run("neural network")
        assert p.ledger.count == 1
        assert p.ledger.get(result.provenance.retrieval_id) is not None

    def test_multiple_runs_accumulate_ledger(self):
        p = make_pipeline()
        p.index(SAMPLE_DOCS)
        p.run("hero")
        p.run("knight")
        p.run("machine learning")
        assert p.ledger.count == 3

    def test_doc_ids_in_result(self):
        p = make_pipeline(top_k=3)
        p.index(SAMPLE_DOCS)
        result = p.run("hero villain")
        assert isinstance(result.doc_ids, list)

    def test_top_doc_id(self):
        p = make_pipeline(top_k=3)
        p.index(SAMPLE_DOCS)
        result = p.run("hero")
        assert result.top_doc_id is not None

    def test_empty_index_returns_empty_ranked(self):
        p = make_pipeline()
        result = p.run("anything")
        assert result.ranked == []

    def test_provenance_has_sources(self):
        p = make_pipeline()
        p.index(SAMPLE_DOCS)
        result = p.run("treasure map")
        assert len(result.provenance.sources) > 0

    def test_provenance_version(self):
        p = make_pipeline()
        p.index(SAMPLE_DOCS)
        result = p.run("quest")
        assert result.provenance.pipeline_version == PIPELINE_VERSION

    def test_context_fits_token_budget(self):
        p = make_pipeline(max_tokens=100)
        p.index(SAMPLE_DOCS)
        result = p.run("hero")
        from literary_system.rag.nkg_context_adapter import ContextSerializer
        tokens = ContextSerializer.estimate_tokens(result.context)
        assert tokens <= 100

    def test_custom_ledger_injected(self):
        led = ProvenanceLedger()
        bm25 = BM25Retriever()
        svc = EmbeddingService(provider="mock")
        tenant = TenantIsolation()
        bridge = QdrantBridge(host="localhost", port=6333, tenant=tenant, embedding_svc=svc, fallback=True)
        dense = DenseRetriever(bridge, collection="custom")
        retriever = HybridRetriever(bm25, dense)
        p = RetrievalPipeline(retriever, ledger=led)
        p.index(SAMPLE_DOCS)
        p.run("hero")
        assert led.count == 1
