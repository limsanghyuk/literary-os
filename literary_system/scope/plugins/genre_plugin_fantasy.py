"""V360: 판타지 장르 플러그인."""
from typing import List

from literary_system.scope.resolver import (
    NarrativeScopePlugin,
    PluginRegistry,
    SceneContext,
    StoryContext,
    StyleDirective,
)


class FantasyPlugin(NarrativeScopePlugin):
    genre_id     = "fantasy"
    display_name = "판타지"

    def resolve_scene(self, scene_ctx: SceneContext, story_ctx: StoryContext) -> StyleDirective:
        return StyleDirective(
            genre_id=self.genre_id, pov="3인칭 제한",
            scene_rhythm="medium", emotional_amp=0.75,
            metadata={"tension": scene_ctx.tension},
        )

    def get_foreshadow_rules(self) -> List[str]:
        return ['마법 체계 복선', '세계관 단서']

PluginRegistry.register(FantasyPlugin)
