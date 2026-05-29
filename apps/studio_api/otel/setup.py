"""
V422: OpenTelemetry SDK 실 연결
ADR-003: SLO — /analyze P95<1.5s, /generate P95<30s, /gate P95<5s, 가용성 99.5%

인터페이스 불변 원칙 (GitNexus):
  - start_span(name, trace_id) → contextmanager[Span]  ← V420과 동일
  - Span.set_attribute / add_event / duration_ms        ← V420과 동일
  - SLO 딕셔너리                                        ← V420과 동일

V420 stub → V422: opentelemetry-sdk 실 연결
            OTLP exporter (환경변수 OTEL_EXPORTER_OTLP_ENDPOINT 설정 시 활성화)
"""
from __future__ import annotations

import os
import time
import uuid
import logging
from contextlib import contextmanager
from typing import Any, Generator

logger = logging.getLogger(__name__)

# ── SLO 상수 (ADR-003) ────────────────────────────────────────
SLO: dict[str, float] = {
    "/api/v1/analyze":  1.5,
    "/api/v1/generate": 30.0,
    "/api/v1/gate":     5.0,
    "/api/v1/import":   60.0,
    "/api/v1/export":   30.0,
    "/api/v1/voice/analyze": 10.0,
}

# ── OpenTelemetry SDK 초기화 ──────────────────────────────────
_OTEL_AVAILABLE = False
_tracer: Any = None
_meter: Any = None

try:
    from opentelemetry import trace as otel_trace, metrics as otel_metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
    )
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import (
        ConsoleMetricExporter, PeriodicExportingMetricReader
    )
    from opentelemetry.sdk.resources import Resource

    _resource = Resource.create({
        "service.name": "literary-os-studio-api",
        "service.version": "V422",
        "deployment.environment": os.environ.get("LITERARY_OS_ENV", "development"),
    })

    # Tracer Provider
    _tracer_provider = TracerProvider(resource=_resource)

    _otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    if _otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            _tracer_provider.add_span_processor(
                BatchSpanProcessor(OTLPSpanExporter(endpoint=_otlp_endpoint))
            )
            logger.info("OTel OTLP exporter 활성화: %s", _otlp_endpoint)
        except Exception as _exc:
            logger.warning("OTLP exporter 초기화 실패 (fallback Console): %s", _exc)
            _tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    else:
        # 개발 환경: 콘솔 exporter (OTEL_LOG_LEVEL=DEBUG 시에만 출력)
        if os.environ.get("OTEL_LOG_LEVEL", "").upper() == "DEBUG":
            _tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    otel_trace.set_tracer_provider(_tracer_provider)
    _tracer = otel_trace.get_tracer("literary-os", "V422")

    # Meter Provider (Prometheus 메트릭 — V421)
    _metric_readers = []
    _prometheus_port = int(os.environ.get("OTEL_PROMETHEUS_PORT", "0"))
    if _prometheus_port:
        try:
            from opentelemetry.exporter.prometheus import PrometheusMetricReader
            _metric_readers.append(PrometheusMetricReader())
            logger.info("Prometheus 메트릭 활성화: port=%d", _prometheus_port)
        except ImportError:
            pass

    # V481 Hotfix: 프로덕션 exporter가 없으면 PeriodicExportingMetricReader(ConsoleMetricExporter)
    # 를 등록하지 않음 — 60초 백그라운드 스레드가 pytest 종료 후 닫힌 stdout에 write를
    # 시도하여 "I/O operation on closed file" ValueError 유발. reader 없이 MeterProvider
    # 를 초기화하면 메트릭 수집은 되지만 export가 없어 teardown 아티팩트가 제거됨.
    _meter_provider = MeterProvider(resource=_resource, metric_readers=_metric_readers)
    otel_metrics.set_meter_provider(_meter_provider)
    _meter = otel_metrics.get_meter("literary-os", "V422")

    # ── SLO 계측 메트릭 ─────────────────────────────────────────
    _request_duration = _meter.create_histogram(
        name="http_request_duration_seconds",
        description="HTTP 요청 처리 시간 (초)",
        unit="s",
    )
    _slo_breach_counter = _meter.create_counter(
        name="slo_breach_total",
        description="SLO 위반 횟수",
    )
    _request_counter = _meter.create_counter(
        name="http_request_total",
        description="HTTP 요청 총 수",
    )

    _OTEL_AVAILABLE = True
    logger.info("OpenTelemetry SDK V422 초기화 완료")

