"""V408 — NarrativeConductor + SeriesSnapshot 테스트 (33 tests)."""
import tempfile
import pytest

from literary_system.orchestrators.narrative_conductor import (
    NarrativeConductor, SeriesSnapshot, EpisodeResult, _advance_tensor, _update_debt
)
from literary_system.memory.narrative_memory_store import SeriesNotFound
from literary_system.episode.episode_state import SeriesConfig
from literary_system.physics.coefficient_store import PhysicsCoefficientStore


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def conductor(tmp_path):
    return NarrativeConductor(memory_root=str(tmp_path / "memory"))


@pytest.fixture
def cfg():
    return SeriesConfig(title="테스트 드라마", total_episodes=16)


# ── SeriesSnapshot 테스트 ─────────────────────────────────────────────────────

class TestSeriesSnapshot:
    def test_next_episode(self):
        snap = SeriesSnapshot(
            series_id="s1", last_episode=3,
            pipeline_state={}, nkg=None,
            debt_ledger={}, coefficient_store=PhysicsCoefficientStore(),
            trajectory={"SP": 0.5, "RU": 0.2, "ET": 0.0, "RD": 0.8},
        )
        assert snap.next_episode == 4

    def test_add_trace(self):
        snap = SeriesSnapshot(
            series_id="s1", last_episode=0,
            pipeline_state={}, nkg=None,
            debt_ledger={}, coefficient_store=PhysicsCoefficientStore(),
            trajectory={},
        )
        snap.add_trace("test trace")
        assert "test trace" in snap.execution_trace

    def test_nkg_none_by_default(self):
        snap = SeriesSnapshot(
            series_id="s1", last_episode=0,
            pipeline_state={}, nkg=None,
            debt_ledger={}, coefficient_store=PhysicsCoefficientStore(),
            trajectory={},
        )
        assert snap.nkg is None


# ── start_series 테스트 ───────────────────────────────────────────────────────

class TestStartSeries:
    def test_returns_series_snapshot(self, conductor, cfg):
        snap = conductor.start_series(cfg, "drama_001")
        assert isinstance(snap, SeriesSnapshot)

    def test_series_id_set(self, conductor, cfg):
        snap = conductor.start_series(cfg, "drama_001")
        assert snap.series_id == "drama_001"

    def test_last_episode_zero(self, conductor, cfg):
        snap = conductor.start_series(cfg, "drama_001")
        assert snap.last_episode == 0

    def test_trajectory_initialized(self, conductor, cfg):
        snap = conductor.start_series(cfg, "drama_001")
        assert "SP" in snap.trajectory
        assert "RU" in snap.trajectory
        assert "ET" in snap.trajectory
        assert "RD" in snap.trajectory

    def test_trace_has_entries(self, conductor, cfg):
        snap = conductor.start_series(cfg, "drama_001")
        assert len(snap.execution_trace) > 0

    def test_duplicate_series_raises(self, conductor, cfg):
        conductor.start_series(cfg, "drama_dup")
        with pytest.raises(FileExistsError):
            conductor.start_series(cfg, "drama_dup")

    def test_coefficient_store_initialized(self, conductor, cfg):
        snap = conductor.start_series(cfg, "drama_001")
        assert isinstance(snap.coefficient_store, PhysicsCoefficientStore)

    def test_seed_metadata_stored(self, conductor, cfg):
        snap = conductor.start_series(cfg, "drama_001", seed_metadata={"genre": "thriller"})
        meta = conductor._memory.get_series_metadata("drama_001")
        assert meta.get("genre") == "thriller"


# ── write_episode 테스트 ──────────────────────────────────────────────────────

