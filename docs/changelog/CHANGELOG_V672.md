# CHANGELOG V672 — DistillationExportPipeline (SP-C.4)

**버전**: v11.45.0
**날짜**: 2026-05-27

## 변경 요약

### 신규 파일
- `literary_system/absorption/distillation.py` — DistillationExportPipeline, 22개 DistilledFeature
- `tests/unit/test_v672_distillation_export.py` — 30 TC
- `docs/adr/ADR-134.md`
- `docs/changelog/CHANGELOG_V672.md`

### 수정 파일
- `literary_system/absorption/__init__.py` — DistillationExportPipeline 익스포트
- `literary_system/gates/release_gate.py` — G72-D 게이트 추가 (73/73 PASS)
- `tools/test_inventory.json` — 8,598 TC (+30)
- `pyproject.toml` — v11.45.0

## 릴리즈 지표
| 항목 | 값 |
|------|-----|
| Release Gate | 73/73 PASS |
| 총 TC | 8,598 |
| DistilledFeature | 22종 |
| IMMEDIATE | 14 |
| NEXT | 8 |
