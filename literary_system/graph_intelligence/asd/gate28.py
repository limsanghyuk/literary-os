"""
Gate28 — StoryQualityGate — V545
====================================
Literary OS Phase 5 ASD SP1

DoctorReport 를 받아 4개 서브게이트를 평가한다.

Gate 임계값
-----------
G28-1  debt_score        ≤ 0.50   (NarrativeDebtReport.overall_debt_score)
G28-2  arc_score         ≤ 0.40   (ArcConsistencyReport.overall_score)
G28-3  high_priority_cnt ≤ 5      (high_priority 추천 수)
G28-4  combined_quality  ≤ 0.45   (narrative_debt×0.55 + arc×0.45)

combined_quality = min(debt_score×0.55 + arc_score×0.45, 1.0)

LLM-0: 외부 호출 없음.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .story_doctor_orchestrator import DoctorReport


@dataclass
class Gate28Check:
    gate_id:   str
    metric:    str
    threshold: float
    actual:    float
    passed:    bool
    message:   str = ""


@dataclass
class Gate28Result:
    approved:        bool
    checks:          List[Gate28Check]
    combined_quality: float
    failed_gates:    List[str]

    def summary(self) -> str:
        status = "PASS" if self.approved else "FAIL"
        lines  = [f"Gate28 StoryQualityGate [{status}]  combined_quality={self.combined_quality:.4f}"]
        for c in self.checks:
            mark = "✓" if c.passed else "✗"
            lines.append(f"  {mark} {c.gate_id}: {c.metric}={c.actual:.4f} (≤{c.threshold})")
        if self.failed_gates:
            lines.append(f"  Blocked by: {', '.join(self.failed_gates)}")
        return "\n".join(lines)


class Gate28:
    """
    Parameters
    ----------
    debt_threshold : float        G28-1 기준 (default 0.50)
    arc_threshold : float         G28-2 기준 (default 0.40)
    high_priority_threshold : int G28-3 기준 (default 5)
    combined_threshold : float    G28-4 기준 (default 0.45)
    """

    def __init__(
        self,
        *,
        debt_threshold: float = 0.50,
        arc_threshold: float = 0.40,
        high_priority_threshold: int = 5,
        combined_threshold: float = 0.45,
    ) -> None:
        self._t_debt     = debt_threshold
        self._t_arc      = arc_threshold
        self._t_high     = high_priority_threshold
        self._t_combined = combined_threshold

    def evaluate(self, report: DoctorReport) -> Gate28Result:
        debt_score  = report.debt_report.overall_debt_score
        arc_score   = report.arc_report.overall_score
        high_cnt    = len(report.high_priority)
        combined    = round(min(debt_score * 0.55 + arc_score * 0.45, 1.0), 4)

        checks = [
            Gate28Check(
                gate_id   = "G28-1",
                metric    = "debt_score",
                threshold = self._t_debt,
                actual    = debt_score,
                passed    = debt_score <= self._t_debt,
                message   = f"NarrativeDebt overall={debt_score:.4f}",
            ),
            Gate28Check(
                gate_id   = "G28-2",
                metric    = "arc_score",
                threshold = self._t_arc,
                actual    = arc_score,
                passed    = arc_score <= self._t_arc,
                message   = f"ArcConsistency overall={arc_score:.4f}",
            ),
            Gate28Check(
                gate_id   = "G28-3",
                metric    = "high_priority_cnt",
                threshold = float(self._t_high),
                actual    = float(high_cnt),
                passed    = high_cnt <= self._t_high,
                message   = f"high_priority recommendations={high_cnt}",
            ),
            Gate28Check(
                gate_id   = "G28-4",
                metric    = "combined_quality",
                threshold = self._t_combined,
                actual    = combined,
                passed    = combined <= self._t_combined,
                message   = f"combined = debt×0.55 + arc×0.45 = {combined:.4f}",
            ),
        ]

        failed = [c.gate_id for c in checks if not c.passed]
        approved = len(failed) == 0

        return Gate28Result(
            approved         = approved,
            checks           = checks,
            combined_quality = combined,
            failed_gates     = failed,
        )
