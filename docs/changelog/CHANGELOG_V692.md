# Changelog — V692

**Version:** 12.1.0-dev (SP-D.1)
**Date:** 2026-05-28
**Branch:** dev/v692-observability-dashboard

## Added

- `literary_system/ops/observability_dashboard.py` (345 lines)
  - `ObsMetricPoint`, `AlertSeverity`, `AlertState`, `PanelType` 열거형
  - `ObsAlert` — `fire_when_below` 방향 지원 알림 규칙
  - `ObsDashboardPanel` — 시계열 기록 + 평균/최대/최소 통계
  - `ObservabilityDashboard` — 멀티패널 집계 + `health()` + `summary()`
  - `create_spd1_dashboard()` — SP-D.1 표준 5패널 팩토리
  - `record_otel_metrics()`, `record_gate_metrics()` 헬퍼
- `tests/unit/test_v692_observability_dashboard.py` — 33 TC ALL PASS
- `docs/adr/ADR-155.md`

## Changed

- (없음)

## Fixed

- (없음)

## Test Results

- V692 신규: 33 PASS
- 누적 총계: 9,172 TC (9,139 + 33)
