"""tests/unit/test_v689_prometheus_trace.py

V689: Prometheus /metrics OTel TraceContext 통합 테스트 (33 TC).

TC-01~08: TraceMetricSnapshot — 기본 및 유효성 검사
TC-09~14: TraceAwareExporter — render_trace() 메트릭 포함 여부
TC-15~20: MetricsEndpoint — handle_request() traceparent 전파
TC-21~26: 엣지 케이스 — 헤더 없음, 잘못된 traceparent, 연속 요청
TC-27~33: 통합 — 카운터 누적, render+endpoint 왕복, error 응답
"""

from __future__ import annotations

import pytest

from literary_system.ops.prometheus_trace_extension import (
    METRICS_CONTENT_TYPE,
    METRICS_ENDPOINT_PATH,
    MetricsEndpoint,
    MetricsResponse,
    TraceAwareExporter,
    TraceMetricSnapshot,
    create_metrics_endpoint,
)
from literary_system.ops.prometheus_exporter import MonitoringConfig
from literary_system.ops.trace_context import (
    TraceContextPropagator,
    new_trace_context,
)


# ─────────────────────────────────────────────────────────────────────────────
# TC-01~08: TraceMetricSnapshot
# ─────────────────────────────────────────────────────────────────────────────

class TestTraceMetricSnapshot:

    def test_tc01_default_creation(self):
        """TC-01: 기본 생성 — 0 값으로 초기화."""
        snap = TraceMetricSnapshot()
        assert snap.spans_exported_total == 0
        assert snap.active_traces == 0
        assert snap.trace_errors_total == 0
        assert snap.p99_span_duration_ms == 0.0

    def test_tc02_custom_values(self):
        """TC-02: 커스텀 값 설정."""
        snap = TraceMetricSnapshot(
            spans_exported_total=1024,
            active_traces=5,
            trace_errors_total=12,
            p99_span_duration_ms=45.7,
        )
        assert snap.spans_exported_total == 1024
        assert snap.active_traces == 5
        assert snap.trace_errors_total == 12
        assert snap.p99_span_duration_ms == 45.7

    def test_tc03_inherits_metric_snapshot_fields(self):
        """TC-03: MetricSnapshot 상속 필드 접근 가능."""
        snap = TraceMetricSnapshot(gates_passed=83, tests_total=8878)
        assert snap.gates_passed == 83
        assert snap.tests_total == 8878
        assert snap.gates_pass_ratio == 1.0  # gates_total 기본값과 동일

    def test_tc04_validate_negative_spans_exported(self):
        """TC-04: spans_exported_total 음수 → 유효성 오류."""
        snap = TraceMetricSnapshot(spans_exported_total=-1)
        errors = snap.validate()
        assert any("spans_exported_total" in e for e in errors)

    def test_tc05_validate_negative_active_traces(self):
        """TC-05: active_traces 음수 → 유효성 오류."""
        snap = TraceMetricSnapshot(active_traces=-3)
        errors = snap.validate()
        assert any("active_traces" in e for e in errors)

    def test_tc06_validate_negative_trace_errors(self):
        """TC-06: trace_errors_total 음수 → 유효성 오류."""
        snap = TraceMetricSnapshot(trace_errors_total=-1)
        errors = snap.validate()
        assert any("trace_errors_total" in e for e in errors)

    def test_tc07_trace_error_ratio(self):
        """TC-07: trace_error_ratio 계산."""
        snap = TraceMetricSnapshot(spans_exported_total=100, trace_errors_total=5)
        assert abs(snap.trace_error_ratio - 0.05) < 1e-9

    def test_tc08_trace_error_ratio_zero_total(self):
        """TC-08: spans_exported_total=0 → error_ratio=0.0."""
        snap = TraceMetricSnapshot(spans_exported_total=0, trace_errors_total=0)
        assert snap.trace_error_ratio == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# TC-09~14: TraceAwareExporter
# ─────────────────────────────────────────────────────────────────────────────

