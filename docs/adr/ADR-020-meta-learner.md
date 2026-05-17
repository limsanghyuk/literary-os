# ADR-020: MetaLearner — NIL Outer-loop Meta-Learning

**상태**: Accepted  
**날짜**: V515  
**결정자**: Literary OS Architecture Team  

---

## 맥락 (Context)

NIL 루프의 내부 학습(AMW SGD, PhysicsRewardBridge Policy Gradient)은 씬 단위로 동작한다.
그러나 **작품 단위의 글로벌 품질 추세**(L_final 시계열)는 내부 루프만으로 포착되지 않는다.

30편 이상의 작품을 처리한 시점에는 충분한 통계가 쌓이므로,
메타 파라미터를 최적화할 outer-loop 도입이 가능해진다.

---

## 결정 (Decision)

`MetaLearner` 를 NIL Outer-loop 레이어로 도입한다.

### 활성화 조건

```
works_count >= ACTIVATION_WORKS (= 30)
```

### Meta-parameters

| 파라미터 | 범위 | 대상 컴포넌트 |
|---------|------|--------------|
| `amw_lr` | [0.001, 0.050] | AdaptiveMomentumWeights |
| `lambda` (λ) | [0.10, 0.80] | NarrativeTensionCurve |
| `lr_factor` | [0.30, 1.50] | NILStabilityModule |
| `agent_weights` | per agent | MAEOrchestratorV2 |

### Outer-loop SGD

```
advantage = L_final - L_baseline          (EMA decay=0.90)
θ_meta ← θ_meta - META_LR × advantage
```

### 개선/악화 임계값

| advantage | 판정 | 대응 |
|-----------|------|------|
| < -0.10 | 개선 중 | NILStabilityModule LR 제약 10% 완화 |
| > +0.10 | 악화 중 | agent_weights 균등화, LR 제약 10% 강화 |

---

## 결과 (Consequences)

### 긍정
- 내부 루프만으로는 달성 불가한 long-horizon 최적화 가능
- MetaState.amw_lr 이 작품 진행에 따라 최적 값으로 수렴

### 부정
- 30편 이전에는 완전 비활성(force_activate() 로 테스트 가능)
- Outer-loop LR 설정이 잘못될 경우 meta-parameter 발산 위험

---

## 연계 ADR

- ADR-019: NILStabilityModule (안정성 제약 레이어)
- ADR-022: TIdealLearner (T_ideal Fourier 계수 적응 — 별도 outer-loop)
