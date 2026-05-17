"""V398 Narrative Attention Economy Tests"""
import pytest
from literary_system.longform.attention_economy import (
    SceneAttentionValue, NarrativeAttentionEconomy, FatigueReport
)

class TestSceneAttentionValue:
    def _make(self, **kw):
        defaults = dict(
            scene_id="S001",
            emotional_reward=0.6, curiosity_reward=0.5,
            payoff_reward=0.4, agency_reward=0.3,
            cognitive_load=0.2, confusion_cost=0.1, repetition_cost=0.1
        )
        defaults.update(kw)
        return SceneAttentionValue(**defaults)

    def test_creation(self):
        s = self._make()
        assert s.scene_id == "S001"

    def test_net_value_formula(self):
        s = self._make(
            emotional_reward=1.0, curiosity_reward=1.0,
            payoff_reward=1.0, agency_reward=1.0,
            cognitive_load=0.0, confusion_cost=0.0, repetition_cost=0.0
        )
        assert abs(s.net_value - 4.0) < 1e-9

    def test_net_value_with_costs(self):
        s = self._make(
            emotional_reward=1.0, curiosity_reward=0.0,
            payoff_reward=0.0, agency_reward=0.0,
            cognitive_load=0.5, confusion_cost=0.0, repetition_cost=0.0
        )
        assert abs(s.net_value - 0.5) < 1e-9

    def test_negative_net_value_possible(self):
        s = self._make(
            emotional_reward=0.0, curiosity_reward=0.0,
            payoff_reward=0.0, agency_reward=0.0,
            cognitive_load=1.0, confusion_cost=1.0, repetition_cost=1.0
        )
        assert s.net_value < 0

    def test_is_draining_property(self):
        s = self._make(
            emotional_reward=0.0, curiosity_reward=0.0,
            payoff_reward=0.0, agency_reward=0.0,
            cognitive_load=1.0, confusion_cost=1.0, repetition_cost=1.0
        )
        assert s.is_draining is True

    def test_good_scene_not_draining(self):
        s = self._make(emotional_reward=0.8, curiosity_reward=0.6,
                       cognitive_load=0.1, confusion_cost=0.0, repetition_cost=0.0)
        assert s.is_draining is False

class TestNarrativeAttentionEconomy:
    def setup_method(self):
        self.economy = NarrativeAttentionEconomy()

    def test_build_synthetic_scenes_count(self):
        scenes = NarrativeAttentionEconomy.build_synthetic_scenes(16, 8)
        assert len(scenes) == 16 * 8

    def test_synthetic_scenes_are_attention_values(self):
        scenes = NarrativeAttentionEconomy.build_synthetic_scenes(16, 4)
        for s in scenes:
            assert isinstance(s, SceneAttentionValue)

    def test_analyze_returns_fatigue_report(self):
        scenes = NarrativeAttentionEconomy.build_synthetic_scenes(16, 8)
        report = self.economy.analyze(scenes, episode_count=16)
        assert isinstance(report, FatigueReport)

    def test_report_has_mid_season_fatigue_risk(self):
        scenes = NarrativeAttentionEconomy.build_synthetic_scenes(16, 8)
        report = self.economy.analyze(scenes, episode_count=16)
        assert hasattr(report, 'mid_season_fatigue_risk')

    def test_report_has_finale_fatigue_risk(self):
        scenes = NarrativeAttentionEconomy.build_synthetic_scenes(16, 8)
        report = self.economy.analyze(scenes, episode_count=16)
        assert hasattr(report, 'finale_fatigue_risk')

    def test_synthetic_passes_mid_season_threshold(self):
        scenes = NarrativeAttentionEconomy.build_synthetic_scenes(16, 8)
        report = self.economy.analyze(scenes, episode_count=16)
        assert report.mid_season_fatigue_risk < 0.4

    def test_synthetic_passes_finale_threshold(self):
        scenes = NarrativeAttentionEconomy.build_synthetic_scenes(16, 8)
        report = self.economy.analyze(scenes, episode_count=16)
        assert report.finale_fatigue_risk < 0.3

    def test_pass_gate_field_exists(self):
        scenes = NarrativeAttentionEconomy.build_synthetic_scenes(16, 8)
        report = self.economy.analyze(scenes, episode_count=16)
        assert hasattr(report, 'pass_gate')

    def test_synthetic_passes_gate(self):
        scenes = NarrativeAttentionEconomy.build_synthetic_scenes(16, 8)
        report = self.economy.analyze(scenes, episode_count=16)
        assert report.pass_gate is True

    def test_all_high_cost_scenes_fail_gate(self):
        scenes = [
            SceneAttentionValue(
                scene_id=f"S{i}",
                emotional_reward=0.0, curiosity_reward=0.0,
                payoff_reward=0.0, agency_reward=0.0,
                cognitive_load=1.0, confusion_cost=1.0, repetition_cost=1.0
            ) for i in range(128)
        ]
        report = self.economy.analyze(scenes, episode_count=16)
        assert report.pass_gate is False

    def test_episode_attention_values_length(self):
        scenes = NarrativeAttentionEconomy.build_synthetic_scenes(16, 8)
        report = self.economy.analyze(scenes, episode_count=16)
        assert len(report.episode_attention_values) == 16

    def test_episode_ending_hook_strengths(self):
        scenes = NarrativeAttentionEconomy.build_synthetic_scenes(16, 8)
        report = self.economy.analyze(scenes, episode_count=16)
        assert hasattr(report, 'episode_ending_hook_strengths')
        assert len(report.episode_ending_hook_strengths) == 16

    def test_empty_scenes_returns_report(self):
        report = self.economy.analyze([], episode_count=16)
        assert isinstance(report, FatigueReport)

