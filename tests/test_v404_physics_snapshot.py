"""V404 — NarrativePhysicsSnapshotEngine 테스트 (18 tests)."""
import pytest
from literary_system.physics.narrative_physics_snapshot import (
    PhysicsSnapshot,
    NarrativePhysicsSnapshotEngine,
    SnapshotRunResult,
    _episode_tension,
)


# ── 헬퍼 ────────────────────────────────────────────────────────────────────

class _FakeSeriesConfig:
    def __init__(self, total_episodes=16, coefficient_store=None):
        self.total_episodes = total_episodes
        self.coefficient_store = coefficient_store
        self.title = "테스트 시리즈"


# ── PhysicsSnapshot 단위 테스트 ───────────────────────────────────────────────

class TestPhysicsSnapshot:
    def test_passed_above_threshold(self):
        snap = PhysicsSnapshot(
            episode_idx=4, fitness_score=7.5,
            energy_violations=0, curiosity_collapse=0,
            snapshot_timestamp="2026-01-01T00:00:00"
        )
        assert snap.passed() is True

    def test_failed_below_threshold(self):
        snap = PhysicsSnapshot(
            episode_idx=8, fitness_score=5.9,
            energy_violations=1, curiosity_collapse=1,
            snapshot_timestamp="2026-01-01T00:00:00"
        )
        assert snap.passed() is False

    def test_passed_custom_threshold(self):
        snap = PhysicsSnapshot(
            episode_idx=1, fitness_score=5.0,
            energy_violations=0, curiosity_collapse=0,
            snapshot_timestamp="2026-01-01T00:00:00"
        )
        assert snap.passed(fitness_min=4.0) is True
        assert snap.passed(fitness_min=6.0) is False

    def test_to_dict(self):
        snap = PhysicsSnapshot(
            episode_idx=12, fitness_score=8.2,
            energy_violations=0, curiosity_collapse=0,
            snapshot_timestamp="2026-05-14T00:00:00"
        )
        d = snap.to_dict()
        assert d["episode_idx"] == 12
        assert d["fitness_score"] == 8.2
        assert "passed" in d


# ── _episode_tension 테스트 ───────────────────────────────────────────────────

class TestEpisodeTension:
    def test_start_low(self):
        assert _episode_tension(0.0) < _episode_tension(0.5)

    def test_end_high(self):
        assert _episode_tension(1.0) >= 0.95

    def test_monotonic_trend(self):
        vals = [_episode_tension(p) for p in [0.0, 0.25, 0.5, 0.75, 1.0]]
        assert vals == sorted(vals), "긴장도는 단조 증가해야 함"

    def test_range(self):
        for p in [0.0, 0.1, 0.5, 0.9, 1.0]:
            v = _episode_tension(p)
            assert 0.0 <= v <= 1.0


# ── NarrativePhysicsSnapshotEngine 테스트 ────────────────────────────────────

class TestNarrativePhysicsSnapshotEngine:
    def test_snapshot_episodes_constant(self):
        eng = NarrativePhysicsSnapshotEngine()
        assert eng.SNAPSHOT_EPISODES == frozenset({1, 4, 8, 12, 16})

    def test_should_snapshot_true(self):
        eng = NarrativePhysicsSnapshotEngine()
        for ep in [1, 4, 8, 12, 16]:
            assert eng.should_snapshot(ep) is True

    def test_should_snapshot_false(self):
        eng = NarrativePhysicsSnapshotEngine()
        for ep in [2, 3, 5, 6, 7, 9, 10, 11, 13, 14, 15]:
            assert eng.should_snapshot(ep) is False

    def test_take_snapshot_returns_physics_snapshot(self):
        eng = NarrativePhysicsSnapshotEngine()
        cfg = _FakeSeriesConfig()
        snap = eng.take_snapshot(cfg, episode_n=4)
        assert isinstance(snap, PhysicsSnapshot)
        assert snap.episode_idx == 4
        assert 0.0 <= snap.fitness_score <= 10.0

    def test_take_snapshot_has_timestamp(self):
        eng = NarrativePhysicsSnapshotEngine()
        cfg = _FakeSeriesConfig()
        snap = eng.take_snapshot(cfg, episode_n=8)
        assert snap.snapshot_timestamp != ""

    def test_run_series_returns_snapshot_run_result(self):
        eng = NarrativePhysicsSnapshotEngine()
        cfg = _FakeSeriesConfig(total_episodes=16)
        result = eng.run_series(cfg)
        assert isinstance(result, SnapshotRunResult)

    def test_run_series_snapshot_count(self):
        eng = NarrativePhysicsSnapshotEngine()
        cfg = _FakeSeriesConfig(total_episodes=16)
        result = eng.run_series(cfg)
        assert len(result.snapshots) == 5  # {1, 4, 8, 12, 16}

    def test_run_series_short_series(self):
        """총 화수 6화 → SNAPSHOT_EPISODES 교집합 {1, 4} 만 실행."""
        eng = NarrativePhysicsSnapshotEngine()
        cfg = _FakeSeriesConfig(total_episodes=6)
        result = eng.run_series(cfg)
        episode_idxs = [s.episode_idx for s in result.snapshots]
        assert 1 in episode_idxs
        assert 4 in episode_idxs
        assert 8 not in episode_idxs

    def test_run_series_mean_fitness_computed(self):
        eng = NarrativePhysicsSnapshotEngine()
        cfg = _FakeSeriesConfig(total_episodes=16)
        result = eng.run_series(cfg)
        assert result.mean_fitness > 0.0

    def test_run_series_overall_pass(self):
        eng = NarrativePhysicsSnapshotEngine()
        cfg = _FakeSeriesConfig(total_episodes=16)
        result = eng.run_series(cfg)
        assert result.overall_pass == (result.mean_fitness >= 6.0)

    def test_run_series_has_trace(self):
        eng = NarrativePhysicsSnapshotEngine()
        cfg = _FakeSeriesConfig(total_episodes=16)
        result = eng.run_series(cfg)
        assert len(result.execution_trace) > 0
        assert any("NarrativePhysicsSnapshotEngine" in t for t in result.execution_trace)
