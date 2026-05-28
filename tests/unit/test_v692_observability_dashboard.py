"""
tests/unit/test_v692_observability_dashboard.py
────────────────────────────────────────────────
V692 SP-D.1 · ObservabilityDashboard 33 TC

TC-01~06  : ObsMetricPoint / ObsAlert 기본
TC-07~12  : ObsDashboardPanel 기록 + 통계
TC-13~18  : ObsAlert 평가 로직 (fire_when_above / fire_when_below)
TC-19~24  : ObservabilityDashboard 패널 관리
TC-25~30  : create_spd1_dashboard 5패널 표준
TC-31~33  : record_otel_metrics / record_gate_metrics / summary
"""

import pytest

from literary_system.ops.observability_dashboard import (
    AlertSeverity,
    AlertState,
    ObsAlert,
    ObsDashboardPanel,
    ObsMetricPoint,
    ObservabilityDashboard,
    PanelType,
    create_spd1_dashboard,
    record_gate_metrics,
    record_otel_metrics,
)


# ──────────────────────────────────────────────
# TC-01~06: 기본 데이터 타입
# ──────────────────────────────────────────────


def test_tc01_obs_metric_point_fields():
    pt = ObsMetricPoint(value=3.14)
    assert pt.value == pytest.approx(3.14)
    assert pt.timestamp > 0
    assert pt.labels == {}


def test_tc02_obs_metric_point_labels():
    pt = ObsMetricPoint(value=1.0, labels={"env": "prod"})
    assert pt.labels["env"] == "prod"


def test_tc03_alert_severity_enum():
    assert AlertSeverity.CRITICAL.value == "critical"
    assert AlertSeverity.WARNING.value == "warning"
    assert AlertSeverity.INFO.value == "info"


def test_tc04_alert_state_enum():
    assert AlertState.OK.value == "ok"
    assert AlertState.FIRING.value == "firing"
    assert AlertState.RESOLVED.value == "resolved"


def test_tc05_panel_type_enum():
    assert PanelType.GAUGE.value == "gauge"
    assert PanelType.COUNTER.value == "counter"
    assert PanelType.TIMESERIES.value == "timeseries"


def test_tc06_obs_alert_default_state():
    alert = ObsAlert(name="TestAlert", metric_name="cpu", threshold=80.0)
    assert alert.state == AlertState.OK
    assert not alert.is_firing
    assert alert.fired_at is None
    assert alert.fire_when_below is False


# ──────────────────────────────────────────────
# TC-07~12: ObsDashboardPanel
# ──────────────────────────────────────────────


def test_tc07_panel_basic_record():
    p = ObsDashboardPanel(name="cpu", panel_type=PanelType.GAUGE)
    p.record(55.0)
    assert p.count() == 1
    assert p.latest_value() == pytest.approx(55.0)


def test_tc08_panel_history():
    p = ObsDashboardPanel(name="mem")
    for v in [10, 20, 30, 40, 50]:
        p.record(float(v))
    hist = p.history(last_n=3)
    assert len(hist) == 3
    assert hist[-1].value == pytest.approx(50.0)


def test_tc09_panel_average():
    p = ObsDashboardPanel(name="lat")
    for v in [100, 200, 300]:
        p.record(float(v))
    assert p.average(last_n=3) == pytest.approx(200.0)


def test_tc10_panel_max_min():
    p = ObsDashboardPanel(name="err")
    for v in [1.0, 5.0, 3.0]:
        p.record(v)
    assert p.max_value() == pytest.approx(5.0)
    assert p.min_value() == pytest.approx(1.0)


def test_tc11_panel_empty_stats():
    p = ObsDashboardPanel(name="empty")
    assert p.latest() is None
    assert p.latest_value() is None
    assert p.average() == 0.0
    assert p.max_value() == 0.0
    assert p.min_value() == 0.0


def test_tc12_panel_max_history_eviction():
    p = ObsDashboardPanel(name="roll", max_history=5)
    for i in range(10):
        p.record(float(i))
    assert p.count() == 5
    assert p.latest_value() == pytest.approx(9.0)


