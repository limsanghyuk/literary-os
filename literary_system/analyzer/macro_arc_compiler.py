from __future__ import annotations

from typing import Any


def _default_act_breakpoints(total_episode_count: int) -> list[int]:
    if total_episode_count <= 3:
        return [1, max(1, total_episode_count)]
    first = max(1, round(total_episode_count * 0.25))
    second = max(first + 1, round(total_episode_count * 0.7))
    return sorted({first, second, total_episode_count})


def _resolve_act_index(episode_index: int, breakpoints: list[int]) -> int:
    for i, bp in enumerate(sorted(breakpoints), start=1):
        if episode_index <= bp:
            return i
    return len(breakpoints)


def compile_macro_arc_packet(project_context: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    total_episode_count = int(project_context.get("total_episode_count", 1))
    episode_index = int(project_context.get("episode_index", 1))
    act_breakpoints = list(project_context.get("act_breakpoints") or _default_act_breakpoints(total_episode_count))
    act_index = int(project_context.get("act_index") or _resolve_act_index(episode_index, act_breakpoints))
    false_climax_episode = project_context.get("false_climax_episode")
    pressure_curve = project_context.get("pressure_curve") or {
        "act_1": "anchor_and_bury_residue",
        "act_2": "escalate_without_release",
        "act_3": "payoff_and_method_blame",
    }
    reveal_budget = project_context.get("reveal_budget") or {
        "act_1": {"core_truth": 0, "surface_hint": 2},
        "act_2": {"core_truth": 1, "surface_hint": 2},
        "act_3": {"core_truth": 2, "surface_hint": 1},
    }
    residue_recall_budget = project_context.get("residue_recall_budget") or {
        "act_1": {"reuse": 1, "new_residue": 2},
        "act_2": {"reuse": 2, "new_residue": 1},
        "act_3": {"reuse": 2, "new_residue": 0},
    }
    pdi_baseline = float(project_context.get("pdi_baseline", project_context.get("pdi_profile", 0.5)))
    anti_cliffhanger_policy = project_context.get("anti_cliffhanger_policy", "forbid_generic_hook")
    macro_arc_mode = project_context.get("macro_arc_mode")
    if not macro_arc_mode:
        if project_context.get("media_type") == "screenplay":
            macro_arc_mode = "feature_film"
        elif total_episode_count >= 8:
            macro_arc_mode = "limited_series"
        else:
            macro_arc_mode = "three_act"
    hitl_gate_required = bool(project_context.get("hitl_gate_required", episode_index in act_breakpoints[:-1]))

    act_key = f"act_{min(act_index, 3)}"
    act_pressure_target = pressure_curve.get(act_key, pressure_curve.get("act_2", "escalate_without_release"))
    act_reveal_budget = reveal_budget.get(act_key, {"core_truth": 0, "surface_hint": 1})
    act_residue_budget = residue_recall_budget.get(act_key, {"reuse": 1, "new_residue": 0})

    macro_packet = {
        "macro_arc_mode": macro_arc_mode,
        "episode_index": episode_index,
        "total_episode_count": total_episode_count,
        "act_breakpoints": act_breakpoints,
        "act_index": act_index,
        "false_climax_episode": false_climax_episode,
        "pressure_curve": pressure_curve,
        "reveal_budget": reveal_budget,
        "residue_recall_budget": residue_recall_budget,
        "pdi_baseline": pdi_baseline,
        "hitl_gate_required": hitl_gate_required,
        "anti_cliffhanger_policy": anti_cliffhanger_policy,
    }
    act_intent_packet = {
        "act_index": act_index,
        "episode_index": episode_index,
        "pressure_target": act_pressure_target,
        "reveal_budget": act_reveal_budget,
        "residue_recall_budget": act_residue_budget,
        "ending_rule": project_context.get(
            "ending_rule",
            "no_false_resolution" if act_index < 3 else "morally_sealed_closure",
        ),
        "anti_cliffhanger_policy": anti_cliffhanger_policy,
        "false_climax_episode": false_climax_episode,
    }
    return macro_packet, act_intent_packet
