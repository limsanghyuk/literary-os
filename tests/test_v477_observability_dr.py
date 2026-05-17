"""
tests/test_v477_observability_dr.py
V477 — ObservabilityStack + DRController 테스트
"""
import pytest
from literary_system.ops.observability_stack import (
    ObservabilityStack, Span, Metric, LoadTestReport,
)
from literary_system.ops.dr_controller import (
    DRController, Snapshot, RestoreReport, DRTestResult,
)


# ──────────────────────────────────────────────────────────────────────────────
# ObservabilityStack
# ──────────────────────────────────────────────────────────────────────────────
class TestObservabilityStack:
    def test_trace_creates_span(self):
        obs = ObservabilityStack()
        with obs.trace("my_span") as span:
            assert isinstance(span, Span)
        assert obs.span_count() == 1

    def test_span_name_recorded(self):
        obs = ObservabilityStack()
        with obs.trace("op_x"):
            pass
        spans = obs.recent_spans(1)
        assert spans[0].name == "op_x"

    def test_trace_nested(self):
        obs = ObservabilityStack()
        with obs.trace("outer"):
            with obs.trace("inner"):
                pass
        assert obs.span_count() == 2

    def test_record_metric_count(self):
        obs = ObservabilityStack()
        obs.record_metric("latency_ms", 120.0)
        assert obs.metric_count() == 1

    def test_record_multiple_metrics(self):
        obs = ObservabilityStack()
        obs.record_metric("req_count", 1.0)
        obs.record_metric("latency_ms", 50.0)
        assert obs.metric_count() == 2

    def test_export_prometheus_contains_metric_name(self):
        obs = ObservabilityStack()
        obs.record_metric("latency_ms", 200.0)
        prom = obs.export_prometheus()
        assert "latency_ms" in prom

    def test_export_prometheus_contains_value(self):
        obs = ObservabilityStack()
        obs.record_metric("latency_ms", 200.0)
        prom = obs.export_prometheus()
        assert "200" in prom

    def test_export_prometheus_multiple_metrics(self):
        obs = ObservabilityStack()
        obs.record_metric("req_count", 5.0)
        obs.record_metric("error_rate", 0.02)
        prom = obs.export_prometheus()
        assert "req_count" in prom
        assert "error_rate" in prom

    def test_load_test_returns_report(self):
        obs = ObservabilityStack()
        report = obs.run_load_test(vus=5, duration_s=1.0)
        assert isinstance(report, LoadTestReport)

    def test_load_test_p95_non_negative(self):
        obs = ObservabilityStack()
        report = obs.run_load_test(vus=10, duration_s=2.0)
        assert report.p95_ms >= 0

    def test_load_test_sla_pass_low_error_rate(self):
        obs = ObservabilityStack()
        report = obs.run_load_test(vus=5, duration_s=1.0,
                                   target_fn=lambda: 100.0, error_rate=0.0)
        assert report.sla_pass is True

    def test_recent_spans_limit(self):
        obs = ObservabilityStack()
        for i in range(5):
            with obs.trace(f"span_{i}"):
                pass
        assert len(obs.recent_spans(3)) == 3

    def test_span_has_duration(self):
        obs = ObservabilityStack()
        with obs.trace("timed") as span:
            pass
        s = obs.recent_spans(1)[0]
        assert s.duration_ms >= 0


# ──────────────────────────────────────────────────────────────────────────────
# DRController
# ──────────────────────────────────────────────────────────────────────────────
class TestDRController:
    def test_take_snapshot_returns_snapshot(self):
        dr = DRController(snapshot_fn=lambda: 64.0)
        snap = dr.take_snapshot()
        assert isinstance(snap, Snapshot)
        assert snap.size_mb == pytest.approx(64.0)

    def test_snapshot_id_format(self):
        dr = DRController()
        snap = dr.take_snapshot()
        assert snap.snapshot_id.startswith("snap_")

    def test_snapshot_count_increments(self):
        dr = DRController()
        dr.take_snapshot()
        dr.take_snapshot()
        assert dr.snapshot_count() == 2

    def test_latest_snapshot(self):
        t = [0.0]
        dr = DRController(clock_fn=lambda: t[0])
        t[0] = 100.0
        dr.take_snapshot()
        t[0] = 200.0
        s2 = dr.take_snapshot()
        assert dr.latest_snapshot().snapshot_id == s2.snapshot_id

    def test_dr_restore_test_pass(self):
        t = [0.0]
        dr = DRController(
            snapshot_fn=lambda: 32.0,
            restore_fn=lambda sid: 1800.0,
            clock_fn=lambda: t[0],
        )
        dr.take_snapshot()
        t[0] = 1800.0
        report = dr.dr_restore_test()
        assert report.rpo_ok is True
        assert report.rto_ok is True
        assert report.result == DRTestResult.PASS

    def test_dr_restore_test_fail_rpo(self):
        t = [0.0]
        dr = DRController(
            snapshot_fn=lambda: 32.0,
            restore_fn=lambda sid: 100.0,
            clock_fn=lambda: t[0],
        )
        dr.take_snapshot()
        t[0] = 7200.0  # 2h elapsed — RPO 초과
        report = dr.dr_restore_test()
        assert report.rpo_ok is False
        assert report.result == DRTestResult.FAIL

    def test_dr_restore_no_snapshot_raises(self):
        dr = DRController()
        with pytest.raises(RuntimeError):
            dr.dr_restore_test()

    def test_needs_snapshot_when_no_snap(self):
        dr = DRController()
        assert dr.needs_snapshot() is True

    def test_needs_snapshot_false_after_recent(self):
        t = [0.0]
        dr = DRController(clock_fn=lambda: t[0])
        dr.take_snapshot()
        t[0] = 100.0  # 100s < 3600s
        assert dr.needs_snapshot() is False

    def test_wal_append(self):
        dr = DRController()
        entry = dr.append_wal("insert", {"row_id": 1})
        assert entry.operation == "insert"
        assert dr.wal_entry_count() == 1

    def test_rto_actual_matches_restore_fn(self):
        t = [0.0]
        dr = DRController(
            snapshot_fn=lambda: 10.0,
            restore_fn=lambda sid: 3600.0,
            clock_fn=lambda: t[0],
        )
        dr.take_snapshot()
        t[0] = 500.0
        report = dr.dr_restore_test()
        assert report.rto_actual_s == pytest.approx(3600.0)

    def test_restore_report_restore_id_format(self):
        t = [0.0]
        dr = DRController(clock_fn=lambda: t[0])
        dr.take_snapshot()
        report = dr.dr_restore_test()
        assert report.restore_id.startswith("rst_")
