from __future__ import annotations

from collections import defaultdict
from typing import Any

from literary_system.common.errors import SchemaValidationError
from literary_system.common.enums import PacketType, PromotionDecision


def _payloads(bundle: dict[str, Any], packet_type: str) -> list[dict[str, Any]]:
    return [p["payload"] for p in bundle["packets"] if p["packet_type"] == packet_type]


def validate_invariants(bundle: dict[str, Any]) -> None:
    ledgers = _payloads(bundle, PacketType.CHARACTER_LEDGER.value)
    ledger_ids = {p["character_id"] for p in ledgers}

    for grid in _payloads(bundle, PacketType.CHARACTER_GRID.value):
        for edge in grid.get("grid_edges", []):
            if edge["source"] not in ledger_ids or edge["target"] not in ledger_ids:
                raise SchemaValidationError("AUTHORITY_UNKNOWN_CHARACTER", "grid edge references unknown character")

    scene_map = {p["scene_id"]: p for p in _payloads(bundle, PacketType.SCENE_DIGEST.value)}
    for plan in _payloads(bundle, PacketType.PRESSURE_CAST_PLAN.value):
        scene_id = plan.get("scene_id")
        if scene_id and scene_id in scene_map:
            active = set(scene_map[scene_id]["active_characters"])
            fg = set(plan.get("foreground_characters", []))
            if not fg.issubset(active):
                raise SchemaValidationError("SCHEMA_INVARIANT_FAILED", "foreground characters must be subset of active_characters")

    known_motifs = set()
    for ledger in ledgers:
        residue_binding = ledger.get("residue_binding", {})
        for items in residue_binding.values():
            known_motifs.update(items)
    for packet in _payloads(bundle, PacketType.RESIDUE_VARIATION_PLAN.value):
        if packet["motif"] not in known_motifs and packet["motif"] not in bundle.get("motif_catalog", []):
            raise SchemaValidationError("AUTHORITY_UNKNOWN_MOTIF", f"unknown motif {packet['motif']}")

    before = defaultdict(int)
    after = defaultdict(int)
    for packet in _payloads(bundle, PacketType.LITERARY_STATE_BEFORE.value):
        before[packet.get("scene_id") or packet.get("bundle_id")] += 1
    for packet in _payloads(bundle, PacketType.LITERARY_STATE_AFTER.value):
        after[packet.get("scene_id") or packet.get("bundle_id")] += 1
    for key in set(before) | set(after):
        if before[key] != after[key]:
            raise SchemaValidationError("STATE_SNAPSHOT_INCOMPLETE", f"before/after snapshot mismatch for {key}")

    final_packets = _payloads(bundle, PacketType.FINAL_ACCEPTANCE.value)
    critic_packets = _payloads(bundle, PacketType.CRITIC_DECISION.value)
    if final_packets:
        promotion = final_packets[-1].get("fewshot_promotion_decision")
        if promotion == PromotionDecision.CANONICAL_FEWSHOT.value and not critic_packets:
            raise SchemaValidationError("PROMOTION_WITHOUT_PROVENANCE", "canonical_fewshot requires critic packet")

    macro_packets = _payloads(bundle, PacketType.MACRO_ARC.value)
    act_packets = _payloads(bundle, PacketType.ACT_INTENT.value)
    if macro_packets and act_packets:
        macro = macro_packets[-1]
        act = act_packets[-1]
        if act.get("act_index") != macro.get("act_index"):
            raise SchemaValidationError("SCHEMA_INVARIANT_FAILED", "macro_arc.act_index must match act_intent.act_index")
        if act.get("episode_index") != macro.get("episode_index"):
            raise SchemaValidationError("SCHEMA_INVARIANT_FAILED", "macro_arc.episode_index must match act_intent.episode_index")
