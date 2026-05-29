# CHANGELOG V642

**버전**: v11.13.0  
**날짜**: 2026-05-26  
**단계**: SP-C.1 MetaLearner 2사이클 + DataAugmentationController 통합 검증

---

## 변경 요약

### 신규 기능

#### MetaLearnerCycle V642 (meta_learner_cycle.py)

- **`run_cycle()` `sample_texts` 파라미터 추가**
  - 제공 시 `DataAugmentationController.augment()` 실제 호출
  - `augment_ratio` 조정 후 즉시 반영
  
- **`CycleReport.augmentation_batch: Optional[AugmentationBatch]`**
  - 증강 배치 결과를 CycleReport에 포함
  - `augmentation_performed` 프로퍼티 추가

- **`AlphaStability` 데이터클래스**
  - `cycle_count`, `alpha_values`, `mean_alpha`, `variance`, `is_stable`
  - `summary` 프로퍼티: STABLE/UNSTABLE 상태 출력

- **`alpha_stability()` 메서드**
  - 다사이클 Krippendorff α 분산 추적
  - `statistics.pvariance()` 기반 모집단 분산
  - 2사이클 미만 → `None` 반환

- **`latest_augmentation_batch()` / `augmentation_batch_history()`**
  - 증강 배치 이력 조회 헬퍼

- **`run_n_cycles()` `sample_texts_list` 확장**
  - V645 통합 검증용 사이클별 증강 텍스트 지정

### 신규 상수
- `ALPHA_STABILITY_MAX_VAR = 0.01`
- `ALPHA_STABILITY_MIN_CYCLES = 2`
- `DEFAULT_AUGMENT_COUNT_PER_CYCLE = 3`
- `CYCLE_AUGMENT_DATASET_ID_PREFIX = "cycle-aug"`

---

## 테스트

| 파일 | TC | 결과 |
|------|----|------|
| test_v642_meta_learner_cycle2.py | 33 | 33/33 PASS ✅ |
| test_v641_meta_learner_cycle.py | 33 | 33/33 PASS ✅ (회귀 없음) |
| test_phase_a_exit.py | 20 | 20/20 PASS ✅ |

**전체 TC**: 7,643

---

## 문서

- ADR-102: MetaLearnerCycle V642 DataAugmentationController 실 통합 + α 안정성 측정

---

## 릴리즈

- **태그**: v11.13.0
- **이전 버전**: v11.12.0 (V641)
- **변경 파일**:
  - `literary_system/constitution/meta_learner_cycle.py` (V641→V642)
  - `tests/unit/test_v642_meta_learner_cycle2.py` (신규)
  - `docs/adr/ADR-102.md` (신규)
  - `docs/changelog/CHANGELOG_V642.md` (신규)
  - `pyproject.toml` (11.12.0 → 11.13.0)
  - `live_core_manifest.json` (v11.12.0 → v11.13.0)
  - `tools/test_inventory.json` (7610 → 7643)
