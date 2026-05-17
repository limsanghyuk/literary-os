"""V370 ReaderSurfaceScorer 확장 테스트."""
import pytest
from literary_system.prose.surface_scorer import ReaderSurfaceScorer, SurfaceScore


class TestScorerConstruction:
    def test_default_threshold(self):
        s = ReaderSurfaceScorer()
        assert s is not None

    def test_custom_threshold(self):
        s = ReaderSurfaceScorer(min_score=7.0)
        assert s is not None

    def test_strict_threshold(self):
        s = ReaderSurfaceScorer(min_score=9.5)
        assert s is not None


class TestSurfaceScoreFields:
    def _make_score(self, **kw):
        s = ReaderSurfaceScorer(min_score=7.0)
        defaults = dict(
            anti_llm_score=9.0,
            emotion_intensity=0.6,
            sensory_density=0.3,
            rhythm_score=8.5,
            consistency_score=9.0,
            pipeline_passed=True,
        )
        defaults.update(kw)
        return s.score(**defaults)

    def test_score_returns_surface_score(self):
        assert isinstance(self._make_score(), SurfaceScore)

    def test_anti_llm_field(self):
        sc = self._make_score(anti_llm_score=9.0)
        assert sc.anti_llm == 9.0

    def test_rhythm_field(self):
        sc = self._make_score(rhythm_score=8.5)
        assert sc.rhythm == 8.5

    def test_consistency_field(self):
        sc = self._make_score(consistency_score=9.0)
        assert sc.consistency == 9.0

    def test_avg_is_float(self):
        assert isinstance(self._make_score().avg, float)

    def test_avg_bounded(self):
        sc = self._make_score()
        assert 0.0 <= sc.avg <= 10.0

    def test_structure_field_present(self):
        sc = self._make_score()
        assert hasattr(sc, "structure")

    def test_emotion_field_present(self):
        sc = self._make_score()
        assert hasattr(sc, "emotion")

    def test_sensory_field_present(self):
        sc = self._make_score()
        assert hasattr(sc, "sensory")


class TestScorerPasses:
    def _scorer(self, threshold=7.0):
        return ReaderSurfaceScorer(min_score=threshold)

    def test_passes_with_perfect_scores(self):
        sc = self._scorer().score(
            anti_llm_score=10.0, emotion_intensity=1.0,
            sensory_density=0.3, rhythm_score=10.0,
            consistency_score=10.0, pipeline_passed=True,
        )
        assert sc.passes(7.0)

    def test_passes_uses_threshold_param(self):
        sc = self._scorer(9.0).score(
            anti_llm_score=9.5, emotion_intensity=0.7,
            sensory_density=0.3, rhythm_score=9.0,
            consistency_score=9.0, pipeline_passed=True,
        )
        assert sc.passes(7.0)

    def test_pipeline_failed_lowers_score(self):
        s = self._scorer()
        sc_ok  = s.score(anti_llm_score=9.0, emotion_intensity=0.6,
                         sensory_density=0.3, rhythm_score=8.5,
                         consistency_score=9.0, pipeline_passed=True)
        sc_bad = s.score(anti_llm_score=9.0, emotion_intensity=0.6,
                         sensory_density=0.3, rhythm_score=8.5,
                         consistency_score=9.0, pipeline_passed=False)
        assert sc_ok.avg >= sc_bad.avg

    def test_sensory_density_optimal_high_score(self):
        s = self._scorer()
        sc = s.score(anti_llm_score=9.0, emotion_intensity=0.6,
                     sensory_density=0.25, rhythm_score=8.5,
                     consistency_score=9.0, pipeline_passed=True)
        assert sc.sensory >= 8.0


class TestScorerReport:
    def test_report_is_str(self):
        s = ReaderSurfaceScorer(min_score=7.0)
        sc = s.score(anti_llm_score=9.0, emotion_intensity=0.6,
                     sensory_density=0.3, rhythm_score=8.5,
                     consistency_score=9.0, pipeline_passed=True)
        assert isinstance(sc.report(), dict)

    def test_report_contains_avg(self):
        s = ReaderSurfaceScorer(min_score=7.0)
        sc = s.score(anti_llm_score=9.0, emotion_intensity=0.6,
                     sensory_density=0.3, rhythm_score=8.5,
                     consistency_score=9.0, pipeline_passed=True)
        report = sc.report()
        assert "avg" in report