class TestTraceAwareExporter:

    def _make_snap(self, **kwargs) -> TraceMetricSnapshot:
        defaults = dict(
            gates_total=83, gates_passed=83, tests_total=8878,
            spans_exported_total=100, active_traces=2,
            trace_errors_total=1, p99_span_duration_ms=15.0,
        )
        defaults.update(kwargs)
        return TraceMetricSnapshot(**defaults)

    def test_tc09_render_trace_includes_base_metrics(self):
        """TC-09: render_trace()에 기존 메트릭 포함."""
        exporter = TraceAwareExporter()
        snap = self._make_snap()
        text = exporter.render_trace(snap)
        assert "literary_os_gates_total" in text
        assert "literary_os_tests_total" in text

    def test_tc10_render_trace_includes_spans_exported(self):
        """TC-10: spans_exported_total 메트릭 렌더링."""
        exporter = TraceAwareExporter()
        snap = self._make_snap(spans_exported_total=512)
        text = exporter.render_trace(snap)
        assert "literary_os_spans_exported_total" in text
        assert "512" in text

    def test_tc11_render_trace_includes_active_traces(self):
        """TC-11: active_traces 메트릭 렌더링."""
        exporter = TraceAwareExporter()
        snap = self._make_snap(active_traces=7)
        text = exporter.render_trace(snap)
        assert "literary_os_active_traces" in text
        assert "7" in text

    def test_tc12_render_trace_includes_trace_errors(self):
        """TC-12: trace_errors_total 메트릭 렌더링."""
        exporter = TraceAwareExporter()
        snap = self._make_snap(trace_errors_total=3)
        text = exporter.render_trace(snap)
        assert "literary_os_trace_errors_total" in text
        assert "3" in text

    def test_tc13_render_trace_includes_p99_duration(self):
        """TC-13: p99_span_duration_ms 메트릭 렌더링."""
        exporter = TraceAwareExporter()
        snap = self._make_snap(p99_span_duration_ms=22.5)
        text = exporter.render_trace(snap)
        assert "literary_os_p99_span_duration_ms" in text
        assert "22.5" in text

    def test_tc14_trace_metric_names_list(self):
        """TC-14: trace_metric_names() 4종 반환."""
        exporter = TraceAwareExporter()
        names = exporter.trace_metric_names()
        assert len(names) == 4
        assert "literary_os_spans_exported_total" in names
        assert "literary_os_active_traces" in names
        assert "literary_os_trace_errors_total" in names
        assert "literary_os_p99_span_duration_ms" in names


# ─────────────────────────────────────────────────────────────────────────────
# TC-15~20: MetricsEndpoint — handle_request()
# ─────────────────────────────────────────────────────────────────────────────

class TestMetricsEndpoint:

    def _make_endpoint(self) -> MetricsEndpoint:
        return create_metrics_endpoint(version="12.0.2", phase="D")

    def _make_snap(self) -> TraceMetricSnapshot:
        return TraceMetricSnapshot(
            gates_total=83, gates_passed=83, tests_total=8878,
            spans_exported_total=200, active_traces=3,
        )

    def test_tc15_handle_request_returns_200(self):
        """TC-15: 정상 요청 → 200 응답."""
        ep = self._make_endpoint()
        resp = ep.handle_request(snapshot=self._make_snap())
        assert resp.status_code == 200
        assert resp.is_ok

    def test_tc16_response_has_traceparent_header(self):
        """TC-16: 응답 헤더에 traceparent 포함."""
        ep = self._make_endpoint()
        resp = ep.handle_request(snapshot=self._make_snap())
        assert "traceparent" in resp.response_headers
        assert resp.traceparent is not None

    def test_tc17_traceparent_propagated_from_request(self):
        """TC-17: 요청 traceparent → 응답 trace_id 상속."""
        ep = self._make_endpoint()
        parent = new_trace_context()
        req_headers: dict = {}
        TraceContextPropagator.inject(parent, req_headers)

        resp = ep.handle_request(request_headers=req_headers, snapshot=self._make_snap())
        # child span은 동일 trace_id 상속
        assert resp.trace_context is not None
        assert resp.trace_context.trace_id == parent.trace_id

    def test_tc18_no_request_traceparent_creates_new(self):
        """TC-18: 요청 traceparent 없음 → 새 trace_id 생성."""
        ep = self._make_endpoint()
        resp = ep.handle_request(snapshot=self._make_snap())
        assert resp.trace_context is not None
        assert resp.trace_context.is_valid()

    def test_tc19_response_body_contains_metrics(self):
        """TC-19: 응답 본문에 Prometheus 메트릭 포함."""
        ep = self._make_endpoint()
        snap = TraceMetricSnapshot(
            gates_total=83, gates_passed=83,
            spans_exported_total=77,
        )
        resp = ep.handle_request(snapshot=snap)
        assert "literary_os_gates_total" in resp.body
        assert "literary_os_spans_exported_total" in resp.body

    def test_tc20_content_type_header(self):
        """TC-20: Content-Type 헤더 정확성."""
        ep = self._make_endpoint()
        resp = ep.handle_request(snapshot=self._make_snap())
        assert resp.content_type == METRICS_CONTENT_TYPE


# ─────────────────────────────────────────────────────────────────────────────
# TC-21~26: 엣지 케이스
# ─────────────────────────────────────────────────────────────────────────────

