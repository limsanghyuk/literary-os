# Phase C 본안 v1.2 — V640 생존 분석 (F4~F10)

**작성일**: 2026-05-26
**기준선**: V640 main HEAD `305742df` (v11.10.0, FeedbackIntegrator)
**선행**: 본안 v1.0 (`faeb863d`) + v1.1 Errata (`1dd93233`)
**상태**: v1.0 골격 유지, v1.1 F1·F2·F3 + v1.2 F4~F10 누적 흡수
**적용 도구**: GitNexus 재인덱싱 (V640 시점) + PREFLIGHT_GUIDE_v1.1 + DEV_PROTOCOL_v2.0 + PACKAGING_PROTOCOL_v1.0

---

## 0. V640 GitNexus 재인덱싱

| 축 | V630 | V640 | 증가 |
|---|---|---|---|
| 모듈 | 790 | 810 | +20 |
| 심볼 | 14,897 | 15,527 | +630 |
| IMPORTS | 4,363 | 5,769 | +1,406 |
| CALLS | 14,811 | 45,178 | +30,367 |

---

## 1. V631~V640 commit 진행 현황

| V | commit | 모듈 | ADR | 본안 v1.0 매핑 |
|---|---|---|---|---|
| V631 | `3d9382cb` | LOSConstitutionV2 (Bayesian Optuna + entropy≥1.5) | ADR-098 | ADR-073 (F5) |
| V632 | `738bd5b6` | ConstitutionWeightTracker | ADR-099 | ADR-074 (F5) |
| V633 | `d8ea1e0a` | PatternLibraryV2 | ADR-075 | ADR-075 |
| V634 | `b591bcc7` | RetrainingScheduler F1 drift | ADR-076 | ADR-076 |
| V635 | `a6485094` | AutoPromotionGate G62 | ADR-077 | ADR-077 |
| V636 | `80fabaa2` | SelfLearningMonitor | ADR-078 | ADR-078 |
| V637 | `b034c708` | ConstitutionEvalV2 + C-M-06 보강 | ADR-079 | ADR-079 |
| V638 | `deae0bb0` | ContaminationDetector | ADR-080 | ADR-080 |
| V639 | `cfc37e34` | **DataAugmentationController** (본안 미포함) | ADR-081 | ADR-081 (F7) |
| V640 | `305742df` | **FeedbackIntegrator** (본안 미포함) | ADR-082 | ADR-082 (F7) |

추가 운영 문서:
- `docs/workflow/DEV_PROTOCOL_v2.0.md` (commit `17e70acd`, F6)
- `docs/workflow/PACKAGING_PROTOCOL_v1.0.md` (commit `46bae089`+`db45c05d`, F6)

---

## 2. 7대 신규 발견 (F4 ~ F10)

### F4. constitution/ 디렉토리 비대화 — 11 모듈

V631~V640 모든 신규 모듈이 `literary_system/constitution/` 단일 디렉토리에 집중. 본안 v1.0 가정의 patterns/, monitoring/, feedback/ 분산과 불일치.

| 본안 가정 경로 | 실제 V640 경로 |
|---|---|
| `literary_system/patterns/pattern_library_v2.py` | `literary_system/constitution/pattern_library_v2.py` |
| `literary_system/finetune/retraining_scheduler.py` | `literary_system/constitution/retraining_scheduler.py` |
| `literary_system/monitoring/self_learning_monitor.py` | `literary_system/constitution/self_learning_monitor.py` |
| `literary_system/monitoring/contamination_detector.py` | `literary_system/constitution/contamination_detector.py` |
| `literary_system/feedback/data_augmentation_controller.py` | `literary_system/constitution/data_augmentation_controller.py` |
| `literary_system/feedback/feedback_integrator.py` | `literary_system/constitution/feedback_integrator.py` |

**정정안**:
- 본안 §6 모듈 매트릭스 갱신: 실제 경로로 정정
- V645 G63 통과 후 1주 할당하여 서브패키지 분리 (constitution/learning/, constitution/monitoring/, constitution/feedback/) — facade re-export로 백워드 호환
- 또는 V680까지 그대로 두고 Phase D에서 재구성 (부담 감소)

### F5. ADR 번호 체계 편차

본안 v1.0 ADR-073~095 (23건) 가정 vs 실제 V631 ADR-098 / V632 ADR-099 / V633~V640 ADR-075~082 혼재.

**정정안**:
- LOSConstitutionV2 (V631): ADR-073 → **ADR-098** 정정
- ConstitutionWeightTracker (V632): ADR-074 → **ADR-099** 정정
- ADR-073/074는 미사용 (deprecated)
- 본안 누적 ADR: ADR-075~095 (21건) + ADR-098 + ADR-099 (2건) = 23건 유지

### F6. DEV_PROTOCOL_v2.0 + PACKAGING_PROTOCOL_v1.0 본안 미반영

| 문서 | 핵심 |
|---|---|
| DEV_PROTOCOL_v2.0 | Preflight 필수화 + 패키지 비교 검증 + CLAUDE.md 경고 |
| PACKAGING_PROTOCOL_v1.0 | ZIP 검증 프로토콜 (파일 수 1,200 기준, 런타임 포함 주석) |

**정정안**:
- 본안 §0 필수 가이드 확장: PREFLIGHT_GUIDE_v1.1 → **+ DEV_PROTOCOL_v2.0 + PACKAGING_PROTOCOL_v1.0**
- 각 SP 진입 전 Preflight + 패키지 비교 의무
- Phase C 릴리즈 commit (V645/V655/V665/V680) 시 PACKAGING ZIP 검증 ADR 부속 의무

### F7. V639/V640 계획 편차

