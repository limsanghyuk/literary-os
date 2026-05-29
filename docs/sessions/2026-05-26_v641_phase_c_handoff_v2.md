# Phase C 통합 핸드오프 v2.0 — 저연산 모드 단일 학습용

**작성일**: 2026-05-26
**기준선**: V640 main HEAD `305742df` (v11.10.0, FeedbackIntegrator)
**선행 통합**: v1.0 (`faeb863d`) + v1.1 Errata (`1dd93233`) + v1.2 Survival (`4d9ac95a`)
**상태**: 4 분리 문서의 모든 결정·정정·보강을 단일 docx + 본 md로 통합 완료

---

## ⚠️ 본 문서가 유일한 학습 대상이다 (저연산 모드용)

저연산 모드(Sonnet 4.6)는 다음 2개 파일만 학습하면 SP-C.1 V641부터 SP-C.4 V680까지 50 versions 진행 가능:

1. `docs/sessions/literary_os_v631_phase_c_FINAL_v2.docx` (통합 본안 v2.0 — 본 핸드오프의 출처)
2. `docs/sessions/2026-05-26_v641_phase_c_handoff_v2.md` (본 문서)

**Archive (deprecated, 참조 보존)**:
- v1.0: `literary_os_v631_phase_c_proposal_final.docx` + `_blueprint_final.docx` + `2026-05-25_v631_phase_c_handoff_final.md`
- v1.1: `literary_os_v631_phase_c_gitnexus_errata.docx` + `2026-05-25_v631_phase_c_errata_v1.1.md`
- v1.2: `literary_os_v631_phase_c_survival_v1.2.docx` + `2026-05-26_v641_phase_c_survival_v1.2.md`

→ 위 6개 파일은 v2.0에 모두 흡수됨. 학습 불필요.

---

## 1. 필수 가이드 (전 SP 진입 전 의무)

```bash
cat docs/workflow/PREFLIGHT_GUIDE_v1.1.md      # 12단계 Preflight (GitNexus 등가 절차)
cat docs/workflow/DEV_PROTOCOL_v2.0.md         # Preflight 필수화 + 패키지 비교 검증
cat docs/workflow/PACKAGING_PROTOCOL_v1.0.md   # ZIP 검증 (파일 수 1,200 기준)
python tools/gitnexus_analyze.py               # 인덱스 재실행 (각 SP 진입 전)
```

---

## 2. 진행 현황 (V631~V640 완료, V641 진입 대기)

| V | 상태 | 모듈 | ADR |
|---|---|---|---|
| V631 | ✅ | LOSConstitutionV2 (Bayesian Optuna + entropy≥1.5) | ADR-098 |
| V632 | ✅ | ConstitutionWeightTracker | ADR-099 |
| V633 | ✅ | PatternLibraryV2 | ADR-075 |
| V634 | ✅ | RetrainingScheduler | ADR-076 |
| V635 | ✅ | AutoPromotionGate G62 | ADR-077 |
| V636 | ✅ | SelfLearningMonitor | ADR-078 |
| V637 | ✅ | ConstitutionEvalV2 + C-M-06 | ADR-079 |
| V638 | ✅ | ContaminationDetector | ADR-080 |
| V639 | ✅ | DataAugmentationController (본안 V639 계획 변경) | ADR-081 |
| V640 | ✅ | FeedbackIntegrator (본안 V640 계획 변경) | ADR-082 |
| **V640-PATCH** | ⏳ **다음** | **SafetyRegressionV2 신설 (F9 의무)** | (Phase B 보강) |
| V641 | ⏳ | MetaLearner 1사이클 + Krippendorff α | - |
| V642 | ⏳ | 2사이클 + DataAugmentationController 통합 | - |
| V643 | ⏳ | 3사이클 + FeedbackIntegrator 통합 | - |
| V644 | ⏳ | 4사이클 + 가중치 수렴 | - |
| V645 | ⏳ | SelfLearningGate G63 | ADR-081 (Gate part) |

---

## 3. 저연산 모드 작업 순서 (Sonnet 4.6 권고)

### 3.1 V640-PATCH (의무, 우선 진행)

```bash
cd /path/to/literary-os
git pull origin main
git checkout -b fix/v640-patch-safety-regression-v2
mkdir -p literary_system/safety
```

`literary_system/safety/safety_regression_v2.py` 작성 (4축 자해/혐오/PII/저작권 0건). 본안 v2.0 §2.3 코드 스켈레톤 참조.

```bash
pytest tests/safety/ -v
git commit -m "V640-PATCH: SafetyRegressionV2 신설 (Phase B 누락 보강 F2/F9)"
git push origin fix/v640-patch-safety-regression-v2
```

### 3.2 V641~V645 (SP-C.1 잔여)

각 V버전마다:
1. `git pull origin main` (이전 PR 머지 확인)
2. `python tools/gitnexus_analyze.py` (인덱스 재실행)
3. `git checkout -b dev/v{N}-...`
4. 본안 v2.0 §2.2 표 그대로 모듈 작성
5. `pytest tests/ -q` (7,246+ PASS 유지)
6. `git commit -m "V{N} SP-C.1: ..."`
7. PR open → 머지

V645 종료 후 SelfLearningGate G63 합격 = SP-C.1 완료.

