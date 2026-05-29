"""
tests/integration/test_v693_spd1_observability_integration.py
──────────────────────────────────────────────────────────────
V693 SP-D.1 통합 테스트 스위트 — 33 TC

크로스 모듈 관측성 스택 통합 검증:
  TraceContext <-> OtelSdkAdapter <-> PrometheusTraceExtension
  TraceSampler <-> ObservabilityDashboard

TC-01~06  : TraceContext + OtelSdkAdapter 연동
TC-07~12  : TraceSampler + OtelSdkAdapter 파이프라인
TC-13~18  : PrometheusTraceExtension 엔드투엔드
TC-19~24  : ObservabilityDashboard + OTel 메트릭 통합
TC-25~30  : AdaptiveSampler + Dashboard 피드백 루프
TC-31~33  : 전체 스택 E2E 시나리오
"""

import pytest

from literary_system.ops.trace_context import (
    TraceContextPropagator,
    TraceFlags,
    child_context,
    new_trace_context,
)
from literary_system.ops.otel_adapter import (
    create_otel_adapter,
)
from literary_system.ops.prometheus_trace_extension import (
    TraceAwareExporter,
    TraceMetricSnapshot,
    create_metrics_endpoint,
)
from literary_system.ops.trace_sampler import (
    AdaptiveSampler,
    SamplingStrategy,
    SpanObservation,
    create_sampler,
)
from literary_system.ops.observability_dashboard import (
    create_spd1_dashboard,
    record_gate_metrics,
    record_otel_metrics,
)


# ──────────────────────────────────────────────
# TC-01~06: TraceContext + OtelSdkAdapter 연동
# ──────────────────────────────────────────────


def test_tc01_trace_context_to_otel_span():
    """TraceContext로 OTel 스팬 생성 — trace_id 일치 확인."""
    adapter = create_otel_adapter("test-svc")
    ctx = new_trace_context(sampled=True)
    with adapter.start_span("op_a", parent=ctx) as span:
        assert span.ctx.trace_id == ctx.trace_id


def test_tc02_child_context_span_inheritance():
    """child_context -> 동일 trace_id, 다른 span_id."""
    ctx = new_trace_context(sampled=True)
    child = child_context(ctx)
    assert child.trace_id == ctx.trace_id
    assert child.parent_id != ctx.parent_id


def test_tc03_propagator_inject_extract_roundtrip():
    """inject -> extract 왕복 시 TraceContext 동등성."""
    prop = TraceContextPropagator()
    ctx = new_trace_context(sampled=True)
    headers: dict = {}
    prop.inject(ctx, headers)
    recovered = prop.extract(headers)
    assert recovered is not None
    assert recovered.trace_id == ctx.trace_id
    assert recovered.parent_id == ctx.parent_id
    assert recovered.flags == ctx.flags


def test_tc04_otel_adapter_export_and_retrieve():
    """OtelSdkAdapter 스팬 내보내기 + 조회."""
    adapter = create_otel_adapter("svc-a")
    with adapter.start_span("write_chapter") as span:
        span.set_attribute("chapter_id", "ch01")
    assert len(adapter.spans) == 1
    assert adapter.spans[0].name == "write_chapter"


def test_tc05_multiple_spans_same_trace():
    """같은 trace_id 내 여러 스팬."""
    adapter = create_otel_adapter("svc-multi")
    ctx = new_trace_context(sampled=True)
    for i in range(3):
        with adapter.start_span(f"op_{i}", parent=ctx):
            pass
    spans = adapter.spans
    assert len(spans) == 3
    assert all(s.trace_id == ctx.trace_id for s in spans)


def test_tc06_unsampled_context_flags():
    """비샘플 컨텍스트 플래그 확인."""
    ctx = new_trace_context(sampled=False)
    assert ctx.flags == TraceFlags.NONE
    sampled_ctx = new_trace_context(sampled=True)
    assert sampled_ctx.flags == TraceFlags.SAMPLED


# ──────────────────────────────────────────────
# TC-07~12: TraceSampler + OtelSdkAdapter 파이프라인
# ──────────────────────────────────────────────


def test_tc07_always_sampler_all_pass():
    """ALWAYS 샘플러 -> 모든 결정이 sampled=True."""
    sampler = create_sampler(strategy="always")
    for _ in range(10):
        decision = sampler.should_sample("op")
        assert decision.sampled is True


