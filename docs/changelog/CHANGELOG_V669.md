# CHANGELOG V669

**Version**: 11.42.0  
**Date**: 2026-05-27  
**Gate Status**: 69/69 PASS  

## 주요 변경사항

| 파일 | 설명 |
|------|------|
| `literary_system/absorption/novelcrafter.py` | NoveltcrafterAbsorber — IP-ADV-003, 5흡수/1보류 |
| `literary_system/absorption/__init__.py` | NoveltcrafterAbsorber export |
| `literary_system/gates/release_gate.py` | Gate G72-3 등록 (총 69 Gates) |
| `tests/unit/test_v669_novelcrafter_absorption.py` | 30 TC PASS |
| `docs/adr/ADR-131.md` | Novelcrafter 흡수 아키텍처 |
| `tools/test_inventory.json` | 8,508 TCs |

## SP-C.4 G72 진행 현황

| 서브게이트 | 경쟁사 | 상태 |
|-----------|--------|------|
| G72-1 | NovelAI | ✅ PASS (V667) |
| G72-2 | Sudowrite | ✅ PASS (V668) |
| G72-3 | Novelcrafter | ✅ PASS (V669) |
| G72-4 | NolanAI | 예정 (V670) |
| G72-5+G72 | Jenova | 예정 (V671) |
