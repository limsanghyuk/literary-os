"""
literary_system/ops/otel_adapter.py
=====================================
V688 — OTel SDK Adapter (D-M-02, ADR-151)

OpenTelemetry SDK의 경량 모의 어댑터.
실제 OTel SDK 설치 없이 동일한 인터페이스를 제공.
실제 환경에서는 `opentelemetry-sdk` 설치 후 OtelSdkAdapter를 사용.

제공 인터페이스:
  SpanData              — 완료된 스팬 데이터
  TraceSpan             — 컨텍스트 매니저 스팬
  OtelSdkAdapter        — 트레이서 + W3C 컨텍스트 전파 통합
  create_otel_adapter() — 팩토리

LLM-0 원칙 완전 준수 (외부 LLM 호출 없음)
ADR-151 참조.
"""
from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, List, Optional

from literary_system.ops.trace_context import (
    TraceContext,
    TraceContextPropagator,
    TraceFlags,
    child_context,
    new_trace_context,
)


# ── 스팬 데이터 ──────────────────────────────────────────────

@dataclass
class SpanData:
    """완료된 스팬의 불변 스냅샷."""
    trace_id:   str
    span_id:    str
    name:       str
    start_ns:   int
    end_ns:     int
    status:     str                       = "ok"
    attributes: Dict[str, Any]            = field(default_factory=dict)
    events:     List[Dict[str, Any]]      = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        return (self.end_ns - self.start_ns) / 1_000_000

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id":   self.trace_id,
            "span_id":    self.span_id,
            "name":       self.name,
            "start_ns":   self.start_ns,
            "end_ns":     self.end_ns,
            "duration_ms": self.duration_ms,
            "status":     self.status,
            "attributes": self.attributes,
            "events":     self.events,
        }


# ── 활성 스팬 ────────────────────────────────────────────────

class TraceSpan:
    """컨텍스트 매니저 스팬 (OTel Span 인터페이스 모의)."""

    def __init__(
        self,
        name: str,
        ctx: TraceContext,
        exporter: "SpanExporter",
    ) -> None:
        self.name = name
        self.ctx  = ctx
        self._exporter = exporter
        self._start_ns = time.time_ns()
        self._end_ns   = 0
        self._status   = "ok"
        self._attributes: Dict[str, Any] = {}
        self._events: List[Dict[str, Any]] = []

    def set_attribute(self, key: str, value: Any) -> "TraceSpan":
        """스팬 속성 설정."""
        self._attributes[key] = value
        return self

    def add_event(self, name: str, **kwargs: Any) -> "TraceSpan":
        """스팬 이벤트 추가."""
        self._events.append({"name": name, "timestamp_ns": time.time_ns(), **kwargs})
        return self

    def set_status(self, status: str) -> "TraceSpan":
        """스팬 상태 설정 ('ok' / 'error')."""
        self._status = status
        return self

    def end(self) -> SpanData:
        """스팬 종료 및 export."""
        self._end_ns = time.time_ns()
        data = SpanData(
            trace_id=self.ctx.trace_id,
            span_id=self.ctx.parent_id,
            name=self.name,
            start_ns=self._start_ns,
            end_ns=self._end_ns,
            status=self._status,
            attributes=dict(self._attributes),
            events=list(self._events),
        )
        self._exporter.export(data)
        return data

    def __enter__(self) -> "TraceSpan":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            self.set_status("error")
            self.set_attribute("error.type", exc_type.__name__)
        self.end()


# ── 스팬 익스포터 ────────────────────────────────────────────

class SpanExporter:
    """완료된 스팬을 수집하는 인메모리 익스포터."""

    def __init__(self) -> None:
        self._spans: List[SpanData] = []

    def export(self, span: SpanData) -> None:
        self._spans.append(span)

    @property
    def spans(self) -> List[SpanData]:
        return list(self._spans)

    def clear(self) -> None:
        self._spans.clear()

    def find_by_name(self, name: str) -> List[SpanData]:
        return [s for s in self._spans if s.name == name]


# ── OTel SDK 어댑터 ──────────────────────────────────────────

