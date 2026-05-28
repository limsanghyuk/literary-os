"""
tests/unit/test_v688_otel_tracecontext.py
V688 — W3C TraceContext + OTel SDK Adapter 검증 (ADR-151)

TC-01~TC-33: TraceContext / TraceContextPropagator / OtelSdkAdapter 전체 커버
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import re
import time

from literary_system.ops.trace_context import (
    TraceContext,
    TraceContextPropagator,
    TraceFlags,
    new_trace_context,
    child_context,
    VERSION,
    TRACEPARENT_HEADER,
    TRACESTATE_HEADER,
)
from literary_system.ops.otel_adapter import (
    SpanData,
    TraceSpan,
    SpanExporter,
    OtelSdkAdapter,
    create_otel_adapter,
)


# ─── TC-01~TC-06: TraceContext 기본 ──────────────────────────

def test_tc01_new_trace_context_valid():
    """TC-01: new_trace_context() → is_valid()=True"""
    ctx = new_trace_context()
    assert ctx.is_valid()


def test_tc02_trace_id_32hex():
    """TC-02: trace_id는 32자 hex"""
    ctx = new_trace_context()
    assert len(ctx.trace_id) == 32
    assert re.fullmatch(r"[0-9a-f]{32}", ctx.trace_id)


def test_tc03_parent_id_16hex():
    """TC-03: parent_id(span_id)는 16자 hex"""
    ctx = new_trace_context()
    assert len(ctx.parent_id) == 16
    assert re.fullmatch(r"[0-9a-f]{16}", ctx.parent_id)


def test_tc04_sampled_flag_default():
    """TC-04: 기본 sampled=True"""
    ctx = new_trace_context()
    assert ctx.is_sampled() is True


def test_tc05_unsampled_flag():
    """TC-05: sampled=False → flags=0"""
    ctx = new_trace_context(sampled=False)
    assert ctx.is_sampled() is False
    assert ctx.flags == TraceFlags.NONE


def test_tc06_traceparent_format():
    """TC-06: traceparent 형식 검증 00-{32}-{16}-{2}"""
    ctx = new_trace_context()
    parts = ctx.traceparent.split("-")
    assert len(parts) == 4
    assert parts[0] == VERSION
    assert len(parts[1]) == 32
    assert len(parts[2]) == 16
    assert len(parts[3]) == 2


# ─── TC-07~TC-11: child_context ──────────────────────────────

def test_tc07_child_inherits_trace_id():
    """TC-07: 자식은 trace_id를 부모에서 상속"""
    parent = new_trace_context()
    child  = child_context(parent)
    assert child.trace_id == parent.trace_id


def test_tc08_child_new_span_id():
    """TC-08: 자식의 span_id(parent_id)는 부모와 다름"""
    parent = new_trace_context()
    child  = child_context(parent)
    assert child.parent_id != parent.parent_id


def test_tc09_child_inherits_flags():
    """TC-09: 자식은 부모 flags 상속"""
    parent = new_trace_context(sampled=True)
    child  = child_context(parent)
    assert child.is_sampled() is True


def test_tc10_child_override_sampled():
    """TC-10: child_context(sampled=False)로 오버라이드"""
    parent = new_trace_context(sampled=True)
    child  = child_context(parent, sampled=False)
    assert child.is_sampled() is False


def test_tc11_child_invalid_parent_raises():
    """TC-11: 유효하지 않은 parent → ValueError"""
    bad = TraceContext(trace_id="0" * 32, parent_id="0" * 16)
    try:
        child_context(bad)
        assert False, "Should raise ValueError"
    except ValueError:
        pass


# ─── TC-12~TC-17: TraceContextPropagator ─────────────────────

def test_tc12_inject_adds_traceparent():
    """TC-12: inject() → 헤더에 traceparent 추가"""
    ctx = new_trace_context()
    headers: dict = {}
    TraceContextPropagator.inject(ctx, headers)
    assert TRACEPARENT_HEADER in headers
    assert headers[TRACEPARENT_HEADER] == ctx.traceparent


def test_tc13_inject_tracestate_if_set():
    """TC-13: tracestate가 있으면 헤더에 포함"""
    ctx = new_trace_context()
    ctx.tracestate = "vendor=abc"
    headers: dict = {}
    TraceContextPropagator.inject(ctx, headers)
    assert TRACESTATE_HEADER in headers


def test_tc14_extract_valid():
    """TC-14: extract() → 올바른 trace_id 복원"""
    ctx = new_trace_context()
    headers = {TRACEPARENT_HEADER: ctx.traceparent}
    extracted = TraceContextPropagator.extract(headers)
    assert extracted is not None
    assert extracted.trace_id == ctx.trace_id


def test_tc15_extract_missing_returns_none():
    """TC-15: 헤더 없으면 None"""
    extracted = TraceContextPropagator.extract({})
    assert extracted is None


def test_tc16_extract_invalid_returns_none():
    """TC-16: 잘못된 traceparent → None"""
    extracted = TraceContextPropagator.extract({TRACEPARENT_HEADER: "bad-value"})
    assert extracted is None


def test_tc17_extract_or_create_creates_root():
    """TC-17: 헤더 없으면 새 컨텍스트 생성"""
    ctx = TraceContextPropagator.extract_or_create({})
    assert ctx.is_valid()


# ─── TC-18~TC-22: TraceContext 직렬화 ────────────────────────

def test_tc18_to_dict():
    """TC-18: to_dict() → traceparent 키 포함"""
    ctx = new_trace_context()
    d = ctx.to_dict()
    assert TRACEPARENT_HEADER in d


def test_tc19_from_traceparent_roundtrip():
    """TC-19: from_traceparent(ctx.traceparent) → 동일 trace_id"""
    ctx = new_trace_context()
    restored = TraceContext.from_traceparent(ctx.traceparent)
    assert restored.trace_id == ctx.trace_id


def test_tc20_from_traceparent_invalid_raises():
    """TC-20: 잘못된 형식 → ValueError"""
    try:
        TraceContext.from_traceparent("00-invalid-bad-zz")
        assert False
    except ValueError:
        pass


def test_tc21_version_ff_rejected():
    """TC-21: version ff → ValueError (reserved)"""
    bad = "ff-" + "a" * 32 + "-" + "b" * 16 + "-01"
    try:
        TraceContext.from_traceparent(bad)
        assert False
    except ValueError:
        pass


def test_tc22_case_insensitive_extract():
    """TC-22: 헤더 키 대소문자 무시"""
    ctx = new_trace_context()
    headers = {"Traceparent": ctx.traceparent}  # 대문자
    extracted = TraceContextPropagator.extract(headers)
    assert extracted is not None
    assert extracted.trace_id == ctx.trace_id


# ─── TC-23~TC-28: OtelSdkAdapter 기본 ───────────────────────

def test_tc23_create_otel_adapter():
    """TC-23: create_otel_adapter() 생성 성공"""
    adapter = create_otel_adapter("test-svc")
    assert adapter.service_name == "test-svc"


def test_tc24_start_span_root():
    """TC-24: 루트 스팬 시작 → 유효 컨텍스트"""
    adapter = create_otel_adapter()
    span = adapter.start_span("root")
    assert span.ctx.is_valid()
    span.end()


def test_tc25_start_span_child_inherits_trace_id():
    """TC-25: 자식 스팬은 부모 trace_id 상속"""
    adapter = create_otel_adapter()
    parent_span = adapter.start_span("parent")
    child_span  = adapter.start_span("child", parent=parent_span.ctx)
    assert child_span.ctx.trace_id == parent_span.ctx.trace_id
    child_span.end()
    parent_span.end()


def test_tc26_span_set_attribute():
    """TC-26: set_attribute() 체이닝"""
    adapter = create_otel_adapter()
    span = adapter.start_span("test")
    result = span.set_attribute("key", "value")
    assert result is span
    assert span._attributes["key"] == "value"
    span.end()


def test_tc27_span_add_event():
    """TC-27: add_event() 기록"""
    adapter = create_otel_adapter()
    span = adapter.start_span("test")
    span.add_event("my_event", data="x")
    assert len(span._events) == 1
    assert span._events[0]["name"] == "my_event"
    span.end()


def test_tc28_span_end_exports():
    """TC-28: span.end() → exporter에 SpanData 저장"""
    adapter = create_otel_adapter()
    span = adapter.start_span("export_test")
    data = span.end()
    assert isinstance(data, SpanData)
    assert len(adapter.spans) == 1
    assert adapter.spans[0].name == "export_test"


# ─── TC-29~TC-33: OtelSdkAdapter 고급 ───────────────────────

def test_tc29_context_manager_span():
    """TC-29: with adapter.trace() 컨텍스트 매니저"""
    adapter = create_otel_adapter()
    with adapter.trace("ctx_span") as span:
        span.set_attribute("a", 1)
    assert len(adapter.spans) == 1
    assert adapter.spans[0].status == "ok"


def test_tc30_context_manager_error_span():
    """TC-30: 예외 발생 시 status='error'"""
    adapter = create_otel_adapter()
    try:
        with adapter.trace("err_span"):
            raise ValueError("boom")
    except ValueError:
        pass
    assert adapter.spans[0].status == "error"


def test_tc31_inject_extract_roundtrip():
    """TC-31: inject → extract 왕복"""
    adapter = create_otel_adapter("svc-a")
    with adapter.trace("outbound") as span:
        headers: dict = {}
        adapter.inject(span.ctx, headers)
        in_ctx = adapter.extract(headers)
        assert in_ctx is not None
        assert in_ctx.trace_id == span.ctx.trace_id


def test_tc32_span_data_duration():
    """TC-32: SpanData.duration_ms >= 0"""
    adapter = create_otel_adapter()
    with adapter.trace("timed") as span:
        time.sleep(0.001)
    assert adapter.spans[0].duration_ms >= 0


def test_tc33_clear_spans():
    """TC-33: clear_spans() → spans 비워짐"""
    adapter = create_otel_adapter()
    with adapter.trace("s1"):
        pass
    assert len(adapter.spans) == 1
    adapter.clear_spans()
    assert len(adapter.spans) == 0