class TestWriteEpisode:
    def test_returns_episode_result(self, conductor, cfg):
        conductor.start_series(cfg, "drama_w")
        result = conductor.write_episode("drama_w", 1)
        assert isinstance(result, EpisodeResult)

    def test_episode_idx_set(self, conductor, cfg):
        conductor.start_series(cfg, "drama_w")
        result = conductor.write_episode("drama_w", 1)
        assert result.episode_idx == 1

    def test_memory_path_set(self, conductor, cfg):
        conductor.start_series(cfg, "drama_w")
        result = conductor.write_episode("drama_w", 1)
        assert result.memory_path != ""

    def test_sequential_episodes(self, conductor, cfg):
        conductor.start_series(cfg, "drama_seq")
        conductor.write_episode("drama_seq", 1)
        conductor.write_episode("drama_seq", 2)
        conductor.write_episode("drama_seq", 3)
        latest = conductor._memory.get_latest_episode("drama_seq")
        assert latest.episode_idx == 3

    def test_trace_has_entries(self, conductor, cfg):
        conductor.start_series(cfg, "drama_t")
        result = conductor.write_episode("drama_t", 1)
        assert len(result.execution_trace) > 0

    def test_no_series_raises(self, conductor):
        with pytest.raises(SeriesNotFound):
            conductor.write_episode("nonexistent_series", 1)

    def test_tensor_advances(self, conductor, cfg):
        conductor.start_series(cfg, "drama_tensor")
        result1 = conductor.write_episode("drama_tensor", 1)
        mem1 = conductor._memory.load_episode("drama_tensor", 1)
        # SP는 초기 0.3보다 커야 함
        assert mem1.narrative_tensor["SP"] > 0.3

    def test_scene_outputs_affect_debt(self, conductor, cfg):
        conductor.start_series(cfg, "drama_debt")
        scene_outputs = [
            {"new_foreshadowings": ["f001", "f002"], "paid_foreshadowings": []}
        ]
        conductor.write_episode("drama_debt", 1, scene_outputs=scene_outputs)
        mem = conductor._memory.load_episode("drama_debt", 1)
        assert "f001" in mem.debt_ledger_snapshot["open"]


# ── get_snapshot 테스트 ───────────────────────────────────────────────────────

class TestGetSnapshot:
    def test_returns_series_snapshot(self, conductor, cfg):
        conductor.start_series(cfg, "drama_snap")
        snap = conductor.get_snapshot("drama_snap")
        assert isinstance(snap, SeriesSnapshot)

    def test_last_episode_reflects_writes(self, conductor, cfg):
        conductor.start_series(cfg, "drama_snap2")
        conductor.write_episode("drama_snap2", 1)
        conductor.write_episode("drama_snap2", 2)
        snap = conductor.get_snapshot("drama_snap2")
        assert snap.last_episode == 2

    def test_not_found_raises(self, conductor):
        with pytest.raises(SeriesNotFound):
            conductor.get_snapshot("nonexistent")


# ── 헬퍼 함수 테스트 ─────────────────────────────────────────────────────────

class TestHelperFunctions:
    def test_advance_tensor_sp_increases(self):
        prev = {"SP": 0.3, "RU": 0.1, "ET": 0.0, "RD": 1.0}
        new = _advance_tensor(prev, progress=0.1, scene_outputs=None)
        assert new["SP"] > 0.3

    def test_advance_tensor_rd_decreases(self):
        prev = {"SP": 0.3, "RU": 0.1, "ET": 0.0, "RD": 1.0}
        new = _advance_tensor(prev, progress=0.1, scene_outputs=None)
        assert new["RD"] < 1.0

    def test_advance_tensor_ru_resolved(self):
        prev = {"SP": 0.3, "RU": 0.5, "ET": 0.0, "RD": 0.8}
        scene_outputs = [{"residue_resolved": True}, {"residue_resolved": True}]
        new = _advance_tensor(prev, progress=0.5, scene_outputs=scene_outputs)
        # 2개 해결 → RU 감소
        assert new["RU"] < 0.5 + 0.03 * 2  # baseline보다 낮아야

    def test_update_debt_new_foreshadowing(self):
        prev = {"open": [], "paid": [], "defaulted": []}
        scene_outputs = [{"new_foreshadowings": ["f001"], "paid_foreshadowings": []}]
        new_debt = _update_debt(prev, scene_outputs)
        assert "f001" in new_debt["open"]

    def test_update_debt_pay_foreshadowing(self):
        prev = {"open": ["f001"], "paid": [], "defaulted": []}
        scene_outputs = [{"new_foreshadowings": [], "paid_foreshadowings": ["f001"]}]
        new_debt = _update_debt(prev, scene_outputs)
        assert "f001" not in new_debt["open"]
        assert "f001" in new_debt["paid"]
