"""V360: 느와르 장르 플러그인."""
from literary_system.scope.resolver import (
    NarrativeScopePlugin, StyleDirective, SceneContext, StoryContext, PluginRegistry
)
from typing import List

class NoirPlugin(NarrativeScopePlugin):
    genre_id     = "noir"
    display_name = "느와르"

    def resolve_scene(self, scene_ctx: SceneContext, story_ctx: StoryContext) -> StyleDirective:
        return StyleDirective(
            genre_id=self.genre_id, pov="1인칭",
            scene_rhythm="fast", emotional_amp=0.4,
            metadata={"tension": scene_ctx.tension},
        )

    def get_foreshadow_rules(self) -> List[str]:
        return ['어두운 상징 복선', '배신 암시']

PluginRegistry.register(NoirPlugin)
