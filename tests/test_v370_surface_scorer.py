"""test_v370_surface_scorer.py — ReaderSurfaceScorer 테스트 (V370)"""
import pytest
from literary_system.prose.surface_scorer import ReaderSurfaceScorer, SurfaceScore


class TestSurfaceScoreFields:
    def test_all_axes_present(self):
        s = SurfaceScore()
        for ax in ("anti_llm","emotion","sensory","rhythm","consistency","structure"):
            assert hasattr(s, ax)

    def test_avg_mean_of_six(self):
        s = SurfaceScore(anti_llm=10, emotion=10, sensory=10,
                         rhythm=10, consistency=10, structure=10)
        assert s.avg == pytest.approx(10.0)

    def test_avg_zero_all(self):
        s = SurfaceScore()
        assert s.avg == pytest.approx(0.0)

    def test_min_score(self):
        s = SurfaceScore(anti_llm=9, emotion=8, sensory=7,
                         rhythm=9, consistency=9, structure=9)
        assert s.min_score == pytest.approx(7.0)

    def test_passes_above_threshold(self):
        s = SurfaceScore(anti_llm=9.5, emotion=9.5, sensory=9.5,
                         rhythm=9.5, consistency=9.5, structure=9.5)
        assert s.passes(9.0) is True

    def test_passes_below_threshold(self):
        s = SurfaceScore(anti_llm=8.0, emotion=8.0, sensory=8.0,
                         rhythm=8.0, consistency=8.0, structure=8.0)
        assert s.passes(9.0) is False

    def test_report_has_all_keys(self):
        s = SurfaceScore()
        r = s.report()
        for k in ("anti_llm","emotion","sensory","rhythm","consistency","structure","avg"):
            assert k in r


class TestReaderSurfaceScorerScore:
    def setup_method(self):
        self.scorer = ReaderSurfaceScorer(min_score=9.0)

    def test_all_none_defaults(self):
        s = self.scorer.score()
        assert isinstance(s, SurfaceScore)
        assert s.avg == pytest.approx(5.0)

    def test_anti_llm_10_scores_high(self):
        s = self.scorer.score(anti_llm_score=10.0)
        assert s.anti_llm == pytest.approx(10.0)

    def test_anti_llm_0_scores_low(self):
        s = self.scorer.score(anti_llm_score=0.0)
        assert s.anti_llm == pytest.approx(0.0)

    def test_pipeline_passed_true_structure_10(self):
        s = self.scorer.score(pipeline_passed=True)
        assert s.structure == pytest.approx(10.0)

    def test_pipeline_passed_false_structure_0(self):
        s = self.scorer.score(pipeline_passed=False)
        assert s.structure == pytest.approx(0.0)

    def test_pipeline_none_structure_5(self):
        s = self.scorer.score(pipeline_passed=None)
        assert s.structure == pytest.approx(5.0)

    def test_emotion_intensity_1_0(self):
        s = self.scorer.score(emotion_intensity=1.0)
        assert s.emotion == pytest.approx(10.0)

    def test_emotion_intensity_0_0(self):
        s = self.scorer.score(emotion_intensity=0.0)
        assert s.emotion == pytest.approx(5.0)

    def test_sensory_density_optimal(self):
        s = self.scorer.score(sensory_density=0.3)
        assert s.sensory == pytest.approx(10.0)

    def test_sensory_density_zero(self):
        s = self.scorer.score(sensory_density=0.0)
        assert s.sensory <= 5.0

    def test_passes_all_ten(self):
        s = self.scorer.score(
            anti_llm_score=10.0, emotion_intensity=1.0,
            sensory_density=0.3, rhythm_score=10.0,
            consistency_score=10.0, pipeline_passed=True,
        )
        assert s.passes(9.0) is True

    def test_passes_method(self):
        s = SurfaceScore(anti_llm=9.5, emotion=9.5, sensory=9.5,
                         rhythm=9.5, consistency=9.5, structure=9.5)
        assert self.scorer.passes(s) is True

    def test_min_score_respected(self):
        strict = ReaderSurfaceScorer(min_score=9.5)
        s = SurfaceScore(anti_llm=9.3, emotion=9.3, sensory=9.3,
                         rhythm=9.3, consistency=9.3, structure=9.3)
        assert strict.passes(s) is False
