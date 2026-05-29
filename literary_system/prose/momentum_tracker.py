"""V370: EmotionalMomentumTracker v2 — 4D 감정 벡터 + CharacterCluster 가중치."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional, Tuple

from literary_system.prose.emotion_behavior import EmotionalDelta


@dataclass
class MomentumEntry:
    scene_id:      str
    delta:         EmotionalDelta
    cluster_weight:float = 0.5


class EmotionalMomentumTrackerV2:
    """
    V360 EmotionalMomentumTracker 확장.
    CharacterCluster cohesion_score를 cluster_weight로 반영하여
    군집 중심 인물의 감정 강도를 차별화한다.
    """

    def __init__(self, window: int = 10) -> None:
        self._window = window
        # char_id → deque of MomentumEntry
        self._history: Dict[str, Deque[MomentumEntry]] = defaultdict(
            lambda: deque(maxlen=window)
        )
        self._cluster_weights: Dict[str, float] = {}

    # ── 클러스터 가중치 등록 ───────────────────────────────────────────
    def register_cluster_weight(self, char_id: str, cohesion_score: float) -> None:
        self._cluster_weights[char_id] = max(0.0, min(1.0, cohesion_score))

    def get_cluster_weight(self, char_id: str) -> float:
        return self._cluster_weights.get(char_id, 0.5)

    # ── 감정 상태 업데이트 ─────────────────────────────────────────────
    def update(self, scene_id: str, delta: EmotionalDelta,
               char_id: str = "") -> None:
        weight = self.get_cluster_weight(char_id)
        entry  = MomentumEntry(scene_id=scene_id, delta=delta, cluster_weight=weight)
        key    = char_id or "__global__"
        self._history[key].append(entry)

    # ── 현재 가중 상태 조회 ────────────────────────────────────────────
    def get_weighted_state(self, char_id: str = "") -> EmotionalDelta:
        """군집 가중치를 반영한 현재 감정 상태 반환."""
        key     = char_id or "__global__"
        history = list(self._history.get(key, []))
        if not history:
            return EmotionalDelta()

        weight  = self.get_cluster_weight(char_id)
        latest  = history[-1].delta
        # 군집 중심(weight↑)일수록 최근 감정을 더 강하게 반영
        blend   = min(0.5 + weight * 0.5, 1.0)

        if len(history) == 1:
            return EmotionalDelta(
                tension=latest.tension * blend,
                sympathy=latest.sympathy * blend,
                dread=latest.dread * blend,
                catharsis=latest.catharsis * blend,
            )

        prev = history[-2].delta
        return EmotionalDelta(
            tension=  round(prev.tension  * (1 - blend) + latest.tension  * blend, 3),
            sympathy= round(prev.sympathy * (1 - blend) + latest.sympathy * blend, 3),
            dread=    round(prev.dread    * (1 - blend) + latest.dread    * blend, 3),
            catharsis=round(prev.catharsis*(1 - blend) + latest.catharsis * blend, 3),
        )

    # ── 감정 아크 조회 ─────────────────────────────────────────────────
    def momentum_arc(self, char_id: str = "",
                     n_scenes: int = 5) -> List[float]:
        """n_scenes 이동 평균 긴장 곡선 (tension 기준) 반환."""
        key     = char_id or "__global__"
        history = list(self._history.get(key, []))[-n_scenes:]
        return [round(e.delta.tension, 3) for e in history]

    def stats(self, char_id: str = "") -> Dict[str, float]:
        key     = char_id or "__global__"
        history = list(self._history.get(key, []))
        if not history:
            return {"count": 0, "avg_tension": 0.0}
        tensions = [e.delta.tension for e in history]
        import statistics
        return {
            "count":        len(history),
            "avg_tension":  round(statistics.mean(tensions), 3),
            "max_tension":  round(max(tensions), 3),
            "cluster_weight": self.get_cluster_weight(char_id),
        }
