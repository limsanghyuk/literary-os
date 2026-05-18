# Changelog — Literary OS

상세 버전별 변경 이력은 `docs/changelog/`를 참조하세요.

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
