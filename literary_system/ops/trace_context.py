"""
literary_system/ops/trace_context.py
=====================================
V688 — W3C TraceContext Propagator (D-M-02, ADR-151)

W3C Trace Context Level 1 (https://www.w3.org/TR/trace-context/) 준수.

제공 인터페이스:
  TraceContext            — traceparent + tracestate 보관 dataclass
  TraceContextPropagator  — inject / extract (dict 헤더 기반)
  TraceFlags              — sampled 비트 플래그
  new_trace_context()     — 신규 루트 스팬 컨텍스트 생성
  child_context()         — 부모 컨텍스트에서 자식 생성

LLM-0 원칙 완전 준수 (외부 LLM 호출 없음)
ADR-151 참조.
"""
from __future__ import annotations

import os
import re
import secrets
from dataclasses import dataclass, field
from enum import IntFlag
from typing import Dict, Optional


# ── 상수 ────────────────────────────────────────────────────

VERSION = "00"
TRACEPARENT_HEADER = "traceparent"
TRACESTATE_HEADER  = "tracestate"

# traceparent 정규식: 00-<32hex>-<16hex>-<2hex>
_TRACEPARENT_RE = re.compile(
    r"^([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$",
    re.ASCII,
)

# tracestate: 최대 32 리스트 멤버 (W3C spec)
_TRACESTATE_MAX_MEMBERS = 32
_TRACESTATE_MEMBER_RE = re.compile(r"^[a-z][a-z0-9_\-*/]{0,255}=[^\s,=]{1,256}$")


# ── 플래그 ───────────────────────────────────────────────────

class TraceFlags(IntFlag):
    """W3C TraceContext flags 바이트."""
    NONE    = 0x00
    SAMPLED = 0x01   # bit 0


# ── 핵심 데이터 모델 ─────────────────────────────────────────

@dataclass
class TraceContext:
    """W3C Trace Context: traceparent + tracestate."""
    version:    str        = VERSION
    trace_id:   str        = ""          # 32-char hex
    parent_id:  str        = ""          # 16-char hex (이 스팬의 span_id)
    flags:      TraceFlags = TraceFlags.SAMPLED
    tracestate: str        = ""          # 선택적 vendor 상태

    # ── 직렬화 ────────────────────────────────────────────────

    @property
    def traceparent(self) -> str:
        """traceparent 헤더 값 반환."""
        return "{}-{}-{}-{:02x}".format(
            self.version,
            self.trace_id,
            self.parent_id,
            int(self.flags),
        )

    def is_sampled(self) -> bool:
        """샘플링 비트가 설정되어 있으면 True."""
        return bool(self.flags & TraceFlags.SAMPLED)

    def is_valid(self) -> bool:
        """W3C 스펙 기준 유효성 검사."""
        return (
            len(self.trace_id) == 32
            and all(c in "0123456789abcdef" for c in self.trace_id)
            and self.trace_id != "0" * 32
            and len(self.parent_id) == 16
            and all(c in "0123456789abcdef" for c in self.parent_id)
            and self.parent_id != "0" * 16
        )

    def to_dict(self) -> Dict[str, str]:
        """헤더 딕셔너리 반환."""
        d: Dict[str, str] = {TRACEPARENT_HEADER: self.traceparent}
        if self.tracestate:
            d[TRACESTATE_HEADER] = self.tracestate
        return d

    @classmethod
    def from_traceparent(cls, header: str) -> "TraceContext":
        """traceparent 문자열 파싱. 실패 시 ValueError."""
        m = _TRACEPARENT_RE.match(header.strip().lower())
        if not m:
            raise ValueError("Invalid traceparent: {}".format(header))
        version, trace_id, parent_id, flags_hex = m.groups()
        if version == "ff":
            raise ValueError("Reserved version ff")
        flags = TraceFlags(int(flags_hex, 16))
        return cls(
            version=version,
            trace_id=trace_id,
            parent_id=parent_id,
            flags=flags,
        )


