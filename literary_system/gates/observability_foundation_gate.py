"""literary_system/gates/observability_foundation_gate.py

V690: G83 Observability Foundation Gate — SP-D.1 관측가능성 기반 검증.

5축 체크포인트:
  OB-1: trace_context.py — W3C TraceContext Level 1 모듈 존재 및 API 완전성
  OB-2: otel_adapter.py — OTel SDK Adapter 모듈 존재 및 인터페이스
  OB-3: prometheus_exporter.py — Prometheus 익스포터 및 MetricSnapshot
  OB-4: prometheus_trace_extension.py — TraceAwareExporter + MetricsEndpoint
  OB-5: D-M-02 통합 검증 — inject→extract 왕복 + /metrics traceparent 전파

합격 기준: OB-1~OB-5 전체 PASS

설계 원칙:
  LLM-0: 외부 LLM 호출 없음.
  G32: print() 사용 금지 — logger 전용.
"""

from __future__ import annotations

import importlib
import inspect
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[2]
if _REPO_ROOT not in sys.path:  # pragma: no cover
    sys.path.insert(0, str(_REPO_ROOT))

GATE_ID = "G83"
GATE_NAME = "Observability Foundation Gate"


# ─────────────────────────────────────────────────────────────────────────────
# Checkpoint Dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ObsCheckpoint:
    """관측가능성 Gate 체크포인트."""
    axis: str                    # OB-1 ~ OB-5
    name: str
    passed: bool = False
    detail: str = ""
    errors: List[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# 체크포인트 구현
# ─────────────────────────────────────────────────────────────────────────────

def _check_ob1_trace_context() -> ObsCheckpoint:
    """OB-1: trace_context.py — W3C TraceContext Level 1 API 완전성."""
    cp = ObsCheckpoint(axis="OB-1", name="trace_context.py W3C API")
    try:
        mod = importlib.import_module("literary_system.ops.trace_context")

        required_classes = ["TraceFlags", "TraceContext", "TraceContextPropagator"]
        required_funcs = ["new_trace_context", "child_context"]

        missing: List[str] = []
        for cls_name in required_classes:
            if not hasattr(mod, cls_name):
                missing.append(cls_name)
        for fn_name in required_funcs:
            if not hasattr(mod, fn_name):
                missing.append(fn_name)

        if missing:
            cp.errors.append(f"누락 심볼: {missing}")
            return cp

        # TraceContext API 검증
        tc_cls = getattr(mod, "TraceContext")
        required_methods = ["from_traceparent", "to_dict", "is_valid", "is_sampled"]
        for m in required_methods:
            if not hasattr(tc_cls, m):
                missing.append(f"TraceContext.{m}")

        # Propagator API 검증
        prop = getattr(mod, "TraceContextPropagator")
        for m in ["inject", "extract", "extract_or_create"]:
            if not hasattr(prop, m):
                missing.append(f"TraceContextPropagator.{m}")

        if missing:
            cp.errors.append(f"누락 메서드: {missing}")
            return cp

        # 실제 동작 검증: new_trace_context()
        ctx = mod.new_trace_context()
        assert ctx.is_valid(), "new_trace_context() returned invalid context"
        assert len(ctx.trace_id) == 32, "trace_id must be 32 hex chars"
        assert len(ctx.parent_id) == 16, "parent_id must be 16 hex chars"

        cp.passed = True
        cp.detail = f"TraceContext API 완전 — trace_id={ctx.trace_id[:8]}..."
    except Exception as exc:
        cp.errors.append(str(exc))
    return cp


def _check_ob2_otel_adapter() -> ObsCheckpoint:
    """OB-2: otel_adapter.py — OTel SDK Adapter 인터페이스."""
    cp = ObsCheckpoint(axis="OB-2", name="otel_adapter.py OTel SDK")
    try:
        mod = importlib.import_module("literary_system.ops.otel_adapter")

        required = ["SpanData", "TraceSpan", "SpanExporter", "OtelSdkAdapter", "create_otel_adapter"]
        missing = [s for s in required if not hasattr(mod, s)]
        if missing:
            cp.errors.append(f"누락 심볼: {missing}")
            return cp

        # 실제 동작: span 생성 → export
        adapter = mod.create_otel_adapter("test-service")
        with adapter.trace("test_span") as span:
            span.set_attribute("k", "v")
        exported = adapter.exporter.spans
        assert len(exported) >= 1, "span이 export되지 않음"
        assert exported[-1].name == "test_span"

        cp.passed = True
        cp.detail = f"OtelSdkAdapter 동작 확인 — {len(exported)} span(s) exported"
    except Exception as exc:
        cp.errors.append(str(exc))
    return cp


def _check_ob3_prometheus_exporter() -> ObsCheckpoint:
    """OB-3: prometheus_exporter.py — Prometheus 익스포터 기본 동작."""
    cp = ObsCheckpoint(axis="OB-3", name="prometheus_exporter.py 기본 동작")
    try:
        mod = importlib.import_module("literary_system.ops.prometheus_exporter")

        required = ["PrometheusExporter", "MetricSnapshot", "MonitoringConfig"]
        missing = [s for s in required if not hasattr(mod, s)]
        if missing:
            cp.errors.append(f"누락 심볼: {missing}")
            return cp

        # 실제 동작: render() 호출
        exp = mod.PrometheusExporter()
        snap = mod.MetricSnapshot(gates_total=83, gates_passed=83, tests_total=8911)
        text = exp.render(snap)

        assert "literary_os_gates_total" in text
        assert "literary_os_tests_total" in text
        assert "83" in text

        cp.passed = True
        cp.detail = f"PrometheusExporter.render() — {len(text.splitlines())} lines"
    except Exception as exc:
        cp.errors.append(str(exc))
    return cp


def _check_ob4_prometheus_trace_extension() -> ObsCheckpoint:
    """OB-4: prometheus_trace_extension.py — TraceAwareExporter + MetricsEndpoint."""
    cp = ObsCheckpoint(axis="OB-4", name="prometheus_trace_extension.py")
    try:
        mod = importlib.import_module(
            "literary_system.ops.prometheus_trace_extension"
        )

        required = [
            "TraceMetricSnapshot", "TraceAwareExporter",
            "MetricsEndpoint", "MetricsResponse", "create_metrics_endpoint",
        ]
        missing = [s for s in required if not hasattr(mod, s)]
        if missing:
            cp.errors.append(f"누락 심볼: {missing}")
            return cp

        # TraceMetricSnapshot — 4종 trace 필드
        snap_cls = mod.TraceMetricSnapshot
        for attr in ["spans_exported_total", "active_traces",
                     "trace_errors_total", "p99_span_duration_ms"]:
            if not hasattr(snap_cls, attr) and attr not in snap_cls.__dataclass_fields__:
                cp.errors.append(f"TraceMetricSnapshot.{attr} 누락")
                return cp

        # TraceAwareExporter — render_trace()
        exp = mod.TraceAwareExporter()
        snap = mod.TraceMetricSnapshot(
            gates_total=83, gates_passed=83, tests_total=8911,
            spans_exported_total=100, active_traces=2,
        )
        text = exp.render_trace(snap)
        assert "literary_os_spans_exported_total" in text
        assert "literary_os_active_traces" in text

        # MetricsEndpoint — handle_request()
        ep = mod.create_metrics_endpoint()
        resp = ep.handle_request(snapshot=snap)
        assert resp.status_code == 200
        assert "traceparent" in resp.response_headers

        cp.passed = True
        cp.detail = (
            f"TraceAwareExporter + MetricsEndpoint 동작 확인 "
            f"— traceparent={resp.traceparent[:16]}..."
        )
    except Exception as exc:
        cp.errors.append(str(exc))
    return cp


def _check_ob5_dm02_integration() -> ObsCheckpoint:
    """OB-5: D-M-02 통합 검증 — inject→extract 왕복 + /metrics traceparent 전파."""
    cp = ObsCheckpoint(axis="OB-5", name="D-M-02 통합: inject→extract + /metrics 전파")
    try:
        tc_mod = importlib.import_module("literary_system.ops.trace_context")
        pe_mod = importlib.import_module(
            "literary_system.ops.prometheus_trace_extension"
        )

        # ① 루트 컨텍스트 생성
        root = tc_mod.new_trace_context(sampled=True)
        assert root.is_valid()

        # ② inject → extract 왕복
        headers: Dict[str, str] = {}
        tc_mod.TraceContextPropagator.inject(root, headers)
        assert "traceparent" in headers

        extracted = tc_mod.TraceContextPropagator.extract(headers)
        assert extracted is not None
        assert extracted.trace_id == root.trace_id
        assert extracted.parent_id == root.parent_id

        # ③ /metrics 엔드포인트 traceparent 전파
        ep = pe_mod.create_metrics_endpoint()
        snap = pe_mod.TraceMetricSnapshot(
            gates_total=83, gates_passed=83, tests_total=8911,
            spans_exported_total=66,
        )
        resp = ep.handle_request(request_headers=dict(headers), snapshot=snap)

        assert resp.is_ok
        assert resp.traceparent is not None

        # child span은 동일 trace_id 상속
        resp_ctx = tc_mod.TraceContext.from_traceparent(resp.traceparent)
        assert resp_ctx.trace_id == root.trace_id, (
            f"trace_id 불일치: {resp_ctx.trace_id} != {root.trace_id}"
        )

        # span_id는 새로운 값 (child span)
        assert resp_ctx.parent_id != root.parent_id, "child span_id must differ"

        cp.passed = True
        cp.detail = (
            f"D-M-02 완전 이행 — "
            f"trace_id={root.trace_id[:8]}... "
            f"child_span={resp_ctx.parent_id[:8]}..."
        )
    except Exception as exc:
        cp.errors.append(str(exc))
    return cp


# ─────────────────────────────────────────────────────────────────────────────
# 메인 Gate 실행 함수
# ─────────────────────────────────────────────────────────────────────────────

def run_g83_gate() -> Dict[str, Any]:
    """G83 Observability Foundation Gate 실행.

    Returns:
        dict with keys: gate_id, gate_name, pass, passed_count, failed_count, checkpoints
    """
    checkers = [
        _check_ob1_trace_context,
        _check_ob2_otel_adapter,
        _check_ob3_prometheus_exporter,
        _check_ob4_prometheus_trace_extension,
        _check_ob5_dm02_integration,
    ]

    results: List[ObsCheckpoint] = []
    for checker in checkers:
        cp = checker()
        results.append(cp)
        if cp.passed:
            logger.info("[G83] %s %s — PASS: %s", cp.axis, cp.name, cp.detail)
        else:
            logger.error("[G83] %s %s — FAIL: %s", cp.axis, cp.name, cp.errors)

    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count
    all_pass = failed_count == 0

    return {
        "gate_id": GATE_ID,
        "gate_name": GATE_NAME,
        "pass": all_pass,
        "passed": all_pass,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "total_count": len(results),
        "checkpoints": [
            {
                "axis": r.axis,
                "name": r.name,
                "passed": r.passed,
                "detail": r.detail,
                "errors": r.errors,
            }
            for r in results
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 독립 실행
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    result = run_g83_gate()
    sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    sys.exit(0 if result["pass"] else 1)
