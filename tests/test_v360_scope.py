"""V360 T11-5: NarrativeScopeResolver + 장르 플러그인 5종 테스트."""
import sys
sys.path.insert(0, "/tmp/v360_build")
import pytest
from literary_system.scope.resolver import (
    NarrativeScopeResolver, NarrativeScopePlugin, PluginRegistry,
    StyleDirective, SceneContext, StoryContext,
)


class TestPluginRegistry:
    def test_all_genres_registered(self):
        resolver = NarrativeScopeResolver()
        genres = PluginRegistry.all_genres()
        assert set(["literary","noir","fantasy","romance","historical"]).issubset(set(genres))

    def test_get_plugin_by_id(self):
        resolver = NarrativeScopeResolver()
        for gid in ["literary","noir","fantasy","romance","historical"]:
            cls = PluginRegistry.get(gid)
            assert cls is not None

    def test_unknown_genre_none(self):
        assert PluginRegistry.get("nonexistent_xyz") is None


class TestResolverLoad:
    def test_load_literary(self):
        r = NarrativeScopeResolver()
        p = r.load("literary")
        assert isinstance(p, NarrativeScopePlugin)
        assert p.genre_id == "literary"

    def test_load_noir(self):
        r = NarrativeScopeResolver()
        p = r.load("noir")
        assert p.genre_id == "noir"

    def test_load_fantasy(self):
        r = NarrativeScopeResolver()
        p = r.load("fantasy")
        assert p.genre_id == "fantasy"

    def test_load_romance(self):
        r = NarrativeScopeResolver()
        p = r.load("romance")
        assert p.genre_id == "romance"

    def test_load_historical(self):
        r = NarrativeScopeResolver()
        p = r.load("historical")
        assert p.genre_id == "historical"

    def test_load_unknown_raises(self):
        r = NarrativeScopeResolver()
        with pytest.raises(ValueError): r.load("unknown_genre")

    def test_default_genre_literary(self):
        r = NarrativeScopeResolver()
        p = r.load()
        assert p.genre_id == "literary"

    def test_available_genres_list(self):
        r = NarrativeScopeResolver()
        genres = r.available_genres()
        assert len(genres) >= 5


class TestStyleDirective:
    def setup_method(self):
        self.r = NarrativeScopeResolver()
        self.scene = SceneContext(scene_id="s1", tension=0.5)
        self.story = StoryContext(genre="literary")

    def test_returns_style_directive(self):
        self.r.load("literary")
        d = self.r.resolve(self.scene, self.story)
        assert isinstance(d, StyleDirective)

    def test_literary_pov_1st(self):
        self.r.load("literary")
        d = self.r.resolve(self.scene, self.story)
        assert "1인칭" in d.pov

    def test_literary_rhythm_slow(self):
        self.r.load("literary")
        d = self.r.resolve(self.scene, self.story)
        assert d.scene_rhythm == "slow"

    def test_literary_amp(self):
        self.r.load("literary")
        d = self.r.resolve(self.scene, self.story)
        assert 0.7 <= d.emotional_amp <= 1.0

    def test_noir_pov_1st(self):
        self.r.load("noir")
        d = self.r.resolve(self.scene, StoryContext(genre="noir"))
        assert "1인칭" in d.pov

    def test_noir_rhythm_fast(self):
        self.r.load("noir")
        d = self.r.resolve(self.scene, StoryContext(genre="noir"))
        assert d.scene_rhythm == "fast"

    def test_fantasy_pov_3rd(self):
        self.r.load("fantasy")
        d = self.r.resolve(self.scene, StoryContext(genre="fantasy"))
        assert "3인칭" in d.pov

    def test_romance_amp_high(self):
        self.r.load("romance")
        d = self.r.resolve(self.scene, StoryContext(genre="romance"))
        assert d.emotional_amp >= 0.9

    def test_historical_pov_omniscient(self):
        self.r.load("historical")
        d = self.r.resolve(self.scene, StoryContext(genre="historical"))
        assert "3인칭" in d.pov or "전지" in d.pov

    def test_genre_id_in_directive(self):
        for gid in ["literary","noir","fantasy","romance","historical"]:
            self.r.load(gid)
            d = self.r.resolve(self.scene, StoryContext(genre=gid))
            assert d.genre_id == gid


class TestForeshadowRules:
    def test_literary_rules_nonempty(self):
        r = NarrativeScopeResolver(); r.load("literary")
        rules = r._active.get_foreshadow_rules()
        assert isinstance(rules, list) and len(rules) >= 1

    def test_noir_rules_nonempty(self):
        r = NarrativeScopeResolver(); r.load("noir")
        assert len(r._active.get_foreshadow_rules()) >= 1

    def test_fantasy_rules_nonempty(self):
        r = NarrativeScopeResolver(); r.load("fantasy")
        assert len(r._active.get_foreshadow_rules()) >= 1

    def test_romance_rules_nonempty(self):
        r = NarrativeScopeResolver(); r.load("romance")
        assert len(r._active.get_foreshadow_rules()) >= 1

    def test_historical_rules_nonempty(self):
        r = NarrativeScopeResolver(); r.load("historical")
        assert len(r._active.get_foreshadow_rules()) >= 1

    def test_rules_are_strings(self):
        r = NarrativeScopeResolver()
        for gid in ["literary","noir","fantasy","romance","historical"]:
            r.load(gid)
            for rule in r._active.get_foreshadow_rules():
                assert isinstance(rule, str)


class TestResolveAutoLoad:
    def test_resolve_without_load_uses_story_genre(self):
        r = NarrativeScopeResolver()
        scene = SceneContext(scene_id="s1", tension=0.6)
        story = StoryContext(genre="noir")
        d = r.resolve(scene, story)
        assert isinstance(d, StyleDirective)

    def test_resolve_multiple_genres(self):
        r = NarrativeScopeResolver()
        scene = SceneContext(scene_id="s1", tension=0.5)
        for gid in ["literary","noir","fantasy","romance","historical"]:
            r.load(gid)
            d = r.resolve(scene, StoryContext(genre=gid))
            assert d.genre_id == gid

    def test_tension_reflected_in_metadata(self):
        r = NarrativeScopeResolver(); r.load("literary")
        scene = SceneContext(scene_id="s1", tension=0.9)
        d = r.resolve(scene, StoryContext(genre="literary"))
        assert "tension" in d.metadata
        assert d.metadata["tension"] == 0.9
