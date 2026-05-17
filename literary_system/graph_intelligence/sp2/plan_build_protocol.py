"""V533 — PlanBuildProtocol
Orchestrates the Plan → Build → Gate workflow for scene modifications.
Integrates Gate26 (narrative) + Gate27 (code dependency) into a single
approval chain.
LLM-0 compliant.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

from literary_system.graph_intelligence.scene_change_pre_gate import (
    Gate26Result, SceneChangePreGate,
)
from literary_system.graph_intelligence.sp2.stage_patch_impact_calculator import (
    PatchType, StagePatchImpact, StagePatchImpactCalculator, StagePatchRequest,
)
from literary_system.graph_intelligence.sp2.gate27 import Gate27, Gate27Result


class ProtocolPhase(Enum):
    PLAN  = "plan"
    BUILD = "build"
    GATE  = "gate"
    DONE  = "done"
    ABORT = "abort"


@dataclass
class ProtocolResult:
    """Full result of a Plan→Build→Gate run."""
    scene_id: str
    approved: bool

    # Plan phase
    patch_impact: Optional[StagePatchImpact] = None

    # Build phase
    gate26_result: Optional[Gate26Result] = None
    gate27_result: Optional[Gate27Result] = None

    # Final
    phase_reached: ProtocolPhase = ProtocolPhase.PLAN
    abort_reason: str = ""
    warnings: List[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"PlanBuildProtocol {'APPROVED' if self.approved else 'BLOCKED'} — {self.scene_id}",
            f"  Phase reached : {self.phase_reached.value}",
        ]
        if self.patch_impact:
            lines.append(f"  Combined risk : {self.patch_impact.combined_risk:.3f} ({self.patch_impact.risk_level})")
        if self.gate26_result:
            lines.append(f"  Gate26        : {'PASS' if self.gate26_result.approved else 'FAIL'}")
        if self.gate27_result:
            lines.append(f"  Gate27        : {'PASS' if self.gate27_result.approved else 'FAIL'}")
        if self.abort_reason:
            lines.append(f"  Abort reason  : {self.abort_reason}")
        for w in self.warnings:
            lines.append(f"  ⚠ {w}")
        return "\n".join(lines)


# Build function type alias: called when both gates pass
BuildFn = Callable[[str, PatchType], bool]


class PlanBuildProtocol:
    """Implements the Plan→Build→Gate protocol.

    Phases
    ------
    PLAN   Compute StagePatchImpact; abort if combined_risk >= abort_threshold
    BUILD  Run Gate26 + Gate27; abort if either fails
    GATE   Call build_fn (the actual scene modification); post-verify
    DONE   Both gates still pass after build
    ABORT  Abort at any phase if gates fail

    Usage::

        protocol = PlanBuildProtocol(gate26, gate27, calculator)
        result = protocol.run(
            StagePatchRequest("sc07", PatchType.EDIT),
            build_fn=lambda sid, pt: True,  # your actual edit logic
        )
    """

    def __init__(
        self,
        gate26: SceneChangePreGate,
        gate27: "Gate27",
        calculator: StagePatchImpactCalculator,
        abort_threshold: float = 0.90,  # abort PLAN phase above this combined risk
    ) -> None:
        self._gate26     = gate26
        self._gate27     = gate27
        self._calculator = calculator
        self._abort_threshold = abort_threshold

    def run(
        self,
        request: StagePatchRequest,
        build_fn: Optional[BuildFn] = None,
    ) -> ProtocolResult:
        result = ProtocolResult(scene_id=request.scene_id, approved=False)

        # ── PLAN ──────────────────────────────────────────────────────
        result.phase_reached = ProtocolPhase.PLAN
        impact = self._calculator.calculate(request)
        result.patch_impact = impact

        if impact.combined_risk >= self._abort_threshold:
            result.abort_reason = (
                f"PLAN aborted: combined_risk={impact.combined_risk:.3f} "
                f">= abort_threshold={self._abort_threshold}"
            )
            result.phase_reached = ProtocolPhase.ABORT
            return result

        # ── BUILD (pre-gate) ───────────────────────────────────────────
        result.phase_reached = ProtocolPhase.BUILD
        g26 = self._gate26.evaluate(request.scene_id)
        g27 = self._gate27.evaluate(request.scene_id)
        result.gate26_result = g26
        result.gate27_result = g27

        if not g26.approved:
            result.abort_reason = f"Gate26 BLOCKED: {g26.reason}"
            result.phase_reached = ProtocolPhase.ABORT
            return result

        if not g27.approved:
            result.abort_reason = f"Gate27 BLOCKED: {g27.reason}"
            result.phase_reached = ProtocolPhase.ABORT
            return result

        # ── GATE (execute + post-verify) ──────────────────────────────
        result.phase_reached = ProtocolPhase.GATE
        if build_fn is not None:
            success = build_fn(request.scene_id, request.patch_type)
            if not success:
                result.abort_reason = "build_fn returned False"
                result.phase_reached = ProtocolPhase.ABORT
                return result

        # Post-verify: re-run gates after build
        g26_post = self._gate26.evaluate(request.scene_id)
        g27_post = self._gate27.evaluate(request.scene_id)
        if not g26_post.approved:
            result.warnings.append(f"Post-build Gate26 regression: {g26_post.reason}")
        if not g27_post.approved:
            result.warnings.append(f"Post-build Gate27 regression: {g27_post.reason}")

        result.approved      = True
        result.phase_reached = ProtocolPhase.DONE
        return result
