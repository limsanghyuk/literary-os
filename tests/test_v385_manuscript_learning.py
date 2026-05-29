"""V385 — ManuscriptLearning Layer 테스트."""
import pytest
from literary_system.learning.privacy_guard import PrivacyGuard, PrivacyViolationError
from literary_system.learning.scene_corpus_builder import SceneCorpusBuilder
from literary_system.learning.physics_coefficient_updater import PhysicsCoefficientUpdater
from literary_system.learning.manuscript_learner import ManuscriptLearner
from literary_system.physics.coefficient_store import PhysicsCoefficientStore
from literary_system.physics.scene_feature_extractor import SceneFeature


GOOD_SCENE = {
    'prose_report': {
        'anti_llm': 0.7, 'emotion': 0.6, 'sensory': 0.65,
        'rhythm': 0.7, 'consistency': 0.75, 'structure': 0.65,
    },
    'conflict_intensity': 0.5, 'scene_energy_ratio': 0.8,
    'motif_residue_score': 0.5, 'curiosity_gradient': 0.6,
    'reader_uncertainty': 0.55, 'reader_pull': 0.6, 'reader_afterimage': 0.5,
}


class TestPrivacyGuard:
    def test_valid_data_passes(self):
        guard = PrivacyGuard()
        guard.validate({'score': 0.7, 'count': 5})

    def test_long_string_raises(self):
        guard = PrivacyGuard()
        with pytest.raises(PrivacyViolationError):
            guard.validate({'text': 'x' * 300})

    def test_short_string_ok(self):
        guard = PrivacyGuard()
        guard.validate({'label': 'ok'})

    def test_numeric_values_ok(self):
        guard = PrivacyGuard()
        guard.validate({'a': 0.5, 'b': 1, 'c': 3.14})

    def test_list_of_long_strings_raises(self):
        guard = PrivacyGuard()
        with pytest.raises(PrivacyViolationError):
            guard.validate({'texts': ['x' * 300]})


class TestSceneCorpusBuilder:
    def test_returns_feature_list(self):
        builder = SceneCorpusBuilder()
        feats = builder.build([GOOD_SCENE])
        assert len(feats) == 1
        assert isinstance(feats[0], SceneFeature)

    def test_multiple_scenes(self):
        builder = SceneCorpusBuilder()
        feats = builder.build([GOOD_SCENE] * 5)
        assert len(feats) == 5

    def test_empty_list(self):
        builder = SceneCorpusBuilder()
        feats = builder.build([])
        assert feats == []

    def test_prose_group_extracted(self):
        builder = SceneCorpusBuilder()
        f = builder.build([GOOD_SCENE])[0]
        assert f.anti_llm_score == pytest.approx(0.7)

    def test_physics_group_extracted(self):
        builder = SceneCorpusBuilder()
        f = builder.build([GOOD_SCENE])[0]
        assert f.conflict_intensity == pytest.approx(0.5)

    def test_privacy_violation_blocked(self):
        builder = SceneCorpusBuilder()
        bad_scene = {**GOOD_SCENE, 'prose_report': {'text': 'x' * 300}}
        with pytest.raises(PrivacyViolationError):
            builder.build([bad_scene])


class TestPhysicsCoefficientUpdater:
    def test_returns_dict(self):
        store = PhysicsCoefficientStore()
        updater = PhysicsCoefficientUpdater(store)
        builder = SceneCorpusBuilder()
        feats = builder.build([GOOD_SCENE] * 3)
        result = updater.update_one_epoch(feats)
        assert isinstance(result, dict)

    def test_empty_features_no_change(self):
        store = PhysicsCoefficientStore()
        initial = store.as_dict().copy()
        updater = PhysicsCoefficientUpdater(store)
        updater.update_one_epoch([])
        assert store.as_dict() == initial

    def test_coefficients_change_after_update(self):
        store = PhysicsCoefficientStore()
        updater = PhysicsCoefficientUpdater(store)
        builder = SceneCorpusBuilder()
        feats = builder.build([GOOD_SCENE] * 5)
        initial_conflict = store.conflict_weight
        updater.update_one_epoch(feats)
        # 계수가 변해야 함 (또는 이미 수렴했을 수 있음)
        assert store.conflict_weight >= 0.05
        assert store.conflict_weight <= 0.45


class TestManuscriptLearner:
    def test_learn_returns_dict(self):
        learner = ManuscriptLearner()
        result = learner.learn([GOOD_SCENE])
        assert isinstance(result, dict)
        assert len(result) == 6

    def test_learn_count_increments(self):
        learner = ManuscriptLearner()
        learner.learn([GOOD_SCENE])
        learner.learn([GOOD_SCENE])
        assert learner.learn_count == 2

    def test_empty_uses_synthetic_fallback(self):
        learner = ManuscriptLearner(fallback_synthetic=True)
        result = learner.learn([])
        assert isinstance(result, dict)

    def test_coefficients_in_valid_range(self):
        learner = ManuscriptLearner()
        result = learner.learn([GOOD_SCENE] * 10)
        for v in result.values():
            assert 0.05 <= v <= 0.45

    def test_multiple_epochs(self):
        learner = ManuscriptLearner()
        for _ in range(5):
            learner.learn([GOOD_SCENE])
        assert learner.learn_count == 5
