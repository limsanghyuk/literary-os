# CHANGELOG V639 — literary-os v11.9.0

**릴리즈**: 2026-05-26
**테마**: SP-C.1 — DataAugmentationController (훈련 데이터 증강 컨트롤러, ADR-081)
**이전 버전**: V638 (v11.8.0, ADR-080, ContaminationDetector)

---

## 신규 파일

### literary_system/constitution/data_augmentation_controller.py (395줄)
- **AugmentedSample**: dataclass — sample_id, original_text, augmented_text, strategy, augment_ratio
- **AugmentationBatch**: dataclass — batch_id(UUID4), created_at, dataset_id, original_count, augmented_count, samples, strategies_used, controller_id, note
  - `summary()` → 1줄 요약 문자열
- **DataAugmentationController**: LOSDB JSONL append-only 영속화
  - `augment(dataset_id, texts, strategies, augment_count, ...)` → AugmentationBatch
  - `augment_single(text, strategy, augment_ratio)` → AugmentedSample
  - `history()` / `last_batch()` / `total_augmented()` / `batches_by_dataset()` / `count()` / `clear()`
  - 메모리 모드(`:memory:`) + 파일 모드(JSONL append)
- **증강 전략 5종**: SYNONYM_SWAP / BACK_TRANSLATE / RANDOM_DELETION / SENTENCE_SHUFFLE / TOKEN_INSERT
- **상수**: DEFAULT_AUGMENT_RATIO=0.15, DEFAULT_AUGMENT_COUNT=3, MAX_AUGMENT_COUNT=10
- **LLM-0 원칙 완전 준수**

## 수정/신규 파일
- `literary_system/constitution/data_augmentation_controller.py` (신규)
- `literary_system/constitution/__init__.py` (DataAugmentationController API 공개)
- `docs/adr/ADR-081.md` (신규)
- `docs/changelog/CHANGELOG_V639.md` (본 파일)
- `manifests/MANIFEST_V639.md` (신규)
- `pyproject.toml` — 11.8.0 → 11.9.0
- `tools/test_inventory.json` — 7,511 TC

## 신규 TC (+33)
- `tests/unit/test_v639_data_augmentation_controller.py` — TC-01~33, 33/33 PASS

## DEV_PROTOCOL_v2.0 준수
- Preflight 12단계 정식 적용
- DataAugmentationController 중복 없음 확인
- LLM-0 위반 0건
- 핵심 클래스 생존 매트릭스 10/10 ✅

## 버전 범프
- `pyproject.toml`: 11.8.0 → **11.9.0**
