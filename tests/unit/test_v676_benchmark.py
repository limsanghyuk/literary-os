"""
V676 단위 테스트 — Enterprise Benchmark Layer (ADR-138, SP-C.4 안정화 2)
30 TC
"""
import pytest
from literary_system.enterprise.benchmark import (
    BenchmarkStatus, BenchmarkTarget, BenchmarkThreshold,
    BenchmarkSample, BenchmarkReport, EnterpriseBenchmarkSuite,
    BenchmarkRunner, BenchmarkGate,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def runner():
    return BenchmarkRunner()

@pytest.fixture
def gate():
    return BenchmarkGate()

def _make_samples(target, elapsed_list, success=True):
    return [BenchmarkSample(target=target, elapsed_ms=e, success=success) for e in elapsed_list]


# ── TC01~TC05: BenchmarkStatus / BenchmarkTarget 열거형 ──────────────────────

def test_benchmark_status_values():
    assert BenchmarkStatus.PASS == "pass"
    assert BenchmarkStatus.FAIL == "fail"
    assert BenchmarkStatus.WARN == "warn"

def test_benchmark_target_values():
    targets = {t.value for t in BenchmarkTarget}
    assert "slo_monitor" in targets
    assert "revenue_calculator" in targets
    assert "full_pipeline" in targets

def test_benchmark_sample_defaults():
    s = BenchmarkSample(target=BenchmarkTarget.SLO_MONITOR, elapsed_ms=5.0)
    assert s.success is True
    assert s.error is None

def test_benchmark_sample_failure():
    s = BenchmarkSample(target=BenchmarkTarget.REVENUE_CALCULATOR, elapsed_ms=1.0, success=False, error="timeout")
    assert not s.success
    assert s.error == "timeout"

def test_benchmark_threshold_fields():
    t = BenchmarkThreshold(
        target=BenchmarkTarget.SLO_MONITOR,
        max_avg_ms=50.0, max_p99_ms=200.0, min_throughput_rps=20.0
    )
    assert t.max_avg_ms == 50.0
    assert t.min_throughput_rps == 20.0


# ── TC06~TC12: BenchmarkRunner 통계 계산 ─────────────────────────────────────

def test_runner_pass_all_green(runner):
    samples = _make_samples(BenchmarkTarget.SLO_MONITOR, [5.0] * 10)
    report = runner.run(BenchmarkTarget.SLO_MONITOR, samples)
    assert report.status == BenchmarkStatus.PASS
    assert report.passed is True

def test_runner_fail_avg_exceeds(runner):
    # avg = 60ms > 50ms threshold
    samples = _make_samples(BenchmarkTarget.SLO_MONITOR, [60.0] * 20)
    report = runner.run(BenchmarkTarget.SLO_MONITOR, samples)
    assert report.status == BenchmarkStatus.FAIL
    assert any("avg_ms" in v for v in report.violations)

def test_runner_fail_p99_exceeds(runner):
    # 99 퍼센타일이 임계 초과
    base = [10.0] * 98 + [300.0, 300.0]
    samples = _make_samples(BenchmarkTarget.SLO_MONITOR, base)
    report = runner.run(BenchmarkTarget.SLO_MONITOR, samples)
    assert BenchmarkStatus.FAIL == report.status

def test_runner_success_rate(runner):
    ok = _make_samples(BenchmarkTarget.REVENUE_CALCULATOR, [2.0] * 8)
    fail = [BenchmarkSample(target=BenchmarkTarget.REVENUE_CALCULATOR, elapsed_ms=2.0, success=False)]
    report = runner.run(BenchmarkTarget.REVENUE_CALCULATOR, ok + fail)
    assert abs(report.success_rate - 8/9) < 0.01

def test_runner_sample_count(runner):
    samples = _make_samples(BenchmarkTarget.FULL_PIPELINE, [15.0] * 30)
    report = runner.run(BenchmarkTarget.FULL_PIPELINE, samples)
    assert report.sample_count == 30

def test_runner_avg_correct(runner):
    samples = _make_samples(BenchmarkTarget.SLO_MONITOR, [10.0, 20.0, 30.0])
    report = runner.run(BenchmarkTarget.SLO_MONITOR, samples)
    assert abs(report.avg_ms - 20.0) < 0.01

def test_runner_throughput_positive(runner):
    samples = _make_samples(BenchmarkTarget.REVENUE_CALCULATOR, [5.0] * 50)
    report = runner.run(BenchmarkTarget.REVENUE_CALCULATOR, samples)
    assert report.throughput_rps > 0


# ── TC13~TC18: BenchmarkReport 속성 ──────────────────────────────────────────

def test_report_passed_true():
    t = BenchmarkThreshold(BenchmarkTarget.SLO_MONITOR, 50, 200, 20)
    r = BenchmarkReport(
        target=BenchmarkTarget.SLO_MONITOR, sample_count=10,
        avg_ms=5.0, p50_ms=5.0, p99_ms=10.0,
        throughput_rps=50.0, success_rate=1.0,
        status=BenchmarkStatus.PASS, threshold=t,
    )
    assert r.passed is True

def test_report_passed_false():
    t = BenchmarkThreshold(BenchmarkTarget.SLO_MONITOR, 50, 200, 20)
    r = BenchmarkReport(
        target=BenchmarkTarget.SLO_MONITOR, sample_count=10,
        avg_ms=60.0, p50_ms=60.0, p99_ms=250.0,
        throughput_rps=5.0, success_rate=1.0,
        status=BenchmarkStatus.FAIL, threshold=t,
        violations=["avg_ms=60 > 50"],
    )
    assert r.passed is False

def test_report_violations_list():
    t = BenchmarkThreshold(BenchmarkTarget.SLO_MONITOR, 50, 200, 20)
    r = BenchmarkReport(
        target=BenchmarkTarget.SLO_MONITOR, sample_count=5,
        avg_ms=5.0, p50_ms=5.0, p99_ms=10.0,
        throughput_rps=100.0, success_rate=1.0,
        status=BenchmarkStatus.PASS, threshold=t,
    )
    assert r.violations == []

def test_suite_all_passed():
    t = BenchmarkThreshold(BenchmarkTarget.SLO_MONITOR, 50, 200, 20)
    rep = BenchmarkReport(
        target=BenchmarkTarget.SLO_MONITOR, sample_count=10,
        avg_ms=5.0, p50_ms=5.0, p99_ms=10.0,
        throughput_rps=50.0, success_rate=1.0,
        status=BenchmarkStatus.PASS, threshold=t,
    )
    suite = EnterpriseBenchmarkSuite(reports=[rep], suite_status=BenchmarkStatus.PASS)
    assert suite.all_passed is True
    assert suite.passed_count == 1
    assert suite.total_count == 1

def test_suite_not_all_passed():
    t = BenchmarkThreshold(BenchmarkTarget.SLO_MONITOR, 50, 200, 20)
    fail_rep = BenchmarkReport(
        target=BenchmarkTarget.SLO_MONITOR, sample_count=5,
        avg_ms=60.0, p50_ms=60.0, p99_ms=250.0,
        throughput_rps=5.0, success_rate=0.9,
        status=BenchmarkStatus.FAIL, threshold=t,
    )
    suite = EnterpriseBenchmarkSuite(reports=[fail_rep], suite_status=BenchmarkStatus.FAIL)
    assert suite.all_passed is False

def test_suite_counts():
    t = BenchmarkThreshold(BenchmarkTarget.SLO_MONITOR, 50, 200, 20)
    reps = [
        BenchmarkReport(
            target=BenchmarkTarget.SLO_MONITOR, sample_count=10,
            avg_ms=5.0, p50_ms=5.0, p99_ms=10.0,
            throughput_rps=50.0, success_rate=1.0,
            status=BenchmarkStatus.PASS, threshold=t,
        ),
        BenchmarkReport(
            target=BenchmarkTarget.REVENUE_CALCULATOR, sample_count=10,
            avg_ms=60.0, p50_ms=60.0, p99_ms=250.0,
            throughput_rps=5.0, success_rate=0.8,
            status=BenchmarkStatus.FAIL, threshold=t,
        ),
    ]
    suite = EnterpriseBenchmarkSuite(reports=reps)
    assert suite.total_count == 2
    assert suite.passed_count == 1


# ── TC19~TC24: BenchmarkGate demo_run ────────────────────────────────────────

def test_gate_demo_run_returns_suite(gate):
    suite = gate.demo_run()
    assert isinstance(suite, EnterpriseBenchmarkSuite)

def test_gate_demo_run_3_reports(gate):
    suite = gate.demo_run()
    assert suite.total_count == 3

def test_gate_demo_run_all_pass(gate):
    suite = gate.demo_run()
    assert suite.all_passed, [r.violations for r in suite.reports]

def test_gate_demo_run_suite_status_pass(gate):
    suite = gate.demo_run()
    assert suite.suite_status == BenchmarkStatus.PASS

def test_gate_demo_run_slo_avg_within_threshold(gate):
    suite = gate.demo_run()
    slo_rep = next(r for r in suite.reports if r.target == BenchmarkTarget.SLO_MONITOR)
    assert slo_rep.avg_ms <= 50.0

def test_gate_demo_run_revenue_avg_within_threshold(gate):
    suite = gate.demo_run()
    rev_rep = next(r for r in suite.reports if r.target == BenchmarkTarget.REVENUE_CALCULATOR)
    assert rev_rep.avg_ms <= 30.0


# ── TC25~TC30: GATE_ID + 패키지 노출 ─────────────────────────────────────────

def test_benchmark_gate_id():
    assert BenchmarkGate.GATE_ID == "G75-BM"

def test_benchmark_runner_default_thresholds():
    runner = BenchmarkRunner()
    assert BenchmarkTarget.SLO_MONITOR in runner.thresholds
    assert BenchmarkTarget.REVENUE_CALCULATOR in runner.thresholds
    assert BenchmarkTarget.FULL_PIPELINE in runner.thresholds

def test_time_call_success(runner):
    sample = runner.time_call(BenchmarkTarget.SLO_MONITOR, lambda: None)
    assert sample.success is True
    assert sample.elapsed_ms >= 0

def test_time_call_failure(runner):
    def boom():
        raise ValueError("boom")
    sample = runner.time_call(BenchmarkTarget.SLO_MONITOR, boom)
    assert sample.success is False
    assert "boom" in (sample.error or "")

def test_enterprise_package_exports_benchmark():
    from literary_system.enterprise import BenchmarkGate as BG, BenchmarkRunner as BR
    assert BG is not None
    assert BR is not None

def test_release_gate_g75_bm():
    from literary_system.gates.release_gate import GATES
    gate_ids = [g[0] for g in GATES]
    assert "benchmark_g75" in gate_ids
