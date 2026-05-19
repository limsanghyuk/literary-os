"""V529b — SceneChangePreGate (Gate26)
Plan→Build approval gate for scene modifications.
LLM-0 compliant: zero LLM calls.

Gate26 thresholds
-----------------
  G26-1  len(direct_impact)     <= 15
  G26-2  len(reveal_impacts)    <= 3
  G26-3  len(foreshadow_breaks) <= 2
  G26-4  risk_score             <= 0.75

All four must pass for the gate to APPROVE.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from literary_system.graph_intelligence.narrative_graph_schema import NarrativeImpactReport
from literary_system.graph_intelligence.narrative_graph_store import NarrativeGraphStore
from literary_system.graph_intelligence.narrative_impact_analyzer import NarrativeImpactAnalyzer

logger = logging.getLogger(__name__)

_G26_DIRECT_MAX           = 15
_G26_REVEAL_MAX           = 3
_G26_FORESHADOW_BREAK_MAX = 2
_G26_RISK_MAX             = 0.75


@dataclass
class GateCheck:
    gate_id: str
    description: str
    threshold: float
    actual: float
    passed: bool

    def __str__(self) -> str:
        status = "✓" if self.passed else "✗"
        return (
            f"{status} {self.gate_id}: {self.description} "
            f"(actual={self.actual}, threshold={self.threshold})"
        )


@dataclass
class Gate26Result:
    scene_id: str
    approved: bool
    checks: List[GateCheck] = field(default_factory=list)
    impact_report: Optional[NarrativeImpactReport] = None
    reason: str = ""

    @property
    def failed_checks(self) -> List[GateCheck]:
        return [c for c in self.checks if not c.passed]

    @property
    def passed_checks(self) -> List[GateCheck]:
        return [c for c in self.checks if c.passed]

    def summary(self) -> str:
        report = self.impact_report
        lines = [
            f"Gate26 {'APPROVED' if self.approved else 'BLOCKED'} — {self.scene_id}",
            f"  Risk score : {report.risk_score if report else 'N/A'}",
            f"  Risk level : {report.risk_level if report else 'N/A'}",
            f"  Decision   : {report.decision if report else 'N/A'}",
        ]
        for c in self.checks:
            lines.append(f"  {c}")
        if self.reason:
            lines.append(f"  Reason     : {self.reason}")
        return "\n".join(lines)


class SceneChangePreGate:
    """Implements Gate26: Plan→Build approval gate.

    Usage::

        gate = SceneChangePreGate(store)
        result = gate.evaluate("scene_07")
        if result.approved:
            ...  # safe to proceed
        else:
            logger.debug(result.summary())
    """

    def __init__(
        self,
        store: NarrativeGraphStore,
        direct_max: int = _G26_DIRECT_MAX,
        reveal_max: int = _G26_REVEAL_MAX,
        foreshadow_break_max: int = _G26_FORESHADOW_BREAK_MAX,
        risk_max: float = _G26_RISK_MAX,
    ) -> None:
        self._store               = store
        self._analyzer            = NarrativeImpactAnalyzer(store)
        self._direct_max          = direct_max
        self._reveal_max          = reveal_max
        self._foreshadow_break_max = foreshadow_break_max
        self._risk_max            = risk_max

    def evaluate(self, scene_id: str, max_depth: int = 2) -> Gate26Result:
        report = self._analyzer.analyze(scene_id, max_depth)
        checks = [
            GateCheck(
                gate_id="G26-1",
                description="direct_impact_count",
                threshold=float(self._direct_max),
                actual=float(len(report.direct_impact)),
                passed=len(report.direct_impact) <= self._direct_max,
            ),
            GateCheck(
                gate_id="G26-2",
                description="reveal_count",
                threshold=float(self._reveal_max),
                actual=float(len(report.reveal_impacts)),
                passed=len(report.reveal_impacts) <= self._reveal_max,
            ),
            GateCheck(
                gate_id="G26-3",
                description="foreshadow_break_count",
                threshold=float(self._foreshadow_break_max),
                actual=float(len(report.foreshadow_breaks)),
                passed=len(report.foreshadow_breaks) <= self._foreshadow_break_max,
            ),
            GateCheck(
                gate_id="G26-4",
                description="risk_score",
                threshold=self._risk_max,
                actual=report.risk_score,
                passed=report.risk_score <= self._risk_max,
            ),
        ]
        approved = all(c.passed for c in checks)
        reason = ""
        if not approved:
            failed = [c.gate_id for c in checks if not c.passed]
            reason = f"Failed: {', '.join(failed)}"
        return Gate26Result(
            scene_id=scene_id,
            approved=approved,
            checks=checks,
            impact_report=report,
            reason=reason,
        )

    def evaluate_batch(
        self, scene_ids: List[str], max_depth: int = 2
    ) -> Dict[str, Gate26Result]:
        return {sid: self.evaluate(sid, max_depth) for sid in scene_ids}

    def is_approved(self, scene_id: str, max_depth: int = 2) -> bool:
        return self.evaluate(scene_id, max_depth).approved
