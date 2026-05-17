"""
V486 -- RAGContextBuilder

HybridRetriever + NKGContextAdapter → LLM 프롬프트 강화 + ADR-007 Provenance

ADR-007: 모든 RAG 응답에 retrieved doc IDs를 첨부한다.

설계:
  RAGContextBuilder  -- 씬 생성 요청에 대해 관련 문서를 검색하고 NKG 컨텍스트로
                        직렬화하여 LLM 프롬프트에 주입 가능한 형태로 반환.
  RAGEnrichedRequest -- 원본 프롬프트 + RAG 컨텍스트 + provenance IDs
  RetrievalProvenance -- ADR-007: doc_id 목록 + 검색 메타정보
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from literary_system.rag.hybrid_retriever import (
    BM25Retriever,
    DenseRetriever,
    HybridRetriever,
    RRFMerger,
    Document,
    RankedResult,
)
from literary_system.rag.qdrant_bridge import QdrantBridge
from literary_system.rag.nkg_context_adapter import (
    NKGContextAdapter,
    NKGNodeSnapshot,
    NKGEdgeSnapshot,
    PriorityLevel,
)


# ---------------------------------------------------------------------------
# ADR-007: Provenance
# ---------------------------------------------------------------------------

@dataclass
class RetrievalProvenance:
    """
    ADR-007 준수: 모든 RAG 응답에 첨부되는 출처 기록.
    retrieved_doc_ids 는 응답 직렬화 시 반드시 포함해야 한다.
    """
    retrieved_doc_ids: List[str]
    query:             str
    retrieval_ts:      float = field(default_factory=time.time)
    top_k_requested:   int   = 5
    total_found:       int   = 0
    retriever_version: str   = "hybrid-v2"
    metadata:          Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "retrieved_doc_ids": self.retrieved_doc_ids,
            "query":             self.query,
            "retrieval_ts":      self.retrieval_ts,
            "top_k_requested":   self.top_k_requested,
            "total_found":       self.total_found,
            "retriever_version": self.retriever_version,
            "metadata":          self.metadata,
        }

    @property
    def provenance_id(self) -> str:
        """SHA256 기반 고유 ID."""
        raw = "|".join(sorted(self.retrieved_doc_ids)) + self.query
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# RAGEnrichedRequest
# ---------------------------------------------------------------------------

@dataclass
class RAGEnrichedRequest:
    """
    원본 프롬프트에 RAG 컨텍스트를 주입한 강화 요청.
    provenance 는 ADR-007 필수 항목.
    """
    original_prompt:   str
    rag_context:       str                   # NKGContextAdapter 직렬화 결과
    enriched_prompt:   str                   # rag_context + original_prompt 조합
    provenance:        RetrievalProvenance
    ranked_results:    List[RankedResult] = field(default_factory=list)
    token_budget_used: int                = 0

    @property
    def has_context(self) -> bool:
        # NKGContextAdapter가 빈 노드일 때도 헤더/푸터를 반환하므로
        # 실제 내용이 있는지 확인
        stripped = self.rag_context.strip()
        if not stripped:
            return False
        # 헤더/푸터만 있는 경우 제외
        _EMPTY = "=== NKG CONTEXT ===" + chr(10) + "=== END NKG CONTEXT ==="
        return stripped != _EMPTY

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_prompt":     self.original_prompt,
            "rag_context_len":     len(self.rag_context),
            "enriched_prompt_len": len(self.enriched_prompt),
            "provenance":          self.provenance.to_dict(),
            "has_context":         self.has_context,
            "token_budget_used":   self.token_budget_used,
        }


# ---------------------------------------------------------------------------
# 팩토리: BM25 전용 HybridRetriever (Qdrant 없이 동작)
# ---------------------------------------------------------------------------

def _make_bm25_only_retriever() -> HybridRetriever:
    """
    Qdrant 없이 BM25만 사용하는 HybridRetriever.
    Dense 검색은 QdrantBridge의 인메모리 폴백으로 동작.
    """
    bm25 = BM25Retriever()
    bridge = QdrantBridge(fallback=True)   # 인메모리 폴백 (Qdrant 없이 동작)
    dense = DenseRetriever(bridge=bridge, collection="default_drama")
    return HybridRetriever(bm25=bm25, dense=dense, bm25_weight=0.7, dense_weight=0.3)


# ---------------------------------------------------------------------------
# RAGContextBuilder
# ---------------------------------------------------------------------------

class RAGContextBuilder:
    """
    HybridRetriever + NKGContextAdapter를 조합하여
    LLM 씬 생성 프롬프트에 주입 가능한 RAG 컨텍스트를 생성한다.

    사용법:
        builder = RAGContextBuilder()
        builder.index_documents(docs)
        enriched = builder.build(query="2화 3씬 갈등", prompt="씬을 써줘")
        # enriched.enriched_prompt → LLM 전달
        # enriched.provenance.retrieved_doc_ids → 응답에 첨부 (ADR-007)
    """

    CONTEXT_HEADER = (
        "=== 참고 문서 (RAG 검색 결과) ===\n"
        "아래 내용을 참고하여 씬을 생성하시오.\n\n"
    )
    CONTEXT_FOOTER = "\n=== 참고 문서 끝 ===\n\n"

    def __init__(
        self,
        retriever:      Optional[HybridRetriever] = None,
        token_budget:   int = 1500,  # NKGContextAdapter max_tokens
        top_k:          int = 5,
        min_score:      float = 0.0,
        include_header: bool = True,
    ) -> None:
        self._retriever    = retriever if retriever is not None else _make_bm25_only_retriever()
        self._token_budget = token_budget
        self._top_k        = top_k
        self._min_score    = min_score
        self._include_header = include_header

    # ------------------------------------------------------------------
    # 문서 인덱싱
    # ------------------------------------------------------------------

    def index_document(self, doc: Document) -> None:
        """HybridRetriever에 문서를 인덱싱한다."""
        self._retriever.index(doc)

    def index_documents(self, docs: List[Document]) -> None:
        """여러 문서를 일괄 인덱싱한다."""
        self._retriever.index_batch(docs)

    # ------------------------------------------------------------------
    # 핵심: build()
    # ------------------------------------------------------------------

    def build(
        self,
        query:       str,
        prompt:      str,
        extra_nodes: Optional[List[NKGNodeSnapshot]] = None,
        extra_edges: Optional[List[NKGEdgeSnapshot]] = None,
    ) -> RAGEnrichedRequest:
        """
        1. HybridRetriever로 query 관련 문서 top-k 검색
        2. 검색 결과를 NKGNodeSnapshot으로 변환
        3. NKGContextAdapter로 직렬화 + 토큰 압축
        4. enriched_prompt = CONTEXT_HEADER + rag_context + original_prompt
        5. ADR-007 provenance 첨부
        """
        # 1. 검색
        results: List[RankedResult] = self._retriever.search(
            query=query, top_k=self._top_k
        )
        results = [r for r in results if r.score >= self._min_score]
        doc_ids = [r.doc_id for r in results]

        # 2. NKGNodeSnapshot 변환
        nodes: List[NKGNodeSnapshot] = []
        for r in results:
            nodes.append(
                NKGNodeSnapshot(
                    node_id=r.doc_id,
                    label=r.metadata.get("label", r.doc_id),
                    content=r.text,
                    priority=self._score_to_priority(r.score, r.rank),
                    metadata={
                        "source": r.source,
                        "score":  r.score,
                        "rank":   r.rank,
                        **r.metadata,
                    },
                )
            )
        if extra_nodes:
            nodes.extend(extra_nodes)

        edges: List[NKGEdgeSnapshot] = extra_edges or []

        # 3. NKGContextAdapter 직렬화 + 압축
        adapter = NKGContextAdapter(max_tokens=self._token_budget)
        adapter.add_nodes(nodes)
        adapter.add_edges(edges)
        rag_context: str = adapter.build_context(compress=True)
        # 토큰 추정: 단어 수 기반
        token_used: int = len(rag_context.split())

        # 4. 프롬프트 조합 (빈 NKG 마커는 컨텍스트로 간주하지 않음)
        _nkg_empty = "=== NKG CONTEXT ===" + chr(10) + "=== END NKG CONTEXT ==="
        has_real_ctx = bool(rag_context.strip()) and rag_context.strip() != _nkg_empty
        if has_real_ctx and self._include_header:
            enriched = self.CONTEXT_HEADER + rag_context + self.CONTEXT_FOOTER + prompt
        elif has_real_ctx:
            enriched = rag_context + chr(10) + chr(10) + prompt
        else:
            enriched = prompt

        # 5. Provenance (ADR-007)
        provenance = RetrievalProvenance(
            retrieved_doc_ids=doc_ids,
            query=query,
            top_k_requested=self._top_k,
            total_found=len(results),
        )

        return RAGEnrichedRequest(
            original_prompt=prompt,
            rag_context=rag_context,
            enriched_prompt=enriched,
            provenance=provenance,
            ranked_results=results,
            token_budget_used=token_used,
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _score_to_priority(score: float, rank: int) -> PriorityLevel:
        if rank <= 1 or score >= 0.8:
            return PriorityLevel.CRITICAL
        if rank <= 2 or score >= 0.6:
            return PriorityLevel.HIGH
        if rank <= 3 or score >= 0.4:
            return PriorityLevel.MEDIUM
        if rank <= 4:
            return PriorityLevel.LOW
        return PriorityLevel.BACKGROUND

    @property
    def indexed_doc_count(self) -> int:
        return len(self._retriever._doc_store)


# ---------------------------------------------------------------------------
# DramaDocumentFactory
# ---------------------------------------------------------------------------

class DramaDocumentFactory:
    """드라마 씬·캐릭터·설정 데이터를 Document로 변환하는 편의 팩토리."""

    @staticmethod
    def from_scene_text(
        scene_id: str, text: str, episode: int = 0, scene_idx: int = 0, **meta: Any,
    ) -> Document:
        return Document(
            doc_id=scene_id, text=text,
            metadata={"type": "scene", "episode": episode, "scene_idx": scene_idx, **meta},
        )

    @staticmethod
    def from_character_profile(
        character_id: str, name: str, description: str, **meta: Any,
    ) -> Document:
        return Document(
            doc_id=character_id,
            text=f"캐릭터: {name}\n{description}",
            metadata={"type": "character", "name": name, **meta},
        )

    @staticmethod
    def from_setting(
        setting_id: str, name: str, description: str, **meta: Any,
    ) -> Document:
        return Document(
            doc_id=setting_id,
            text=f"배경: {name}\n{description}",
            metadata={"type": "setting", "name": name, **meta},
        )
