"""test_v360_scope_extended.py — NarrativeScopeResolver/Plugin 심화 테스트 (V360)"""
import pytest
from literary_system.scope.resolver import (
    NarrativeScopeResolver, NarrativeScopePlugin, PluginRegistry,
    StyleDirective, SceneContext, StoryContext
)
from typing import List


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_scene(genre="literary", tension=0.5):
    sc = SceneContext(scene_id="sc1", tension=tension)
    st = StoryContext(genre=genre)
    return sc, st


# ---------------------------------------------------------------------------
# TestPluginRegistry
# ---------------------------------------------------------------------------
class TestPluginRegistry:
    def test_register_and_get_class(self):
        class DummyPluginA(NarrativeScopePlugin):
            genre_id = "dummy_ext_a"
            display_name = "더미A"
            def resolve_scene(self, sc, st): return StyleDirective(genre_id="dummy_ext_a")
            def get_foreshadow_rules(self): return []
        PluginRegistry.register(DummyPluginA)
        p_cls = PluginRegistry.get("dummy_ext_a")
        assert p_cls is not None
        assert p_cls.genre_id == "dummy_ext_a"

    def test_get_unknown_returns_none(self):
        assert PluginRegistry.get("nonexistent_genre_xyz") is None

    def test_all_genres_contains_builtins(self):
        r = NarrativeScopeResolver()
        genres = r.available_genres()
        for g in ("literary", "noir", "fantasy", "romance", "historical"):
            assert g in genres

    def test_all_genres_at_least_five(self):
        r = NarrativeScopeResolver()
        assert len(r.available_genres()) >= 5

    def test_register_custom_plugin_visible_in_resolver(self):
        class CustomPlugin(NarrativeScopePlugin):
            genre_id = "custom_test_genre"
            display_name = "커스텀"
            def resolve_scene(self, sc, st): return StyleDirective(genre_id="custom_test_genre", scene_rhythm="fast")
            def get_foreshadow_rules(self): return ["복선1"]
        PluginRegistry.register(CustomPlugin)
        r = NarrativeScopeResolver()
        assert "custom_test_genre" in r.available_genres()

    def test_register_overwrites_same_genre_id(self):
        class PluginV1(NarrativeScopePlugin):
            genre_id = "overwrite_test"
            display_name = "V1"
            def resolve_scene(self, sc, st): return StyleDirective(genre_id="overwrite_test", scene_rhythm="slow")
            def get_foreshadow_rules(self): return []
        class PluginV2(NarrativeScopePlugin):
            genre_id = "overwrite_test"
            display_name = "V2"
            def resolve_scene(self, sc, st): return StyleDirective(genre_id="overwrite_test", scene_rhythm="fast")
            def get_foreshadow_rules(self): return []
        PluginRegistry.register(PluginV1)
        PluginRegistry.register(PluginV2)
        cls = PluginRegistry.get("overwrite_test")
        assert cls.display_name == "V2"


# ---------------------------------------------------------------------------
# TestStyleDirectiveFields
# ---------------------------------------------------------------------------
class TestStyleDirectiveFields:
    def test_directive_has_scene_rhythm(self):
        sc, st = make_scene("literary")
        r = NarrativeScopeResolver()
        r.load("literary")
        d = r.resolve(sc, st)
        assert d.scene_rhythm in ("slow", "medium", "fast")

    def test_directive_has_pov(self):
        sc, st = make_scene("literary")
        r = NarrativeScopeResolver()
        r.load("literary")
        d = r.resolve(sc, st)
        assert d.pov is not None and len(d.pov) > 0

    def test_directive_has_emotional_amp(self):
        sc, st = make_scene("literary")
        r = NarrativeScopeResolver()
        r.load("literary")
        d = r.resolve(sc, st)
        assert 0.0 <= d.emotional_amp <= 1.0

    def test_directive_is_style_directive_instance(self):
        sc, st = make_scene("literary")
        r = NarrativeScopeResolver()
        r.load("literary")
        d = r.resolve(sc, st)
        assert isinstance(d, StyleDirective)

    def test_directive_genre_id_matches(self):
        sc, st = make_scene("noir")
        r = NarrativeScopeResolver()
        r.load("noir")
        d = r.resolve(sc, st)
        assert d.genre_id == "noir"


# ---------------------------------------------------------------------------
# TestLiteraryPlugin
# ---------------------------------------------------------------------------
class TestLiteraryPlugin:
    def setup_method(self):
        self.r = NarrativeScopeResolver()
        self.r.load("literary")

    def test_literary_rhythm_slow(self):
        sc, st = make_scene("literary")
        d = self.r.resolve(sc, st)
        assert d.scene_rhythm == "slow"

    def test_literary_amplitude(self):
        sc, st = make_scene("literary")
        d = self.r.resolve(sc, st)
        assert d.emotional_amp == pytest.approx(0.8, abs=0.05)

    def test_literary_pov_first_person(self):
        sc, st = make_scene("literary")
        d = self.r.resolve(sc, st)
        assert "1인칭" in d.pov

    def test_literary_foreshadow_rules_list(self):
        plugin = PluginRegistry.get("literary")()
        rules = plugin.get_foreshadow_rules()
        assert isinstance(rules, list)

    def test_literary_metadata_has_tension(self):
        sc, st = make_scene("literary", tension=0.9)
        d = self.r.resolve(sc, st)
        assert d.metadata.get("tension") == pytest.approx(0.9)


