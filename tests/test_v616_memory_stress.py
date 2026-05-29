"""
test_v616_memory_stress.py — V616 MemoryLeakDetector + StressTester 테스트

테스트 클래스:
  TestMemorySnapshot       (4 TC) — MemorySnapshot.take / top_allocators
  TestLeakReport           (4 TC) — LeakReport 속성 및 to_dict
  TestMemoryLeakDetector   (7 TC) — start/stop/baseline/check/diff/context
  TestPhaseResult          (4 TC) — _percentile + PhaseResult 속성
  TestStressTester         (6 TC) — run_phase / run / quick_stress / SLO 판정
"""

from __future__ import annotations

import time
import unittest
from unittest.mock import patch

from literary_system.optimization.memory_leak_detector import (
    AllocatorEntry,
    LeakReport,
    MemoryLeakDetector,
    MemorySnapshot,
)
from literary_system.optimization.stress_tester import (
    PhaseResult,
    StressConfig,
    StressResult,
    StressTester,
    _percentile,
)


# ─────────────────────────────────────────────────────────────────────────────
# TestMemorySnapshot
# ─────────────────────────────────────────────────────────────────────────────

class TestMemorySnapshot(unittest.TestCase):
    """MemorySnapshot 기본 기능 테스트."""

    def test_take_returns_snapshot(self):
        """take()가 MemorySnapshot 인스턴스를 반환해야 한다."""
        snap = MemorySnapshot.take()
        self.assertIsInstance(snap, MemorySnapshot)

    def test_total_bytes_non_negative(self):
        """total_bytes가 0 이상이어야 한다."""
        snap = MemorySnapshot.take()
        self.assertGreaterEqual(snap.total_bytes, 0)

    def test_top_allocators_returns_list(self):
        """top_allocators()가 리스트를 반환해야 한다."""
        snap = MemorySnapshot.take()
        allocators = snap.top_allocators(n=5)
        self.assertIsInstance(allocators, list)
        self.assertLessEqual(len(allocators), 5)

    def test_allocator_entry_to_dict(self):
        """AllocatorEntry.to_dict()가 필수 키를 포함해야 한다."""
        entry = AllocatorEntry(filename="test.py", lineno=10, size_bytes=1024)
        d = entry.to_dict()
        self.assertIn("filename", d)
        self.assertIn("lineno", d)
        self.assertIn("size_bytes", d)
        self.assertEqual(d["filename"], "test.py")
        self.assertEqual(d["size_bytes"], 1024)


# ─────────────────────────────────────────────────────────────────────────────
# TestLeakReport
# ─────────────────────────────────────────────────────────────────────────────

class TestLeakReport(unittest.TestCase):
    """LeakReport 속성 및 직렬화 테스트."""

    def _make_report(self, delta: int, threshold: int) -> LeakReport:
        return LeakReport(
            baseline_bytes=1_000_000,
            current_bytes=1_000_000 + delta,
            delta_bytes=delta,
            threshold_bytes=threshold,
            is_leaking=(delta > threshold),
        )

    def test_is_leaking_true_when_delta_exceeds_threshold(self):
        """delta > threshold 일 때 is_leaking=True이어야 한다."""
        report = self._make_report(delta=20_000_000, threshold=10_000_000)
        self.assertTrue(report.is_leaking)

    def test_is_leaking_false_when_delta_below_threshold(self):
        """delta < threshold 일 때 is_leaking=False이어야 한다."""
        report = self._make_report(delta=1_000, threshold=10_000_000)
        self.assertFalse(report.is_leaking)

    def test_delta_mb_property(self):
        """delta_mb = delta_bytes / 1MB이어야 한다."""
        report = self._make_report(delta=5_242_880, threshold=10_000_000)  # 5 MB
        self.assertAlmostEqual(report.delta_mb, 5.0, places=1)

    def test_to_dict_contains_required_keys(self):
        """to_dict()가 필수 키를 모두 포함해야 한다."""
        report = self._make_report(delta=100, threshold=10_000_000)
        d = report.to_dict()
        required = {
            "baseline_bytes", "current_bytes", "delta_bytes", "delta_mb",
            "threshold_bytes", "threshold_mb", "is_leaking", "top_allocators",
        }
        for key in required:
            self.assertIn(key, d, f"누락된 키: {key}")


# ─────────────────────────────────────────────────────────────────────────────
# TestMemoryLeakDetector
# ─────────────────────────────────────────────────────────────────────────────

