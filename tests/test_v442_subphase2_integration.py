"""
V442 -- SubPhase 2 Integration Tests
RAG stack: QdrantBridge + HybridRetriever + NKGContextAdapter + RetrievalPipeline + DataRightsAPI
"""
import pytest
from literary_system.rag.qdrant_bridge import QdrantBridge, EmbeddingService, TenantIsolation
from literary_system.rag.hybrid_retriever import (
    BM25Retriever, DenseRetriever, HybridRetriever,
    CrossEncoderReRanker, Document,
)
from literary_system.rag.nkg_context_adapter import (
    NKGContextAdapter, NKGNodeSnapshot, PriorityLevel, ContextSerializer,
)
from literary_system.rag.retrieval_pipeline import (
    RetrievalPipeline, ProvenanceLedger, PIPELINE_VERSION,
)
from literary_system.rag.bge_hosting_gate import (
    BGEHostingInput, BGEHostingGate, GPUTier, HostingRecommendation,
)
from literary_system.rag.data_rights_api import (
    DataRightsAPI, ConsentStatus, SubjectRegistry,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_full_pipeline(max_tokens=2048, top_k=5):
    bm25 = BM25Retriever()
    svc = EmbeddingService(provider="mock")
    tenant = TenantIsolation()
    bridge = QdrantBridge(host="localhost", port=6333, tenant=tenant, embedding_svc=svc, fallback=True)
    dense = DenseRetriever(bridge, collection="integration")
    reranker = CrossEncoderReRanker(provider="mock")
    retriever = HybridRetriever(bm25, dense, reranker=reranker)
    return RetrievalPipeline(retriever, max_context_tokens=max_tokens, top_k=top_k)


CORPUS = [
    Document("d1", "the brave knight slays the dragon at dawn", {"genre": "fantasy"}),
    Document("d2", "neural networks process information through layers", {"genre": "tech"}),
    Document("d3", "the queen commands her army to march north", {"genre": "fantasy"}),
    Document("d4", "RAG systems combine retrieval with generation", {"genre": "tech"}),
    Document("d5", "the wizard casts a spell of eternal sleep", {"genre": "fantasy"}),
    Document("d6", "gradient descent optimizes the loss function", {"genre": "tech"}),
]


# ---------------------------------------------------------------------------
# TestRAGStackModuleSurvival
# ---------------------------------------------------------------------------

class TestRAGStackModuleSurvival:
    """Verify all SubPhase 2 modules are importable and instantiable."""

    def test_qdrant_bridge_survives(self):
        svc = EmbeddingService(provider="mock")
        tenant = TenantIsolation()
        bridge = QdrantBridge(host="localhost", port=6333, tenant=tenant, embedding_svc=svc, fallback=True)
        assert bridge.backend == "in_memory"

    def test_hybrid_retriever_survives(self):
        bm25 = BM25Retriever()
        svc = EmbeddingService(provider="mock")
        tenant = TenantIsolation()
        bridge = QdrantBridge(host="localhost", port=6333, tenant=tenant, embedding_svc=svc, fallback=True)
        dense = DenseRetriever(bridge, collection="survival")
        h = HybridRetriever(bm25, dense)
        assert h.indexed_count == 0

    def test_nkg_context_adapter_survives(self):
        adapter = NKGContextAdapter()
        adapter.add_node(NKGNodeSnapshot("n1", "label", "content"))
        ctx = adapter.build_context()
        assert "NKG CONTEXT" in ctx

    def test_retrieval_pipeline_survives(self):
        p = make_full_pipeline()
        assert p.stats()["pipeline_version"] == PIPELINE_VERSION

    def test_bge_hosting_gate_survives(self):
        gate = BGEHostingGate()
        inp = BGEHostingInput(monthly_embedding_calls=1_000_000, gpu_tier=GPUTier.T4)
        dec = gate.evaluate(inp)
        assert dec.recommendation in list(HostingRecommendation)

    def test_data_rights_api_survives(self):
        api = DataRightsAPI()
        api.registry.register("s1", "test@example.com")
        assert api.registry.count == 1


# ---------------------------------------------------------------------------
# TestFullRAGPipeline
# ---------------------------------------------------------------------------

class TestFullRAGPipeline:
    def test_index_and_retrieve(self):
        p = make_full_pipeline()
        p.index(CORPUS)
        result = p.run("knight dragon")
        assert len(result.ranked) > 0
        assert result.provenance.pipeline_version == PIPELINE_VERSION

    def test_context_contains_retrieved_text(self):
        p = make_full_pipeline()
        p.index(CORPUS)
        result = p.run("neural network gradient")
        assert "=== NKG CONTEXT ===" in result.context

    def test_provenance_sources_match_ranked(self):
        p = make_full_pipeline(top_k=3)
        p.index(CORPUS)
        result = p.run("wizard spell")
        ranked_ids = {r.doc_id for r in result.ranked}
        prov_ids = {s.doc_id for s in result.provenance.sources}
        assert ranked_ids == prov_ids

    def test_multiple_queries_accumulate_ledger(self):
        p = make_full_pipeline()
        p.index(CORPUS)
        for q in ["knight", "neural", "queen", "RAG"]:
            p.run(q)
        assert p.ledger.count == 4

    def test_context_fits_tight_budget(self):
        p = make_full_pipeline(max_tokens=80)
        p.index(CORPUS)
        result = p.run("knight dragon")
        tokens = ContextSerializer.estimate_tokens(result.context)
        assert tokens <= 80


# ---------------------------------------------------------------------------
# TestDataRightsPipelineIntegration
# ---------------------------------------------------------------------------

class TestDataRightsPipelineIntegration:
    def test_erasure_removes_docs(self):
        api = DataRightsAPI()
        api.registry.register("alice", "alice@example.com", consent=ConsentStatus.GRANTED)
        api.index_document("alice", "doc_a1", "alice content 1")
        api.index_document("alice", "doc_a2", "alice content 2")
        assert api.indexed_doc_count == 2
        deleted = api.right_to_erasure("alice")
        assert deleted == 2
        assert api.indexed_doc_count == 0

    def test_consent_required_for_indexing(self):
        api = DataRightsAPI()
        api.registry.register("bob", "bob@example.com", consent=ConsentStatus.DENIED)
        ok = api.index_document("bob", "doc_b1", "bob content")
        assert ok is False
        assert api.indexed_doc_count == 0

    def test_portability_export_structure(self):
        api = DataRightsAPI()
        api.registry.register("carol", "carol@example.com", consent=ConsentStatus.GRANTED)
        api.index_document("carol", "doc_c1", "carol content")
        export = api.right_to_portability("carol")
        assert export["subject_id"] == "carol"
        assert len(export["documents"]) == 1
        assert "exported_at" in export

    def test_audit_log_complete(self):
        api = DataRightsAPI()
        api.registry.register("dave", "dave@example.com", consent=ConsentStatus.GRANTED)
        api.index_document("dave", "doc_d1", "content")
        api.right_to_access("dave")
        api.right_to_erasure("dave")
        logs = api.audit_log.for_subject("dave")
        assert len(logs) >= 2


# ---------------------------------------------------------------------------
# TestSubPhase2AllModulesConnected
# ---------------------------------------------------------------------------

class TestSubPhase2AllModulesConnected:
    """Gate-level check: all SubPhase 2 symbols importable and functional."""

    def test_embedding_service_mock(self):
        svc = EmbeddingService(provider="mock")
        result = svc.embed("test text")
        assert len(result.vector) == 1024
        assert abs(sum(x**2 for x in result.vector) - 1.0) < 0.001

    def test_tenant_isolation_collection_naming(self):
        ti = TenantIsolation()
        ti.register("tenant_a")
        col = ti.collection_name("tenant_a", "docs")
        assert col == "tenant_a_docs"

    def test_rrf_merger_deterministic(self):
        from literary_system.rag.hybrid_retriever import RRFMerger
        m = RRFMerger()
        a = [("d1", 1.0), ("d2", 0.5)]
        b = [("d1", 0.9), ("d3", 0.6)]
        r1 = m.merge([a, b])
        r2 = m.merge([a, b])
        assert r1 == r2

    def test_nkg_priority_filter(self):
        nodes = [
            NKGNodeSnapshot("n1", "L", "C", PriorityLevel.CRITICAL),
            NKGNodeSnapshot("n2", "L", "C", PriorityLevel.BACKGROUND),
        ]
        filtered = NKGContextAdapter.filter_by_priority(nodes, PriorityLevel.HIGH)
        assert len(filtered) == 1
        assert filtered[0].priority == PriorityLevel.CRITICAL

    def test_provenance_ledger_export(self):
        p = make_full_pipeline()
        p.index(CORPUS[:3])
        p.run("knight")
        exported = p.ledger.export()
        assert len(exported) == 1
        assert "retrieval_id" in exported[0]
