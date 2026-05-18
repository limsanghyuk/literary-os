# CHANGELOG — V491 (Literary OS Phase 2 SP2 완료)

**릴리즈 일자:** 2026-05-16  
**버전:** 4.9.1  
**단계:** Phase 2 SP2 — RAG 통합 레이어

---

## SP2 신규 모듈 (V486~V491)

### V486 — RAGContextBuilder
- `literary_system/rag/rag_context_builder.py`
- `RAGContextBuilder`: HybridRetriever + NKGContextAdapter → LLM 프롬프트 주입
- `RetrievalProvenance`: ADR-007 준수 — 모든 응답에 `retrieved_doc_ids` 첨부
- `RAGEnrichedRequest`: `has_context` 프로퍼티 — NKG 빈 마커 자동 감지
- `DramaDocumentFactory`: `from_scene_text` / `from_character_profile` / `from_setting`
- 테스트: `tests/test_v486_rag_context_builder.py` (20 PASS)

### V487 — CachedGateway (SemanticCache Layer)
- `literary_system/llm_bridge/cached_gateway.py`
- SHA-256 캐시 키: `sorted(doc_ids) + "|" + prompt + "|" + model_id`
- TTL 24h, `CacheStats.hit_rate` 프로퍼티
- `call_with_provenance()` → `(LLMResponse, cache_hit: bool)` 반환
- 테스트: `tests/test_v487_cached_gateway.py` (18 PASS)

### V488 — TenantIsolationV2
- `literary_system/tenant/tenant_isolation_v2.py`
- `KMSKeyManager`: HMAC-SHA256 키 파생, 30일 롤링 로테이션
- `DataHygieneFilter`: PII / 품질 / 옵트인 / 라이선스 4단 검증 (ADR-008)
- `TenantRAGRegistry`: 테넌트별 컬렉션 격리 (`t_{md5[:8]}`)
- 테스트: `tests/test_v488_tenant_isolation_v2.py` (22 PASS)

### V489 — RAGPipelineOrchestrator
- `literary_system/pipelines/rag_pipeline_orchestrator.py`
- `RAGPipelineOrchestrator.generate()`: RAGContextBuilder → CachedGateway → Provenance 첨부
- `RAGSceneResult`: scene_text / provenance / cache_hit / enriched / hygiene
- `make_default_orchestrator()` 팩토리
- 테스트: `tests/test_v489_rag_pipeline_orchestrator.py` (14 PASS)

### V490 — Gate 23 (SP2 통합 릴리즈 게이트)
- `literary_system/gates/gate23_rag_sp2.py`
- 4개 모듈 × 21개 심볼 생존 검증
- ADR-007 Provenance 계약 검증 포함
- `release_gate.py` GATES 리스트 등록 (Gate 23)

### V491 — SP2 통합 패키징
- `pyproject.toml` version 4.9.1
- 전체 회귀: **4669 PASS / 20 SKIP**
- `literary_os_v491_SP2.zip` 배포

---

## 버그픽스 / 설계 수정

| 항목 | 내용 |
|------|------|
| NKG 빈 마커 | `NKGContextAdapter` 빈 출력 `"=== NKG CONTEXT ===\n=== END NKG CONTEXT ==="` 정상 감지 |
| HybridRetriever API | 필수 positional args `bm25 + dense` 정확히 전달 |
| QdrantBridge fallback | `QdrantBridge(fallback=True)` 인메모리 폴백 사용 |
| CachedGateway.clear() | `SemanticCacheRedis.flush_tenant()` 올바른 API 사용 |
| LLMResponse import | `llm_context` 모듈에서 정확히 임포트 |
| 버전 허용 목록 | 5개 통합 테스트 파일에 `"V491"` 추가 |

---

## ADR 준수 현황

| ADR | 제목 | 상태 |
|-----|------|------|
| ADR-006 | ModelLifecycle | ✅ SP1 완료 |
| ADR-007 | RAG Provenance | ✅ V486 RetrievalProvenance.to_dict() |
| ADR-008 | Data Hygiene | ✅ V488 DataHygieneFilter 4단 검증 |
| ADR-009 | LLM-as-Judge Calibration | 🔜 SP4 대상 |
| ADR-010 | Graceful Degradation | 🔜 SP4 대상 |

---

## 다음 단계 — SP3 (V492~V497)

SLM 수출 레이어: TraceQualityFilter + PIIScrubber + DatasetCardGenerator + SyntheticAugmentor
