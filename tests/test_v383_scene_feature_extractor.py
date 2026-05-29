"""V383 — SceneFeatureExtractor + PrivacyGuard 테스트."""
import pytest
from literary_system.physics.scene_feature_extractor import (
    SceneFeatureExtractor, SceneFeature, PrivacyGuardViolation
)


GOOD_REPORT = {
    'anti_llm': 0.7, 'emotion': 0.6, 'sensory': 0.65,
    'rhythm': 0.7, 'consistency': 0.75, 'structure': 0.65,
}


@pytest.fixture
def extractor():
    return SceneFeatureExtractor()


class TestSceneFeatureExtractor:
    def test_returns_scene_feature(self, extractor):
        f = extractor.extract(GOOD_REPORT)
        assert isinstance(f, SceneFeature)

    def test_13_fields(self, extractor):
        f = extractor.extract(GOOD_REPORT)
        assert len(f) == 13

    def test_prose_group_values(self, extractor):
        f = extractor.extract(GOOD_REPORT)
        assert f.anti_llm_score    == pytest.approx(0.7)
        assert f.emotion_score     == pytest.approx(0.6)
        assert f.sensory_score     == pytest.approx(0.65)
        assert f.rhythm_score      == pytest.approx(0.7)
        assert f.consistency_score == pytest.approx(0.75)
        assert f.structure_score   == pytest.approx(0.65)

    def test_physics_group_values(self, extractor):
        f = extractor.extract(
            GOOD_REPORT,
            conflict_intensity=0.5,
            scene_energy_ratio=0.8,
            motif_residue_score=0.4,
            curiosity_gradient=0.6,
        )
        assert f.conflict_intensity  == pytest.approx(0.5)
        assert f.scene_energy_ratio  == pytest.approx(0.8)
        assert f.motif_residue_score == pytest.approx(0.4)
        assert f.curiosity_gradient  == pytest.approx(0.6)

    def test_trajectory_group_values(self, extractor):
        f = extractor.extract(
            GOOD_REPORT,
            reader_uncertainty=0.55,
            reader_pull=0.6,
            reader_afterimage=0.45,
        )
        assert f.reader_uncertainty == pytest.approx(0.55)
        assert f.reader_pull        == pytest.approx(0.6)
        assert f.reader_afterimage  == pytest.approx(0.45)

    def test_as_vector_length(self, extractor):
        f = extractor.extract(GOOD_REPORT)
        assert len(f.as_vector()) == 13

    def test_privacy_guard_long_string(self, extractor):
        bad_report = {**GOOD_REPORT, 'text': 'x' * 200}
        with pytest.raises(PrivacyGuardViolation):
            extractor.extract(bad_report)

    def test_privacy_guard_short_ok(self, extractor):
        ok_report = {**GOOD_REPORT, 'label': 'ok'}
        f = extractor.extract(ok_report)
        assert isinstance(f, SceneFeature)

    def test_missing_prose_key_defaults_zero(self, extractor):
        f = extractor.extract({'anti_llm': 0.5})
        assert f.emotion_score == pytest.approx(0.0)

    def test_all_defaults_zero_on_empty(self, extractor):
        f = extractor.extract({})
        assert all(v == 0.0 for v in f.as_vector())

    def test_vector_order(self, extractor):
        f = extractor.extract(GOOD_REPORT,
            conflict_intensity=0.3, scene_energy_ratio=0.4,
            motif_residue_score=0.5, curiosity_gradient=0.6,
            reader_uncertainty=0.7, reader_pull=0.8, reader_afterimage=0.9,
        )
        v = f.as_vector()
        # 첫 6개: prose, 다음 4개: physics, 마지막 3개: trajectory
        assert v[6]  == pytest.approx(0.3)  # conflict
        assert v[10] == pytest.approx(0.7)  # reader_uncertainty