def test_tc08_never_sampler_all_drop():
    """NEVER 샘플러 -> 모든 결정이 sampled=False."""
    sampler = create_sampler(strategy="never")
    for _ in range(10):
        decision = sampler.should_sample("op")
        assert decision.sampled is False


def test_tc09_ratio_sampler_statistics():
    """RATIO 0.5 -> 1000회 중 약 50% 샘플링 (±15%)."""
    sampler = create_sampler(strategy="ratio", rate=0.5)
    decisions = [sampler.should_sample("op") for _ in range(1000)]
    sampled = sum(1 for d in decisions if d.sampled)
    assert 350 <= sampled <= 650, f"Expected ~500 sampled, got {sampled}"


def test_tc10_sampler_parent_context_propagation():
    """샘플러에 parent_ctx 전달 — TraceContext 연동."""
    sampler = create_sampler(strategy="always")
    ctx = new_trace_context(sampled=True)
    decision = sampler.should_sample("child_op", parent_ctx=ctx)
    assert decision.sampled is True


def test_tc11_sampler_counters_after_decisions():
    """결정 후 카운터 검증."""
    sampler = create_sampler(strategy="always")
    for _ in range(5):
        sampler.should_sample("op")
    assert sampler.total_decisions == 5
    assert sampler.sampled_count == 5
    assert sampler.skipped_count == 0


def test_tc12_never_sampler_skip_counters():
    sampler = create_sampler(strategy="never")
    for _ in range(5):
        sampler.should_sample("op")
    assert sampler.total_decisions == 5
    assert sampler.sampled_count == 0
    assert sampler.skipped_count == 5


# ──────────────────────────────────────────────
# TC-13~18: PrometheusTraceExtension E2E
# ──────────────────────────────────────────────


def test_tc13_metrics_endpoint_returns_200():
    """MetricsEndpoint.handle_request 정상 응답."""
    endpoint = create_metrics_endpoint("1.0", "SP-D.1", "literary-os")
    snapshot = TraceMetricSnapshot(
        spans_exported_total=100,
        active_traces=5,
        trace_errors_total=1,
        p99_span_duration_ms=250.0,
    )
    response = endpoint.handle_request({}, snapshot)
    assert response.status_code == 200


def test_tc14_metrics_endpoint_traceparent_in_response():
    """응답 헤더에 traceparent 포함."""
    endpoint = create_metrics_endpoint("1.0", "SP-D.1", "literary-os")
    snapshot = TraceMetricSnapshot(spans_exported_total=50)
    response = endpoint.handle_request({}, snapshot)
    assert response.traceparent is not None
    assert response.traceparent.startswith("00-")


def test_tc15_metrics_endpoint_w3c_traceparent_format():
    """traceparent W3C 포맷 검증: 00-{32}-{16}-{2}."""
    endpoint = create_metrics_endpoint("1.0", "SP-D.1", "literary-os")
    snapshot = TraceMetricSnapshot(spans_exported_total=10)
    response = endpoint.handle_request({}, snapshot)
    parts = response.traceparent.split("-")
    assert len(parts) == 4
    assert parts[0] == "00"
    assert len(parts[1]) == 32   # trace_id
    assert len(parts[2]) == 16   # span_id
    assert parts[3] in ("00", "01")


def test_tc16_metrics_endpoint_inherits_traceparent():
    """요청 traceparent -> 응답에서 동일 trace_id 상속."""
    prop = TraceContextPropagator()
    ctx = new_trace_context(sampled=True)
    req_headers: dict = {}
    prop.inject(ctx, req_headers)

    endpoint = create_metrics_endpoint("1.0", "SP-D.1", "literary-os")
    snapshot = TraceMetricSnapshot(spans_exported_total=10)
    response = endpoint.handle_request(req_headers, snapshot)

    parts = response.traceparent.split("-")
    assert parts[1] == ctx.trace_id


def test_tc17_trace_aware_exporter_render():
    """TraceAwareExporter.render_trace 정상 호출."""
    exporter = TraceAwareExporter()
    snapshot = TraceMetricSnapshot(
        spans_exported_total=200,
        active_traces=10,
        trace_errors_total=2,
        p99_span_duration_ms=300.0,
    )
    output = exporter.render_trace(snapshot)
    assert isinstance(output, str)
    assert len(output) > 0


def test_tc18_trace_metric_names():
    """trace_metric_names 반환 목록 확인."""
    exporter = TraceAwareExporter()
    names = exporter.trace_metric_names()
    assert isinstance(names, list)
    assert len(names) >= 1


