# Literary OS — 개발자 컨텍스트

## ⚠️ 개발 착수 전 필수 실행 (DEV_PROTOCOL_v2.0 §1)

```bash
# 반드시 이 명령을 실행한 뒤 결과를 확인하고 개발을 시작한다
python3 tools/gitnexus_analyze.py   # Step 1: 코드그래프 현황
python3 tools/run_release_gate.py   # Step 12: Gate 기준선 확인
```

> **전체 절차**: `docs/workflow/DEV_PROTOCOL_v2.0.md` 참조  
> Preflight 없이 착수한 커밋은 릴리즈 승인 대상이 아님.

---

## 빠른 시작

```bash
pip install -e ".[dev]"
pytest tests/ -q                         # → 5529+ passed
python -c "from literary_system.gates.release_gate import run_release_gate; r=run_release_gate(); print(r['summary'])"
# → {"pass": true, "gates_passed": 39, "total_gates": 39}
```

## 핵심 설계 원칙

**LLM-0** (ADR-015/031): `graph_intelligence/`, `predictive/`, `corpus/`, `multiwork/` — 외부 LLM 호출 0건. LLM은 산문 생성에만 선택적 호출.

**Thread-safety**: 모든 multiwork 클래스는 `threading.RLock` 사용.

**CIM 수식**: `W[i][j] = 1 − exp(−0.95 × count)`

**GenreTransfer 수식**: `transferred[k] = (1−α) × target[k] + α × source[k]`

## 버전 계보 (Phase별 요약)

| 버전 범위 | 핵심 추가 |
|-----------|-----------|
| V327~V400 | 코어 파이프라인, NKG, GDAP, LLMNodeRouter, Episode, FullSceneOrchestrator |
| V411~V480 | StudioAPI v2, OAuth, OTel, RAG, Compliance(SP3), FineTune(SP4), ScaleOps(SP5) |
| V481~V497 | Hotfix, EpisodeStructure, RealLLM어댑터, DramaEpisodeGenerator, TrainingData |
| V498~V525 | NIE v2.0 — PhysicsReward, CIM, SparseCIM, NIL루프, Gate25 |
| V526~V540 | GIG — NarrativeGraph, CodeDependencyGraph, PlanBuildProtocol, Gate26/27 |
| V541~V545 | ASD — NarrativeDebt, ArcConsistency, StoryDoctor, AutoRepair, Gate28 |
| V546~V555 | PNE — PNECore, DebtPredictor, PreemptiveGate, FeedbackLearner, Gate29 |
| V556~V560 | Corpus — ExternalCorpusBridge, BGEM3Embedder, CIMBootstrap, Gate30 |
| V562~V571 | MultiWork Stage C — 7모듈 + Gate31 |
| **V572~V581** | **LOSDB 기반 — SchemaRegistry + MigrationManager + ADR-040 (현재 최신)** |

## GitNexus 인덱스 현황 (V589 AST 분석 기준 — release_v589)

```
인덱스명:               release_v589
버전 기준:              v9.4.0 / 47 Gates / ADR-001~050
literary_system/ 서브패키지: 60개+
소스 파일 (non-test):   728개 (Python)

심볼(Symbols):        12,297개
  클래스:              2,207개
  메서드:              9,360개
  함수:                  545개
  테스트 함수:           185개

관계(Relationships):  21,237개
  IMPORTS:             3,552개
  USES:                5,651개
  CALLS:               12,034개

실행흐름(Exec Flows):  2,752개

[V588 신규] QueryInterface 심볼:  18개
[V589 신규] HealthMonitor 심볼:   102개 (BackendHealthMonitor, BackendCircuitState 등)

릴리즈 게이트:        47/47 PASS (G1~G48)
테스트:            5,760+ PASS
```

> GitNexus analyze는 `npx gitnexus analyze --force`로 재실행 가능 (완료에 ~60초 소요).  
> 샌드박스 환경 gitnexus NPM 설치 불가 시: `python3 tools/gitnexus_analyze.py` (python_fallback)

## literary_system 서브패키지 지도

