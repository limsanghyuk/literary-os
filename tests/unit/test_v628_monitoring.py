"""tests/unit/test_v628_monitoring.py

V628 Prometheus Exporter + Grafana Dashboard 테스트 (30 TC)
- TC-01~10: TestPrometheusExporterBasic
- TC-11~20: TestMetricSnapshot
- TC-21~30: TestGrafanaDashboardSpec

설계 원칙:
  LLM-0: PrometheusExporter 내부에 외부 LLM 호출 없음 (순수 메트릭 포매팅)
  G32: print() 없음 — logger 사용
  G37: PrometheusExporter, MetricSnapshot, MonitoringConfig — 유일 클래스명
"""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from literary_system.ops.prometheus_exporter import (
    METRIC_PREFIX,
    PrometheusExporter,
    MetricSnapshot,
    MonitoringConfig,
)


# ─────────────────────────────────────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def _default_snapshot() -> MetricSnapshot:
    return MetricSnapshot(
        gates_total=60,
        gates_passed=60,
        tests_total=7060,
        cost_slo_used_usd=45.0,
        cost_slo_hard_usd=120.0,
        serve_latency_ms=120.0,
        train_jobs_active=0,
        lora_promoted_count=3,
    )


def _default_exporter() -> PrometheusExporter:
    config = MonitoringConfig(version="10.32.0", phase="B")
    return PrometheusExporter(config)


GRAFANA_JSON_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "deploy", "monitoring", "grafana_dashboard.json"
)


# ─────────────────────────────────────────────────────────────────────────────
# TC-01~10: TestPrometheusExporterBasic
# ─────────────────────────────────────────────────────────────────────────────
class TestPrometheusExporterBasic(unittest.TestCase):
    """PrometheusExporter 기본 동작 10건."""

    def test_tc01_version_attribute(self):
        """TC-01: VERSION 속성 존재."""
        self.assertTrue(hasattr(PrometheusExporter, "VERSION"))
        self.assertIsInstance(PrometheusExporter.VERSION, str)

    def test_tc02_default_config(self):
        """TC-02: 설정 없이 생성 가능 — 기본 MonitoringConfig 적용."""
        exp = PrometheusExporter()
        self.assertIsNotNone(exp.config)
        self.assertEqual(exp.config.metric_prefix, METRIC_PREFIX)

    def test_tc03_collect_snapshot(self):
        """TC-03: collect() 호출 시 snapshot_count 증가."""
        exp = _default_exporter()
        snap = _default_snapshot()
        self.assertEqual(exp.snapshot_count(), 0)
        exp.collect(snap)
        self.assertEqual(exp.snapshot_count(), 1)

    def test_tc04_render_returns_string(self):
        """TC-04: render() → str 반환."""
        exp = _default_exporter()
        exp.collect(_default_snapshot())
        result = exp.render()
        self.assertIsInstance(result, str)

    def test_tc05_render_contains_metric_prefix(self):
        """TC-05: 출력에 literary_os_ 프리픽스 포함."""
        exp = _default_exporter()
        exp.collect(_default_snapshot())
        text = exp.render()
        self.assertIn("literary_os_", text)

    def test_tc06_render_contains_gates_passed(self):
        """TC-06: gates_passed 메트릭 포함."""
        exp = _default_exporter()
        exp.collect(_default_snapshot())
        text = exp.render()
        self.assertIn("literary_os_gates_passed", text)

    def test_tc07_render_contains_build_info(self):
        """TC-07: build_info 메트릭 포함."""
        exp = _default_exporter()
        exp.collect(_default_snapshot())
        text = exp.render()
        self.assertIn("literary_os_build_info", text)
        self.assertIn('version="10.32.0"', text)

    def test_tc08_render_without_collect_raises(self):
        """TC-08: 스냅샷 없이 render() → RuntimeError."""
        exp = _default_exporter()
        with self.assertRaises(RuntimeError):
            exp.render()

    def test_tc09_reset_clears_buffer(self):
        """TC-09: reset() 후 snapshot_count == 0."""
        exp = _default_exporter()
        exp.collect(_default_snapshot())
        exp.reset()
        self.assertEqual(exp.snapshot_count(), 0)

    def test_tc10_metric_names_list(self):
        """TC-10: metric_names() — literary_os_ 프리픽스 포함 목록."""
        exp = _default_exporter()
        names = exp.metric_names()
        self.assertIsInstance(names, list)
        self.assertTrue(all(n.startswith("literary_os_") for n in names))
        self.assertTrue(len(names) >= 9)


