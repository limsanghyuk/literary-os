"""
V324 - MAEOrchestrator  (Phase 1)
Alpha/Beta/Gamma 3에이전트 앙상블 → 2/3 합의 프로토콜.

설계 원칙 (P3 LLM 0회, P4 MAE 앙상블, P5 계수 추적성):
  - MAEResult는 LearnedCoefficientStore.record() metadata에 첨부
  - 합의 기준: 3에이전트 중 2개 이상 PASS
  - LLM 0회. 완전 로컬.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List

from literary_system.evaluation.mae_agents import (
    AlphaAgent, BetaAgent, GammaAgent, AgentVerdict,
)
from literary_system.evaluation.scene_metrics_collector import SceneMetrics
from literary_system.validation.coefficient_mapper import MAEWeights


# ════════════════════════════════════════════════════════════════════
# MAEResult
# ════════════════════════════════════════════════════════════════════

@dataclass
class MAEResult:
    """MAEOrchestrator 평가 결과."""
    scene_id: str
    consensus: bool                   # True = 2/3 이상 PASS
    votes: List[AgentVerdict]
    alpha: AgentVerdict
    beta: AgentVerdict
    gamma: AgentVerdict
    timestamp: float = field(default_factory=time.time)

    @property
    def pass_count(self) -> int:
        return sum(1 for v in self.votes if v.passed)

    def to_dict(self) -> dict:
        return {
            "scene_id": self.scene_id,
            "consensus": self.consensus,
            "pass_count": self.pass_count,
            "votes": [v.to_dict() for v in self.votes],
            "alpha": self.alpha.to_dict(),
            "beta": self.beta.to_dict(),
            "gamma": self.gamma.to_dict(),
            "timestamp": self.timestamp,
        }


# ════════════════════════════════════════════════════════════════════
# MAEOrchestrator
# ════════════════════════════════════════════════════════════════════

class MAEOrchestrator:
    """
    3에이전트 앙상블 조율자.

    MAEWeights로 에이전트 가중치를 설정하고,
    SceneMetrics를 받아 각 에이전트의 평가를 수집한 후
    2/3 합의로 최종 판정을 내린다.
    """

    CONSENSUS_THRESHOLD = 2  # 3개 중 2개 이상 PASS

    def __init__(self, weights: MAEWeights | None = None) -> None:
        w = weights or MAEWeights()
        self._alpha = AlphaAgent(weight=w.alpha_logic)
        self._beta = BetaAgent(weight=w.beta_char)
        self._gamma = GammaAgent(weight=w.gamma_tension)
        self._weights = w
        self._history: List[MAEResult] = []

    def evaluate(self, scene_id: str, metrics: SceneMetrics) -> MAEResult:
        """씬 평가 실행 → MAEResult 반환."""
        alpha_v = self._alpha.evaluate(scene_id, metrics)
        beta_v = self._beta.evaluate(scene_id, metrics)
        gamma_v = self._gamma.evaluate(scene_id, metrics)

        votes = [alpha_v, beta_v, gamma_v]
        pass_count = sum(1 for v in votes if v.passed)
        consensus = pass_count >= self.CONSENSUS_THRESHOLD

        result = MAEResult(
            scene_id=scene_id,
            consensus=consensus,
            votes=votes,
            alpha=alpha_v,
            beta=beta_v,
            gamma=gamma_v,
        )
        self._history.append(result)
        return result

    def update_weights(self, weights: MAEWeights) -> None:
        """CoefficientMapper.map_to_mae() 결과로 가중치 갱신."""
        self._alpha.weight = weights.alpha_logic
        self._beta.weight = weights.beta_char
        self._gamma.weight = weights.gamma_tension
        self._weights = weights

    def get_history(self) -> List[MAEResult]:
        """평가 이력 반환."""
        return list(self._history)

    def clear_history(self) -> None:
        self._history.clear()
