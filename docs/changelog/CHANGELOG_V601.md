# CHANGELOG V601 — SP-B.2 RLHF RewardModel v1.0

**버전**: v10.6.0  
**날짜**: 2026-05-22  
**커밋**: (후기입)  
**태그**: v10.6.0, v10.6.0-V601  

---

## 개요

SP-B.2(V601~V610) RLHF 루프의 첫 단계.
LOSConstitution 5축을 스칼라 보상 R(scene)으로 변환하는
**RewardModel v1.0**을 구현하고 `literary_system/rlhf/` 패키지를 신설.

---

## 신규 파일

### `literary_system/rlhf/__init__.py`
- RLHF 패키지 초기화
- RewardModel, RewardResult, ConstitutionAxisReward, AdversarialSeed 공개

### `literary_system/rlhf/reward_model.py`
- **RewardModel**: Constitution 5축 → 스칼라 R(scene) [0.0, 1.0]
- **마커 가중치 상한 0.20** (MARKER_WEIGHT_CAP, 보상 해킹 방지, B-V2-03)
- **적대적 시드 5종** 탐지기 내장:
  - `marker_stuffing` (패널티 0.15)
  - `length_inflation` (0.10)
  - `repetition_pattern` (0.12)
  - `extreme_emotion` (0.08)
  - `genre_deviation` (0.10)
- **`adv_seeds` 인터페이스**: `test_adversarial_seed()` + `run_adversarial_suite()`
- **`quality_correlation()` hook** (D23): Pearson r 누적 계산
- **LLM-0 원칙**: 외부 LLM API 호출 없음 (LOSConstitution 규칙 기반)
- LOSConstitution import 실패 시 규칙 기반 폴백 자동 적용
- `compute_batch()`, `summary()` 지원

### `docs/adr/ADR-061.md`
- RLHF 보상 모델 설계 결정 문서
- 마커 상한 0.20 / 적대적 시드 5종 / quality_correlation hook 근거

### `tests/unit/test_v601_reward_model.py`
- 8 TC (TC-A1~A3: 기본, TC-B1~B2: 가중치 상한, TC-C1~C3: 적대적+상관)

---

## 변경 파일

### `pyproject.toml`
- version: `10.5.0` → `10.6.0`
- description 업데이트 (V601 반영)

---

## 수치 목표

| 항목 | V600 기준선 | V601 목표 |
|------|------------|----------|
| Tests PASS | 6,382+ | 6,390+ |
| Gates | 53 | 53 (Gate G55는 V603) |
| 신규 TC | — | +8 |

---

## 다음 단계

- **V602**: RLHFDatasetBuilder — (씬, 보상) 쌍 JSONL + 8B/3B 듀얼 dataset
- **V603**: PPOTrainer + ConstraintGuard + Gate G55 (KL ≤0.08 cycle1)
