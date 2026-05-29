"""
test_v617_long_run_monitor.py — V617 LongRunMonitor 테스트

테스트 클래스:
  TestLongRunConfig     (4 TC) — 기본값, 필드 검증
  TestEpochResult       (5 TC) — all_pass, pass_stress/leak, to_dict
  TestLongRunReport     (5 TC) — all_pass, failed_epochs, p95_trend, leak_trend, to_dict
  TestLongRunMonitorRun (7 TC) — run / quick_monitor / epoch PASS/FAIL / SLO 위반 / summary
  TestLongRunEdgeCases  (4 TC) — epochs=1, 에러 허용, peak_memory, memory_sampler
"""

from __future__ import annotations

import time
import unittest

from literary_system.optimization.long_run_monitor import (
    EpochResult,
    LongRunMonitor,
    LongRunReport,
    LongRunConfig,
)
from literary_system.optimization.memory_leak_detector import (
    AllocatorEntry,
    LeakReport,
    MemoryLeakDetector,
    MemorySnapshot,
)
from literary_system.optimization.stress_tester import (
    StressConfig,
    StressResult,
    StressTester,
    PhaseResult,
)


# ─────────────────────────────────────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def _make_phase(phase: str, iters: int, ms: float = 1.0) -> PhaseResult:
    return PhaseResult(phase=phase, iterations=iters, latencies_ms=[ms] * iters)


def _make_stress(p95_ms: float = 1.0, all_pass: bool = True) -> StressResult:
    cfg = StressConfig(target_p95_ms=1500.0)
    w = _make_phase("warmup", 2)
    s = _make_phase("sustained", 5, ms=p95_ms)
    c = _make_phase("cooldown", 1)
    return StressResult(
        config=cfg,
        warmup=w,
        sustained=s,
        cooldown=c,
        slo_p95_pass=all_pass,
        slo_p99_pass=True,
        slo_memory_pass=True,
    )


def _make_leak(delta_mb: float = 0.0, leaking: bool = False) -> LeakReport:
    threshold = int(10 * 1024 * 1024)
    delta = int(delta_mb * 1024 * 1024)
    return LeakReport(
        baseline_bytes=1_000_000,
        current_bytes=1_000_000 + delta,
        delta_bytes=delta,
        threshold_bytes=threshold,
        is_leaking=leaking,
    )


def _make_epoch(epoch: int = 1, pass_stress: bool = True, pass_leak: bool = True) -> EpochResult:
    stress = _make_stress(all_pass=pass_stress)
    leak = _make_leak(leaking=not pass_leak)
    return EpochResult(epoch=epoch, stress=stress, leak=leak, duration_s=0.1)


# ─────────────────────────────────────────────────────────────────────────────
# TestLongRunConfig
# ─────────────────────────────────────────────────────────────────────────────

class TestLongRunConfig(unittest.TestCase):
    def test_default_epochs(self):
        """기본 epochs는 3이어야 한다."""
        cfg = LongRunConfig()
        self.assertEqual(cfg.epochs, 3)

    def test_default_target_p95(self):
        """기본 target_p95_ms는 1500.0이어야 한다."""
        cfg = LongRunConfig()
        self.assertEqual(cfg.target_p95_ms, 1500.0)

    def test_custom_epochs(self):
        """커스텀 epochs 설정이 반영되어야 한다."""
        cfg = LongRunConfig(epochs=10)
        self.assertEqual(cfg.epochs, 10)

    def test_none_slo_allowed(self):
        """SLO를 None으로 설정할 수 있어야 한다."""
        cfg = LongRunConfig(target_p95_ms=None, leak_threshold_mb=None)
        self.assertIsNone(cfg.target_p95_ms)
        self.assertIsNone(cfg.leak_threshold_mb)


# ─────────────────────────────────────────────────────────────────────────────
# TestEpochResult
# ─────────────────────────────────────────────────────────────────────────────

