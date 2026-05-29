"""V397 Voice Manifold / Style Genome Tests"""
import pytest
from literary_system.longform.voice_manifold import (
    VoiceVector, DriftType, DriftResult, VoiceManifold, StyleGenome, VoiceDriftReport
)

class TestVoiceVector:
    def _make(self, seed=0.5):
        return VoiceVector(
            sentence_length_dist=seed, dialogue_ratio=seed, silence_ratio=seed,
            metaphor_density=seed, sensory_channel_pref=seed, verb_strength=seed,
            abstraction_ratio=seed, rhythm_variance=seed, ellipsis_freq=seed,
            subtext_density=seed, tactile_density=seed, visual_density=seed,
            auditory_density=seed
        )

    def test_has_13_dimensions(self):
        v = self._make()
        lst = v.as_list()
        assert len(lst) == 13

    def test_cosine_distance_zero_with_self(self):
        v = self._make()
        assert abs(v.cosine_distance(v)) < 1e-9

    def test_cosine_distance_range(self):
        v1 = self._make(0.1)
        v2 = self._make(0.9)
        d = v1.cosine_distance(v2)
        assert 0.0 <= d <= 2.0

    def test_cosine_distance_symmetric(self):
        v1 = self._make(0.2)
        v2 = self._make(0.8)
        assert abs(v1.cosine_distance(v2) - v2.cosine_distance(v1)) < 1e-9

    def test_average_of_identical_vectors(self):
        v = self._make(0.5)
        avg = VoiceVector.average([v, v, v])
        assert abs(avg.cosine_distance(v)) < 1e-9

    def test_average_is_midpoint(self):
        fields = dict(sentence_length_dist=0.5, dialogue_ratio=0.5, silence_ratio=0.5,
                      metaphor_density=0.0, sensory_channel_pref=0.5, verb_strength=0.5,
                      abstraction_ratio=0.5, rhythm_variance=0.5, ellipsis_freq=0.5,
                      subtext_density=0.5, tactile_density=0.5, visual_density=0.5,
                      auditory_density=0.5)
        v1 = VoiceVector(**{**fields, "metaphor_density": 0.0})
        v2 = VoiceVector(**{**fields, "metaphor_density": 1.0})
        avg = VoiceVector.average([v1, v2])
        assert abs(avg.metaphor_density - 0.5) < 1e-9

    def test_default_construction(self):
        v = VoiceVector()
        assert v.sentence_length_dist == 0.5

class TestDriftType:
    def test_all_drift_types(self):
        for dt in [DriftType.NONE, DriftType.PERMITTED, DriftType.BLOCKED]:
            assert dt is not None

    def test_is_string_enum(self):
        assert isinstance(DriftType.NONE, str)

class TestVoiceManifold:
    def setup_method(self):
        self.manifold = VoiceManifold()

    def _make(self, seed=0.5):
        return VoiceVector(
            sentence_length_dist=seed, dialogue_ratio=seed, silence_ratio=seed,
            metaphor_density=seed, sensory_channel_pref=seed, verb_strength=seed,
            abstraction_ratio=seed, rhythm_variance=seed, ellipsis_freq=seed,
            subtext_density=seed, tactile_density=seed, visual_density=seed,
            auditory_density=seed
        )

    def test_drift_thresholds(self):
        assert VoiceManifold.DRIFT_THRESHOLD_PERMITTED == 0.15
        assert VoiceManifold.DRIFT_THRESHOLD_BLOCKED == 0.30

    def test_anchor_episodes_constant(self):
        assert VoiceManifold.ANCHOR_EPISODES == 3

    def test_set_anchor(self):
        vectors = [self._make(0.5) for _ in range(3)]
        self.manifold.set_anchor(vectors)
        assert self.manifold.anchor_vector is not None

    def test_anchor_is_average(self):
        vectors = [self._make(0.5) for _ in range(3)]
        self.manifold.set_anchor(vectors)
        assert abs(self.manifold.anchor_vector.cosine_distance(self._make(0.5))) < 1e-9

    def test_analyze_drift_returns_report(self):
        self.manifold.set_anchor([self._make(0.5)] * 3)
        episode_vecs = [self._make(0.5) for _ in range(16)]
        report = self.manifold.analyze_drift(episode_vecs, growth_episodes=[])
        assert isinstance(report, VoiceDriftReport)

    def test_no_drift_from_anchor(self):
        self.manifold.set_anchor([self._make(0.5)] * 3)
        episode_vecs = [self._make(0.5) for _ in range(16)]
        report = self.manifold.analyze_drift(episode_vecs, growth_episodes=[])
        assert report.blocked_drift_count == 0

    def test_large_drift_detected_as_blocked(self):
        # Orthogonal vectors have cosine_distance=1.0 >> BLOCKED threshold 0.3
        anchor_vec = VoiceVector(
            sentence_length_dist=1.0, dialogue_ratio=0.0, silence_ratio=0.0,
            metaphor_density=0.0, sensory_channel_pref=0.0, verb_strength=0.0,
            abstraction_ratio=0.0, rhythm_variance=0.0, ellipsis_freq=0.0,
            subtext_density=0.0, tactile_density=0.0, visual_density=0.0, auditory_density=0.0)
        drift_vec = VoiceVector(
            sentence_length_dist=0.0, dialogue_ratio=1.0, silence_ratio=0.0,
            metaphor_density=0.0, sensory_channel_pref=0.0, verb_strength=0.0,
            abstraction_ratio=0.0, rhythm_variance=0.0, ellipsis_freq=0.0,
            subtext_density=0.0, tactile_density=0.0, visual_density=0.0, auditory_density=0.0)
        self.manifold.set_anchor([anchor_vec] * 3)
        episode_vecs = [anchor_vec] * 3 + [drift_vec] * 13
        report = self.manifold.analyze_drift(episode_vecs, growth_episodes=[])
        assert report.blocked_drift_count > 0

    def test_drift_report_has_pass_gate(self):
        self.manifold.set_anchor([self._make(0.5)] * 3)
        episode_vecs = [self._make(0.5) for _ in range(16)]
        report = self.manifold.analyze_drift(episode_vecs, growth_episodes=[])
        assert hasattr(report, 'pass_gate')
        assert isinstance(report.pass_gate, bool)

    def test_no_drift_passes_gate(self):
        self.manifold.set_anchor([self._make(0.5)] * 3)
        episode_vecs = [self._make(0.5) for _ in range(16)]
        report = self.manifold.analyze_drift(episode_vecs, growth_episodes=[])
        assert report.pass_gate is True

class TestStyleGenome:
    def test_build_synthetic_returns_vectors(self):
        vectors = StyleGenome.build_synthetic(episode_count=16)
        assert len(vectors) == 16

    def test_synthetic_vectors_are_voice_vectors(self):
        vectors = StyleGenome.build_synthetic(episode_count=16)
        for v in vectors:
            assert isinstance(v, VoiceVector)

    def test_extract_returns_voice_vector(self):
        prose_features = {
            "avg_sentence_length": 25, "dialogue_pct": 0.4,
            "metaphor_count": 3, "total_sentences": 50
        }
        v = StyleGenome.extract(prose_features)
        assert isinstance(v, VoiceVector)