except ImportError as _ie:
    logger.info("opentelemetry-sdk 미설치 — stub 모드 유지 (%s)", _ie)
except Exception as _exc:
    logger.warning("OTel 초기화 오류 — stub 모드 유지: %s", _exc)


# ── Span 래퍼 (인터페이스 불변) ───────────────────────────────
class Span:
    """
    V420 인터페이스 완전 호환 Span 래퍼.
    _otel_span이 있으면 OTel SDK로 위임, 없으면 stub.
    """

    def __init__(self, name: str, trace_id: str = "", otel_span: Any = None) -> None:
        self.name = name
        self.trace_id = trace_id or str(uuid.uuid4())
        self._start = time.monotonic()
        self._end: float | None = None
        self._otel_span = otel_span
        self._attrs: dict[str, Any] = {}
        self._events: list[dict] = []

    def set_attribute(self, key: str, value: Any) -> None:
        self._attrs[key] = value
        if self._otel_span is not None:
            try:
                self._otel_span.set_attribute(key, value)
            except Exception:
                pass

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        self._events.append({"name": name, "attributes": attributes or {}})
        if self._otel_span is not None:
            try:
                self._otel_span.add_event(name, attributes=attributes or {})
            except Exception:
                pass

    def end(self) -> None:
        self._end = time.monotonic()
        if self._otel_span is not None:
            try:
                self._otel_span.end()
            except Exception:
                pass

    @property
    def duration_ms(self) -> float:
        end = self._end if self._end is not None else time.monotonic()
        return (end - self._start) * 1000.0


@contextmanager
def start_span(
    name: str,
    trace_id: str = "",
) -> Generator[Span, None, None]:
    """
    OTel span 컨텍스트 매니저.
    V420 인터페이스 불변 — 내부에서 OTel SDK 사용 (가용 시).

    사용:
        with start_span("analyze.drse", trace_id=req_id) as span:
            span.set_attribute("series_id", req.series_id)
    """
    otel_span = None
    if _OTEL_AVAILABLE and _tracer is not None:
        try:
            ctx_manager = _tracer.start_as_current_span(
                name,
                attributes={"trace.id": trace_id or ""},
            )
            otel_span = ctx_manager.__enter__()
        except Exception:
            otel_span = None

    span = Span(name=name, trace_id=trace_id, otel_span=otel_span)

    try:
        yield span
    finally:
        span.end()

        # ── SLO 계측 ──────────────────────────────────────────
        dur_s = span.duration_ms / 1000.0

        if _OTEL_AVAILABLE:
            try:
                # 경로 추출 (/api/v1/... 형식)
                http_path = span._attrs.get("http.path", name)
                labels = {
                    "endpoint": http_path,
                    "span_name": name,
                }
                _request_duration.record(dur_s, labels)
                _request_counter.add(1, labels)

                slo_limit = SLO.get(http_path)
                if slo_limit and dur_s > slo_limit:
                    _slo_breach_counter.add(1, {**labels, "slo_limit_s": str(slo_limit)})
                    logger.warning(
                        "SLO 위반 [%s] %.3fs > %.1fs",
                        http_path, dur_s, slo_limit,
                    )
            except Exception:
                pass

        # OTel span 종료
        if otel_span is not None:
            try:
                ctx_manager.__exit__(None, None, None)
            except Exception:
                pass


def new_trace_id() -> str:
    """새 trace ID 생성 — UUID4 hex."""
    return str(uuid.uuid4())
