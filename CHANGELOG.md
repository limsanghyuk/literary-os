## [10.10.0] — 2026-05-22 — V605 SP-B.2 CanaryController + ModelServingEndpoint (ADR-065)

### Added
- `literary_system/serving/canary_controller.py`: CanaryController v1.0 — 4단계 Canary (5/25/50/100%) + Gate 판정 + 자동 롤백
- `literary_system/serving/model_serving_endpoint.py`: ModelServingEndpoint v1.0 — FastAPI /model_card 엔드포인트 (소프트-임포트)
- `literary_system/serving/__init__.py`: serving 패키지 신규 생성
- `docs/adr/ADR-065.md`: CanaryController + ModelServingEndpoint 설계 결정 문서
- `tests/unit/test_v605_canary_controller.py`: 36 TC PASS

### Changed
- `pyproject.toml`: version 10.9.0 → 10.10.0

## [10.9.0] — 2026-05-22 — V604 SP-B.2 RLHFMonitor v1.0 + 자동 롤백 (ADR-064)

### Added
- `literary_system/rlhf/rlhf_monitor.py`: RLHFMonitor v1.0 — 슬라이딩 윈도우 이동평균 보상 추세 + 자동 롤백 트리거
- `docs/adr/ADR-064.md`: RLHFMonitor 설계 결정 문서
- `tests/unit/test_v604_rlhf_monitor.py`: 27 TC (TC-1~TC-27) PASS

### Changed
- `literary_system/rlhf/__init__.py`: RLHFMonitor·MonitorConfig·MonitorState·RewardSnapshot·RollbackRecord export 추가
- `pyproject.toml`: version 10.8.0 → 10.9.0

## [10.8.0] — 2026-05-22 — V603 SP-B.2 PPOTrainer + ConstraintGuard + Gate G55 (ADR-063)

### Added
- `literary_system/rlhf/ppo_trainer.py`: PPOTrainer v1.0 — Clipped PPO + KL 추적 + LCG RNG (LLM-0)
- `literary_system/rlhf/constraint_guard.py`: ConstraintGuard v1.0 — KL 하드리밋·보상 클램프·엔트로피 붕괴 감지
- `docs/adr/ADR-063.md`: PPOTrainer + ConstraintGuard 설계 결정 문서
- `tests/unit/test_v603_ppo_trainer.py`: 9 TC (TC-1~TC-9) PASS
- Gate G55 (PPO Stability) — 6 CP: KL 안정성·ConstraintGuard·PPOResult 통합 검증

### Changed
- `literary_system/rlhf/__init__.py`: PPOTrainer·PPOConfig·PPOResult·PPOStep·ConstraintGuard·GuardConfig·GuardState·ViolationRecord export 추가

## [10.7.0] — 2026-05-22 — V602 SP-B.2 RLHFDatasetBuilder v1.0 (ADR-062)

### Added
- `literary_system/rlhf/rlhf_dataset_builder.py`: RLHFDatasetBuilder v1.0 — (씬,보상) JSONL + 8B/3B 듀얼 + 결정론적 80/10/10 split
- `docs/adr/ADR-062.md`: 데이터셋 빌더 설계 결정 문서
- `tests/unit/test_v602_dataset_builder.py`: 9 TC PASS

## [10.6.0] — 2026-05-22 — V601 SP-B.2 RLHF RewardModel v1.0 (ADR-061)

### Added
- `literary_system/rlhf/__init__.py`: RLHF 패키지 초기화 (SP-B.2)
- `literary_system/rlhf/reward_model.py`: RewardModel v1.0 — Constitution 5축→스칼라 R(scene), MARKER_WEIGHT_CAP=0.20, 적대적 시드 5종, quality_correlation() hook
- `docs/adr/ADR-061.md`: RLHF 보상 모델 설계 결정
- `tests/unit/test_v601_reward_model.py`: 8 TC (기본·가중치·적대적)

### Changed
- `pyproject.toml`: version 10.5.0 → 10.6.0
- `README.md`: badges 10.6.0 / 6390 PASS / V601

---

## [10.5.0] — 2026-05-22 — V600 Phase B SP-B.1 완료 — Gate G54 + finetune_ci.yml + 모델 적합성 갱신

### Added
- `literary_system/gates/lora_finetuning_gate.py`: Gate G54 7체크포인트 수직 통합 (ADR-060)
- `.github/workflows/finetune_ci.yml`: 격주 파인튜닝 CI (B-M-06)
- `docs/adr/ADR-060.md`: Fine-tuning Pipeline Gate 설계 결정
- `lora_training_config.py`: LLAMA32_LITE_MODEL + llama32_lite() + 호환성 명시
- `pyproject.toml`: [finetune] optional-deps (transformers/peft/trl/bitsandbytes 등)

