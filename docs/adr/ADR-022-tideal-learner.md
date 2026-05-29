# ADR-022: TIdealLearner — T_ideal Fourier 계수 적응

**상태**: Accepted  
**날짜**: V518  
**결정자**: Literary OS Architecture Team  

---

## 맥락 (Context)

`NarrativeTensionCurve` 의 T_ideal 은 장르 불문 고정 Fourier 계수를 사용한다.

```
T_ideal(t) = 0.60 + 0.40·sin(2πt − 0.50) + 0.20·sin(6πt)
```

실제 드라마 작품마다 최적 긴장 곡선은 다르다. 멜로드라마는 완만한 상승,
스릴러는 가파른 피크, 로맨틱 코미디는 이중 봉우리 구조를 선호한다.

---

## 결정 (Decision)

`TIdealLearner` 를 도입해 장르·작품별로 Fourier 계수 {base, a1, a2} 를 SGD 로 적응시킨다.

### 계수 범위

| 계수 | 범위 |
|------|------|
| `base` | [0.40, 0.80] |
| `a1` (fundamental) | [0.10, 0.60] |
| `a2` (harmonic) | [0.05, 0.40] |

### 장르별 초기값

| 장르 | base | a1 | a2 |
|------|------|----|----|
| melodrama | 0.60 | 0.45 | 0.20 |
| thriller | 0.65 | 0.50 | 0.25 |
| romcom | 0.55 | 0.35 | 0.15 |
| family | 0.58 | 0.38 | 0.18 |
| default | 0.60 | 0.40 | 0.20 |

### SGD 갱신

```
∂L/∂base = (2/N) · Σ (T_ideal(t) − T_actual(t))
∂L/∂a1   = (2/N) · Σ (T_ideal(t) − T_actual(t)) · sin(2πt − 0.50)
∂L/∂a2   = (2/N) · Σ (T_ideal(t) − T_actual(t)) · sin(6πt)

θ ← θ − T_LR · ∇θ  (T_LR = 0.005, grad clip = ±0.50)
```

### 반영

`TIdealLearner.update()` 내부에서 `tension_curve.update_fourier_coefficients()` 를 직접 호출한다.

---

## 결과 (Consequences)

### 긍정
- 장르 맞춤 T_ideal 로 L_tension 지속 감소
- 히스토리 창(5편) 을 통해 일시적 이상치에 대한 내성 확보

### 부정
- 장르 지정 없이 사용 시 "default" 계수로만 수렴

---

## 연계 ADR

- ADR-020: MetaLearner (λ 갱신 — L_final 전체 최적화)
- ADR-016: NIE-L7 Container (V518+ `enable_meta_learner=True` 로 활성화)
