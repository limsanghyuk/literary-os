# CHANGELOG V636 — v11.6.0

## 릴리즈 정보
- **버전**: v11.6.0 | **Gates**: 61/61 PASS | **Tests**: 7,412
- **테마**: SelfLearningMonitor — SP-C.1 파이프라인 상태 모니터 (ADR-078)

## 핵심 변경

| 파일 | 내용 |
|------|------|
| `literary_system/constitution/self_learning_monitor.py` | SelfLearningMonitor + MonitorSnapshot + ComponentStatus (334줄) |
| `tests/unit/test_v636_self_learning_monitor.py` | TC-01~33, 33/33 PASS |
| `docs/adr/ADR-078.md` | 설계 결정 |
| `literary_system/constitution/__init__.py` | SelfLearningMonitor 등 공개 |
| `pyproject.toml` | 11.5.0 → 11.6.0 |
| `tools/test_inventory.json` | 7,412 TC |

## 이상 감지 4종
ROLLBACK_SURGE / F1_EXTREME_DROP / PATTERN_EMPTY / GATE_FAIL_STREAK