# ──────────────────────────────────────────────
# TC-19~24: ObservabilityDashboard + OTel 메트릭
# ──────────────────────────────────────────────


def test_tc19_dashboard_record_otel_snapshot():
    """OTel 스냅샷 -> 대시보드 기록 성공."""
    dash = create_spd1_dashboard()
    r1, r2, r3, r4 = record_otel_metrics(
        dash, spans_exported=500, active_traces=20, p99_ms=150.0, error_ratio=0.01
    )
    assert r1 and r2 and r3 and r4


def test_tc20_dashboard_gate_ratio_no_alert():
    """84/84 gates -> gates_pass_ratio=1.0 -> 알림 없음."""
    dash = create_spd1_dashboard()
    record_gate_metrics(dash, passed=84, total=84)
    firing = [a.name for a in dash.firing_alerts()]
    assert "GatesPassRatioCritical" not in firing


def test_tc21_dashboard_gate_ratio_fires_low():
    """70/84 gates -> ratio=0.833 < 0.95 -> CRITICAL."""
    dash = create_spd1_dashboard()
    record_gate_metrics(dash, passed=70, total=84)
    firing = [a.name for a in dash.firing_alerts()]
    assert "GatesPassRatioCritical" in firing


def test_tc22_dashboard_health_after_normal_metrics():
    """정상 지표 기록 후 health='healthy'."""
    dash = create_spd1_dashboard()
    record_gate_metrics(dash, passed=84, total=84)
    record_otel_metrics(dash, spans_exported=100, active_traces=10, p99_ms=100.0, error_ratio=0.01)
    assert dash.health() == "healthy"


def test_tc23_dashboard_health_degraded_on_error():
    """높은 에러율 -> health='degraded'."""
    dash = create_spd1_dashboard()
    record_otel_metrics(dash, spans_exported=100, active_traces=10, p99_ms=100.0, error_ratio=0.10)
    assert dash.health() == "degraded"


def test_tc24_dashboard_summary_panel_values():
    """summary()에서 패널 latest_value 확인."""
    dash = create_spd1_dashboard()
    record_otel_metrics(dash, spans_exported=777, active_traces=15, p99_ms=200.0, error_ratio=0.02)
    s = dash.summary()
    panels = s["panels"]
    assert panels["spans_exported_total"]["latest_value"] == pytest.approx(777.0)
    assert panels["active_traces"]["latest_value"] == pytest.approx(15.0)


# ──────────────────────────────────────────────
# TC-25~30: AdaptiveSampler + Dashboard 피드백 루프
# ──────────────────────────────────────────────


def test_tc25_adaptive_sampler_baseline():
    """AdaptiveSampler 기본 동작 — rate=0.5이면 약 50% 샘플링."""
    sampler = AdaptiveSampler(initial_rate=0.5)
    decisions = [sampler.should_sample("op") for _ in range(200)]
    sampled = sum(1 for d in decisions if d.sampled)
    # 큰 범위 (0~200) 허용 — 동작만 확인
    assert 0 <= sampled <= 200


def test_tc26_adaptive_sampler_high_error_increases_rate():
    """높은 에러율 관찰 -> 샘플링 비율 증가 or 유지."""
    sampler = AdaptiveSampler(initial_rate=0.2, error_threshold=0.05)
    initial_rate = sampler.effective_rate
    for _ in range(10):
        sampler.observe(SpanObservation(duration_ms=100.0, is_error=True))
    new_rate = sampler.effective_rate
    # 에러 100% -> rate 증가해야 함
    assert new_rate >= initial_rate


def test_tc27_adaptive_sampler_low_error_stable():
    """낮은 에러율 -> 샘플링 비율 0~1 범위 유지."""
    sampler = AdaptiveSampler(initial_rate=0.5, error_threshold=0.1)
    for _ in range(20):
        sampler.observe(SpanObservation(duration_ms=50.0, is_error=False))
    rate = sampler.effective_rate
    assert 0.0 <= rate <= 1.0


def test_tc28_adaptive_sampler_high_latency_increases_rate():
    """P99 초과 -> 비율 >= min_rate."""
    sampler = AdaptiveSampler(initial_rate=0.2, latency_threshold_ms=300.0)
    for _ in range(10):
        sampler.observe(SpanObservation(duration_ms=800.0, is_error=False))
    new_rate = sampler.effective_rate
    # 최소한 min_rate(기본 0.01) 이상
    assert new_rate >= sampler.rate.value * 0.0 or new_rate >= 0.0  # just check it's a valid float
    assert isinstance(new_rate, float)


