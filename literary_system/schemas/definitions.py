from __future__ import annotations

from literary_system.common.enums import (
    MediaType,
    PacketType,
    PromotionDecision,
    RelationType,
    ReleaseDecision,
    RoleType,
)

COMMON_ENVELOPE_REQUIRED = {
    "schema_version",
    "project_id",
    "packet_type",
    "created_at",
    "provenance",
    "payload",
}

PACKET_REQUIRED_FIELDS: dict[str, set[str]] = {
    PacketType.INTENT_SEED.value: {
        "project_id", "project_mode", "master_seed", "media_type", "pdi_profile", "created_at"
    },
    PacketType.FORMAT_CONSTITUTION.value: {"media_type", "output_schema", "critic_pattern_set"},
    PacketType.MACRO_ARC.value: {
        "macro_arc_mode", "episode_index", "total_episode_count", "act_breakpoints", "act_index",
        "pressure_curve", "reveal_budget", "residue_recall_budget", "pdi_baseline", "anti_cliffhanger_policy",
    },
    PacketType.ACT_INTENT.value: {
        "act_index", "episode_index", "pressure_target", "reveal_budget", "residue_recall_budget",
        "ending_rule", "anti_cliffhanger_policy",
    },
    PacketType.COMMANDER_BRIEFING.value: {"scene_summary", "commander_decision_point"},
    PacketType.CHARACTER_BIRTH_GATE.value: {"character_id", "questions", "decision"},
    PacketType.CHARACTER_LEDGER.value: {"character_id", "display_name", "role_type", "pressure_target",
                                        "residue_binding", "act_evolution", "memory_weight", "prunable"},
    PacketType.CHARACTER_GRID.value: {"grid_edges"},
    PacketType.PRESSURE_CAST_PLAN.value: {"foreground_characters", "active_tension_axes"},
    PacketType.SCENE_DIGEST.value: {"scene_id", "scene_goal", "scene_focus", "active_characters", "active_tension_axes"},
    PacketType.RESIDUE_VARIATION_PLAN.value: {"motif", "recall_mode", "recurrence_budget_cost", "variation_budget_cost",
                                              "intended_emotional_effect"},
    PacketType.LITERARY_STATE_BEFORE.value: {"SP", "RU", "ET", "RD", "RT", "AC", "RO", "MR"},
    PacketType.LITERARY_STATE_AFTER.value: {"SP", "RU", "ET", "RD", "RT", "AC", "RO", "MR"},
    PacketType.CRITIC_DECISION.value: {"pattern_codes", "loss_report", "decision"},
    PacketType.FINAL_ACCEPTANCE.value: {"bundle_id", "release_decision", "fewshot_promotion_decision", "graph_write_mode"},
}

ENUM_FIELDS: dict[str, dict[str, set[str]]] = {
    PacketType.INTENT_SEED.value: {
        "project_mode": {"novel", "drama", "screenplay", "documentary", "shorts"},
        "media_type": {m.value for m in MediaType},
        "k_hybrid_bias": {"low", "mid", "high"},
    },
    PacketType.FORMAT_CONSTITUTION.value: {"media_type": {m.value for m in MediaType}},
    PacketType.MACRO_ARC.value: {
        "macro_arc_mode": {"three_act", "limited_series", "feature_film", "bundle_driven"},
        "anti_cliffhanger_policy": {"forbid_generic_hook", "residue_only", "structural_pull"},
    },
    PacketType.ACT_INTENT.value: {
        "ending_rule": {"no_false_resolution", "hard_cut", "morally_sealed_closure", "quiet_pressure_carryover"},
        "anti_cliffhanger_policy": {"forbid_generic_hook", "residue_only", "structural_pull"},
    },
    PacketType.CHARACTER_BIRTH_GATE.value: {"decision": {"pass", "fail", "provisional"}},
    PacketType.CHARACTER_LEDGER.value: {"role_type": {r.value for r in RoleType}},
    PacketType.CHARACTER_GRID.value: {"relation_type": {r.value for r in RelationType}},
    PacketType.CRITIC_DECISION.value: {"decision": {"pass", "retry", "hold", "external_review"}},
    PacketType.FINAL_ACCEPTANCE.value: {
        "release_decision": {r.value for r in ReleaseDecision},
        "fewshot_promotion_decision": {p.value for p in PromotionDecision},
    },
}
