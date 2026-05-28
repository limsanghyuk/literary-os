"""
tests/unit/test_v681_benchmark_p99.py
======================================
V681: TD-1 P99 Percentile 정정 테스트 (D-M-09, ADR-143)

NIST R-7 선형 보간법 검증 + BenchmarkRunner 통합 확인
TC-01 ~ TC-20
"""
from __future__ import annotations

import pytest
from literary_system.enterprise.benchmark import percentile, BenchmarkRunner, BenchmarkTarget, BenchmarkSample


# ---------------------------------------------------------------------------
# TC-01 ~ TC-08: percentile() 단위 테스트
# ---------------------------------------------------------------------------

class TestPercentileFunction:
    """percentile() NIST R-7 구현 검증."""

    def test_empty_returns_zero(self):
        """TC-01: n=0 → 0.0."""
        assert percentile([], 0.99) == 0.0

    def test_single_element(self):
        """TC-02: n=1 → data[0]."""
        assert percentile([42.0], 0.99) == 42.0

    def test_two_elements_p99(self):
        """TC-03: n=2, P99 선형보간 → 1.0 근처."""
        v = percentile([1.0, 2.0], 0.99)
        assert 1.9 <= v <= 2.0

    def test_n100_p99_correct(self):
        """TC-04: n=100, P99 = 99.01 (구버전은 100.0 반환)."""
        data = list(range(1, 101))
        v = percentile(data, 0.99)
        assert abs(v - 99.01) < 0.001

    def test_n50_p99_not_max(self):
        """TC-05: n=50, P99 ≠ 최댓값 50."""
        data = list(range(1, 51))
        v = percentile(data, 0.99)
        assert v < 50.0  # 구버전은 50.0 반환

    def test_p50_is_median(self):
        """TC-06: P50 = 중간값."""
        v = percentile([1.0, 2.0, 3.0, 4.0, 5.0], 0.5)
        assert abs(v - 3.0) < 0.001

    def test_negative_values(self):
        """TC-07: 음수값 배열 처리."""
        data = [-5.0, -3.0, -1.0, 0.0, 2.0]
        v = percentile(data, 0.99)
        assert v >= data[0]

    def test_identical_values(self):
        """TC-08: 동일값 배열 → 해당 값 반환."""
        v = percentile([7.0] * 10, 0.99)
        assert abs(v - 7.0) < 0.001


# ---------------------------------------------------------------------------
# TC-09 ~ TC-12: 구버전 대비 정확도
# ---------------------------------------------------------------------------

class TestPercentileVsOldMethod:
    """구버전(sorted[int(n*0.99)]) 대비 정확도 비교."""

    def test_n50_differs_from_old(self):
        """TC-09: n=50일 때 구버전과 다른 결과."""
        data = list(range(1, 51))
        v_new = percentile(data, 0.99)
        v_old = float(sorted(data)[int(len(data) * 0.99)])
        assert abs(v_new - v_old) > 0.0  # 다른 값

    def test_n100_differs_from_old(self):
        """TC-10: n=100일 때 구버전과 다른 결과."""
        data = list(range(1, 101))
        v_new = percentile(data, 0.99)
        v_old = float(sorted(data)[int(len(data) * 0.99)])
        assert abs(v_new - v_old) > 0.0

    def test_new_less_than_old_n50(self):
        """TC-11: n=50 신버전 < 구버전 (최댓값 편향 제거)."""
        data = list(range(1, 51))
        assert percentile(data, 0.99) < float(sorted(data)[int(len(data) * 0.99)])

    def test_p99_within_range(self):
        """TC-12: P99는 반드시 min~max 범위 내."""
        import random
        random.seed(42)
        data = [random.uniform(0, 1000) for _ in range(200)]
        v = percentile(data, 0.99)
        assert min(data) <= v <= max(data)


# ---------------------------------------------------------------------------
# TC-13 ~ TC-16: BenchmarkRunner 통합 — percentile 함수 사용 확인
# ---------------------------------------------------------------------------

class TestBenchmarkRunnerUsesPercentile:
    """BenchmarkRunner._compile_report()가 percentile()를 사용하는지 검증."""

    def _make_samples(self, values: list) -> list:
        return [BenchmarkSample(target=BenchmarkTarget.SLO_MONITOR, elapsed_ms=v, success=True) for v in values]

    def test_report_p99_uses_percentile_n50(self):
        """TC-13: n=50 리포트 P99 ≠ 최댓값."""
        runner = BenchmarkRunner()
        samples = self._make_samples(list(range(1, 51)))
        report = runner.run(BenchmarkTarget.GENERATE, samples)
        assert report.p99_ms < 50.0  # 구버전이면 50.0 반환

    def test_report_p99_n2_valid(self):
        """TC-14: n=2 리포트 P99 = 선형보간값."""
        runner = BenchmarkRunner()
        samples = self._make_samples([10.0, 20.0])
        report = runner.run(BenchmarkTarget.GENERATE, samples)
        assert 10.0 <= report.p99_ms <= 20.0

    def test_report_p99_single_sample_equals_avg(self):
        """TC-15: n=1 → p99_ms = avg_ms."""
        runner = BenchmarkRunner()
        samples = self._make_samples([99.0])
        report = runner.run(BenchmarkTarget.GENERATE, samples)
        assert report.p99_ms == report.avg_ms

    def test_report_structure_intact(self):
        """TC-16: 보고서 구조 유지 (avg, p50, p99, violations 포함)."""
        runner = BenchmarkRunner()
        samples = self._make_samples([50.0] * 20)
        report = runner.run(BenchmarkTarget.ANALYZE, samples)
        assert hasattr(report, 'avg_ms')
        assert hasattr(report, 'p50_ms')
        assert hasattr(report, 'p99_ms')
        assert hasattr(report, 'violations')


# ---------------------------------------------------------------------------
# TC-17 ~ TC-20: 경계값 및 특수 케이스
# ---------------------------------------------------------------------------

class TestPercentileBoundary:
    """경계값 및 특수 케이스."""

    def test_p0_returns_min(self):
        """TC-17: P0 = 최솟값."""
        data = [3.0, 1.0, 2.0]
        assert percentile(data, 0.0) == 1.0

    def test_p100_returns_max(self):
        """TC-18: P100 = 최댓값."""
        data = [3.0, 1.0, 2.0]
        assert percentile(data, 1.0) == 3.0

    def test_large_n_monotonic(self):
        """TC-19: 분위수 단조 증가."""
        data = list(range(1, 1001))
        p25 = percentile(data, 0.25)
        p50 = percentile(data, 0.50)
        p75 = percentile(data, 0.75)
        p99 = percentile(data, 0.99)
        assert p25 < p50 < p75 < p99

    def test_float_precision(self):
        """TC-20: 부동소수점 정밀도."""
        data = [0.1 * i for i in range(1, 101)]
        v = percentile(data, 0.99)
        assert 0.0 < v <= 10.0
