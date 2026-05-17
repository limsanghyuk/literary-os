"""
ArcConsistencyChecker — V542
==============================
Literary OS Phase 5 ASD SP1

캐릭터 아크 일관성을 에피소드 그래프 전체에서 검증한다.

검사 항목
---------
AC-1  캐릭터 등장 후 감정 압력(EmotionPressure) 기록이 없는 경우
      → 아크 미추적 (arc_not_tracked)
AC-2  RelationshipNode 의 양 끝 캐릭터 중 하나가 episode_last 를 넘어
      여전히 관계 엣지를 가지는 경우 → 종료된 캐릭터에 대한 관계 불일치
      (arc_post_death_edge)
AC-3  같은 두 캐릭터 쌍 사이에 모순 관계(CONTRADICTS 엣지)가 2개 이상인 경우
      → 관계 모순 중첩 (arc_contradiction_overflow)
AC-4  CHARACTER 의 episode_first > episode_last 인 경우 (데이터 오류)
      → 에피소드 순서 역전 (arc_episode_inversion)

LLM-0: 외부 호출 없음.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from ..narrative_graph_schema import NarrativeEdgeType, NarrativeNodeType
from ..narrative_graph_store import NarrativeGraphStore


class ArcIssueType(str, Enum):
    ARC_NOT_TRACKED         = "arc_not_tracked"
    ARC_POST_DEATH_EDGE     = "arc_post_death_edge"
    ARC_CONTRADICTION_OVERFLOW = "arc_contradiction_overflow"
    ARC_EPISODE_INVERSION   = "arc_episode_inversion"


@dataclass
class ArcIssue:
    issue_type:   ArcIssueType
    character_id: str
    label:        str
    detail:       str
    severity:     float
    related_ids:  List[str] = field(default_factory=list)


@dataclass
class ArcConsistencyReport:
    total_issues:          int
    not_tracked:           List[ArcIssue]
    post_death_edges:      List[ArcIssue]
    contradiction_flows:   List[ArcIssue]
    episode_inversions:    List[ArcIssue]
    overall_score:         float   # 평균 severity; 0 = 문제없음

    @property
    def all_issues(self) -> List[ArcIssue]:
        return (self.not_tracked + self.post_death_edges
                + self.contradiction_flows + self.episode_inversions)

    def is_consistent(self) -> bool:
        return self.total_issues == 0


class ArcConsistencyChecker:
    """
    Parameters
    ----------
    store : NarrativeGraphStore
    not_tracked_severity : float
        AC-1 심각도 (default 0.45)
    post_death_severity : float
        AC-2 심각도 (default 0.80)
    contradiction_severity : float
        AC-3 심각도 (default 0.65)
    inversion_severity : float
        AC-4 심각도 (default 0.90)
    contradiction_threshold : int
        AC-3 허용 모순 수 초과 기준 (default 2)
    """

    def __init__(
        self,
        store: NarrativeGraphStore,
        *,
        not_tracked_severity: float = 0.45,
        post_death_severity: float = 0.80,
        contradiction_severity: float = 0.65,
        inversion_severity: float = 0.90,
        contradiction_threshold: int = 2,
    ) -> None:
        self._store = store
        self._sev_not_tracked    = max(0.0, min(1.0, not_tracked_severity))
        self._sev_post_death     = max(0.0, min(1.0, post_death_severity))
        self._sev_contradiction  = max(0.0, min(1.0, contradiction_severity))
        self._sev_inversion      = max(0.0, min(1.0, inversion_severity))
        self._contradiction_thr  = max(1, contradiction_threshold)

    def check(self) -> ArcConsistencyReport:
        not_tracked  = self._check_ac1_not_tracked()
        post_death   = self._check_ac2_post_death()
        contradicts  = self._check_ac3_contradiction_overflow()
        inversions   = self._check_ac4_episode_inversion()

        all_issues = not_tracked + post_death + contradicts + inversions
        total      = len(all_issues)
        score      = (sum(i.severity for i in all_issues) / total) if total else 0.0

        return ArcConsistencyReport(
            total_issues        = total,
            not_tracked         = not_tracked,
            post_death_edges    = post_death,
            contradiction_flows = contradicts,
            episode_inversions  = inversions,
            overall_score       = round(score, 4),
        )

    # ------------------------------------------------------------------
    # AC-1: 감정 압력 미추적
    # ------------------------------------------------------------------
    def _check_ac1_not_tracked(self) -> List[ArcIssue]:
        issues: List[ArcIssue] = []
        # EmotionPressure 노드들의 메타에서 character_id 수집
        tracked_chars: set = set()
        for ep_node in self._store.nodes_by_type(NarrativeNodeType.EMOTION_PRESSURE):
            cid = ep_node.meta.get("character_id")
            if cid:
                tracked_chars.add(cid)
        # ESCALATES / RELIEVES 엣지의 src 가 CHARACTER 이면 추적됨
        for edge in self._store.edges_by_type(NarrativeEdgeType.ESCALATES):
            src = self._store.get_node(edge.src_id)
            if src and src.node_type == NarrativeNodeType.CHARACTER:
                tracked_chars.add(edge.src_id)
        for edge in self._store.edges_by_type(NarrativeEdgeType.RELIEVES):
            src = self._store.get_node(edge.src_id)
            if src and src.node_type == NarrativeNodeType.CHARACTER:
                tracked_chars.add(edge.src_id)

        for node in self._store.nodes_by_type(NarrativeNodeType.CHARACTER):
            if node.node_id not in tracked_chars:
                issues.append(ArcIssue(
                    issue_type   = ArcIssueType.ARC_NOT_TRACKED,
                    character_id = node.node_id,
                    label        = node.label,
                    detail       = "감정 압력/ESCALATES/RELIEVES 미추적 캐릭터",
                    severity     = self._sev_not_tracked,
                ))
        return issues

    # ------------------------------------------------------------------
    # AC-2: 종료 캐릭터 이후 엣지
    # ------------------------------------------------------------------
    def _check_ac2_post_death(self) -> List[ArcIssue]:
        issues: List[ArcIssue] = []
        for node in self._store.nodes_by_type(NarrativeNodeType.CHARACTER):
            ep_last = getattr(node, "episode_last", None)
            if ep_last is None:
                continue

            # RelationshipNode 확인: char_a_id or char_b_id == node.node_id
            for rel in self._store.nodes_by_type(NarrativeNodeType.RELATIONSHIP):
                char_a = getattr(rel, "char_a_id", None)
                char_b = getattr(rel, "char_b_id", None)
                rel_ep = getattr(rel, "episode", None)
                if char_a != node.node_id and char_b != node.node_id:
                    continue
                if rel_ep is not None and rel_ep > ep_last:
                    issues.append(ArcIssue(
                        issue_type   = ArcIssueType.ARC_POST_DEATH_EDGE,
                        character_id = node.node_id,
                        label        = node.label,
                        detail       = (
                            f"episode_last={ep_last} 이후 RelationshipNode "
                            f"ep={rel_ep}: {rel.node_id}"
                        ),
                        severity     = self._sev_post_death,
                        related_ids  = [rel.node_id],
                    ))

        return issues

    # ------------------------------------------------------------------
    # AC-3: 모순 중첩
    # ------------------------------------------------------------------
    def _check_ac3_contradiction_overflow(self) -> List[ArcIssue]:
        # 캐릭터 쌍 → CONTRADICTS 엣지 수
        pair_count: Dict[Tuple[str, str], List[str]] = {}
        for edge in self._store.edges_by_type(NarrativeEdgeType.CONTRADICTS):
            src_n = self._store.get_node(edge.src_id)
            dst_n = self._store.get_node(edge.dst_id)
            if (src_n and src_n.node_type == NarrativeNodeType.CHARACTER
                    and dst_n and dst_n.node_type == NarrativeNodeType.CHARACTER):
                key = (min(edge.src_id, edge.dst_id), max(edge.src_id, edge.dst_id))
                pair_count.setdefault(key, []).append(edge.edge_id)

        issues: List[ArcIssue] = []
        for (ca, cb), eids in pair_count.items():
            if len(eids) >= self._contradiction_thr:
                na = self._store.get_node(ca)
                nb = self._store.get_node(cb)
                label_a = na.label if na else ca
                label_b = nb.label if nb else cb
                issues.append(ArcIssue(
                    issue_type   = ArcIssueType.ARC_CONTRADICTION_OVERFLOW,
                    character_id = ca,
                    label        = f"{label_a} ↔ {label_b}",
                    detail       = (
                        f"CONTRADICTS 엣지 {len(eids)}개 "
                        f"(허용 기준 {self._contradiction_thr})"
                    ),
                    severity     = self._sev_contradiction,
                    related_ids  = [cb] + eids,
                ))

        return issues

    # ------------------------------------------------------------------
    # AC-4: 에피소드 역전
    # ------------------------------------------------------------------
    def _check_ac4_episode_inversion(self) -> List[ArcIssue]:
        issues: List[ArcIssue] = []
        for node in self._store.nodes_by_type(NarrativeNodeType.CHARACTER):
            ep_first = getattr(node, "episode_first", None)
            ep_last  = getattr(node, "episode_last", None)
            if ep_first is not None and ep_last is not None and ep_first > ep_last:
                issues.append(ArcIssue(
                    issue_type   = ArcIssueType.ARC_EPISODE_INVERSION,
                    character_id = node.node_id,
                    label        = node.label,
                    detail       = (
                        f"episode_first={ep_first} > episode_last={ep_last}"
                    ),
                    severity     = self._sev_inversion,
                ))
        return issues
