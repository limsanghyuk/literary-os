"""
StoryDoctorOrchestrator — V543
================================
Literary OS Phase 5 ASD SP1

NarrativeDebtDetector + ArcConsistencyChecker 결과를 통합하고
GIG 블라스트 반경을 이용해 우선순위가 매겨진 수리 추천 목록을 생성한다.

우선순위 공식
-------------
priority_score = severity × (1 + blast_weight × blast_ratio)

  blast_ratio = len(affected_scenes) / max(total_scenes, 1)
  blast_weight = 1.5  (기본)

결과는 priority_score 내림차순으로 정렬된다.

LLM-0: 외부 호출 없음.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Union

from ..narrative_graph_schema import NarrativeNodeType
from ..narrative_graph_store import NarrativeGraphStore
from ..narrative_impact_analyzer import NarrativeImpactAnalyzer
from .arc_consistency_checker import (
    ArcConsistencyChecker,
    ArcConsistencyReport,
    ArcIssue,
    ArcIssueType,
)
from .narrative_debt_detector import (
    DebtType,
    NarrativeDebtDetector,
    NarrativeDebtItem,
    NarrativeDebtReport,
)


class RepairCategory(str, Enum):
    RESOLVE_SECRET      = "resolve_secret"
    FIX_FORESHADOW      = "fix_foreshadow"
    REVIVE_THREAD       = "revive_thread"
    ARC_TRACKING        = "arc_tracking"
    ARC_POST_DEATH      = "arc_post_death"
    ARC_CONTRADICTION   = "arc_contradiction"
    ARC_INVERSION       = "arc_inversion"


@dataclass
class RepairRecommendation:
    recommendation_id: str
    category:          RepairCategory
    node_id:           str
    label:             str
    detail:            str
    severity:          float
    blast_ratio:       float          # 0.0~1.0
    priority_score:    float          # 높을수록 먼저 수리
    affected_scenes:   List[str] = field(default_factory=list)
    related_ids:       List[str] = field(default_factory=list)


@dataclass
class DoctorReport:
    recommendations:    List[RepairRecommendation]
    total_issues:       int
    high_priority:      List[RepairRecommendation]   # priority_score >= 0.70
    medium_priority:    List[RepairRecommendation]   # 0.40 <= score < 0.70
    low_priority:       List[RepairRecommendation]   # score < 0.40
    debt_report:        NarrativeDebtReport
    arc_report:         ArcConsistencyReport

    def is_healthy(self) -> bool:
        return self.total_issues == 0


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

_DEBT_TO_CATEGORY = {
    DebtType.UNRESOLVED_SECRET:  RepairCategory.RESOLVE_SECRET,
    DebtType.BROKEN_FORESHADOW:  RepairCategory.FIX_FORESHADOW,
    DebtType.ABANDONED_THREAD:   RepairCategory.REVIVE_THREAD,
}

_ARC_TO_CATEGORY = {
    ArcIssueType.ARC_NOT_TRACKED:            RepairCategory.ARC_TRACKING,
    ArcIssueType.ARC_POST_DEATH_EDGE:        RepairCategory.ARC_POST_DEATH,
    ArcIssueType.ARC_CONTRADICTION_OVERFLOW: RepairCategory.ARC_CONTRADICTION,
    ArcIssueType.ARC_EPISODE_INVERSION:      RepairCategory.ARC_INVERSION,
}


class StoryDoctorOrchestrator:
    """
    Parameters
    ----------
    store : NarrativeGraphStore
    blast_weight : float
        블라스트 반경 가중치 (default 1.5)
    blast_max_depth : int
        NarrativeImpactAnalyzer 탐색 깊이 (default 2)
    high_threshold : float
        high_priority 기준 priority_score (default 0.70)
    medium_threshold : float
        medium_priority 기준 priority_score (default 0.40)
    """

    def __init__(
        self,
        store: NarrativeGraphStore,
        *,
        blast_weight: float = 1.5,
        blast_max_depth: int = 2,
        high_threshold: float = 0.70,
        medium_threshold: float = 0.40,
    ) -> None:
        self._store          = store
        self._blast_weight   = blast_weight
        self._blast_depth    = blast_max_depth
        self._high_thr       = high_threshold
        self._medium_thr     = medium_threshold
        self._analyzer       = NarrativeImpactAnalyzer(store)
        self._debt_detector  = NarrativeDebtDetector(store)
        self._arc_checker    = ArcConsistencyChecker(store)

    # ------------------------------------------------------------------
    def diagnose(self) -> DoctorReport:
        debt_report = self._debt_detector.detect()
        arc_report  = self._arc_checker.check()

        total_scenes = len(self._store.nodes_by_type(NarrativeNodeType.SCENE))

        recs: List[RepairRecommendation] = []
        rid  = 0

        # Debt items
        for item in debt_report.all_items:
            rid += 1
            rec = self._build_from_debt(item, rid, total_scenes)
            recs.append(rec)

        # Arc issues
        for issue in arc_report.all_issues:
            rid += 1
            rec = self._build_from_arc(issue, rid, total_scenes)
            recs.append(rec)

        # Sort by priority_score desc
        recs.sort(key=lambda r: r.priority_score, reverse=True)

        high   = [r for r in recs if r.priority_score >= self._high_thr]
        medium = [r for r in recs if self._medium_thr <= r.priority_score < self._high_thr]
        low    = [r for r in recs if r.priority_score < self._medium_thr]

        return DoctorReport(
            recommendations  = recs,
            total_issues     = len(recs),
            high_priority    = high,
            medium_priority  = medium,
            low_priority     = low,
            debt_report      = debt_report,
            arc_report       = arc_report,
        )

    # ------------------------------------------------------------------
    def _blast_for(self, node_id: str, total_scenes: int):
        """node_id 씬의 블라스트 반경 반환. 씬이 아니면 ([], 0.0)."""
        node = self._store.get_node(node_id)
        if node is None or node.node_type != NarrativeNodeType.SCENE:
            return [], 0.0
        try:
            report = self._analyzer.analyze(node_id, self._blast_depth)
            affected = list(set(report.direct_impact) | set(report.indirect_impact))
            ratio    = len(affected) / max(total_scenes, 1)
            return affected, round(ratio, 4)
        except Exception:
            return [], 0.0

    def _priority(self, severity: float, blast_ratio: float) -> float:
        score = severity * (1.0 + self._blast_weight * blast_ratio)
        return round(min(score, 1.0), 4)

    def _build_from_debt(
        self,
        item: NarrativeDebtItem,
        rid: int,
        total_scenes: int,
    ) -> RepairRecommendation:
        affected, ratio = self._blast_for(item.node_id, total_scenes)
        return RepairRecommendation(
            recommendation_id = f"R{rid:04d}",
            category          = _DEBT_TO_CATEGORY[item.debt_type],
            node_id           = item.node_id,
            label             = item.label,
            detail            = item.detail,
            severity          = item.severity,
            blast_ratio       = ratio,
            priority_score    = self._priority(item.severity, ratio),
            affected_scenes   = affected,
            related_ids       = item.related_ids,
        )

    def _build_from_arc(
        self,
        issue: ArcIssue,
        rid: int,
        total_scenes: int,
    ) -> RepairRecommendation:
        affected, ratio = self._blast_for(issue.character_id, total_scenes)
        return RepairRecommendation(
            recommendation_id = f"R{rid:04d}",
            category          = _ARC_TO_CATEGORY[issue.issue_type],
            node_id           = issue.character_id,
            label             = issue.label,
            detail            = issue.detail,
            severity          = issue.severity,
            blast_ratio       = ratio,
            priority_score    = self._priority(issue.severity, ratio),
            affected_scenes   = affected,
            related_ids       = issue.related_ids,
        )
