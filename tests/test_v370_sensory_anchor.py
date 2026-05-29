"""test_v370_sensory_anchor.py — SensoryAnchorInjector 테스트 (V370)"""
import pytest
from literary_system.prose.sensory_anchor import (
    SensoryAnchorInjector, SettingSeed, AnchoredSceneIR,
)


class TestSettingSeed:
    def test_default_empty(self):
        s = SettingSeed()
        assert s.visual == s.audio == s.tactile == ""

    def test_custom_values(self):
        s = SettingSeed(visual="창문", audio="기차", tactile="손잡이")
        assert s.visual == "창문"

    def test_metadata_default_empty(self):
        s = SettingSeed()
        assert s.metadata == {}


class TestAnchoredSceneIR:
    def test_fields_exist(self):
        a = AnchoredSceneIR(scene_id="s1", base_text="test")
        assert hasattr(a, "injected_text")
        assert hasattr(a, "density")
        assert hasattr(a, "anchors")

    def test_density_default_zero(self):
        a = AnchoredSceneIR(scene_id="s1", base_text="test")
        assert a.density == pytest.approx(0.0)


class TestInjectBasics:
    def setup_method(self):
        self.inj = SensoryAnchorInjector()
        self.base = "그가 문을 열었다. 그녀가 돌아봤다."

    def test_returns_anchored_scene_ir(self):
        r = self.inj.inject("s1", self.base)
        assert isinstance(r, AnchoredSceneIR)

    def test_scene_id_preserved(self):
        r = self.inj.inject("s1", self.base)
        assert r.scene_id == "s1"

    def test_base_text_preserved(self):
        r = self.inj.inject("s1", self.base)
        assert r.base_text == self.base

    def test_injected_text_longer(self):
        r = self.inj.inject("s1", self.base)
        assert len(r.injected_text) >= len(self.base)

    def test_density_positive(self):
        r = self.inj.inject("s1", self.base)
        assert r.density > 0.0

    def test_density_at_most_one(self):
        r = self.inj.inject("s1", self.base)
        assert r.density <= 1.0

    def test_anchors_populated(self):
        r = self.inj.inject("s1", self.base)
        assert isinstance(r.anchors, SettingSeed)


class TestCustomSeed:
    def test_custom_visual_injected(self):
        inj  = SensoryAnchorInjector()
        seed = SettingSeed(visual="먼지 낀 창문으로 빛이 들어왔다.")
        r    = inj.inject("s1", "그가 앉았다.", seed)
        assert "먼지 낀 창문" in r.injected_text

    def test_custom_audio_injected(self):
        inj  = SensoryAnchorInjector()
        seed = SettingSeed(audio="냉장고 소리가 들렸다.")
        r    = inj.inject("s1", "그녀가 서 있었다. 잠시 후 앉았다.", seed)
        assert "냉장고 소리" in r.injected_text

    def test_custom_tactile_injected(self):
        inj  = SensoryAnchorInjector()
        seed = SettingSeed(tactile="손잡이가 차가웠다.")
        r    = inj.inject("s1", "그가 문을 열었다. 안으로 들어갔다.", seed)
        assert "손잡이가 차가웠다" in r.injected_text

    def test_empty_seed_uses_defaults(self):
        inj  = SensoryAnchorInjector()
        seed = SettingSeed()
        r    = inj.inject("s1", "그가 걸었다. 멈췄다.", seed)
        assert len(r.injected_text) > len("그가 걸었다. 멈췄다.")

    def test_all_three_axes_injected(self):
        inj  = SensoryAnchorInjector()
        seed = SettingSeed(visual="v", audio="a", tactile="t")
        r    = inj.inject("s1", "문장1. 문장2. 문장3.", seed)
        assert r.density > 0.0


class TestSplitStatic:
    def test_single_sentence(self):
        parts = SensoryAnchorInjector._split("안녕하세요.")
        assert len(parts) >= 1

    def test_multiple_sentences(self):
        parts = SensoryAnchorInjector._split("그가 왔다. 그녀가 갔다. 모두 사라졌다.")
        assert len(parts) == 3

    def test_empty_string(self):
        parts = SensoryAnchorInjector._split("")
        assert parts == [""]
