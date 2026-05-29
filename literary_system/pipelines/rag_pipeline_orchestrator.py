"""
V489 -- RAGPipelineOrchestrator

SceneGenerationPipeline ↔ RAG 완전 통합 오케스트레이터.

흐름:
  1. RAGContextBuilder.build(query, prompt) → RAGEnrichedRequest
  2. CachedGateway.call(enriched_prompt, doc_ids=provenance.retrieved_doc_ids)
     → LLMResponse (캐시 히트 시 LLM 호출 없음)
  3. 응답에 ADR-007 provenance 첨부
  4. TenantIsolationV2.check_hygiene() → 응답 품질 보장

설계:
  RAGPipelineOrchestrator -- 위 흐름을 단일 call() 메서드로 노출
  RAGSceneResult          -- 씬 텍스트 + provenance + 캐시 정보
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from literary_system.llm_bridge.cached_gateway import CachedGateway
from literary_system.llm_bridge.llm_context import LLMContext, LLMResponse
from literary_system.rag.hybrid_retriever import Document
from literary_system.rag.rag_context_builder import (
    DramaDocumentFactory,
    RAGContextBuilder,
    RAGEnrichedRequest,
    RetrievalProvenance,
)
from literary_system.tenant.tenant_isolation_v2 import HygieneResult, TenantIsolationV2

# ---------------------------------------------------------------------------
# 결과 데이터 모델
# ---------------------------------------------------------------------------

@dataclass
class RAGSceneResult:
    """
    RAGPipelineOrchestrator.generate() 결과.
    ADR-007: provenance 필드에 retrieved_doc_ids 항상 포함.
    """
    scene_text:   str
    provenance:   RetrievalProvenance
    provider_id:  str
    latency_ms:   float
    cache_hit:    bool
    enriched:     bool                 # RAG 컨텍스트 주입 여부
    hygiene:      Optional[HygieneResult] = None
    metadata:     Dict[str, Any]      = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_text_len":      len(self.scene_text),
            "provenance":          self.provenance.to_dict(),
            "provider_id":         self.provider_id,
            "latency_ms":          self.latency_ms,
            "cache_hit":           self.cache_hit,
            "enriched":            self.enriched,
            "hygiene_passed":      self.hygiene.passed if self.hygiene else None,
        }


# ---------------------------------------------------------------------------
# RAGPipelineOrchestrator
# ---------------------------------------------------------------------------

class RAGPipelineOrchestrator:
    """
    RAGContextBuilder + CachedGateway + TenantIsolationV2 통합 오케스트레이터.

    Literary OS에서 씬 생성 시 자동으로:
    - NKG/드라마 문서를 검색하여 프롬프트에 주입
    - 동일 요청은 캐시에서 즉시 반환 (비용 절약)
    - ADR-007: 모든 결과에 출처(provenance) 첨부
    - ADR-008: 출력 텍스트 품질·PII 필터

    사용법:
        orch = RAGPipelineOrchestrator(gateway=cached_gateway)
        orch.index_documents(drama_docs)
        result = orch.generate(
            query="2화 3씬 갈등",
            prompt="이준혁과 원장이 대립하는 씬을 써줘",
            tenant_id="studio_A",
        )
        # result.scene_text  → 생성된 씬 텍스트
        # result.provenance.retrieved_doc_ids  → ADR-007
    """

    def __init__(
        self,
        gateway:      CachedGateway,
        rag_builder:  Optional[RAGContextBuilder]   = None,
        tenant_iso:   Optional[TenantIsolationV2]   = None,
        top_k:        int   = 5,
        token_budget: int   = 1500,
        check_hygiene: bool = False,   # 출력 품질 필터 활성화 여부
    ) -> None:
        self._gateway     = gateway
        self._rag         = rag_builder or RAGContextBuilder(
            top_k=top_k, token_budget=token_budget
        )
        self._iso         = tenant_iso or TenantIsolationV2()
        self._check_hygiene = check_hygiene
        self._generate_count = 0
        self._cache_hit_count = 0

    # ------------------------------------------------------------------
    # 문서 인덱싱
    # ------------------------------------------------------------------

    def index_documents(self, docs: List[Document]) -> None:
        self._rag.index_documents(docs)

    def index_document(self, doc: Document) -> None:
        self._rag.index_document(doc)

    # ------------------------------------------------------------------
    # 핵심: generate()
    # ------------------------------------------------------------------

    def generate(
        self,
        query:     str,
        prompt:    str,
        context:   Union[LLMContext, dict, None] = None,
        tenant_id: str = "",
        model_id:  str = "",
    ) -> RAGSceneResult:
        """
        RAG-증강 씬 생성.

        1. RAGContextBuilder.build() → enriched prompt + provenance
        2. CachedGateway.call() (캐시 우선)
        3. ADR-007 provenance 첨부
        4. (선택) ADR-008 hygiene check
        """
        t0 = time.monotonic()

        # 1. RAG 컨텍스트 빌드
        enriched: RAGEnrichedRequest = self._rag.build(
            query=query,
            prompt=prompt,
        )

        # 2. 캐시 우선 LLM 호출
        resp, cache_hit = self._gateway.call_with_provenance(
            prompt=enriched.enriched_prompt,
            context=context,
            doc_ids=enriched.provenance.retrieved_doc_ids,
            model_id=model_id,
        )

        latency_ms = (time.monotonic() - t0) * 1000.0
        self._generate_count += 1
        if cache_hit:
            self._cache_hit_count += 1

        # 3. (선택) 출력 품질 필터
        hygiene: Optional[HygieneResult] = None
        if self._check_hygiene and resp.text:
            hygiene = self._iso.check_hygiene(resp.text)

        return RAGSceneResult(
            scene_text=resp.text,
            provenance=enriched.provenance,
            provider_id=resp.provider_id,
            latency_ms=round(latency_ms, 2),
            cache_hit=cache_hit,
            enriched=enriched.has_context,
            hygiene=hygiene,
            metadata={
                "query":              query,
                "tenant_id":          tenant_id,
                "token_budget_used":  enriched.token_budget_used,
                "ranked_count":       len(enriched.ranked_results),
            },
        )

    # ------------------------------------------------------------------
    # 통계
    # ------------------------------------------------------------------

    @property
    def generate_count(self) -> int:
        return self._generate_count

    @property
    def cache_hit_count(self) -> int:
        return self._cache_hit_count

    @property
    def cache_hit_rate(self) -> float:
        if self._generate_count == 0:
            return 0.0
        return self._cache_hit_count / self._generate_count

    def gateway_stats(self) -> Dict[str, Any]:
        return self._gateway.stats.to_dict()

    @property
    def indexed_doc_count(self) -> int:
        return self._rag.indexed_doc_count


# ---------------------------------------------------------------------------
# 팩토리: 기본 오케스트레이터 생성
# ---------------------------------------------------------------------------

def make_default_orchestrator(
    task_router=None,
    top_k: int = 5,
    token_budget: int = 1500,
) -> RAGPipelineOrchestrator:
    """
    UnifiedLLMGateway + CachedGateway + RAGContextBuilder 기본 조합.
    task_router=None 이면 Mock 모드.
    """
    from literary_system.llm_bridge.gateway.unified_llm_gateway import UnifiedLLMGateway
    from literary_system.llm_bridge.routing.task_router import TaskRouter

    if task_router is None:
        import os
        os.environ.setdefault("ANTHROPIC_API_KEY", "")
        task_router = TaskRouter.from_env()

    gw = UnifiedLLMGateway(task_router=task_router)
    cached_gw = CachedGateway(gateway=gw)
    return RAGPipelineOrchestrator(
        gateway=cached_gw,
        top_k=top_k,
        token_budget=token_budget,
    )
