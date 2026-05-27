"""
V652 — AgentEnsembleEvaluator (SP-C.2 Multi-Agent Ensemble).
여러 CoordinatorResult 후보를 집계·비교해 최선의 씬을 선택.
NarrativeFitnessArbiter와 연동하여 SELECT/MERGE/REJECT 결정.
LLM-0: 외부 API 직접 호출 없음. ADR-112.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 평가 축 정의 (C-M-09 헌법 5축)
EVAL_AXES = [
    "narrative_coherence",
    "emotional_resonance",
    "character_consistency",
    "pacing",
    "thematic_depth",
]


@dataclass
class EnsembleEvalResult:
    """앙상블 평가 결과 — 최종 선택 씬 포함."""
    selected_scene_id: str
    selected_text:     str
    aggregate_score:   float          # 0.0 ~ 1.0
    decision:          str            # SELECT / MERGE / REJECT
    candidate_scores:  Dict[str, float] = field(default_factory=dict)
    merge_sources:     List[str]       = field(default_factory=list)  # MERGE 시 원본 씬 IDs
    evaluation_note:   str             = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected_scene_id": self.selected_scene_id,
            "selected_text":     self.selected_text,
            "aggregate_score":   self.aggregate_score,
            "decision":          self.decision,
            "candidate_scores":  self.candidate_scores,
            "merge_sources":     self.merge_sources,
            "evaluation_note":   self.evaluation_note,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EnsembleEvalResult":
        return cls(
            selected_scene_id=d["selected_scene_id"],
            selected_text=d.get("selected_text", ""),
            aggregate_score=d.get("aggregate_score", 0.0),
            decision=d.get("decision", "UNKNOWN"),
            candidate_scores=d.get("candidate_scores", {}),
            merge_sources=d.get("merge_sources", []),
            evaluation_note=d.get("evaluation_note", ""),
        )


class AgentEnsembleEvaluator:
    """
    Multi-Agent Ensemble 최종 평가자.

    - 복수의 CoordinatorResult 후보를 입력받아 최선을 선택.
    - NarrativeFitnessArbiter를 통해 SELECT / MERGE / REJECT 결정.
    - MERGE 시 가장 높은 점수를 가진 두 후보의 텍스트를 결합.
    - REJECT 시 가장 높은 점수 후보를 최선으로 사용 (항상 산출물 반환).
    """

    SELECT_THRESHOLD: float = 0.80  # NarrativeFitnessArbiter SELECT 임계값
    MERGE_THRESHOLD:  float = 0.55  # NarrativeFitnessArbiter MERGE 임계값

    def __init__(self, arbiter=None) -> None:
        self._arbiter = arbiter

    def _get_arbiter(self):
        if self._arbiter is None:
            try:
                from literary_system.ensemble.narrative_fitness_arbiter import (
                    NarrativeFitnessArbiter,
                )
                self._arbiter = NarrativeFitnessArbiter()
            except Exception as exc:  # noqa: BLE001
                logger.warning("NarrativeFitnessArbiter 로드 실패: %s", exc)
                self._arbiter = _StubArbiter()
        return self._arbiter

    def evaluate(
        self,
        candidates: List[Dict[str, Any]],
    ) -> EnsembleEvalResult:
        """
        후보 목록을 평가해 최선의 씬을 반환.

        Parameters
        ----------
        candidates : list[dict]
            CoordinatorResult.to_dict() 형식의 후보 목록.
            각 항목에 scene_id, final_text, last_critic_score 포함 필요.

        Returns
        -------
        EnsembleEvalResult
        """
        if not candidates:
            return EnsembleEvalResult(
                selected_scene_id="empty",
                selected_text="",
                aggregate_score=0.0,
                decision="REJECT",
                evaluation_note="후보 없음",
            )

        # 1. 각 후보 점수 계산
        scored: List[Dict[str, Any]] = []
        for cand in candidates:
            scene_id = cand.get("scene_id", "unknown")
            score    = self._score_candidate(cand)
            scored.append({"scene_id": scene_id, "score": score, "cand": cand})

        scored.sort(key=lambda x: x["score"], reverse=True)
        best = scored[0]

        # 2. NarrativeFitnessArbiter 결정
        decision = self._arbiter_decision(best["score"])

        # 3. MERGE: 상위 2개 텍스트 결합
        merge_sources: List[str] = []
        final_text = best["cand"].get("final_text", "")
        if decision == "MERGE" and len(scored) >= 2:
            second = scored[1]
            final_text = self._merge_texts(
                best["cand"].get("final_text", ""),
                second["cand"].get("final_text", ""),
            )
            merge_sources = [best["scene_id"], second["scene_id"]]

        candidate_scores = {s["scene_id"]: round(s["score"], 4) for s in scored}

        # REJECT 시 텍스트·씬 ID를 비움 (안전 기본값)
        if decision == "REJECT":
            final_text = ""
            selected_id = ""
        else:
            selected_id = best["scene_id"]

        return EnsembleEvalResult(
            selected_scene_id=selected_id,
            selected_text=final_text,
            aggregate_score=round(best["score"], 4),
            decision=decision,
            candidate_scores=candidate_scores,
            merge_sources=merge_sources,
            evaluation_note=f"최고 점수 후보 {best['scene_id']} ({decision})",
        )

    def _score_candidate(self, cand: Dict[str, Any]) -> float:
        """후보 점수 계산 (critic_score 기반 + 텍스트 길이 보정)."""
        critic_score = float(cand.get("last_critic_score", 0.0))
        text = cand.get("final_text", "")
        text_len = len(text)
        # 텍스트 길이 보너스 (최대 +0.05, 1000자 기준)
        length_bonus = min(0.05, text_len / 1000 * 0.05)
        raw = critic_score + length_bonus
        return max(0.0, min(1.0, raw))

    def _arbiter_decision(self, score: float) -> str:
        if score >= self.SELECT_THRESHOLD:
            return "SELECT"
        if score >= self.MERGE_THRESHOLD:
            return "MERGE"
        return "REJECT"

    def _merge_texts(self, text_a: str, text_b: str) -> str:
        """두 텍스트를 단락 수준에서 병합 (단순 교차 병합)."""
        lines_a = [l for l in text_a.splitlines() if l.strip()]
        lines_b = [l for l in text_b.splitlines() if l.strip()]
        merged: List[str] = []
        max_len = max(len(lines_a), len(lines_b))
        for i in range(max_len):
            if i < len(lines_a):
                merged.append(lines_a[i])
            if i < len(lines_b) and lines_b[i] not in merged:
                merged.append(lines_b[i])
        return "\n".join(merged) if merged else text_a


class _StubArbiter:
    """NarrativeFitnessArbiter 미사용 시 폴백."""
    def decide(self, score: float) -> str:
        if score >= 0.80:
            return "SELECT"
        if score >= 0.55:
            return "MERGE"
        return "REJECT"
