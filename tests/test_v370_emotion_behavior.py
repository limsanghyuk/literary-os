"""test_v370_emotion_behavior.py — EmotionToBehaviorRenderer 테스트 (V370)"""
import pytest
from literary_system.prose.emotion_behavior import (
    EmotionToBehaviorRenderer, EmotionalDelta, BehaviorText,
    _weight_band, _select_complex_key,
)


class TestEmotionalDelta:
    def test_dominant_tension(self):
        d = EmotionalDelta(tension=0.9, sympathy=0.1)
        assert d.dominant() == "tension"

    def test_dominant_dread(self):
        d = EmotionalDelta(dread=0.8)
        assert d.dominant() == "dread"

    def test_dominant_catharsis(self):
        d = EmotionalDelta(catharsis=0.7)
        assert d.dominant() == "catharsis"

    def test_dominant_sympathy(self):
        d = EmotionalDelta(sympathy=0.6)
        assert d.dominant() == "sympathy"

    def test_intensity_max(self):
        d = EmotionalDelta(tension=0.3, dread=0.8, sympathy=0.2)
        assert d.intensity() == pytest.approx(0.8)

    def test_intensity_zero(self):
        d = EmotionalDelta()
        assert d.intensity() == pytest.approx(0.0)

    def test_defaults_zero(self):
        d = EmotionalDelta()
        assert d.tension == d.sympathy == d.dread == d.catharsis == 0.0


class TestWeightBand:
    def test_low_band(self):
        assert _weight_band(0.0) == "low"
        assert _weight_band(0.39) == "low"

    def test_mid_band(self):
        assert _weight_band(0.4) == "mid"
        assert _weight_band(0.69) == "mid"

    def test_high_band(self):
        assert _weight_band(0.7) == "high"
        assert _weight_band(1.0) == "high"


class TestClusterWeight:
    def test_default_weight_0_5(self):
        r = EmotionToBehaviorRenderer()
        assert r.get_cluster_weight("unknown") == pytest.approx(0.5)

    def test_register_and_get(self):
        r = EmotionToBehaviorRenderer()
        r.register_cluster("hero", 0.9)
        assert r.get_cluster_weight("hero") == pytest.approx(0.9)

    def test_weight_clamped_max(self):
        r = EmotionToBehaviorRenderer()
        r.register_cluster("c1", 1.5)
        assert r.get_cluster_weight("c1") == pytest.approx(1.0)

    def test_weight_clamped_min(self):
        r = EmotionToBehaviorRenderer()
        r.register_cluster("c2", -0.5)
        assert r.get_cluster_weight("c2") == pytest.approx(0.0)

    def test_registry_init(self):
        r = EmotionToBehaviorRenderer(cluster_registry={"hero": 0.8})
        assert r.get_cluster_weight("hero") == pytest.approx(0.8)


class TestRenderOutput:
    def test_render_returns_behavior_text(self):
        r = EmotionToBehaviorRenderer()
        d = EmotionalDelta(tension=0.7)
        b = r.render(d, "c1")
        assert isinstance(b, BehaviorText)

    def test_behavior_text_not_empty(self):
        r = EmotionToBehaviorRenderer()
        d = EmotionalDelta(dread=0.8)
        b = r.render(d, "c1")
        assert len(b.text) > 0

    def test_intensity_zero_when_emotion_zero(self):
        r = EmotionToBehaviorRenderer()
        d = EmotionalDelta()
        b = r.render(d, "c1")
        assert b.intensity == pytest.approx(0.0)

    def test_high_weight_high_intensity(self):
        r = EmotionToBehaviorRenderer()
        r.register_cluster("hero", 0.9)
        d = EmotionalDelta(tension=1.0)
        b = r.render(d, "hero")
        assert b.intensity >= 0.7

    def test_emotion_field_set(self):
        r = EmotionToBehaviorRenderer()
        d = EmotionalDelta(sympathy=0.8)
        b = r.render(d, "")
        assert b.emotion in ("sympathy", "tension", "dread", "catharsis",
                             "dread+tension", "sympathy-tension", "tension+catharsis")

    def test_render_sequence(self):
        r = EmotionToBehaviorRenderer()
        pairs = [(EmotionalDelta(tension=0.5), "c1"),
                 (EmotionalDelta(dread=0.8), "c2")]
        results = r.render_sequence(pairs)
        assert len(results) == 2
        assert all(isinstance(b, BehaviorText) for b in results)


class TestComplexEmotions:
    def test_dread_plus_tension(self):
        key = _select_complex_key(EmotionalDelta(dread=0.6, tension=0.6))
        assert key == "dread+tension"

    def test_pure_catharsis_not_complex(self):
        key = _select_complex_key(EmotionalDelta(catharsis=0.9))
        assert key is None

    def test_complex_render_not_empty(self):
        r = EmotionToBehaviorRenderer()
        d = EmotionalDelta(dread=0.8, tension=0.8)
        b = r.render(d, "")
        assert len(b.text) > 0
