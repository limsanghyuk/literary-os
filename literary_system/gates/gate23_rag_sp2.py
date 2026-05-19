"""Gate 23: RAG-LLM SP2 통합 생존 게이트 (V491)

SP2에서 신규 추가된 4개 모듈이 올바르게 임포트되고
핵심 인터페이스를 보유하는지 검증한다.

검증 대상:
  - RAGContextBuilder      (rag_context_builder.py)
  - CachedGateway          (cached_gateway.py)
  - TenantIsolationV2      (tenant_isolation_v2.py)
  - RAGPipelineOrchestrator(rag_pipeline_orchestrator.py)
"""

from __future__ import annotations


def _gate_rag_sp2_survival() -> dict:
    """SP2 핵심 4모듈 생존 검증."""
    symbols: list[str] = []
    errors: list[str] = []

    # ── 1. RAGContextBuilder ───────────────────────────────────────────
    try:
        from literary_system.rag.rag_context_builder import (
            DramaDocumentFactory,
            RAGContextBuilder,
            RAGEnrichedRequest,
            RetrievalProvenance,
        )
        assert callable(getattr(RAGContextBuilder, "build", None)), \
            "RAGContextBuilder.build() 누락"
        assert hasattr(RetrievalProvenance, "to_dict"), \
            "RetrievalProvenance.to_dict() 누락"
        assert hasattr(RAGEnrichedRequest, "has_context"), \
            "RAGEnrichedRequest.has_context 프로퍼티 누락"
        # DramaDocumentFactory 실제 메서드 검증
        assert callable(getattr(DramaDocumentFactory, "from_scene_text", None)), \
            "DramaDocumentFactory.from_scene_text() 누락"
        assert callable(getattr(DramaDocumentFactory, "from_character_profile", None)), \
            "DramaDocumentFactory.from_character_profile() 누락"
        symbols += [
            "RAGContextBuilder.build",
            "RetrievalProvenance.to_dict",
            "RAGEnrichedRequest.has_context",
            "DramaDocumentFactory.from_scene_text",
            "DramaDocumentFactory.from_character_profile",
        ]
    except Exception as exc:
        errors.append(f"RAGContextBuilder: {exc}")

    # ── 2. CachedGateway ──────────────────────────────────────────────
    try:
        from literary_system.llm_bridge.cached_gateway import (
            CachedGateway,
            CacheStats,
        )
        assert callable(getattr(CachedGateway, "call", None)), \
            "CachedGateway.call() 누락"
        assert callable(getattr(CachedGateway, "call_with_provenance", None)), \
            "CachedGateway.call_with_provenance() 누락"
        assert callable(getattr(CachedGateway, "make_cache_key", None)), \
            "CachedGateway.make_cache_key() 누락"
        assert hasattr(CacheStats, "hit_rate"), \
            "CacheStats.hit_rate 프로퍼티 누락"
        symbols += [
            "CachedGateway.call",
            "CachedGateway.call_with_provenance",
            "CachedGateway.make_cache_key",
            "CacheStats.hit_rate",
        ]
    except Exception as exc:
        errors.append(f"CachedGateway: {exc}")

    # ── 3. TenantIsolationV2 ──────────────────────────────────────────
    try:
        from literary_system.tenant.tenant_isolation_v2 import (
            DataHygieneFilter,
            DataHygieneViolation,
            KMSKeyManager,
            TenantIsolationV2,
            TenantRAGRegistry,
        )
        assert callable(getattr(TenantIsolationV2, "register_tenant", None)), \
            "TenantIsolationV2.register_tenant() 누락"
        assert callable(getattr(TenantIsolationV2, "verify_isolation", None)), \
            "TenantIsolationV2.verify_isolation() 누락"
        assert callable(getattr(TenantIsolationV2, "check_hygiene", None)), \
            "TenantIsolationV2.check_hygiene() 누락"
        assert callable(getattr(TenantRAGRegistry, "register", None)), \
            "TenantRAGRegistry.register() 누락"
        assert callable(getattr(DataHygieneFilter, "check", None)), \
            "DataHygieneFilter.check() 누락"
        assert callable(getattr(KMSKeyManager, "derive_key", None)), \
            "KMSKeyManager.derive_key() 누락"
        assert hasattr(DataHygieneViolation, "PII_DETECTED"), \
            "DataHygieneViolation.PII_DETECTED 누락"
        symbols += [
            "TenantIsolationV2.register_tenant",
            "TenantIsolationV2.verify_isolation",
            "TenantIsolationV2.check_hygiene",
            "TenantRAGRegistry.register",
            "DataHygieneFilter.check",
            "KMSKeyManager.derive_key",
            "DataHygieneViolation.PII_DETECTED",
        ]
    except Exception as exc:
        errors.append(f"TenantIsolationV2: {exc}")

    # ── 4. RAGPipelineOrchestrator ────────────────────────────────────
    try:
        from literary_system.pipelines.rag_pipeline_orchestrator import (
            RAGPipelineOrchestrator,
            RAGSceneResult,
            make_default_orchestrator,
        )
        assert callable(getattr(RAGPipelineOrchestrator, "generate", None)), \
            "RAGPipelineOrchestrator.generate() 누락"
        assert callable(make_default_orchestrator), \
            "make_default_orchestrator() 누락"
        # 인스턴스 생성 후 속성 확인 (dataclass)
        import datetime

        from literary_system.rag.rag_context_builder import RetrievalProvenance as RP
        p = RP(retrieved_doc_ids=["d1"], query="q",
                retrieval_ts=datetime.datetime.now())
        r = RAGSceneResult(
            scene_text="test", provenance=p, provider_id="test",
            latency_ms=1.0, cache_hit=False, enriched=False,
        )
        assert hasattr(r, "provenance"), "RAGSceneResult.provenance 필드 누락"
        assert hasattr(r, "cache_hit"),  "RAGSceneResult.cache_hit 필드 누락"
        symbols += [
            "RAGPipelineOrchestrator.generate",
            "make_default_orchestrator",
            "RAGSceneResult.provenance",
            "RAGSceneResult.cache_hit",
        ]
    except Exception as exc:
        errors.append(f"RAGPipelineOrchestrator: {exc}")

    # ── ADR-007 Provenance 계약 확인 ──────────────────────────────────
    try:
        import datetime

        from literary_system.rag.rag_context_builder import RetrievalProvenance
        p = RetrievalProvenance(
            retrieved_doc_ids=["d1", "d2"],
            query="test",
            retrieval_ts=datetime.datetime.now(),
        )
        d = p.to_dict()
        assert "retrieved_doc_ids" in d, "ADR-007: retrieved_doc_ids 키 누락"
        symbols.append("ADR-007:retrieved_doc_ids_in_to_dict")
    except Exception as exc:
        errors.append(f"ADR-007 provenance contract: {exc}")

    passed = len(errors) == 0
    return {
        "pass": passed,
        "symbols_verified": symbols,
        "count": len(symbols),
        "errors": errors,
        "adr": ["ADR-007 (RAG Provenance)", "ADR-008 (Data Hygiene)"],
    }
