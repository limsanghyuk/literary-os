from __future__ import annotations

from typing import Any


def detect_state_drift(bundle: dict[str, Any]) -> dict[str, Any]:
    before = [p["payload"] for p in bundle["packets"] if p["packet_type"] == "literary_state_snapshot_before"]
    after = [p["payload"] for p in bundle["packets"] if p["packet_type"] == "literary_state_snapshot_after"]
    act_intent = next((p["payload"] for p in bundle["packets"] if p["packet_type"] == "act_intent_packet"), {})
    alarms = []
    for b, a in zip(before, after):
        codes = []
        if b["SP"] > 0.6 and a["ET"] < 0.0:
            codes.append("HIGH_SP_FLAT_ET")
        if a["RU"] < 0.25 and a["RO"] < 0.5:
            codes.append("LOW_RU_LOW_RO")
        if a["MR"] > 0.65 and a["RD"]["aggregate"] > 0.45:
            codes.append("OVERLOADED_MR_WITHOUT_PAYOFF")
        if act_intent.get("anti_cliffhanger_policy") == "forbid_generic_hook" and a["RU"] > 0.9 and a["reader_afterimage"] < 0.35:
            codes.append("CHEAP_HOOK_SUSPECTED")
        if codes:
            alarms.append({"scene_id": a.get("scene_id"), "drift_reason_codes": codes})
    return {
        "alarm": bool(alarms),
        "items": alarms,
        "recommended_action": "hold_and_rebrief" if alarms else "none",
    }
