"""V370 StyleDNA v2 확장 테스트."""
import pytest
from literary_system.prose.style_dna import StyleDNA, StyleDNAProfile


GENRES = ["literary", "noir", "fantasy", "romance", "historical"]


class TestStyleDNAInit:
    def test_default_init(self):
        dna = StyleDNA()
        assert dna is not None

    def test_all_five_genres_accessible(self):
        dna = StyleDNA()
        for g in GENRES:
            profile = dna.get(g)
            assert profile is not None

    def test_get_returns_profile_type(self):
        dna = StyleDNA()
        for g in GENRES:
            assert isinstance(dna.get(g), StyleDNAProfile)


class TestStyleDNAProfileFields:
    def setup_method(self):
        self.dna = StyleDNA()

    def test_literary_pov_1st(self):
        p = self.dna.get("literary")
        assert "1인칭" in p.pov

    def test_literary_scene_rhythm_slow(self):
        p = self.dna.get("literary")
        assert p.scene_rhythm == "slow"

    def test_noir_scene_rhythm_fast(self):
        p = self.dna.get("noir")
        assert p.scene_rhythm == "fast"

    def test_fantasy_scene_rhythm_medium(self):
        p = self.dna.get("fantasy")
        assert p.scene_rhythm == "medium"

    def test_romance_scene_rhythm_medium(self):
        p = self.dna.get("romance")
        assert p.scene_rhythm == "medium"

    def test_historical_scene_rhythm_slow(self):
        p = self.dna.get("historical")
        assert p.scene_rhythm == "slow"

    def test_literary_anti_llm_strict(self):
        p = self.dna.get("literary")
        assert p.anti_llm_strictness == "strict"

    def test_noir_anti_llm_firm(self):
        p = self.dna.get("noir")
        assert p.anti_llm_strictness == "firm"

    def test_romance_anti_llm_relaxed(self):
        p = self.dna.get("romance")
        assert p.anti_llm_strictness == "relaxed"

    def test_historical_anti_llm_firm(self):
        p = self.dna.get("historical")
        assert p.anti_llm_strictness == "firm"

    def test_fantasy_anti_llm_standard(self):
        p = self.dna.get("fantasy")
        assert p.anti_llm_strictness == "standard"

    def test_literary_inner_monologue_true(self):
        p = self.dna.get("literary")
        assert p.inner_monologue is True

    def test_noir_inner_monologue_false(self):
        p = self.dna.get("noir")
        assert p.inner_monologue is False

    def test_romance_inner_monologue_true(self):
        p = self.dna.get("romance")
        assert p.inner_monologue is True

    def test_literary_emotional_amp_high(self):
        p = self.dna.get("literary")
        assert p.emotional_amp >= 0.7

    def test_romance_emotional_amp_highest(self):
        p = self.dna.get("romance")
        assert p.emotional_amp >= 0.9

    def test_noir_emotional_amp_low(self):
        p = self.dna.get("noir")
        assert p.emotional_amp <= 0.5

    def test_sensory_priority_is_list(self):
        dna = StyleDNA()
        for g in GENRES:
            p = dna.get(g)
            assert isinstance(p.sensory_priority, list)
            assert len(p.sensory_priority) == 3

    def test_literary_sensory_tactile_first(self):
        p = self.dna.get("literary")
        assert p.sensory_priority[0] == "tactile"

    def test_noir_sensory_visual_first(self):
        p = self.dna.get("noir")
        assert p.sensory_priority[0] == "visual"

    def test_profile_genre_id_matches_key(self):
        dna = StyleDNA()
        for g in GENRES:
            p = dna.get(g)
            assert p.genre_id == g


class TestStyleDNAUnknownGenre:
    def test_unknown_genre_raises(self):
        """알 수 없는 장르는 ValueError 발생."""
        import pytest
        dna = StyleDNA()
        with pytest.raises(ValueError):
            dna.get("unknown_genre_xyz")

    def test_empty_genre_id_raises(self):
        import pytest
        dna = StyleDNA()
        with pytest.raises(ValueError):
            dna.get("")


class TestStyleDNAImmutability:
    def test_profiles_not_mutated_across_calls(self):
        dna = StyleDNA()
        p1 = dna.get("literary")
        p2 = dna.get("literary")
        assert p1.scene_rhythm == p2.scene_rhythm

    def test_all_genres_return_valid_profiles(self):
        dna = StyleDNA()
        profiles = [dna.get(g) for g in GENRES]
        assert all(isinstance(p, StyleDNAProfile) for p in profiles)

    def test_scene_rhythm_valid_values(self):
        dna = StyleDNA()
        valid = {"slow", "medium", "fast"}
        for g in GENRES:
            assert dna.get(g).scene_rhythm in valid
