"""
Enterprise Benchmark Layer (V676, SP-C.4 안정화 2)
SLO·Revenue 레이어 성능 측정 + BenchmarkGate

ADR-138
"""
from __future__ import annotations

import time
import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


# ---------------------------------------------------------------------------
# NIST R-7 Percentile (D-M-09, ADR-143)
# ---------------------------------------------------------------------------
def percentile(data: List[float], p: float) -> float:
    """NIST recommended linear interpolation (R-7).

    p: 0.0 ~ 1.0 (예: 0.99 = P99)
    sorted[int(n*0.99)] 대비 정확: n=50/100 엣지에서 최댓값 편향 제거.
    
    엣지 케이스:
      - n=0 → 0.0
      - n=1 → data[0]
      - 음수값, 동일값 배열 → 정상 처리
    """
    if not data:
        return 0.0
    if len(data) == 1:
        return float(data[0])
    sorted_data = sorted(data)
    n = len(sorted_data)
    rank = p * (n - 1)
    lo = int(rank)
    hi = min(lo + 1, n - 1)
    frac = rank - lo
    return float(sorted_data[lo] + frac * (sorted_data[hi] - sorted_data[lo]))



# ── Enums ─────────────────────────────────────────────────────────────────────

class BenchmarkStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


class BenchmarkTarget(str, Enum):
    SLO_MONITOR = "slo_monitor"
    REVENUE_CALCULATOR = "revenue_calculator"
    FULL_PIPELINE = "full_pipeline"


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class BenchmarkThreshold:
    """성능 임계값 설정."""
    target: BenchmarkTarget
    max_avg_ms: float          # 평균 응답 임계값 (ms)
    max_p99_ms: float          # P99 임계값 (ms)
    min_throughput_rps: float  # 최소 처리량 (req/s)


@dataclass
class BenchmarkSample:
    """단일 벤치마크 샘플."""
    target: BenchmarkTarget
    elapsed_ms: float
    success: bool = True
    error: Optional[str] = None


@dataclass
class BenchmarkReport:
    """벤치마크 측정 결과 보고서."""
    target: BenchmarkTarget
    sample_count: int
    avg_ms: float
    p50_ms: float
    p99_ms: float
    throughput_rps: float
    success_rate: float
    status: BenchmarkStatus
    threshold: BenchmarkThreshold
    violations: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status == BenchmarkStatus.PASS


@dataclass
class EnterpriseBenchmarkSuite:
    """전체 Enterprise 벤치마크 스위트 결과."""
    reports: List[BenchmarkReport] = field(default_factory=list)
    suite_status: BenchmarkStatus = BenchmarkStatus.PASS

    @property
    def all_passed(self) -> bool:
        return all(r.passed for r in self.reports)

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.reports if r.passed)

    @property
    def total_count(self) -> int:
        return len(self.reports)


# ── BenchmarkRunner ────────────────────────────────────────────────────────────

