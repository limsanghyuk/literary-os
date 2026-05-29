# MANIFEST — V624 (v10.29.0)

**빌드**: 2026-05-25
**기반**: literary-os v10.28.0 (V623)

## 신규 컴포넌트

- `literary_system/testing/` — LongRunScenario + MemoryRegressionChecker
- `tests/unit/test_v624_long_run_scenario.py` — 30 TC

## 품질 지표

- Gates: 60/60 PASS
- Tests: 6,930 TC
- LongRunScenario: 24 epoch, 임계값 50MB/epoch
- MemoryRegression: 10 run, 기울기 < 5 MB/run
