"""
literary_system/ops/observability_stack.py
V477 — ObservabilityStack (OTel 트레이스/메트릭/로그 + Prometheus export)

인터페이스:
  trace(span_name, fn) → Any         (컨텍스트 매니저/래퍼)
  record_metric(name, val, labels)   → None
  log(level, msg, **kw)              → None
  export_prometheus() → str           (Prometheus text format)
  run_load_test(vus, duration_s) → LoadTestReport

LLM-0 준수: export_fn / sink_fn 주입 가능, 순수 인메모리 mock
"""
from __future__ import annotations

import time
import uuid
import statistics
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Generator, List, Optional


# ── 열거형 ───────────────────────────────────────────────────

class LogLevel(str, Enum):
    DEBUG   = "DEBUG"
    INFO    = "INFO"
    WARNING = "WARNING"
    ERROR   = "ERROR"


# ── 데이터 모델 ──────────────────────────────────────────────

@dataclass
class Span:
    trace_id:  str
    span_id:   str
    name:      str
    start_ns:  int
    end_ns:    int    = 0
    status:    str    = "ok"
    attributes: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        return (self.end_ns - self.start_ns) / 1_000_000


@dataclass
class Metric:
    name:      str
    value:     float
    labels:    Dict[str, str] = field(default_factory=dict)
    timestamp: float          = field(default_factory=time.time)


@dataclass
class LogEntry:
    level:     str
    message:   str
    timestamp: float = field(default_factory=time.time)
    extra:     Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadTestReport:
    vus:              int
    duration_s:       float
    total_requests:   int
    success_count:    int
    error_count:      int
    p50_ms:           float
    p95_ms:           float
    p99_ms:           float
    rps:              float
    sla_pass:         bool   = False

    @classmethod
    def from_latencies(
        cls,
        vus: int,
        duration_s: float,
        latencies_ms: List[float],
        errors: int = 0,
    ) -> "LoadTestReport":
        total = len(latencies_ms) + errors
        sorted_lat = sorted(latencies_ms)
        n = len(sorted_lat)
        # Bug-Fix: min(idx, n-1) boundary protection for small sample sizes
        p50 = sorted_lat[min(int(n * 0.50), n - 1)] if n else 0.0
        p95 = sorted_lat[min(int(n * 0.95), n - 1)] if n else 0.0
        p99 = sorted_lat[min(int(n * 0.99), n - 1)] if n else 0.0
        rps = total / duration_s if duration_s > 0 else 0.0
        return cls(
            vus=vus,
            duration_s=duration_s,
            total_requests=total,
            success_count=len(latencies_ms),
            error_count=errors,
            p50_ms=round(p50, 2),
            p95_ms=round(p95, 2),
            p99_ms=round(p99, 2),
            rps=round(rps, 2),
            sla_pass=(p95 < 3000.0),  # SLO: p95 < 3s (ADR-015)
        )


# ── ObservabilityStack ────────────────────────────────────────

