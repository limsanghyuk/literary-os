"""test_v370_momentum_v2.py — EmotionalMomentumTrackerV2 테스트 (V370)"""
import pytest
from literary_system.prose.momentum_tracker import EmotionalMomentumTrackerV2, MomentumEntry
from literary_system.prose.emotion_behavior import EmotionalDelta


class TestClusterWeightRegistry:
    def test_default_weight(self):
        t = EmotionalMomentumTrackerV2()
        assert t.get_cluster_weight("unknown") == pytest.approx(0.5)

    def test_register_weight(self):
        t = EmotionalMomentumTrackerV2()
        t.register_cluster_weight("hero", 0.9)
        assert t.get_cluster_weight("hero") == pytest.approx(0.9)

    def test_weight_clamped_max(self):
        t = EmotionalMomentumTrackerV2()
        t.register_cluster_weight("c1", 1.5)
        assert t.get_cluster_weight("c1") == pytest.approx(1.0)

    def test_weight_clamped_min(self):
        t = EmotionalMomentumTrackerV2()
        t.register_cluster_weight("c2", -0.5)
        assert t.get_cluster_weight("c2") == pytest.approx(0.0)


class TestUpdate:
    def test_update_stores_entry(self):
        t = EmotionalMomentumTrackerV2()
        t.update("s1", EmotionalDelta(tension=0.7), "hero")
        assert len(t._history["hero"]) == 1

    def test_global_key_used_without_char_id(self):
        t = EmotionalMomentumTrackerV2()
        t.update("s1", EmotionalDelta(tension=0.5))
        assert len(t._history["__global__"]) == 1

    def test_window_limit(self):
        t = EmotionalMomentumTrackerV2(window=3)
        for i in range(5):
            t.update(f"s{i}", EmotionalDelta(tension=float(i)/5), "hero")
        assert len(t._history["hero"]) == 3

    def test_cluster_weight_stored_in_entry(self):
        t = EmotionalMomentumTrackerV2()
        t.register_cluster_weight("hero", 0.8)
        t.update("s1", EmotionalDelta(tension=0.5), "hero")
        entry = list(t._history["hero"])[0]
        assert entry.cluster_weight == pytest.approx(0.8)


class TestGetWeightedState:
    def test_empty_returns_zero_delta(self):
        t = EmotionalMomentumTrackerV2()
        d = t.get_weighted_state("nobody")
        assert d.tension == pytest.approx(0.0)

    def test_single_entry_weighted(self):
        t = EmotionalMomentumTrackerV2()
        t.register_cluster_weight("hero", 1.0)
        t.update("s1", EmotionalDelta(tension=1.0), "hero")
        d = t.get_weighted_state("hero")
        assert d.tension > 0.0

    def test_high_weight_amplifies(self):
        t = EmotionalMomentumTrackerV2()
        t.register_cluster_weight("hero", 0.9)
        t.register_cluster_weight("extra", 0.1)
        t.update("s1", EmotionalDelta(tension=0.5), "hero")
        t.update("s1", EmotionalDelta(tension=0.5), "extra")
        d_hero  = t.get_weighted_state("hero")
        d_extra = t.get_weighted_state("extra")
        assert d_hero.tension >= d_extra.tension

    def test_returns_emotional_delta(self):
        t = EmotionalMomentumTrackerV2()
        t.update("s1", EmotionalDelta(dread=0.6))
        d = t.get_weighted_state()
        assert isinstance(d, EmotionalDelta)


class TestMomentumArc:
    def test_arc_empty(self):
        t = EmotionalMomentumTrackerV2()
        assert t.momentum_arc("nobody") == []

    def test_arc_n_scenes(self):
        t = EmotionalMomentumTrackerV2()
        for i in range(6):
            t.update(f"s{i}", EmotionalDelta(tension=i/5), "hero")
        arc = t.momentum_arc("hero", n_scenes=5)
        assert len(arc) == 5

    def test_arc_values_match_tension(self):
        t = EmotionalMomentumTrackerV2()
        t.update("s1", EmotionalDelta(tension=0.3), "hero")
        t.update("s2", EmotionalDelta(tension=0.7), "hero")
        arc = t.momentum_arc("hero")
        assert 0.3 in arc or 0.7 in arc


class TestStats:
    def test_stats_empty(self):
        t = EmotionalMomentumTrackerV2()
        s = t.stats("nobody")
        assert s["count"] == 0

    def test_stats_count(self):
        t = EmotionalMomentumTrackerV2()
        t.update("s1", EmotionalDelta(tension=0.5), "hero")
        t.update("s2", EmotionalDelta(tension=0.8), "hero")
        s = t.stats("hero")
        assert s["count"] == 2

    def test_stats_avg_tension(self):
        t = EmotionalMomentumTrackerV2()
        t.update("s1", EmotionalDelta(tension=0.5), "hero")
        t.update("s2", EmotionalDelta(tension=1.0), "hero")
        s = t.stats("hero")
        assert s["avg_tension"] == pytest.approx(0.75)
