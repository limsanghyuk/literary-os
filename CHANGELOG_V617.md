# Changelog — V617 (v10.22.0)

**Date**: 2026-05-23  
**Version**: v10.22.0  
**SP**: SP-B.4 통합 최적화 + Exit  

---

## 신규 모듈

### `literary_system/optimization/long_run_monitor.py` (308줄)
- **LongRunConfig** — 에포크 기반 장기 실행 설정 dataclass
- **EpochResult** — 단일 에포크 실행 결과 (StressResult + LeakReport + duration_s + all_pass)
- **LongRunReport** — 전체 실행 보고서 (epochs, p95_trend, leak_delta_trend, peak_memory_mb)
- **LongRunMonitor** — 메인 모니터 클래스 (run, run_epoch, quick_monitor, summary)

## 테스트

- `tests/test_v617_long_run_monitor.py` — 25 TC, ALL PASS
  - TestLongRunConfig (4) / TestEpochResult (5) / TestLongRunReport (5)
  - TestLongRunMonitorRun (7) / TestLongRunEdgeCases (4)

## ADR

- ADR-077: LongRunMonitor v1.0 — 에포크 기반 장기 실행 내구성 모니터

## 수치

| 항목 | 이전 (V616) | 이후 (V617) |
|------|------------|------------|
| 버전 | v10.21.0 | v10.22.0 |
| 테스트 | 6,628 PASS | 6,653 PASS |
| Gates | 59/59 | 59/59 |
| ADR | ADR-076 | ADR-077 |

## 수정 사항

- `MonitorConfig` → `LongRunConfig` 클래스명 변경 (G37 DuplicateZero 충돌 방지)
- `tools/test_inventory.json` 재생성 (6,653 tests, EA-6 PASS)

## SP-B.4 진행률

V614 PerformanceOptimizer ✅ → V615 Gate G60 ✅ → V616 MemoryLeakDetector+StressTester ✅ → **V617 LongRunMonitor ✅** → V618~V630 (다음)