class OtelSdkAdapter:
    """
    OTel SDK + W3C TraceContext 통합 어댑터.

    사용법:
        adapter = OtelSdkAdapter(service_name="literary-os")

        # 신규 루트 트레이스
        with adapter.start_span("process_chapter") as span:
            span.set_attribute("chapter.id", 42)

        # 인바운드 HTTP 요청에서 컨텍스트 전파
        ctx = adapter.extract(request_headers)
        with adapter.start_span("handle_request", parent=ctx) as span:
            ...

        # 아웃바운드 요청에 컨텍스트 주입
        out_headers = {}
        adapter.inject(span.ctx, out_headers)
    """

    def __init__(
        self,
        service_name: str = "literary-os",
        sampled: bool = True,
    ) -> None:
        self.service_name = service_name
        self._sampled     = sampled
        self._exporter    = SpanExporter()
        self._propagator  = TraceContextPropagator()

    # ── 스팬 생성 ────────────────────────────────────────────

    def start_span(
        self,
        name: str,
        parent: Optional[TraceContext] = None,
    ) -> TraceSpan:
        """새 스팬을 시작한다.

        parent가 주어지면 자식 컨텍스트를 파생,
        없으면 새 루트 컨텍스트를 생성.
        """
        if parent is not None:
            ctx = child_context(parent, sampled=self._sampled)
        else:
            ctx = new_trace_context(sampled=self._sampled)

        ctx.tracestate = "svc={}".format(self.service_name)
        span = TraceSpan(name=name, ctx=ctx, exporter=self._exporter)
        span.set_attribute("service.name", self.service_name)
        return span

    @contextmanager
    def trace(
        self,
        name: str,
        parent: Optional[TraceContext] = None,
    ) -> Generator[TraceSpan, None, None]:
        """컨텍스트 매니저 형태의 트레이스 헬퍼."""
        span = self.start_span(name, parent=parent)
        try:
            yield span
        except Exception as exc:
            span.set_status("error")
            span.set_attribute("error.message", str(exc))
            raise
        finally:
            if span._end_ns == 0:
                span.end()

    # ── 컨텍스트 전파 ────────────────────────────────────────

    def inject(self, ctx: TraceContext, headers: Dict[str, str]) -> None:
        """outbound 헤더에 TraceContext 주입."""
        TraceContextPropagator.inject(ctx, headers)

    def extract(self, headers: Dict[str, str]) -> Optional[TraceContext]:
        """inbound 헤더에서 TraceContext 추출. 없으면 None."""
        return TraceContextPropagator.extract(headers)

    def extract_or_create(self, headers: Dict[str, str]) -> TraceContext:
        """헤더 추출 또는 새 루트 컨텍스트 생성."""
        return TraceContextPropagator.extract_or_create(headers)

    # ── 익스포터 접근 ────────────────────────────────────────

    @property
    def exporter(self) -> SpanExporter:
        return self._exporter

    @property
    def spans(self) -> List[SpanData]:
        return self._exporter.spans

    def clear_spans(self) -> None:
        self._exporter.clear()


# ── 팩토리 ──────────────────────────────────────────────────

def create_otel_adapter(
    service_name: str = "literary-os",
    sampled: bool = True,
) -> OtelSdkAdapter:
    """OtelSdkAdapter 팩토리."""
    return OtelSdkAdapter(service_name=service_name, sampled=sampled)


# ── 독립 실행 데모 ───────────────────────────────────────────

if __name__ == "__main__":
    import sys
    adapter = create_otel_adapter("demo-service")

    # 루트 스팬
    with adapter.trace("root.operation") as root_span:
        root_span.set_attribute("user.id", "user_001")
        root_span.add_event("processing_started")

        # 자식 스팬 (컨텍스트 전파)
        outbound: Dict[str, str] = {}
        adapter.inject(root_span.ctx, outbound)
        sys.stdout.write("Injected headers: " + str(outbound) + "\n")

        inbound_ctx = adapter.extract(outbound)
        with adapter.trace("child.operation", parent=inbound_ctx) as child_span:
            child_span.set_attribute("child.key", "value")

    sys.stdout.write("\nCompleted spans: " + str(len(adapter.spans)) + "\n")
    for s in adapter.spans:
        sys.stdout.write(f"  [{s.status}] {s.name} — {s.duration_ms:.2f}ms — trace={s.trace_id[:8]}...\n")
