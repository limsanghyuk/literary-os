"""V537 — SceneBlastRadiusReport
Rich, human-readable blast radius report combining narrative + code coupling.
Consumed by PlanBuildProtocol and external dashboards.
LLM-0 compliant.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from literary_system.graph_intelligence.narrative_graph_schema import NarrativeImpactReport
from literary_system.graph_intelligence.narrative_graph_store import NarrativeGraphStore
from literary_system.graph_intelligence.narrative_impact_analyzer import NarrativeImpactAnalyzer
from literary_system.graph_intelligence.sp2.code_dependency_graph import CodeDependencyGraph
from literary_system.graph_intelligence.sp2.stage_patch_impact_calculator import (
    PatchType,
    StagePatchImpact,
    StagePatchImpactCalculator,
    StagePatchRequest,
)

logger = logging.getLogger(__name__)


@dataclass
class SceneBlastRadiusReport:
    """Unified blast radius report merging narrative + code coupling layers.

    Fields
    ------
    scene_id            Target scene being analysed
    narrative_report    NarrativeImpactReport from SP1 analyzer
    patch_impact        StagePatchImpact from SP2 calculator
    combined_risk       Final combined risk score (0.0–1.0)
    risk_level          low / medium / high / critical
    recommendation      proceed / review / split_required / hold
    affected_scenes     Union of narrative + coupling blast radius
    reveal_ids          Reveal nodes in blast radius
    foreshadow_breaks   Foreshadow break motif IDs
    top_coupled         Top-5 scenes by coupling score
    """
    scene_id: str
    narrative_report: Optional[NarrativeImpactReport] = None
    patch_impact: Optional[StagePatchImpact] = None
    combined_risk: float = 0.0
    risk_level: str = "low"
    recommendation: str = "proceed"
    affected_scenes: List[str] = field(default_factory=list)
    reveal_ids: List[str] = field(default_factory=list)
    foreshadow_breaks: List[str] = field(default_factory=list)
    top_coupled: List[Dict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "scene_id":          self.scene_id,
            "combined_risk":     self.combined_risk,
            "risk_level":        self.risk_level,
            "recommendation":    self.recommendation,
            "affected_scenes":   self.affected_scenes,
            "reveal_count":      len(self.reveal_ids),
            "foreshadow_breaks": len(self.foreshadow_breaks),
            "top_coupled":       self.top_coupled[:5],
            "warnings":          self.warnings,
        }

    def summary(self) -> str:
        lines = [
            "══════ SceneBlastRadiusReport ══════",
            f"Scene        : {self.scene_id}",
            f"Risk         : {self.risk_level.upper()} ({self.combined_risk:.3f})",
            f"Recommend    : {self.recommendation}",
            f"Affected     : {len(self.affected_scenes)} scenes",
            f"Reveals      : {len(self.reveal_ids)}",
            f"ForeshadowBrk: {len(self.foreshadow_breaks)}",
        ]
        if self.top_coupled:
            lines.append("Top coupled  :")
            for tc in self.top_coupled[:3]:
                lines.append(f"  {tc['scene_id']} (score={tc['score']:.3f})")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        return "\n".join(lines)


class BlastRadiusReportBuilder:
    """Builds SceneBlastRadiusReport by combining all analysis layers.

    Usage::

        builder = BlastRadiusReportBuilder(store, code_dep)
        report  = builder.build("sc07", PatchType.EDIT)
        logger.debug(report.summary())
    """

    def __init__(
        self,
        narrative_store: NarrativeGraphStore,
        code_dep: CodeDependencyGraph,
        max_depth: int = 2,
    ) -> None:
        self._store     = narrative_store
        self._code_dep  = code_dep
        self._analyzer  = NarrativeImpactAnalyzer(narrative_store)
        self._calculator = StagePatchImpactCalculator(narrative_store, code_dep, max_depth)
        self._max_depth = max_depth

    def build(
        self,
        scene_id: str,
        patch_type: PatchType = PatchType.EDIT,
    ) -> SceneBlastRadiusReport:
        report = SceneBlastRadiusReport(scene_id=scene_id)

        # Narrative layer
        narr = self._analyzer.analyze(scene_id, self._max_depth)
        report.narrative_report   = narr
        report.reveal_ids         = narr.reveal_impacts
        report.foreshadow_breaks  = narr.foreshadow_breaks

        # Patch impact layer (narrative + coupling)
        impact = self._calculator.calculate(
            StagePatchRequest(scene_id=scene_id, patch_type=patch_type)
        )
        report.patch_impact    = impact
        report.combined_risk   = impact.combined_risk
        report.risk_level      = impact.risk_level
        report.recommendation  = impact.recommendation
        report.warnings        = list(impact.warnings)

        # Affected scenes: union of narrative blast + coupled scenes
        affected = set(narr.direct_impact) | set(narr.indirect_impact)
        affected |= set(impact.coupled_scenes) | set(impact.indirect_coupled)
        affected.discard(scene_id)
        report.affected_scenes = sorted(affected)

        # Top coupled by score
        top = []
        for coupled_id in impact.coupled_scenes:
            score = self._code_dep.coupling_score(scene_id, coupled_id)
            top.append({"scene_id": coupled_id, "score": score})
        top.sort(key=lambda x: x["score"], reverse=True)
        report.top_coupled = top[:5]

        return report

    def build_batch(
        self,
        scene_ids: List[str],
        patch_type: PatchType = PatchType.EDIT,
    ) -> Dict[str, SceneBlastRadiusReport]:
        return {sid: self.build(sid, patch_type) for sid in scene_ids}
