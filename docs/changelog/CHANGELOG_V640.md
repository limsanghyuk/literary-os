# CHANGELOG V640 — literary-os v11.10.0

**릴리즈**: 2026-05-26
**테마**: SP-C.1 — FeedbackIntegrator (인간 피드백 통합기, ADR-082)
**이전 버전**: V639 (v11.9.0, ADR-081, DataAugmentationController)

---

## 신규 파일

### literary_system/constitution/feedback_integrator.py (375줄)
- **FeedbackRecord**: dataclass — record_id(UUID4), scene_id, feedback_type, evaluator_id, original_score, corrected_score, label_before, label_after, annotation, note
  - `correction_delta()` → corrected - original
- **IntegrationResult**: dataclass — result_id(UUID4), feedback_count, avg_correction_delta, rejection_rate, label_revision_rate, signal_strength, has_signal
  - `summary()` → 1줄 요약
- **FeedbackIntegrator**: LOSDB JSONL append-only 영속화
  - `record_feedback(...)` → FeedbackRecord
  - `batch_record(items)` → List[FeedbackRecord]
  - `integrate(scene_ids)` → IntegrationResult
  - `feedbacks()` / `feedbacks_by_scene()` / `feedbacks_by_type()` / `feedbacks_by_evaluator()`
  - `integration_history()` / `last_result()` / `count()` / `clear()`
- **상수**: MIN_FEEDBACK_FOR_SIGNAL=3, CORRECTION_WEIGHT=0.8, REJECTION_PENALTY=0.5

## 수정/신규 파일
- `literary_system/constitution/feedback_integrator.py` (신규)
- `literary_system/constitution/__init__.py` (FeedbackIntegrator API 공개)
- `docs/adr/ADR-082.md` (신규)
- `docs/changelog/CHANGELOG_V640.md` (본 파일)
- `manifests/MANIFEST_V640.md` (신규)
- `pyproject.toml` — 11.9.0 → 11.10.0
- `tools/test_inventory.json` — 7,544 TC

## 신규 TC (+33)
- TC-01~33 / 33/33 PASS

## DEV_PROTOCOL_v2.0 준수
- Preflight 12단계 전 단계 적용
- FeedbackIntegrator/FeedbackRecord/IntegrationResult 중복 없음 확인
- LLM-0 위반 0건
- 핵심 클래스 10/10 생존 ✅
