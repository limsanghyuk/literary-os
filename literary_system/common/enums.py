from __future__ import annotations

from enum import Enum


class MediaType(str, Enum):
    PROSE = "prose"
    DRAMA = "drama"
    SCREENPLAY = "screenplay"
    DOCUMENTARY = "documentary"
    SHORTS = "shorts"


class PacketType(str, Enum):
    INTENT_SEED = "intent_seed_packet"
    FORMAT_CONSTITUTION = "format_constitution_packet"
    MACRO_ARC = "macro_arc_packet"
    ACT_INTENT = "act_intent_packet"
    COMMANDER_BRIEFING = "commander_briefing"
    CHARACTER_BIRTH_GATE = "character_birth_gate_result"
    CHARACTER_LEDGER = "character_ledger"
    CHARACTER_GRID = "character_grid"
    PRESSURE_CAST_PLAN = "pressure_cast_plan"
    SCENE_DIGEST = "scene_digest"
    RESIDUE_VARIATION_PLAN = "residue_variation_plan"
    LITERARY_STATE_BEFORE = "literary_state_snapshot_before"
    LITERARY_STATE_AFTER = "literary_state_snapshot_after"
    CRITIC_DECISION = "critic_decision_packet"
    FINAL_ACCEPTANCE = "final_acceptance_packet"


class SourceTier(str, Enum):
    T0 = "T0"
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"


class PromotionDecision(str, Enum):
    ARCHIVE_ONLY = "archive_only"
    CANDIDATE_FEWSHOT = "candidate_fewshot"
    CANONICAL_FEWSHOT = "canonical_fewshot"


class ReleaseDecision(str, Enum):
    ACCEPT = "accept"
    RETRY = "retry"
    HOLD = "hold"
    REJECT = "reject"


class RelationType(str, Enum):
    PRESSURE = "pressure"
    MIRROR = "mirror"
    STRUCTURE = "structure"
    DEPENDENCY = "dependency"
    CONCEALED_CONFLICT = "concealed_conflict"


class RoleType(str, Enum):
    PRESSURE = "pressure"
    MIRROR = "mirror"
    STRUCTURE = "structure"
    WITNESS = "witness"
    RESIDUE_CARRIER = "residue_carrier"
