from __future__ import annotations

from collections import Counter
from typing import Any

from literary_system.analyzer.text_analysis import emotional_signature


def _count_relation_pressure(character_ids: list[str], grid_edges: list[dict[str, Any]]) -> float:
    present = set(character_ids)
    intensity = 0.0
    for edge in grid_edges:
        if edge.get("source") in present and edge.get("target") in present:
            intensity += float(edge.get("intensity", 0.0))
    return intensity


def estimate_states(
    scene_digests: list[dict[str, Any]],
    grid: dict[str, Any] | None = None,
    residue_plan: list[dict[str, Any]] | None = None,
    macro_arc_packet: dict[str, Any] | None = None,
    act_intent_packet: dict[str, Any] | None = None,
    pdi_profile: float = 0.5,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    before_packets = []
    after_packets = []
    motif_counter = Counter(item.get("motif") for item in (residue_plan or []) if item.get("motif"))
    grid_edges = (grid or {}).get("grid_edges", [])
    act_index = int((macro_arc_packet or {}).get("act_index", 1))
    pressure_rule = (act_intent_packet or {}).get("pressure_target", "escalate_without_release")
    anti_hook = (act_intent_packet or {}).get("anti_cliffhanger_policy", "forbid_generic_hook")

    for idx, scene in enumerate(scene_digests, start=1):
        raw = scene.get("raw_text", "")
        d_sp, d_ru, d_et = emotional_signature(raw)
        relation_pressure = _count_relation_pressure(scene.get("active_characters", []), grid_edges)
        motif_hits = sum(motif_counter.get(m, 0) for m in scene.get("detected_motifs", []))
        tension_axes = len(scene.get("active_tension_axes", []))
        risk_count = len(scene.get("continuity_risks", []))
        quoted_turns = scene.get("quoted_turns", 0)

        act_sp_bias = {1: 0.04, 2: 0.12, 3: 0.08}.get(act_index, 0.05)
        act_ru_bias = {1: 0.06, 2: 0.10, 3: 0.03}.get(act_index, 0.05)
        act_et_bias = {1: -0.04, 2: 0.02, 3: 0.06}.get(act_index, 0.0)
        pdi_pressure = max(0.0, (0.5 - pdi_profile) * 0.18)
        pdi_orientation = max(0.0, pdi_profile - 0.5) * 0.12

        sp = 0.24 + act_sp_bias + 0.11 * tension_axes + 0.06 * len(scene.get("active_characters", [])) + d_sp + min(0.25, relation_pressure * 0.15) + pdi_pressure
        ru = 0.24 + act_ru_bias + 0.08 * risk_count + 0.04 * motif_hits + d_ru
        et = -0.10 + act_et_bias + d_et + min(0.10, quoted_turns * 0.01)
        rt = 0.22 + min(0.52, relation_pressure * 0.24) + 0.08 * tension_axes
        ac = max(0.40, 0.9 - 0.05 * risk_count - (0.03 if pressure_rule == "escalate_without_release" and quoted_turns > 8 else 0.0))
        ro = max(0.30, 0.86 - 0.07 * risk_count - 0.03 * max(0, len(scene.get("active_characters", [])) - 3) + pdi_orientation)
        mr = min(1.0, 0.10 + 0.11 * motif_hits)
        rd_aggregate = max(0.05, min(1.0, 0.46 - 0.035 * motif_hits + 0.02 * idx - 0.03 * act_index))
        per_residue = {}
        for motif in scene.get("detected_motifs", [])[:4]:
            count = motif_counter.get(motif, 1)
            per_residue[motif] = {
                "RD_raw": round(max(0.05, 0.34 - 0.03 * count), 2),
                "RD_boosted": round(min(0.4, 0.08 + 0.03 * count + (0.02 if act_index >= 2 else 0.0)), 2),
                "RD_saturation": round(min(0.5, 0.02 * count), 2),
            }

        before = {
            "scene_id": scene["scene_id"],
            "bundle_id": scene.get("bundle_id", "bundle_001"),
            "act_index": act_index,
            "SP": round(min(1.0, sp), 2),
            "RU": round(min(1.0, ru), 2),
            "ET": round(max(-1.0, min(1.0, et)), 2),
            "RD": {"aggregate": round(rd_aggregate, 2), "per_residue": per_residue},
            "RT": round(min(1.0, rt), 2),
            "AC": round(min(1.0, ac), 2),
            "RO": round(min(1.0, ro), 2),
            "MR": round(mr, 2),
            "reader_trust": round(min(1.0, 0.60 + ac * 0.2), 2),
            "reader_afterimage": round(min(1.0, 0.22 + mr * 0.3 + max(0, et) * 0.15), 2),
            "evidence": scene.get("source_refs", []),
        }
        after = dict(before)
        sp_gain = 0.08 if pressure_rule == "escalate_without_release" else 0.04
        after["SP"] = round(min(1.0, before["SP"] + sp_gain + 0.02 * tension_axes), 2)
        after["RU"] = round(min(1.0, before["RU"] + (0.02 if anti_hook == "forbid_generic_hook" else 0.05) + 0.02 * risk_count), 2)
        after["ET"] = round(max(-1.0, min(1.0, before["ET"] + (0.05 if quoted_turns else 0.02) + (0.03 if act_index == 3 else 0.0))), 2)
        after["reader_afterimage"] = round(min(1.0, before["reader_afterimage"] + 0.10 + 0.03 * motif_hits + (0.02 if anti_hook == "structural_pull" else 0.0)), 2)
        before_packets.append(before)
        after_packets.append(after)
    return before_packets, after_packets
