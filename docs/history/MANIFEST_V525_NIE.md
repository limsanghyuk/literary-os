# MANIFEST — Literary OS V525 NIE v2.0

Version: 5.2.5  
Release Date: 2026-05-17  
Phase: Phase 3 NIE v2.0 (Narrative Intelligence Engine)

---

## NIE Module Inventory

### literary_system/nie/ (14 modules)

| 파일 | 버전 | 핵심 클래스 | 역할 |
|------|------|------------|------|
| `__init__.py` | V498 | — | NIE 패키지 진입점 |
| `physics_reward_bridge.py` | V498 | PhysicsRewardBridge, BridgeResult | NIL Step5 보상 신호 |
| `nie_l7_container.py` | V498 | NIE_L7_Container | 7-Layer 통합 컨테이너 |
| `mae_agents_v2.py` | V499 | MAEOrchestratorV2, MAEResultV2 | 4종 MAE 에이전트 |
| `adaptive_momentum_weights.py` | V500 | AdaptiveMomentumWeights, EmotionalVector | α SGD 학습 |
| `character_influence_matrix.py` | V501~V504 | CIM, SparseCIM, TopKTriangleFilter | PageRank 영향 행렬 |
| `temporal_cim.py` | V505~V508 | TemporalCIM, TemporalTriangleExtractor | W[t][i][j] 시간축 텐서 |
| `query_intent_classifier.py` | V509~V510 | QueryIntentClassifier, DramaLexicon | 인텐트 분류 + RAG 라우팅 |
| `narrative_tension_curve.py` | V511 | NarrativeTensionCurve | T_ideal Fourier 곡선 + L_final |
| `nil_stability_module.py` | V512 | NILStabilityModule, StabilityEvent | 발산/진동 감지 + LR 조정 |
| `agent_calibrator.py` | V513 | AgentCalibrator, RubricCalibrator | Phase2 격주 재교정 |
| `meta_learner.py` | V515 | MetaLearner, MetaUpdateResult | 외부 루프 SGD (30편 후) |
| `tideal_learner.py` | V518 | TIdealLearner, FourierUpdate | 장르별 Fourier SGD |
| `nil_orchestrator.py` | V519~V521 | NILOrchestrator, NIEConfig | 6단계 NIL 통합 루프 |
| `gate25.py` | V522 | Gate25, Gate25Result | 5-Gate NIE 릴리즈 게이트 |

---

## ADR Inventory

### docs/adr/ (Phase 3 신규, ADR-015~ADR-022)

| ADR | 제목 | 결정 핵심 |
|-----|------|-----------|
| ADR-015 | PhysicsRewardBridge LLM-0 Policy | MAEOrchestrator/agent/judge 만 LLM 호출 |
| ADR-016 | MAE v2 Reader Sub-Personas | 에이전트당 Reader 3종 서브-페르소나 |
| ADR-017 | Adaptive Momentum Weights SGD | α ∈ [0.05, 0.95] 클리핑 SGD |
| ADR-018 | CIM + TemporalCIM Architecture | PageRank + W[t][i][j] 플래시백 decay |
| ADR-019 | NIL Stability Module | 발산 × 3 → LR×0.50, 진동 × 5/10 → LR×0.70 |
| ADR-020 | MetaLearner Outer-Loop SGD | advantage = L_final − EMA_baseline |
| ADR-021 | NILOrchestrator Integration | PhysicsRewardBridge 인라인 우회 결정 |
| ADR-022 | TIdealLearner Fourier Adaptation | CLIP_GRAD=0.50, T_LR=0.005 |

---

## Test Inventory

### Phase 3 NIE 신규 테스트 파일 (8종, 243건)

| 파일 | 테스트 수 | 대상 모듈 |
|------|-----------|-----------|
| `tests/test_v498_physics_reward_bridge.py` | 26 | PhysicsRewardBridge, NIE-L7 |
| `tests/test_v499_v500_mae_amw.py` | 30 | MAEOrchestratorV2, AMW |
| `tests/test_v501_v504_cim.py` | 35 | CIM, SparseCIM, TopKTriangleFilter |
| `tests/test_v505_v508_temporal_cim.py` | 23 | TemporalCIM |
| `tests/test_v509_v511_intent_tension.py` | 34 | QueryIntentClassifier, NarrativeTensionCurve |
| `tests/test_v512_v514_stability_calibrator.py` | 37 | NILStabilityModule, AgentCalibrator |
| `tests/test_v515_v518_meta_tideal.py` | 35 | MetaLearner, TIdealLearner |
| `tests/test_v519_v522_nil_gate.py` | 23 | NILOrchestrator, Gate25 |
| **합계** | **243** | |

---

## Gate25 Thresholds

| Gate | 지표 | 임계값 | 방향 |
|------|------|--------|------|
| G1 | L_final (서사 손실) | 0.15 | ≤ |
| G2 | agent_sigma (에이전트 표준편차) | 0.10 | ≤ |
| G3 | NPS (순추천지수) | 25 | ≥ |
| G4 | cost_usd_per_episode | $5.00 | ≤ |
| G5 | episode_pass_rate | 0.90 | ≥ |

---

## Key Constants Reference

### NILStabilityModule (ADR-019)
```
DIVERGE_THRESHOLD = 0.10      # |Δα| 발산 임계
DIVERGE_CONSECUTIVE = 3       # 연속 발산 횟수
LR_DIVERGE_FACTOR = 0.50      # 발산 시 LR 감소
OSCILLATION_SIGN_CROSS = 5    # 진동 부호 교차 횟수
LR_OSC_FACTOR = 0.70          # 진동 시 LR 감소
BOUNDARY_INNER_LOW = 0.305    # 하한 경계
BOUNDARY_INNER_HIGH = 0.795   # 상한 경계
```

### MetaLearner (ADR-020)
```
ACTIVATION_WORKS = 30         # 외부 루프 활성화 작품 수
META_LR = 0.01                # 메타-학습률
BASELINE_DECAY = 0.90         # EMA baseline 감쇠율
AMW_LR_MIN / MAX = 0.001 / 0.1
LAMBDA_MIN / MAX = 0.01 / 1.0
```

### TIdealLearner (ADR-022)
```
T_LR = 0.005                  # Fourier 계수 학습률
CLIP_GRAD = 0.50              # 그래디언트 클리핑
GENRE_WINDOW = 5              # 장르 슬라이딩 윈도우
```

### AgentCalibrator
```
PHASE2_ACTIVATION_WORKS = 10  # Phase2 전환 작품 수
BIWEEKLY_INTERVAL_WORKS = 2   # 격주 교정 간격
MIN_WEIGHT = 0.05             # 에이전트 최소 가중치
WEIGHT_ADJUST_CAP = 0.15      # 1회 가중치 조정 상한
```

---

## Full Test Count

| 구분 | 수량 |
|------|------|
| 전체 통과 | 5061 |
| 전체 스킵 | 20 |
| 전체 실패 | 0 |
| Phase3 NIE 전용 | 243 |
| Phase1+2 유산 | 4818 |

---

## File Counts

```
literary_system/nie/          15 files (14 modules + __init__)
docs/adr/                     8 new ADRs (ADR-015 ~ ADR-022)
tests/                        8 new test files (Phase3 NIE)
manifests/                    live_core_manifest.json (V525)
```