### Fixed (문서 일치화)
- README/pyproject/MANIFEST/RELEASE_INFO/CHANGELOG: V598~V599 누락 갱신 완료
- README badges: 10.5.0 / 53/53 / 6382 PASS

### Gates
- Gate G54: 7/7 PASS ✅ — SP-B.1 완료
- 누적 53/53 PASS

### Tests
- `tests/unit/test_v600_finetuning_gate.py`: 21 TC (TC-A~F)
- 누적: 6,382+ PASS (**V595.2 기준 +200 달성**)

---

## [10.4.0] — 2026-05-21 — V599 Phase B SP-B.1 PreTrainSafety + FineTuneEvalPipeline + LongContextStrategy

### Added
- `literary_system/finetune/pre_train_safety.py`: PreTrainSafety 4축 (PII/Toxic/Copyright/Quality, B-M-09)
- `literary_system/finetune/finetune_eval_pipeline.py`: FineTuneEvalPipeline 5축 + Krippendorff α (B-M-07/08)
- `literary_system/finetune/long_context_strategy.py`: LongContextStrategy 100K청크 + 16K오버랩 (B-M-11)
- `docs/adr/ADR-059.md`: 파인튜닝 평가 기준선 + 안전성 + 장문 전략

### Tests
- `tests/unit/test_v599_pretrain_safety.py`: 17 TC PASS
- 누적: 6,228+ PASS (V598 기준 6,211 + 17 신규)

---

## [10.3.0] — 2026-05-21 — V598 Phase B SP-B.1 LoRAArtifact + LoRAModelRegistry + LoRAInferenceGateway + Gate G53

### Added
- `literary_system/finetune/lora_artifact.py`: LoRAArtifact 3-tag safetensors + sha256 무결성 (B-M-03)
- `literary_system/finetune/lora_model_registry.py`: LoRAModelRegistry CANDIDATE→VALIDATED→PROMOTED (LLM-1)
- `literary_system/finetune/lora_inference_gateway.py`: LoRAInferenceGateway PROMOTED 전용 서빙
- `literary_system/gates/lora_inference_gate.py`: Gate G53 8체크포인트 (레이턴시≤2초 + 100자+)
- `docs/adr/ADR-058.md`: LoRA 추론 게이트웨이 계약

### Gates
- Gate G53: 8/8 PASS
- 누적 52/52 PASS

### Tests
- `tests/unit/test_v598_lora_inference.py`: 14 TC PASS
- 누적: 6,211+ PASS

---

## [10.2.0] — 2026-05-21 — V597 Phase B SP-B.1 LoRA Training Pipeline

### Added
- `literary_system/finetune/lora_training_config.py`: LoRATrainingConfig (rank=16, q/k/v/o_proj, bf16, B-M-05)
- `literary_system/finetune/lora_job_runner.py`: LoRAJobRunner + BiweeklyScheduler (격주/주간 SLO $96, B-M-06)
- `deploy/helm/train_plane/`: TrainPlane Helm Chart 스텁 — literary-train 네임스페이스 격리 (B-M-16)
- `docs/adr/ADR-057.md`: LoRA 학습 설정 + GPU 격리 정책
- `tests/unit/test_v597_lora_training.py`: 9 TC (TC-A1~A3, B1~B4, C1~C2)

### Changed
- `literary_system/finetune/__init__.py`: LoRATrainingConfig, LoRAJobRunner, BiweeklyScheduler export 추가

### Tests
- 6,211 collected (+9 from V596)
- 51/51 Release Gates PASS

## [10.1.0] — 2026-05-21 — V596 Phase B SP-B.1

### Added
- `literary_system/governance/`: LoRAProvenanceLedger (sha256 체인) + DSRHandler (30-day SLA)
- `literary_system/finetune/`: LoRADatasetBuilder + DatasetSplitter (8:1:1, seed=42) + DatasetRegistry (sha256+DVC)
- ADR-056: LoRA Dataset Format + DSR Policy
- 11 TC → 6,202 tests total, 51/51 Gates PASS

# Changelog — Literary OS

상세 버전별 변경 이력은 `docs/changelog/`를 참조하세요.

---


## [10.0.3] — V595.3 Phase A Atomicity & Gate Freshness Final — 2026-05-21

### P1 결함 4종 수정 (기능 추가 없음)

