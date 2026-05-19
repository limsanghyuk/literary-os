"""
V487 -- CachedGateway

UnifiedLLMGateway에 SemanticCacheRedis 레이어를 추가한 캐싱 래퍼.

캐시 키: SHA256(sorted_doc_ids + "|" + prompt + "|" + model_id)
         ADR-007 Provenance와 연동하여 retrieved_doc_ids를 키에 포함.
TTL: 24h (86400초)

설계:
  CachedGateway  -- UnifiedLLMGateway + SemanticCacheRedis 통합
                    call() 시 캐시 히트 → LLM 호출 없이 즉시 반환
                    캐시 미스 → 실제 LLM 호출 후 결과 저장
  CacheStats     -- 캐시 적중률·절약 비용 추적
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import List, Optional, Union

from literary_system.cost_cache.semantic_cache_redis import SemanticCacheRedis
from literary_system.llm_bridge.gateway.unified_llm_gateway import UnifiedLLMGateway
from literary_system.llm_bridge.llm_context import LLMContext, LLMResponse

# ---------------------------------------------------------------------------
# CacheStats
# ---------------------------------------------------------------------------

@dataclass
class CacheStats:
    hits:         int = 0
    misses:       int = 0
    total_calls:  int = 0
    saved_calls:  int = 0   # = hits (LLM 호출 절약 횟수)

    @property
    def hit_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.hits / self.total_calls

    def to_dict(self) -> dict:
        return {
            "hits":        self.hits,
            "misses":      self.misses,
            "total_calls": self.total_calls,
            "hit_rate":    round(self.hit_rate, 4),
            "saved_calls": self.saved_calls,
        }


# ---------------------------------------------------------------------------
# CachedGateway
# ---------------------------------------------------------------------------

class CachedGateway:
    """
    UnifiedLLMGateway + SemanticCacheRedis 통합 캐싱 래퍼.

    사용법:
        gw = UnifiedLLMGateway(...)
        cached = CachedGateway(gateway=gw)
        resp = cached.call(prompt, context, doc_ids=["doc1", "doc2"])
        # doc_ids = ADR-007 retrieved_doc_ids (RAGEnrichedRequest.provenance 에서 가져옴)
    """

    DEFAULT_TTL_S: int = 86_400   # 24h

    def __init__(
        self,
        gateway:    UnifiedLLMGateway,
        cache:      Optional[SemanticCacheRedis] = None,
        ttl_s:      int  = DEFAULT_TTL_S,
        enabled:    bool = True,
    ) -> None:
        self._gateway = gateway
        self._cache   = cache if cache is not None else SemanticCacheRedis(ttl_s=ttl_s)
        self._ttl_s   = ttl_s
        self._enabled = enabled
        self._stats   = CacheStats()

    # ------------------------------------------------------------------
    # 캐시 키 생성
    # ------------------------------------------------------------------

    @staticmethod
    def make_cache_key(
        prompt:   str,
        doc_ids:  List[str],
        model_id: str = "",
    ) -> str:
        """
        SHA256(sorted_doc_ids + "|" + prompt + "|" + model_id)
        ADR-007: doc_ids를 키에 포함하여 다른 문서 컨텍스트와 충돌 방지.
        """
        sorted_docs = "|".join(sorted(doc_ids))
        raw = f"{sorted_docs}|{prompt}|{model_id}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def call(
        self,
        prompt:   str,
        context:  Union[LLMContext, dict, None] = None,
        doc_ids:  Optional[List[str]] = None,
        model_id: str = "",
    ) -> LLMResponse:
        """
        캐시 우선 LLM 호출.

        Parameters
        ----------
        prompt   : LLM 프롬프트
        context  : LLMContext (또는 dict)
        doc_ids  : ADR-007 retrieved_doc_ids (캐시 키 차별화)
        model_id : 어댑터 모델 ID (선택, 캐시 키 차별화)
        """
        self._stats.total_calls += 1
        doc_ids = doc_ids or []

        if self._enabled:
            cache_key = self.make_cache_key(prompt, doc_ids, model_id)
            cached_text = self._cache.get(prompt=cache_key, model_id=model_id)
            if cached_text is not None:
                # 캐시 히트
                self._stats.hits += 1
                self._stats.saved_calls += 1
                return LLMResponse(
                    text=cached_text,
                    provider_id="cache",
                    latency_ms=0.0,
                    fallback_used=False,
                )

        # 캐시 미스 → 실제 LLM 호출
        self._stats.misses += 1
        resp = self._gateway.call(prompt=prompt, context=context)

        # 결과 캐시 저장
        if self._enabled and resp.text:
            cache_key = self.make_cache_key(prompt, doc_ids, model_id)
            self._cache.set(prompt=cache_key, model_id=model_id, response=resp.text)

        return resp

    def call_with_provenance(
        self,
        prompt:    str,
        context:   Union[LLMContext, dict, None] = None,
        doc_ids:   Optional[List[str]] = None,
        model_id:  str = "",
    ) -> tuple:
        """
        call() + (response, cache_hit) 튜플 반환.
        캐시 히트 여부를 명시적으로 알 수 있다.
        """
        pre_hits = self._stats.hits
        resp = self.call(prompt=prompt, context=context, doc_ids=doc_ids, model_id=model_id)
        cache_hit = self._stats.hits > pre_hits
        return resp, cache_hit

    # ------------------------------------------------------------------
    # 캐시 관리
    # ------------------------------------------------------------------

    def invalidate(self, prompt: str, doc_ids: List[str], model_id: str = "") -> None:
        """특정 캐시 엔트리 무효화."""
        cache_key = self.make_cache_key(prompt, doc_ids, model_id)
        self._cache.delete(key=cache_key)

    def clear(self) -> int:
        """전체 캐시 삭제 후 삭제된 엔트리 수 반환."""
        return self._cache.flush_tenant()

    # ------------------------------------------------------------------
    # 통계
    # ------------------------------------------------------------------

    @property
    def stats(self) -> CacheStats:
        return self._stats

    def reset_stats(self) -> None:
        self._stats = CacheStats()

    @property
    def gateway(self) -> UnifiedLLMGateway:
        return self._gateway

    @property
    def cache_enabled(self) -> bool:
        return self._enabled
