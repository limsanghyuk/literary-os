# CHANGELOG V671 — Jenova 경쟁 흡수 G72-5 + G72 통합 게이트

**버전**: v11.44.0
**날짜**: 2026-05-27
**서브페이즈**: SP-C.4 (경쟁 흡수)

---

## 변경 요약

### 신규 파일
- `literary_system/absorption/jenova.py` — JenovaAbsorber, IP_ADV_005 (6개 항목, cleared=True)
  - 6 FeatureGap: KoreanGenreBlending, EmotionalPeakScheduler, NarrativeCoherenceValidator,
    CharacterRelationshipMapper (흡수), PredictiveAudienceFeedback (거부), RealTimeCollab (연기)
- `tests/unit/test_v671_jenova_absorption.py` — 30 TC (TC01~TC30)
- `docs/adr/ADR-133.md` — Jenova 흡수 결정 기록
- `docs/changelog/CHANGELOG_V671.md` — 본 문서

### 수정 파일
- `literary_system/absorption/__init__.py` — JenovaAbsorber 익스포트 추가
- `literary_system/gates/release_gate.py` — G72-5 + G72 통합 게이트 추가 (72/72 PASS)
- `tools/test_inventory.json` — 8,568 TC (기존 8,538 → +30)
- `pyproject.toml` — version 11.43.0 → 11.44.0

---

## 릴리즈 지표

| 항목 | 값 |
|------|-----|
| Release Gate | 72/72 PASS |
| 총 TC | 8,568 |
| 신규 TC | 30 |
| 흡수 기능 | 4 |
| 거부/연기 | 2 |
| IP 자문 | IP-ADV-005 (cleared) |

---

## SP-C.4 완료 현황

| 게이트 | 경쟁사 | 상태 |
|--------|--------|------|
| G72-1 | NovelAI | ✅ PASS |
| G72-2 | Sudowrite | ✅ PASS |
| G72-3 | Novelcrafter | ✅ PASS |
| G72-4 | NolanAI | ✅ PASS |
| G72-5 | Jenova | ✅ PASS |
| **G72** | **통합** | **✅ ALL PASS** |