- **FIX-A** SQLiteRealAdapter: executescript() → BEGIN IMMEDIATE + 개별 execute() (migration 원자성)
- **FIX-B** VectorRealAdapter: save op 분리 + 파일 바이트 스냅샷 rollback (파일 divergence 해소)
- **FIX-C** BackendHealthMonitor: HALF_OPEN 전이 시 last_check_ok=False (probe 없는 traffic 차단)
- **FIX-D** PhaseAExitGate EA-6: source_hash 검증 추가 (stale inventory PASS 차단)

### 테스트

- 신규 9개 TC (TC-A1~D3): tests/unit/test_v595_3_fixes.py
- test_inventory.json 재생성: 6188 tests, source_hash 갱신
- README badge: 5897 → 6179 PASS

### 검증

- compileall: PASS
- check_version_consistency --strict: PASS (git tag 경고 제외)
- run_release_gate.py: 51/51 PASS
- E2E prose tests: 20 passed, 2 skipped

---

## [10.0.2] — V595.2 Release Authority Finalization — 2026-05-21

### 릴리즈 무결성 완성

**P0 수정 (3건):**
- SHA256SUMS git-tracked 파일 기준 재생성 (0 missing, 0 mismatch)
- 문서 권위 통일: README H1/pyproject desc/RELEASE_INFO/MANIFEST → V595.2/51 Gates
- REAL LLM 테스트: API key 없으면 skip, check_version_consistency 검사 범위 확장

**CI 수정 (2건):**
- Ruff I001 import 정렬 26건 자동 수정 (CI green)
- qdrant-client optional-deps 등록 (preflight_step13 PASS)

**P1 수정 (3건):**
- LOSDBClient private field 접근 제거 (public query API 추가)
- SQLite migration: split(";") → executescript() 교체
- Phase A Exit Gate EA-6: pytest subprocess → test_inventory.json 읽기 방식

**검증:**
- CI: ALL GREEN (Ruff PASS + preflight_step13 PASS)
- run_release_gate.py: 51/51 PASS
- check_version_consistency --strict: ALL CONSISTENT
- SHA256SUMS: 0 missing, 0 mismatch
- pytest -m real_llm (no key): 0 passed, 2 skipped

---

## [10.0.1] — V595.1 Integrity Hotfix — 2026-05-21

### 버그 수정 12건

**P0 Critical (6건):**
- FIX-1: G32 print() 위반 수정 (phase_a_exit_gate.py → sys.stdout.write)
- FIX-2: GraphRealAdapter unknown op → ValueError + 원자적 snapshot 롤백
- FIX-3: BackendHealthMonitor last_check_ok 필드 — 첫 ping 실패 즉시 unavailable
- FIX-4: literary_cli.py sc%4 → (sc-1)%4 (1-based 씬 오프셋)
- FIX-5: _score_debt/_score_tension 빈 텍스트 조기 반환 0.0
- FIX-6: CorpusPiiFilter.filter_entries 뮤테이션 → dataclasses.replace()

**P1 High (6건):**
- FIX-7: _score_arc 위치기반 기승전결 순서 검증
- FIX-8: _NARRATIVE_MARKERS 한국어 조사 7개 제거 (DRSE 편향 해소)
- FIX-9: MinHash _shingle hash() → hashlib.md5 (PYTHONHASHSEED 독립)
- FIX-10: E2E CP-6 첫 씬 100~500자 범위 강제
- FIX-11: SQLiteRealAdapter _quote_identifier() SQL injection 방지
- FIX-12: GraphRealAdapter.add_edge 중복 id 처리

**검증:**
- run_release_gate.py: 51/51 PASS
- check_version_consistency --strict: ALL CONSISTENT
- SHA256SUMS.txt: 867 files, 0 mismatch

---

## [10.0.0] — V595 — 2026-05-21

### Phase A 완료 + Integrity Hotfix

**SP-A.8 신규 구현:**
- `apps/cli/literary_cli.py` — Minimal-CLI v0.1 (analyze/repair/generate)
- `literary_system/gates/phase_a_exit_gate.py` — Gate G52 (6축 검증)
- ADR-055 — Phase A Exit Gate 의사결정

**V595.1 버그 수정 (12건):**
- P0: G32 print() 위반 수정, GraphRealAdapter 원자적 롤백, BackendHealthMonitor last_check_ok, sc%4→(sc-1)%4, 빈텍스트 0.19→0.0, PII 뮤테이션 방지
- P1: _score_arc 위치기반 순서검증, DRSE 조사마커 제거, MinHash hash()→md5, E2E CP-6 100~500자 강제, SQLite identifier quoting, add_edge 중복 처리

---

## [9.2.0] — V587 — 2026-05-20

### SP-α 외부 신뢰 회복 (ADR-048) + SP-β Gate 계층화 + E2E 게이트

