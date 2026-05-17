from __future__ import annotations

from typing import Any


def find_edges(edges: list[dict[str, Any]], character_id: str) -> list[dict[str, Any]]:
    return [edge for edge in edges if edge.get("source") == character_id or edge.get("target") == character_id]