# ── 팩토리 함수 ──────────────────────────────────────────────

def new_trace_context(sampled: bool = True) -> TraceContext:
    """새 루트 TraceContext 생성 (cryptographically random IDs)."""
    trace_id  = secrets.token_hex(16)   # 32 hex chars
    parent_id = secrets.token_hex(8)    # 16 hex chars
    flags = TraceFlags.SAMPLED if sampled else TraceFlags.NONE
    return TraceContext(
        trace_id=trace_id,
        parent_id=parent_id,
        flags=flags,
    )


def child_context(parent: TraceContext, sampled: Optional[bool] = None) -> TraceContext:
    """부모 TraceContext에서 자식 스팬 컨텍스트 생성.

    - trace_id 를 부모에서 그대로 상속
    - parent_id 는 새 span_id (자식의 span_id)
    - flags 는 부모 상속 (sampled 인자로 오버라이드 가능)
    - tracestate 는 부모에서 상속
    """
    if not parent.is_valid():
        raise ValueError("Parent TraceContext is invalid: {}".format(parent.traceparent))
    child_span_id = secrets.token_hex(8)
    if sampled is None:
        flags = parent.flags
    else:
        flags = TraceFlags.SAMPLED if sampled else TraceFlags.NONE
    return TraceContext(
        trace_id=parent.trace_id,
        parent_id=child_span_id,
        flags=flags,
        tracestate=parent.tracestate,
    )


# ── 프로파게이터 ─────────────────────────────────────────────

class TraceContextPropagator:
    """W3C TraceContext HTTP 헤더 inject / extract."""

    @staticmethod
    def inject(ctx: TraceContext, headers: Dict[str, str]) -> None:
        """헤더 딕셔너리에 TraceContext를 주입한다 (in-place)."""
        headers[TRACEPARENT_HEADER] = ctx.traceparent
        if ctx.tracestate:
            headers[TRACESTATE_HEADER] = ctx.tracestate

    @staticmethod
    def extract(headers: Dict[str, str]) -> Optional[TraceContext]:
        """헤더 딕셔너리에서 TraceContext를 추출한다.

        파싱 실패 시 None 반환 (오류 전파 방지).
        """
        # 대소문자 무시 헤더 조회
        normalized = {k.lower(): v for k, v in headers.items()}
        raw = normalized.get(TRACEPARENT_HEADER, "")
        if not raw:
            return None
        try:
            ctx = TraceContext.from_traceparent(raw)
        except (ValueError, Exception):
            return None

        # tracestate 파싱 (선택)
        ts = normalized.get(TRACESTATE_HEADER, "")
        if ts:
            members = [m.strip() for m in ts.split(",") if m.strip()]
            # 최대 32 멤버만 허용
            members = members[:_TRACESTATE_MAX_MEMBERS]
            ctx.tracestate = ",".join(members)
        return ctx

    @staticmethod
    def extract_or_create(headers: Dict[str, str]) -> TraceContext:
        """헤더에서 추출, 없으면 새 루트 컨텍스트 생성."""
        ctx = TraceContextPropagator.extract(headers)
        return ctx if ctx is not None else new_trace_context()


# ── 독립 실행 ────────────────────────────────────────────────

if __name__ == "__main__":
    # 데모
    root = new_trace_context()
    print("Root TraceContext:")
    print("  traceparent:", root.traceparent)
    print("  is_sampled:", root.is_sampled())
    print("  is_valid:", root.is_valid())

    child = child_context(root)
    print("\nChild TraceContext:")
    print("  traceparent:", child.traceparent)
    print("  trace_id inherited:", child.trace_id == root.trace_id)

    headers: Dict[str, str] = {}
    TraceContextPropagator.inject(root, headers)
    print("\nInjected headers:", headers)

    extracted = TraceContextPropagator.extract(headers)
    print("Extracted trace_id matches:", extracted and extracted.trace_id == root.trace_id)
