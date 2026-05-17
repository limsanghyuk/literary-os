"""V395 Scene Necessity Tests"""
import pytest
from literary_system.longform.scene_necessity import (
    SceneFunctionType, StateDelta, SceneNecessityChecker, NecessityResult, NecessityReport
)

class TestSceneFunctionType:
    def test_all_types_exist(self):
        for t in [SceneFunctionType.NARRATIVE, SceneFunctionType.ATMOSPHERE,
                  SceneFunctionType.EMOTIONAL_RESIDUE]:
            assert t is not None

    def test_is_string_enum(self):
        assert isinstance(SceneFunctionType.NARRATIVE, str)

class TestStateDelta:
    def test_creation_all_zeros(self):
        d = StateDelta()
        assert d.changed_dimensions == 0

    def test_changed_dimensions_counts_above_threshold(self):
        d = StateDelta(belief=0.1, emotion=0.1)
        assert d.changed_dimensions == 2

    def test_threshold_is_005(self):
        assert StateDelta.THRESHOLD == 0.05

    def test_below_threshold_not_changed(self):
        d = StateDelta(belief=0.04)
        assert d.changed_dimensions == 0

    def test_all_8_dimensions_changed(self):
        d = StateDelta(belief=0.1, emotion=0.1, relationship=0.1, reveal=0.1,
                       conflict=0.1, motif=0.1, agency=0.1, curiosity=0.1)
        assert d.changed_dimensions == 8

    def test_negative_values_count(self):
        d = StateDelta(belief=-0.1, emotion=-0.1)
        assert d.changed_dimensions == 2

class TestSceneNecessityChecker:
    def setup_method(self):
        self.checker = SceneNecessityChecker()

    def test_weak_threshold_constant(self):
        assert SceneNecessityChecker.WEAK_THRESHOLD == 2

    def test_strong_scene_passes(self):
        delta = StateDelta(belief=0.2, emotion=0.2)
        result = self.checker.check_scene("S001", delta, SceneFunctionType.NARRATIVE)
        assert isinstance(result, NecessityResult)
        assert result.is_necessary is True

    def test_weak_scene_narrative_not_necessary(self):
        delta = StateDelta(belief=0.1)  # only 1 changed
        result = self.checker.check_scene("S002", delta, SceneFunctionType.NARRATIVE)
        assert result.is_necessary is False

    def test_atmosphere_scene_protected(self):
        delta = StateDelta()  # 0 changed dims
        result = self.checker.check_scene("S003", delta, SceneFunctionType.ATMOSPHERE)
        assert result.is_necessary is True

    def test_emotional_residue_protected(self):
        delta = StateDelta()
        result = self.checker.check_scene("S004", delta, SceneFunctionType.EMOTIONAL_RESIDUE)
        assert result.is_necessary is True

    def test_necessity_result_has_action(self):
        delta = StateDelta(belief=0.2, emotion=0.2)
        result = self.checker.check_scene("S005", delta)
        assert result.action == "keep"

    def test_removable_scene(self):
        delta = StateDelta()  # 0 changed dims, NARRATIVE
        result = self.checker.check_scene("S006", delta, SceneFunctionType.NARRATIVE)
        assert result.is_removable is True

    def test_analyze_returns_necessity_report(self):
        deltas = {"S001": StateDelta(belief=0.2, emotion=0.2),
                  "S002": StateDelta()}
        funcs = {"S001": SceneFunctionType.NARRATIVE,
                 "S002": SceneFunctionType.ATMOSPHERE}
        report = self.checker.analyze(deltas, funcs)
        assert isinstance(report, NecessityReport)

    def test_weak_scene_ratio_below_threshold_passes(self):
        deltas = {}
        funcs = {}
        for i in range(20):
            deltas[f"S{i:03d}"] = StateDelta(belief=0.2, emotion=0.2)
            funcs[f"S{i:03d}"] = SceneFunctionType.NARRATIVE
        # Add 1 weak narrative scene (5% of 20 = 5%)
        deltas["WEAK"] = StateDelta()
        funcs["WEAK"] = SceneFunctionType.NARRATIVE
        report = self.checker.analyze(deltas, funcs)
        assert report.pass_gate is True

    def test_all_weak_narrative_fails_gate(self):
        deltas = {}
        funcs = {}
        for i in range(10):
            deltas[f"S{i}"] = StateDelta()
            funcs[f"S{i}"] = SceneFunctionType.NARRATIVE
        report = self.checker.analyze(deltas, funcs)
        assert report.pass_gate is False

    def test_report_has_weak_scene_ratio(self):
        report = self.checker.analyze({"S": StateDelta(belief=0.2, emotion=0.2)})
        assert hasattr(report, 'weak_scene_ratio')

    def test_report_removable_scenes(self):
        deltas = {"S1": StateDelta(), "S2": StateDelta(belief=0.2, emotion=0.2)}
        funcs = {"S1": SceneFunctionType.NARRATIVE, "S2": SceneFunctionType.NARRATIVE}
        report = self.checker.analyze(deltas, funcs)
        assert "S1" in report.removable_scenes