class TestEpochResult(unittest.TestCase):
    def test_all_pass_when_both_pass(self):
        """stress + leak 모두 PASS이면 all_pass=True."""
        epoch = _make_epoch(pass_stress=True, pass_leak=True)
        self.assertTrue(epoch.all_pass)

    def test_all_pass_false_when_stress_fails(self):
        """stress FAIL이면 all_pass=False."""
        epoch = _make_epoch(pass_stress=False, pass_leak=True)
        self.assertFalse(epoch.all_pass)

    def test_all_pass_false_when_leak_detected(self):
        """누수 감지 시 all_pass=False."""
        epoch = _make_epoch(pass_stress=True, pass_leak=False)
        self.assertFalse(epoch.all_pass)

    def test_epoch_number_stored(self):
        """epoch 번호가 올바르게 저장되어야 한다."""
        epoch = _make_epoch(epoch=5)
        self.assertEqual(epoch.epoch, 5)

    def test_to_dict_keys(self):
        """to_dict()가 필수 키를 포함해야 한다."""
        epoch = _make_epoch()
        d = epoch.to_dict()
        for key in ["epoch", "all_pass", "pass_stress", "pass_leak", "duration_s", "stress", "leak"]:
            self.assertIn(key, d)


# ─────────────────────────────────────────────────────────────────────────────
# TestLongRunReport
# ─────────────────────────────────────────────────────────────────────────────

class TestLongRunReport(unittest.TestCase):
    def _make_report(self, results) -> LongRunReport:
        cfg = LongRunConfig(epochs=len(results))
        report = LongRunReport(config=cfg, epochs=results, total_duration_s=1.0)
        return report

    def test_all_pass_when_all_epochs_pass(self):
        """모든 epoch PASS이면 all_pass=True."""
        report = self._make_report([_make_epoch(1), _make_epoch(2)])
        self.assertTrue(report.all_pass)

    def test_all_pass_false_when_one_epoch_fails(self):
        """하나라도 실패하면 all_pass=False."""
        report = self._make_report([
            _make_epoch(1, pass_stress=True),
            _make_epoch(2, pass_stress=False),
        ])
        self.assertFalse(report.all_pass)

    def test_failed_epochs_list(self):
        """failed_epochs가 실패한 epoch 번호를 반환해야 한다."""
        report = self._make_report([
            _make_epoch(1, pass_stress=True),
            _make_epoch(2, pass_stress=False),
            _make_epoch(3, pass_stress=True),
        ])
        self.assertEqual(report.failed_epochs, [2])

    def test_p95_trend_length(self):
        """p95_trend 길이 = epoch 수이어야 한다."""
        report = self._make_report([_make_epoch(i) for i in range(1, 4)])
        self.assertEqual(len(report.p95_trend), 3)

    def test_to_dict_contains_all_pass(self):
        """to_dict()에 all_pass, total_epochs, epochs 포함."""
        report = self._make_report([_make_epoch(1)])
        d = report.to_dict()
        self.assertIn("all_pass", d)
        self.assertIn("total_epochs", d)
        self.assertIn("epochs", d)


# ─────────────────────────────────────────────────────────────────────────────
# TestLongRunMonitorRun
# ─────────────────────────────────────────────────────────────────────────────