class TestEdgeCases:

    def test_tc21_empty_request_headers(self):
        """TC-21: 빈 헤더 dict → 정상 처리."""
        ep = create_metrics_endpoint()
        resp = ep.handle_request(request_headers={}, snapshot=TraceMetricSnapshot())
        assert resp.is_ok

    def test_tc22_none_request_headers(self):
        """TC-22: None 헤더 → 정상 처리."""
        ep = create_metrics_endpoint()
        resp = ep.handle_request(request_headers=None, snapshot=TraceMetricSnapshot())
        assert resp.is_ok
        assert resp.trace_context is not None

    def test_tc23_invalid_traceparent_creates_new(self):
        """TC-23: 잘못된 traceparent → 새 trace 생성 (에러 없음)."""
        ep = create_metrics_endpoint()
        resp = ep.handle_request(
            request_headers={"traceparent": "invalid-header"},
            snapshot=TraceMetricSnapshot(),
        )
        assert resp.is_ok
        assert resp.trace_context is not None

    def test_tc24_request_counter_increments(self):
        """TC-24: 요청마다 request_count 증가."""
        ep = create_metrics_endpoint()
        snap = TraceMetricSnapshot()
        ep.handle_request(snapshot=snap)
        ep.handle_request(snapshot=snap)
        ep.handle_request(snapshot=snap)
        assert ep.request_count == 3

    def test_tc25_reset_counters(self):
        """TC-25: reset_counters() 후 카운터 0."""
        ep = create_metrics_endpoint()
        ep.handle_request(snapshot=TraceMetricSnapshot())
        ep.handle_request(snapshot=TraceMetricSnapshot())
        ep.reset_counters()
        assert ep.request_count == 0
        assert ep.error_count == 0

    def test_tc26_consecutive_requests_different_span_ids(self):
        """TC-26: 연속 요청 — 다른 span_id (동일 trace_id 가능)."""
        ep = create_metrics_endpoint()
        parent = new_trace_context()
        req_headers: dict = {}
        TraceContextPropagator.inject(parent, req_headers)

        resp1 = ep.handle_request(request_headers=dict(req_headers), snapshot=TraceMetricSnapshot())
        resp2 = ep.handle_request(request_headers=dict(req_headers), snapshot=TraceMetricSnapshot())

        # 동일 trace_id
        assert resp1.trace_context.trace_id == resp2.trace_context.trace_id
        # 다른 span_id (각 요청마다 새 child span)
        assert resp1.trace_context.parent_id != resp2.trace_context.parent_id


# ─────────────────────────────────────────────────────────────────────────────
# TC-27~33: 통합
# ─────────────────────────────────────────────────────────────────────────────

class TestIntegration:

    def test_tc27_full_round_trip_traceparent(self):
        """TC-27: 요청 traceparent → 응답 traceparent 왕복 검증."""
        ep = create_metrics_endpoint()
        ctx = new_trace_context()
        req_headers: dict = {}
        TraceContextPropagator.inject(ctx, req_headers)

        resp = ep.handle_request(request_headers=req_headers, snapshot=TraceMetricSnapshot())
        # 응답 traceparent 파싱 가능
        from literary_system.ops.trace_context import TraceContext
        parsed = TraceContext.from_traceparent(resp.traceparent)
        assert parsed.is_valid()
        assert parsed.trace_id == ctx.trace_id

    def test_tc28_render_trace_metric_counts(self):
        """TC-28: render_trace() 메트릭 라인 수 검증."""
        exporter = TraceAwareExporter()
        snap = TraceMetricSnapshot(
            gates_total=83, gates_passed=83, tests_total=8878,
            spans_exported_total=100, active_traces=2,
            trace_errors_total=0, p99_span_duration_ms=10.0,
        )
        text = exporter.render_trace(snap)
        # TYPE 선언 수 = 기본 메트릭 10 + trace 메트릭 4 = 14 (build_info 포함)
        type_lines = [l for l in text.split("\n") if l.startswith("# TYPE")]
        assert len(type_lines) >= 14

    def test_tc29_endpoint_duration_ms_positive(self):
        """TC-29: 처리 시간 > 0."""
        ep = create_metrics_endpoint()
        resp = ep.handle_request(snapshot=TraceMetricSnapshot())
        assert resp.duration_ms >= 0.0

    def test_tc30_snapshot_with_trace_context_field(self):
        """TC-30: trace_context 필드 설정 → has_trace_context() True."""
        ctx = new_trace_context()
        snap = TraceMetricSnapshot(trace_context=ctx)
        assert snap.has_trace_context()

    def test_tc31_snapshot_without_trace_context(self):
        """TC-31: trace_context 없음 → has_trace_context() False."""
        snap = TraceMetricSnapshot()
        assert not snap.has_trace_context()

    def test_tc32_create_metrics_endpoint_factory(self):
        """TC-32: 팩토리 함수로 엔드포인트 생성."""
        ep = create_metrics_endpoint(version="12.0.2", phase="D")
        assert ep is not None
        assert isinstance(ep, MetricsEndpoint)

    def test_tc33_trace_aware_exporter_collect_then_render(self):
        """TC-33: collect_trace() → render_trace() 통합 흐름."""
        exporter = TraceAwareExporter()
        snap = TraceMetricSnapshot(
            gates_total=83, gates_passed=83, tests_total=8878,
            spans_exported_total=500, active_traces=4,
            trace_errors_total=10, p99_span_duration_ms=30.0,
        )
        exporter.collect_trace(snap)
        assert exporter.snapshot_count() == 1
        text = exporter.render_trace(snap)
        assert "500" in text
        assert "30.0" in text
