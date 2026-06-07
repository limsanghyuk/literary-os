# 공식 엔진 실데이터 1차 실행 결과 (2026-06-06)

데이터 보강계획 ③ 실증: 파일럿 L3(오징어게임 8씬)을 **실제 physics 공식 엔진**에 주입 실행.

## 실행 (mock 아님, 실제 모듈)
- `literary_system.physics.scene_feature_extractor.SceneFeature`
- `literary_system.physics.coefficient_store.PhysicsCoefficientStore`
- `literary_system.learning.physics_coefficient_updater.PhysicsCoefficientUpdater` (LR 0.01)

## 결과
| 계수 | 초기 | epoch5 | 파일럿 평균 신호 |
|---|---|---|---|
| conflict_weight | 0.200 | 0.232 | 0.85 |
| scene_energy_weight | 0.150 | 0.180 | 0.76 |
| motif_weight | 0.150 | 0.179 | 0.74 |
| curiosity_weight | 0.200 | 0.214 | 0.47 |

- 8씬 주입 → 계수가 신호 방향으로 gradient 갱신(weight_sum 1.11). **공식이 실 씬(L3) 데이터를 소비·학습함을 코드로 확인.**

## 무엇이 검증됐고, 무엇이 아닌가 (정직)
- ✅ 검증: 공식 엔진이 실 형태의 씬 데이터를 **소비해 계수를 학습하는 파이프라인이 동작**한다. (mock/합성 아닌 실제 모듈 + 파일럿 L3)
- ❌ 미검증: 공식 점수가 **인간이 느끼는 품질과 상관되는가**(공식의 타당성). N=8·1편·LLM 회상이라 통계적 의미 없음.
- 즉 '메커니즘 동작'은 입증, '공식 타당성'은 규모(실 씬 O(10^3))+정답(작가 선호/Gold)으로 별도 검증 필요(= G_VALUE_PROOF).

## 다음
1. DRSE 잔향 스코어러를 복선 검증셋에 주입(씬 beat를 proxy text로) → 복선 회수 점수.
2. 30~50편 회차 L2/L3 확대 → 계수 안정성 통계 검증.
3. 작가 선호 라벨과 공식 점수 상관 측정(타당성 검증).
