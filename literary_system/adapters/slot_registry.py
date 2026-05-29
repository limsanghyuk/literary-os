from __future__ import annotations

"""Registry of common creative-engine slot aliases for adapter spec generation.

This module keeps the standard adapter core stable while allowing incoming
project packages to use varied file names. The spec designer maps discovered
files into these slot groups.
"""

SLOT_REGISTRY: dict[str, list[str]] = {
    "project_context": ["project_context", "project", "engine.profile", "engine_profile"],
    "constitution": ["constitution", "format_constitution", "engine_constitution", "story.law", "story_law"],
    "characters": ["characters", "cast", "people.map", "people_map"],
    "scenes": ["scenes", "scene_plan", "beats", "beat.sheet", "beat_sheet"],
    "seed": ["seed", "master_seed", "premise.note", "premise_note"],
    "sources": ["sources"],
    "notes": ["notes"],
    "packets": ["packets"],
    "extensions": ["extensions"],
}

def normalize_slot_name(name: str) -> str | None:
    lowered = name.lower().replace('-', '_')
    for slot, aliases in SLOT_REGISTRY.items():
        if lowered == slot or lowered in aliases:
            return slot
    return None
