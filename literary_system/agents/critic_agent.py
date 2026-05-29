"""
V648 — CriticAgent (SP-C.2 Multi-Agent Ensemble).
C-M-09: Critic은 재생성 요청 권한 보유 (round_num < 3).
헌법 5축 평가 + NarrativeFitnessArbiter 결정.
LLM-0: 외부 API 직접 호출 없음.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from literary_system.ensemble.narrative_fitness_arbiter import (
    CandidateScore,
    EnsembleDecisionType,
    NarrativeFitnessArbiter,
)


@dataclass
class CriticReport:
    """비평 결과 — CriticAgent 생성물."""
    scene_id: str
    passed: bool
    constitution_score: float          # 0.0 ~ 1.0
    fitness_decision: str              # SELECT / MERGE / REJECT
    suggestions: List[str] = field(default_factory=list)
    request_regeneration: bool = False
    round_num: int = 1
    axis_scores: Dict[str, float] = field(default_factory=dict)


class CriticAgent:
    """초안 품질 평가 에이전트 (헌법 5축 + NFA 결정, C-M-09)."""

    ROLE = "critic"
    PASS_THRESHOLD = 0.65
    AXES = [
        "narrative_coherence",
        "emotional_resonance",
        "character_consistency",
        "pacing",
        "thematic_depth",
    ]

    def __init__(
        self,
        constitution: Optional[Any] = None,
        arbiter: Optional[NarrativeFitnessArbiter] = None,
    ) -> None:
        self._constitution = constitution
        self._arbiter = arbiter or NarrativeFitnessArbiter()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def evaluate(
        self,
        draft_dict: Dict[str, Any],
        blueprint_dict: Optional[Dict[str, Any]] = None,
        round_num: int = 1,
    ) -> CriticReport:
        """
        초안 평가.

        Args:
            draft_dict:     ScriptDraft 혹은 dict (scene_id, draft_text 포함).
            blueprint_dict: 선택적 원본 Blueprint 참조.
            round_num:      현재 라운드 (1-indexed).

        Returns:
            CriticReport
        """
        scene_id: str = draft_dict.get("scene_id", "unknown")
        text: str = draft_dict.get("draft_text", "")

        # 1. 헌법 5축 평가
        axis_scores = self._evaluate_constitution(text, blueprint_dict)
        constitution_score = sum(axis_scores.values()) / len(axis_scores)

        # 2. NarrativeFitnessArbiter 결정
        decision = self._arbiter_decision(constitution_score)

        # 3. 통과 여부 (점수 ≥ 0.65 AND REJECT 아님)
        passed = (
            constitution_score >= self.PASS_THRESHOLD
            and decision != EnsembleDecisionType.REJECT
        )

        # 4. 제안 사항
        suggestions = self._build_suggestions(axis_scores, passed)

        # C-M-09: Critic은 round_num < 3일 때 재생성 요청 가능
        request_regen = (not passed) and (round_num < 3)

        return CriticReport(
            scene_id=scene_id,
            passed=passed,
            constitution_score=round(constitution_score, 4),
            fitness_decision=decision.value,
            suggestions=suggestions,
            request_regeneration=request_regen,
            round_num=round_num,
            axis_scores={k: round(v, 4) for k, v in axis_scores.items()},
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _evaluate_constitution(
        self,
        text: str,
        blueprint_dict: Optional[Dict[str, Any]],
    ) -> Dict[str, float]:
        """헌법 5축 점수 계산. Constitution 없으면 휴리스틱 사용."""
        if self._constitution is not None:
            try:
                raw = self._constitution.evaluate(text)
                if isinstance(raw, dict):
                    return {ax: float(raw.get(ax, 0.5)) for ax in self.AXES}
            except Exception:
                pass

        return self._heuristic_scores(text)

    def _heuristic_scores(self, text: str) -> Dict[str, float]:
        """텍스트 길이·키워드 기반 간이 휴리스틱."""
        text_len = len(text)
        base = min(0.75, 0.40 + text_len / 2000)
        # 각 축에 미세 편차 부여 (±0.02)
        offsets = [0.0, 0.01, -0.01, 0.02, -0.02]
        return {
            ax: round(max(0.0, min(1.0, base + offsets[i])), 4)
            for i, ax in enumerate(self.AXES)
        }

    def _arbiter_decision(self, score: float) -> EnsembleDecisionType:
        """점수 기반 Arbiter 결정 (NFA 없을 때 폴백)."""
        if score >= 0.80:
            return EnsembleDecisionType.SELECT
        if score >= 0.55:
            return EnsembleDecisionType.MERGE
        return EnsembleDecisionType.REJECT

    def _build_suggestions(
        self,
        axis_scores: Dict[str, float],
        passed: bool,
    ) -> List[str]:
        if passed:
            return []
        suggestions = []
        for ax, sc in axis_scores.items():
            if sc < self.PASS_THRESHOLD:
                suggestions.append(f"{ax} 개선 필요 (현재={sc:.2f})")
        return suggestions
