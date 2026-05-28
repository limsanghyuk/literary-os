"""literary_system/ops/prometheus_trace_extension.py

V689: Prometheus /metrics 엔드포인트 OTel TraceContext 통합 확장.

설계 원칙:
  LLM-0: 외부 LLM 호출 없음.
  G32: print() 사용 금지 — logger 전용.
  D-M-02: W3C TraceContext propagation — inject/extract 강제.

제공 컴포넌트:
  TraceMetricSnapshot  — span 관련 메트릭을 포함한 확장 스냅샷
  TraceAwareExporter   — trace 컨텍스트 인식 Prometheus 익스포터
  MetricsEndpoint      — /metrics HTTP 엔드포인트 시뮬레이터 (traceparent 전파)
  MetricsResponse      — 엔드포인트 응답 dataclass
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from literary_system.ops.prometheus_exporter import (
    MetricSnapshot,
    MonitoringConfig,
    PrometheusExporter,
)
from literary_system.ops.trace_context import (
    TraceContext,
    TraceContextPropagator,
    new_trace_context,
    child_context,
)
from literary_system.ops.otel_adapter import (
    OtelSdkAdapter,
    SpanData,
    SpanExporter,
    create_otel_adapter,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# 상수
# ─────────────────────────────────────────────────────────────────────────────

TRACE_METRIC_NAMES: Tuple[str, ...] = (
    "spans_exported_total",
    "active_traces",
    "trace_errors_total",
    "p99_span_duration_ms",
)

METRICS_ENDPOINT_PATH = "/metrics"
METRICS_CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"


# ─────────────────────────────────────────────────────────────────────────────
# TraceMetricSnapshot
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TraceMetricSnapshot(MetricSnapshot):
    """Prometheus 메트릭 스냅샷 + OTel trace 통계."""

    # OTel 트레이스 메트릭
    spans_exported_total: int = 0          # 누적 exported span 수 (counter)
    active_traces: int = 0                 # 현재 활성 trace 수 (gauge)
    trace_errors_total: int = 0            # 에러 상태 span 수 (counter)
    p99_span_duration_ms: float = 0.0      # P99 span 지연시간 (ms, gauge)

    # 연결된 trace 컨텍스트 (렌더링 시 traceparent 헤더 생성용)
    trace_context: Optional[TraceContext] = field(default=None, compare=False)

    def validate(self) -> List[str]:
        errors = super().validate()
        if self.spans_exported_total < 0:
            errors.append(
                f"spans_exported_total={self.spans_exported_total} must be >= 0"
            )
        if self.active_traces < 0:
            errors.append(f"active_traces={self.active_traces} must be >= 0")
        if self.trace_errors_total < 0:
            errors.append(
                f"trace_errors_total={self.trace_errors_total} must be >= 0"
            )
        if self.p99_span_duration_ms < 0:
            errors.append(
                f"p99_span_duration_ms={self.p99_span_duration_ms} must be >= 0"
            )
        return errors

    @property
    def trace_error_ratio(self) -> float:
        """에러 span 비율 (spans_exported_total 기준)."""
        if self.spans_exported_total <= 0:
            return 0.0
        return min(1.0, self.trace_errors_total / self.spans_exported_total)

    def has_trace_context(self) -> bool:
        """유효한 trace 컨텍스트 보유 여부."""
        return self.trace_context is not None and self.trace_context.is_valid()


# ─────────────────────────────────────────────────────────────────────────────
# MetricsResponse
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MetricsResponse:
    """MetricsEndpoint.handle_request() 반환값."""

    status_code: int                       # HTTP 상태 코드 (200 / 500)
    content_type: str                      # Content-Type 헤더값
    body: str                              # Prometheus exposition format 본문
    response_headers: Dict[str, str]       # 응답 헤더 (traceparent 포함)
    trace_context: Optional[TraceContext]  # 이 요청에 부여된 trace 컨텍스트
    duration_ms: float = 0.0              # 처리 시간 (ms)

    @property
    def traceparent(self) -> Optional[str]:
        """응답 traceparent 헤더값 (없으면 None)."""
        return self.response_headers.get("traceparent")

    @property
    def is_ok(self) -> bool:
        return self.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# TraceAwareExporter
# ─────────────────────────────────────────────────────────────────────────────

class TraceAwareExporter(PrometheusExporter):
    """PrometheusExporter 확장 — OTel trace 메트릭 추가 렌더링.

    사용 예::

        exporter = TraceAwareExporter()
        snap = TraceMetricSnapshot(
            gates_passed=83, tests_total=8878,
            spans_exported_total=1024, active_traces=3,
            trace_errors_total=2, p99_span_duration_ms=12.5,
        )
        text = exporter.render_trace(snap)
    """

    EXPORTER_VERSION = "1.1.0"

    def __init__(self, config: Optional[MonitoringConfig] = None) -> None:
        super().__init__(config)
        logger.info(
            "[TraceAwareExporter] 초기화 — version=%s", self.EXPORTER_VERSION
        )

    # ── 공개 API ──────────────────────────────────────────────────────────────

    def render_trace(self, snapshot: TraceMetricSnapshot) -> str:
        """기존 메트릭 + trace 메트릭을 포함한 exposition format 반환."""
        errors = snapshot.validate()
        if errors:
            raise ValueError(f"TraceMetricSnapshot 유효성 오류: {errors}")

        # 기본 메트릭 렌더링 (부모 render() 재사용)
        base_text = self.render(snapshot)

        prefix = self.config.metric_prefix
        lines: List[str] = []

        # spans_exported_total (counter)
        lines += [
            f"# HELP {prefix}_spans_exported_total Total OTel spans exported",
            f"# TYPE {prefix}_spans_exported_total counter",
            f"{prefix}_spans_exported_total {snapshot.spans_exported_total}",
        ]

        # active_traces (gauge)
        lines += [
            f"# HELP {prefix}_active_traces Currently active distributed traces",
            f"# TYPE {prefix}_active_traces gauge",
            f"{prefix}_active_traces {snapshot.active_traces}",
        ]

        # trace_errors_total (counter)
        lines += [
            f"# HELP {prefix}_trace_errors_total Total error-status spans",
            f"# TYPE {prefix}_trace_errors_total counter",
            f"{prefix}_trace_errors_total {snapshot.trace_errors_total}",
        ]

        # p99_span_duration_ms (gauge)
        lines += [
            f"# HELP {prefix}_p99_span_duration_ms P99 OTel span duration in ms",
            f"# TYPE {prefix}_p99_span_duration_ms gauge",
            f"{prefix}_p99_span_duration_ms {snapshot.p99_span_duration_ms}",
        ]

        trace_text = "\n".join(lines) + "\n"
        return base_text + trace_text

    def collect_trace(self, snapshot: TraceMetricSnapshot) -> None:
        """TraceMetricSnapshot 수집 — 기존 collect()의 TraceMetricSnapshot 버전."""
        self.collect(snapshot)  # 부모 메서드 재사용 (MetricSnapshot 호환)

    def trace_metric_names(self) -> List[str]:
        """trace 전용 메트릭 이름 목록."""
        prefix = self.config.metric_prefix
        return [f"{prefix}_{name}" for name in TRACE_METRIC_NAMES]


# ─────────────────────────────────────────────────────────────────────────────
# MetricsEndpoint
# ─────────────────────────────────────────────────────────────────────────────

class MetricsEndpoint:
    """/metrics HTTP 엔드포인트 시뮬레이터.

    실제 HTTP 서버 없이 request headers → response 사이클을 모델링.
    W3C TraceContext를 extract → span 생성 → inject 하여
    /metrics 요청-응답에 traceparent가 전파되는 것을 검증.

    사용 예::

        endpoint = MetricsEndpoint()
        snapshot = TraceMetricSnapshot(gates_passed=83, spans_exported_total=100)
        response = endpoint.handle_request(
            request_headers={"traceparent": "00-abc..."},
            snapshot=snapshot,
        )
        assert "traceparent" in response.response_headers
        assert response.is_ok
    """

    def __init__(
        self,
        exporter: Optional[TraceAwareExporter] = None,
        adapter: Optional[OtelSdkAdapter] = None,
    ) -> None:
        self.exporter: TraceAwareExporter = exporter or TraceAwareExporter()
        self.adapter: OtelSdkAdapter = adapter or create_otel_adapter("literary-os-metrics")
        self._request_count: int = 0
        self._error_count: int = 0
        logger.info("[MetricsEndpoint] 초기화 완료")

    # ── 공개 API ──────────────────────────────────────────────────────────────

    def handle_request(
        self,
        request_headers: Optional[Dict[str, str]] = None,
        snapshot: Optional[TraceMetricSnapshot] = None,
    ) -> MetricsResponse:
        """/metrics 요청 처리.

        1. request_headers에서 traceparent 추출 (없으면 신규 생성)
        2. child span 생성 (metrics_scrape span)
        3. 메트릭 렌더링
        4. response_headers에 traceparent inject
        5. MetricsResponse 반환

        Args:
            request_headers: HTTP 요청 헤더 dict (traceparent 포함 가능)
            snapshot: 렌더링할 TraceMetricSnapshot

        Returns:
            MetricsResponse
        """
        t_start = time.monotonic()
        self._request_count += 1
        headers = request_headers or {}

        # ① TraceContext 추출 또는 신규 생성
        parent_ctx: TraceContext = TraceContextPropagator.extract_or_create(headers)

        # ② child span 생성 (metrics_scrape)
        child_ctx = child_context(parent_ctx)
        span = self.adapter.start_span("metrics_scrape", parent=parent_ctx)
        span.set_attribute("http.method", "GET")
        span.set_attribute("http.path", METRICS_ENDPOINT_PATH)
        span.set_attribute("request_count", self._request_count)

        try:
            # ③ 스냅샷이 없으면 최소 기본값 사용
            if snapshot is None:
                snapshot = TraceMetricSnapshot()

            # ④ 메트릭 렌더링
            body = self.exporter.render_trace(snapshot)

            # ⑤ 응답 헤더 구성 — child traceparent inject
            response_headers: Dict[str, str] = {
                "Content-Type": METRICS_CONTENT_TYPE,
            }
            TraceContextPropagator.inject(child_ctx, response_headers)

            span.set_attribute("http.status_code", 200)
            span_data = span.end()

            duration_ms = (time.monotonic() - t_start) * 1000.0
            logger.info(
                "[MetricsEndpoint] GET /metrics — trace=%s span=%s %.1fms",
                child_ctx.trace_id[:8],
                child_ctx.parent_id[:8],
                duration_ms,
            )

            return MetricsResponse(
                status_code=200,
                content_type=METRICS_CONTENT_TYPE,
                body=body,
                response_headers=response_headers,
                trace_context=child_ctx,
                duration_ms=duration_ms,
            )

        except Exception as exc:
            self._error_count += 1
            span.set_status("error")
            span.set_attribute("error.message", str(exc))
            span.end()

            response_headers = {"Content-Type": "text/plain"}
            TraceContextPropagator.inject(child_ctx, response_headers)

            duration_ms = (time.monotonic() - t_start) * 1000.0
            logger.error(
                "[MetricsEndpoint] /metrics 처리 오류: %s", exc, exc_info=True
            )

            return MetricsResponse(
                status_code=500,
                content_type="text/plain",
                body=f"# Error: {exc}\n",
                response_headers=response_headers,
                trace_context=child_ctx,
                duration_ms=duration_ms,
            )

    @property
    def request_count(self) -> int:
        """총 요청 수."""
        return self._request_count

    @property
    def error_count(self) -> int:
        """에러 응답 수."""
        return self._error_count

    def reset_counters(self) -> None:
        """요청/에러 카운터 초기화."""
        self._request_count = 0
        self._error_count = 0


# ─────────────────────────────────────────────────────────────────────────────
# 팩토리
# ─────────────────────────────────────────────────────────────────────────────

def create_metrics_endpoint(
    version: str = "12.0.2",
    phase: str = "D",
    service_name: str = "literary-os-metrics",
) -> MetricsEndpoint:
    """MetricsEndpoint 팩토리 함수."""
    config = MonitoringConfig(version=version, phase=phase)
    exporter = TraceAwareExporter(config)
    adapter = create_otel_adapter(service_name=service_name)
    return MetricsEndpoint(exporter=exporter, adapter=adapter)
