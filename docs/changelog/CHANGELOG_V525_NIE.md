# CHANGELOG — Literary OS V525 (Phase 3 NIE v2.0)

Release Date: 2026-05-17  
Base: V497-HF (4818 PASS)  
Final: V525 (5061 PASS, +243 NIE-specific tests)

---

## Phase 3 Overview

NIE v2.0 (Narrative Intelligence Engine) 는 Literary OS 에 수학적 자기강화 루프를 도입한다.
6-단계 NIL(Narrative Intelligence Loop) 이 씬 단위로 실행되며, 장르·에피소드·작품 레벨에서
메타-학습을 통해 점진적으로 서사 품질 지표(L_final)를 최소화한다.

NIL 루프: CIM → TriangleTension → AMW → MAE → PhysicsRewardBridge → RAG/TensionCurve

---

## V498 — PhysicsRewardBridge + NIE-L7 Container

### New Modules
- `literary_system/nie/physics_reward_bridge.py`
  - NIL Step 5 핵심: L_final 보상 신호 계산
  - BridgeResult: scene_id, reward, advantage, baseline, coefficients_updated, delta
  - ADR-015 LLM-0 정책: MAEOrchestrator/agent/judge 만 LLM 호출 허용
- `literary_system/nie/nie_l7_container.py`
  - NIE-L7 컨테이너 스켈레톤 (7-Layer 통합 진입점)

### New ADRs
- `docs/adr/ADR-015-physics-reward-bridge-llm0-policy.md`
- `docs/adr/ADR-016-mae-v2-reader-sub-personas.md`

---

## V499~V500 — MAEAgentsV2 + AdaptiveMomentumWeights

### New Modules
- `literary_system/nie/mae_agents_v2.py`
  - MAEOrchestratorV2: 4종 에이전트 (StructureAgent, EmotionAgent, ThemeAgent, PacingAgent)
  - Reader 서브-페르소나 3종 per 에이전트
  - evaluate() → MAEResultV2 (verdict_list, overall_pass, pass_rate, sigma)
- `literary_system/nie/adaptive_momentum_weights.py`
  - 4차원 α 벡터 [tension, sympathy, dread, catharsis] SGD 학습
  - update(emotion_feedback) → EmotionalVector
  - ADR-017 수식: α_new = clip(α + lr·advantage·feedback, [0.05, 0.95])

### New ADRs
- `docs/adr/ADR-017-adaptive-momentum-weights.md`

---

## V501~V504 — CharacterInfluenceMatrix

### New Modules
- `literary_system/nie/character_influence_matrix.py`
  - CIM: 캐릭터 영향 행렬 (PageRank 기반 Influence Score)
  - SparseCIM: 희소 행렬 최적화 (1000+ 캐릭터 지원)
  - TopKTriangleFilter: 상위 K 삼각형 텐션 관계 추출
  - 5-Tier 영향력 분류: PROTAGONIST/DEUTERAGONIST/SUPPORTING/MINOR/BACKGROUND
  - PageRankCalculator: 반복 수렴 (tol=1e-6, max_iter=100)

### New ADRs
- `docs/adr/ADR-018-character-influence-matrix.md` (Part 1)

---

## V505~V508 — TemporalCIM

### New Modules
- `literary_system/nie/temporal_cim.py`
  - W[t][i][j]: 시간축 3D 캐릭터 영향 텐서
  - 플래시백 가중치 decay: w_flashback = w_current × FLASHBACK_DECAY^Δt
  - 에피소드 경계 처리: set_episode() + _apply_boundary_decay()
  - TemporalTriangleExtractor: 시간 통합 삼각형 관계 추출

### New ADRs
- `docs/adr/ADR-018-temporal-cim.md` (Part 2, ADR-018 확장)

---

## V509~V511 — QueryIntentClassifier + NarrativeTensionCurve

### New Modules
- `literary_system/nie/query_intent_classifier.py`
  - 3종 인텐트 분류: CHARACTER / EMOTIONAL / PLOT_EVENT
  - DramaLexicon: 한국 드라마 장르별 어휘 사전 (멜로/스릴러/로맨틱코미디/가족)
  - RAG 쿼리 라우팅 최적화
- `literary_system/nie/narrative_tension_curve.py`
  - T_ideal(t) = base + a1·sin(2πt−0.50) + a2·sin(6πt)
  - L_final = MSE(T_ideal, T_actual) + λ·Σ|α_i − α_target_i|²
  - record() + get_l_final() + update_fourier_coefficients()

---

## V512 — NILStabilityModule (ADR-019)

### New Modules
- `literary_system/nie/nil_stability_module.py`
  - 발산 감지: |Δα| > 0.10 × 3연속 → LR × 0.50
  - 진동 감지: 부호 교차 5회/10 에폭 → LR × 0.70
  - 경계 알람: BOUNDARY_INNER_LOW=0.305, BOUNDARY_INNER_HIGH=0.795
  - LR 계층: effective = base_lr × lr_factor_diverge × lr_factor_osc
  - StabilityEvent: NORMAL / DIVERGENCE / OSCILLATION / BOUNDARY_LOW / BOUNDARY_HIGH

### New ADRs
- `docs/adr/ADR-019-nil-stability.md`

---

