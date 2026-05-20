# MANIFEST — Literary OS V587

버전: 9.2.0  
릴리즈일: 2026-05-20  
빌드 타입: V587 SP-α 릴리즈

## 테스트 결과

| 항목 | 값 |
|------|----|
| PASS | 5,897+ |
| FAIL | 0 |
| SKIP | 20 |
| 릴리즈 게이트 | 44/44 PASS |
| 테스트 파일 | 219개 |

## 패키지 구성

```
literary_system/
├── action_compiler/        # ActionPacket, SnapshotManager
├── adapters/               # SGO/BOO 어댑터
├── adapters_live/          # 실 LLM 연결 어댑터 (Claude/OpenAI/Ollama)
├── analyzer/               # 스토리 분석
├── arc/                    # ArcConsistency
├── billing/                # BillingEngine (Stripe + 토스페이먼츠)
├── causal/                 # CausalPlotGraph
├── corpus/                 # 외부 코퍼스 브릿지 (V557~V561)
├── db/                     # LOSDB Phase A~C (V581~V586)
│   ├── schema_registry.py  # SchemaRegistry — 3-백엔드 스키마 버전 관리
│   ├── migration_manager.py # MigrationManager + SQL/Graph/Vector 어댑터
│   ├── migration_engine.py  # MigrationEngine 통합 오케스트레이터 (V583)
│   ├── sql_real_adapter.py  # SQLiteRealAdapter — sqlite3 REAL 구현 (V582)
│   ├── vector_real_adapter.py # VectorRealAdapter — numpy-optional (V584)
│   ├── graph_real_adapter.py  # GraphRealAdapter — networkx-optional (V585)
│   ├── losdb_client.py      # LOSDBClient Facade + cross_query (V586)
│   ├── cli.py              # LOSDB CLI — status/analyze/migrate/health (V583)
│   └── __init__.py         # 공개 API
├── drse/                   # DRSE 점수 산정
├── gates/                  # Release Gate 시스템 (G1~G45)
│   ├── release_gate.py     # 44개 게이트 오케스트레이터
│   └── gate_registry.py    # GateRegistryEntry + GATE_REGISTRY 단일 소스
├── graph_intelligence/     # NKG, 감정 링커, 지식 그래프 (LLM-0)
├── llm_bridge/             # CanonicalLLMBridge (ADR-034~035)
├── longform/               # Fractal Plot Tree
├── multiwork/              # 다중작품 관리 (V562~V571)
├── nie/                    # NIE L7 컨테이너
├── orchestrators/          # 장편 오케스트레이터
├── predictive/             # PNE 예측 엔진 (V551~V555)
├── tenant/                 # 멀티테넌트 관리
└── ...                     # 65개 서브패키지 합계
```

## Gate 목록 (G1~G45)

