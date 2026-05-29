"""test_v370_style_dna.py — StyleDNA v2 테스트 (V370)"""
import pytest
from literary_system.prose.style_dna import StyleDNA, StyleDNAProfile, _PROFILES


class TestStyleDNABuiltins:
    def setup_method(self):
        self.dna = StyleDNA()

    def test_five_genres_available(self):
        assert len(self.dna.available_genres()) >= 5

    def test_literary_exists(self):
        p = self.dna.get("literary")
        assert p.genre_id == "literary"

    def test_noir_exists(self):
        p = self.dna.get("noir")
        assert p.genre_id == "noir"

    def test_fantasy_exists(self):
        p = self.dna.get("fantasy")
        assert p.genre_id == "fantasy"

    def test_romance_exists(self):
        p = self.dna.get("romance")
        assert p.genre_id == "romance"

    def test_historical_exists(self):
        p = self.dna.get("historical")
        assert p.genre_id == "historical"


class TestLiteraryProfile:
    def setup_method(self):
        self.p = StyleDNA().get("literary")

    def test_pov_first_person(self):
        assert "1인칭" in self.p.pov

    def test_rhythm_slow(self):
        assert self.p.scene_rhythm == "slow"

    def test_emotional_amp_0_8(self):
        assert self.p.emotional_amp == pytest.approx(0.8)

    def test_anti_llm_strict(self):
        assert self.p.anti_llm_strictness == "strict"

    def test_inner_monologue_true(self):
        assert self.p.inner_monologue is True

    def test_sensory_priority_tactile_first(self):
        assert self.p.sensory_priority[0] == "tactile"


class TestNoirProfile:
    def setup_method(self):
        self.p = StyleDNA().get("noir")

    def test_rhythm_fast(self):
        assert self.p.scene_rhythm == "fast"

    def test_emotional_amp_low(self):
        assert self.p.emotional_amp < 0.5

    def test_anti_llm_firm(self):
        assert self.p.anti_llm_strictness == "firm"

    def test_inner_monologue_false(self):
        assert self.p.inner_monologue is False


class TestRomanceProfile:
    def setup_method(self):
        self.p = StyleDNA().get("romance")

    def test_emotional_amp_high(self):
        assert self.p.emotional_amp >= 0.9

    def test_anti_llm_relaxed(self):
        assert self.p.anti_llm_strictness == "relaxed"

    def test_tactile_first_priority(self):
        assert self.p.sensory_priority[0] == "tactile"


class TestStyleDNAMethods:
    def setup_method(self):
        self.dna = StyleDNA()

    def test_anti_llm_strictness_method(self):
        assert self.dna.anti_llm_strictness("literary") == "strict"

    def test_sensory_priority_method(self):
        pri = self.dna.sensory_priority("noir")
        assert isinstance(pri, list)
        assert len(pri) == 3

    def test_scene_rhythm_method(self):
        assert self.dna.scene_rhythm("noir") == "fast"

    def test_register_custom_profile(self):
        p = StyleDNAProfile(
            genre_id="custom", pov="1인칭", scene_rhythm="fast",
            emotional_amp=0.5, anti_llm_strictness="firm",
            sensory_priority=["visual", "audio", "tactile"],
        )
        self.dna.register(p)
        assert "custom" in self.dna.available_genres()

    def test_get_unknown_raises(self):
        with pytest.raises(ValueError):
            self.dna.get("unknown_genre_xyz")

    def test_available_genres_list(self):
        genres = self.dna.available_genres()
        assert isinstance(genres, list)
        assert all(isinstance(g, str) for g in genres)