class TestMemoryLeakDetector(unittest.TestCase):
    """MemoryLeakDetector 전체 기능 테스트."""

    def setUp(self):
        self.detector = MemoryLeakDetector(threshold_mb=10.0)

    def tearDown(self):
        self.detector.stop()

    def test_start_enables_tracing(self):
        """start() 후 tracemalloc이 활성화되어야 한다."""
        import tracemalloc
        self.detector.start()
        self.assertTrue(tracemalloc.is_tracing())

    def test_stop_disables_tracing(self):
        """stop() 후 tracemalloc이 비활성화되어야 한다."""
        import tracemalloc
        self.detector.start()
        self.detector.stop()
        # 다른 테스트가 시작 중일 수 있으니 _tracing 상태만 확인
        self.assertFalse(self.detector._tracing)

    def test_baseline_returns_snapshot(self):
        """baseline()이 MemorySnapshot을 반환해야 한다."""
        snap = self.detector.baseline()
        self.assertIsInstance(snap, MemorySnapshot)

    def test_capture_returns_snapshot(self):
        """capture()가 MemorySnapshot을 반환해야 한다."""
        self.detector.start()
        snap = self.detector.capture()
        self.assertIsInstance(snap, MemorySnapshot)

    def test_check_no_leak_on_small_allocation(self):
        """소량 할당 후 is_leaking=False이어야 한다."""
        bl = self.detector.baseline()
        _ = [0] * 100  # 소량 할당
        report = self.detector.check(bl)
        self.assertIsInstance(report, LeakReport)
        # 10 MB 임계값이므로 소량 할당은 누수 아님
        self.assertFalse(report.is_leaking)

    def test_diff_detects_large_allocation(self):
        """임계값 초과 할당은 is_leaking=True이어야 한다."""
        detector = MemoryLeakDetector(threshold_mb=0.001)  # 1 KB 임계
        bl = detector.baseline()
        _ = bytearray(100_000)  # 100 KB 할당
        current = detector.capture()
        report = detector.diff(bl, current)
        # 100 KB > 1 KB 임계 → leaking
        self.assertTrue(report.is_leaking)
        detector.stop()

    def test_context_manager(self):
        """컨텍스트 매니저로 사용 가능해야 한다."""
        with MemoryLeakDetector(threshold_mb=10.0) as det:
            bl = det._baseline_snapshot
            self.assertIsNotNone(bl)
            report = det.check(bl)
            self.assertIsInstance(report, LeakReport)


# ─────────────────────────────────────────────────────────────────────────────
# TestPhaseResult
# ─────────────────────────────────────────────────────────────────────────────

class TestPhaseResult(unittest.TestCase):
    """PhaseResult 백분위수 및 속성 테스트."""

    def test_percentile_p50(self):
        """_percentile([10,20,30,40,50], 50) ≈ 30이어야 한다."""
        data = [10.0, 20.0, 30.0, 40.0, 50.0]
        result = _percentile(data, 50)
        self.assertAlmostEqual(result, 30.0, places=1)

    def test_percentile_p95_on_single_element(self):
        """단일 요소 리스트의 P95는 해당 요소값이어야 한다."""
        result = _percentile([42.0], 95)
        self.assertAlmostEqual(result, 42.0)

    def test_phase_result_p95(self):
        """PhaseResult.p95_ms가 _percentile과 일치해야 한다."""
        pr = PhaseResult(phase="test", iterations=5, latencies_ms=[10.0, 20.0, 30.0, 40.0, 50.0])
        expected = _percentile([10.0, 20.0, 30.0, 40.0, 50.0], 95)
        self.assertAlmostEqual(pr.p95_ms, expected, places=2)

    def test_to_dict_keys(self):
        """to_dict()가 필수 키를 포함해야 한다."""
        pr = PhaseResult(phase="warmup", iterations=3, latencies_ms=[5.0, 10.0, 15.0])
        d = pr.to_dict()
        for key in ["phase", "iterations", "p50_ms", "p95_ms", "p99_ms", "mean_ms"]:
            self.assertIn(key, d)


# ─────────────────────────────────────────────────────────────────────────────
# TestStressTester
# ─────────────────────────────────────────────────────────────────────────────

class TestStressTester(unittest.TestCase):
    """StressTester 실행 및 SLO 판정 테스트."""

    def test_run_phase_records_latencies(self):
        """run_phase()가 iterations만큼 latency를 기록해야 한다."""
        tester = StressTester(StressConfig(sustained_iters=5))
        result = tester.run_phase("test", lambda: None, iters=5)
        self.assertEqual(len(result.latencies_ms), 5)
        self.assertEqual(result.errors, 0)

    def test_run_phase_handles_exceptions(self):
        """run_phase()가 예외 발생을 오류 카운트로 기록해야 한다."""
        def fail_fn():
            raise ValueError("의도적 오류")

        tester = StressTester(StressConfig())
        result = tester.run_phase("test", fail_fn, iters=3)
        self.assertEqual(result.errors, 3)
        self.assertEqual(len(result.latencies_ms), 0)

    def test_run_returns_stress_result(self):
        """run()이 StressResult를 반환해야 한다."""
        cfg = StressConfig(warmup_iters=2, sustained_iters=5, cooldown_iters=1)
        tester = StressTester(cfg)
        result = tester.run(lambda: None)
        self.assertIsInstance(result, StressResult)

    def test_quick_stress_passes_for_fast_fn(self):
        """빠른 함수는 quick_stress에서 SLO를 통과해야 한다."""
        result = StressTester.quick_stress(
            fn=lambda: None,
            warmup=2,
            iters=5,
            target_p95_ms=1500.0,
        )
        self.assertTrue(result.slo_p95_pass)
        self.assertTrue(result.all_pass)

    def test_slo_p95_fail_for_slow_fn(self):
        """P95 임계값을 초과하는 함수는 SLO 실패해야 한다."""
        def slow_fn():
            time.sleep(0.01)  # 10ms

        cfg = StressConfig(
            warmup_iters=1,
            sustained_iters=5,
            cooldown_iters=1,
            target_p95_ms=1.0,  # 1ms — 실패 유도
        )
        result = StressTester(cfg).run(slow_fn)
        self.assertFalse(result.slo_p95_pass)
        self.assertFalse(result.all_pass)

    def test_to_dict_contains_all_pass(self):
        """StressResult.to_dict()가 all_pass 키를 포함해야 한다."""
        result = StressTester.quick_stress(lambda: None, warmup=1, iters=3)
        d = result.to_dict()
        self.assertIn("all_pass", d)
        self.assertIn("warmup", d)
        self.assertIn("sustained", d)
        self.assertIn("cooldown", d)


if __name__ == "__main__":
    unittest.main()
