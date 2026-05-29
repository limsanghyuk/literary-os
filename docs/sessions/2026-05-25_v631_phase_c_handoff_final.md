# Phase C 본안 핸드오프 Final — V631~V680 저연산 모드용

**작성일**: 2026-05-25
**작성 모드**: 상위 연산 모드 (Opus)
**대상**: 저연산 개발 모드
**기반 초안**: GitHub `docs/sessions/literary_os_v631_phase_c_{proposal,blueprint}.docx` + `docs/phase/literary-os-phase-c-design.docx` + `2026-05-22_v631_phase_c_handoff.md` (commit 9488645d 후속, 2026-05-22 push)
**본안 산출물**:
- `docs/sessions/literary_os_v631_phase_c_proposal_final.docx` (3인 합의 본안 v1.0 Final)
- `docs/sessions/literary_os_v631_phase_c_blueprint_final.docx` (시스템 설계도 v1.0 Final)
- `docs/sessions/2026-05-25_v631_phase_c_handoff_final.md` (본 문서)
**기준선**: v11.0.0 (V630 AUDIT3) · 60 Gates · 7,213 Tests · ADR-001~097 · 1,036 파일
**목표 상태**: v12.0.0 (V680) · 74 Gates · 10,000+ Tests · ADR-001~107

---

## 0. 본 문서의 위치

2026-05-22에 GitHub에 push된 Phase C **초안** 3종(proposal·blueprint·handoff)을 base로 3인 전문가가 V630 AUDIT3 실측 자산 정합 검증 후 12개 보강 사항(C-M-01 ~ C-M-12)을 분산 부착한 **본안 Final**의 저연산 모드용 작업 지시서다.

**초안 → 본안 진화 규칙**: 초안의 4 SP / V631~V680 / 23 ADR / 14 Gate / 20 쟁점 합의 골격은 **그대로 계승**. 본안은 12개 보강 사항을 각 V버전에 분산 부착 + 8개 신규 쟁점(C-21~C-28) 해소.

---

## 1. 학습해야 할 핵심 문서 (우선순위)

| 순위 | 문서 | 학습 목적 |
|------|------|-----------|
| **1순위** | `docs/sessions/literary_os_v631_phase_c_proposal_final.docx` | 4 SP + 12 보강 + 28 쟁점 + G75 8축 |
| **2순위** | `docs/sessions/literary_os_v631_phase_c_blueprint_final.docx` | 40+ 모듈 + 14 Gate + 23 ADR 스켈레톤 + 본안 10건 추가 모듈 |
| 참조 | `docs/sessions/literary_os_v631_phase_c_proposal.docx` | 초안 proposal (본안 base) |
| 참조 | `docs/sessions/literary_os_v631_phase_c_blueprint.docx` | 초안 blueprint (모듈 스켈레톤 풍부) |
| 참조 | `docs/phase/literary-os-phase-c-design.docx` | 초안 통합본 (blueprint과 동일 SHA) |
| 참조 | `docs/sessions/2026-05-22_v631_phase_c_handoff.md` | 초안 handoff (압축본) |
| 참조 | `docs/sessions/2026-05-21_v596_v630_phase_b_handoff.md` | Phase B 핸드오프 (선행) |
| 필수 | `LITERARY_OS_CLAUDE_PREFLIGHT_GUIDE.md` | 매 SP 진입 전 15단계 |

---

## 2. Phase B 종료 전제 - V630 AUDIT3 기준 확인 사항

Phase C 진입 전 다음이 main HEAD에 commit되어 있어야 한다 (이미 완료):

- V630 G61 7축 InterfaceTrace + MIN_TESTS 7000 + ADR-097 + v11.0.0 (commit `2b67077638`)
- V630-AUDIT (`03660a7e4b`): BUG-R1~R4/V4/M1/M2 수정
- V630-AUDIT2 (`128f09bee0`): BUG-T1 source_hash 재생성 + TC-61~63 + META-1
- V630-AUDIT3 (`bb9dbadd37`): WARN-M1/D1/1 정합성 + source_hash 재갱신
- 60/60 Gates ALL PASS
- 7,213 Tests 0 failure
- ADR-001~097 commit
- CI GREEN

