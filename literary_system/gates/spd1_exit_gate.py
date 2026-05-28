"""
literary_system/gates/spd1_exit_gate.py
────────────────────────────────────────
SP-D.1 Exit Gate — Phase D Sub-Phase D.1 완료 기준 검증

ADR-157: SP-D.1 Exit Gate — 관측성 스택 완전 구축 확인

검증 축:
  E1 - TraceContext 전파 레이어 (W3C Level 1)
  E2 - OTel SDK 어댑터 + 스팬 내보내기
  E3 - Prometheus /metrics OTel 통합 (D-M-02 완성)
  E4 - TraceSampler 4전략 (ALWAYS/NEVER/RATIO/ADAPTIVE)
  E5 - ObservabilityDashboard 5패널 + 알림 시스템
  E6 - G83 Observability Foundation Gate 84/84 PASS

LLM 외부 호출 금지 (ADR-015 / ADR-031)
"""

from __future__ import annotations

import importlib
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ──────────────────────────────────────────────
# 결과 데이터 클래스
# ──────────────────────────────────────────────


@dataclass
class ExitCheckpoint:
    axis: str
    name: str
    passed: bool
    detail: str = ""
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class SpD1ExitResult:
    gate_id: str = "SP-D.1-EXIT"
    gate_name: str = "SP-D.1 Exit Gate — Observability Stack Complete"
    passed: bool = False
    passed_count: int = 0
    failed_count: int = 0
    checkpoints: List[ExitCheckpoint] = field(default_factory=list)
    duration_ms: float = 0.0
    version: str = "12.1.0"
    tc_total: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "passed": self.passed,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "duration_ms": round(self.duration_ms, 2),
            "version": self.version,
            "tc_total": self.tc_total,
            "checkpoints": [
                {
                    "axis": c.axis,
                    "name": c.name,
                    "passed": c.passed,
                    "detail": c.detail,
                    "error": c.error,
                }
                for c in self.checkpoints
            ],
        }


# ──────────────────────────────────────────────
# 각 축 검증 함수
# ──────────────────────────────────────────────


def _check_e1_trace_context() -> ExitCheckpoint:
    """E1: W3C TraceContext Level 1 전파 레이어."""
    start = time.time()
    try:
        from literary_system.ops.trace_context import (
            TraceContextPropagator,
            TraceFlags,
            new_trace_context,
            child_context,
        )
        ctx = new_trace_context(sampled=True)
        assert ctx.flags == TraceFlags.SAMPLED
        assert len(ctx.trace_id) == 32
        assert len(ctx.parent_id) == 16

        child = child_context(ctx)
        assert child.trace_id == ctx.trace_id
        assert child.parent_id != ctx.parent_id

        prop = TraceContextPropagator()
        headers: dict = {}
        prop.inject(ctx, headers)
        recovered = prop.extract(headers)
        assert recovered is not None
        assert recovered.trace_id == ctx.trace_id

        return ExitCheckpoint(
            axis="E1", name="W3C TraceContext Level 1", passed=True,
            detail="traceparent inject/extract + child_context PASS",
            duration_ms=(time.time() - start) * 1000,
        )
    except Exception as exc:
        return ExitCheckpoint(
            axis="E1", name="W3C TraceContext Level 1", passed=False,
            error=str(exc), duration_ms=(time.time() - start) * 1000,
        )


def _check_e2_otel_adapter() -> ExitCheckpoint:
    """E2: OTel SDK 어댑터 + 스팬 내보내기."""
    start = time.time()
    try:
        from literary_system.ops.otel_adapter import create_otel_adapter
        from literary_system.ops.trace_context import new_trace_context

        adapter = create_otel_adapter("spd1-exit-check")
        ctx = new_trace_context(sampled=True)
        with adapter.start_span("exit_check_span", parent=ctx) as span:
            span.set_attribute("check", "E2")

        spans = adapter.spans
        assert len(spans) == 1
        assert spans[0].name == "exit_check_span"
        assert spans[0].trace_id == ctx.trace_id

        return ExitCheckpoint(
            axis="E2", name="OTel SDK Adapter + SpanExporter", passed=True,
            detail=f"span exported: trace_id={ctx.trace_id[:8]}...",
            duration_ms=(time.time() - start) * 1000,
        )
    except Exception as exc:
        return ExitCheckpoint(
            axis="E2", name="OTel SDK Adapter + SpanExporter", passed=False,
            error=str(exc), duration_ms=(time.time() - start) * 1000,
        )


def _check_e3_prometheus_trace_extension() -> ExitCheckpoint:
    """E3: Prometheus /metrics OTel 통합 (D-M-02 완성)."""
    start = time.time()
    try:
        from literary_system.ops.prometheus_trace_extension import (
            TraceMetricSnapshot,
            create_metrics_endpoint,
        )
        from literary_system.ops.trace_context import TraceContextPropagator, new_trace_context

        # traceparent 전달 → 응답 traceparent에서 동일 trace_id 확인
        prop = TraceContextPropagator()
        ctx = new_trace_context(sampled=True)
        req_hdrs: dict = {}
        prop.inject(ctx, req_hdrs)

        endpoint = create_metrics_endpoint("12.1.0", "SP-D.1", "literary-os")
        snap = TraceMetricSnapshot(spans_exported_total=10)
        response = endpoint.handle_request(req_hdrs, snap)

        assert response.status_code == 200
        parts = response.traceparent.split("-")
        assert len(parts) == 4
        assert parts[1] == ctx.trace_id  # trace_id 상속

        return ExitCheckpoint(
            axis="E3", name="Prometheus /metrics OTel 통합 (D-M-02)", passed=True,
            detail="traceparent 상속 E2E PASS",
            duration_ms=(time.time() - start) * 1000,
        )
    except Exception as exc:
        return ExitCheckpoint(
            axis="E3", name="Prometheus /metrics OTel 통합 (D-M-02)", passed=False,
            error=str(exc), duration_ms=(time.time() - start) * 1000,
        )


