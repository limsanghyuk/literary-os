"""
V383 — ConflictCollisionCalculus
씬별 갈등 충돌 강도 계산. LLM 0회. 결정론적.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Tuple


@dataclass
class ConflictCollisionResult:
    conflict_intensity: float          # 0.0 ~ 1.0
    collision_pairs:    List[Tuple[str, str]] = field(default_factory=list)
    stagnation_warning: bool = False


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


class ConflictCollisionCalculus:
    """
    CharacterCluster 기반 갈등 강도 계산.
    conflict_edges: NKG의 CONFLICT_EDGE 타입 쌍 목록.
    cluster_weights: {char_id: weight} — CharacterCluster.cluster_weight
    """

    def calculate(
        self,
        character_ids:   List[str],
        conflict_edges:  List[Tuple[str, str]],
        cluster_weights: Dict[str, float],
    ) -> ConflictCollisionResult:
        if not character_ids:
            return ConflictCollisionResult(
                conflict_intensity=0.0,
                collision_pairs=[],
                stagnation_warning=True,
            )

        char_set = set(character_ids)
        valid_pairs = [
            (a, b) for a, b in conflict_edges
            if a in char_set and b in char_set
        ]

        if not valid_pairs:
            return ConflictCollisionResult(
                conflict_intensity=0.0,
                collision_pairs=[],
                stagnation_warning=True,
            )

        # 가중 합산
        weighted_sum = 0.0
        for a, b in valid_pairs:
            wa = cluster_weights.get(a, 0.5)
            wb = cluster_weights.get(b, 0.5)
            weighted_sum += wa * wb

        # 정규화: 최대 가능 가중치 = 모든 캐릭터 쌍의 최대 조합
        n = len(character_ids)
        max_pairs = max(n * (n - 1) / 2, 1)
        max_weight = max_pairs * 1.0  # 각 쌍 최대 가중치 = 1.0 * 1.0
        intensity = _clamp(weighted_sum / max_weight, 0.0, 1.0)

        return ConflictCollisionResult(
            conflict_intensity  = intensity,
            collision_pairs     = valid_pairs,
            stagnation_warning  = (intensity < 0.1),
        )
