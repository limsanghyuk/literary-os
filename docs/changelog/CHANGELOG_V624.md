# CHANGELOG — V624 (v10.29.0)

**날짜**: 2026-05-25
**베이스**: V623 (v10.28.0, commit d32b799c)
**커밋 대상**: main

## 요약

24h 장기 시나리오 + 메모리 회귀 검증 인프라 신설 (본안 v3.0 V624 항목).

## 신규 파일 (5종)

| 파일 | 설명 |
|------|------|
| `literary_system/testing/__init__.py` | testing 패키지 초기화 |
| `literary_system/testing/long_run_scenario.py` | LongRunScenario (24 epoch 압축) |
| `literary_system/testing/memory_regression.py` | MemoryRegressionChecker (회귀 감지) |
| `tests/unit/test_v624_long_run_scenario.py` | 30 TC 테스트 스위트 |
| `docs/adr/ADR-091.md` | 설계 결정 문서 |

## 변경 파일 (3종)

| 파일 | 변경 내용 |
|------|-----------|
| `pyproject.toml` | 10.28.0 → 10.29.0 |
| `literary_system/gates/release_gate.py` | version "V624" |
| `tools/test_inventory.json` | 6,900 → 6,930 TC |

## 지표

| 항목 | V623 | V624 |
|------|------|------|
| 버전 | 10.28.0 | 10.29.0 |
| Tests | 6,900 | 6,930 |
| Gates | 60/60 | 60/60 |
| 신규 모듈 | — | literary_system/testing/ |

## 설계 결정 (ADR-091)

- 24 epoch 압축 실행 (epoch = 1h 압축)
- 메모리 증가 허용: 50 MB/epoch (경고 20 MB)
- 회귀 기울기 허용: 5 MB/run (경고 2 MB)
- LLM-0 원칙 준수: 외부 LLM 호출 없음
