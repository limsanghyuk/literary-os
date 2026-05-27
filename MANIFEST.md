# MANIFEST — Literary OS V655

버전: 11.28.0
릴리즈일: 2026-05-27
빌드 타입: Phase C SP-C.2 완전 종료 — SuiteRegistrationGate G67 + HuggingFace 등록 준비 (V655, ADR-115)

## 테스트 결과

| 항목 | 값 |
|------|----|
| PASS | 8,053 |
| FAIL | 0 |
| SKIP | 2 (REAL LLM — API 키 없을 시) |
| 릴리즈 게이트 | **66/66 PASS** |
| SP-C.2 추가 TC | +246 (V648~V655 누적) |

## 릴리즈 게이트 현황

| Gate | 검증 항목 | 버전 | 상태 |
|------|-----------|------|------|
| G01~G28 | Phase 1~5 전체 | v1.0~v6.3 | ✅ PASS |
| G29~G52 | Phase A SP-A.1~SP-A.8 전체 | v7.0~v10.0 | ✅ PASS |
| G53 | LoRA Artifact Validation | v10.3.0 (V598) | ✅ PASS |
| G54 | FineTune E2E Pipeline | v10.5.0 (V600) | ✅ PASS |
| G55 | PPO Stability (KL≤0.05) | v10.8.0 (V603) | ✅ PASS |
| G56 | RLHF Reward (mean≥0.75) | v10.11.0 (V606) | ✅ PASS |
| G57 | Constitution Axis (Pearson≥0.80) | v10.11.0 (V606) | ✅ PASS |
| G58 | LoRA Stacking Adapter | v10.14.0 (V609) | ✅ PASS |
| G59 | SharedCharacterDB + SharedWorldDB | v10.17.0 (V612) | ✅ PASS |
| G60 | MultiWork Orchestration | v10.20.0 (V615) | ✅ PASS |
| G61 | Phase B Exit Gate (7축) | v11.0.0 (V630) | ✅ PASS |
| G62 | AutoPromotionGate (R≥0.78, 롤백=0) | v11.5.0 (V635) | ✅ PASS |
| G63 | SP-C.1 Exit Gate (5축) | v11.9.0 (V640) | ✅ PASS |
| G64 | AgentCoordinatorGate (SP-C.2) | v11.25.0 (V652) | ✅ PASS |
| G65 | EnsembleQualityGate (R≥0.83) | v11.26.0 (V653) | ✅ PASS |
| G66 | MAEMultiWorkGate (P95≤8.0초, 3작품) | v11.27.0 (V654) | ✅ PASS |
| G67 | SuiteRegistrationGate (SP-C.2 4조건) | v11.28.0 (V655) | ✅ PASS |

## SP-C.2 신규 모듈 (V646~V655)

| 버전 | 모듈 | 설명 | ADR |
|------|------|------|-----|
| V646 | `literary_system/agents/director_agent.py` | DirectorAgent + MicroPlanner (최상위 오케스트레이터) | ADR-106 |
| V647 | `literary_system/agents/script_agent.py` | ScriptAgent + LoRA InferenceGateway 직결 | ADR-107 |
| V648 | `literary_system/agents/critic_agent.py` | CriticAgent + CriticReport (PASS_THRESHOLD=0.65) | ADR-108 |
| V649 | `literary_system/agents/editor_agent.py` | EditorAgent + EditedScene + KoreanCadencePlanner | ADR-109 |
| V650 | `literary_system/agents/agent_coordinator.py` | AgentCoordinator + CoordinatorResult (max 3 round-trip) | ADR-110 |
| V651 | `literary_system/agents/ensemble_memory_cache.py` | EnsembleMemoryCache + TTL + 캐릭터 상태 공유 | ADR-111 |
| V652 | `literary_system/gates/evaluator_gate.py` | AgentEnsembleEvaluator G65 (R≥0.83) | ADR-112 |
| V653 | `literary_system/agents/agent_safety_guard.py` | AgentSafetyGuard + SafetyResult (5축 검증) | ADR-113 |
| V654 | `literary_system/ensemble/mae_multiwork_gate.py` | MAEMultiWorkGate G66 (3작품 동시 P95≤8초) | ADR-114 |
| V655 | `literary_system/ensemble/suite_registration_gate.py` | SuiteRegistrationGate G67 + ModelCardMetadata | ADR-115 |

## SP-C 진행 현황

| 서브페이즈 | 버전 범위 | 상태 |
|-----------|----------|------|
| SP-C.1 자기학습 엔진 | V631~V640 | ✅ 완료 (G62+G63, ADR-098~082) |
| SP-C.2 멀티에이전트 앙상블 | V646~V655 | ✅ **완료** (G64~G67, ADR-106~115) |
| SP-C.3 PublicSDK + 경쟁흡수 | V656~V665 | ⏳ 예정 |
| SP-C.4 Phase C Exit Gate | V666~V680 | ⏳ 예정 |

## 핵심 상수 (SP-C.2)

| 상수 | 값 | 용도 |
|------|----|------|
| `PASS_THRESHOLD` | 0.65 | CriticAgent 씬 통과 기준 |
| `MIN_ENSEMBLE_SCORE` | 0.83 | EnsembleQualityGate R 기준 |
| `P95_THRESHOLD_SEC` | 8.0 | MAEMultiWorkGate 레이턴시 상한 |
| `MAX_ROUNDS` | 3 | AgentCoordinator 최대 왕복 |
| `ATIA_MIN_SCORE` | 0.70 | SuiteRegistrationGate ATIA 기준 |
| `MIN_TEST_COUNT` | 500 | SuiteRegistrationGate TC 기준 |
| `MAX_WORKERS` | 4 | ThreadPoolExecutor (MAEMultiWorkGate) |
| `MIN_PROJECTS` | 3 | MAEMultiWorkGate 최소 동시 작품 수 |

## 파일 구조 (주요)

```
literary-os/
├── literary_system/
│   ├── agents/           ← SP-C.2 Agent Ensemble (V646~V653)
│   │   ├── director_agent.py
│   │   ├── script_agent.py
│   │   ├── critic_agent.py
│   │   ├── editor_agent.py
│   │   ├── agent_coordinator.py
│   │   ├── ensemble_memory_cache.py
│   │   └── agent_safety_guard.py
│   ├── ensemble/         ← SP-C.2 게이트 (V654~V655)
│   │   ├── mae_multiwork_gate.py
│   │   └── suite_registration_gate.py
│   └── gates/
│       ├── coordinator_gate.py   (G64)
│       ├── evaluator_gate.py     (G65)
│       └── release_gate.py       (66개 게이트 등록)
├── tests/unit/           ← 8053 TC
├── docs/adr/             ← ADR-106~115
└── tools/
    └── test_inventory.json  (8053 tests, source_hash 최신)
```