# ---------------------------------------------------------------------------
# TestNoirPlugin
# ---------------------------------------------------------------------------
class TestNoirPlugin:
    def setup_method(self):
        self.r = NarrativeScopeResolver()
        self.r.load("noir")

    def test_noir_rhythm_fast(self):
        sc, st = make_scene("noir")
        d = self.r.resolve(sc, st)
        assert d.scene_rhythm == "fast"

    def test_noir_amplitude_low(self):
        sc, st = make_scene("noir")
        d = self.r.resolve(sc, st)
        assert d.emotional_amp < 0.5

    def test_noir_pov_first_person(self):
        sc, st = make_scene("noir")
        d = self.r.resolve(sc, st)
        assert "1인칭" in d.pov

    def test_noir_foreshadow_rules_list(self):
        plugin = PluginRegistry.get("noir")()
        rules = plugin.get_foreshadow_rules()
        assert isinstance(rules, list)


# ---------------------------------------------------------------------------
# TestFantasyPlugin
# ---------------------------------------------------------------------------
class TestFantasyPlugin:
    def setup_method(self):
        self.r = NarrativeScopeResolver()
        self.r.load("fantasy")

    def test_fantasy_rhythm_medium(self):
        sc, st = make_scene("fantasy")
        d = self.r.resolve(sc, st)
        assert d.scene_rhythm == "medium"

    def test_fantasy_amplitude(self):
        sc, st = make_scene("fantasy")
        d = self.r.resolve(sc, st)
        assert d.emotional_amp == pytest.approx(0.75, abs=0.05)

    def test_fantasy_pov_third(self):
        sc, st = make_scene("fantasy")
        d = self.r.resolve(sc, st)
        assert "3인칭" in d.pov

    def test_fantasy_foreshadow_rules_list(self):
        plugin = PluginRegistry.get("fantasy")()
        rules = plugin.get_foreshadow_rules()
        assert isinstance(rules, list)


# ---------------------------------------------------------------------------
# TestRomancePlugin
# ---------------------------------------------------------------------------
class TestRomancePlugin:
    def setup_method(self):
        self.r = NarrativeScopeResolver()
        self.r.load("romance")

    def test_romance_amplitude_high(self):
        sc, st = make_scene("romance")
        d = self.r.resolve(sc, st)
        assert d.emotional_amp >= 0.9

    def test_romance_pov_third(self):
        sc, st = make_scene("romance")
        d = self.r.resolve(sc, st)
        assert "3인칭" in d.pov

    def test_romance_rhythm_medium(self):
        sc, st = make_scene("romance")
        d = self.r.resolve(sc, st)
        assert d.scene_rhythm == "medium"

    def test_romance_genre_id(self):
        sc, st = make_scene("romance")
        d = self.r.resolve(sc, st)
        assert d.genre_id == "romance"


# ---------------------------------------------------------------------------
# TestHistoricalPlugin
# ---------------------------------------------------------------------------
class TestHistoricalPlugin:
    def setup_method(self):
        self.r = NarrativeScopeResolver()
        self.r.load("historical")

    def test_historical_rhythm_slow(self):
        sc, st = make_scene("historical")
        d = self.r.resolve(sc, st)
        assert d.scene_rhythm == "slow"

    def test_historical_amplitude_moderate(self):
        sc, st = make_scene("historical")
        d = self.r.resolve(sc, st)
        assert d.emotional_amp == pytest.approx(0.6, abs=0.05)

    def test_historical_pov_third(self):
        sc, st = make_scene("historical")
        d = self.r.resolve(sc, st)
        assert "3인칭" in d.pov

    def test_historical_foreshadow_rules_list(self):
        plugin = PluginRegistry.get("historical")()
        rules = plugin.get_foreshadow_rules()
        assert isinstance(rules, list)


# ---------------------------------------------------------------------------
# TestResolverBehavior
# ---------------------------------------------------------------------------
class TestResolverBehavior:
    def test_load_switches_plugin(self):
        r = NarrativeScopeResolver()
        r.load("literary")
        sc, st = make_scene("literary")
        d1 = r.resolve(sc, st)
        r.load("noir")
        d2 = r.resolve(sc, st)
        assert d1.scene_rhythm != d2.scene_rhythm  # slow vs fast

    def test_resolve_without_explicit_load_uses_genre(self):
        r = NarrativeScopeResolver()
        sc = SceneContext(scene_id="sc1", tension=0.5)
        st = StoryContext(genre="literary")
        d = r.resolve(sc, st)
        assert isinstance(d, StyleDirective)

    def test_load_unknown_genre_raises(self):
        r = NarrativeScopeResolver()
        with pytest.raises(Exception):
            r.load("unknown_genre_xyz_abc")

    def test_load_is_idempotent(self):
        r = NarrativeScopeResolver()
        r.load("literary")
        r.load("literary")
        sc, st = make_scene("literary")
        d = r.resolve(sc, st)
        assert d.scene_rhythm == "slow"

    def test_switch_genre_all_five(self):
        r = NarrativeScopeResolver()
        for genre in ["literary", "noir", "fantasy", "romance", "historical"]:
            r.load(genre)
            sc, st = make_scene(genre)
            d = r.resolve(sc, st)
            assert isinstance(d, StyleDirective)
            assert d.genre_id == genre

    def test_tension_passed_to_metadata(self):
        r = NarrativeScopeResolver()
        r.load("literary")
        sc = SceneContext(scene_id="sc1", tension=0.77)
        st = StoryContext(genre="literary")
        d = r.resolve(sc, st)
        assert d.metadata.get("tension") == pytest.approx(0.77)