| Gate | ID | Layer | ADR | 버전 추가 |
|------|----|-------|-----|---------|
| G1 | graph_nodes_g1 | L1 | ADR-023 | V400 |
| G2 | llm_zero_g2 | L1 | ADR-031 | V400 |
| G3 | gate_hierarchy_g3 | L1 | ADR-028 | V548 |
| G4 | nil_stability_g4 | L2 | ADR-019 | V400 |
| G5 | physics_reward_g5 | L2 | ADR-015 | V400 |
| G6 | meta_learner_g6 | L2 | ADR-020 | V400 |
| G7 | temporal_cim_g7 | L2 | ADR-021 | V400 |
| G8 | scene_necessity_g8 | L2 | ADR-014 | V400 |
| G9 | studio_api_g9 | L3 | ADR-006 | V430 |
| G10 | cost_ledger_g10 | L3 | — | V430 |
| G11 | llm_context_g11 | L3 | — | V431 |
| G12 | retrieval_pipeline_g12 | L3 | ADR-007 | V440 |
| G13 | data_rights_g13 | L3 | — | V442 |
| G14 | trace_quality_g14 | L3 | ADR-008 | V445 |
| G15 | live_adapter_g15 | L3 | — | V455 |
| G16 | dr_controller_g16 | L3 | ADR-018 | V461 |
| G17 | sub1_adapter_survival_g17 | L3 | — | V456 |
| G18 | graph_sync_g18 | L2 | ADR-027 | V546 |
| G19 | nil_pbp_g19 | L2 | ADR-029 | V547 |
| G20 | auto_repair_g20 | L2 | ADR-030 | V547 |
| G21 | llm0_static_g21 | L1 | ADR-031 | V548 |
| G22 | corpus_pipeline_g22 | L2 | — | V560 |
| G23 | multi_work_g23 | L2 | — | V571 |
| G24 | graph_nexus_g24 | L2 | ADR-023 | V556 |
| G25 | graph_sync_v2_g25 | L2 | ADR-027 | V546 |
| G26 | predictive_g26 | L2 | — | V555 |
| G27 | tenant_manager_g27 | L3 | ADR-011 | V457 |
| G28 | billing_engine_g28 | L3 | ADR-012 | V459 |
| G29 | compliance_g29 | L3 | — | V465 |
| G30 | finetune_g30 | L3 | ADR-008 | V469 |
| G31 | dev_mode_g31 | L1 | ADR-034 | V575 |
| G32 | logging_discipline_g32 | L1 | ADR-034 | V576 |
| G33 | schema_roundtrip_g33 | L1 | ADR-034 | V576 |
| G34 | auth_regression_g34 | L1 | ADR-034 | V576 |
| G35 | adapter_canonical_g35 | L1 | ADR-035 | V577 |
| G36 | gate_registry_g36 | L1 | ADR-032 | V578 |
| G37 | duplicate_zero_g37 | L1 | ADR-033 | V579 |
| G38 | async_discipline_g38 | L1 | ADR-036 | V580 |
| G39 | performance_baseline_g39 | L1 | ADR-039 | V580 |
| G40 | db_migration_g40 | L1 | ADR-040 | V581 |
| G41 | sql_real_adapter_g41 | L1 | ADR-041 | V582 |
| G42 | migration_engine_g42 | L1 | ADR-042 | V583 |
| G43 | vector_real_adapter_g43 | L1 | ADR-043 | V584 |
| G44 | graph_real_adapter_g44 | L1 | ADR-044 | V585 |
| G45 | losdb_client_g45 | L1 | ADR-045 | **V586** |

## 핵심 불변 원칙

| 원칙 | 내용 |
|------|------|
| LLM-0 | graph_intelligence/, predictive/, corpus/, multiwork/ — 외부 LLM 호출 0건 |
| DEV_MODE | 기본값 항상 "false" (ADR-034 보안 패치) |
| Preflight | 15단계 — 모든 버전 진입 전 필수 |

## 핵심 심볼 현황

| 분류 | 수 |
|------|----|
| 서브패키지 | 65 |
| 소스 파일 (.py) | 362+ |
| 테스트 파일 | 219 |
| ADR 문서 파일 | 45 (docs/adr/) |
| 게이트 등록 | 44/44 (G1~G45) |

## LOSDB Phase 완료 현황

| 레이어 | Mock | REAL |
|--------|------|------|
| SQL | V581 ✅ | V582 ✅ |
| Vector | V581 ✅ | V584 ✅ |
| Graph | V581 ✅ | V585 ✅ |
| Facade | — | V586 ✅ |

## 버전 이력 (V575~V586)

| 버전 | 주요 내용 | Gate |
|------|----------|------|
| V575 | DEV_MODE 보안 패치 + logging 전환 | G31 |
| V576 | 테스트 강화 + 커버리지 게이트 | G32~G34 |
| V577 | LLM 어댑터 캐노니컬 통합 | G35 |
| V578 | GATE_REGISTRY 단일소스 + ADR 자동 추출 | G36 |
| V579 | 중복 클래스 해소 | G37 |
| V580 | AsyncDiscipline + PerformanceBaseline | G38~G39 |
| V581 | LOSDB Phase A — SchemaRegistry + MigrationManager | G40 |
| V582 | LOSDB Phase B — SQLiteRealAdapter REAL | G41 |
| V583 | LOSDB Phase B — MigrationEngine 통합 오케스트레이터 | G42 |
| V584 | LOSDB Phase B — VectorRealAdapter (numpy-optional) | G43 |
| V585 | LOSDB Phase B — GraphRealAdapter (networkx-optional) | G44 |
| **V586** | **LOSDB Phase C — LOSDBClient Facade + cross_query** | **G45** |

---

*생성: V586 (2026-05-20) — 이전 MANIFEST_V581 대체*
