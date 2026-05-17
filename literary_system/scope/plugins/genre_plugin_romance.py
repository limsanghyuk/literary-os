"""V360: 로맨스 장르 플러그인."""
from literary_system.scope.resolver import (
    NarrativeScopePlugin, StyleDirective, SceneContext, StoryContext, PluginRegistry
)
from typing import List

class RomancePlugin(NarrativeScopePlugin):
    genre_id     = "romance"
    display_name = "로맨스"

    def resolve_scene(self, scene_ctx: SceneContext, story_ctx: StoryContext) -> StyleDirective:
        return StyleDirective(
            genre_id=self.genre_id, pov="3인칭 제한",
            scene_rhythm="medium", emotional_amp=0.95,
            metadata={"tension": scene_ctx.tension},
        )

    def get_foreshadow_rules(self) -> List[str]:
        return ['감정 복선', '관계 발전 암시']

PluginRegistry.register(RomancePlugin)
