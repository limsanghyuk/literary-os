"""
V437 -- QdrantBridge + EmbeddingService + TenantIsolation tests
"""
from __future__ import annotations
import pytest
from literary_system.rag.qdrant_bridge import (
    EmbeddingService, EmbeddingResult, EmbeddingServiceError,
    TenantIsolation, TenantConfig,
    QdrantBridge, InMemoryVectorStore, VectorDocument, SearchResult,
    QdrantBridgeError,
)


class TestEmbeddingService:
    def test_mock_provider_returns_vector(self):
        svc = EmbeddingService(provider="mock")
        result = svc.embed("hello world")
        assert isinstance(result, EmbeddingResult)
        assert len(result.vector) == 1024

    def test_mock_vector_is_unit_norm(self):
        svc = EmbeddingService(provider="mock")
        v = svc.embed("test").vector
        norm = sum(x**2 for x in v) ** 0.5
        assert abs(norm - 1.0) < 0.001

    def test_mock_deterministic(self):
        svc = EmbeddingService(provider="mock")
        v1 = svc.embed("same text").vector
        v2 = svc.embed("same text").vector
        assert v1 == v2

    def test_mock_different_texts_differ(self):
        svc = EmbeddingService(provider="mock")
        v1 = svc.embed("text A").vector
        v2 = svc.embed("text B").vector
        assert v1 != v2

    def test_embed_batch(self):
        svc = EmbeddingService(provider="mock")
        results = svc.embed_batch(["a", "b", "c"])
        assert len(results) == 3
        assert all(isinstance(r, EmbeddingResult) for r in results)

    def test_invalid_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            EmbeddingService(provider="invalid")

    def test_together_no_key_raises(self):
        svc = EmbeddingService(provider="together", api_key="")
        with pytest.raises(EmbeddingServiceError, match="TOGETHER_API_KEY"):
            svc.embed("test")

    def test_call_count(self):
        svc = EmbeddingService(provider="mock")
        svc.embed("a")
        svc.embed("b")
        assert svc._call_count == 2


class TestTenantIsolation:
    def test_register_and_get(self):
        t = TenantIsolation()
        cfg = t.register("tenant1", kms_key_id="key-abc")
        assert t.get("tenant1") is cfg
        assert cfg.kms_key_id == "key-abc"

    def test_duplicate_raises(self):
        t = TenantIsolation()
        t.register("t1")
        with pytest.raises(ValueError, match="already registered"):
            t.register("t1")

    def test_collection_name(self):
        t = TenantIsolation()
        t.register("acme")
        name = t.collection_name("acme", "scenes")
        assert name == "acme_scenes"

    def test_inactive_tenant_raises(self):
        t = TenantIsolation()
        t.register("t1")
        t.deactivate("t1")
        with pytest.raises(ValueError, match="inactive"):
            t.collection_name("t1", "scenes")

    def test_list_active(self):
        t = TenantIsolation()
        t.register("a")
        t.register("b")
        t.deactivate("b")
        active = t.list_active()
        assert len(active) == 1
        assert active[0].tenant_id == "a"


class TestInMemoryVectorStore:
    def _vec(self, val: float, dim: int = 4) -> list:
        return [val] * dim

    def test_upsert_and_count(self):
        store = InMemoryVectorStore()
        doc = VectorDocument(doc_id="d1", text="hello", vector=self._vec(0.5))
        store.upsert("col", doc)
        assert store.count("col") == 1

    def test_search_returns_ranked(self):
        store = InMemoryVectorStore()
        store.upsert("col", VectorDocument("d1", "text1", [1,0,0,0]))
        store.upsert("col", VectorDocument("d2", "text2", [0,1,0,0]))
        results = store.search("col", [1,0,0,0], top_k=2)
        assert results[0].doc_id == "d1"
        assert results[0].score > results[1].score

    def test_delete(self):
        store = InMemoryVectorStore()
        store.upsert("col", VectorDocument("d1", "t", [1,0,0,0]))
        assert store.delete("col", "d1") is True
        assert store.count("col") == 0

    def test_delete_nonexistent(self):
        store = InMemoryVectorStore()
        assert store.delete("col", "missing") is False

    def test_empty_search(self):
        store = InMemoryVectorStore()
        results = store.search("empty", [1,0,0,0])
        assert results == []


class TestQdrantBridge:
    def _make_bridge(self):
        svc = EmbeddingService(provider="mock", dimension=16)
        return QdrantBridge(
            host="localhost", port=9999,  # unreachable -> fallback
            embedding_svc=svc, fallback=True,
        )

    def test_backend_is_in_memory(self):
        b = self._make_bridge()
        assert b.backend == "in_memory"

    def test_upsert_and_search(self):
        b = self._make_bridge()
        b.upsert("scenes", "s1", "A hero appears")
        b.upsert("scenes", "s2", "Villain enters")
        results = b.search("scenes", "hero", top_k=2)
        assert len(results) == 2
        assert all(isinstance(r, SearchResult) for r in results)

    def test_upsert_with_metadata(self):
        b = self._make_bridge()
        b.upsert("col", "d1", "text", metadata={"episode": 1})
        results = b.search("col", "text", top_k=1)
        assert results[0].metadata.get("episode") == 1

    def test_tenant_isolated_collection(self):
        svc = EmbeddingService(provider="mock", dimension=16)
        tenant = TenantIsolation()
        tenant.register("corp_a")
        tenant.register("corp_b")
        b = QdrantBridge(port=9999, embedding_svc=svc, tenant=tenant)

        b.upsert("scenes", "s1", "corp_a doc", tenant_id="corp_a")
        b.upsert("scenes", "s2", "corp_b doc", tenant_id="corp_b")

        # corp_a search should only see corp_a docs
        results_a = b.search("scenes", "doc", top_k=5, tenant_id="corp_a")
        results_b = b.search("scenes", "doc", top_k=5, tenant_id="corp_b")

        ids_a = {r.doc_id for r in results_a}
        ids_b = {r.doc_id for r in results_b}
        assert ids_a.isdisjoint(ids_b)  # no overlap

    def test_delete(self):
        b = self._make_bridge()
        b.upsert("col", "d1", "text")
        assert b.count("col") == 1
        b.delete("col", "d1")
        assert b.count("col") == 0
