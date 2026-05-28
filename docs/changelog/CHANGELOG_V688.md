# CHANGELOG V688 — OTel SDK + W3C TraceContext (D-M-02)

## Version: 12.x-dev (dev branch: dev/v688-otel-tracecontext)
## Date: 2026-05-28
## Phase: D / SP-D.1 (V681~V695)

---

## 변경 요약

W3C Trace Context Level 1 전파기와 OTel SDK Adapter를 도입하여 literary-os의 분산 트레이싱 기반을 구축한다.

---

## 신규 파일

### `literary_system/ops/trace_context.py`
- `TraceFlags(IntFlag)` — NONE=0x00, SAMPLED=0x01
- `TraceContext(dataclass)` — traceparent 포맷 생성/파싱
- `TraceContextPropagator` — inject/extract/extract_or_create
- `new_trace_context()` — 신규 루트 TraceContext 생성
- `child_context()` — 부모 trace_id 상속, 새 span_id 생성

### `literary_system/ops/otel_adapter.py`
- `SpanData(dataclass)` — 완료된 Span 데이터 (duration_ms 포함)
- `TraceSpan` — set_attribute / add_event / set_status / context manager
- `SpanExporter` — in-memory Span 누적 및 조회
- `OtelSdkAdapter` — start_span / trace(ctx mgr) / inject / extract
- `create_otel_adapter()` — 팩토리 함수

### `tests/unit/test_v688_otel_tracecontext.py`
- 33 TC (TC-01~TC-33) ALL PASS
- TC-01~06: TraceContext 기본 (hex 길이, traceparent 포맷, flags)
- TC-07~11: child_context 계층 (trace_id 상속, 새 span_id)
- TC-12~17: Propagator inject/extract (헤더 왕복, 누락 처리)
- TC-18~22: 직렬화/역직렬화 (to_dict, from_traceparent, 대소문자)
- TC-23~28: OtelSdkAdapter 기본 (생성, span, export)
- TC-29~33: Advanced (context manager, error span, inject-extract, duration, clear)

### `docs/adr/ADR-151.md`
- D-M-02 W3C TraceContext Level 1 채택 결정 기록

---

## ADR
- **ADR-151**: W3C TraceContext Level 1 Propagator 도입 (D-M-02)

---

## 테스트 결과
- 신규 TC: 33개
- 누적 TC: 8,878+ (V687 기준 8,845 + 33)
- Gates: 83/83 PASS (기존 유지)
