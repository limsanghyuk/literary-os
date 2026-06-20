"""learning/pairing/report.py — 빌더 리포트(임계위반·E4 reject·혼합비 실측)."""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from .strategies.base import PairVerdict, MIX


@dataclass
class BuildReport:
    total_in: int
    accepted: int
    dropped_length: int
    dropped_e4: int
    soft_flags: int
    mix_actual: Dict[str, float]
    mix_target: Dict[str, float]
    e4_breakdown: Dict[str, int]
    held_count: int = 0

    def to_dict(self) -> dict:
        return {
            "total_in": self.total_in, "accepted": self.accepted,
            "dropped_length": self.dropped_length, "dropped_e4": self.dropped_e4,
            "soft_flags": self.soft_flags,
            "mix_actual": self.mix_actual, "mix_target": self.mix_target,
            "e4_breakdown": self.e4_breakdown, "held_count": self.held_count,
        }


def build_report(verdicts: Sequence[PairVerdict], held_count: int = 0) -> BuildReport:
    acc = [v for v in verdicts if v.accept]
    drop_len = sum(1 for v in verdicts if v.drop_reason == "length")
    drop_e4 = sum(1 for v in verdicts if v.drop_reason == "e4_reject")
    soft = sum(1 for v in acc if v.soft_flag)
    strat_counts = Counter(v.strategy for v in acc)
    n = max(len(acc), 1)
    mix_actual = {k: round(strat_counts.get(k, 0) / n, 4) for k in MIX}
    e4 = Counter(v.e4_decision for v in acc)
    return BuildReport(
        total_in=len(verdicts), accepted=len(acc),
        dropped_length=drop_len, dropped_e4=drop_e4, soft_flags=soft,
        mix_actual=mix_actual, mix_target=dict(MIX),
        e4_breakdown=dict(e4), held_count=held_count,
    )
