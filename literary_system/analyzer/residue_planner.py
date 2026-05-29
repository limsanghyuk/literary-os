from __future__ import annotations

from typing import Any


def build_residue_variation_plan(
    project_context: dict[str, Any],
    scenes: list[dict[str, Any]],
    ledgers: list[dict[str, Any]],
    act_intent_packet: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    explicit = project_context.get("residue_variation_plan")
    if explicit:
        return explicit

    motif_candidates = []
    for scene in scenes:
        motif_candidates.extend(scene.get("detected_motifs", []))
    for ledger in ledgers:
        rb = ledger.get("residue_binding", {})
        for vals in rb.values():
            motif_candidates.extend(vals)

    seen = []
    for motif in motif_candidates:
        if motif and motif not in seen:
            seen.append(motif)

    act_residue_budget = (act_intent_packet or {}).get("residue_recall_budget", {"reuse": 1, "new_residue": 1})
    reuse_budget = int(act_residue_budget.get("reuse", 1))
    new_budget = int(act_residue_budget.get("new_residue", 1))
    plans = []
    for idx, motif in enumerate(seen[: max(4, reuse_budget + new_budget)]):
        plans.append({
            "motif": motif,
            "recall_mode": "variation" if idx < reuse_budget else "introduce_or_delay",
            "scene_affordance": [f"scene_echo_{idx+1}", f"gesture_shift_{idx+1}"],
            "recurrence_budget_cost": 1,
            "variation_budget_cost": 2 if idx < reuse_budget else 1,
            "intended_emotional_effect": "afterimage_and_pressure" if idx < reuse_budget else "bury_seed",
        })
    return plans
