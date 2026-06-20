"""learning/pairing/credit.py — P4 크레딧 할당(스텁).

거시아크 단위 크레딧 분배 계약은 P4(HIER-PLANNER) 설계 미존재 → 빈칸. P0은 인터페이스만
제공한다. 현 스텁은 쌍 내 씬에 균등 분배(uniform). 실 구현은 P4에서 교체.
"""
from __future__ import annotations
from typing import Dict, List


class UniformCreditAssigner:
    """씬 수로 균등 분배. P4 HIER-PLANNER 도입 시 아크-인지 분배로 교체."""
    name = "uniform-stub"

    def assign(self, scene_ids: List[str], pair_reward: float = 1.0) -> Dict[str, float]:
        n = len(scene_ids)
        if n == 0:
            return {}
        share = pair_reward / n
        return {sid: share for sid in scene_ids}