본안 v1.0 SP-C.1:
- V639: KoreanDrama-Suite-v1 HuggingFace 비공개 등록 준비
- V640: MetaLearner 1사이클 완료 검증

실제 commit:
- V639: DataAugmentationController (ADR-081)
- V640: FeedbackIntegrator (ADR-082)

**정정안 (SP-C.1 V641~V645 재배치)**:

| V | 원본 본안 | v1.2 정정 |
|---|---|---|
| V641 | MetaLearner 1사이클 | MetaLearner 1사이클 + Krippendorff α 1차 측정 + **SafetyRegressionV2 신설 (F9 의무)** |
| V642 | 2사이클 | 2사이클 + DataAugmentationController(V639) 통합 검증 |
| V643 | 3사이클 | 3사이클 + FeedbackIntegrator(V640) 통합 검증 |
| V644 | 4사이클 | 4사이클 + 가중치 수렴 확인 |
| V645 | SelfLearningGate G63 | G63 + (선택) constitution/ 서브패키지 분리 |

Suite 패키징은 SP-C.2 V655 G67 Suite Registration으로 이연.

### F8. SP-C.2 모듈 경로 V640 시점 충돌 0건 (안전)

V640에 `literary_system/agents/`, `eval/agent_*` 디렉토리/파일 모두 미존재. 본안 V646~V655 8개 신규 모듈 모두 충돌 없음.

`/tmp/los_v640`에서 검증:
- `agents/director_agent.py` ✅ 안전
- `agents/script_agent.py` ✅ 안전
- `agents/critic_agent.py` ✅ 안전
- `agents/editor_agent.py` ✅ 안전
- `agents/agent_coordinator.py` ✅ 안전
- `agents/prompt_cache_layer.py` ✅ 안전
- `agents/agent_trace_logger.py` ✅ 안전
- `eval/agent_ensemble_evaluator.py` ✅ 안전

### F9. SafetyRegressionV2 V640 시점 여전히 미신설 (F2 강화)

`literary_system/safety/` 디렉토리 V640에도 부재. v1.1 Errata F2 권고 commit 안 됨.

**v1.2 강화**:
- V641 진입 시 'V640-PATCH'로 SafetyRegressionV2 신설 **의무** (옵션 A 권장)
- 임계 앞당김: 'SP-C.2 V650 진입 시점' → **'SP-C.1 V641 진입 시점'**
- 미신설 상태로 V650 진입 차단

### F10. ensemble/ 마이그레이션 진행도 0% (F3 미진행)

V640 시점 `literary_system/agents/` 디렉토리 자체 미존재 → ensemble/ 4-step 마이그레이션 0단계.

**상태**: V646 SP-C.2 진입 시점에 일괄 진행 계획 유지 (v1.1 4-step 그대로).

---

## 3. SP-C.1 잔여 (V641~V645) 권고 작업

```bash
# V641 진입 (가장 중요: SafetyRegressionV2 신설 의무)
cd /path/to/literary-os
git pull origin main   # 305742df 또는 이후

# F9: SafetyRegressionV2 신설 (V640-PATCH)
git checkout -b fix/v640-patch-safety-regression-v2
mkdir -p literary_system/safety
# safety_regression_v2.py 작성 (4축: 자해/혐오/PII/저작권 0건)
# tests/safety/test_safety_regression_v2.py 작성
pytest tests/safety/ -v
git commit -m "V640-PATCH: SafetyRegressionV2 신설 (Phase B 누락 보강, F2/F9)"
git push origin fix/v640-patch-safety-regression-v2

# V641 본 작업
git checkout main && git pull
git checkout -b dev/v641-sp-c1-metalearner-cycle1
# MetaLearner 1사이클 실행 + Krippendorff α 1차 측정
pytest tests/ -q   # 7,213+ PASS 유지
git commit -m "V641 SP-C.1: MetaLearner 1사이클 + Krippendorff α (F7)"
```

---

## 4. 누적 변경 사항 (v1.0 → v1.1 → v1.2)

| 발견 | 문서 | 상태 | 요지 |
|---|---|---|---|
| F1 | v1.1 | 정정 | LoRAStackingAdapter V611 실 구현 (V615 → V611) |
| F2 | v1.1→v1.2 강화 | **미해결** | SafetyRegressionV2 V640 미신설 → V641 의무 |
| F3 | v1.1 | 미진행 | ensemble/ 4-step V646 일괄 |
| F4 | v1.2 | 신규 | constitution/ 11 모듈 비대화 |
| F5 | v1.2 | 신규 | ADR-073/074 → ADR-098/099 정정 |
| F6 | v1.2 | 신규 | DEV_PROTOCOL_v2.0 + PACKAGING_PROTOCOL_v1.0 흡수 |
| F7 | v1.2 | 신규 | V639/V640 편차 → V641~V645 재배치 |
| F8 | v1.2 | 안전 | SP-C.2 충돌 0건 |
| F9 | v1.2 | 강화 | F2 임계 V650→V641 |
| F10 | v1.2 | 미진행 | F3 진행 0% |

---

## 5. 메타데이터

- **문서 ID**: LOS-PHASE-C-SURVIVAL-V1.2-2026-05-26
- **선행**: v1.0 `2026-05-25_v631_phase_c_handoff_final.md`, v1.1 `2026-05-25_v631_phase_c_errata_v1.1.md`
- **본 문서 docx**: `literary_os_v631_phase_c_survival_v1.2.docx`
- **인덱스 자료**: `/tmp/phaseC/gn_v640.json` (로컬, GitHub 미commit)
- **로컬 작업 경로**: `C:\literary_claude\claude` (회사, 2026-05-26 갱신)
