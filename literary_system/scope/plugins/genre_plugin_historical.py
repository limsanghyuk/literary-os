"""V360: 역사 소설 장르 플러그인."""
from typing import List

from literary_system.scope.resolver import (
    NarrativeScopePlugin,
    PluginRegistry,
    SceneContext,
    StoryContext,
    StyleDirective,
)


class HistoricalPlugin(NarrativeScopePlugin):
    genre_id     = "historical"
    display_name = "역사 소설"

    def resolve_scene(self, scene_ctx: SceneContext, story_ctx: StoryContext) -> StyleDirective:
        return StyleDirective(
            genre_id=self.genre_id, pov="3인칭 전지",
            scene_rhythm="slow", emotional_amp=0.6,
            metadata={"tension": scene_ctx.tension},
        )

    def get_foreshadow_rules(self) -> List[str]:
        return ['역사적 사건 복선', '시대 배경 암시']

PluginRegistry.register(HistoricalPlugin)
