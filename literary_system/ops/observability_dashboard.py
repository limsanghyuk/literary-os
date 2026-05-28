"""
literary_system/ops/observability_dashboard.py
───────────────────────────────────────────────
SP-D.1 V692 · ObservabilityDashboard — 멀티패널 메트릭 집계 + 알림 룰

ADR-155: SP-D.1 Observability Dashboard 실시간 운영 지표 시각화 계층
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertState(str, Enum):
    OK = "ok"
    FIRING = "firing"
    RESOLVED = "resolved"


class PanelType(str, Enum):
    GAUGE = "gauge"
    COUNTER = "counter"
    TIMESERIES = "timeseries"


@dataclass
class ObsMetricPoint:
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class ObsAlert:
    """임계값 기반 알림 규칙.

    fire_when_below=True  -> value < threshold 이면 FIRING
    fire_when_below=False -> value >= threshold 이면 FIRING (기본)
    """
    name: str
    metric_name: str
    threshold: float
    severity: AlertSeverity = AlertSeverity.WARNING
    state: AlertState = AlertState.OK
    fire_when_below: bool = False
    _fired_at: Optional[float] = field(default=None, init=False, repr=False)

    def evaluate(self, value: float) -> bool:
        if self.fire_when_below:
            firing = value < self.threshold
        else:
            firing = value >= self.threshold

        previous = self.state
        if firing:
            self.state = AlertState.FIRING
            if self._fired_at is None:
                self._fired_at = time.time()
        else:
            if previous == AlertState.FIRING:
                self.state = AlertState.RESOLVED
            else:
                self.state = AlertState.OK
            self._fired_at = None

        return firing

    @property
    def is_firing(self) -> bool:
        return self.state == AlertState.FIRING

    @property
    def fired_at(self) -> Optional[float]:
        return self._fired_at


class ObsDashboardPanel:
    def __init__(
        self,
        name: str,
        panel_type: PanelType = PanelType.GAUGE,
        unit: str = "",
        description: str = "",
        max_history: int = 1000,
    ) -> None:
        self.name = name
        self.panel_type = panel_type
        self.unit = unit
        self.description = description
        self._max_history = max_history
        self._points: List[ObsMetricPoint] = []
        self._alerts: List[ObsAlert] = []

    def record(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        point = ObsMetricPoint(value=value, labels=labels or {})
        self._points.append(point)
        if len(self._points) > self._max_history:
            self._points = self._points[-self._max_history:]
        for alert in self._alerts:
            if alert.metric_name == self.name:
                alert.evaluate(value)

    def history(self, last_n: int = 10) -> List[ObsMetricPoint]:
        return self._points[-last_n:]

    def latest(self) -> Optional[ObsMetricPoint]:
        return self._points[-1] if self._points else None

    def latest_value(self) -> Optional[float]:
        p = self.latest()
        return p.value if p else None

    def average(self, last_n: int = 10) -> float:
        pts = self._points[-last_n:]
        if not pts:
            return 0.0
        return sum(p.value for p in pts) / len(pts)

    def max_value(self, last_n: int = 10) -> float:
        pts = self._points[-last_n:]
        return max(p.value for p in pts) if pts else 0.0

    def min_value(self, last_n: int = 10) -> float:
        pts = self._points[-last_n:]
        return min(p.value for p in pts) if pts else 0.0

    def count(self) -> int:
        return len(self._points)

    def add_alert(self, alert: ObsAlert) -> None:
        self._alerts.append(alert)

    def firing_alerts(self) -> List[ObsAlert]:
        return [a for a in self._alerts if a.is_firing]

    def all_alerts(self) -> List[ObsAlert]:
        return list(self._alerts)

    def to_dict(self) -> Dict:
        latest = self.latest()
        return {
            "name": self.name,
            "type": self.panel_type.value,
            "unit": self.unit,
            "description": self.description,
            "latest_value": latest.value if latest else None,
            "count": self.count(),
            "average_last10": round(self.average(), 4),
            "max_last10": round(self.max_value(), 4),
            "min_last10": round(self.min_value(), 4),
            "firing_alerts": [a.name for a in self.firing_alerts()],
        }


class ObservabilityDashboard:
    def __init__(self, service_name: str = "literary-os", version: str = "SP-D.1") -> None:
        self.service_name = service_name
        self.version = version
        self._panels: Dict[str, ObsDashboardPanel] = {}
        self._created_at: float = time.time()

    def add_panel(self, panel: ObsDashboardPanel) -> None:
        self._panels[panel.name] = panel

    def panel(self, name: str) -> Optional[ObsDashboardPanel]:
        return self._panels.get(name)

    def panels(self) -> List[ObsDashboardPanel]:
        return list(self._panels.values())

    def panel_names(self) -> List[str]:
        return list(self._panels.keys())

    def record(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> bool:
        p = self._panels.get(metric_name)
        if p is None:
            return False
        p.record(value, labels)
        return True

    def firing_alerts(self) -> List[ObsAlert]:
        result: List[ObsAlert] = []
        for panel in self._panels.values():
            result.extend(panel.firing_alerts())
        return result

    def all_alerts(self) -> List[ObsAlert]:
        result: List[ObsAlert] = []
        for panel in self._panels.values():
            result.extend(panel.all_alerts())
        return result

    def alert_summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {s.value: 0 for s in AlertSeverity}
        for alert in self.firing_alerts():
            counts[alert.severity.value] += 1
        return counts

    def health(self) -> str:
        firing = self.firing_alerts()
        severities = {a.severity for a in firing}
        if AlertSeverity.CRITICAL in severities:
            return "degraded"
        if AlertSeverity.WARNING in severities:
            return "warning"
        return "healthy"

    def summary(self) -> Dict:
        return {
            "service": self.service_name,
            "version": self.version,
            "health": self.health(),
            "panel_count": len(self._panels),
            "panels": {name: p.to_dict() for name, p in self._panels.items()},
            "firing_alerts": [
                {
                    "name": a.name,
                    "metric": a.metric_name,
                    "severity": a.severity.value,
                    "threshold": a.threshold,
                    "fire_when_below": a.fire_when_below,
                }
                for a in self.firing_alerts()
            ],
            "alert_summary": self.alert_summary(),
        }


def create_spd1_dashboard(service_name: str = "literary-os") -> ObservabilityDashboard:
    """SP-D.1 표준 5패널 대시보드."""
    dash = ObservabilityDashboard(service_name=service_name, version="SP-D.1")

    # 1. gates_pass_ratio  (fire_when_below=True: 0.95 미만 -> CRITICAL)
    p1 = ObsDashboardPanel(
        name="gates_pass_ratio",
        panel_type=PanelType.GAUGE,
        unit="ratio",
        description="릴리즈 Gate PASS 비율 (>=0.95 정상)",
    )
    p1.add_alert(ObsAlert(
        name="GatesPassRatioCritical",
        metric_name="gates_pass_ratio",
        threshold=0.95,
        severity=AlertSeverity.CRITICAL,
        fire_when_below=True,
    ))
    dash.add_panel(p1)

    # 2. spans_exported_total
    p2 = ObsDashboardPanel(
        name="spans_exported_total",
        panel_type=PanelType.COUNTER,
        unit="spans",
        description="OTel Exporter 총 스팬 수",
    )
    p2.add_alert(ObsAlert(
        name="SpanVolumeHigh",
        metric_name="spans_exported_total",
        threshold=50_000,
        severity=AlertSeverity.WARNING,
        fire_when_below=False,
    ))
    dash.add_panel(p2)

    # 3. active_traces
    p3 = ObsDashboardPanel(
        name="active_traces",
        panel_type=PanelType.GAUGE,
        unit="traces",
        description="현재 활성 트레이스 수",
    )
    p3.add_alert(ObsAlert(
        name="ActiveTracesHigh",
        metric_name="active_traces",
        threshold=100,
        severity=AlertSeverity.WARNING,
        fire_when_below=False,
    ))
    dash.add_panel(p3)

    # 4. p99_span_duration_ms
    p4 = ObsDashboardPanel(
        name="p99_span_duration_ms",
        panel_type=PanelType.GAUGE,
        unit="ms",
        description="스팬 처리 P99 지연시간",
    )
    p4.add_alert(ObsAlert(
        name="P99LatencyHigh",
        metric_name="p99_span_duration_ms",
        threshold=500,
        severity=AlertSeverity.WARNING,
        fire_when_below=False,
    ))
    dash.add_panel(p4)

    # 5. trace_error_ratio
    p5 = ObsDashboardPanel(
        name="trace_error_ratio",
        panel_type=PanelType.GAUGE,
        unit="ratio",
        description="트레이스 에러 비율 (<=0.05 정상)",
    )
    p5.add_alert(ObsAlert(
        name="TraceErrorRatioCritical",
        metric_name="trace_error_ratio",
        threshold=0.05,
        severity=AlertSeverity.CRITICAL,
        fire_when_below=False,
    ))
    dash.add_panel(p5)

    return dash


def record_otel_metrics(
    dashboard: ObservabilityDashboard,
    spans_exported: int,
    active_traces: int,
    p99_ms: float,
    error_ratio: float,
) -> Tuple[bool, bool, bool, bool]:
    r1 = dashboard.record("spans_exported_total", float(spans_exported))
    r2 = dashboard.record("active_traces", float(active_traces))
    r3 = dashboard.record("p99_span_duration_ms", p99_ms)
    r4 = dashboard.record("trace_error_ratio", error_ratio)
    return r1, r2, r3, r4


def record_gate_metrics(
    dashboard: ObservabilityDashboard,
    passed: int,
    total: int,
) -> bool:
    ratio = passed / total if total > 0 else 0.0
    return dashboard.record("gates_pass_ratio", ratio)
