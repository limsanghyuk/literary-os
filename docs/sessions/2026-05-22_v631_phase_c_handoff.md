# Phase C 핸드오프 — V631~V680 저연산 모드용

**작성일**: 2026-05-22
**기반 문서**:
- `docs/phase/literary-os-phase-b-design.docx` (Phase B 설계 원본)
- `docs/sessions/2026-05-21_v596_v630_phase_b_handoff.md` (Phase B 핸드오프)
- `docs/sessions/literary_os_v581_blueprint_v2.docx` (5-Phase 장기 로드맵)
**본안 산출물**:
- `docs/sessions/literary_os_v631_phase_c_proposal.docx` — 3인 합의 제안서 v1.0
- `docs/sessions/literary_os_v631_phase_c_design.docx` — 기술 설계도 v1.0
- `docs/sessions/2026-05-22_v631_phase_c_handoff.md` — 본 문서
**기준선**: v11.0.0 (V630) · 60 Gates · 7,000+ Tests · ADR-001~072
**목표 상태**: v12.0.0 (V680) · 74 Gates · 10,000+ Tests · ADR-001~095

---

## 0. Phase C 위치 (장기 로드맵 내)

v581 Blueprint v2.0 원본:
- Phase A (V581~V595): LOSDB+Constitution+CLI 베타 ✅ DONE (v10.0.2)
- Phase B (V596~V630): 실 LoRA+RLHF+MultiWork+영업 → v11.0.0
- Phase C (원본 §C): RLHF 자가 개선 루프 → **Phase B SP-B.2로 이미 통합**
- Phase D (원본 §D): PublicSDK+경쟁 흡수 → **Phase C에 통합**
- **Phase C (본안)**: Self-Learning + 멀티 에이전트 + Production + 경쟁 흡수

---

## 1. 4 Sub-Phase 직렬 진행

### SP-C.1 (V631~V645) — Self-Learning Loop + Constitution v2.0

| V | 핵심 구현물 | Gate/ADR |
|---|---|---|
| 631 | LOSConstitution v2.0 MetaLearner (Bayesian Opt w1~w5) | ADR-073 |
| 632 | ConstitutionWeightTracker (LOSDB 영속화 + 롤백) | ADR-074 |
| 633 | PatternLibraryV2 (압축+랭킹) | ADR-075 |
| 634 | RetrainingScheduler (F1 drift/7일, MIN_INTERVAL=7일) | ADR-076 |
| 635 | AutoPromotionGate G62 (R≥0.78, 롤백 0건) | G62, ADR-077 |
| 636~638 | SelfLearningMonitor + ConstitutionEvalV2 + ContaminationDetector | ADR-078~080 |
| 639 | KoreanDrama-Suite-v1 HuggingFace 비공개 등록 준비 | — |
| 640~644 | MetaLearner 반복 학습 2~4사이클 | — |
| 645 | SelfLearningGate G63 (오염 0%, α≥0.70) | G63, ADR-081 |

**SP-C.1 완료 조건**: G62 + G63 PASS + R(scene)≥0.78 + MetaLearner 4사이클 + +500 테스트

---

### SP-C.2 (V646~V655) — Multi-Agent Ensemble Writing System

| V | 핵심 구현물 | Gate/ADR |
|---|---|---|
| 646 | DirectorAgent (SceneBlueprint 5요소) | ADR-082 |
| 647 | ScriptAgent (LoRA InferenceGateway 직결) | ADR-083 |
| 648 | CriticAgent (Constitution v2.0 평가) | ADR-084 |
| 649 | EditorAgent (KoreanCadencePlanner 정제) | ADR-085 |
| 650 | AgentCoordinator (max 3 round-trip, 30s timeout) | G64, ADR-086 |
| 651 | AgentMemoryCache (TTL + 캐릭터 상태 공유) | ADR-087 |
| 652 | Ensemble Quality Gate G65 (R≥0.83) | G65, ADR-088 |
| 653 | AgentSafetyGuard (모든 에이전트 출력 검사) | ADR-089 |
| 654 | MAE-MultiWork Gate G66 (3작품 P95≤8초) | G66 |
| 655 | Suite Registration Gate G67 + HuggingFace 등록 | G67, ADR-090 |

**SP-C.2 완료 조건**: G64~G67 PASS + 앙상블 R(scene)≥0.83 + +500 테스트

---

### SP-C.3 (V656~V665) — Production API + PublicSDK + Reader Feedback

| V | 핵심 구현물 | Gate/ADR |
|---|---|---|
| 656 | PublicSDK v1.0 (analyze/repair/predict/generate) | ADR-091 |
| 657 | OpenAPI 3.1 Swagger + Postman + 3언어 샘플 | ADR-092 |
| 658 | B2B Partner API (OAuth 2.1 + Webhook + 1,000 RPM) | ADR-093 |
| 659 | ReaderFeedbackCollector (PIPA 익명화, G68) | G68, ADR-094 |
| 660 | FeedbackToRLHF Adapter (z-score 이상치 제거) | — |
| 661 | Feedback Loop Gate G69 (24h 무중단) | G69 |
| 662 | ModelServingEndpoint v2.0 (Kubernetes HPA) | — |
| 663 | SDK Stability Gate G70 (20명 베타, P0 0건) | G70 |
| 664 | B2B Partner Gate G71 (LOI 3건) | G71 |
| 665 | SP-C.3 완료 보고 + PyPI 등록 준비 | — |

**SP-C.3 완료 조건**: G68~G71 PASS + LOI 3건 + SDK 베타 안정 + +1,000 테스트

---

### SP-C.4 (V666~V680) — Competitive Absorption + Enterprise Scale + Exit

| V | 핵심 구현물 | Gate/ADR |
|---|---|---|
| 666 | DistillationExportPipeline 설계 (v0.1) | — |
| 667~671 | 경쟁 흡수 5종 (NovelAI/Sudowrite/Novelcrafter/NolanAI/Jenova) | G72 |
| 672 | DistillationExportPipeline v0.1 구현 | ADR-095 |
| 673 | Enterprise SLO Gate G73 (99.9% + 1,000RPM) | G73 |
| 674 | Revenue Gate G74 (정식 계약 1건) | G74 |
| 675 | Phase C 운영 문서 완성 | — |
| 676~679 | 30일 안정화 + 보안 감사 | — |
| 680 | Phase C Exit Gate G75 (74/74 + 10,000+) + v12.0.0 | G75 |

---

## 2. 절대 원칙 (Phase C 전 범위 불변)

- **LLM-0**: corpus/, constitution/, finetune/ 외부 LLM 호출 금지 (절대)
- **LLM-1**: PROMOTED 단계 모델만 서빙 (AutoPromotionGate G62 통과 필수)
- **DEV_MODE**: 항상 false (ADR-034)
- **경쟁 흡수**: 독립 재구현 원칙, 경쟁사 코드/데이터 불사용

## 3. GPU SLO Phase C

- **하드 상한**: $200/월 (Phase B $120에서 확대)
- **재학습 최소 간격**: 7일 (RetrainingScheduler.MIN_INTERVAL_DAYS)
- **초과 시**: 재학습 간격 2배 연장 자동 적용

## 4. Phase D 진입 조건

G75 PASS + 정식 계약 1건 + v12.0.0 릴리즈 후 상위 연산 모드 호출:
"Phase D (V700+, SaaS + 다언어 확장) 본안 설계도 작성 요청"

---
**문서 ID**: LOS-PHASE-C-HANDOFF-2026-05-22
**선행 문서**: 2026-05-21_v596_v630_phase_b_handoff.md
