"""
V440 -- RetrievalPipeline + Provenance (ADR-007)

Orchestrates the full RAG retrieval flow:
  1. HybridRetriever -> candidate set
  2. NKGContextAdapter -> priority-ordered context block
  3. ProvenanceRecord -> immutable audit trail per retrieval
  4. RetrievalPipeline -> single entry-point for caller

ADR-007 Provenance contract:
  Every retrieval emits a ProvenanceRecord with:
    - query hash (SHA-256)
    - retrieval_id (UUID4)
    - timestamp (ISO-8601)
    - sources: [(doc_id, score, retriever_type)]
    - context_tokens used
    - pipeline_version
"""
from __future__ import annotations
import logging

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from literary_system.rag.hybrid_retriever import (
    HybridRetriever, RankedResult, Document,
)
from literary_system.rag.nkg_context_adapter import (
    NKGContextAdapter, NKGNodeSnapshot, PriorityLevel, ContextSerializer,
)

logger = logging.getLogger(__name__)


PIPELINE_VERSION = "V440"


# ---------------------------------------------------------------------------
# ProvenanceRecord  (ADR-007)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SourceEntry:
    """Single source document in a provenance record."""
    doc_id:         str
    score:          float
    retriever_type: str   # "hybrid" | "bm25" | "dense"
    rank:           int


@dataclass(frozen=True)
class ProvenanceRecord:
    """
    ADR-007 immutable audit record for a single retrieval call.
    Frozen dataclass -- cannot be mutated after creation.
    """
    retrieval_id:     str
    query_hash:       str
    timestamp:        str
    sources:          tuple
    context_tokens:   int
    pipeline_version: str
    metadata:         Dict[str, Any] = field(default_factory=dict, compare=False, hash=False)

    @classmethod
    def create(
        cls,
        query: str,
        results: List[RankedResult],
        context_tokens: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ProvenanceRecord":
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        retrieval_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        sources = tuple(
            SourceEntry(
                doc_id=r.doc_id,
                score=r.score,
                retriever_type=r.source,
                rank=r.rank,
            )
            for r in results
        )
        return cls(
            retrieval_id=retrieval_id,
            query_hash=query_hash,
            timestamp=timestamp,
            sources=sources,
            context_tokens=context_tokens,
            pipeline_version=PIPELINE_VERSION,
            metadata=metadata or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "retrieval_id": self.retrieval_id,
            "query_hash": self.query_hash,
            "timestamp": self.timestamp,
            "sources": [
                {
                    "doc_id": s.doc_id,
                    "score": s.score,
                    "retriever_type": s.retriever_type,
                    "rank": s.rank,
                }
                for s in self.sources
            ],
            "context_tokens": self.context_tokens,
            "pipeline_version": self.pipeline_version,
        }


# ---------------------------------------------------------------------------
# ProvenanceLedger  -- session-level audit log
# ---------------------------------------------------------------------------

class ProvenanceLedger:
    """
    In-memory audit ledger for a retrieval session.
    Append-only: records can be read but not modified or deleted.
    """

    def __init__(self) -> None:
        self._records: List[ProvenanceRecord] = []

    def append(self, record: ProvenanceRecord) -> None:
        self._records.append(record)

    def get(self, retrieval_id: str) -> Optional[ProvenanceRecord]:
        for r in self._records:
            if r.retrieval_id == retrieval_id:
                return r
        return None

    def all_records(self) -> List[ProvenanceRecord]:
        return list(self._records)

    @property
    def count(self) -> int:
        return len(self._records)

    def export(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._records]


# ---------------------------------------------------------------------------
# RetrievalResult  -- pipeline output bundle
# ---------------------------------------------------------------------------

@dataclass
class RetrievalResult:
    """Full output of one RetrievalPipeline.run() call."""
    query:       str
    ranked:      List[RankedResult]
    context:     str
    provenance:  ProvenanceRecord

    @property
    def doc_ids(self) -> List[str]:
        return [r.doc_id for r in self.ranked]

    @property
    def top_doc_id(self) -> Optional[str]:
        return self.ranked[0].doc_id if self.ranked else None


# ---------------------------------------------------------------------------
# RetrievalPipeline
# ---------------------------------------------------------------------------

class RetrievalPipeline:
    """
    Full RAG pipeline entry-point.

    Stage 1: HybridRetriever retrieves top-k candidate documents.
    Stage 2: Candidates are converted to NKGNodeSnapshots and
             rendered into a token-budgeted context block.
    Stage 3: ProvenanceRecord is created and appended to ledger.

    Usage:
        pipeline = RetrievalPipeline(retriever, max_context_tokens=1024)
        pipeline.index(docs)
        result = pipeline.run(query)
        logger.debug(result.context)
        logger.debug(result.provenance.retrieval_id)
    """

    def __init__(
        self,
        retriever: HybridRetriever,
        max_context_tokens: int = 2048,
        top_k: int = 5,
        ledger: Optional[ProvenanceLedger] = None,
    ) -> None:
        self._retriever = retriever
        self._max_context_tokens = max_context_tokens
        self._top_k = top_k
        self._ledger = ledger or ProvenanceLedger()

    # --- indexing -----------------------------------------------------------

    def index(self, docs: List[Document]) -> None:
        self._retriever.index_batch(docs)

    # --- retrieval ----------------------------------------------------------

    def run(
        self,
        query: str,
        top_k: Optional[int] = None,
        use_rerank: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RetrievalResult:
        """
        Execute full retrieval pipeline.

        Returns RetrievalResult with ranked docs, context string, provenance.
        """
        k = top_k or self._top_k
        ranked = self._retriever.search(query, top_k=k, use_rerank=use_rerank)

        context = self._build_context(query, ranked)
        context_tokens = ContextSerializer.estimate_tokens(context)

        prov = ProvenanceRecord.create(
            query=query,
            results=ranked,
            context_tokens=context_tokens,
            metadata=metadata,
        )
        self._ledger.append(prov)

        return RetrievalResult(
            query=query,
            ranked=ranked,
            context=context,
            provenance=prov,
        )

    # --- context assembly ---------------------------------------------------

    def _build_context(self, query: str, ranked: List[RankedResult]) -> str:
        """Convert ranked results to NKG context block."""
        adapter = NKGContextAdapter(max_tokens=self._max_context_tokens)
        for r in ranked:
            priority = self._score_to_priority(r.score)
            node = NKGNodeSnapshot(
                node_id=r.doc_id,
                label=r.doc_id,
                content=r.text,
                priority=priority,
                metadata=r.metadata,
            )
            adapter.add_node(node)
        return adapter.build_context(compress=True)

    @staticmethod
    def _score_to_priority(score: float) -> PriorityLevel:
        """Map retrieval score to PriorityLevel."""
        if score >= 0.8:
            return PriorityLevel.CRITICAL
        if score >= 0.5:
            return PriorityLevel.HIGH
        if score >= 0.3:
            return PriorityLevel.MEDIUM
        if score >= 0.1:
            return PriorityLevel.LOW
        return PriorityLevel.BACKGROUND

    # --- ledger access ------------------------------------------------------

    @property
    def ledger(self) -> ProvenanceLedger:
        return self._ledger

    def stats(self) -> Dict[str, Any]:
        return {
            "indexed_docs": self._retriever.indexed_count,
            "top_k": self._top_k,
            "max_context_tokens": self._max_context_tokens,
            "retrievals_logged": self._ledger.count,
            "pipeline_version": PIPELINE_VERSION,
        }
