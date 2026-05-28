"""tests/gates/test_v690_observability_foundation_gate.py

V690: G83 Observability Foundation Gate 테스트 (33 TC).

TC-01~07: OB-1 trace_context.py API 검증
TC-08~13: OB-2 otel_adapter.py 검증
TC-14~18: OB-3 prometheus_exporter.py 검증
TC-19~24: OB-4 prometheus_trace_extension.py 검증
TC-25~29: OB-5 D-M-02 통합 검증
TC-30~33: run_g83_gate() 전체 게이트 실행 검증
"""

from __future__ import annotations

import pytest

from literary_system.gates.observability_foundation_gate import (
    ObsCheckpoint,
    run_g83_gate,
    _check_ob1_trace_context,
    _check_ob2_otel_adapter,
    _check_ob3_prometheus_exporter,
    _check_ob4_prometheus_trace_extension,
    _check_ob5_dm02_integration,
    GATE_ID,
    GATE_NAME,
)


# ─────────────────────────────────────────────────────────────────────────────
# TC-01~07: OB-1 trace_context.py
# ─────────────────────────────────────────────────────────────────────────────

class TestOB1TraceContext:

    def test_tc01_ob1_passes(self):
        """TC-01: OB-1 PASS."""
        cp = _check_ob1_trace_context()
        assert cp.passed, f"OB-1 실패: {cp.errors}"

    def test_tc02_ob1_axis_label(self):
        """TC-02: axis 레이블 OB-1."""
        cp = _check_ob1_trace_context()
        assert cp.axis == "OB-1"

    def test_tc03_ob1_no_errors(self):
        """TC-03: 에러 목록 비어있음."""
        cp = _check_ob1_trace_context()
        assert len(cp.errors) == 0

    def test_tc04_ob1_detail_nonempty(self):
        """TC-04: detail 문자열 비어있지 않음."""
        cp = _check_ob1_trace_context()
        assert len(cp.detail) > 0

    def test_tc05_trace_context_import(self):
        """TC-05: trace_context 모듈 직접 임포트."""
        from literary_system.ops.trace_context import TraceContext, new_trace_context
        ctx = new_trace_context()
        assert ctx.is_valid()

    def test_tc06_trace_id_length(self):
        """TC-06: trace_id 32자."""
        from literary_system.ops.trace_context import new_trace_context
        ctx = new_trace_context()
        assert len(ctx.trace_id) == 32

    def test_tc07_parent_id_length(self):
        """TC-07: parent_id 16자."""
        from literary_system.ops.trace_context import new_trace_context
        ctx = new_trace_context()
        assert len(ctx.parent_id) == 16


# ─────────────────────────────────────────────────────────────────────────────
# TC-08~13: OB-2 otel_adapter.py
# ─────────────────────────────────────────────────────────────────────────────

class TestOB2OtelAdapter:

    def test_tc08_ob2_passes(self):
        """TC-08: OB-2 PASS."""
        cp = _check_ob2_otel_adapter()
        assert cp.passed, f"OB-2 실패: {cp.errors}"

    def test_tc09_ob2_axis_label(self):
        """TC-09: axis 레이블 OB-2."""
        cp = _check_ob2_otel_adapter()
        assert cp.axis == "OB-2"

    def test_tc10_ob2_no_errors(self):
        """TC-10: 에러 없음."""
        cp = _check_ob2_otel_adapter()
        assert len(cp.errors) == 0

    def test_tc11_otel_adapter_span_export(self):
        """TC-11: OtelSdkAdapter span export 동작."""
        from literary_system.ops.otel_adapter import create_otel_adapter
        adapter = create_otel_adapter()
        with adapter.trace("test") as span:
            span.set_attribute("k", "v")
        assert len(adapter.exporter.spans) >= 1

    def test_tc12_span_data_duration(self):
        """TC-12: SpanData.duration_ms >= 0."""
        from literary_system.ops.otel_adapter import create_otel_adapter
        adapter = create_otel_adapter()
        with adapter.trace("dur_test"):
            pass
        assert adapter.exporter.spans[-1].duration_ms >= 0

    def test_tc13_ob2_detail_contains_span(self):
        """TC-13: detail에 'span' 포함."""
        cp = _check_ob2_otel_adapter()
        assert "span" in cp.detail.lower()


# ─────────────────────────────────────────────────────────────────────────────
# TC-14~18: OB-3 prometheus_exporter.py
# ─────────────────────────────────────────────────────────────────────────────

class TestOB3PrometheusExporter:

    def test_tc14_ob3_passes(self):
        """TC-14: OB-3 PASS."""
        cp = _check_ob3_prometheus_exporter()
        assert cp.passed, f"OB-3 실패: {cp.errors}"

    def test_tc15_ob3_axis_label(self):
        """TC-15: axis 레이블 OB-3."""
        cp = _check_ob3_prometheus_exporter()
        assert cp.axis == "OB-3"

    def test_tc16_ob3_no_errors(self):
        """TC-16: 에러 없음."""
        cp = _check_ob3_prometheus_exporter()
        assert len(cp.errors) == 0

    def test_tc17_prometheus_render_has_gates(self):
        """TC-17: render() 출력에 gates_total 포함."""
        from literary_system.ops.prometheus_exporter import PrometheusExporter, MetricSnapshot
        exp = PrometheusExporter()
        text = exp.render(MetricSnapshot(gates_total=83, gates_passed=83))
        assert "literary_os_gates_total" in text

    def test_tc18_ob3_detail_contains_lines(self):
        """TC-18: detail에 'lines' 포함."""
        cp = _check_ob3_prometheus_exporter()
        assert "lines" in cp.detail.lower()