V630 자산 확인 (1,036 파일):
- `literary_system/constitution/los_constitution.py` (V594 v1.0)
- `literary_system/llm_bridge/canonical_bridge_v2.py` (V610)
- `literary_system/finetune/*.py` (15 파일, LoRA + RLHF + Long Context 풀스택)
- `literary_system/ensemble/gate8_ensemble.py` + `narrative_fitness_arbiter.py` (V646 마이그레이션 대상)
- `literary_system/gates/phase_a_exit_gate.py` (G52) + `phase_b_exit_gate.py` (G61)
- `deploy/helm/train_plane/` + `serve_plane/` (V662 v2.0 base)

---

## 3. 4 Sub-Phase 직렬 진행 (총 50 versions, 14개월)

### SP-C.1 (V631~V645, 15 versions, M+0~M+4개월) — Self-Learning Loop + Constitution v2.0

**초안 골격**: Constitution v2.0 MetaLearner → WeightTracker → PatternLibV2 → RetrainingScheduler → AutoPromotionGate G62 → SelfLearningMonitor → ConstitutionEvalV2 → ContaminationDetector → Suite v1 패키징 → MetaLearner 1~4 사이클 → SelfLearningGate G63.

**본안 보강 분산 부착**:

V631 체크리스트:
- [ ] `literary_system/constitution/los_constitution_v2.py` (V1 상속)
- [ ] Bayesian Optimization (Optuna) w1~w5 학습
- [ ] **본안 C-M-05**: `entropy(w) >= 1.5` 분포 제약 추가
- [ ] ADR-073 본문 + entropy 정책 부속

V632 체크리스트:
- [ ] `literary_system/constitution/constitution_weight_tracker.py`
- [ ] version 태그 발행 (4-tag Reproducibility 지원)
- [ ] `literary_system/finetune/lora_artifact.py` 확장: `constitution_weights_version: str` 필드 추가 (**본안 C-M-06**)
- [ ] ADR-074

V633 체크리스트:
- [ ] `literary_system/patterns/pattern_library_v2.py` (압축+랭킹)
- [ ] ADR-075

V634 체크리스트:
- [ ] `literary_system/finetune/retraining_scheduler.py`
- [ ] MIN_INTERVAL_DAYS = 7
- [ ] **본안 보강**: GPU SLO 초과 시 7→14일 자동 연장
- [ ] ADR-076

V635 체크리스트:
- [ ] `literary_system/gates/auto_promotion_gate.py` (G62)
- [ ] R(scene) >= 0.78 + AB 10회 PASS + 자동 승급 + 롤백 0
- [ ] ADR-077

V636~V638:
- [ ] `literary_system/monitoring/self_learning_monitor.py`
- [ ] `literary_system/constitution/constitution_eval_v2.py` (인간 calibration 5→10명, 초안 C-10)
- [ ] `literary_system/monitoring/contamination_detector.py`
- [ ] ADR-078~080

V639: KoreanDrama-Suite-v1 HuggingFace 비공개 등록 준비 + ATIA Model Card v2

V640~V644: MetaLearner 1~4 사이클 (격주, 월 ~$80 GPU SLO 분할)

V645:
- [ ] `literary_system/gates/self_learning_gate.py` (G63)
- [ ] 오염 0%, KL<0.05, Krippendorff α>=0.70, 추세 양수 3사이클
- [ ] ADR-081

**SP-C.1 완료 조건**: G62 + G63 PASS + R(scene)>=0.78 + 4사이클 + +500 TC

---

### SP-C.2 (V646~V655, 10 versions, M+4~M+7개월) — Multi-Agent Ensemble

**초안 골격**: DirectorAgent → ScriptAgent → CriticAgent → EditorAgent → AgentCoordinator G64 → AgentMemoryCache → EnsembleQualityGate G65 → AgentSafetyGuard → MAE-MultiWork G66 → SuiteRegistration G67.

