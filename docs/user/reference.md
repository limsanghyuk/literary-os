# Literary OS — Gate & ADR 레퍼런스 (v9.2.0)

자동 생성 기준일: 2026-05-20 (gen_cli_reference.py)

---

## Release Gate 목록 (45개)

| Gate ID | 설명 |
|---------|------|
| `llm_zero` | LLM-0 외부 호출 금지 |
| `arc_integrity` | SeriesArcPlanner 4막 비율 |
| `reveal_budget` | RevealBudget BLOCK 게이트 |
| `knowledge_leakage` | READER_ONLY 누수 방지 |
| `packaging` | cli_entry 패키징 무결성 |
| `pipeline_survival` | 파이프라인 핵심 로직 생존 |
| `drse_quality` | DRSE Dual Score 품질 검증 |
| `llm_adapter_contract` | LLM 어댑터 계약 검증 (Gate 10) |
| `studio_api_contract` | Studio API 라우터-엔드포인트 계약 |
| `rag_stack_survival` | RAG 스택 핵심 모듈 생존 (Gate 12) |
| `slm_subphase3_survival` | SLM SubPhase 3 모듈 생존 (Gate 13) |
| `quality_subphase4_survival` | Quality SubPhase 4 모듈 생존 (Gate 14) |
| `live_adapter_sp1` | Live Adapter SP1 골든셋 50개 회귀 (Gate 15) |
| `sp2_tenant_survival` | SP2 멀티테넌트·결제·DR 생존 (Gate 16) |
| `subphase1_adapter_survival` | SubPhase1 Adapter Layer 생존 (Gate 17) |
| `sp3_compliance_sovereignty` | SP3 Compliance·Governance·DataSovereignty (Gate 18) |
| `sp4_finetune_lora_poc` | SP4 FineTune LoRA POC (Gate 19) |
| `sp5_ops_survival` | SP5 Ops 레이어 생존 (Gate 20) |
| `scene_pipeline_survival` | SceneGenerationPipeline + LLM Adapter Layer (Gate 21) |
| `drama_generator_survival` | DramaEpisodeGenerator Mock 모드 생존 (Gate 22) |
| `rag_sp2_integration` | RAG-LLM SP2 통합 생존 (Gate 23) |
| `slm_sp3_integration` | SP3 SLM 수출 레이어 생존 (Gate 24) |
| `nie_convergence_gate25` | NIE 수렴 게이트 (Gate 25, L2) |
| `narrative_blast_gate26` | NarrativeGraph Blast Radius 게이트 (Gate 26, L3) |
| `code_coupling_gate27` | CodeCoupling 게이트 (Gate 27, L3) |
| `story_quality_gate28` | StoryQualityGate ASD 품질 (Gate 28, L4) |
| `llm0_static_analysis` | graph_intelligence LLM-0 정적 분석 (ADR-031) |
| `pne_convergence_gate29` | PNE 통합 게이트 (Gate 29, L2) |
| `corpus_quality_gate30` | ExternalCorpusBridge 게이트 (Gate 30, L2) |
| `multiwork_gate31` | MultiWork Stage C 게이트 (Gate 31, L3) |
| `logging_discipline_g32` | LoggingDiscipline: print()·bare-except 금지 (Gate 32, ADR-034) |
| `schema_roundtrip_g33` | SchemaRoundTrip: 직렬화/역직렬화 무결성 (Gate 33, ADR-034) |
| `auth_regression_g34` | AuthRegression: DEV_MODE 기본값=false 회귀 방지 (Gate 34, ADR-034) |
| `adapter_canonical_g35` | AdapterCanonical: G3 캐노니컬 어댑터 체계 검증 (Gate 35, ADR-035) |
| `gate_registry_g36` | GateRegistry: 레지스트리 단일 소스 무결성 (Gate 36, ADR-032) |
| `duplicate_zero_g37` | DuplicateZero: literary_system 중복 클래스명 0건 (Gate 37) |
| `async_discipline_g38` | AsyncDiscipline: deprecated async 패턴 0건 (Gate 38, ADR-036) |
| `performance_baseline_g39` | PerformanceBaseline: 핵심 연산 성능 회귀 방지 (Gate 39, ADR-039) |
| `db_migration_g40` | DBMigration: SchemaRegistry + MigrationManager 생존 검증 (Gate 40, ADR-040... |
| `sql_real_adapter_g41` | SQLRealAdapter: SQLiteRealAdapter REAL + LOSDB CLI (Gate 41, ADR-041) |
| `migration_engine_g42` | MigrationEngine: 통합 오케스트레이터 + MigrationPlan + 롤백 체이닝 (Gate 42, ADR-042... |
| `vector_real_adapter_g43` | VectorRealAdapter: numpy-optional 벡터 스토어 + JSON 영속화 + rollback (Gate 4... |
| `graph_real_adapter_g44` | GraphRealAdapter: networkx-optional 그래프 스토어 + JSON 영속화 + rollback (Gat... |
| `losdb_client_g45` | LOSDBClient: LOSDB 통합 Facade + cross_query (Gate 45, ADR-045) |
| `e2e_prose_g46` | E2EProseGate: 6-checkpoint E2E 산문 파이프라인 (Gate 46, ADR-047) |

---

## ADR 목록

- **ADR-001**: —
- **ADR-002**: —
- **ADR-003**: —
- **ADR-004**: —
- **ADR-005**: —
- **ADR-006**: —
- **ADR-007**: —
- **ADR-008**: —
- **ADR-009**: —
- **ADR-010**: —
- **ADR-011**: —
- **ADR-012**: —
- **ADR-013**: —
- **ADR-014**: —
- **ADR-015**: —
- **ADR-016**: —
- **ADR-017**: —
- **ADR-018**: —
- **ADR-019**: —
- **ADR-020**: —
- **ADR-021**: —
- **ADR-022**: —
- **ADR-023**: —
- **ADR-024**: —
- **ADR-025**: —
- **ADR-026**: —
- **ADR-027**: —
- **ADR-028**: —
- **ADR-029**: —
- **ADR-030**: —
- **ADR-031**: —
- **ADR-032**: —
- **ADR-033**: —
- **ADR-034**: —
- **ADR-035**: —
- **ADR-036**: V580
- **ADR-037**: —
- **ADR-038**: —
- **ADR-039**: V580
- **ADR-040**: V581
- **ADR-041**: V582
- **ADR-042**: V583
- **ADR-043**: GraphRealAdapter — Neo4j/NetworkX 그래프 백엔드 (LOSDB Phase C)
- **ADR-045**: LOSDBClient Facade — 단일 진입점 + cross_query API
- **ADR-046**: V587
- **ADR-047**: V587
- **ADR-048**: V587

---

## API 요약

자세한 API 설명은 [docs/user/reference.md](reference.md) 의 수동 작성 섹션을 참조하세요.

### 핵심 진입점

```python
# 전체 45 Gates 실행
from literary_system.gates.release_gate import run_release_gate
r = run_release_gate()
print(r["gates_passed"], "/", r["total_gates"])  # 45 / 45

# fast-path (L0+L1)
from literary_system.gates.release_gate import run_release_gate_tiered
r = run_release_gate_tiered(tiers=["L0", "L1"])

# E2E 산문 게이트
from literary_system.gates.e2e_prose_gate import gate_e2e_prose
result = gate_e2e_prose(mock=True)
print(result.checkpoints_passed, "/", result.total_checkpoints)  # 6 / 6

# 샘플 드라마 생성
python examples/sample_drama/generate.py
```
