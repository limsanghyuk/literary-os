"""
critic/alignment_monitor.py — Critic↔인간 GT 일치율 (V757, ADR-217)

Gold 쌍에서 critic 앙상블 판정 vs 인간 GT 다수결 일치율 측정 → G_LLM1_ALIGNMENT(≥0.80).
인간 GT가 LLM critic을 캘리브레이션하는 절대 닻(human_gt 재사용).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from literary_system.critic.base import CriticContext
from literary_system.critic.ensemble import CriticEnsemble
from literary_system.validation.human_gt import majority_by_pair

ALIGNMENT_MIN: float = 0.80


@dataclass(frozen=True)
class AlignmentReport:
    n_pairs: int
    agreement_rate: float
    passed: bool
    per_pair: List[Dict] = field(default_factory=list)

    @property
    def summary(self) -> str:
        return (f"Critic↔인간 일치율={self.agreement_rate:.3f} "
                f"[{'PASS' if self.passed else 'FAIL'}] (min {ALIGNMENT_MIN}, n={self.n_pairs})")


def _human_majority_ab(gt_records) -> Dict[str, str]:
    """인간 GT 다수결(left/right/tie) → a/b/tie (a=left, b=right)."""
    maj = majority_by_pair(gt_records)
    return {pid: {"left": "a", "right": "b", "tie": "tie"}[w] for pid, w in maj.items()}


def measure_alignment(pairs: List[Tuple[str, str, str, str, str]],
                      ensemble: CriticEnsemble,
                      ctx_of: Callable[[str], CriticContext],
                      gt_records) -> AlignmentReport:
    """pairs: [(pair_id, a_id, b_id, a_text, b_text)] (a=left, b=right 규약)."""
    human = _human_majority_ab(gt_records)
    rows: List[Dict] = []
    agree = n = 0
    for pid, a_id, b_id, a_text, b_text in pairs:
        hw = human.get(pid)
        if hw is None:
            continue
        cw = ensemble.evaluate(a_text, b_text, ctx_of(pid), a_id, b_id).winner
        n += 1
        match = (cw == hw)
        agree += int(match)
        rows.append({"pair": pid, "critic": cw, "human": hw, "match": match})
    rate = agree / n if n else 0.0
    return AlignmentReport(n_pairs=n, agreement_rate=round(rate, 4),
                           passed=rate >= ALIGNMENT_MIN, per_pair=rows)