V646 체크리스트:
- [ ] `literary_system/agents/director_agent.py` (씬 청사진 5요소)
- [ ] **본안 C-M-04**: `literary_system/agents/__init__.py`에서 V630 `ensemble/gate8_ensemble.py`와 `narrative_fitness_arbiter.py` 백워드 호환 re-export
- [ ] ADR-082 + ensemble/ legacy 마이그레이션 정책 부속

V647: `script_agent.py` (LoRA 직결 + AgentSafetyGuard 사전) + ADR-083

V648: `critic_agent.py` (NarrativeFitnessArbiter 평가 컴포넌트로 통합) + ADR-084

V649: `editor_agent.py` + **본안 C-M-09**: 거부 권한 없음 명시 (ADR-085 부속)

V650 체크리스트 (가장 중요):
- [ ] `literary_system/agents/agent_coordinator.py` (G64)
- [ ] max_rounds=3 + timeout=30s + 초안 폴백
- [ ] **본안 C-M-01**: `literary_system/agents/prompt_cache_layer.py` (TTL 60s, LRU 1000, prefix 512 hash)
- [ ] **본안 C-M-02**: `literary_system/agents/agent_trace_logger.py` (UUID + 90일 보존 + LOSDB 영속화)
- [ ] **ADR-086 부속**: AgentResponsibility Matrix (Director-Script-Critic-Editor 권한 명문화)
- [ ] Gate G64 PASS 기준: cache hit ratio >= 0.3 (본안 추가)

V651: `agent_memory_cache.py` (TTL+무효화) + ADR-087

