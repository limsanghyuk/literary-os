"""V360: 문예 소설 장르 플러그인."""
from typing import List

from literary_system.scope.resolver import (
    NarrativeScopePlugin,
    PluginRegistry,
    SceneContext,
    StoryContext,
    StyleDirective,
)


class LiteraryPlugin(NarrativeScopePlugin):
    genre_id     = "literary"
    display_name = "문예 소설"

    def resolve_scene(self, scene_ctx: SceneContext, story_ctx: StoryContext) -> StyleDirective:
        return StyleDirective(
            genre_id=self.genre_id, pov="1인칭",
            scene_rhythm="slow", emotional_amp=0.8,
            metadata={"tension": scene_ctx.tension},
        )

    def get_foreshadow_rules(self) -> List[str]:
        return ['긴장 고조 씬에 복선 삽입', '독자 공감 우선']

PluginRegistry.register(LiteraryPlugin)
