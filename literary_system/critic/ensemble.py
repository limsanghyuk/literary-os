"""
critic/ensemble.py — 5축 Critic 합의 앙상블 (V756, ADR-216) = Pass7 패널 승격.

5축 critic verdict → pairwise BT 합의(절대점수 금지). RAG 필수(CriticContext).
Pass7 판정자로 주입 가능: ensemble.as_judge() → judge(draft, ref) 콜러블.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from literary_system.critic.base import CriticContext, CriticVerdict, aggregate_verdicts
from literary_system.critic.llm_critics import make_ensemble


@dataclass(frozen=True)
class EnsembleResult:
    winner: str                       # "a" | "b" | "tie"  (BT 합의)
    consensus: Dict[str, float]
    per_axis: List[CriticVerdict]
    n_axes: int
    axis_winners: Dict[str, str] = field(default_factory=dict)


class CriticEnsemble:
    """5축 LLM critic 합의. RAG 필수·쌍대만."""
    def __init__(self, llm: Optional[Callable[[str], str]] = None, seed: Optional[int] = None) -> None:
        self._critics = make_ensemble(llm=llm, seed=seed)

    def evaluate(self, a_text: str, b_text: str, ctx: CriticContext,
                 a_id: str = "a", b_id: str = "b") -> EnsembleResult:
        verdicts = [c.evaluate(a_text, b_text, ctx) for c in self._critics]
        consensus = aggregate_verdicts(verdicts, a_id, b_id)
        sa, sb = consensus.get(a_id, 0.0), consensus.get(b_id, 0.0)
        winner = "a" if sa > sb else ("b" if sb > sa else "tie")
        return EnsembleResult(
            winner=winner, consensus=consensus, per_axis=verdicts, n_axes=len(verdicts),
            axis_winners={v.axis: v.winner for v in verdicts})

    def as_judge(self, ctx: CriticContext) -> Callable[[str, str], str]:
        """Pass7 판정자 어댑터: judge(draft, ref) → 'draft'|'ref'|'tie'."""
        def judge(draft: str, ref: str) -> str:
            r = self.evaluate(draft, ref, ctx, "draft", "ref")
            return {"a": "draft", "b": "ref", "tie": "tie"}[r.winner]
        return judge
