from __future__ import annotations

from typing import Any


def build_scene_cards(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    scene_payloads = [p["payload"] for p in bundle["packets"] if p["packet_type"] == "scene_digest"]
    cast_map = {p["payload"]["scene_id"]: p["payload"] for p in bundle["packets"] if p["packet_type"] == "pressure_cast_plan"}
    cards = []
    for scene in scene_payloads:
        cast = cast_map.get(scene["scene_id"], {})
        cards.append({
            "card_type": "scene",
            "scene_id": scene["scene_id"],
            "bundle_id": scene.get("bundle_id"),
            "scene_goal": scene["scene_goal"],
            "scene_focus": scene["scene_focus"],
            "active_characters": scene["active_characters"],
            "active_tension_axes": scene["active_tension_axes"],
            "foreground_characters": cast.get("foreground_characters", []),
        })
    return cards


def build_vector_cards(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    cards = []
    for scene in build_scene_cards(bundle):
        text = (
            f"scene_id: {scene['scene_id']}\n"
            f"bundle_id: {scene.get('bundle_id')}\n"
            f"goal: {scene['scene_goal']}\n"
            f"focus: {scene['scene_focus']}\n"
            f"active_characters: {', '.join(scene['active_characters'])}\n"
            f"tension_axes: {', '.join(scene['active_tension_axes'])}"
        )
        cards.append({
            "id": scene["scene_id"],
            "document": text,
            "metadata": {
                "card_type": "scene",
                "bundle_id": scene.get("bundle_id"),
                "active_characters": scene["active_characters"],
            },
        })
    return cards
