"""V396 Dialogue Pragmatics Engine Tests"""
import pytest
from literary_system.longform.dialogue_pragmatics import (
    DialogueProfile, DialogueForce, DialoguePragmaticsEngine, DialogueReport
)

class TestDialogueProfile:
    def test_creation(self):
        p = DialogueProfile(character_id="A")
        assert p.character_id == "A"

    def test_default_values(self):
        p = DialogueProfile(character_id="B")
        assert 0.0 <= p.honorific_distance <= 1.0
        assert 0.0 <= p.subtext_density <= 1.0

    def test_custom_values(self):
        p = DialogueProfile(
            character_id="C",
            honorific_distance=0.9,
            subtext_density=0.7,
            silence_ratio=0.3,
            expository_ratio=0.05
        )
        assert p.honorific_distance == 0.9
        assert p.expository_ratio == 0.05

    def test_all_fields_accessible(self):
        p = DialogueProfile(character_id="D")
        assert hasattr(p, 'honorific_distance')
        assert hasattr(p, 'speech_level_variance')
        assert hasattr(p, 'subtext_density')
        assert hasattr(p, 'silence_ratio')
        assert hasattr(p, 'expository_ratio')

class TestDialogueForce:
    def test_creation(self):
        f = DialogueForce(scene_id="ep1_sc2")
        assert f.scene_id == "ep1_sc2"

    def test_total_force_zero_by_default(self):
        f = DialogueForce(scene_id="s1")
        assert f.total_force == 0.0

    def test_total_force_sum(self):
        f = DialogueForce(
            scene_id="s1", subtext_gap=0.5, relation_pressure=0.3,
            speech_level_shift=0.1, withheld_information=0.2,
            silence_weight=0.1, rank_pressure=0.1
        )
        expected = 0.5 + 0.3 + 0.1 + 0.2 + 0.1 + 0.1
        assert abs(f.total_force - expected) < 1e-9

class TestDialoguePragmaticsEngine:
    def setup_method(self):
        self.engine = DialoguePragmaticsEngine()
        self.char_ids = ["A", "B", "C"]

    def test_build_synthetic_profiles(self):
        profiles = DialoguePragmaticsEngine.build_synthetic_profiles(self.char_ids)
        assert len(profiles) == 3
        for cid in self.char_ids:
            assert cid in profiles

    def test_synthetic_profiles_are_dialogue_profile(self):
        profiles = DialoguePragmaticsEngine.build_synthetic_profiles(self.char_ids)
        for p in profiles.values():
            assert isinstance(p, DialogueProfile)

    def test_analyze_profiles_returns_dialogue_report(self):
        profiles = DialoguePragmaticsEngine.build_synthetic_profiles(self.char_ids)
        report = self.engine.analyze_profiles(profiles, [])
        assert isinstance(report, DialogueReport)

    def test_report_has_is_consistent(self):
        profiles = DialoguePragmaticsEngine.build_synthetic_profiles(self.char_ids)
        report = self.engine.analyze_profiles(profiles, [])
        assert hasattr(report, 'is_consistent')

    def test_is_consistent_is_bool(self):
        profiles = DialoguePragmaticsEngine.build_synthetic_profiles(self.char_ids)
        report = self.engine.analyze_profiles(profiles, [])
        assert isinstance(report.is_consistent, bool)

    def test_pass_gate_property(self):
        profiles = DialoguePragmaticsEngine.build_synthetic_profiles(self.char_ids)
        report = self.engine.analyze_profiles(profiles, [])
        assert isinstance(report.pass_gate, bool)

    def test_engine_is_diagnostics_only(self):
        profiles = DialoguePragmaticsEngine.build_synthetic_profiles(self.char_ids)
        report = self.engine.analyze_profiles(profiles, [])
        assert report is not None

    def test_synthetic_profiles_pass_consistency(self):
        # Synthetic profiles should have low speech_level_variance and expository_ratio
        profiles = DialoguePragmaticsEngine.build_synthetic_profiles(self.char_ids)
        report = self.engine.analyze_profiles(profiles, [])
        assert report.is_consistent is True

    def test_empty_char_list(self):
        profiles = DialoguePragmaticsEngine.build_synthetic_profiles([])
        assert len(profiles) == 0

    def test_high_variance_fails_consistency(self):
        profiles = {
            "A": DialogueProfile(character_id="A", speech_level_variance=0.9),
            "B": DialogueProfile(character_id="B", speech_level_variance=0.8),
        }
        report = self.engine.analyze_profiles(profiles, [])
        assert report.is_consistent is False

    def test_honorific_distance_range_in_synthetic(self):
        profiles = DialoguePragmaticsEngine.build_synthetic_profiles(self.char_ids)
        for p in profiles.values():
            assert 0.0 <= p.honorific_distance <= 1.0

    def test_report_has_character_profiles(self):
        profiles = DialoguePragmaticsEngine.build_synthetic_profiles(self.char_ids)
        report = self.engine.analyze_profiles(profiles, [])
        assert hasattr(report, 'character_profiles')