- `ci.yml` Gate 수 39 → **45** 정정 (ADR-048 + G46 추가)
- `tools/check_version_consistency.py` 6파일 SSoT 검사 확장 (ADR-048)
- `.github/workflows/release.yml` 신규 — post-tag 자동 Release 생성
- `CHANGELOG.md` V572~V586 15 entries 소급 추가
- **Gate G46 (E2EProseGate)**: 6-checkpoint E2E 산문 파이프라인 — NIE/ASD/GIG/LOSDB/Constitution/CLI (ADR-047)
- `run_release_gate_tiered(tiers=[...])` 신설 — L0/L1/L2/L3 4계층 (ADR-046)
- L0+L1 fast-path 실측: **1103.7ms** (목표 30s ✅)
- `ci.yml` 4-tier 잡 분리: gate-l0 / gate-pr / test(full) / security-quick
- `docs/adr/ADR-046-gate-hierarchy.md`, `ADR-047-e2e-prose-policy.md`, `ADR-048-doc-consistency-ci.md` 신규
- 게이트 합계: **45/45 PASS**

---

## [9.1.0] — V586 — 2026-05-20

### LOSDB Phase C — LOSDBClient Facade 완성

- `LOSDBClient` Facade: `cross_query`, `query_by_label`, `health_check` 구현 (ADR-045)
- Gate G45 (`_gate_losdb_client_g45`) 신설 — L3 full-path
- 전체 테스트: 5,744 PASS / 릴리즈 게이트: 44/44 PASS

---

## [9.0.1] — V585 — 2026-05-20

### LOSDB Phase C — GraphRealAdapter

- `GraphRealAdapter`: NetworkX 기반 그래프 CRUD + 선택적 NetworkX 의존성 (ADR-044)
- Gate G44 (`_gate_graph_real_adapter_g44`) 신설

---

## [9.0.0] — V584 — 2026-05-20

### LOSDB Phase B — VectorRealAdapter

- `VectorRealAdapter`: numpy 기반 벡터 저장소 + 코사인 유사도 검색 (ADR-043)
- numpy 선택적 의존성 처리 (없을 시 fallback)
- Gate G43 (`_gate_vector_real_adapter_g43`) 신설

---

## [8.8.0] — V583 — 2026-05-20

### LOSDB Phase B — MigrationEngine

- `MigrationEngine`: `MigrationPlan` + `MigrationStep` + 자동 스키마 마이그레이션 (ADR-042)
- Gate G42 (`_gate_migration_engine_g42`) 신설

---

## [8.7.0] — V582 — 2026-05-20

### LOSDB Phase B — SQLiteRealAdapter + LOSDB CLI

- `SQLiteRealAdapter`: DDL 자동 생성 + CRUD + 마이그레이션 실행 (ADR-041)
- `literary_system/db/cli.py`: analyze / repair / generate 3 명령 스켈레톤
- Gate G41 (`_gate_sql_real_adapter_g41`) 신설

---

## [8.6.0] — V581 — 2026-05-19

### LOSDB Phase A — SchemaRegistry + MigrationManager (ADR-040)

- `SchemaRegistry`: NKG / DKG / ProseStyle 통합 스키마 등록
- `MigrationManager`: SQL / Graph / Vector 3백엔드 어댑터 추상화
- Gate G40 (`_gate_db_migration_g40`) 신설 — 44번째 게이트
- Preflight Guide 15단계 확정

---

## [8.5.0] — V580 — 2026-05-19

### Async Discipline + Performance Baseline (ADR-036, ADR-039)

- `AsyncDisciplineChecker`: `await` 누락 패턴 정적 탐지 (ADR-036)
- `PerformanceBaselineProfiler`: 핵심 5개 모듈 타임라인 측정 (ADR-039)
- Gate G38 + Gate G39 신설

---

## [8.4.0] — V579 — 2026-05-19

### Duplicate Class Resolution (ADR-037)

- `DuplicateClassDetector`: 동일 이름 클래스 중복 탐지
- Gate G37 신설

---

## [8.3.0] — V578 — 2026-05-19

### Gate Registry Single Source of Truth (ADR-032)

- `gate_registry.py`: `GateRegistryEntry` 단일 소스 + `layer` 필드 (L0~L4)
- Gate G36 신설

---

## [8.2.0] — V577 — 2026-05-19

### LLM Adapter Canonical Bridge (ADR-035)

- `CanonicalLLMBridge`: Claude / OpenAI / Ollama 단일 인터페이스
- Gate G35 신설

---

## [8.1.0] — V576 — 2026-05-19

### Test Fortification

