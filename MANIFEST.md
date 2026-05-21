# MANIFEST — Literary OS V596

버전: 10.0.3  
릴리즈일: 2026-05-21  
빌드 타입: Phase A Final — Release Authority Finalization

## 테스트 결과

| 항목 | 값 |
|------|----|
| PASS | 6,179+ |
| FAIL | 0 |
| SKIP | 1 |
| 릴리즈 게이트 | **51/51 PASS** |
| 신규 테스트 | V595 기준 +40 (TC01~TC40) |

## Phase A 완료 릴리즈 게이트 현황

| Gate | 검증 항목 | 버전 | 상태 |
|------|-----------|------|------|
| G01~G46 | 기존 V581~V587 게이트 | — | ✅ 전체 PASS |
| G47 | QueryInterface + Qdrant | V588 | ✅ PASS |
| G48 | BackendHealthMonitor + HybridRetrieverV2 | V589 | ✅ PASS |
| G49 | GPUAdapterContract + CostSLO | V590 | ✅ PASS |
| G50 | EquivalenceTester 5축 + 골든셋20 | V591 | ✅ PASS |
| G51 | LOSConstitution v1.0 (5축 가중합) | V594 | ✅ PASS |
| G52 | Phase A Exit Gate (EA-1~EA-6) | V595 | ✅ PASS |
| **합계** | | | **51/51 ALL PASS** |

## V595.2 신규 산출물

| 파일 | 유형 | 설명 |
|------|------|------|
| tools/generate_test_inventory.py | 신규 | pytest 수집 결과 JSON 생성 도구 |
| tools/test_inventory.json | 신규 | EA-6용 테스트 수집 인벤토리 |
| literary_system/db/losdb_client.py | 수정 | private field 접근 제거 |
| literary_system/db/vector_real_adapter.py | 수정 | query_by_label() 공개 API 추가 |
| literary_system/db/graph_real_adapter.py | 수정 | query_nodes_by_label() 공개 API 추가 |
| literary_system/db/sql_real_adapter.py | 수정 | migration executescript() 교체 |
| literary_system/gates/phase_a_exit_gate.py | 수정 | EA-6 test_inventory.json 읽기 방식 |
| tests/e2e/test_e2e_prose.py | 수정 | requires_real_llm skipif 마커 |
| tools/check_version_consistency.py | 수정 | README H1/pyproject desc 검사 추가 |

## V595.1 Integrity Hotfix 산출물 (12건)

| 파일 | 수정 내용 |
|------|-----------|
| literary_system/gates/phase_a_exit_gate.py | G32 print() → sys.stdout.write |
| literary_system/db/graph_real_adapter.py | unknown op ValueError + snapshot rollback |
| literary_system/db/health_monitor.py | last_check_ok 필드 + is_available() 강화 |
| apps/cli/literary_cli.py | sc%4 → (sc-1)%4 오프셋 수정 |
| literary_system/constitution/los_constitution.py | 빈 텍스트 가드 + _score_arc 위치기반 |
| literary_system/corpus/corpus_pii_filter.py | dataclasses.replace() 불변성 |
| literary_system/corpus/corpus_validator.py | DRSE 마커 10개 + MinHash MD5 |
| literary_system/gates/e2e_prose_gate.py | CP-6 첫 씬 100~500자 |
| literary_system/db/sql_real_adapter.py | _quote_identifier() SQL injection 방지 |

## 아키텍처 제약 (변경 불가)

- **LLM-0**: corpus/, constitution/, finetune/ 외부 LLM 호출 금지
- **DEV_MODE**: 기본값 항상 `"false"` (ADR-034)
- **Preflight**: 15단계 체크 모든 버전 진입 전 필수
