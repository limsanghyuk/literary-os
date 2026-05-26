# MANIFEST V636 — v11.6.0

| 항목 | 값 |
|------|-----|
| Gates | 61/61 | Tests | 7,412 | ADR | ADR-078 |

## SelfLearningMonitor
- `capture(components, rollback_count, recent_drift, gate_fail_streak, pattern_count)` → MonitorSnapshot
- `detect_anomalies()` → List[str] (4종 이상 코드)
- `history()` / `last_snapshot()` / `unhealthy_snapshots()` / `count()` / `clear()`
