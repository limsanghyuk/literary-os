"""Tests — V391 EpisodeState."""
import pytest
from literary_system.episode.episode_state import (
    ActPosition, MicroPlotSlot, EpisodeState, NarrativeStateTensor, SeriesConfig
)


class TestActPosition:
    def test_values(self):
        assert ActPosition.SETUP.value == "SETUP"
        assert ActPosition.COLLISION.value == "COLLISION"
    def test_all_five(self):
        assert len(ActPosition) == 5


class TestMicroPlotSlot:
    def test_default_filled(self):
        s = MicroPlotSlot(0, scene_budget=5, reveal_budget=0.2,
                          emotional_target=0.5, conflict_weight=0.4, act_function="intro")
        assert s.filled is False
    def test_fields(self):
        s = MicroPlotSlot(1, 6, 0.3, 0.7, 0.5, "escalation")
        assert s.slot_idx == 1
        assert s.scene_budget == 6


class TestEpisodeState:
    @pytest.fixture
    def ep(self):
        return EpisodeState(episode_idx=0, act_position=ActPosition.SETUP)

    def test_initial_microplot_count(self, ep):
        assert ep.microplot_count == 0

    def test_add_slots(self, ep):
        ep.microplot_slots.append(
            MicroPlotSlot(0, 5, 0.2, 0.5, 0.4, "intro")
        )
        assert ep.microplot_count == 1

    def test_total_scene_budget(self, ep):
        ep.microplot_slots = [
            MicroPlotSlot(0, 5, 0.2, 0.5, 0.4, "intro"),
            MicroPlotSlot(1, 7, 0.1, 0.6, 0.5, "pressure"),
        ]
        assert ep.total_scene_budget == 12

    def test_mark_slot_filled(self, ep):
        ep.microplot_slots = [MicroPlotSlot(0, 5, 0.2, 0.5, 0.4, "intro")]
        ep.mark_slot_filled(0)
        assert ep.microplot_slots[0].filled is True

    def test_all_slots_filled_empty(self, ep):
        assert ep.all_slots_filled() is True

    def test_all_slots_filled_false(self, ep):
        ep.microplot_slots = [MicroPlotSlot(0, 5, 0.2, 0.5, 0.4, "intro")]
        assert ep.all_slots_filled() is False

    def test_add_trace(self, ep):
        ep.add_trace("test message")
        assert len(ep.execution_trace) == 1
        assert "[Ep00]" in ep.execution_trace[0]

    def test_episode_idx(self, ep):
        assert ep.episode_idx == 0

    def test_completed_default(self, ep):
        assert ep.completed is False


class TestNarrativeStateTensor:
    @pytest.fixture
    def tensor(self):
        return NarrativeStateTensor(total_episodes=16)

    def test_remaining_budget_initial(self, tensor):
        assert tensor.remaining_reveal_budget == 1.0

    def test_current_episode_idx(self, tensor):
        assert tensor.current_episode_idx == 0

    def test_push_episode(self, tensor):
        ep = EpisodeState(episode_idx=0, act_position=ActPosition.SETUP)
        tensor.push_episode(ep)
        assert tensor.current_episode_idx == 1

    def test_update_from_episode(self, tensor):
        from literary_system.episode.episode_state import CharacterEpisodeState
        ep = EpisodeState(episode_idx=0, act_position=ActPosition.SETUP)
        ep.character_states["A"] = CharacterEpisodeState("A", emotional_level=0.8)
        tensor.update_from_episode(ep)
        assert tensor.avg_emotional_momentum == pytest.approx(0.8, abs=0.01)


class TestSeriesConfig:
    def test_defaults(self):
        cfg = SeriesConfig("TestDrama")
        assert cfg.total_episodes == 16
        assert cfg.runtime_minutes == 60
        assert cfg.genre == "korean_drama"

    def test_24_episode(self):
        cfg = SeriesConfig("Long Drama", total_episodes=24)
        assert cfg.total_episodes == 24

    def test_protagonist_ids(self):
        cfg = SeriesConfig("Drama", protagonist_ids=["A", "B"])
        assert len(cfg.protagonist_ids) == 2
