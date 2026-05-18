# Literary OS V481 — Hotfix Manifest

**버전:** V481  
**릴리즈 유형:** Hotfix  
**기준선:** V480 (literary_os_v480_FINAL2.zip)  
**릴리즈 일자:** 2026-05-16  
**패키지:** `literary_os_v481_HOTFIX.zip`

---

## 릴리즈 요약

| 항목 | 값 |
|------|---|
| 수정 버그 | 4개 클러스터 (H4/H5/H6/H7) |
| 인프라 정비 | 4건 (H1/H2/H3/OTel) |
| 테스트 결과 | 4452 PASS / 0 FAIL / 18 SKIP |
| Python 호환 | 3.10+ |
| 파일 크기 | ~13 MB |

---

## Hotfix 체크리스트

| ID | 항목 | 상태 |
|----|------|------|
| H1 | pyproject.toml version 4.8.0 → 4.8.1 | ✅ DONE |
| H2 | tests/ 디렉토리 zip 패키징 포함 확인 | ✅ DONE |
| H3 | manifests/live_core_manifest.json V481 갱신 | ✅ DONE |
| H4 | ProviderHealthMonitor._do_check return ok 추가 | ✅ DONE |
| H5 | TaskRouter._is_tier_healthy get_provider_id() 방식 ADR 확정 | ✅ DONE |
| H6 | make_default_gateway() return UnifiedLLMGateway(...) 추가 | ✅ DONE |
| H7 | LLMNodeRouter.stats() public API 추가 | ✅ DONE |
| —  | OTel teardown I/O 오류 수정 | ✅ DONE |
| —  | CHANGELOG_V481.md 작성 | ✅ DONE |
| —  | MANIFEST_V481_HOTFIX.md 작성 | ✅ DONE |

---

## 핵심 모듈 목록 (V481 기준)

### LLM Bridge 레이어
- `literary_system.llm_bridge.gateway.unified_llm_gateway` — UnifiedLLMGateway + make_default_gateway (H6 수정)
- `literary_system.llm_bridge.routing.task_router` — TaskRouter (H5 ADR 확정)
- `literary_system.llm_bridge.health.provider_health_monitor` — ProviderHealthMonitor (H4 수정)
- `literary_system.llm_bridge.llm_node_router` — LLMNodeRouter (H7 stats 추가)
- `literary_system.llm_bridge.physics_aware_router` — PhysicsAwareRouter
- `literary_system.llm_bridge.resilience` — ResilienceWrapper

### Compliance 레이어 (SP3)
- `literary_system.compliance.gdpr_module` — GDPRComplianceModule
- `literary_system.compliance.pii_scrubber` — PIIScrubber
- `literary_system.compliance.audit_trail` — AuditTrailDB
- `literary_system.compliance.cross_border_api` — CrossBorderTransferAPI
- `literary_system.compliance.deletion_cascade` — DeletionCascade

### SLM / FineTune 레이어 (SP4)
- `literary_system.slm.fine_tune_job_manager` — FineTuneJobManager
- `literary_system.slm.prose_style_dataset` — ProseStyleDataset
- `literary_system.slm.model_eval_harness` — ModelEvalHarness
- `literary_system.slm.safety_regression_suite` — SafetyRegressionSuite
- `literary_system.slm.dataset_builder_v443` — DatasetBuilderV443

### Ops / Scale 레이어 (SP5)
- `literary_system.ops.load_balancer` — LoadBalancer (WRR-Cost)
- `literary_system.ops.circuit_breaker` — CircuitBreaker
- `literary_system.ops.observability_stack` — ObservabilityStack
- `literary_system.billing.billing_engine` — BillingEngine

### Studio API
- `apps.studio_api.main` — StudioAPI (FastAPI)
- `apps.studio_api.otel.setup` — OTel 초기화 (teardown 수정)

---

## 알려진 제한사항

| 항목 | 내용 |
|------|------|
| SKIP 18개 | OTel OTLP exporter, live Stripe endpoint — 외부 서비스 의존, 기능 무관 |
| 실 LLM 연결 | V482~V485 Phase 1에서 ANTHROPIC_API_KEY 연동 예정 |
| Studio UI | React v1 골격만 존재, V485에서 완성 예정 |

---

## 다음 단계 (V482 Phase 1)

- `EpisodeStructureCalculator` — K dynamic calculation (60분 1화 구조)
- `SceneNecessityChecker` — ADR-014 구현
- 실 LLM 연결 (ANTHROPIC_API_KEY + Ollama)
- 60분 드라마 5화 생성 + 전문가 블라인드 평가

**LITERARY OS V481 HOTFIX — RELEASED**  
4452 PASSED / 0 FAILED — 2026-05-16