class ObservabilityStack:
    """
    OTel 트레이스 / 메트릭 / 로그 통합 스택.

    export_fn: (spans) → None   (기본: 인메모리 누적)
    sink_fn:   (logs) → None    (기본: 인메모리 누적)
    """

    def __init__(
        self,
        service_name: str = "literary-os",
        export_fn: Optional[Callable[[List[Span]], None]] = None,
        sink_fn:   Optional[Callable[[List[LogEntry]], None]] = None,
    ) -> None:
        self.service_name = service_name
        self._export_fn   = export_fn or (lambda spans: None)
        self._sink_fn     = sink_fn   or (lambda logs: None)

        self._spans:   List[Span]     = []
        self._metrics: List[Metric]   = []
        self._logs:    List[LogEntry] = []

    # ── 트레이스 ─────────────────────────────────────────────

    @contextmanager
    def trace(
        self,
        span_name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Generator[Span, None, None]:
        """컨텍스트 매니저 방식 스팬."""
        trace_id = uuid.uuid4().hex
        span_id  = uuid.uuid4().hex[:16]
        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            name=span_name,
            start_ns=time.time_ns(),
            attributes=attributes or {},
        )
        try:
            yield span
            span.status = "ok"
        except Exception as exc:
            span.status = f"error:{type(exc).__name__}"
            raise
        finally:
            span.end_ns = time.time_ns()
            self._spans.append(span)
            self._export_fn([span])

    def trace_fn(self, span_name: str, fn: Callable[[], Any], **attrs) -> Any:
        """함수 래핑 방식 스팬."""
        trace_id = uuid.uuid4().hex
        span_id  = uuid.uuid4().hex[:16]
        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            name=span_name,
            start_ns=time.time_ns(),
            attributes=attrs,
        )
        try:
            result = fn()
            span.status = "ok"
            return result
        except Exception as exc:
            span.status = f"error:{type(exc).__name__}"
            raise
        finally:
            span.end_ns = time.time_ns()
            self._spans.append(span)
            self._export_fn([span])

    # ── 메트릭 ──────────────────────────────────────────────

    def record_metric(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        m = Metric(name=name, value=value, labels=labels or {})
        self._metrics.append(m)

    # ── 로그 ────────────────────────────────────────────────

    def log(self, level: str, message: str, **extra) -> None:
        entry = LogEntry(level=level.upper(), message=message, extra=extra)
        self._logs.append(entry)
        self._sink_fn([entry])

    def info(self, msg: str, **kw)  -> None: self.log("INFO",    msg, **kw)
    def warn(self, msg: str, **kw)  -> None: self.log("WARNING", msg, **kw)
    def error(self, msg: str, **kw) -> None: self.log("ERROR",   msg, **kw)
    def debug(self, msg: str, **kw) -> None: self.log("DEBUG",   msg, **kw)

    # ── Prometheus export ─────────────────────────────────────

    def export_prometheus(self) -> str:
        """메트릭을 Prometheus text format으로 직렬화."""
        lines: List[str] = []
        # 메트릭 집계
        agg: Dict[str, Dict[str, List[float]]] = {}
        for m in self._metrics:
            key = m.name
            label_str = ",".join(f'{k}="{v}"' for k, v in sorted(m.labels.items()))
            agg.setdefault(key, {}).setdefault(label_str, []).append(m.value)

        for metric_name, label_groups in sorted(agg.items()):
            lines.append(f"# HELP {metric_name} literary-os metric")
            lines.append(f"# TYPE {metric_name} gauge")
            for label_str, vals in label_groups.items():
                avg = sum(vals) / len(vals)
                if label_str:
                    lines.append(f'{metric_name}{{{label_str}}} {avg:.6f}')
                else:
                    lines.append(f'{metric_name} {avg:.6f}')

        return "\n".join(lines) + ("\n" if lines else "")

    # ── 로드 테스트 시뮬레이션 ───────────────────────────────

    def run_load_test(
        self,
        vus: int = 100,
        duration_s: float = 60.0,
        target_fn: Optional[Callable[[], float]] = None,
        error_rate: float = 0.02,
    ) -> LoadTestReport:
        """
        가상 로드 테스트 시뮬레이션.

        target_fn: () → latency_ms  (기본: 정규분포 mock)
        error_rate: 오류 비율 (기본 2%)
        목표: p95 < 3000ms (SLO ADR-015)
        """
        import random

        rng = random.Random(42)  # 결정론적 시드 — target_fn·error_rate 모두 동일 rng 사용

        if target_fn is None:
            # 기본 mock: 평균 200ms, σ=80ms — seeded rng 사용으로 결정론적 보장
            def target_fn() -> float:  # type: ignore[misc]
                return max(50.0, rng.gauss(200.0, 80.0))

        total_requests = int(vus * duration_s / 0.5)  # VU당 0.5s 간격 가정
        latencies: List[float] = []
        errors = 0
        for _ in range(total_requests):
            if rng.random() < error_rate:
                errors += 1
            else:
                lat = target_fn()
                latencies.append(float(lat))

        report = LoadTestReport.from_latencies(
            vus=vus,
            duration_s=duration_s,
            latencies_ms=latencies,
            errors=errors,
        )
        # 결과 기록
        self.record_metric("load_test_p95_ms", report.p95_ms,
                           {"vus": str(vus)})
        self.record_metric("load_test_rps",    report.rps,
                           {"vus": str(vus)})
        return report

    # ── 집계 ────────────────────────────────────────────────

    def span_count(self) -> int:
        return len(self._spans)

    def metric_count(self) -> int:
        return len(self._metrics)

    def log_count(self) -> int:
        return len(self._logs)

    def recent_spans(self, n: int = 10) -> List[Span]:
        return self._spans[-n:]