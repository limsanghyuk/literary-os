"""
V313→V322: PromptAssembler
사전 설계층의 모든 패킷을 V312 런타임 호출용 최소 프롬프트로 조립.
bundle.json 포맷으로 출력 → V312 node_v311_bundle_parser 호환.
LLM 0회.
"""
from __future__ import annotations

from typing import Any


class PromptAssembler:
    """
    설계 패킷 → V312 bundle.json 호환 포맷 조립.
    분리 원칙: "브리핑은 브리핑, 렌더링은 렌더링."
    """

    def assemble(
        self,
        episode_no: int,
        seed_contract: dict[str, Any],
        macroarc_packet: dict[str, Any],
        character_grid: dict[str, Any],
        residue_plan: dict[str, Any],
        style_dna: dict[str, Any],
        literary_state_before: dict[str, float] | None = None,
        fewshot_refs: list[str] | None = None,
        commander_briefing: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        V312 bundle_parser 입력 포맷으로 조립.
        V311의 9개 packet 포맷을 그대로 준수.
        """
        pid = seed_contract.get("project_id", "proj_unknown")

        # ── 기본 Literary State ────────────────────
        if not literary_state_before:
            literary_state_before = {
                "SP": 0.30 + episode_no * 0.04,
                "RU": 0.60,
                "ET": 0.0,
                "RD": 0.10,
                "RT": 0.30,
                "AC": 0.70,
                "RO": 0.55,
                "MR": 0.10,
            }

        # ── Episode Intent ─────────────────────────
        intents = macroarc_packet.get("episode_intents", [])
        ep_intent = next(
            (i for i in intents if i.get("episode_no") == episode_no),
            {
                "episode_no": episode_no,
                "intent": "raise_pressure_without_release",
                "reveal_budget": 0.20,
                "pressure_target": 0.55,
            }
        )

        # ── Commander Briefing 기본값 ──────────────
        if not commander_briefing:
            commander_briefing = {
                "full_arc_strategy": macroarc_packet.get("macro_goal", ""),
                "current_bundle_strategy": ep_intent.get("intent", ""),
                "episode_positioning": f"EP{episode_no:02d}",
                "scene_summary": seed_contract.get("user_prompt", ""),
                "decision_point": "to_be_inferred",
            }

        # ── render_instruction 조립 ────────────────
        genre = seed_contract.get("genre", "general_drama")
        fmt   = seed_contract.get("format_type", "screenplay")
        style_name = style_dna.get("profile_name", "restrained_low_burn")
        forbidden  = style_dna.get("forbidden", [])
        preferred  = style_dna.get("preferred", [])
        pdi_target = style_dna.get("pdi_baseline", 0.35)

        render_instruction = (
            f"Write episode {episode_no} as {fmt}. "
            f"Genre: {genre}. "
            f"Act intent: {ep_intent.get('intent', '')}. "
            f"PDI target: {pdi_target} (action/gesture > emotion explanation). "
            f"Style: {style_name}. "
            f"Forbidden: {', '.join(forbidden[:5])}. "
            f"Preferred: {', '.join(preferred[:3])}. "
            f"Anti-cliffhanger policy: {macroarc_packet.get('anti_cliffhanger_policy', True)}. "
            f"No cheap hook endings."
        )

        # ── V312 bundle.json 포맷 조립 ─────────────
        bundle = {
            "project_id": pid,
            "episode_no": episode_no,
            "packets": [
                {
                    "packet_type": "intent_seed_packet",
                    "payload": {
                        "project_id": pid,
                        "seed_text": seed_contract.get("user_prompt", ""),
                        "media_type": fmt,
                        "pdi_profile": pdi_target,
                        "genre": genre,
                    },
                },
                {
                    "packet_type": "format_constitution_packet",
                    "payload": {
                        "media_type": fmt,
                        "forbidden_rules": seed_contract.get("forbidden_rules", []),
                    },
                },
                {
                    "packet_type": "macro_arc_packet",
                    "payload": {
                        **macroarc_packet,
                        "episode_index": episode_no,
                        "act_index": ep_intent.get("act_index", 1),
                        "PDI_arc": {"target": pdi_target},
                        "reveal_budget": f"이번 화 {ep_intent.get('reveal_budget', 0.2)}",
                        "residue_recall_budget": "3개 이하",
                        "act_climax_type": ep_intent.get("intent", "quiet_revelation"),
                    },
                },
                {
                    "packet_type": "act_intent_packet",
                    "payload": ep_intent,
                },
                {
                    "packet_type": "character_ledger",
                    "payload": character_grid,
                },
                {
                    "packet_type": "character_grid",
                    "payload": character_grid,
                },
                {
                    "packet_type": "scene_digest",
                    "payload": {
                        "scene_id": f"EP{episode_no:02d}_ACT01",
                        "action_kind": "revelatory_action"
                        if episode_no % 3 == 0 else "decisive_action",
                        "scene_focus": ep_intent.get("intent", ""),
                        "active_characters": [
                            c.get("char_id", "")
                            for c in character_grid.get("characters", [])[:3]
                        ],
                    },
                },
                {
                    "packet_type": "residue_variation_plan",
                    "payload": residue_plan,
                },
                {
                    "packet_type": "commander_briefing",
                    "payload": commander_briefing,
                },
            ],
            "state_before": literary_state_before,
            "render_instruction": render_instruction,
            "fewshot_refs": fewshot_refs or [],
            "style_dna": style_dna,
        }

        return bundle

    def to_v312_input(self, bundle: dict[str, Any]) -> dict[str, Any]:
        """
        bundle.json → V312 SovereignState 초기화 dict.
        V312 node_v311_bundle_parser 호환.
        """
        return {
            "v311_mode": True,
            "v311_bundle_json": bundle,
            "seed_text": bundle.get("render_instruction", ""),
            "v310_mode": True,
        }
