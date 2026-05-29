from __future__ import annotations

from typing import Any


def build_pressure_cast_plans(
    scene_digests: list[dict[str, Any]],
    project_context: dict[str, Any],
    act_intent_packet: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    results = []
    global_required_residue = project_context.get("required_residue_signals", [])
    pressure_target = (act_intent_packet or {}).get("pressure_target")
    for scene in scene_digests:
        active = list(scene.get("active_characters", []))
        foreground = active[: min(3, len(active))]
        background = active[3:]
        suppressed = project_context.get("suppressed_characters", [])
        active_axes = list(scene.get("active_tension_axes", []))
        if pressure_target and pressure_target not in active_axes:
            active_axes = [pressure_target] + active_axes
        required_residue_signals = list(dict.fromkeys(scene.get("detected_motifs", [])[:2] + global_required_residue))[:4]
        results.append({
            "scene_id": scene["scene_id"],
            "foreground_characters": foreground,
            "background_characters": background,
            "suppressed_characters": suppressed,
            "active_tension_axes": active_axes[:3],
            "required_residue_signals": required_residue_signals,
        })
    return results