# ─────────────────────────────────────────────────────────────────────────────
# TC-19~24: OB-4 prometheus_trace_extension.py
# ─────────────────────────────────────────────────────────────────────────────

class TestOB4PrometheusTraceExtension:

    def test_tc19_ob4_passes(self):
        """TC-19: OB-4 PASS."""
        cp = _check_ob4_prometheus_trace_extension()
        assert cp.passed, f"OB-4 실패: {cp.errors}"

    def test_tc20_ob4_axis_label(self):
        """TC-20: axis 레이블 OB-4."""
        cp = _check_ob4_prometheus_trace_extension()
        assert cp.axis == "OB-4"

    def test_tc21_ob4_no_errors(self):
        """TC-21: 에러 없음."""
        cp = _check_ob4_prometheus_trace_extension()
        assert len(cp.errors) == 0

    def test_tc22_trace_metric_snapshot_fields(self):
        """TC-22: TraceMetricSnapshot 4종 필드 존재."""
        from literary_system.ops.prometheus_trace_extension import TraceMetricSnapshot
        snap = TraceMetricSnapshot()
        assert hasattr(snap, "spans_exported_total")
        assert hasattr(snap, "active_traces")
        assert hasattr(snap, "trace_errors_total")
        assert hasattr(snap, "p99_span_duration_ms")

    def test_tc23_metrics_endpoint_traceparent(self):
        """TC-23: MetricsEndpoint 응답에 traceparent 포함."""
        from literary_system.ops.prometheus_trace_extension import create_metrics_endpoint, TraceMetricSnapshot
        ep = create_metrics_endpoint()
        resp = ep.handle_request(snapshot=TraceMetricSnapshot())
        assert "traceparent" in resp.response_headers

    def test_tc24_ob4_detail_contains_traceparent(self):
        """TC-24: detail에 'traceparent' 포함."""
        cp = _check_ob4_prometheus_trace_extension()
        assert "traceparent" in cp.detail.lower()


# ─────────────────────────────────────────────────────────────────────────────
# TC-25~29: OB-5 D-M-02 통합
# ─────────────────────────────────────────────────────────────────────────────

class TestOB5DM02Integration:

    def test_tc25_ob5_passes(self):
        """TC-25: OB-5 PASS."""
        cp = _check_ob5_dm02_integration()
        assert cp.passed, f"OB-5 실패: {cp.errors}"

    def test_tc26_ob5_axis_label(self):
        """TC-26: axis 레이블 OB-5."""
        cp = _check_ob5_dm02_integration()
        assert cp.axis == "OB-5"

    def test_tc27_ob5_no_errors(self):
        """TC-27: 에러 없음."""
        cp = _check_ob5_dm02_integration()
        assert len(cp.errors) == 0

    def test_tc28_dm02_trace_id_inheritance(self):
        """TC-28: D-M-02 — /metrics 응답에서 trace_id 상속."""
        from literary_system.ops.trace_context import new_trace_context, TraceContextPropagator, TraceContext
        from literary_system.ops.prometheus_trace_extension import create_metrics_endpoint, TraceMetricSnapshot

        root = new_trace_context()
        headers: dict = {}
        TraceContextPropagator.inject(root, headers)

        ep = create_metrics_endpoint()
        resp = ep.handle_request(request_headers=headers, snapshot=TraceMetricSnapshot())
        child = TraceContext.from_traceparent(resp.traceparent)
        assert child.trace_id == root.trace_id

    def test_tc29_ob5_detail_contains_dm02(self):
        """TC-29: detail에 'D-M-02' 포함."""
        cp = _check_ob5_dm02_integration()
        assert "D-M-02" in cp.detail


# ─────────────────────────────────────────────────────────────────────────────
# TC-30~33: run_g83_gate() 전체 게이트
# ─────────────────────────────────────────────────────────────────────────────

class TestRunG83Gate:

    def test_tc30_gate_passes(self):
        """TC-30: run_g83_gate() 전체 PASS."""
        result = run_g83_gate()
        assert result["pass"], f"G83 실패 체크포인트: {[c for c in result['checkpoints'] if not c['passed']]}"

    def test_tc31_gate_id(self):
        """TC-31: gate_id == 'G83'."""
        result = run_g83_gate()
        assert result["gate_id"] == "G83"

    def test_tc32_all_checkpoints_pass(self):
        """TC-32: 5/5 체크포인트 PASS."""
        result = run_g83_gate()
        assert result["passed_count"] == 5
        assert result["failed_count"] == 0
        assert result["total_count"] == 5

    def test_tc33_checkpoints_structure(self):
        """TC-33: 체크포인트 구조 검증 (axis, name, passed, detail, errors)."""
        result = run_g83_gate()
        axes = [c["axis"] for c in result["checkpoints"]]
        assert axes == ["OB-1", "OB-2", "OB-3", "OB-4", "OB-5"]
        for cp in result["checkpoints"]:
            assert "axis" in cp
            assert "name" in cp
            assert "passed" in cp
            assert isinstance(cp["errors"], list)
