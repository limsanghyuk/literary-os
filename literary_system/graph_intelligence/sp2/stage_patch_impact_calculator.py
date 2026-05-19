"""V532 — StagePatchImpactCalculator
Calculates the full impact of a proposed scene patch (edit/delete/insert)
by combining NarrativeImpactAnalyzer (story graph) + CodeDependencyGraph (script coupling).
LLM-0 compliant.
"""
from __future__ import annotations
import logging

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set

from literary_system.graph_intelligence.narrative_impact_analyzer import NarrativeImpactAnalyzer
from literary_system.graph_intelligence.narrative_graph_schema import NarrativeImpactReport
from literary_system.graph_intelligence.narrative_graph_store import NarrativeGraphStore
from literary_system.graph_intelligence.sp2.code_dependency_graph import CodeDependencyGraph

logger = logging.getLogger(__name__)


class PatchType(Enum):
    EDIT   = "edit"     # Modify content of existing scene
    DELETE = "delete"   # Remove scene entirely
    INSERT = "insert"   # Add new scene (minimal impact)
    REORDER = "reorder" # Move scene position (structural)


@dataclass
class StagePatchRequest:
    """Describes a proposed patch to a screenplay scene."""
    scene_id: str
    patch_type: PatchType
    description: str = ""
    # For REORDER: new position 0.0–1.0
    new_position: Optional[float] = None
    # For INSERT: the scene this new scene is inserted after
    after_scene_id: Optional[str] = None


@dataclass
class StagePatchImpact:
    """Combined impact report from narrative + code coupling analysis."""
    scene_id: str
    patch_type: PatchType

    # Narrative graph impact
    narrative_report: Optional[NarrativeImpactReport] = None

    # Code dependency impact
    coupled_scenes: List[str] = field(default_factory=list)       # direct
    indirect_coupled: List[str] = field(default_factory=list)     # depth-2

    # Combined risk
    narrative_risk: float = 0.0
    coupling_risk: float = 0.0
    combined_risk: float = 0.0
    risk_level: str = "low"
    recommendation: str = "proceed"

    # Detail
    warnings: List[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"=== StagePatchImpact ===",
            f"Scene      : {self.scene_id}  [{self.patch_type.value}]",
            f"NarrRisk   : {self.narrative_risk:.3f} ({self.narrative_report.risk_level if self.narrative_report else 'N/A'})",
            f"CouplingRisk: {self.coupling_risk:.3f}",
            f"CombinedRisk: {self.combined_risk:.3f} → {self.risk_level.upper()}",
            f"Recommend  : {self.recommendation}",
            f"Coupled    : {len(self.coupled_scenes)} direct / {len(self.indirect_coupled)} indirect",
        ]
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        return "\n".join(lines)


# Risk combination weights
_W_NARRATIVE = 0.60
_W_COUPLING  = 0.40

# Coupling risk: each directly coupled scene adds this much
_W_DIRECT_COUPLE   = 0.15
_W_INDIRECT_COUPLE = 0.06

# Patch type multipliers
_PATCH_MULTIPLIER = {
    PatchType.EDIT:    1.0,
    PatchType.DELETE:  1.5,   # Deletions propagate more aggressively
    PatchType.REORDER: 0.6,
    PatchType.INSERT:  0.2,
}

_CRITICAL = 0.80
_HIGH     = 0.55
_MEDIUM   = 0.30


class StagePatchImpactCalculator:
    """Combines narrative graph + code dependency analysis into a unified patch impact.

    Usage::

        calc = StagePatchImpactCalculator(narrative_store, code_dep_graph)
        impact = calc.calculate(StagePatchRequest("sc07", PatchType.DELETE))
        logger.debug(impact.summary())
    """

    def __init__(
        self,
        narrative_store: NarrativeGraphStore,
        code_dep: CodeDependencyGraph,
        max_depth: int = 2,
    ) -> None:
        self._narrator   = NarrativeImpactAnalyzer(narrative_store)
        self._code_dep   = code_dep
        self._max_depth  = max_depth

    def calculate(self, request: StagePatchRequest) -> StagePatchImpact:
        impact = StagePatchImpact(
            scene_id=request.scene_id,
            patch_type=request.patch_type,
        )

        multiplier = _PATCH_MULTIPLIER[request.patch_type]

        # --- Narrative analysis ---
        narr_report = self._narrator.analyze(request.scene_id, self._max_depth)
        impact.narrative_report  = narr_report
        impact.narrative_risk    = round(narr_report.risk_score * multiplier, 4)

        # --- Code dependency analysis ---
        try:
            direct   = self._code_dep.direct_deps(request.scene_id)
            indirect_set: Set[str] = set()
            for d in direct:
                for nb in self._code_dep.direct_deps(d):
                    if nb != request.scene_id and nb not in direct:
                        indirect_set.add(nb)
            indirect = sorted(indirect_set)
            impact.coupled_scenes   = direct
            impact.indirect_coupled = indirect
            coupling_raw = min(
                len(direct)   * _W_DIRECT_COUPLE
                + len(indirect) * _W_INDIRECT_COUPLE,
                1.0,
            )
            impact.coupling_risk = round(coupling_raw * multiplier, 4)
        except RuntimeError as e:
            # Code dep graph not built — degrade gracefully
            impact.warnings.append(f"CodeDependencyGraph: {e}")
            impact.coupling_risk = 0.0

        # --- Combined risk ---
        combined = round(
            min(
                impact.narrative_risk * _W_NARRATIVE
                + impact.coupling_risk  * _W_COUPLING,
                1.0,
            ),
            4,
        )
        impact.combined_risk = combined
        impact.risk_level, impact.recommendation = self._classify(combined)

        if request.patch_type == PatchType.DELETE and combined >= _HIGH:
            impact.warnings.append(
                "DELETE on high-risk scene: consider splitting into EDIT + soft-deprecate"
            )
        return impact

    def calculate_batch(
        self, requests: List[StagePatchRequest]
    ) -> Dict[str, StagePatchImpact]:
        return {r.scene_id: self.calculate(r) for r in requests}

    @staticmethod
    def _classify(score: float):
        if score >= _CRITICAL:
            return "critical", "hold"
        if score >= _HIGH:
            return "high", "split_required"
        if score >= _MEDIUM:
            return "medium", "review"
        return "low", "proceed"
