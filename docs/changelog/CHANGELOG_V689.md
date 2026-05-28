# CHANGELOG V689 — Prometheus /metrics OTel TraceContext 통합 (D-M-02 완성)

## Version: 12.x-dev (dev branch: dev/v689-prometheus-trace)
## Date: 2026-05-28
## Phase: D / SP-D.1 (V681~V695)

---

## 변경 요약

Prometheus /metrics 엔드포인트에 W3C TraceContext 전파를 통합하여 D-M-02를 완전히 이행한다.
span 관련 메트릭 4종을 추가하고, MetricsEndpoint가 traceparent를 inject/extract 한다.

---

## 신규 파일

### `literary_system/ops/prometheus_trace_extension.py` (368줄)
- `TraceMetricSnapshot(MetricSnapshot)` — spans_exported_total / active_traces / trace_errors_total / p99_span_duration_ms 추가
- `TraceAwareExporter(PrometheusExporter)` — render_trace() / collect_trace() / trace_metric_names()
- `MetricsEndpoint` — handle_request() traceparent extract → child span → inject 흐름
- `MetricsResponse` — status_code / body / response_headers / trace_context / duration_ms
- `create_metrics_endpoint()` — 팩토리 함수

### `tests/unit/test_v689_prometheus_trace.py` (33 TC, ALL PASS)
- TC-01~08: TraceMetricSnapshot 기본·유효성·비율 계산
- TC-09~14: TraceAwareExporter render_trace() 4종 메트릭 포함 여부
- TC-15~20: MetricsEndpoint 200 응답, traceparent 전파, Content-Type
- TC-21~26: 엣지 케이스 (빈 헤더, 잘못된 traceparent, 카운터, reset)
- TC-27~33: 통합 (왕복 검증, TYPE 라인 수, duration, factory)

### `docs/adr/ADR-152.md`
- D-M-02 Prometheus /metrics OTel 통합 결정 기록
- D-M-02 완성 선언 (V688+V689 합산)

---

## D-M-02 완성 체크리스트
- [x] W3C traceparent 파싱/생성 (V688)
- [x] tracestate 보존 (V688)
- [x] inject / extract API (V688)
- [x] child_context() span 계층 (V688)
- [x] OTel SDK Adapter (in-memory) (V688)
- [x] /metrics 엔드포인트 traceparent 전파 (V689)
- [x] span 관련 Prometheus 메트릭 4종 (V689)

---

## 테스트 결과
- 신규 TC: 33개
- 누적 TC: 8,911+ (V688 기준 8,878 + 33)
- Gates: 83/83 PASS (기존 유지)
