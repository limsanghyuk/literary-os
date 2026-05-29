"""
V437 -- QdrantBridge + EmbeddingService + TenantIsolation

QdrantBridge:     Qdrant vector DB client (HTTP REST). pgvector dict fallback.
EmbeddingService: BGE-M3 via Together.ai (delegated) or sentence-transformers local.
TenantIsolation:  Per-tenant collection namespacing + KMS key separation.

Design:
  - Qdrant not required at import time (graceful degradation to in-memory dict)
  - EmbeddingService: provider=together | local | mock
  - TenantIsolation: collection_name = tenant_id + "_" + base_collection
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# EmbeddingService
# ---------------------------------------------------------------------------

EMBEDDING_DIM = 1024   # BGE-M3 standard dimension


@dataclass
class EmbeddingResult:
    text:      str
    vector:    List[float]
    model:     str  = ""
    latency_ms: float = 0.0


class EmbeddingServiceError(Exception):
    pass


class EmbeddingService:
    """
    Text -> dense vector embedding service.

    Providers:
      together  -- Together.ai API (BGE-M3 delegated, requires TOGETHER_API_KEY)
      local     -- sentence-transformers (requires pip install sentence-transformers)
      mock      -- unit-test stub (deterministic hash-based vector)
    """

    TOGETHER_URL  = "https://api.together.xyz/v1/embeddings"
    TOGETHER_MODEL = "BAAI/bge-m3"

    def __init__(
        self,
        provider:  str = "mock",
        api_key:   str = "",
        model:     str = "",
        dimension: int = EMBEDDING_DIM,
    ) -> None:
        if provider not in ("together", "local", "mock"):
            raise ValueError("Unknown provider: " + provider)
        self.provider  = provider
        self.api_key   = api_key
        self.model     = model or ("BAAI/bge-m3" if provider == "together" else "mock")
        self.dimension = dimension
        self._call_count = 0

    def embed(self, text: str) -> EmbeddingResult:
        t0 = time.monotonic()
        if self.provider == "mock":
            vector = self._mock_vector(text)
        elif self.provider == "together":
            vector = self._together_embed(text)
        elif self.provider == "local":
            vector = self._local_embed(text)
        else:
            raise EmbeddingServiceError("Unknown provider: " + self.provider)
        latency = (time.monotonic() - t0) * 1000.0
        self._call_count += 1
        return EmbeddingResult(
            text=text, vector=vector, model=self.model, latency_ms=round(latency, 2)
        )

    def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        return [self.embed(t) for t in texts]

    def _mock_vector(self, text: str) -> List[float]:
        """Deterministic hash-based unit vector for testing."""
        seed = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16)
        import random
        rng = random.Random(seed)
        raw = [rng.gauss(0, 1) for _ in range(self.dimension)]
        norm = sum(x**2 for x in raw) ** 0.5 or 1.0
        return [x / norm for x in raw]

    def _together_embed(self, text: str) -> List[float]:
        if not self.api_key:
            raise EmbeddingServiceError("TOGETHER_API_KEY not set")
        payload = json.dumps({"model": self.model, "input": text}).encode("utf-8")
        req = urllib.request.Request(
            self.TOGETHER_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self.api_key,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = json.loads(r.read().decode("utf-8"))
            return body["data"][0]["embedding"]
        except Exception as e:
            raise EmbeddingServiceError("Together.ai error: " + str(e))

    def _local_embed(self, text: str) -> List[float]:
        try:
            from sentence_transformers import SentenceTransformer
            model_name = self.model if self.model != "mock" else "all-MiniLM-L6-v2"
            model = SentenceTransformer(model_name)
            vec = model.encode(text).tolist()
            return vec
        except ImportError:
            raise EmbeddingServiceError("sentence-transformers not installed")


# ---------------------------------------------------------------------------
# TenantIsolation
# ---------------------------------------------------------------------------

@dataclass
class QdrantTenantConfig:
    tenant_id:    str
    kms_key_id:   str  = ""   # KMS key for encryption at rest
    created_at:   float = field(default_factory=time.time)
    active:       bool  = True


class TenantIsolation:
    """
    Per-tenant collection namespacing.
    collection_name(tenant_id, base) = tenant_id + "_" + base
    """

    def __init__(self) -> None:
        self._tenants: Dict[str, TenantConfig] = {}

    def register(self, tenant_id: str, kms_key_id: str = "") -> TenantConfig:
        if tenant_id in self._tenants:
            raise ValueError("Tenant already registered: " + tenant_id)
        cfg = TenantConfig(tenant_id=tenant_id, kms_key_id=kms_key_id)
        self._tenants[tenant_id] = cfg
        return cfg

    def get(self, tenant_id: str) -> TenantConfig:
        if tenant_id not in self._tenants:
            raise KeyError("Unknown tenant: " + tenant_id)
        return self._tenants[tenant_id]

    def collection_name(self, tenant_id: str, base_collection: str) -> str:
        cfg = self.get(tenant_id)
        if not cfg.active:
            raise ValueError("Tenant is inactive: " + tenant_id)
        return tenant_id + "_" + base_collection

    def deactivate(self, tenant_id: str) -> None:
        self.get(tenant_id).active = False

    def list_active(self) -> List[TenantConfig]:
        return [t for t in self._tenants.values() if t.active]


# ---------------------------------------------------------------------------
# QdrantBridge
# ---------------------------------------------------------------------------

@dataclass
class VectorDocument:
    doc_id:    str
    text:      str
    vector:    List[float]
    metadata:  dict = field(default_factory=dict)
    tenant_id: str  = ""


@dataclass
class QdrantSearchResult:
    doc_id:  str
    text:    str
    score:   float
    metadata: dict = field(default_factory=dict)


class QdrantBridgeError(Exception):
    pass


class InMemoryVectorStore:
    """In-memory pgvector fallback (no Qdrant required)."""

    def __init__(self) -> None:
        self._docs: Dict[str, Dict[str, VectorDocument]] = {}

    def upsert(self, collection: str, doc: VectorDocument) -> None:
        if collection not in self._docs:
            self._docs[collection] = {}
        self._docs[collection][doc.doc_id] = doc

    def search(self, collection: str, query_vector: List[float], top_k: int = 5) -> List[SearchResult]:
        docs = list(self._docs.get(collection, {}).values())
        if not docs:
            return []
        scored = [(doc, self._cosine(query_vector, doc.vector)) for doc in docs]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [
            SearchResult(doc_id=d.doc_id, text=d.text, score=s, metadata=d.metadata)
            for d, s in scored[:top_k]
        ]

    def delete(self, collection: str, doc_id: str) -> bool:
        col = self._docs.get(collection, {})
        if doc_id in col:
            del col[doc_id]
            return True
        return False

    def count(self, collection: str) -> int:
        return len(self._docs.get(collection, {}))

    @staticmethod
    def _cosine(a: List[float], b: List[float]) -> float:
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x**2 for x in a) ** 0.5
        nb = sum(x**2 for x in b) ** 0.5
        return dot / (na * nb) if (na * nb) > 0 else 0.0


class QdrantBridge:
    """
    Qdrant vector DB bridge.
    Falls back to InMemoryVectorStore when Qdrant is unavailable.

    HNSW config: ef=200, m=16 (Qdrant default for production).
    """

    HNSW_EF = 200
    HNSW_M  = 16

    def __init__(
        self,
        host:          str = "localhost",
        port:          int = 6333,
        tenant:        Optional[TenantIsolation] = None,
        embedding_svc: Optional[EmbeddingService] = None,
        fallback:      bool = True,
    ) -> None:
        self.host = host
        self.port = port
        self._tenant    = tenant or TenantIsolation()
        self._embed_svc = embedding_svc or EmbeddingService(provider="mock")
        self._fallback  = InMemoryVectorStore() if fallback else None
        self._qdrant_ok = self._probe()

    def _probe(self) -> bool:
        try:
            url = "http://" + self.host + ":" + str(self.port) + "/healthz"
            with urllib.request.urlopen(url, timeout=2) as r:
                return r.status == 200
        except Exception:
            return False

    @property
    def backend(self) -> str:
        return "qdrant" if self._qdrant_ok else "in_memory"

    def upsert(
        self,
        collection:  str,
        doc_id:      str,
        text:        str,
        metadata:    Optional[dict] = None,
        tenant_id:   str = "",
    ) -> None:
        if tenant_id:
            collection = self._tenant.collection_name(tenant_id, collection)
        result = self._embed_svc.embed(text)
        doc = VectorDocument(
            doc_id=doc_id, text=text, vector=result.vector,
            metadata=metadata or {}, tenant_id=tenant_id,
        )
        if self._qdrant_ok:
            self._qdrant_upsert(collection, doc)
        elif self._fallback:
            self._fallback.upsert(collection, doc)
        else:
            raise QdrantBridgeError("No backend available")

    def search(
        self,
        collection:  str,
        query:       str,
        top_k:       int = 5,
        tenant_id:   str = "",
    ) -> List[SearchResult]:
        if tenant_id:
            collection = self._tenant.collection_name(tenant_id, collection)
        q_vec = self._embed_svc.embed(query).vector
        if self._qdrant_ok:
            return self._qdrant_search(collection, q_vec, top_k)
        elif self._fallback:
            return self._fallback.search(collection, q_vec, top_k)
        return []

    def delete(self, collection: str, doc_id: str, tenant_id: str = "") -> bool:
        if tenant_id:
            collection = self._tenant.collection_name(tenant_id, collection)
        if self._fallback:
            return self._fallback.delete(collection, doc_id)
        return False

    def count(self, collection: str, tenant_id: str = "") -> int:
        if tenant_id:
            collection = self._tenant.collection_name(tenant_id, collection)
        if self._fallback:
            return self._fallback.count(collection)
        return 0

    # -- Qdrant REST stubs (real implementation when Qdrant is live) --

    def _qdrant_upsert(self, collection: str, doc: VectorDocument) -> None:
        url = "http://" + self.host + ":" + str(self.port) + "/collections/" + collection + "/points"
        payload = json.dumps({"points": [{
            "id": abs(hash(doc.doc_id)) % (2**31),
            "vector": doc.vector,
            "payload": {"text": doc.text, **doc.metadata},
        }]}).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="PUT",
        )
        try:
            urllib.request.urlopen(req, timeout=10)
        except Exception:
            if self._fallback:
                self._fallback.upsert(collection, doc)
                self._qdrant_ok = False

    def _qdrant_search(self, collection: str, vector: List[float], top_k: int) -> List[SearchResult]:
        url = "http://" + self.host + ":" + str(self.port) + "/collections/" + collection + "/points/search"
        payload = json.dumps({"vector": vector, "limit": top_k, "with_payload": True}).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                body = json.loads(r.read().decode("utf-8"))
            return [
                SearchResult(
                    doc_id=str(hit["id"]),
                    text=hit["payload"].get("text", ""),
                    score=hit["score"],
                    metadata={k: v for k, v in hit["payload"].items() if k != "text"},
                )
                for hit in body.get("result", [])
            ]
        except Exception:
            if self._fallback:
                return self._fallback.search(collection, vector, top_k)
            return []

SearchResult = QdrantSearchResult  # V579 backward-compat alias

TenantConfig = QdrantTenantConfig  # V579 backward-compat alias
