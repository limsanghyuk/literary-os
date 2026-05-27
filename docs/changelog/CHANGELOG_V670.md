# CHANGELOG V670

**Version**: 11.43.0  
**Date**: 2026-05-27  
**Gate Status**: 70/70 PASS  

## 주요 변경사항

| 파일 | 설명 |
|------|------|
| `absorption/nolan_ai.py` | NolanAIAbsorber — IP-ADV-004, 5흡수/1보류 |
| `absorption/__init__.py` | NolanAIAbsorber export |
| `gates/release_gate.py` | Gate G72-4 등록 (총 70 Gates) |
| `tests/unit/test_v670_nolan_ai_absorption.py` | 30 TC PASS |
| `docs/adr/ADR-132.md` | NolanAI 흡수 아키텍처 |
| `tools/test_inventory.json` | 8,538 TCs |

## SP-C.4 G72 진행 현황

| 서브게이트 | 경쟁사 | 상태 |
|-----------|--------|------|
| G72-1 | NovelAI | ✅ PASS (V667) |
| G72-2 | Sudowrite | ✅ PASS (V668) |
| G72-3 | Novelcrafter | ✅ PASS (V669) |
| G72-4 | NolanAI | ✅ PASS (V670) |
| G72-5+G72 | Jenova | 예정 (V671) |
