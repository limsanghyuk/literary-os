from __future__ import annotations

from typing import Any


def build_catalog(bundle: dict[str, Any]) -> dict[str, Any]:
    project_id = bundle["project_id"]
    catalog = {
        "project_id": project_id,
        "project": [],
        "characters": [],
        "scenes": [],
        "motifs": [],
        "relations": [],
        "macro_arc": [],
        "act_intents": [],
        "briefings": [],
    }
    for packet in bundle["packets"]:
        payload = packet["payload"]
        if packet["packet_type"] == "intent_seed_packet":
            catalog["project"].append(payload)
        elif packet["packet_type"] == "character_ledger":
            catalog["characters"].append(payload)
        elif packet["packet_type"] == "scene_digest":
            catalog["scenes"].append(payload)
        elif packet["packet_type"] == "residue_variation_plan":
            catalog["motifs"].append(payload)
        elif packet["packet_type"] == "character_grid":
            catalog["relations"].extend(payload["grid_edges"])
        elif packet["packet_type"] == "macro_arc_packet":
            catalog["macro_arc"].append(payload)
        elif packet["packet_type"] == "act_intent_packet":
            catalog["act_intents"].append(payload)
        elif packet["packet_type"] == "commander_briefing":
            catalog["briefings"].append(payload)
    return catalog
