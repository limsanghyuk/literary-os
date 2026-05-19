"""
V389 — NarrativeFitnessArbiter.
GPT Stage96 Provider Ensemble 점수 공식 흡수.
REJECT / SELECT / MERGE 결정.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EnsembleDecisionType(str, Enum):
    REJECT = "REJECT"
    SELECT = "SELECT"
    MERGE  = "MERGE"


@dataclass
class CandidateScore:
    provider_name:         str
    narrative_fitness:     float   # NarrativeFitnessScore (0~10, 정규화 0~1)
    reader_surface:        float
    agent_benchmark:       float
    provider_reliability:  float
    cost_efficiency:       float
    leakage_risk:          float
    branchpoint_regression: float
    style_drift:           float
    total_score:           float = 0.0

    def __post_init__(self):
        self.total_score = self._compute()

    def _compute(self) -> float:
        """GPT Stage96 Ensemble 점수 공식."""
        return (
            (self.narrative_fitness / 10.0)  * 0.28 +
            self.reader_surface               * 0.16 +
            self.agent_benchmark              * 0.12 +
            self.provider_reliability         * 0.18 +
            self.cost_efficiency              * 0.08
            - self.leakage_risk
            - self.branchpoint_regression
            - self.style_drift
        )


@dataclass
class EnsembleDecision:
    decision_type:    EnsembleDecisionType
    selected:         Optional[str]           = None   # SELECT 시 provider_name
    merge_map:        Dict[str, str]          = field(default_factory=dict)  # MERGE 시 씬→provider
    scores:           List[CandidateScore]    = field(default_factory=list)
    reason:           str                     = ""


_REJECT_THRESHOLD  = 0.30   # 최고 점수가 이 미만이면 REJECT
_SELECT_MARGIN     = 0.10   # 1위-2위 점수 차가 이 이상이면 SELECT, 미만이면 MERGE


class NarrativeFitnessArbiter:
    """
    복수 Provider 후보 중재.
    multi_llm_router와 연동하여 최적 결과 선택.
    """

    def __init__(
        self,
        reject_threshold: float = _REJECT_THRESHOLD,
        select_margin:    float = _SELECT_MARGIN,
    ) -> None:
        self._reject_threshold = reject_threshold
        self._select_margin    = select_margin

    def arbitrate(self, candidates: List[CandidateScore]) -> EnsembleDecision:
        if not candidates:
            return EnsembleDecision(
                decision_type = EnsembleDecisionType.REJECT,
                reason = "No candidates provided",
            )

        ranked = sorted(candidates, key=lambda c: -c.total_score)
        best   = ranked[0]

        if best.total_score < self._reject_threshold:
            return EnsembleDecision(
                decision_type = EnsembleDecisionType.REJECT,
                scores        = ranked,
                reason = f"Best score {best.total_score:.3f} < threshold {self._reject_threshold}",
            )

        if len(ranked) == 1:
            return EnsembleDecision(
                decision_type = EnsembleDecisionType.SELECT,
                selected      = best.provider_name,
                scores        = ranked,
                reason = "Single candidate auto-selected",
            )

        margin = best.total_score - ranked[1].total_score

        if margin >= self._select_margin:
            return EnsembleDecision(
                decision_type = EnsembleDecisionType.SELECT,
                selected      = best.provider_name,
                scores        = ranked,
                reason = f"Clear winner by margin {margin:.3f} >= {self._select_margin}",
            )
        else:
            # MERGE: 두 후보의 씬별 최고값 선택
            merge_map = self._build_merge_map(ranked[0], ranked[1])
            return EnsembleDecision(
                decision_type = EnsembleDecisionType.MERGE,
                merge_map     = merge_map,
                scores        = ranked,
                reason = f"Close scores (margin={margin:.3f}), merging top 2",
            )

    def _build_merge_map(self, c1: CandidateScore, c2: CandidateScore) -> Dict[str, str]:
        """간단한 MERGE 전략: 피처별 높은 점수 provider를 씬에 배정."""
        merge = {}
        if c1.narrative_fitness >= c2.narrative_fitness:
            merge['narrative'] = c1.provider_name
        else:
            merge['narrative'] = c2.provider_name
        if c1.reader_surface >= c2.reader_surface:
            merge['surface'] = c1.provider_name
        else:
            merge['surface'] = c2.provider_name
        return merge
