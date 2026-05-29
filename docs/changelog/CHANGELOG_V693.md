# Changelog — V693

**Version:** 12.1.0-dev (SP-D.1)
**Date:** 2026-05-28

## Added

- `tests/integration/test_v693_spd1_observability_integration.py` — 33 TC ALL PASS
  - TC-01~06: TraceContext + OtelSdkAdapter 연동
  - TC-07~12: TraceSampler 파이프라인
  - TC-13~18: PrometheusTraceExtension E2E
  - TC-19~24: ObservabilityDashboard + OTel 통합
  - TC-25~30: AdaptiveSampler + Dashboard 피드백
  - TC-31~33: 전체 스택 E2E
- `docs/adr/ADR-156.md` — 통합 테스트 스위트 결정 기록

## Test Results

- V693 신규: 33 PASS
- 누적 총계: 9,205 TC (9,172 + 33)