# ─────────────────────────────────────────────────────────────────────────────
# TC-11~20: TestMetricSnapshot
# ─────────────────────────────────────────────────────────────────────────────
class TestMetricSnapshot(unittest.TestCase):
    """MetricSnapshot 동작 10건."""

    def test_tc11_default_snapshot_valid(self):
        """TC-11: 기본 MetricSnapshot 생성 → validate() 에러 없음."""
        snap = _default_snapshot()
        self.assertEqual(snap.validate(), [])

    def test_tc12_gates_pass_ratio_full(self):
        """TC-12: 60/60 → pass_ratio=1.0."""
        snap = MetricSnapshot(gates_total=60, gates_passed=60)
        self.assertEqual(snap.gates_pass_ratio, 1.0)

    def test_tc13_gates_pass_ratio_partial(self):
        """TC-13: 45/60 → pass_ratio=0.75."""
        snap = MetricSnapshot(gates_total=60, gates_passed=45)
        self.assertAlmostEqual(snap.gates_pass_ratio, 0.75)

    def test_tc14_gates_pass_ratio_zero_total(self):
        """TC-14: gates_total=0 → pass_ratio=0.0 (ZeroDivision 방지)."""
        snap = MetricSnapshot(gates_total=0, gates_passed=0)
        self.assertEqual(snap.gates_pass_ratio, 0.0)

    def test_tc15_is_healthy_true(self):
        """TC-15: 정상 스냅샷 → is_healthy()=True."""
        snap = _default_snapshot()
        self.assertTrue(snap.is_healthy())

    def test_tc16_is_healthy_false_low_pass_ratio(self):
        """TC-16: 낮은 pass_ratio → is_healthy()=False."""
        snap = MetricSnapshot(gates_total=60, gates_passed=50)  # 83.3% < 95%
        self.assertFalse(snap.is_healthy())

    def test_tc17_validate_gates_passed_exceeds_total(self):
        """TC-17: gates_passed > gates_total → 에러."""
        snap = MetricSnapshot(gates_total=60, gates_passed=61)
        errors = snap.validate()
        self.assertTrue(len(errors) > 0)

    def test_tc18_validate_negative_tests_total(self):
        """TC-18: tests_total < 0 → 에러."""
        snap = MetricSnapshot(tests_total=-1)
        errors = snap.validate()
        self.assertTrue(len(errors) > 0)

    def test_tc19_validate_negative_cost(self):
        """TC-19: cost_slo_used_usd < 0 → 에러."""
        snap = MetricSnapshot(cost_slo_used_usd=-5.0)
        errors = snap.validate()
        self.assertTrue(len(errors) > 0)

    def test_tc20_cost_slo_utilization(self):
        """TC-20: used=60, hard=120 → utilization=0.5."""
        snap = MetricSnapshot(cost_slo_used_usd=60.0, cost_slo_hard_usd=120.0)
        self.assertAlmostEqual(snap.cost_slo_utilization, 0.5)


# ─────────────────────────────────────────────────────────────────────────────
# TC-21~30: TestGrafanaDashboardSpec
# ─────────────────────────────────────────────────────────────────────────────
class TestGrafanaDashboardSpec(unittest.TestCase):
    """Grafana 대시보드 JSON 스펙 검증 10건."""

    @classmethod
    def setUpClass(cls):
        """대시보드 JSON 로드."""
        with open(GRAFANA_JSON_PATH, "r", encoding="utf-8") as f:
            cls.dashboard = json.load(f)

    def test_tc21_json_parseable(self):
        """TC-21: grafana_dashboard.json 파싱 성공."""
        self.assertIsInstance(self.dashboard, dict)

    def test_tc22_has_title(self):
        """TC-22: 대시보드 title 존재."""
        self.assertIn("title", self.dashboard)
        self.assertIsInstance(self.dashboard["title"], str)

    def test_tc23_has_uid(self):
        """TC-23: uid 필드 존재."""
        self.assertIn("uid", self.dashboard)

    def test_tc24_has_panels(self):
        """TC-24: panels 배열 존재 + 최소 1개."""
        self.assertIn("panels", self.dashboard)
        self.assertTrue(len(self.dashboard["panels"]) >= 1)

    def test_tc25_panels_have_titles(self):
        """TC-25: 모든 패널에 title 필드 존재."""
        for panel in self.dashboard["panels"]:
            self.assertIn("title", panel, f"Panel {panel.get('id')} missing title")

    def test_tc26_has_tags(self):
        """TC-26: tags 배열에 'literary-os' 포함."""
        self.assertIn("tags", self.dashboard)
        self.assertIn("literary-os", self.dashboard["tags"])

    def test_tc27_has_prometheus_datasource(self):
        """TC-27: __inputs에 Prometheus datasource 정의."""
        self.assertIn("__inputs", self.dashboard)
        prom_inputs = [
            i for i in self.dashboard["__inputs"]
            if i.get("pluginId") == "prometheus"
        ]
        self.assertTrue(len(prom_inputs) >= 1)

    def test_tc28_panels_have_targets(self):
        """TC-28: 모든 패널에 targets 배열 존재."""
        for panel in self.dashboard["panels"]:
            self.assertIn("targets", panel, f"Panel '{panel.get('title')}' missing targets")
            self.assertTrue(len(panel["targets"]) >= 1)

    def test_tc29_targets_use_literary_os_metrics(self):
        """TC-29: 모든 target expr이 literary_os_ 메트릭 참조."""
        for panel in self.dashboard["panels"]:
            for target in panel.get("targets", []):
                expr = target.get("expr", "")
                self.assertIn(
                    "literary_os_", expr,
                    f"Panel '{panel.get('title')}' target expr doesn't use literary_os_ prefix: {expr}"
                )

    def test_tc30_monitoring_config_validate(self):
        """TC-30: MonitoringConfig 기본값 validate() 에러 없음."""
        config = MonitoringConfig()
        errors = config.validate()
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
