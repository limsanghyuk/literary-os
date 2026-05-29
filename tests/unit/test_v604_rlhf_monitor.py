"""
V604 단위 테스트 — RLHFMonitor

TC-1: MonitorConfig 기본값 검증
TC-2: MonitorConfig 유효성 검사 (잘못된 값 → ValueError)
TC-3: record() — RewardSnapshot 반환 및 필드 확인
TC-4: moving_average() — 슬라이딩 윈도우 정확도
TC-5: trend() — improving 감지
TC-6: trend() — degrading 감지
TC-7: trend() — cold-start unknown (min_samples 미달)
TC-8: check_rollback() — 연속 감소 3회 → 트리거
TC-9: summary() — 7 필수 키 존재
"""
from __future__ import annotations

import pytest

from literary_system.rlhf.rlhf_monitor import (
    TREND_DEGRADING,
    TREND_IMPROVING,
    TREND_UNKNOWN,
    MonitorConfig,
    RLHFMonitor,
)


# ---------------------------------------------------------------------------
# TC-1: MonitorConfig 기본값
# ---------------------------------------------------------------------------
class TestMonitorConfigDefaults:
    def test_window_size_default(self):
        cfg = MonitorConfig()
        assert cfg.window_size == 10

    def test_rollback_threshold_default(self):
        cfg = MonitorConfig()
        assert 0.0 < cfg.rollback_threshold <= 1.0

    def test_degradation_steps_default(self):
        cfg = MonitorConfig()
        assert cfg.degradation_steps >= 1

    def test_min_samples_default(self):
        cfg = MonitorConfig()
        assert cfg.min_samples >= 1


# ---------------------------------------------------------------------------
# TC-2: MonitorConfig 유효성 검사
# ---------------------------------------------------------------------------
class TestMonitorConfigValidation:
    def test_invalid_window_size(self):
        with pytest.raises(ValueError):
            MonitorConfig(window_size=0)

    def test_invalid_rollback_threshold_negative(self):
        with pytest.raises(ValueError):
            MonitorConfig(rollback_threshold=-0.1)

    def test_invalid_rollback_threshold_over_one(self):
        with pytest.raises(ValueError):
            MonitorConfig(rollback_threshold=1.5)

    def test_invalid_degradation_steps(self):
        with pytest.raises(ValueError):
            MonitorConfig(degradation_steps=0)

    def test_invalid_min_samples(self):
        with pytest.raises(ValueError):
            MonitorConfig(min_samples=0)


# ---------------------------------------------------------------------------
# TC-3: record() 반환 타입 및 필드
# ---------------------------------------------------------------------------
class TestRecord:
    def test_returns_reward_snapshot(self):
        from literary_system.rlhf.rlhf_monitor import RewardSnapshot
        monitor = RLHFMonitor()
        snap = monitor.record(step=1, rewards=[0.70, 0.75])
        assert isinstance(snap, RewardSnapshot)

    def test_snapshot_step(self):
        monitor = RLHFMonitor()
        snap = monitor.record(step=5, rewards=[0.80])
        assert snap.step == 5

    def test_snapshot_mean_reward(self):
        monitor = RLHFMonitor()
        snap = monitor.record(step=1, rewards=[0.60, 0.80])
        assert abs(snap.mean_reward - 0.70) < 1e-9

    def test_empty_rewards_raises(self):
        monitor = RLHFMonitor()
        with pytest.raises((ValueError, ZeroDivisionError)):
            monitor.record(step=1, rewards=[])

    def test_snapshot_n_samples_increments(self):
        monitor = RLHFMonitor()
        monitor.record(step=1, rewards=[0.70])
        snap2 = monitor.record(step=2, rewards=[0.72])
        assert snap2.n_samples == 2


# ---------------------------------------------------------------------------
# TC-4: moving_average() 정확도
# ---------------------------------------------------------------------------
class TestMovingAverage:
    def test_single_step(self):
        monitor = RLHFMonitor()
        monitor.record(step=1, rewards=[0.80])
        assert abs(monitor.moving_average() - 0.80) < 1e-9

    def test_window_clips_to_available(self):
        monitor = RLHFMonitor(MonitorConfig(window_size=10))
        for i, r in enumerate([0.60, 0.70, 0.80]):
            monitor.record(step=i, rewards=[r])
        expected = (0.60 + 0.70 + 0.80) / 3
        assert abs(monitor.moving_average() - expected) < 1e-9

    def test_window_respects_size(self):
        monitor = RLHFMonitor(MonitorConfig(window_size=2))
        monitor.record(step=1, rewards=[0.50])
        monitor.record(step=2, rewards=[0.60])
        monitor.record(step=3, rewards=[0.80])
        # window_size=2 → 최근 2개: 0.60, 0.80
        expected = (0.60 + 0.80) / 2
        assert abs(monitor.moving_average() - expected) < 1e-9

    def test_empty_returns_zero(self):
        monitor = RLHFMonitor()
        assert monitor.moving_average() == 0.0