## V513 — AgentCalibrator

### New Modules
- `literary_system/nie/agent_calibrator.py`
  - Phase1 (기본 추적) → Phase2 (격주 RubricCalibrator 활성화)
  - PHASE2_ACTIVATION_WORKS=10, BIWEEKLY_INTERVAL_WORKS=2
  - RubricCalibrator: rubric = 0.70×pass_rate + 0.30×sigma_score
  - iterative floor-budget 정규화 (MIN_WEIGHT=0.05 보장)
  - compute_new_weights(): 발산 방지 반복 알고리즘

---

## V515 — MetaLearner (ADR-020)

### New Modules
- `literary_system/nie/meta_learner.py`
  - 외부 루프 SGD: 작품 30편 후 활성화 (ACTIVATION_WORKS=30)
  - advantage = L_final − EMA_baseline (BASELINE_DECAY=0.90)
  - 메타-파라미터 조정: AMW LR / λ / lr_factor / agent_weight
  - 개선 시 (advantage < −0.10): stability LR × 1.10 (이완)
  - 악화 시 (advantage > +0.10): stability LR × 0.90 + 에이전트 가중치 균등화

### New ADRs
- `docs/adr/ADR-020-meta-learner.md`

---

## V518 — TIdealLearner (ADR-022)

### New Modules
- `literary_system/nie/tideal_learner.py`
  - 장르별 푸리에 계수 SGD (T_LR=0.005, CLIP_GRAD=0.50)
  - T_ideal(t) = base + a1·sin(2πt−0.50) + a2·sin(6πt)
  - 장르별 초기화: melodrama / thriller / romcom / family / default
  - 그래디언트: err·sin(2πt), err·sin(6πt) 로 a1, a2 업데이트
  - NarrativeTensionCurve.update_fourier_coefficients() 직접 호출

### New ADRs
- `docs/adr/ADR-022-tideal-learner.md`

---

## V519~V521 — NILOrchestrator (ADR-021)

### New Modules
- `literary_system/nie/nil_orchestrator.py`
  - 전체 NIL 6단계 루프 통합 오케스트레이터
  - NIEConfig: enable_stability / enable_temporal_cim / enable_meta_learner / enable_rag_classifier
  - process_scene(SceneInput) → NILResult:
    1. CIM.update() + TemporalCIM.update()
    2. CIM.top_k_triangles()
    3. AMW.update() → EmotionalVector → dict 변환
    4. MAEOrchestratorV2.evaluate() → MAEResultV2
    5. 인라인 보상 브리지 (LLM-0 준수): BridgeResult 생성
    6. NarrativeTensionCurve.record() + QueryIntentClassifier 라우팅
  - complete_work(genre) → WorkCompletionResult: TIdeal → AgentCalibrator → MetaLearner
  - complete_episode(): TemporalCIM 에피소드 경계 처리

### Architecture Note
  - PhysicsRewardBridge V430 레거시 인터페이스(SceneMetrics) 우회
  - MAEOrchestratorV2 verdict 결과를 인라인으로 처리
  - BridgeResult 데이터클래스만 임포트하여 타입 호환성 유지

### New ADRs
- `docs/adr/ADR-021-nil-orchestrator-integration.md`

---

## V522 — Gate25

### New Modules
- `literary_system/nie/gate25.py`
  - 5-Gate NIE v2.0 릴리즈 게이트
  - G1: L_final ≤ 0.15 (서사 손실 임계)
  - G2: agent_sigma ≤ 0.10 (에이전트 일관성)
  - G3: NPS ≥ 25 (독자 순추천지수)
  - G4: cost_usd_per_episode ≤ $5.00 (에피소드당 비용)
  - G5: episode_pass_rate ≥ 0.90 (에피소드 통과율)
  - run_from_orchestrator() 헬퍼: NILOrchestrator 상태 직접 추출

---

## V523~V525 — NIE v2.0 통합 릴리즈

### Release Actions
- `pyproject.toml`: version 4.9.2 → 5.2.5
- `manifests/live_core_manifest.json`: V481 → V525 (Gate 14종 전원 pass)
- `MANIFEST_V525_NIE.md`: 신규 모듈 14종 + ADR 8종 + 테스트 243건 목록
- `CHANGELOG_V525_NIE.md`: V498~V525 전체 변경 이력

### Test Summary
| 구간 | 누적 PASS | 증가 |
|------|-----------|------|
| V497-HF 기준선 | 4818 | — |
| V498 | 4844 | +26 |
| V499~V500 | 4874 | +30 |
| V501~V504 | 4909 | +35 |
| V505~V508 | 4932 | +23 |
| V509~V511 | 4966 | +34 |
| V512~V514 | 5003 | +37 |
| V515~V518 | 5038 | +35 |
| V519~V522 | 5061 | +23 |
| **V525 최종** | **5061** | **+243 total** |

---

## Breaking Changes

없음. 모든 Phase 2 모듈과 하위 호환 유지.

## Deprecations

없음.

## Known Issues

- PhysicsRewardBridge V430 레거시 인터페이스: NILOrchestrator 에서 인라인 구현으로 우회됨
  (V530+ 에서 통합 예정)
- OTel exporter teardown 경고: 기능과 무관한 테스트 아티팩트

