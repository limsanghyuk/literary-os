# Phase C 본안 v1.1 Errata — GitNexus 인덱스 적용 결과

**작성일**: 2026-05-25
**선행**: 본안 v1.0 Final (commit `faeb863d`, 2026-05-25 push)
**적용 가이드**: `docs/workflow/PREFLIGHT_GUIDE_v1.1.md` (V630 자산)
**적용 도구**: `tools/gitnexus_analyze.py` (AST 기반, V589 신설)
**상태**: v1.0 골격 유지, 3개 발견(F1·F2·F3) 흡수

---

## 0. 본 문서의 위치

본안 v1.0 작성 시 GitNexus 인덱스 미적용 결함을 사후 검증으로 보완. 본안 v1.0의 4 SP·14 Gate·23 ADR·12 보강 골격은 그대로 유지. 저연산 모드는 본안 v1.0 + 본 v1.1 Errata를 함께 학습한 후 SP-C.1 V631 진입.

---

## 1. GitNexus 인덱스 결과 (V630-AUDIT3)

| 축 | 값 |
|---|---|
| 총 모듈 | 790 (literary_system 508 + tests 282) |
| 총 심볼 | 14,897 (class 2,638 / method 11,383 / function 670 / test_fn 206) |
| 총 관계 | 26,146 (IMPORTS 4,363 / USES 6,972 / CALLS 14,811) |

저장: `/tmp/phaseC/gitnexus_index_v630.json`

---

## 2. 3대 발견 (F1·F2·F3)

### F1. lora_stacking_adapter.py 이미 V611 실 구현 (본안 C-M-12 정정)

**v1.0 주장**: Phase B V615에서 인터페이스만 정의, V658에서 활성화.

**v1.1 실측**: `literary_system/serving/lora_stacking_adapter.py` 이미 V611에 **실 구현 존재**. LoRAWeight dataclass + 가중치 합산 + MultiWorkCIMV2.reward_weighted_global_weight 자동 계수 + 스택 유효성 검증(계수 합 ≤ 1.0+ε) + LLM-0 스텁(apply_to_model).

**정정안**:
- C-M-12 명칭: "인터페이스 활성화" → "B2B Partner API endpoint 노출 + Multi-LoRA 합성 활성화"
- V658 작업 범위 축소: 기존 LoRAStackingAdapter를 호출하는 endpoint 추가만 신규
- 본안 v1.0 §3.2 `/generate/multi_lora` endpoint 스켈레톤 호환 유지. 출처를 V615→V611로 표기 정정.
- Phase B 핸드오프의 V615 명시도 V611로 수정 권고 (후속 작업).

### F2. literary_system/safety/safety_regression_v2.py 부재

**v1.0 주장**: Phase B V609에서 신설한 SafetyRegressionV2를 Phase C agents에서 활용.

**v1.1 실측**: `literary_system/safety/` 디렉토리 **자체 미존재**. `grep "class SafetyRegressionV2"` 0 hit. Phase B SP-B.8 V609 단계 신설 예정이었으나 V630 시점에 실제 commit되지 않음.

**정정안**:
- Phase B 누락 자산임을 인정. Phase C에서 신설 또는 Phase B 후속 보강 commit 필요.
- V647 ScriptAgent + V649 EditorAgent + V653 AgentSafetyGuard의 PreTrainSafetyResult 적용 기재는 유효 (Phase B V599 `pre_train_safety.py`는 존재 검증됨).
- **신규 작업 항목**:
  - **옵션 A** (권장): Phase C SP-C.2 V650 진입 전 'V630-AUDIT4'로 SafetyRegressionV2 신설 commit (1주)
  - **옵션 B**: Phase C SP-C.4 V676~V679 안정화 구간에서 보강
- AgentSafetyGuard (V653) 코드 스켈레톤은 pre_train_safety.py를 호출하는 형태로 1차 작성, SafetyRegressionV2 commit 후 위임 추가.

### F3. ensemble/ 마이그레이션 영향 범위 (C-M-04 강화)

**v1.0 주장**: `literary_system/agents/__init__.py`에서 `ensemble/gate8_ensemble + narrative_fitness_arbiter` 백워드 호환 re-export.

