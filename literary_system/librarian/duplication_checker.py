from __future__ import annotations

from typing import Any


def check_duplicates(bundle: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    seen_characters: set[str] = set()
    seen_scenes: set[str] = set()
    for packet in bundle["packets"]:
        payload = packet["payload"]
        if packet["packet_type"] == "character_ledger":
            cid = payload["character_id"]
            if cid in seen_characters:
                warnings.append(f"duplicate character_id: {cid}")
            seen_characters.add(cid)
        if packet["packet_type"] == "scene_digest":
            sid = payload["scene_id"]
            if sid in seen_scenes:
                warnings.append(f"duplicate scene_id: {sid}")
            seen_scenes.add(sid)
    return warnings
