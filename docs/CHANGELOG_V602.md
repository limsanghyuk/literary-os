# CHANGELOG V602 — RLHFDatasetBuilder v1.0

**버전**: v10.7.0  
**날짜**: 2026-05-22  
**태그**: v10.7.0, v10.7.0-V602  

---

## 개요

SP-B.2(V601~V610) RLHF 루프 2단계.
RewardModel(V601)의 출력을 활용해 **(씬, 보상) 쌍 JSONL** 데이터셋을 생성하는
**RLHFDatasetBuilder v1.0** 구현. 8B/3B 듀얼 dataset 지원.

---

## 신규 파일

### `literary_system/rlhf/rlhf_dataset_builder.py`
- **RLHFDatasetBuilder**: 씬 목록 → JSONL 데이터셋 빌더
- **DatasetEntry**: (씬, 보상) 쌍 단위 (entry_id, scene, reward, passed, axis_rewards, model_target, split)
- **DatasetStats**: 총계·pass_count·mean/min/max reward·train/val/test 분포
- **BuildResult**: build() 반환값 (output_path, stats, entry_count, model_target, threshold)
- **`build()`**: 씬 → JSONL 저장 (filter_passed 옵션)
- **`build_dual()`**: 8B/3B 두 파일 동시 생성
- **`load()`**: JSONL → DatasetEntry 목록 재로드
- **`summary()`**: 저장 파일 요약 통계
- **결정론적 분할**: floor(N × ratio) 기반 80/10/10 train/val/test
- **LLM-0 원칙**: 외부 LLM API 호출 없음

### `docs/adr/ADR-062.md`
- RLHFDatasetBuilder 설계 결정 문서
- JSONL 포맷 / filter_passed / 듀얼 dataset / 결정론적 split 근거

### `tests/unit/test_v602_dataset_builder.py`
- 9 TC (TC-A1~A3: 기본, TC-B1~B2: 유효성, TC-C1~C3: 듀얼+로드+분할, TC-추가: summary)

---

## 변경 파일

### `literary_system/rlhf/__init__.py`
- V602 공개 API 추가: RLHFDatasetBuilder, DatasetEntry, DatasetStats, BuildResult

### `pyproject.toml`
- version: `10.6.0` → `10.7.0`

---

## 수치 목표

| 항목 | V601 기준선 | V602 목표 |
|------|------------|----------|
| Tests PASS | 6,285+ | 6,294+ |
| Gates | 53 | 53 (Gate G55는 V603) |
| 신규 TC | — | +9 |

---

## 다음 단계

- **V603**: PPOTrainer + ConstraintGuard + Gate G55 (KL ≤ 0.08 cycle1, ADR-062)