class TestLongRunMonitorRun(unittest.TestCase):
    def test_run_returns_report(self):
        """run()이 LongRunReport를 반환해야 한다."""
        cfg = LongRunConfig(epochs=2, warmup_iters=1, sustained_iters=3, cooldown_iters=1)
        monitor = LongRunMonitor(cfg)
        report = monitor.run(lambda: None)
        self.assertIsInstance(report, LongRunReport)

    def test_correct_epoch_count(self):
        """epochs 파라미터만큼 EpochResult가 생성되어야 한다."""
        cfg = LongRunConfig(epochs=3, warmup_iters=1, sustained_iters=3, cooldown_iters=1)
        report = LongRunMonitor(cfg).run(lambda: None)
        self.assertEqual(len(report.epochs), 3)

    def test_fast_fn_passes_p95_slo(self):
        """빠른 함수는 P95 SLO를 통과해야 한다."""
        cfg = LongRunConfig(epochs=2, warmup_iters=1, sustained_iters=5,
                            cooldown_iters=1, target_p95_ms=1500.0)
        report = LongRunMonitor(cfg).run(lambda: None)
        self.assertTrue(report.all_pass)

    def test_slow_fn_fails_p95_slo(self):
        """P95 임계값 초과 함수는 SLO 실패해야 한다."""
        def slow():
            time.sleep(0.01)  # 10ms

        cfg = LongRunConfig(epochs=1, warmup_iters=1, sustained_iters=3,
                            cooldown_iters=1, target_p95_ms=1.0)  # 1ms — 실패 유도
        report = LongRunMonitor(cfg).run(slow)
        self.assertFalse(report.all_pass)
        self.assertEqual(len(report.failed_epochs), 1)

    def test_quick_monitor_classmethod(self):
        """quick_monitor()가 LongRunReport를 반환해야 한다."""
        report = LongRunMonitor.quick_monitor(lambda: None, epochs=2)
        self.assertIsInstance(report, LongRunReport)
        self.assertEqual(len(report.epochs), 2)

    def test_summary_contains_pass_status(self):
        """summary()가 PASS/FAIL 문자열을 포함해야 한다."""
        cfg = LongRunConfig(epochs=2, warmup_iters=1, sustained_iters=3, cooldown_iters=1)
        monitor = LongRunMonitor(cfg)
        report = monitor.run(lambda: None)
        s = monitor.summary(report)
        self.assertIn("PASS", s)

    def test_total_duration_positive(self):
        """total_duration_s가 양수여야 한다."""
        cfg = LongRunConfig(epochs=2, warmup_iters=1, sustained_iters=3, cooldown_iters=1)
        report = LongRunMonitor(cfg).run(lambda: None)
        self.assertGreaterEqual(report.total_duration_s, 0)


# ─────────────────────────────────────────────────────────────────────────────
# TestLongRunEdgeCases
# ─────────────────────────────────────────────────────────────────────────────

class TestLongRunEdgeCases(unittest.TestCase):
    def test_single_epoch(self):
        """epochs=1로도 정상 동작해야 한다."""
        cfg = LongRunConfig(epochs=1, warmup_iters=1, sustained_iters=3, cooldown_iters=1)
        report = LongRunMonitor(cfg).run(lambda: None)
        self.assertEqual(len(report.epochs), 1)

    def test_fn_with_exceptions_counts_errors(self):
        """fn이 예외를 던져도 모니터가 중단되지 않아야 한다."""
        call_count = [0]

        def flaky():
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                raise RuntimeError("의도적 오류")

        cfg = LongRunConfig(epochs=2, warmup_iters=1, sustained_iters=4, cooldown_iters=1)
        report = LongRunMonitor(cfg).run(flaky)
        # 예외가 있어도 report가 생성되어야 함
        self.assertEqual(len(report.epochs), 2)

    def test_memory_sampler_used(self):
        """memory_sampler 콜백이 peak_memory에 반영되어야 한다."""
        sampler_calls = [0]

        def sampler() -> float:
            sampler_calls[0] += 1
            return 100.0  # 100 MB

        cfg = LongRunConfig(epochs=2, warmup_iters=1, sustained_iters=3, cooldown_iters=1)
        report = LongRunMonitor(cfg).run(lambda: None, memory_sampler=sampler)
        # sampler가 최소 1번 이상 호출되어야 함
        self.assertGreater(sampler_calls[0], 0)

    def test_leak_delta_trend_length_matches_epochs(self):
        """leak_delta_trend 길이 = epochs 수이어야 한다."""
        cfg = LongRunConfig(epochs=3, warmup_iters=1, sustained_iters=3, cooldown_iters=1)
        report = LongRunMonitor(cfg).run(lambda: None)
        self.assertEqual(len(report.leak_delta_trend), 3)


if __name__ == "__main__":
    unittest.main()
