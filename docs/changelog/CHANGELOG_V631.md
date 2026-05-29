# CHANGELOG V631 — Phase C SP-C.1: LOSConstitution v2.0 Bayesian Weight Optimiser (v11.1.0)

**날짜**: 2026-05-25
**버전**: v11.1.0
**이전**: V630 v11.0.0 / Phase B 완전 종료 + G61 7축

---

## 개요

V631은 Literary OS Phase C의 첫 번째 릴리즈이다.
SP-C.1 Self-Learning Loop의 기반을 마련하기 위해 LOSConstitution v2.0을 구현한다.
기존 v1.0의 고정 가중치(drse=0.30, debt=0.20, arc=0.20, tension=0.15, prose=0.15)를
Bayesian Optimisation(Optuna TPE Sampler)으로 자동 탐색하는 구조로 전환한다.

---

## 핵심 변경

### 신규 파일 — literary_system/constitution/los_constitution_v2.py (330+ lines)

- **LOSConstitutionV2**: LOSConstitution v1.0 완전 상속 + Bayesian Optimization 추가
  - `optimise_weights(samples, n_trials)`: Optuna TPE Sampler로 w1~w5 최적화
  - `entropy_ok` property: entropy(w) >= 1.5 분포 제약 (C-M-05, ADR-098)
  - `current_entropy` property: 현재 Shannon 엔트로피 값
  - `save(path)` / `load(path)`: JSON 영속화
  - `optimisation_history`: 누적 최적화 이력

- **OptimisationResult**: 최적화 결과 컨테이너
  - best_weights, best_mse, entropy, n_trials, n_pruned, converged
  - `to_dict()` 직렬화

- **entropy_constraint_pass(weights, threshold)**: 엔트로피 제약 검사 유틸
- **_shannon_entropy(weights)**: Shannon 엔트로피 계산 (bits)

### 수정 파일

- `literary_system/constitution/__init__.py`: LOSConstitutionV2, OptimisationResult, entropy_constraint_pass export 추가
- `literary_system/gates/release_gate.py`: version "V630" → "V631"
- `pyproject.toml`: optuna>=3.0 의존성 추가 (SP-C.1 Bayesian Opt)

### 신규 ADR

- `docs/adr/ADR-098.md`: LOSConstitution v2.0 Bayesian Weight Optimiser 설계 결정

### 신규 TC (+33)

- `tests/unit/test_v631_constitution_v2.py` (33 TC):
  - TC-01~10: TestLOSConstitutionV2Basic
  - TC-11~20: TestEntropyConstraint
  - TC-21~33: TestOptimisationResult + save/load

---

## 테스트 결과

| 구분 | 수 |
|------|-----|
| 신규 TC | +33 |
| 총 TC | 7,246 |
| FAIL | 0 |

---

## 절대 원칙 준수

- LLM-0: corpus/, constitution/, finetune/ 외부 LLM 호출 없음 ✅
- LLM-1: optuna 자체는 내부 최적화 라이브러리, 외부 LLM 호출 없음 ✅
- DEV_MODE: false 고정 ✅