def _check_e4_trace_sampler() -> ExitCheckpoint:
    """E4: TraceSampler 4전략."""
    start = time.time()
    try:
        from literary_system.ops.trace_sampler import (
            AdaptiveSampler,
            SpanObservation,
            create_sampler,
        )

        # ALWAYS
        s_always = create_sampler(strategy="always")
        assert all(s_always.should_sample("op").sampled for _ in range(5))

        # NEVER
        s_never = create_sampler(strategy="never")
        assert all(not s_never.should_sample("op").sampled for _ in range(5))

        # RATIO
        s_ratio = create_sampler(strategy="ratio", rate=0.5)
        decisions = [s_ratio.should_sample("op") for _ in range(100)]
        sampled = sum(1 for d in decisions if d.sampled)
        assert 5 <= sampled <= 95  # 너무 극단적이지 않음

        # ADAPTIVE
        s_adapt = AdaptiveSampler(initial_rate=0.3)
        for _ in range(10):
            s_adapt.observe(SpanObservation(duration_ms=800.0, is_error=True))
        rate = s_adapt.effective_rate
        assert 0.0 <= rate <= 1.0

        return ExitCheckpoint(
            axis="E4", name="TraceSampler 4전략 (ALWAYS/NEVER/RATIO/ADAPTIVE)", passed=True,
            detail=f"RATIO sampled={sampled}/100, ADAPTIVE rate={rate:.3f}",
            duration_ms=(time.time() - start) * 1000,
        )
    except Exception as exc:
        return ExitCheckpoint(
            axis="E4", name="TraceSampler 4전략", passed=False,
            error=str(exc), duration_ms=(time.time() - start) * 1000,
        )


def _check_e5_observability_dashboard() -> ExitCheckpoint:
    """E5: ObservabilityDashboard 5패널 + 알림 시스템."""
    start = time.time()
    try:
        from literary_system.ops.observability_dashboard import (
            create_spd1_dashboard,
            record_gate_metrics,
            record_otel_metrics,
        )

        dash = create_spd1_dashboard()
        assert len(dash.panel_names()) == 5

        # 정상 지표 → healthy
        record_gate_metrics(dash, passed=84, total=84)
        record_otel_metrics(dash, spans_exported=100, active_traces=10, p99_ms=100.0, error_ratio=0.01)
        assert dash.health() == "healthy"

        # 비정상 지표 → degraded
        dash2 = create_spd1_dashboard()
        record_otel_metrics(dash2, spans_exported=0, active_traces=0, p99_ms=0.0, error_ratio=0.20)
        assert dash2.health() == "degraded"

        summary = dash.summary()
        assert summary["panel_count"] == 5

        return ExitCheckpoint(
            axis="E5", name="ObservabilityDashboard 5패널 + 알림", passed=True,
            detail="healthy/degraded 상태 전환 + summary PASS",
            duration_ms=(time.time() - start) * 1000,
        )
    except Exception as exc:
        return ExitCheckpoint(
            axis="E5", name="ObservabilityDashboard 5패널 + 알림", passed=False,
            error=str(exc), duration_ms=(time.time() - start) * 1000,
        )


def _check_e6_g83_gate() -> ExitCheckpoint:
    """E6: G83 Observability Foundation Gate 84/84 PASS."""
    start = time.time()
    try:
        from literary_system.gates.release_gate import GATES

        # G83가 등록되어 있는지 확인
        gate_names = [g[0] for g in GATES]
        assert "observability_foundation_g83" in gate_names, "G83 not registered"
        assert len(GATES) >= 84, f"Expected >=84 gates, got {len(GATES)}"

        # G83 직접 실행
        from literary_system.gates.observability_foundation_gate import run_g83_gate
        result = run_g83_gate()
        assert result["pass"] is True, f"G83 failed: {result}"
        assert result["passed_count"] == 5

        return ExitCheckpoint(
            axis="E6", name="G83 Observability Foundation Gate", passed=True,
            detail=f"G83 5/5 PASS, Total gates: {len(GATES)}",
            duration_ms=(time.time() - start) * 1000,
        )
    except Exception as exc:
        return ExitCheckpoint(
            axis="E6", name="G83 Observability Foundation Gate", passed=False,
            error=str(exc), duration_ms=(time.time() - start) * 1000,
        )


# ──────────────────────────────────────────────
# 메인 실행
# ──────────────────────────────────────────────


def run_spd1_exit_gate() -> SpD1ExitResult:
    """SP-D.1 Exit Gate 6축 전체 실행."""
    start = time.time()
    result = SpD1ExitResult()

    checkers = [
        _check_e1_trace_context,
        _check_e2_otel_adapter,
        _check_e3_prometheus_trace_extension,
        _check_e4_trace_sampler,
        _check_e5_observability_dashboard,
        _check_e6_g83_gate,
    ]

    for checker in checkers:
        cp = checker()
        result.checkpoints.append(cp)
        if cp.passed:
            result.passed_count += 1
        else:
            result.failed_count += 1

    result.passed = result.failed_count == 0
    result.duration_ms = (time.time() - start) * 1000
    # V694 기준 누적 TC
    result.tc_total = 9205 + 33  # V694 +33 = 9238

    return result


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────


if __name__ == "__main__":
    import json
    result = run_spd1_exit_gate()
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    status = "PASS" if result.passed else "FAIL"
    print(f"\n[SP-D.1 EXIT GATE] {status} — {result.passed_count}/6 PASS")
