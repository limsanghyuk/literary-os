# CHANGELOG V634 — v11.4.0

## 릴리즈 정보
- **버전**: v11.4.0
- **Phase**: C SP-C.1 (Self-Learning Loop)
- **테마**: RetrainingScheduler — F1 Drift 기반 재학습 스케줄러 (ADR-076)
- **날짜**: 2026-05-26

## 핵심 변경

### 신규 파일
| 파일 | 설명 |
|------|------|
| `literary_system/constitution/retraining_scheduler.py` | RetrainingScheduler + ScheduleRecord (276줄) |
| `tests/unit/test_v634_retraining_scheduler.py` | TC-01~34, 34/34 PASS |
| `docs/adr/ADR-076.md` | F1 drift 스케줄러 설계 결정 |
| `docs/changelog/CHANGELOG_V634.md` | 본 파일 |
| `manifests/MANIFEST_V634.md` | V634 산출물 매니페스트 |

### 수정 파일
| 파일 | 변경 내용 |
|------|----------|
| `literary_system/constitution/__init__.py` | RetrainingScheduler, ScheduleRecord, DRIFT_THRESHOLD, MIN_INTERVAL_DAYS 공개 |
| `pyproject.toml` | 11.3.0 → 11.4.0 |
| `tools/test_inventory.json` | 7,312 → 7,346 TC |

## 테스트 현황
- **전체 TC**: 7,346 (단위 1,149 PASS)
- **신규 TC**: 34 (TC-01~34)
- **Gates**: 60/60 PASS

## ADR
- ADR-076: DRIFT_THRESHOLD=0.03, MIN_INTERVAL_DAYS=7, JSONL append-only

## LLM-0 준수
외부 LLM 호출 없음. DEV_MODE=false.