### 3.3 V646 (SP-C.2 진입) — ensemble/ 4-step 마이그레이션 필수

V646 진입 시 본안 v2.0 §3.2 4-step 의무 수행 (단순 re-export 1줄 X):

- **Step 1**: `mkdir literary_system/agents` + `director_agent.py` 등 신설
- **Step 2**: `literary_system/ensemble/__init__.py` facade 재구성 (agents/* + legacy 양립)
- **Step 3**: `orchestrators/full_scene_orchestrator.py` 점진 교체 (V680까지 양쪽 import 지원)
- **Step 4**: `tests/test_agents_*.py` 신규 + `test_v389_provider_ensemble`/`test_v579_duplicate_zero` 병행

### 3.4 V647~V655 (SP-C.2 본 작업)

본안 v2.0 §3.1 표 그대로. 핵심:
- V647 ScriptAgent (LoRA InferenceGateway 직결, V640-PATCH SafetyV2 위임)
- V648 CriticAgent (NarrativeFitnessArbiter V630 통합)
- V649 EditorAgent (거부 권한 없음 C-M-09)
- V650 AgentCoordinator G64 + PromptCacheLayer + AgentTraceLogger (C-M-01/02 코드 스켈레톤 §3.3/3.4)
- V652 AgentEnsembleEvaluator G65 (Welch t-test p<0.05 C-M-07)
- V655 KoreanDrama-Suite-v1 HuggingFace 등록 G67

### 3.5 V656~V665 (SP-C.3) — F1 정정

V658 진입 시 핵심 인지:
- **LoRAStackingAdapter는 V611에 이미 실 구현 존재**
- V658에서는 호출 endpoint만 신규 (인터페이스 신설 아님)
- 본안 v2.0 §4.2 코드 스켈레톤 참조

### 3.6 V666~V680 (SP-C.4)

본안 v2.0 §5.1 표 그대로. 핵심:
- V667~V671: 경쟁 흡수 5종 + 각각 IP 자문 commit 의무 (C-M-11)
- V672: Distillation v0.1
- V680: PhaseCExitGate G75 8축 (Phase B G61 7축 + InterfaceTrace 30일)

---

## 4. 매 V버전 commit 전 의무 (DEV_PROTOCOL_v2.0)

```bash
# 1. Preflight 12단계 (PREFLIGHT_GUIDE_v1.1)
python tools/gitnexus_analyze.py    # 또는 tools/preflight_nexus.py

# 2. 패키지 비교 검증 (DEV_PROTOCOL_v2.0)
python tools/check_version_consistency.py --strict

# 3. ZIP 검증 (PACKAGING_PROTOCOL_v1.0)
# 릴리즈 commit만: 파일 수 1,200 기준 + 런타임 포함 주석

# 4. Release Gate
python -c "from literary_system.gates.release_gate import run_release_gate; print(run_release_gate()['summary'])"

# 5. 전체 테스트
pytest tests/ -q
```

---

## 5. 위험 신호 — 상위 모드(Opus)에 보고할 상황

| 신호 | 의미 |
|---|---|
| PASS 7,246 → 7,240 미만 후퇴 | 회귀 발생 |
| MetaLearner entropy < 1.5 자동 롤백 1회 | C-M-05 ConstitutionWeightTracker 호출 |
| AgentCoordinator timeout 3회 연속 | max_rounds 또는 timeout 재설정 검토 |
| Ensemble Welch t-test p > 0.05 | 앙상블 효과 통계적 비유의 |
| 월 GPU SLO $200 도달 | RetrainingScheduler 7→14 자동 연장 발동 |
| ReaderFeedback DSR 30일 미응답 1건 | 거버넌스 침해 즉시 중단 |
| 경쟁 흡수 IP 자문 미commit으로 V667~V671 진입 | C-M-11 위반 자동 차단 |
| G75 InterfaceTrace 8번째 축 데이터 < 1,000건 | 30일 audit 불충분 |
| 인간 calibration agreement < 0.5 | ConstitutionEvalV2 재정의 |

위 발생 시 자체 판단 없이 즉시 보고.

---

## 6. 22건 보강 누적 (v1.0 12 + v1.1·v1.2 10 = 22)

상세는 본안 v2.0 §8. 핵심:

| 단계 | 보강 수 | 상태 |
|---|---|---|
| v1.0 C-M-01 ~ C-M-12 | 12건 | C-M-05/06 ✅ commit / 나머지 10건 ⏳ |
| v1.1 F1·F2·F3 | 3건 | F1 V658에서 / F2 V640-PATCH 의무 / F3 V646 4-step |
| v1.2 F4 ~ F10 | 7건 | F5/F6/F7/F8 ✅ 본안 흡수 / F4/F9/F10 ⏳ |

---

## 7. 메타데이터

- **문서 ID**: LOS-PHASE-C-HANDOFF-V2.0-2026-05-26
- **선행 (deprecated)**: v1.0/v1.1/v1.2 6개 분리 문서
- **본안 docx**: `docs/sessions/literary_os_v631_phase_c_FINAL_v2.docx`
- **로컬 작업 경로**: `C:\literary_claude\claude` (회사)
- **유효 기간**: Phase C 종료(V680)까지. V681 Phase D 진입 시 별도 핸드오프 발행
