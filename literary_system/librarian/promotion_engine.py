from __future__ import annotations

from typing import Any

from literary_system.common.enums import PromotionDecision


class PromotionEngine:
    def decide(self, bundle: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
        final = next((p["payload"] for p in bundle["packets"] if p["packet_type"] == "final_acceptance_packet"), {})
        critic = next((p["payload"] for p in bundle["packets"] if p["packet_type"] == "critic_decision_packet"), {})
        requested = final.get("fewshot_promotion_decision", PromotionDecision.ARCHIVE_ONLY.value)
        l_total = critic.get("loss_report", {}).get("L_total", 1.0)

        decision = PromotionDecision.ARCHIVE_ONLY.value
        if requested == PromotionDecision.CANONICAL_FEWSHOT.value and critic:
            decision = PromotionDecision.CANONICAL_FEWSHOT.value if l_total <= 0.12 else PromotionDecision.CANDIDATE_FEWSHOT.value
        elif requested == PromotionDecision.CANDIDATE_FEWSHOT.value:
            decision = PromotionDecision.CANDIDATE_FEWSHOT.value if l_total <= 0.2 else PromotionDecision.ARCHIVE_ONLY.value

        return {
            "requested": requested,
            "resolved": decision,
            "reason": f"critic L_total={l_total:.3f}",
        }
