"""
critic/arbitration.py — Arbitration Protocol v1 (V759, ADR-219)

공식(구조 게이트)↔critic(LLM) 불일치를 3분기로 중재:
  - agree            : 공식=critic
  - formula_defect   : 인간이 critic 편 → 공식 recalibrate 신호
  - critic_defect    : 인간이 공식 편 → critic 프롬프트 개선 신호
  - genuine_ambiguous: 인간 tie → 진성 모호
  - pending          : 인간 미판정 → disagreement_queue(인간 큐)
인간 판정 = 최고가치 학습신호(human_gt). 공식 winner=LOSConstitution R 비교.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

R_TIE_EPS: float = 0.02


@dataclass(frozen=True)
class DisagreementRecord:
    pair_id: str
    formula_winner: str           # a|b|tie
    critic_winner: str
    classification: str
    human_winner: Optional[str] = None
    r_gap: Optional[float] = None


def classify(formula_w: str, critic_w: str, human_w: Optional[str] = None) -> str:
    if formula_w == critic_w:
        return "agree"
    if human_w is None:
        return "pending"
    if human_w == "tie":
        return "genuine_ambiguous"
    if human_w == critic_w:
        return "formula_defect"
    if human_w == formula_w:
        return "critic_defect"
    return "genuine_ambiguous"


def formula_winner(a_text: str, b_text: str, constitution=None) -> Tuple[str, float]:
    """공식 R 비교 → (winner a|b|tie, R_gap)."""
    if constitution is None:
        from literary_system.constitution.los_constitution import LOSConstitution
        constitution = LOSConstitution()
    ra = constitution.score_scene_full(a_text).total
    rb = constitution.score_scene_full(b_text).total
    gap = round(ra - rb, 4)
    if abs(gap) < R_TIE_EPS:
        return "tie", gap
    return ("a" if ra > rb else "b"), gap


def arbitrate(items: List[Dict]) -> Dict:
    """items: [{pair_id, formula_winner, critic_winner, human_winner?, r_gap?}]
       → records + disagreement_queue(pending) + 분류 카운트."""
    records: List[DisagreementRecord] = []
    queue: List[str] = []
    for it in items:
        cls = classify(it["formula_winner"], it["critic_winner"], it.get("human_winner"))
        rec = DisagreementRecord(
            pair_id=it["pair_id"], formula_winner=it["formula_winner"],
            critic_winner=it["critic_winner"], classification=cls,
            human_winner=it.get("human_winner"), r_gap=it.get("r_gap"))
        records.append(rec)
        if cls == "pending":
            queue.append(rec.pair_id)
    return {"records": records, "disagreement_queue": queue,
            "counts": dict(Counter(r.classification for r in records))}
