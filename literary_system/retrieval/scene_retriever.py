from __future__ import annotations

from typing import Any


def find_scene_cards(cards: list[dict[str, Any]], character_id: str) -> list[dict[str, Any]]:
    return [card for card in cards if character_id in card.get("active_characters", [])]