# ──────────────────────────────────────────────
# TC-13~18: ObsAlert 평가 로직
# ──────────────────────────────────────────────


def test_tc13_alert_fires_when_above():
    alert = ObsAlert(name="CpuHigh", metric_name="cpu", threshold=80.0)
    result = alert.evaluate(85.0)
    assert result is True
    assert alert.is_firing
    assert alert.state == AlertState.FIRING


def test_tc14_alert_ok_below_threshold():
    alert = ObsAlert(name="CpuHigh", metric_name="cpu", threshold=80.0)
    result = alert.evaluate(70.0)
    assert result is False
    assert not alert.is_firing
    assert alert.state == AlertState.OK


def test_tc15_alert_fire_when_below():
    alert = ObsAlert(
        name="GateLow", metric_name="gate_ratio", threshold=0.95, fire_when_below=True
    )
    result = alert.evaluate(0.90)
    assert result is True
    assert alert.is_firing


def test_tc16_alert_fire_when_below_ok():
    alert = ObsAlert(
        name="GateLow", metric_name="gate_ratio", threshold=0.95, fire_when_below=True
    )
    result = alert.evaluate(0.99)
    assert result is False
    assert not alert.is_firing


def test_tc17_alert_transition_firing_to_resolved():
    alert = ObsAlert(name="Lat", metric_name="p99", threshold=500.0)
    alert.evaluate(600.0)
    assert alert.is_firing
    alert.evaluate(400.0)
    assert alert.state == AlertState.RESOLVED
    assert not alert.is_firing


def test_tc18_alert_fired_at_timestamp():
    import time
    alert = ObsAlert(name="Test", metric_name="x", threshold=10.0)
    before = time.time()
    alert.evaluate(15.0)
    after = time.time()
    assert alert.fired_at is not None
    assert before <= alert.fired_at <= after


# ──────────────────────────────────────────────
# TC-19~24: ObservabilityDashboard
# ──────────────────────────────────────────────


def test_tc19_dashboard_add_panel():
    dash = ObservabilityDashboard(service_name="test-svc")
    p = ObsDashboardPanel(name="cpu")
    dash.add_panel(p)
    assert "cpu" in dash.panel_names()
    assert dash.panel("cpu") is p


def test_tc20_dashboard_record_routes_to_panel():
    dash = ObservabilityDashboard()
    dash.add_panel(ObsDashboardPanel(name="mem"))
    ok = dash.record("mem", 256.0)
    assert ok is True
    assert dash.panel("mem").latest_value() == pytest.approx(256.0)


def test_tc21_dashboard_record_unknown_panel_false():
    dash = ObservabilityDashboard()
    ok = dash.record("nonexistent", 1.0)
    assert ok is False


def test_tc22_dashboard_firing_alerts_aggregated():
    dash = ObservabilityDashboard()
    p = ObsDashboardPanel(name="err")
    p.add_alert(ObsAlert(name="ErrHigh", metric_name="err", threshold=0.1))
    dash.add_panel(p)
    dash.record("err", 0.5)
    firing = dash.firing_alerts()
    assert len(firing) == 1
    assert firing[0].name == "ErrHigh"


def test_tc23_dashboard_health_degraded_on_critical():
    dash = ObservabilityDashboard()
    p = ObsDashboardPanel(name="gate")
    p.add_alert(ObsAlert(
        name="GateCrit", metric_name="gate", threshold=0.95,
        severity=AlertSeverity.CRITICAL, fire_when_below=True
    ))
    dash.add_panel(p)
    dash.record("gate", 0.80)
    assert dash.health() == "degraded"


def test_tc24_dashboard_health_warning():
    dash = ObservabilityDashboard()
    p = ObsDashboardPanel(name="lat")
    p.add_alert(ObsAlert(
        name="LatHigh", metric_name="lat", threshold=500,
        severity=AlertSeverity.WARNING
    ))
    dash.add_panel(p)
    dash.record("lat", 600.0)
    assert dash.health() == "warning"


