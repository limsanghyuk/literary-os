"""
V500 - AdaptiveMomentumWeights (AMW)
Gap 1: EmotionalMomentumTracker α_dim을 학습 가능 파라미터로 전환.

설계 (ADR-015 기반):
  - α_dim ∈ [0.05, 0.95] (ALPHA_MIN, ALPHA_MAX)  # [G1-FIX] ADR-017
  - 1-step SGD: α_dim += LR * grad
  - grad = (target_dim - current_dim) × advantage
  - PageRank 기반 초기화: α_dim = base × PR_weight (NIL Step 3)
  - NILStabilityModule 연동 (V512+): get_effective_lr()

4D 감정 차원: tension, sympathy, dread, catharsis
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from literary_system.emotion.emotional_momentum_tracker import (
    EmotionalMomentumTracker,
    EmotionalVector,
)

logger = logging.getLogger(__name__)

# AMW 하이퍼파라미터
ALPHA_MIN = 0.05  # [G1-FIX] ADR-017 준수: 0.30 → 0.05
ALPHA_MAX = 0.95  # [G1-FIX] ADR-017 준수: 0.80 → 0.95
LR_AMW = 0.005
DIMS = ("tension", "sympathy", "dread", "catharsis")

# 장르별 초기 α (ADR-017: 장르 조건부 초기값)
GENRE_ALPHA_INIT: Dict[str, Dict[str, float]] = {
    "melodrama":  {"tension": 0.55, "sympathy": 0.70, "dread": 0.40, "catharsis": 0.60},
    "thriller":   {"tension": 0.75, "sympathy": 0.35, "dread": 0.70, "catharsis": 0.40},
    "romcom":     {"tension": 0.40, "sympathy": 0.65, "dread": 0.30, "catharsis": 0.65},
    "family":     {"tension": 0.45, "sympathy": 0.60, "dread": 0.35, "catharsis": 0.70},
    "default":    {"tension": 0.50, "sympathy": 0.50, "dread": 0.40, "catharsis": 0.50},
}


@dataclass
class AMWState:
    """현재 α_dim 값 스냅샷."""
    alpha: Dict[str, float]
    episode_idx: int = 0
    update_count: int = 0

    def to_dict(self) -> dict:
        return {
            "alpha": {k: round(v, 4) for k, v in self.alpha.items()},
            "episode_idx": self.episode_idx,
            "update_count": self.update_count,
        }


class AdaptiveMomentumWeights:
    """
    NIL Step 3 — α_dim 학습 파라미터.

    기존 EmotionalMomentumTracker의 고정 ALPHA=0.15를 대체.
    각 감정 차원별 독립 학습률 α_dim ∈ [0.3, 0.8].

    사용법:
        amw = AdaptiveMomentumWeights(genre="melodrama")
        new_vec = amw.update(scene_record, advantage=0.3, seq_plan=None)
    """

    def __init__(
        self,
        genre: str = "default",
        stability_module=None,  # NILStabilityModule (V512+)
        pagerank_weights: Optional[Dict[str, float]] = None,
    ) -> None:
        init = GENRE_ALPHA_INIT.get(genre, GENRE_ALPHA_INIT["default"]).copy()
        # PageRank 기반 초기화 (V502+: 실제 PageRank 주입)
        if pagerank_weights:
            pr_mean = sum(pagerank_weights.values()) / max(len(pagerank_weights), 1)
            for dim in DIMS:
                pr_scale = min(2.0, pr_mean / 0.25) if pr_mean > 0 else 1.0
                init[dim] = self._clamp(init[dim] * pr_scale)

        self._alpha: Dict[str, float] = init
        self._stability = stability_module
        self._tracker = EmotionalMomentumTracker()
        self._history: List[AMWState] = []
        self._update_count = 0
        logger.debug("AMW init genre=%s alpha=%s", genre, self._alpha)

    def update(
        self,
        scene_record,
        advantage: float = 0.0,
        seq_plan=None,
        episode_idx: int = 0,
    ) -> EmotionalVector:
        """
        α_dim SGD 업데이트 + EmotionalVector 계산.

        Args:
            scene_record: 씬 레코드 (EmotionalMomentumTracker 형식)
            advantage:    R - R_baseline (PhysicsRewardBridge에서 주입)
            seq_plan:     SequencePlan (tension_target 포함)
            episode_idx:  현재 에피소드 인덱스

        Returns:
            업데이트된 EmotionalVector
        """
        # 1) LR 조정 (NILStabilityModule)
        effective_lr = LR_AMW
        if self._stability is not None:
            effective_lr = self._stability.get_effective_lr("amw", LR_AMW)

        # 2) 현재 EMT로 delta 추정 (기존 _estimate 활용)
        delta = self._tracker._estimate(scene_record, seq_plan)

        # 3) α_dim SGD 업데이트
        old_alpha = self._alpha.copy()
        for dim in DIMS:
            target = getattr(delta, dim, 0.5)
            current = getattr(self._tracker.current(), dim, 0.5)
            grad = (target - current) * advantage
            new_a = self._alpha[dim] + effective_lr * grad
            self._alpha[dim] = self._clamp(new_a)

            # NILStabilityModule 발산 감지 (V512+)
            if self._stability is not None:
                self._stability.check_divergence(dim, self._alpha[dim], old_alpha[dim])

        # 4) 학습된 α로 EMT EMA 계산
        p = self._tracker.current()
        new_vec = EmotionalVector(
            tension   = EmotionalMomentumTracker.DECAY * p.tension   + self._alpha["tension"]   * delta.tension,
            sympathy  = EmotionalMomentumTracker.DECAY * p.sympathy  + self._alpha["sympathy"]  * delta.sympathy,
            dread     = EmotionalMomentumTracker.DECAY * p.dread     + self._alpha["dread"]      * delta.dread,
            catharsis = EmotionalMomentumTracker.DECAY * p.catharsis + self._alpha["catharsis"] * delta.catharsis,
        )
        # tracker 상태 동기화
        self._tracker._current = new_vec
        self._tracker._history.append(new_vec)

        self._update_count += 1
        self._history.append(AMWState(
            alpha=self._alpha.copy(),
            episode_idx=episode_idx,
            update_count=self._update_count,
        ))
        return new_vec

    def get_alpha(self) -> Dict[str, float]:
        return self._alpha.copy()

    def get_state(self) -> AMWState:
        return AMWState(
            alpha=self._alpha.copy(),
            update_count=self._update_count,
        )

    def get_history(self) -> List[AMWState]:
        return list(self._history)

    def current_vector(self) -> EmotionalVector:
        return self._tracker.current()

    def reset(self, genre: str = "default") -> None:
        init = GENRE_ALPHA_INIT.get(genre, GENRE_ALPHA_INIT["default"]).copy()
        self._alpha = init
        self._tracker.reset()
        self._history.clear()
        self._update_count = 0

    @staticmethod
    def _clamp(v: float) -> float:
        return max(ALPHA_MIN, min(ALPHA_MAX, v))