**v1.1 실측 (depth 1, 9건 importer)**:

| Importer | Import 대상 |
|---|---|
| `literary_system.ensemble.__init__` | gate8_ensemble |
| `literary_system.ensemble.__init__` | narrative_fitness_arbiter |
| `literary_system.ensemble.gate8_ensemble` | narrative_fitness_arbiter (내부) |
| `literary_system.orchestrators.full_scene_orchestrator` | gate8_ensemble (EnsembleGate, EnsembleGateResult) |
| `literary_system.orchestrators.full_scene_orchestrator` | narrative_fitness_arbiter (CandidateScore) |
| `tests.test_v389_provider_ensemble` | gate8_ensemble + narrative_fitness_arbiter |
| `tests.test_v579_duplicate_zero` | gate8_ensemble |

**정정안 (C-M-04 강화) — V646 4-step 마이그레이션**:

```python
# Step 1: agents/* 신설 (DirectorAgent + CriticAgent 등). 기존 ensemble/* 보존.

# Step 2: ensemble/__init__.py를 facade로 재구성
#   - 신규 agents/* 도 re-export
from literary_system.agents.critic_agent import CriticAgent
from literary_system.agents.agent_coordinator import AgentCoordinator
#   - 기존 alias 유지
from .gate8_ensemble import EnsembleGate, EnsembleGateResult  # legacy
from .narrative_fitness_arbiter import CandidateScore  # legacy

# Step 3: orchestrators/full_scene_orchestrator.py
#   - V646~V649 진입 시 점진적 import 경로 교체
#   - 기존: from literary_system.ensemble.gate8_ensemble import EnsembleGate
#   - 신규: from literary_system.agents.agent_coordinator import AgentCoordinator
#   - 백워드 호환: V680까지 양쪽 지원

# Step 4: tests/test_v389_provider_ensemble + test_v579_duplicate_zero
#   - Phase C에서 신규 tests/test_agents_*.py 추가 (병행 운영)
#   - V680 진입 시 legacy 테스트 정리 검토
```

---

## 3. 레거시 핵심 클래스 blast radius (depth 1)

10개 레거시 클래스 callers 측정:

| 클래스 | 활용 | callers | 검증 |
|---|---|---|---|
| LOSConstitution | v2.0 상속 (V631) | 5 | ✅ |
| LoRAInferenceGateway | ScriptAgent 직결 (V647) | 4 | ✅ |
| CanonicalBridgeV2 | PublicSDK 호출 (V656) | 3 | ✅ |
| **LoRAStackingAdapter** | **B2B endpoint (V658)** | **5** | **⚠️ F1 정정** |
| **SafetyRegressionV2** | **AgentSafetyGuard 위임 (V653)** | **0** | **❌ F2 부재** |
| CanaryController | AgentRouter 통합 (V662) | 3 | ✅ |
| phase_b_exit_gate | G75 8축 확장 (V680) | 0 | ✅ (Gate 정상) |
| EquivalenceTester | AgentEnsembleEvaluator 비교 (V652) | 3 | ✅ |
| RewardModel | MetaLearner 결합 (V631) | 4 | ✅ |
| PPOTrainer | AgentCoordinator 결합 (V650) | 4 | ✅ |

합계 31 callers (평균 3.1). v1.0 §B '15/16 존재' → v1.1 '14/16 존재 + 1건 F2 신설 + 1건 F1 출처 정정'.

---

## 4. 본안 v1.0 → v1.1 변경 사항

| 섹션 | v1.0 | v1.1 |
|---|---|---|
| C-M-12 명칭 | Phase B V615 인터페이스 활성화 | V611 실 구현 호출 endpoint (V658 신규) |
| V658 작업 범위 | LoRAStackingAdapter 활성화 신규 | 기존 V611 LoRAStackingAdapter 호출 endpoint만 신규 |
| V615 표기 | Phase B 핸드오프 V615 | V611로 정정 권고 (Phase B 후속) |
| SafetyRegressionV2 | V609에서 신설 가정 | 부재. V630-AUDIT4 또는 SP-C.4에서 신설 |
| C-M-04 | agents/__init__.py re-export | 4-step 마이그레이션 (facade + orchestrators + tests) |
| G64 검증 | AgentCoordinator 사이클 + 타임아웃 | + ensemble→agents 마이그레이션 회귀 0 |
| G72 검증 | 경쟁 흡수 5종 | + ensemble/ 의존성 0 확인 |
| G75 C8 축 | InterfaceTrace 30일 audit | + ensemble/ legacy 호출 비율 ≤ 5% |

