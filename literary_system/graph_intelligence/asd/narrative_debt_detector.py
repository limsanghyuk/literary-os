"""
NarrativeDebtDetector — V541
==============================
Literary OS Phase 5 ASD SP1

그래프를 스캔해 세 종류의 서사 부채를 탐지한다.

1. UnresolvedSecret  : SECRET 노드에 연결된 REVEALS 엣지가 없거나, 연결된
                       RevealNode 의 reveal_episode 가 None 인 경우.
2. BrokenForeshadow  : FORESHADOWS 엣지(motif → future_scene)의 dst_id 가
                       그래프에 SceneNode 로 존재하지 않거나, 해당 씬 노드가
                       고아(들어오는 CAUSES/DEPENDS_ON 엣지 0개)인 경우.
3. AbandonedThread   : CHARACTER 노드가 episode_first 이후 episode_last 가
                       None 이거나, 해당 캐릭터를 src 로 갖는 나가는 엣지가
                       전혀 없는 경우(고아 캐릭터).

LLM-0: 외부 호출 없음. 순수 그래프 탐색.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from ..narrative_graph_schema import NarrativeEdgeType, NarrativeNodeType
from ..narrative_graph_store import NarrativeGraphStore

# ---------------------------------------------------------------------------
# Debt item types
# ---------------------------------------------------------------------------

class NarrativeDebtType(str, Enum):
    UNRESOLVED_SECRET    = "unresolved_secret"
    BROKEN_FORESHADOW    = "broken_foreshadow"
    ABANDONED_THREAD     = "abandoned_thread"


@dataclass
class NarrativeDebtItem:
    debt_type:    DebtType
    node_id:      str
    label:        str
    detail:       str
    severity:     float        # 0.0 ~ 1.0
    related_ids:  List[str] = field(default_factory=list)


@dataclass
class NarrativeDebtReport:
    total_debts:           int
    unresolved_secrets:    List[NarrativeDebtItem]
    broken_foreshadows:    List[NarrativeDebtItem]
    abandoned_threads:     List[NarrativeDebtItem]
    overall_debt_score:    float   # weighted mean of severity; 0 = clean

    @property
    def all_items(self) -> List[NarrativeDebtItem]:
        return (self.unresolved_secrets
                + self.broken_foreshadows
                + self.abandoned_threads)

    def is_clean(self) -> bool:
        return self.total_debts == 0


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------

class NarrativeDebtDetector:
    """
    Parameters
    ----------
    store : NarrativeGraphStore
    secret_severity : float
    foreshadow_severity : float
    thread_severity : float
    """

    def __init__(
        self,
        store: NarrativeGraphStore,
        *,
        secret_severity: float = 0.70,
        foreshadow_severity: float = 0.60,
        thread_severity: float = 0.50,
    ) -> None:
        self._store = store
        self._sev_secret     = max(0.0, min(1.0, secret_severity))
        self._sev_foreshadow = max(0.0, min(1.0, foreshadow_severity))
        self._sev_thread     = max(0.0, min(1.0, thread_severity))

    def detect(self) -> NarrativeDebtReport:
        secrets    = self._detect_unresolved_secrets()
        foreshadow = self._detect_broken_foreshadows()
        threads    = self._detect_abandoned_threads()

        all_items  = secrets + foreshadow + threads
        total      = len(all_items)
        score      = (sum(i.severity for i in all_items) / total) if total else 0.0

        return NarrativeDebtReport(
            total_debts        = total,
            unresolved_secrets = secrets,
            broken_foreshadows = foreshadow,
            abandoned_threads  = threads,
            overall_debt_score = round(score, 4),
        )

    def _detect_unresolved_secrets(self) -> List[NarrativeDebtItem]:
        items: List[NarrativeDebtItem] = []
        for node in self._store.nodes_by_type(NarrativeNodeType.SECRET):
            outgoing = self._store.edges_from(node.node_id)
            reveal_edges = [
                e for e in outgoing
                if e.edge_type == NarrativeEdgeType.REVEALS
            ]
            if not reveal_edges:
                items.append(NarrativeDebtItem(
                    debt_type   = DebtType.UNRESOLVED_SECRET,
                    node_id     = node.node_id,
                    label       = node.label,
                    detail      = "SECRET 노드에 REVEALS 엣지 없음",
                    severity    = self._sev_secret,
                    related_ids = [],
                ))
                continue

            unlinked: List[str] = []
            for edge in reveal_edges:
                target = self._store.get_node(edge.dst_id)
                if target is None or target.node_type != NarrativeNodeType.REVEAL:
                    unlinked.append(edge.dst_id)

            if unlinked:
                items.append(NarrativeDebtItem(
                    debt_type   = DebtType.UNRESOLVED_SECRET,
                    node_id     = node.node_id,
                    label       = node.label,
                    detail      = f"REVEALS 대상 노드 미등록: {unlinked}",
                    severity    = self._sev_secret * 0.8,
                    related_ids = unlinked,
                ))

        return items

    def _detect_broken_foreshadows(self) -> List[NarrativeDebtItem]:
        items: List[NarrativeDebtItem] = []
        for edge in self._store.edges_by_type(NarrativeEdgeType.FORESHADOWS):
            src_node = self._store.get_node(edge.src_id)
            dst_node = self._store.get_node(edge.dst_id)

            if dst_node is None:
                items.append(NarrativeDebtItem(
                    debt_type   = DebtType.BROKEN_FORESHADOW,
                    node_id     = edge.src_id,
                    label       = src_node.label if src_node else edge.src_id,
                    detail      = f"복선 대상 씬 없음: dst_id={edge.dst_id}",
                    severity    = self._sev_foreshadow,
                    related_ids = [edge.dst_id],
                ))
                continue

            if dst_node.node_type != NarrativeNodeType.SCENE:
                items.append(NarrativeDebtItem(
                    debt_type   = DebtType.BROKEN_FORESHADOW,
                    node_id     = edge.src_id,
                    label       = src_node.label if src_node else edge.src_id,
                    detail      = f"복선 대상이 SCENE이 아님: {dst_node.node_type}",
                    severity    = self._sev_foreshadow * 0.7,
                    related_ids = [edge.dst_id],
                ))
                continue

            incoming = self._store.edges_to(dst_node.node_id)
            causal_in = [
                e for e in incoming
                if e.edge_type in (
                    NarrativeEdgeType.CAUSES,
                    NarrativeEdgeType.DEPENDS_ON,
                )
            ]
            if not causal_in:
                items.append(NarrativeDebtItem(
                    debt_type   = DebtType.BROKEN_FORESHADOW,
                    node_id     = edge.src_id,
                    label       = src_node.label if src_node else edge.src_id,
                    detail      = (
                        f"복선 대상 씬({dst_node.node_id})에 "
                        "CAUSES/DEPENDS_ON 인입 엣지 없음(고아 씬)"
                    ),
                    severity    = self._sev_foreshadow * 0.5,
                    related_ids = [dst_node.node_id],
                ))

        return items

    def _detect_abandoned_threads(self) -> List[NarrativeDebtItem]:
        items: List[NarrativeDebtItem] = []
        for node in self._store.nodes_by_type(NarrativeNodeType.CHARACTER):
            outgoing = self._store.edges_from(node.node_id)
            episode_last = getattr(node, "episode_last", None)

            if episode_last is None and not outgoing:
                items.append(NarrativeDebtItem(
                    debt_type   = DebtType.ABANDONED_THREAD,
                    node_id     = node.node_id,
                    label       = node.label,
                    detail      = "episode_last 미설정 + 나가는 엣지 없음",
                    severity    = self._sev_thread,
                    related_ids = [],
                ))
            elif not outgoing:
                items.append(NarrativeDebtItem(
                    debt_type   = DebtType.ABANDONED_THREAD,
                    node_id     = node.node_id,
                    label       = node.label,
                    detail      = "캐릭터 나가는 엣지 없음(고아 캐릭터)",
                    severity    = self._sev_thread * 0.6,
                    related_ids = [],
                ))

        return items

DebtType = NarrativeDebtType  # V579 backward-compat alias