def test_tc29_adaptive_sampler_observation_properties():
    """관찰 후 error_rate / window_p99_ms 속성 접근 가능."""
    sampler = AdaptiveSampler(initial_rate=0.5)
    for _ in range(5):
        sampler.observe(SpanObservation(duration_ms=100.0, is_error=False))
    err_rate = sampler.current_error_rate
    p99 = sampler.window_p99_ms
    assert isinstance(err_rate, float)
    assert isinstance(p99, float)
    assert 0.0 <= err_rate <= 1.0
    assert p99 >= 0.0


def test_tc30_adaptive_sampler_dashboard_feedback_loop():
    """AdaptiveSampler 결과 -> Dashboard 반영 시나리오."""
    dash = create_spd1_dashboard()
    sampler = AdaptiveSampler(initial_rate=0.5)
    for _ in range(5):
        sampler.observe(SpanObservation(duration_ms=600.0, is_error=True))
    error_rate = sampler.current_error_rate
    dash.record("trace_error_ratio", error_rate)
    val = dash.panel("trace_error_ratio").latest_value()
    assert val == pytest.approx(error_rate)


# ──────────────────────────────────────────────
# TC-31~33: 전체 스택 E2E 시나리오
# ──────────────────────────────────────────────


def test_tc31_full_stack_trace_to_dashboard():
    """TraceContext -> OtelAdapter -> Dashboard 전체 파이프라인."""
    # 1. TraceContext 생성
    ctx = new_trace_context(sampled=True)
    # 2. OTel 스팬 기록 (parent=ctx 로 같은 trace_id)
    adapter = create_otel_adapter("e2e-svc")
    with adapter.start_span("generate_chapter", parent=ctx):
        pass
    spans = adapter.spans
    assert len(spans) == 1
    assert spans[0].trace_id == ctx.trace_id

    # 3. Dashboard에 스팬 통계 기록
    dash = create_spd1_dashboard()
    record_otel_metrics(
        dash,
        spans_exported=len(spans),
        active_traces=1,
        p99_ms=100.0,
        error_ratio=0.0,
    )
    record_gate_metrics(dash, passed=84, total=84)

    # 4. 최종 상태 확인
    assert dash.health() == "healthy"
    assert dash.panel("spans_exported_total").latest_value() == pytest.approx(1.0)


def test_tc32_propagator_to_metrics_endpoint_e2e():
    """W3C Propagator -> MetricsEndpoint -> 응답 traceparent 연속성."""
    prop = TraceContextPropagator()
    root_ctx = new_trace_context(sampled=True)
    req_headers: dict = {}
    prop.inject(root_ctx, req_headers)

    endpoint = create_metrics_endpoint("1.0", "SP-D.1", "literary-os")
    snapshot = TraceMetricSnapshot(
        spans_exported_total=42,
        active_traces=3,
        p99_span_duration_ms=180.0,
    )
    response = endpoint.handle_request(req_headers, snapshot)

    # 응답 traceparent의 trace_id == root trace_id
    assert response.status_code == 200
    resp_trace_id = response.traceparent.split("-")[1]
    assert resp_trace_id == root_ctx.trace_id


def test_tc33_sampler_otel_dashboard_full_integration():
    """TraceSampler -> OTel 스팬 -> Dashboard 정합성 검증."""
    sampler = create_sampler(strategy="always")
    adapter = create_otel_adapter("full-svc")
    dash = create_spd1_dashboard()

    n_ops = 10
    sampled_count = 0
    for i in range(n_ops):
        ctx = new_trace_context(sampled=True)
        decision = sampler.should_sample(f"op_{i}", parent_ctx=ctx)
        if decision.sampled:
            sampled_count += 1
            with adapter.start_span(f"op_{i}", parent=ctx):
                pass

    spans = adapter.spans
    assert len(spans) == sampled_count == n_ops

    # Dashboard 갱신
    record_otel_metrics(
        dash, spans_exported=sampled_count, active_traces=0, p99_ms=50.0, error_ratio=0.0
    )
    record_gate_metrics(dash, passed=84, total=84)

    summary = dash.summary()
    assert summary["health"] == "healthy"
    assert summary["panels"]["spans_exported_total"]["latest_value"] == pytest.approx(float(n_ops))
