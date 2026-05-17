"""V534 — Gate27: CodeDependencyGate
Gates scene modifications based on script-level coupling risk.
Complements Gate26 (narrative risk) with structural coupling checks.
LLM-0 compliant.

Gate27 thresholds
-----------------
  G27-1  direct_coupled_count  <= 10
  G27-2  coupling_score_max    <= 0.80  (max single-pair coupling)
  G27-3  coupling_risk         <= 0.70  (from StagePatchImpactCalculator)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from literary_system.graph_intelligence.sp2.code_dependency_graph import CodeDependencyGraph
from literary_system.graph_intelligence.sp2.stage_patch_impact_calculator import (
    PatchType, StagePatchImpact, StagePatchImpactCalculator, StagePatchRequest,
)

_G27_DIRECT_MAX         = 10
_G27_MAX_COUPLING_SCORE = 0.80
_G27_COUPLING_RISK_MAX  = 0.70


@dataclass
class Gate27Check:
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
class Gate27Result:
    scene_id: str
    approved: bool
    checks: List[Gate27Check] = field(default_factory=list)
    impact: Optional[StagePatchImpact] = None
    reason: str = ""

    @property
    def failed_checks(self) -> List[Gate27Check]:
        return [c for c in self.checks if not c.passed]

    def summary(self) -> str:
        lines = [
            f"Gate27 {'APPROVED' if self.approved else 'BLOCKED'} — {self.scene_id}",
            f"  Coupling risk : {self.impact.coupling_risk if self.impact else 'N/A'}",
        ]
        for c in self.checks:
            lines.append(f"  {c}")
        if self.reason:
            lines.append(f"  Reason        : {self.reason}")
        return "\n".join(lines)


class Gate27:
    """Gate27: Code dependency gate for scene modifications.

    Usage::

        gate = Gate27(code_dep, calculator)
        result = gate.evaluate("sc07")
        if result.approved:
            ...
    """

    def __init__(
        self,
        code_dep: CodeDependencyGraph,
        calculator: StagePatchImpactCalculator,
        direct_max: int = _G27_DIRECT_MAX,
        max_coupling_score: float = _G27_MAX_COUPLING_SCORE,
        coupling_risk_max: float = _G27_COUPLING_RISK_MAX,
    ) -> None:
        self._code_dep          = code_dep
        self._calculator        = calculator
        self._direct_max        = direct_max
        self._max_coupling      = max_coupling_score
        self._coupling_risk_max = coupling_risk_max

    def evaluate(
        self,
        scene_id: str,
        patch_type: PatchType = PatchType.EDIT,
    ) -> Gate27Result:
        request = StagePatchRequest(scene_id=scene_id, patch_type=patch_type)
        impact  = self._calculator.calculate(request)

        # G27-1: direct coupled count
        direct_count = len(impact.coupled_scenes)

        # G27-2: max single coupling score
        max_cs = 0.0
        for coupled_id in impact.coupled_scenes:
            cs = self._code_dep.coupling_score(scene_id, coupled_id)
            if cs > max_cs:
                max_cs = cs

        # G27-3: coupling risk
        coupling_risk = impact.coupling_risk

        checks = [
            Gate27Check(
                gate_id="G27-1",
                description="direct_coupled_count",
                threshold=float(self._direct_max),
                actual=float(direct_count),
                passed=direct_count <= self._direct_max,
            ),
            Gate27Check(
                gate_id="G27-2",
                description="max_coupling_score",
                threshold=self._max_coupling,
                actual=round(max_cs, 4),
                passed=max_cs <= self._max_coupling,
            ),
            Gate27Check(
                gate_id="G27-3",
                description="coupling_risk",
                threshold=self._coupling_risk_max,
                actual=round(coupling_risk, 4),
                passed=coupling_risk <= self._coupling_risk_max,
            ),
        ]
        approved = all(c.passed for c in checks)
        reason = ""
        if not approved:
            failed = [c.gate_id for c in checks if not c.passed]
            reason = f"Failed: {', '.join(failed)}"

        return Gate27Result(
            scene_id=scene_id,
            approved=approved,
            checks=checks,
            impact=impact,
            reason=reason,
        )

    def evaluate_batch(
        self, scene_ids: List[str], patch_type: PatchType = PatchType.EDIT
    ) -> Dict[str, Gate27Result]:
        return {sid: self.evaluate(sid, patch_type) for sid in scene_ids}

    def is_approved(self, scene_id: str, patch_type: PatchType = PatchType.EDIT) -> bool:
        return self.evaluate(scene_id, patch_type).approved
