# CHANGELOG — V545 HF (Hotfix)

**릴리즈일**: 2026-05-17  
**기준**: V545 ASD (5210 PASS / 20 SKIP / 0 FAIL)  
**분류**: Pre-Phase 6 Stage A 핫픽스

---

## 수정 항목

### [B1] NarrativeTensionCurve.ideal_curve() — Fourier 합성값 클립

- **파일**: `literary_system/nie/narrative_tension_curve.py`
- **증상**: Fourier 합성 결과값이 [0.0, 1.0] 범위를 초과 (최대 1.1514, 12/100점)
- **원인**: `ideal_curve()`가 `t_ideal()` 반환값을 무클립 반환
- **수정**: `max(0.0, min(1.0, self.t_ideal(...)))` 클립 적용
- **ADR 근거**: ADR-020 §3.1 "T_ideal ∈ [0.0, 1.0] 보장"

### [B2] NarrativeTensionCurve.compute_l_final() — λ 계수 역전 수정

- **파일**: `literary_system/nie/narrative_tension_curve.py`
- **증상**: L_final 수식이 `L_tension + λ·L_coverage`로 구현되어 ADR-020 규격 위반
- **원인**: ADR-020 §4.2 수식 `L_final = λ·L_tension + (1-λ)·L_coverage`가 잘못 구현됨
- **수정**: `self._lambda * l_tension + (1 - self._lambda) * l_coverage`로 교정
- **연관**: `tests/test_v509_v511_rag_tension.py::test_l_final_structure` 기대값 갱신

### [B3] NIEContainer 외부 참조 별칭 추가

- **파일**: `literary_system/nie/nie_l7_container.py`
- **증상**: 매니페스트·NILOrchestrator 등이 `NIE_L7_Container`로 참조 시 ImportError
- **수정**: `NIE_L7_Container = NIEContainer` 별칭 추가

### [G1] AdaptiveMomentumWeights ALPHA 범위 교정

- **파일**: `literary_system/nie/adaptive_momentum_weights.py`
- **증상**: `ALPHA_MIN=0.30, ALPHA_MAX=0.80` — ADR-017 규격 [0.05, 0.95] 위반
- **수정**: `ALPHA_MIN=0.05`, `ALPHA_MAX=0.95`

### [G2] CharacterInfluenceMatrix PAGERANK_ITER 교정

- **파일**: `literary_system/nie/character_influence_matrix.py`
- **증상**: `PAGERANK_ITER=30` — ADR-018 규격 "≥50" 위반
- **수정**: `PAGERANK_ITER=50`

---

## 테스트 결과

| 구분 | V545 기준 | V545 HF |
|------|----------|---------|
| PASS | 5210 | 5210 |
| SKIP | 20 | 20 |
| FAIL | 0 | 0 |

**회귀 없음 확인.**
