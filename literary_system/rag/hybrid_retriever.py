"""
V438 -- HybridRetriever
BM25 sparse + dense vector + Reciprocal Rank Fusion + cross-encoder re-rank.

Design:
  BM25Retriever      -- TF-IDF / BM25 sparse retrieval over in-memory corpus
  DenseRetriever     -- wraps QdrantBridge for embedding-based search
  RRFMerger          -- Reciprocal Rank Fusion (k=60, standard)
  CrossEncoderReRanker -- mock / sentence-transformers cross-encoder
  HybridRetriever    -- orchestrates all stages, returns RankedResult list
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from literary_system.rag.qdrant_bridge import QdrantBridge, SearchResult

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class Document:
    """Indexed document unit."""
    doc_id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RankedResult:
    """Single result returned by HybridRetriever."""
    doc_id: str
    text: str
    score: float
    rank: int
    source: str          # "bm25" | "dense" | "hybrid"
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# BM25Retriever  (pure Python, no external dependency)
# ---------------------------------------------------------------------------

class BM25Retriever:
    """
    Okapi BM25 sparse retriever.
    k1=1.5, b=0.75 -- standard defaults.
    Corpus is indexed at construction; call index() to add documents.
    """

    K1: float = 1.5
    B: float  = 0.75

    def __init__(self) -> None:
        self._docs: Dict[str, Document] = {}
        self._tf: Dict[str, Dict[str, float]] = {}   # doc_id -> {term -> tf}
        self._df: Dict[str, int] = {}                # term -> doc freq
        self._dl: Dict[str, int] = {}                # doc_id -> doc len
        self._avg_dl: float = 0.0

    # --- indexing -----------------------------------------------------------

    def index(self, doc: Document) -> None:
        """Add or replace a document in the BM25 index."""
        tokens = self._tokenize(doc.text)
        self._docs[doc.doc_id] = doc
        self._dl[doc.doc_id] = len(tokens)

        tf_local: Dict[str, int] = {}
        for t in tokens:
            tf_local[t] = tf_local.get(t, 0) + 1

        # update IDF denominators
        old_tf = self._tf.get(doc.doc_id, {})
        for term in old_tf:
            self._df[term] = max(0, self._df.get(term, 0) - 1)

        self._tf[doc.doc_id] = {t: float(c) for t, c in tf_local.items()}

        for term in tf_local:
            self._df[term] = self._df.get(term, 0) + 1

        total_len = sum(self._dl.values())
        self._avg_dl = total_len / len(self._dl) if self._dl else 0.0

    def index_batch(self, docs: List[Document]) -> None:
        for d in docs:
            self.index(d)

    # --- retrieval ----------------------------------------------------------

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Return [(doc_id, score)] sorted by BM25 score descending."""
        if not self._docs:
            return []
        query_terms = self._tokenize(query)
        N = len(self._docs)
        scores: Dict[str, float] = {}

        for term in query_terms:
            df = self._df.get(term, 0)
            if df == 0:
                continue
            idf = math.log((N - df + 0.5) / (df + 0.5) + 1)
            for doc_id, tf_map in self._tf.items():
                tf = tf_map.get(term, 0.0)
                if tf == 0.0:
                    continue
                dl = self._dl[doc_id]
                numerator = tf * (self.K1 + 1)
                denominator = tf + self.K1 * (1 - self.B + self.B * dl / max(self._avg_dl, 1))
                scores[doc_id] = scores.get(doc_id, 0.0) + idf * (numerator / denominator)

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

    @property
    def doc_count(self) -> int:
        return len(self._docs)

    # --- helpers ------------------------------------------------------------

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Lowercase, split on whitespace/punctuation."""
        import re
        return re.findall(r"[a-zA-Z0-9가-힣]+", text.lower())


# ---------------------------------------------------------------------------
# DenseRetriever  (wraps QdrantBridge)
# ---------------------------------------------------------------------------

class DenseRetriever:
    """Thin adapter over QdrantBridge for dense ANN search."""

    def __init__(self, bridge: QdrantBridge, collection: str, tenant_id: str = "") -> None:
        self._bridge = bridge
        self._collection = collection
        self._tenant_id = tenant_id

    def upsert(self, doc: Document) -> None:
        self._bridge.upsert(
            collection=self._collection,
            doc_id=doc.doc_id,
            text=doc.text,
            metadata=doc.metadata,
            tenant_id=self._tenant_id,
        )

    def upsert_batch(self, docs: List[Document]) -> None:
        for d in docs:
            self.upsert(d)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        results: List[SearchResult] = self._bridge.search(
            collection=self._collection,
            query=query,
            top_k=top_k,
            tenant_id=self._tenant_id,
        )
        return [(r.doc_id, r.score) for r in results]


# ---------------------------------------------------------------------------
# RRFMerger  (Reciprocal Rank Fusion)
# ---------------------------------------------------------------------------

class RRFMerger:
    """
    Reciprocal Rank Fusion.
    rrf_score(d) = sum_over_lists( 1 / (k + rank(d)) )
    k=60 per original Cormack et al. 2009 paper.
    """

    DEFAULT_K: int = 60

    def __init__(self, k: int = DEFAULT_K) -> None:
        self.k = k

    def merge(
        self,
        ranked_lists: List[List[Tuple[str, float]]],
        weights: Optional[List[float]] = None,
    ) -> List[Tuple[str, float]]:
        """
        Merge N ranked lists into a single fused ranking.

        Args:
            ranked_lists: each list is [(doc_id, score)] sorted desc
            weights: optional per-list weight (default 1.0 each)

        Returns:
            [(doc_id, rrf_score)] sorted desc
        """
        if not ranked_lists:
            return []

        n = len(ranked_lists)
        w = weights if weights and len(weights) == n else [1.0] * n

        fused: Dict[str, float] = {}
        for lst, weight in zip(ranked_lists, w):
            for rank, (doc_id, _) in enumerate(lst, start=1):
                fused[doc_id] = fused.get(doc_id, 0.0) + weight / (self.k + rank)

        return sorted(fused.items(), key=lambda x: x[1], reverse=True)


# ---------------------------------------------------------------------------
# CrossEncoderReRanker
# ---------------------------------------------------------------------------

class CrossEncoderReRanker:
    """
    Cross-encoder re-ranker.
    provider="mock"          -- deterministic score from text overlap
    provider="sentence_transformers" -- real cross-encoder (optional dep)
    """

    def __init__(
        self,
        provider: str = "mock",
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    ) -> None:
        if provider not in ("mock", "sentence_transformers"):
            raise ValueError(f"Unknown cross-encoder provider: {provider}")
        self._provider = provider
        self._model_name = model_name
        self._model = None

        if provider == "sentence_transformers":
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(model_name)
            except ImportError as exc:
                raise ImportError(
                    "sentence_transformers required for provider='sentence_transformers'"
                ) from exc

    def rerank(
        self,
        query: str,
        candidates: List[Tuple[str, str, float]],
        top_k: Optional[int] = None,
    ) -> List[Tuple[str, float]]:
        """
        Re-rank candidates.

        Args:
            query: original query string
            candidates: [(doc_id, text, prior_score)]
            top_k: limit output size

        Returns:
            [(doc_id, rerank_score)] sorted desc
        """
        if not candidates:
            return []

        if self._provider == "sentence_transformers" and self._model is not None:
            pairs = [(query, c[1]) for c in candidates]
            scores = self._model.predict(pairs)
            result = [(candidates[i][0], float(scores[i])) for i in range(len(candidates))]
        else:
            result = [(c[0], self._mock_score(query, c[1])) for c in candidates]

        result.sort(key=lambda x: x[1], reverse=True)
        if top_k is not None:
            result = result[:top_k]
        return result

    @staticmethod
    def _mock_score(query: str, text: str) -> float:
        """Deterministic mock: Jaccard similarity of token sets."""
        q_tokens = set(query.lower().split())
        t_tokens = set(text.lower().split())
        if not q_tokens and not t_tokens:
            return 1.0
        if not q_tokens or not t_tokens:
            return 0.0
        inter = q_tokens & t_tokens
        union = q_tokens | t_tokens
        # add small hash-based perturbation for determinism
        h = int(hashlib.md5((query + text).encode()).hexdigest(), 16)
        noise = (h % 1000) / 100000.0
        return len(inter) / len(union) + noise


# ---------------------------------------------------------------------------
# HybridRetriever  (main orchestrator)
# ---------------------------------------------------------------------------

class HybridRetriever:
    """
    Two-stage hybrid retriever:
      Stage 1 -- BM25 + Dense ANN -> RRF fusion
      Stage 2 -- CrossEncoder re-rank (optional)

    Usage:
        retriever = HybridRetriever(bm25, dense, merger, reranker)
        retriever.index(docs)
        results = retriever.search(query, top_k=5)
    """

    def __init__(
        self,
        bm25: BM25Retriever,
        dense: DenseRetriever,
        merger: Optional[RRFMerger] = None,
        reranker: Optional[CrossEncoderReRanker] = None,
        bm25_weight: float = 0.5,
        dense_weight: float = 0.5,
        candidate_multiplier: int = 3,
    ) -> None:
        self._bm25 = bm25
        self._dense = dense
        self._merger = merger or RRFMerger()
        self._reranker = reranker
        self._bm25_weight = bm25_weight
        self._dense_weight = dense_weight
        self._candidate_multiplier = candidate_multiplier
        self._doc_store: Dict[str, Document] = {}

    # --- indexing -----------------------------------------------------------

    def index(self, doc: Document) -> None:
        self._doc_store[doc.doc_id] = doc
        self._bm25.index(doc)
        self._dense.upsert(doc)

    def index_batch(self, docs: List[Document]) -> None:
        for d in docs:
            self.index(d)

    # --- search -------------------------------------------------------------

    def search(
        self,
        query: str,
        top_k: int = 10,
        use_rerank: bool = True,
        rerank_top_k: Optional[int] = None,
    ) -> List[RankedResult]:
        """
        Full hybrid search pipeline.

        Returns list of RankedResult sorted by final score.
        """
        candidate_k = top_k * self._candidate_multiplier

        bm25_hits = self._bm25.search(query, top_k=candidate_k)
        dense_hits = self._dense.search(query, top_k=candidate_k)

        fused = self._merger.merge(
            [bm25_hits, dense_hits],
            weights=[self._bm25_weight, self._dense_weight],
        )

        if self._reranker and use_rerank and fused:
            candidates = []
            for doc_id, score in fused:
                doc = self._doc_store.get(doc_id)
                text = doc.text if doc else ""
                candidates.append((doc_id, text, score))

            reranked = self._reranker.rerank(
                query,
                candidates,
                top_k=rerank_top_k or top_k,
            )
            final = reranked[:top_k]
            source = "hybrid"
        else:
            final = fused[:top_k]
            source = "hybrid"

        results = []
        for rank, (doc_id, score) in enumerate(final, start=1):
            doc = self._doc_store.get(doc_id)
            results.append(
                RankedResult(
                    doc_id=doc_id,
                    text=doc.text if doc else "",
                    score=score,
                    rank=rank,
                    source=source,
                    metadata=doc.metadata if doc else {},
                )
            )
        return results

    # --- stats --------------------------------------------------------------

    @property
    def indexed_count(self) -> int:
        return len(self._doc_store)

    def stats(self) -> Dict[str, Any]:
        return {
            "indexed_docs": self.indexed_count,
            "bm25_docs": self._bm25.doc_count,
            "bm25_weight": self._bm25_weight,
            "dense_weight": self._dense_weight,
            "reranker": self._reranker is not None,
            "rrf_k": self._merger.k,
        }