---

## 5. 본안 v1.1 추가 위험 신호 (4건)

| # | 위험 | 임계 | 대응 |
|---|---|---|---|
| v1.1-R10 | ensemble/ legacy import 회귀 | full_scene_orchestrator 테스트 1건 FAIL | C-M-04 4-step 점검 |
| v1.1-R11 | SafetyRegressionV2 신설 지연 | SP-C.2 V650 진입 시점 미commit | SP-C.4 안정화 구간으로 이연 결정 |
| v1.1-R12 | LoRAStackingAdapter 시그니처 변경 | MultiWorkCIMV2.reward_weighted_global_weight 변경 | V658 endpoint 작성 전 재확인 의무 |
| v1.1-R13 | GitNexus 인덱스 stale | 결과 vs git diff 불일치 | 각 SP 진입 전 인덱스 재실행 (PREFLIGHT v1.1 §1.1) |

---

## 6. 저연산 모드 첫 명령 시퀀스 (v1.1 적용)

```bash
# 1. V630 AUDIT3 main HEAD 확인
cd /path/to/literary-os
git pull origin main   # faeb863d (본안 v1.0) 또는 본 v1.1 commit 이후

# 2. GitNexus 인덱스 (PREFLIGHT v1.1 §1.1)
python tools/gitnexus_analyze.py
# → 14,897 symbols 확인 (기준선 일치)

# 3. F2 SafetyRegressionV2 신설 commit (V630-AUDIT4, 옵션 A)
mkdir -p literary_system/safety
# safety_regression_v2.py 작성 (4축 자해/혐오/PII/저작권 0건)
# Phase B 핸드오프 SafetyRegressionV2 코드 스켈레톤 참조
git checkout -b fix/v630-audit4-safety-regression-v2
# ... 패치
pytest tests/safety/ -v
git commit -m "V630-AUDIT4: SafetyRegressionV2 신설 (Phase B 누락 보강, F2)"
git push origin fix/v630-audit4-safety-regression-v2

# 4. F3 ensemble facade 재구성 (V646 진입 시 1step Step 2 우선)
git checkout main && git pull
git checkout -b dev/v646-sp-c2-director + ensemble_facade
# literary_system/ensemble/__init__.py 갱신
# Step 1: agents/director_agent.py 신설
# Step 2: ensemble/__init__.py facade
# ...

# 5. SP-C.1 V631 진입 (본안 v1.0 골격 + v1.1 정정 반영)
git checkout -b dev/v631-sp-c1-constitution-v2
# los_constitution_v2.py (entropy >=1.5 본안 C-M-05)
# constitution_weight_tracker.py
pytest tests/ -q  # 7,213+ PASS 유지
git commit -m "V631 SP-C.1: LOSConstitution v2.0 + entropy 1.5 (ADR-073, C-M-05)"
```

---

## 7. 메타데이터

- **문서 ID**: LOS-PHASE-C-ERRATA-V1.1-2026-05-25
- **선행 문서**:
  - `2026-05-25_v631_phase_c_handoff_final.md` (본안 v1.0 핸드오프)
  - `literary_os_v631_phase_c_proposal_final.docx`
  - `literary_os_v631_phase_c_blueprint_final.docx`
- **본 문서 docx**: `literary_os_v631_phase_c_gitnexus_errata.docx`
- **인덱스 자료**: `/tmp/phaseC/gitnexus_index_v630.json` (로컬, GitHub 미commit)
- **유효 기간**: Phase C 종료(V680)까지. 매 SP 진입 시 GitNexus 인덱스 재실행 의무.