class BenchmarkRunner:
    """성능 샘플 수집 및 통계 계산."""

    DEFAULT_THRESHOLDS: List[BenchmarkThreshold] = [
        BenchmarkThreshold(
            target=BenchmarkTarget.SLO_MONITOR,
            max_avg_ms=50.0,
            max_p99_ms=200.0,
            min_throughput_rps=20.0,
        ),
        BenchmarkThreshold(
            target=BenchmarkTarget.REVENUE_CALCULATOR,
            max_avg_ms=30.0,
            max_p99_ms=120.0,
            min_throughput_rps=30.0,
        ),
        BenchmarkThreshold(
            target=BenchmarkTarget.FULL_PIPELINE,
            max_avg_ms=100.0,
            max_p99_ms=400.0,
            min_throughput_rps=10.0,
        ),
    ]

    def __init__(self, thresholds: Optional[List[BenchmarkThreshold]] = None):
        self.thresholds = {t.target: t for t in (thresholds or self.DEFAULT_THRESHOLDS)}

    def run(
        self,
        target: BenchmarkTarget,
        samples: List[BenchmarkSample],
    ) -> BenchmarkReport:
        """샘플 목록으로부터 BenchmarkReport 생성."""
        threshold = self.thresholds[target]

        elapsed_list = [s.elapsed_ms for s in samples]
        success_count = sum(1 for s in samples if s.success)

        avg_ms = statistics.mean(elapsed_list) if elapsed_list else 0.0
        p50_ms = statistics.median(elapsed_list) if elapsed_list else 0.0
        p99_ms = percentile(elapsed_list, 0.99) if len(elapsed_list) >= 2 else avg_ms
        success_rate = success_count / len(samples) if samples else 0.0
        # 처리량: 샘플 총 시간(ms → s) 대비 성공 수
        total_ms = sum(elapsed_list)
        throughput_rps = (success_count / (total_ms / 1000.0)) if total_ms > 0 else 0.0

        violations: List[str] = []
        if avg_ms > threshold.max_avg_ms:
            violations.append(
                f"avg_ms={avg_ms:.1f} > threshold={threshold.max_avg_ms}"
            )
        if p99_ms > threshold.max_p99_ms:
            violations.append(
                f"p99_ms={p99_ms:.1f} > threshold={threshold.max_p99_ms}"
            )
        if throughput_rps < threshold.min_throughput_rps:
            violations.append(
                f"throughput={throughput_rps:.1f} rps < threshold={threshold.min_throughput_rps}"
            )

        if violations:
            status = BenchmarkStatus.FAIL
        elif avg_ms > threshold.max_avg_ms * 0.8:
            status = BenchmarkStatus.WARN
        else:
            status = BenchmarkStatus.PASS

        return BenchmarkReport(
            target=target,
            sample_count=len(samples),
            avg_ms=avg_ms,
            p50_ms=p50_ms,
            p99_ms=p99_ms,
            throughput_rps=throughput_rps,
            success_rate=success_rate,
            status=status,
            threshold=threshold,
            violations=violations,
        )

    def time_call(self, target: BenchmarkTarget, fn, *args, **kwargs) -> BenchmarkSample:
        """단일 함수 호출 시간 측정."""
        start = time.perf_counter()
        try:
            fn(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000.0
            return BenchmarkSample(target=target, elapsed_ms=elapsed, success=True)
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000.0
            return BenchmarkSample(
                target=target, elapsed_ms=elapsed, success=False, error=str(exc)
            )


# ── BenchmarkGate ──────────────────────────────────────────────────────────────

class BenchmarkGate:
    """Enterprise 성능 벤치마크 게이트 (G75 전용)."""

    GATE_ID = "G75-BM"

    def __init__(self, runner: Optional[BenchmarkRunner] = None):
        self.runner = runner or BenchmarkRunner()

    def demo_run(self) -> EnterpriseBenchmarkSuite:
        """
        데모 시나리오 실행:
        - SLO_MONITOR: 50 샘플, 2~10 ms
        - REVENUE_CALCULATOR: 50 샘플, 1~8 ms
        - FULL_PIPELINE: 30 샘플, 5~25 ms
        """
        import random
        rng = random.Random(42)

        suite = EnterpriseBenchmarkSuite()

        # SLO_MONITOR
        slo_samples = [
            BenchmarkSample(
                target=BenchmarkTarget.SLO_MONITOR,
                elapsed_ms=rng.uniform(2.0, 10.0),
                success=True,
            )
            for _ in range(50)
        ]
        suite.reports.append(
            self.runner.run(BenchmarkTarget.SLO_MONITOR, slo_samples)
        )

        # REVENUE_CALCULATOR
        rev_samples = [
            BenchmarkSample(
                target=BenchmarkTarget.REVENUE_CALCULATOR,
                elapsed_ms=rng.uniform(1.0, 8.0),
                success=True,
            )
            for _ in range(50)
        ]
        suite.reports.append(
            self.runner.run(BenchmarkTarget.REVENUE_CALCULATOR, rev_samples)
        )

        # FULL_PIPELINE
        pipe_samples = [
            BenchmarkSample(
                target=BenchmarkTarget.FULL_PIPELINE,
                elapsed_ms=rng.uniform(5.0, 25.0),
                success=True,
            )
            for _ in range(30)
        ]
        suite.reports.append(
            self.runner.run(BenchmarkTarget.FULL_PIPELINE, pipe_samples)
        )

        suite.suite_status = (
            BenchmarkStatus.PASS if suite.all_passed else BenchmarkStatus.FAIL
        )
        return suite