- Gate G33 + Gate G34 신설 (인증·로깅 회귀)
- 테스트 5,529 PASS 달성

---

## [8.0.0] — V575 — 2026-05-19

### Security & Hygiene (ADR-034)

- DEV_MODE 기본값 `"false"` 강제 (ADR-034)
- Preflight Step15 확정

---

## [7.9.0] — V574 — 2026-05-19

### Hotfix: AutoRepairExecutor API + stub router

- Bug-1: `AutoRepairExecutor` API 불일치 수정
- Bug-2: `analyze.py` stub router 수정

---

## [7.8.1] — V573 — 2026-05-19

### Hotfix: BUG-1/2/3 (Gate28 회귀 방지)

- BUG-1: `release_gate.py` `overall_passed` → `approved`
- BUG-2: `DebtReport` / `ArcReport` 타입명 + 생성자 수정
- BUG-3: `ActionPacketParser` → `ToolUseParser` (3개 파일)
- Preflight Step14 신설

---

## [7.8.0] — V572 — 2026-05-19

### CI 5잡 + Preflight Step13

- GitHub Actions CI 5잡 구축
- `tools/preflight_step13.py` 신설

---

## [7.7.1] — V571 — 2026-05-17 (현재)

### Phase 6 Stage C — MultiWork 완성

**신규 패키지: `literary_system/multiwork/`**
- `MultiWorkCore` — WorkProject FSM, 세션 라이프사이클 관리
- `SharedCharacterDB` — 작품 간 공유 캐릭터 DB (RLock thread-safe)
- `SharedWorldDB` — 공유 세계관 DB
- `GenreTransferLearning` — 장르 전이 학습 (`transferred[k] = (1−α)·target[k] + α·source[k]`)
- `ProjectIsolationManager` — 프로젝트 격리 관리
- `MultiWorkCIM` — 다중작품 CIM 연결 강도 계산
- `AuthorLicenseAPI` — PERSONAL / COMMERCIAL 스코프 라이선스 제어
- `MultiWorkOrchestrator` — 통합 오케스트레이터
- Gate31 (`_gate_multiwork_g31`) 신설

**테스트**: 5,456 PASS / 0 FAIL / 20 SKIP  
**릴리즈 게이트**: 30/30 PASS

---

## [7.0.0] — V556 — 2026-05-17

### 고립 모듈 4종 파이프라인 연결

- `FractalPlotTreeBuilder.build()` → `longform_endurance_orchestrator.py` 스텝 2.5 연결
- `NKGEmotionalLinker.compute_ev_delta()` → `nkg/pipeline.py` 독립 실행 연결
- `ReaderSimulator.estimate_batch()` → `scene_metrics_collector.py` 연결
- `PreemptiveGate.evaluate_batch()` → `feedback_learner.run_prediction_cycle()` 연결

**테스트**: 5,293 PASS

---

## [6.5.0] — V555 — Phase 6 Stage B (PNE)

### Predictive Narrative Engine 완성

- `PNECore` — 예측적 서사 엔진 핵심
- `DebtPredictor` — 서사 부채 예측기
- `PreemptiveGate` — 선제적 게이트
- `FeedbackLearner` — 피드백 학습기
- Gate29 (`_gate_pne_g29`) 신설
- ADR-031 LLM0StaticGate, ADR-027~030 완료

**테스트**: 5,268 PASS / 릴리즈 게이트 28/28 PASS

---

## [6.0.x] — V557~V561 — Phase 6 Stage B+ (Corpus)

### 외부 코퍼스 브릿지

- `CorpusIngestor` — 시나리오 씬 수집 (합성 1만 씬)
- `BGEM3Embedder` — BGE-M3 1024-dim 벡터 임베딩
- `CIMBootstrap` — CIM 초기화
- `CorpusValidator` — 라이선스·PII·품질 필터
- Gate30 (`_gate_corpus_g30`) 신설

---

## [5.x] — V545~V548 — Phase 6 Stage A (Cleanup)

- ADR-027: GraphSyncOrchestrator
- ADR-028: Gate Hierarchy (3-tier)
- ADR-029: NIL×PBP 통합
- ADR-030: AutoRepair SafetyNet
- ADR-031: LLM0StaticGate
- Gate25~G28 신설

**테스트**: 5,210 PASS (V545 기준)

---

## [4.x] — V451~V462 — Phase 3 (Live Adapter + SaaS)

- LLM 어댑터 실연결 (Claude v3, OpenAI, Ollama)
- SP2 테넌트 격리 (TenantManager, BillingEngine)
- DR Controller (RPO 1h), Gate15~16

---

## [이전 버전]

V380 이전 상세 이력 → `docs/changelog/` 참조