# ---------------------------------------------------------------------------
# TC-5: trend() — improving
# ---------------------------------------------------------------------------
class TestTrendImproving:
    def test_improving_trend(self):
        cfg = MonitorConfig(window_size=6, min_samples=6)
        monitor = RLHFMonitor(cfg)
        # 전반 낮음 → 후반 높음
        for i, r in enumerate([0.50, 0.52, 0.54, 0.70, 0.75, 0.80]):
            monitor.record(step=i, rewards=[r])
        assert monitor.trend() == TREND_IMPROVING


# ---------------------------------------------------------------------------
# TC-6: trend() — degrading
# ---------------------------------------------------------------------------
class TestTrendDegrading:
    def test_degrading_trend(self):
        cfg = MonitorConfig(window_size=6, min_samples=6)
        monitor = RLHFMonitor(cfg)
        # 전반 높음 → 후반 낮음
        for i, r in enumerate([0.80, 0.78, 0.75, 0.55, 0.50, 0.45]):
            monitor.record(step=i, rewards=[r])
        assert monitor.trend() == TREND_DEGRADING


# ---------------------------------------------------------------------------
# TC-7: trend() — cold-start unknown
# ---------------------------------------------------------------------------
class TestTrendColdStart:
    def test_unknown_before_min_samples(self):
        cfg = MonitorConfig(min_samples=5)
        monitor = RLHFMonitor(cfg)
        monitor.record(step=1, rewards=[0.70])
        monitor.record(step=2, rewards=[0.60])
        assert monitor.trend() == TREND_UNKNOWN


# ---------------------------------------------------------------------------
# TC-8: check_rollback() — 연속 감소 트리거
# ---------------------------------------------------------------------------
class TestCheckRollback:
    def test_consecutive_degradation_triggers(self):
        cfg = MonitorConfig(degradation_steps=3, min_samples=1)
        monitor = RLHFMonitor(cfg)
        monitor.record(step=1, rewards=[0.80])
        monitor.record(step=2, rewards=[0.75])  # 1번째 감소
        monitor.record(step=3, rewards=[0.70])  # 2번째 감소
        monitor.record(step=4, rewards=[0.65])  # 3번째 감소 → 트리거
        triggered = monitor.check_rollback(step=4)
        assert triggered is True
        assert monitor.state.should_rollback is True

    def test_no_rollback_when_stable(self):
        cfg = MonitorConfig(degradation_steps=3, min_samples=1)
        monitor = RLHFMonitor(cfg)
        for i, r in enumerate([0.70, 0.72, 0.74, 0.76]):
            monitor.record(step=i, rewards=[r])
        triggered = monitor.check_rollback(step=3)
        assert triggered is False

    def test_reset_rollback_flag(self):
        cfg = MonitorConfig(degradation_steps=3, min_samples=1)
        monitor = RLHFMonitor(cfg)
        monitor.record(step=1, rewards=[0.80])
        monitor.record(step=2, rewards=[0.70])
        monitor.record(step=3, rewards=[0.60])
        monitor.record(step=4, rewards=[0.50])
        monitor.check_rollback(step=4)
        monitor.reset_rollback_flag()
        assert monitor.state.should_rollback is False
        assert monitor.state.consecutive_degradations == 0

    def test_rollback_record_saved(self):
        cfg = MonitorConfig(degradation_steps=3, min_samples=1)
        monitor = RLHFMonitor(cfg)
        monitor.record(step=1, rewards=[0.80])
        monitor.record(step=2, rewards=[0.75])
        monitor.record(step=3, rewards=[0.70])
        monitor.record(step=4, rewards=[0.65])
        monitor.check_rollback(step=4)
        assert len(monitor.state.rollback_records) == 1
        assert monitor.state.total_rollbacks == 1


# ---------------------------------------------------------------------------
# TC-9: summary() 7 필수 키
# ---------------------------------------------------------------------------
class TestSummary:
    REQUIRED_KEYS = {
        "total_steps",
        "current_moving_avg",
        "current_trend",
        "total_rollbacks",
        "consecutive_degradations",
        "should_rollback",
        "last_mean_reward",
    }

    def test_summary_has_all_keys(self):
        monitor = RLHFMonitor()
        for i in range(3):
            monitor.record(step=i, rewards=[0.70 + i * 0.02])
        summary = monitor.summary()
        assert self.REQUIRED_KEYS.issubset(set(summary.keys()))

    def test_summary_total_steps(self):
        monitor = RLHFMonitor()
        for i in range(4):
            monitor.record(step=i, rewards=[0.70])
        assert monitor.summary()["total_steps"] == 4
