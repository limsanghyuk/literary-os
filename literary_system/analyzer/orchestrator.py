from __future__ import annotations

from typing import Any

from literary_system.analyzer.character_birth_gate import evaluate_character_birth
from literary_system.analyzer.commander_briefing_builder import build_commander_briefing
from literary_system.analyzer.format_router import route_media_type
from literary_system.analyzer.grid_builder import build_character_grid
from literary_system.analyzer.intake import ingest_inputs
from literary_system.analyzer.ledger_builder import build_character_ledger
from literary_system.analyzer.macro_arc_compiler import compile_macro_arc_packet
from literary_system.analyzer.packet_compiler import compile_packets
from literary_system.analyzer.pressure_cast_planner import build_pressure_cast_plans
from literary_system.analyzer.residue_planner import build_residue_variation_plan
from literary_system.analyzer.scene_digest_builder import build_scene_digests
from literary_system.analyzer.source_tiering import assign_source_tiers
from literary_system.analyzer.state_estimator import estimate_states
from literary_system.common.enums import PacketType
from literary_system.common.logging import get_logger
from literary_system.common.time import utc_now_iso


class StandardLiteraryAnalyzer:
    def __init__(self) -> None:
        self.logger = get_logger(self.__class__.__name__)

    def analyze(self, inputs: list[dict[str, Any]], project_context: dict[str, Any]) -> dict[str, Any]:
        project_id = project_context["project_id"]
        ingested = ingest_inputs(inputs)
        tiered = assign_source_tiers(ingested)
        source_tiers = sorted({item["source_tier"] for item in tiered})
        media_type, constitution = route_media_type(project_context)

        intent_seed = {
            "project_id": project_id,
            "project_mode": project_context.get("project_mode", media_type),
            "master_seed": project_context.get("master_seed", ""),
            "media_type": media_type,
            "episode_runtime_min": project_context.get("episode_runtime_min", 60),
            "total_episode_count": project_context.get("total_episode_count", 1),
            "act_bundle_size": project_context.get("act_bundle_size", 3),
            "pdi_profile": float(project_context.get("pdi_profile", 0.5)),
            "authorial_profile_hint": project_context.get("authorial_profile_hint", ""),
            "k_hybrid_bias": project_context.get("k_hybrid_bias", "mid"),
            "forbidden_tendencies": project_context.get(
                "forbidden_tendencies",
                ["cheap_hook", "explained_emotion", "explanatory_ending"],
            ),
            "hitl_policy": project_context.get("hitl_policy", {
                "contract_review_enabled": True,
                "router_escalation_enabled": True,
                "final_baseline_promotion_enabled": True,
            }),
            "created_at": utc_now_iso(),
        }

        macro_arc_packet, act_intent_packet = compile_macro_arc_packet({**project_context, **intent_seed})
        ledgers = build_character_ledger(project_context, tiered)
        birth_results = evaluate_character_birth(ledgers, literary_state=literary_state if hasattr(self, "_literary_state") else None)
        scenes = build_scene_digests(project_context, tiered, ledgers)
        grid = build_character_grid(project_context, ledgers, scenes)
        residue_plan = build_residue_variation_plan(project_context, scenes, ledgers, act_intent_packet)
        dominant_motifs = [item["motif"] for item in residue_plan[:3] if item.get("motif")]
        before_states, after_states = estimate_states(
            scenes,
            grid,
            residue_plan,
            macro_arc_packet=macro_arc_packet,
            act_intent_packet=act_intent_packet,
            pdi_profile=intent_seed["pdi_profile"],
        )
        cast_plans = build_pressure_cast_plans(scenes, project_context, act_intent_packet)
        commander_briefing = build_commander_briefing(project_context, scenes, macro_arc_packet, act_intent_packet, dominant_motifs)

        critic_patterns = list(project_context.get("critic_pattern_codes", []))
        if act_intent_packet["anti_cliffhanger_policy"] == "forbid_generic_hook":
            critic_patterns.append("MA-02_ANTI_CLIFFHANGER_INTEGRITY")
        critic_patterns.append("MA-01_MACROARC_FIDELITY")

        packets: list[tuple[str, dict[str, Any]]] = [
            (PacketType.INTENT_SEED.value, intent_seed),
            (PacketType.FORMAT_CONSTITUTION.value, constitution),
            (PacketType.MACRO_ARC.value, macro_arc_packet),
            (PacketType.ACT_INTENT.value, act_intent_packet),
            (PacketType.COMMANDER_BRIEFING.value, commander_briefing),
        ]
        packets.extend((PacketType.CHARACTER_BIRTH_GATE.value, payload) for payload in birth_results)
        packets.extend((PacketType.CHARACTER_LEDGER.value, payload) for payload in ledgers)
        packets.append((PacketType.CHARACTER_GRID.value, grid))
        packets.extend((PacketType.SCENE_DIGEST.value, payload) for payload in scenes)
        packets.extend((PacketType.PRESSURE_CAST_PLAN.value, payload) for payload in cast_plans)
        packets.extend((PacketType.RESIDUE_VARIATION_PLAN.value, payload) for payload in residue_plan)
        packets.extend((PacketType.LITERARY_STATE_BEFORE.value, payload) for payload in before_states)
        packets.extend((PacketType.LITERARY_STATE_AFTER.value, payload) for payload in after_states)
        packets.append((PacketType.CRITIC_DECISION.value, {
            "pattern_codes": critic_patterns,
            "loss_report": project_context.get("loss_report", {
                "L_total": 0.11 if act_intent_packet["anti_cliffhanger_policy"] == "forbid_generic_hook" else 0.14,
                "L_struct": 0.02,
                "L_smell_surface": 0.02,
                "L_smell_structural": 0.03,
                "L_auth": 0.01,
                "L_reader_pull": 0.02,
                "L_reader_afterimage": 0.01,
            }),
            "loss_profile": project_context.get("loss_profile", {
                "media_type": media_type,
                "act_position": f"act_{macro_arc_packet['act_index']}",
                "authorial_profile": project_context.get("authorial_profile_hint", ""),
            }),
            "repair_plan": project_context.get("repair_plan", [
                {"pattern_code": "MA-02_ANTI_CLIFFHANGER_INTEGRITY", "repair_transform": "convert_hook_to_structural_pull"}
            ]),
            "decision": project_context.get("critic_decision", "pass"),
        }))
        packets.append((PacketType.FINAL_ACCEPTANCE.value, {
            "bundle_id": project_context.get("acceptance_bundle_id", scenes[0]["bundle_id"] if scenes else "bundle_001"),
            "release_decision": project_context.get("release_decision", "accept"),
            "fewshot_promotion_decision": project_context.get("fewshot_promotion_decision", "archive_only"),
            "graph_write_mode": project_context.get("graph_write_mode", "archive+residue"),
            "commander_notes": project_context.get("commander_notes", ""),
        }))

        bundle = compile_packets(project_id=project_id, packets=packets, source_tiers=source_tiers)
        bundle["analysis_summary"] = {
            "scene_count": len(scenes),
            "character_count": len(ledgers),
            "dominant_motifs": dominant_motifs,
            "macro_arc_mode": macro_arc_packet["macro_arc_mode"],
            "act_index": macro_arc_packet["act_index"],
            "pressure_target": act_intent_packet["pressure_target"],
            "inferred_from_raw_sources": not bool(project_context.get("scenes")),
        }
        self.logger.info("analyzed project %s into %d packets", project_id, len(bundle["packets"]))
        return bundle