V652 체크리스트:
- [ ] **본안 C-M-07**: `literary_system/eval/agent_ensemble_evaluator.py` (Welch's t-test)
- [ ] 단일 LoRA 100 prompt vs 4-Agent 100 prompt
- [ ] delta >= 0.05 + p_value < 0.05
- [ ] Gate G65 + ADR-088

V653: `agent_safety_guard.py` (Pre/Post 양면) + ADR-089

V654: MAE-MultiWork G66 (3작품 동시 P95 <= 8초)

V655: HuggingFace Suite v1 등록 + G67 + ATIA Model Card v2 (ADR-090)

**본안 추가 CI**:
- [ ] `.github/workflows/agent_ensemble_eval.yml` (PR마다 100 prompt 평가, 30분, **C-M-08**)

**SP-C.2 완료 조건**: G64~G67 PASS + R(scene) >= 0.83 (p<0.05) + cache hit >= 0.3 + +500 TC

---

### SP-C.3 (V656~V665, 10 versions, M+7~M+10개월) — Production API + PublicSDK + Reader Feedback

V656: `literary_system/sdk/public_sdk_v1.py` (analyze/repair/predict/generate 4 API, SemVer 2.0) + ADR-091

V657: OpenAPI 3.1 Swagger + Postman + 3언어 샘플 (Python/JS/Shell) + ADR-092

V658 체크리스트:
- [ ] `literary_system/api/b2b_partner_api.py` (FastAPI router)
- [ ] OAuth 2.1 + Webhook + Rate Limit 1,000 RPM
- [ ] **본안 C-M-12**: `/generate/multi_lora` endpoint — LoRAStackingAdapter 활성 (Phase B V615 인터페이스를 Phase C에서 활성). 장르별 LoRA n개 attach 허용
- [ ] ADR-093 본문 + LoRAStackingAdapter 활성 정책 부속

V659 체크리스트:
- [ ] `literary_system/feedback/reader_feedback_collector.py` (G68)
- [ ] PIPA 익명화 (user_id, IP, fingerprint)
- [ ] 수집 지연 <=500ms
- [ ] **본안 C-M-10**: `governance/dsr_handler.py` 연결 + 30일 SLA 자동 카운트다운
- [ ] ADR-094 + DSR 정책 부속

V660: `literary_system/feedback/feedback_to_rlhf.py` (z-score>3 자동 제외)

V661: Feedback Loop G69 (24h 무중단)

V662 체크리스트:
- [ ] `literary_system/serving/model_serving_endpoint.py` v2.0
- [ ] Kubernetes HPA 자동 스케일링
- [ ] **본안 C-M-03**: `literary_system/serving/agent_router.py` (단일/Ensemble/Cascade 라우팅)
- [ ] TrainPlane/ServePlane Helm v2.0 검증

V663: SDK Stability G70 (20명 베타, P0 0건, 응답 <=2초)

V664: B2B Partner G71 (LOI 3건 + LoRAStackingAdapter 활성 동작 확인)

V665: PyPI 등록 준비 + Grafana 대시보드

**본안 추가 CI**:
- [ ] `.github/workflows/nightly_meta_learner.yml` (Optuna 50 trial, 1h, $5 GPU, **C-M-08**)

**SP-C.3 완료 조건**: G68~G71 PASS + LOI 3건 + DSR 30일 SLA 100% + +1,000 TC

---

### SP-C.4 (V666~V680, 15 versions, M+10~M+14개월) — Competitive Absorption + Enterprise + Exit

V666: `distillation/distillation_export.py` 설계 (v0.1)

V667~V671 체크리스트:
- [ ] **본안 C-M-11**: 각 모듈 헤더에 IP 자문 보고서 링크 + `docs/legal/ip_review_*.md` 5건 commit 의무
- [ ] `literary_system/competition/novelai_style_absorber.py` (V667) — 씬 스타일 메타데이터 태그 (이미지 생성 X)
- [ ] `literary_system/competition/sudowrite_beat_absorber.py` (V668) — DirectorAgent Beat 분해
- [ ] `literary_system/competition/novelcrafter_template_absorber.py` (V669) — 플롯 템플릿 v2.0
- [ ] `literary_system/competition/nolanai_format_absorber.py` (V670) — Final Draft / PDF 변환
- [ ] `literary_system/competition/jenova_korean_absorber.py` (V671) — KoreanCadencePlanner v2.0 + EXAONE
- [ ] G72 (5종 PASS + IP 자문 5건 + 회귀 0)

V672: `distillation/distillation_export.py` v0.1 (safetensors + GGUF) + ADR-095

V673: Enterprise SLO G73 (99.9% 30일 + 1,000 RPM + RTO<=5분 + 보안 취약점 High+ 0건)

V674: Revenue G74 (정식 계약 1건 또는 MOU+파일럿 유료화 대체 인정)

V675: 운영 문서 완성 + ADR-073~095 본문 + **본안 추가**: 분기 매출 보고서 템플릿 + 외부 감사 패키지

V676~V679: 30일 안정화 + 메모리 누수 + 자동 복구 + 보안 감사

V680 체크리스트:
- [ ] `literary_system/gates/phase_c_exit_gate.py` (G75 8축)
- [ ] **본안 C-28**: 8번째 축 — InterfaceTrace 30일 audit (`AgentTraceLogger.query_for_audit(since_days=30)`)
- [ ] v12.0.0 릴리즈 + GitHub Release
- [ ] Phase D 진입 선언

**SP-C.4 완료 조건**: G72~G75 PASS + 정식 계약 1건 + InterfaceTrace 30일 + v12.0.0 + +1,000 TC

---

## 4. Gate G75 — Phase C Exit 8축 (V680, 본안 C-28)

| 축 | 지표 | 임계값 | 근거 |
|----|------|--------|------|
| C1 | 74 Gates ALL PASS | 74/74 | 누적 |
| C2 | 10,000+ Tests | total_pass >= 10,000 | 누적 |
| C3 | SP-C.1 | G62 + G63 PASS | V635 + V645 |
| C4 | SP-C.2 | G64~G67 PASS | V650/652/654/655 |
| C5 | SP-C.3 | G68~G71 PASS | V659/661/663/664 |
| C6 | SP-C.4 | G72~G74 PASS + G75 자체 | V671/673/674/680 |
| C7 | v12.0.0 릴리즈 | GitHub Release commit | V680 |
| C8 | InterfaceTrace 30일+ audit | traces >= 1000 + safety 0건 + 평균 r >= 0.83 | **본안 C-28**, AgentTraceLogger 30일 |

8축 모두 PASS = Phase D (V700+, SaaS + 다언어 확장) 진입 가능.

---

## 5. 신규 Gate 14건 (G62~G75) + 신규 ADR 23건 (073~095)

본안 설계도 §5 참조. 본안 보강:

- G62 + entropy ≥1.5 (C-M-05)
- G64 + cache hit ratio ≥0.3 (C-M-01)
- G65 + Welch t-test (C-M-07)
- G68 + DSR 30일 SLA 등록 (C-M-10)
- G71 + LoRAStackingAdapter 활성 동작 (C-M-12)
- G72 + IP 자문 5건 commit (C-M-11)
- G75 + 8축 InterfaceTrace 30일 (C-28)

---

## 6. PR 분할 권장 (~90 PR — V버전당 평균 2개)

50 versions × 평균 2 PR = ~100 PR. SP 종료 시점 (V645/V655/V665/V680) 통합 PR 1개 추가.

---

## 7. 의존성 그래프

```
SP-C.1 (V631~V645) Self-Learning Loop + Constitution v2.0
   |   본안 보강: entropy ≥1.5 (C-M-05), 4-tag (C-M-06), 10명 calibration
   v
SP-C.2 (V646~V655) Multi-Agent Ensemble
   |   본안 보강: PromptCache (C-M-01), TraceLogger (C-M-02), Responsibility Matrix (C-M-09)
   |               ensemble/ legacy 마이그레이션 (C-M-04), Welch t-test (C-M-07)
   v
SP-C.3 (V656~V665) Production API + Reader Feedback
   |   본안 보강: LoRAStackingAdapter 활성 (C-M-12), ReaderFeedback DSR (C-M-10)
   |               AgentRouter (C-M-03), CI 분리 (C-M-08)
   v
SP-C.4 (V666~V680) Competitive Absorption + Exit
   |   본안 보강: IP 자문 5건 (C-M-11), G75 8축 InterfaceTrace (C-28)
   v
Phase D 진입 (V700+, SaaS + 다언어 확장)
```

**병렬 운영 트랙** (비-CI):
- 인간 calibration 10명: V637~V680 (매월 1회 100 샘플, ~$500/월)
- IP 자문 5건: V667~V671 시작 전 완료
- 분기 매출 보고: V675부터 정착

---

## 8. PREFLIGHT_GUIDE 15단계 (V431 이후 매 SP 필수)

(Phase B 핸드오프와 동일, 생략)

특히 Phase C 추가 점검:
- **LLM-0 / LLM-1 원칙**: corpus/constitution/ 외부 LLM 호출 0건 (절대). agents/는 finetune/ 내부 LoRA만 사용 (LLM-1).
- **GPU SLO $200/월**: MetaLearner $80 + Ensemble $60 + RLHF $40 + Eval $20 분할
- **MIN_INTERVAL 7일**: RetrainingScheduler 강제 (초과 시 14일 자동 연장)
- **PromptCache hit ratio**: V650 이후 dashboard에서 모니터 (목표 ≥0.3)

---

## 9. 위험 신호 — 상위 모드에 보고할 상황

- **PASS 7,213 → 7,200 미만** 후퇴
- **MetaLearner entropy < 1.5 발생** → ConstitutionWeightTracker 자동 롤백 1회 발동 후 보고
- **AgentCoordinator timeout 3회 연속** → max_rounds 또는 timeout 재설정 필요
- **AgentEnsembleEvaluator p-value > 0.05** → 앙상블 효과 통계적 비유의. SP-C.2 재검토
- **월 GPU SLO $200 도달** → RetrainingScheduler MIN_INTERVAL 7→14 자동 연장 발동 후 보고
- **ReaderFeedback DSR 30일 미응답 1건** → 거버넌스 침해 즉시 중단
- **경쟁 흡수 IP 자문 미commit으로 V667~V671 진입 시도** → 자동 차단 + 보고
- **G75 InterfaceTrace 8번째 축 데이터 < 1,000건** → 30일 audit 불충분, 추가 운영 필요
- **인간 calibration agreement < 0.5** → ConstitutionEvalV2 재정의

---

## 10. V680 종료 → Phase D 진입 준비

Phase C 종료 후 (G75 8축 PASS):
1. 메모리 업데이트: `project_phase6_roadmap.md` → V680 완료, V700+ Phase D 다음 타겟
2. KoreanDrama-Suite-v1 HuggingFace 공개 전환 검토 (정식 계약 1건 + 매출 발생 후)
3. AgentTraceLogger 90일+ 데이터 → Phase D AgentDistillation 학습 데이터로 활용 준비
4. 상위 연산 모드 호출: "Phase D (V700+, SaaS + 다언어 확장) 본안 설계도 작성 요청"
5. 별도 세션에서 `docs/sessions/literary_os_v700_phase_d_blueprint.docx` 작성

---

## 11. 본안 추가 모듈 (10건) — 초안 31 + 본안 10 = 41 신규

본안 설계도 §6 참조. 핵심:

1. `literary_system/agents/prompt_cache_layer.py` (V650, C-M-01)
2. `literary_system/agents/agent_trace_logger.py` (V650, C-M-02)
3. `literary_system/eval/agent_ensemble_evaluator.py` (V652, C-M-07)
4. `literary_system/agents/__init__.py` legacy 마이그레이션 (V646, C-M-04)
5. `docs/legal/ip_review_*.md` 5건 (V667~V671, C-M-11)
6. `.github/workflows/nightly_meta_learner.yml` (V665, C-M-08)
7. `.github/workflows/agent_ensemble_eval.yml` (V655, C-M-08)
8. `literary_system/governance/dsr_handler.py` 확장 (V659, C-M-10)
9. `literary_system/finetune/lora_artifact.py` 확장 (V632, C-M-06)
10. `literary_system/serving/agent_router.py` (V662, C-M-03)

---

## 12. 첫 명령 시퀀스

```bash
# V630 AUDIT3 main HEAD 확인
cd /path/to/literary-os
git pull origin main
git log --oneline -5   # bb9dbadd37 V630-AUDIT3 commit 확인

# 진입 전 점검
python tools/check_version_consistency.py     # exit 0
gh release list | head -10                    # V630/v11.0.0 존재
pytest tests/ -q                              # 7,213 PASS

# Phase C 본안 학습
cat docs/sessions/2026-05-25_v631_phase_c_handoff_final.md   # 본 문서

# SP-C.1 V631 진입
git checkout -b dev/v631-sp-c1-constitution-v2
# Preflight 15단계 수행

# los_constitution_v2.py 작성 (Blueprint §1.1 스켈레톤 참조)
# entropy >= 1.5 분포 제약 (본안 C-M-05) 포함

pytest tests/ -q                              # 7,213+ PASS 유지
git add -A && git commit -m "V631 SP-C.1: LOSConstitution v2.0 MetaLearner + entropy 1.5 (ADR-073, C-M-05)"
git push origin dev/v631-sp-c1-constitution-v2
# PR open, 머지 후 V632 진입

# ... 반복 (50 versions, 14개월)
```

---

## 13. 메타데이터

- **문서 ID**: LOS-PHASE-C-PROPOSAL-FINAL-HANDOFF-2026-05-25
- **유효 기간**: Phase C 종료(V680)까지. V700+ 진입 시 별도 핸드오프 발행
- **선행 문서**: `2026-05-22_v631_phase_c_handoff.md` (초안)
- **기반 자산**: `literary_os_v630_AUDIT3_FINAL.zip` (1,036 파일, V630-AUDIT3)
- **후속 문서**: `2026-XX-XX_v700_phase_d_handoff.md` (Phase C 종료 후 발행)
