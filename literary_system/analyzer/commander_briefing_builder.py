from __future__ import annotations

from typing import Any


def build_commander_briefing(
    project_context: dict[str, Any],
    scenes: list[dict[str, Any]],
    macro_arc_packet: dict[str, Any],
    act_intent_packet: dict[str, Any],
    dominant_motifs: list[str],
) -> dict[str, Any]:
    scene_summary = project_context.get("scene_summary") or (scenes[0]["scene_goal"] if scenes else "")
    return {
        "full_arc_strategy": project_context.get(
            "full_arc_strategy",
            "전체 형세를 먼저 깔고 장면은 그 형세 안의 수읽기로만 움직인다.",
        ),
        "current_bundle_strategy": project_context.get(
            "current_bundle_strategy",
            f"act_{macro_arc_packet['act_index']}의 압력 규칙에 맞춰 이번 번들의 공개량과 residue 회수를 제한한다.",
        ),
        "episode_positioning": project_context.get(
            "episode_positioning",
            f"episode_{macro_arc_packet['episode_index']}_act_{macro_arc_packet['act_index']}",
        ),
        "scene_summary": scene_summary,
        "commander_decision_point": project_context.get(
            "commander_decision_point",
            "이번 장면이 장기 구조를 배반하지 않는지 점검",
        ),
        "global_strategy": "macro_strategy_engine",
        "local_tactic": "scene_as_reading_move",
        "dominant_motifs": dominant_motifs,
        "scene_count": len(scenes),
        "act_index": macro_arc_packet["act_index"],
        "pressure_target": act_intent_packet["pressure_target"],
        "anti_cliffhanger_policy": act_intent_packet["anti_cliffhanger_policy"],
    }
