from __future__ import annotations

from collections import defaultdict
from typing import Any

from literary_system.common.enums import RelationType


def build_character_grid(
    project_context: dict[str, Any],
    ledgers: list[dict[str, Any]],
    scenes: list[dict[str, Any]],
) -> dict[str, Any]:
    if project_context.get("character_grid"):
        return project_context["character_grid"]

    id_to_role = {char["character_id"]: char.get("role_type") for char in ledgers}
    id_to_target = {char["character_id"]: char.get("pressure_target") for char in ledgers}
    cooccur = defaultdict(int)
    shared_axes = defaultdict(set)
    for scene in scenes:
        chars = scene.get("active_characters", [])
        axes = scene.get("active_tension_axes", [])
        for i, source in enumerate(chars):
            for target in chars[i + 1:]:
                key = tuple(sorted((source, target)))
                cooccur[key] += 1
                shared_axes[key].update(axes)

    edges = []
    for (source, target), count in cooccur.items():
        source_target = id_to_target.get(source)
        target_target = id_to_target.get(target)
        if source_target == target_target and source_target not in {None, "", "story_pressure"}:
            relation_type = RelationType.MIRROR.value
        elif RelationType.STRUCTURE.value in {id_to_role.get(source), id_to_role.get(target)}:
            relation_type = RelationType.STRUCTURE.value
        elif "비밀" in shared_axes[(source, target)] or "secret" in shared_axes[(source, target)]:
            relation_type = RelationType.CONCEALED_CONFLICT.value
        elif count >= 2:
            relation_type = RelationType.DEPENDENCY.value
        else:
            relation_type = RelationType.PRESSURE.value
        intensity = round(min(1.0, 0.35 + count * 0.18 + min(0.18, len(shared_axes[(source, target)]) * 0.04)), 2)
        edges.append({
            "source": source,
            "target": target,
            "relation_type": relation_type,
            "tension_axis": ", ".join(sorted(shared_axes[(source, target)])[:2]) or "shared_scene",
            "intensity": intensity,
            "phase": project_context.get("grid_phase", "act_1"),
            "scene_activation_hint": " / ".join(sorted(shared_axes[(source, target)])[:2]) or "scene_co_presence",
        })

    edges.sort(key=lambda e: (-e["intensity"], e["source"], e["target"]))
    return {"grid_edges": edges[:12]}