```
literary_system/
├── db/               ← V581~V589 LOSDB 기반 레이어
│   ├── schema_registry.py      BackendType(SQL/Graph/Vector), SchemaVersion, SchemaRegistry (싱글턴)
│   ├── migration_manager.py    Migration, MigrationManager, BaseMigrationAdapter, SQL/Graph/VectorMigrationAdapter
│   ├── migration_engine.py     MigrationEngine, MigrationPlan, MigrationExecutionRecord (V583)
│   ├── sql_real_adapter.py     SQLiteRealAdapter, get_rows() (V582)
│   ├── vector_real_adapter.py  VectorRealAdapter, VectorRecord, JSON영속화 (V584)
│   ├── graph_real_adapter.py   GraphRealAdapter, GraphRecord, GraphEdgeRecord, JSON영속화 (V585)
│   ├── losdb_client.py         LOSDBClient Facade, LOSDBClientRecord, cross_query() (V586)
│   ├── query_interface.py      QueryInterface, SceneResult, CharacterResult, AggregateResult (V588, ADR-049)
│   ├── health_monitor.py       BackendHealthMonitor, AvailabilityState, BackendCircuitState (V589, ADR-050)
│   └── __init__.py             공개 API (전체 export)
│
├── multiwork/        ← V562~V571 신규 (MultiWork Stage C)
│   ├── multi_work_core.py          WorkStatus FSM, WorkProject, WorkSession, MultiWorkCore
│   ├── shared_character_db.py      RelationType(7), CharacterProfile, SharedCharacterDB
│   ├── shared_world_db.py          Location, Faction, TimelineEvent, LoreEntry, SharedWorldDB
│   ├── genre_transfer.py           GenreProfile, TransferRecord, GenreTransferLearning
│   ├── project_isolation.py        IsolationPolicy, AuditEntry, ProjectIsolationManager
│   ├── multi_work_cim.py           CIMEntry, ProjectCIM, MultiWorkCIM
│   ├── author_license_api.py       LicenseType(4), LicenseScope(5), AuthorLicenseAPI
│   └── multi_work_orchestrator.py  MultiWorkOrchestrator (7컴포넌트 통합)
│
├── predictive/       ← V551~V555 PNE
│   ├── pne_core.py           RepairOutcome, PatternLibrary, PNECore
│   ├── debt_predictor.py     DebtPrediction, PredictionReport, DebtPredictor
│   ├── preemptive_gate.py    PreemptiveGate (NIL Step6 사전차단)
│   └── feedback_learner.py   FeedbackLearner (F1 추적, 모델 재학습)
│
├── corpus/           ← V556~V560 ExternalCorpusBridge
│   ├── corpus_ingestor.py    CorpusIngestor
│   ├── bgem3_embedder.py     BGEM3Embedder (SHA-256 fallback, LLM-0 준수)
│   └── cim_bootstrap.py      CIMBootstrap (W = 1−exp(−0.95×count))
│
├── graph_intelligence/ ← V526~V545 GIG + ASD
│   ├── narrative_graph_store.py    NarrativeGraphStore
│   ├── narrative_impact_analyzer.py NarrativeImpactAnalyzer
│   ├── asd/
│   │   ├── auto_repair_executor.py   AutoRepairExecutor
│   │   └── story_doctor_orchestrator.py StoryDoctorOrchestrator
│   └── ...
│
├── nie/              ← V498~V525 NIE v2.0
│   ├── nil_orchestrator.py   NILOrchestrator
│   ├── physics_reward_bridge.py PhysicsRewardBridge
│   └── ...
│
├── llm_bridge/       ← 멀티어댑터 레이어
│   ├── gateway/unified_llm_gateway.py  UnifiedLLMGateway
│   ├── routing/task_router.py          TaskRouter
│   └── ...
│
├── drse/             DualSemanticScorer (DRSE 엔진)
├── gates/            release_gate.py (30-gate 오케스트레이터, V571)
├── compliance/       GDPRComplianceModule, EUAIActGovernance, PIIScannerV2
├── finetune/         FineTuneJobManager (LoRA), ProseStyleDataset, ModelEvalHarness
├── ops/              LoadBalancer(WRR), CircuitBreaker, ObservabilityStack
├── rag/              RAGContextBuilder, SemanticCacheLayer, RAGPipelineOrchestrator
├── physics/          NarrativePhysicsEngine, CIM, SparseCIM, PageRank
├── nkg/              NKGGraphStore, NKGSearchEngine (BM25+Vector RRF K=60)
└── ...
```

## Release Gate (30/30)

```bash
python -c "
from literary_system.gates.release_gate import run_release_gate
r = run_release_gate()
print(r['summary'])
"
# → RELEASE GATE PASS: 30/30 gates passed
```

| Gate | 담당 레이어 |
|------|------------|
| G01~G16 | 레거시 누적 (V327~V480) |
| G17 | Compliance (GDPR/EU AI Act) |
| G18~G20 | SP3/SP4/SP5 통합 |
| G21~G22 | Hotfix/EP구조 |
| G23 | RAG Pipeline |
| G24 | TrainingData (TraceQuality/PII) |
| G25 | NIL (NIE v2.0 통합) |
| G26~G27 | GIG (NarrativeGraph/CodeDependency) |
| G28 | ASD (StoryDoctor/AutoRepair) |
| G29 | PNE (DebtPredictor/PreemptiveGate) |
| G30 | Corpus (BGEM3/CIMBootstrap) |
| **G31** | **MultiWork Stage C (V571 최종)** |

## ADR 목록

| ADR | 결정 |
|-----|------|
| ADR-001~005 | 7-Layer / OAuth / OTel / TieredModel / TestPolicy |
| ADR-006~010 | Phase 2 SubPhase 1~4 아키텍처 |
| ADR-014 | SceneNecessity 정책 |
| ADR-015 | LLM-0 (외부 LLM 호출 금지 범위) |
| ADR-016~022 | NIE v2.0 (CIM/PageRank/NIL/MetaLearner/TIdeal) |
| ADR-023~025 | GIG (NarrativeGraph/CodeDep/PlanBuild) |
| ADR-027~031 | Phase 6 (Cleanup/PNE/Corpus/MultiWork/License) |

## MultiWork Stage C 주요 제약 (ADR-031)

- `PERSONAL`: max 3 프로젝트, `{GENERATE, EXPORT}` scope
- `COMMERCIAL`: max 10, `+MULTI_WORK, +API_ACCESS`
- `ENTERPRISE`: unlimited, 모든 scope
- `RESEARCH`: max 5, `+FINE_TUNE` (단, API_ACCESS 없음)
- `cross_project_read`: owner_id가 requester의 `allowed_projects` 화이트리스트에 있어야 허용

## 개발 시 필수 체크

```bash
# 1. 테스트
pytest tests/ -q

# 2. 릴리즈 게이트
python -c "from literary_system.gates.release_gate import run_release_gate; r=run_release_gate(); print(r['summary'])"

# 3. LLM-0 확인 (multiwork/ 추가 시)
grep -r "requests\|httpx\|openai\|anthropic" literary_system/multiwork/ --include="*.py"
# → 결과 0건이어야 함
```

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **release_v589** (12297 symbols, 21237 relationships, 2752 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/release_v589/context` | Codebase overview, check index freshness |
| `gitnexus://repo/release_v589/clusters` | All functional areas |
| `gitnexus://repo/release_v589/processes` | All execution flows |
| `gitnexus://repo/release_v589/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
