# CHANGELOG — V623 (v10.28.0)

**Release Date:** 2026-05-25  
**Base Version:** V622 (v10.27.0, 6,861 TC)  
**Release Version:** v10.28.0  
**TC Delta:** +40 (6,901 TC)

---

## Summary

V623: G37 DuplicateZero 해소 + G61 Phase B Exit Gate PASS 달성 (60/60).
SP-B.2/B.3 retrofit 통합 E2E 39 TC + ADR-090.

---

## Changes

### Bug Fixes

#### G37 RoutingPolicy 중복 해소 (Critical)
- `agent_envelope.py` `RoutingPolicy` dataclass → `AgentRoutingPolicy`로 rename
- `llm_node_router.py` `RoutingPolicy(str, Enum)` — 기존 3축 라우팅 열거형 단독 소유 유지
- `canonical_bridge_v2.py` + `test_v621_sp_b2_retrofit.py` 모두 `AgentRoutingPolicy` 참조 업데이트
- 연쇄 효과: G37 PASS → passed_count(59)+1=60 ≥ MIN_GATES(60) → **G61 C5 PASS → 60/60 달성**

### New Features

#### SystemIntegrationTest 확장 (tests/integration/test_system_integration.py)
4개 TC 클래스 신규 (+39 TC):

| 클래스 | TC | 검증 내용 |
|--------|----|-----------|
| TestV621AgentEnvelopeIntegration | 10 | AgentEnvelope/AgentRoutingPolicy/CanonicalBridge E2E |
| TestV622SPB3RetrofitIntegration | 13 | ConflictPolicy/WorkloadProfile/AdvSeed/RewardModelV2 E2E |
| TestHelmPreValidation | 7 | Chart.yaml/values.yaml 위생 + helm lint/dry-run |
| TestV623CrossComponentIntegration | 9 | V621+V622 크로스 컴포넌트 통합 |

#### ADR-090: V623 SystemIntegrationTest + Helm 사전 검증
- RoutingPolicy 중복 해소 결정 기록
- Helm 사전 검증 전략 (파일시스템 항상 실행 / helm CLI skip if 미설치)
- LLM-0 원칙 준수 확인 (모든 테스트 MOCK 모드)

### Tests

| Suite | PASS | SKIP | FAIL |
|-------|------|------|------|
| unit | 701 | 0 | 0 |
| integration | 69 | 2 | 0 |
| e2e | 3 | 5 | 0 |
| **Total** | **773** | **7** | **0** |

**Total TC (inventory):** 6,901  
**Release Gate:** 60/60 PASS ✅  
**G37 DuplicateZero:** PASS (중복 0건)  
**G61 Phase B Exit Gate:** PASS (60/60 C5 달성)
