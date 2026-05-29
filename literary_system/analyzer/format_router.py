from __future__ import annotations

from literary_system.common.enums import MediaType


def route_media_type(project_context: dict) -> tuple[str, dict]:
    media_type = project_context.get("media_type") or project_context.get("project_mode") or MediaType.PROSE.value
    constitution = {
        "media_type": media_type,
        "output_schema": f"{media_type}_bundle_v1",
        "critic_pattern_set": [
            "NON_VISUAL_STAGE_DIRECTION",
            "DIALOGUE_SUBTEXT_LEAK",
            "SCRIPT_PROSE_DRIFT",
        ] if media_type in {MediaType.DRAMA.value, MediaType.SCREENPLAY.value} else [
            "PROSE_EXPOSITION_LEAK",
            "POV_DRIFT",
            "SYMBOL_OVEREXPLANATION",
        ],
    }
    return media_type, constitution
