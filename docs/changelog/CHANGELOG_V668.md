# CHANGELOG V668

**Version**: 11.41.0  
**Date**: 2026-05-27  
**Branch**: dev/v668-sudowrite-absorption  
**Gate Status**: 68/68 PASS  

---

## 주요 변경사항

### 신규 파일

| 파일 | 설명 |
|------|------|
| `literary_system/absorption/sudowrite.py` | SudowriteAbsorber — IP-ADV-002 + 5개 FeatureGap (4흡수/1보류) |
| `tests/unit/test_v668_sudowrite_absorption.py` | 30 TC (TC01~TC30) — G72-2 단위 테스트 |
| `docs/adr/ADR-130.md` | Sudowrite 경쟁 흡수 아키텍처 결정 |
| `docs/changelog/CHANGELOG_V668.md` | 본 파일 |

### 수정 파일

| 파일 | 변경 내용 |
|------|----------|
| `literary_system/absorption/__init__.py` | SudowriteAbsorber export 추가 |
| `literary_system/gates/release_gate.py` | `_gate_sudowrite_absorption_g72_2()` + GATES.append (Gate 68) |
| `pyproject.toml` | `version = "11.41.0"` |
| `tools/test_inventory.json` | 재생성 (8,478 TCs) |

---

## 테스트 현황

- **단위 테스트**: 30 TC (TC01~TC30) — 전체 PASS
- **총 테스트 수**: 8,478
- **Release Gate**: 68/68 PASS

---

## SP-C.4 G72 진행 현황

| 서브게이트 | 경쟁사 | 버전 | 상태 |
|-----------|--------|------|------|
| G72-1 | NovelAI | V667 | ✅ PASS |
| G72-2 | Sudowrite | V668 | ✅ PASS |
| G72-3 | Novelcrafter | V669 | 예정 |
| G72-4 | NolanAI | V670 | 예정 |
| G72-5 + G72 | Jenova 통합 | V671 | 예정 |

---

## IP 자문 커밋

- **IP-ADV-002**: Sudowrite UI/UX 패턴 — 독자 구현으로 클리어 ✅