# ──────────────────────────────────────────────
# TC-25~30: create_spd1_dashboard
# ──────────────────────────────────────────────


def test_tc25_spd1_dashboard_5_panels():
    dash = create_spd1_dashboard()
    assert len(dash.panel_names()) == 5
    for name in [
        "gates_pass_ratio",
        "spans_exported_total",
        "active_traces",
        "p99_span_duration_ms",
        "trace_error_ratio",
    ]:
        assert name in dash.panel_names(), f"Missing panel: {name}"


def test_tc26_spd1_gates_pass_ratio_alert_fires_below():
    dash = create_spd1_dashboard()
    dash.record("gates_pass_ratio", 0.80)  # < 0.95 -> CRITICAL
    firing = dash.firing_alerts()
    names = [a.name for a in firing]
    assert "GatesPassRatioCritical" in names


def test_tc27_spd1_gates_pass_ratio_ok_above():
    dash = create_spd1_dashboard()
    dash.record("gates_pass_ratio", 0.99)  # >= 0.95 -> OK
    firing = dash.firing_alerts()
    names = [a.name for a in firing]
    assert "GatesPassRatioCritical" not in names


def test_tc28_spd1_trace_error_ratio_fires():
    dash = create_spd1_dashboard()
    dash.record("trace_error_ratio", 0.10)  # >= 0.05 -> CRITICAL
    firing = dash.firing_alerts()
    names = [a.name for a in firing]
    assert "TraceErrorRatioCritical" in names


def test_tc29_spd1_active_traces_alert():
    dash = create_spd1_dashboard()
    dash.record("active_traces", 150.0)  # >= 100 -> WARNING
    firing = dash.firing_alerts()
    names = [a.name for a in firing]
    assert "ActiveTracesHigh" in names


def test_tc30_spd1_no_alerts_normal_operation():
    dash = create_spd1_dashboard()
    dash.record("gates_pass_ratio", 0.98)
    dash.record("spans_exported_total", 1000.0)
    dash.record("active_traces", 30.0)
    dash.record("p99_span_duration_ms", 150.0)
    dash.record("trace_error_ratio", 0.01)
    assert dash.health() == "healthy"
    assert len(dash.firing_alerts()) == 0


# ──────────────────────────────────────────────
# TC-31~33: 헬퍼 함수 + summary
# ──────────────────────────────────────────────


def test_tc31_record_otel_metrics_helper():
    dash = create_spd1_dashboard()
    results = record_otel_metrics(dash, spans_exported=500, active_traces=10, p99_ms=200.0, error_ratio=0.01)
    assert all(results), f"Some metrics failed: {results}"
    assert dash.panel("spans_exported_total").latest_value() == pytest.approx(500.0)
    assert dash.panel("active_traces").latest_value() == pytest.approx(10.0)
    assert dash.panel("p99_span_duration_ms").latest_value() == pytest.approx(200.0)
    assert dash.panel("trace_error_ratio").latest_value() == pytest.approx(0.01)


def test_tc32_record_gate_metrics_helper():
    dash = create_spd1_dashboard()
    ok = record_gate_metrics(dash, passed=84, total=84)
    assert ok is True
    val = dash.panel("gates_pass_ratio").latest_value()
    assert val == pytest.approx(1.0)


def test_tc33_summary_structure():
    dash = create_spd1_dashboard(service_name="my-svc")
    dash.record("gates_pass_ratio", 0.99)
    dash.record("trace_error_ratio", 0.01)
    s = dash.summary()
    assert s["service"] == "my-svc"
    assert s["version"] == "SP-D.1"
    assert s["panel_count"] == 5
    assert "panels" in s
    assert "firing_alerts" in s
    assert "alert_summary" in s
    assert s["health"] == "healthy"
    # alert_summary keys
    for key in ["info", "warning", "critical"]:
        assert key in s["alert_summary"]
