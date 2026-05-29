# ADR-019: NIL Stability Module — 수렴 안정화

**상태**: Accepted  
**날짜**: V512  
**결정자**: Literary OS Architecture Team  

---

## 맥락 (Context)

AdaptiveMomentumWeights(AMW) 의 α 파라미터는 1-step SGD 로 갱신된다.
PhysicsRewardBridge 를 통해 advantage 값이 전파될 때, 특정 조건에서:

1. **발산(Divergence)**: |Δα| 가 크게 유지될 경우 α 가 경계 [0.30, 0.80] 밖으로 탈출 시도
2. **진동(Oscillation)**: α 가 목표 근방에서 ±를 반복하며 수렴하지 않음
3. **경계 응축(Boundary Condensation)**: α 가 경계에 밀착해 다양성을 잃음

이를 방치하면 NarrativeTensionCurve 의 L_final 이 개선되지 않거나, MAE 에이전트 가중치가 불안정해진다.

---

## 결정 (Decision)

`NILStabilityModule` 을 NIL 루프 내 독립 감시 레이어로 배치한다.

### 감지 규칙

| 이벤트 | 조건 | 대응 |
|--------|------|------|
| DIVERGENCE | `\|Δα\|` > 0.10 연속 3회 | LR × 0.50 (최저 0.05) |
| OSCILLATION | sign 교차 ≥ 5회 / 최근 10 epoch | LR × 0.70 (최저 0.10) |
| BOUNDARY_LOW | α ≤ 0.305 | alarm (LR 변경 없음) |
| BOUNDARY_HIGH | α ≥ 0.795 | alarm (LR 변경 없음) |

### 아키텍처

```
AMW.update()
  └─ NILStabilityModule.update(dim, α_new, α_old)
       ├─ _check_divergence()  → lr_factor_diverge 갱신
       ├─ _check_oscillation() → lr_factor_osc 갱신
       └─ check_boundary()     → alarm event

PhysicsRewardBridge.process()
  └─ NILStabilityModule.get_effective_lr("physics", base_lr)
```

### LR 계층 구조

```
effective_lr = base_lr × lr_factor_diverge × lr_factor_osc
```

- AMW 차원별 계수 독립 관리
- PhysicsRewardBridge 는 "physics" 키 사용 (AMW 와 별개)
- 모듈별 최솟값: `amw` = min(모든 차원 계수)

---

## 결과 (Consequences)

### 긍정
- α 발산 사고 방지로 NIL 루프 안정성 향상
- 진동 감지로 수렴 속도 개선
- MetaLearner(V515+) 의 outer-loop 안정성 사전 보장

### 부정
- LR 축소가 누적될 경우 학습 정체 위험 → V519 통합 테스트에서 검증

---

## 연계 ADR

- ADR-016: NIE-L7 Container (NILStabilityModule 은 V512 기본 비활성, `enable_stability=True` 로 활성화)
- ADR-020: MetaLearner (외부 loop 에서 lr_factor 리셋 가능)
