# CHANGELOG V690 — G83 Observability Foundation Gate

## Version: 12.x-dev (dev branch: dev/v690-g83-observability-gate)
## Date: 2026-05-28
## Phase: D / SP-D.1 (V681~V695)

---

## 변경 요약

SP-D.1 관측가능성 기반 전체를 검증하는 G83 Observability Foundation Gate를 신설한다.
5축 체크포인트(OB-1~OB-5)로 V688~V689 산출물의 API 완전성과 D-M-02 통합을 자동 검증한다.

---

## 신규 파일

### `literary_system/gates/observability_foundation_gate.py` (329줄)
- OB-1: trace_context.py W3C API 완전성
- OB-2: otel_adapter.py span export 동작
- OB-3: prometheus_exporter.py render() 동작
- OB-4: prometheus_trace_extension.py TraceAwareExporter + MetricsEndpoint
- OB-5: D-M-02 통합 검증 (inject→extract 왕복 + /metrics traceparent 전파)

### `tests/gates/test_v690_observability_foundation_gate.py` (33 TC, ALL PASS)

### `docs/adr/ADR-153.md`

---

## 수정 파일

### `literary_system/gates/release_gate.py`
- G83 Observability Foundation Gate 등록
- 총 Gates: 83 → 84

---

## 테스트 결과
- 신규 TC: 33개
- 누적 TC: 8,944+ (V689 기준 8,911 + 33)
- Gates: **84/84 PASS** (G83 신규 포함)
