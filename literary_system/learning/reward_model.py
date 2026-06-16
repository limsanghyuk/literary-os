"""
learning/reward_model.py — E.4 쌍대 보상모델 (V763, ADR-223)

생성 draft가 실명작 레퍼런스 풀을 이기는 비율을 보상으로 산출(절대점수 금지).
critic 앙상블(또는 주입 judge)이 쌍대 판정 → 보상 R(x) ∈ [0,1].
DPO는 보상 불요(쌍대 직접); 본 보상모델은 RLHF/PPO·loop-C 격차 추적용.
보상↑ = 생성이 명작에 근접(loop-C 학습 목표).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence, Tuple

from literary_system.learning.loop_c import PreferencePair, generation_win_rate


@dataclass(frozen=True)
class RewardScore:
    draft_id: str
    reward: float          # [0,1] draft가 레퍼런스 풀을 이기는 비율(tie=0.5)
    n_refs: int


class PairwiseRewardModel:
    """쌍대 선호 보상. judge: (draft, ref) -> 'draft'|'ref'|'tie'."""
    def __init__(self, judge: Callable[[str, str], str]) -> None:
        if judge is None:
            raise ValueError("judge 콜러블 필요(critic 앙상블 as_judge 등)")
        self._judge = judge

    def reward_vs_refs(self, draft: str, refs: Sequence[str], draft_id: str = "draft") -> RewardScore:
        if not refs:
            return RewardScore(draft_id, 0.0, 0)
        s = 0.0
        for r in refs:
            v = self._judge(draft, r)
            s += 1.0 if v == "draft" else (0.5 if v == "tie" else 0.0)
        return RewardScore(draft_id, round(s / len(refs), 4), len(refs))

    def batch(self, items: List[Tuple[str, str, Sequence[str]]]) -> List[RewardScore]:
        """items: [(draft_id, draft, refs)] → RewardScore[]."""
        return [self.reward_vs_refs(d, refs, did) for did, d, refs in items]


def reward_from_pairs(pairs: List[PreferencePair]) -> float:
    """누적 선호쌍 → 스칼라 보상(생성 승률). loop-C 격차 추적."""
    return generation_win_rate(pairs)


def ensemble_reward_model(llm, ctx, n_judges: int = 3) -> PairwiseRewardModel:
    """critic 앙상블(3페르소나) 기반 보상모델 생성."""
    from literary_system.critic.ensemble import CriticEnsemble
    return PairwiseRewardModel(judge=CriticEnsemble(llm=llm, n_judges=n_judges).as_judge(ctx))
