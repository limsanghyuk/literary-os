"""Tests — V392 EpisodePlanner + MicroPlotMatrix."""
import pytest
from literary_system.episode.episode_state import (
    ActPosition, NarrativeStateTensor, SeriesConfig
)
from literary_system.episode.episode_planner import EpisodePlanner, EpisodePlan
from literary_system.episode.microplot_matrix import MicroPlotMatrix


@pytest.fixture
def cfg():
    return SeriesConfig("TestDrama", total_episodes=16, protagonist_ids=["A","B"])

@pytest.fixture
def tensor(cfg):
    return NarrativeStateTensor(
        total_episodes=16, active_characters=["A","B","C"],
        conflict_pressure=0.5, avg_emotional_momentum=0.5,
        scene_energy_required=0.6, avg_curiosity_gradient=0.6,
    )

@pytest.fixture
def planner():
    return EpisodePlanner()


class TestEpisodePlanner:
    def test_plan_returns_plan(self, planner, cfg, tensor):
        plan = planner.plan(cfg, 0, tensor)
        assert isinstance(plan, EpisodePlan)

    def test_k_in_range(self, planner, cfg, tensor):
        for i in range(16):
            ep_state = planner.plan(cfg, i, tensor).to_episode_state()
            tensor.push_episode(ep_state)
            k = ep_state.microplot_count
            assert 2 <= k <= 8, f"K={k} out of range at ep{i}"

    def test_setup_act_at_start(self, planner, cfg, tensor):
        plan = planner.plan(cfg, 0, tensor)
        assert plan.act_position == ActPosition.SETUP

    def test_collision_act_in_middle(self, planner, cfg, tensor):
        for i in range(8):
            tensor.push_episode(planner.plan(cfg, i, tensor).to_episode_state())
        plan = planner.plan(cfg, 8, tensor)
        assert plan.act_position in (ActPosition.COLLISION, ActPosition.PRESSURE, ActPosition.REVERSAL)

    def test_residue_act_at_end(self, planner, cfg, tensor):
        plan = planner.plan(cfg, 15, tensor)
        assert plan.act_position == ActPosition.RESIDUE

    def test_slot_functions_length(self, planner, cfg, tensor):
        plan = planner.plan(cfg, 0, tensor)
        assert len(plan.slot_functions) == plan.microplot_count

    def test_emotional_targets_length(self, planner, cfg, tensor):
        plan = planner.plan(cfg, 0, tensor)
        assert len(plan.emotional_targets) == plan.microplot_count

    def test_to_episode_state(self, planner, cfg, tensor):
        plan = planner.plan(cfg, 0, tensor)
        ep = plan.to_episode_state()
        assert ep.microplot_count == plan.microplot_count

    def test_planning_trace(self, planner, cfg, tensor):
        plan = planner.plan(cfg, 0, tensor)
        assert len(plan.planning_trace) > 0

    def test_scene_budget_positive(self, planner, cfg, tensor):
        plan = planner.plan(cfg, 5, tensor)
        assert plan.total_scene_budget > 0

    def test_24ep_config(self, planner):
        cfg24 = SeriesConfig("Long", total_episodes=24)
        t24 = NarrativeStateTensor(total_episodes=24, active_characters=["A"])
        plan = planner.plan(cfg24, 12, t24)
        assert 2 <= plan.microplot_count <= 8


class TestMicroPlotMatrix:
    @pytest.fixture
    def matrix(self, planner, cfg, tensor):
        plans = []
        for i in range(16):
            plan = planner.plan(cfg, i, tensor)
            plans.append(plan)
            tensor.push_episode(plan.to_episode_state())
        return MicroPlotMatrix.build(plans)

    def test_episode_count(self, matrix):
        assert matrix.episode_count == 16

    def test_total_microplots_positive(self, matrix):
        assert matrix.total_microplot_count > 0

    def test_k_curve_length(self, matrix):
        assert len(matrix.k_curve()) == 16

    def test_scene_budget_curve_length(self, matrix):
        assert len(matrix.scene_budget_curve()) == 16

    def test_get_k(self, matrix):
        k = matrix.get_k(0)
        assert 2 <= k <= 8

    def test_out_of_range(self, matrix):
        with pytest.raises(IndexError):
            matrix.get_k(99)

    def test_to_csv(self, matrix):
        csv = matrix.to_csv()
        assert "episode_idx" in csv
        assert "microplot_count" in csv

    def test_summary(self, matrix):
        s = matrix.summary()
        assert "k_avg" in s
        assert s["episode_count"] == 16
        assert s["k_min"] >= 2
        assert s["k_max"] <= 8

    def test_total_scene_budget_positive(self, matrix):
        assert matrix.total_scene_budget > 0
