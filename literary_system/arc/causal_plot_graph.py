"""
V380: arc/causal_plot_graph.py — CausalPlotGraph

16부작 전체 아크를 방향성 그래프로 관리.
NKGGraphStore와 분리된 독립 그래프 — 서사 설계 레이어(L1)에서 동작.

기능:
  - ArcPlotNode / ArcPlotEdge CRUD
  - 에피소드 간 인과·복선 엣지 자동 추론 (패턴 기반, LLM 0회)
  - 4막(기/승/전/결) 구조 검증
  - 텐션 곡선 생성 (선형 + S자형)
  - NKGGraphStore 동기화 (단방향 write)

LLM 0회.
"""
from __future__ import annotations

import logging
import math
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from literary_system.arc.schema import (
    ArcAct,
    ArcPlotEdge,
    ArcPlotEdgeType,
    ArcPlotNode,
)

logger = logging.getLogger(__name__)


class CausalPlotGraph:
    """
    에피소드 단위 인과 플롯 그래프.

    사용 예:
        graph = CausalPlotGraph()
        planner = SeriesArcPlanner(total_episodes=16)
        planner.plan(graph)
        logger.debug(graph.tension_curve())
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, ArcPlotNode] = {}
        self._edges: List[ArcPlotEdge]      = []
        self._out:   Dict[str, List[ArcPlotEdge]] = defaultdict(list)
        self._in:    Dict[str, List[ArcPlotEdge]] = defaultdict(list)

    # ── 노드 ──────────────────────────────────────────────────────
    def add_node(self, node: ArcPlotNode) -> None:
        self._nodes[node.episode_id] = node

    def get_node(self, episode_id: str) -> Optional[ArcPlotNode]:
        return self._nodes.get(episode_id)

    def remove_node(self, episode_id: str) -> None:
        self._nodes.pop(episode_id, None)
        self.remove_edges_for(episode_id)

    def all_nodes(self) -> List[ArcPlotNode]:
        return sorted(self._nodes.values(), key=lambda n: n.episode_index)

    def nodes_by_act(self, act: ArcAct) -> List[ArcPlotNode]:
        return [n for n in self._nodes.values() if n.act == act]

    # ── 엣지 ──────────────────────────────────────────────────────
    def add_edge(self, edge: ArcPlotEdge) -> None:
        self._edges.append(edge)
        self._out[edge.source].append(edge)
        self._in[edge.target].append(edge)

    def all_edges(self) -> List[ArcPlotEdge]:
        return list(self._edges)

    def edges_from(self, episode_id: str,
                   edge_type: Optional[ArcPlotEdgeType] = None) -> List[ArcPlotEdge]:
        edges = self._out.get(episode_id, [])
        if edge_type:
            edges = [e for e in edges if e.edge_type == edge_type]
        return edges

    def edges_to(self, episode_id: str,
                 edge_type: Optional[ArcPlotEdgeType] = None) -> List[ArcPlotEdge]:
        edges = self._in.get(episode_id, [])
        if edge_type:
            edges = [e for e in edges if e.edge_type == edge_type]
        return edges

    def remove_edges_for(self, episode_id: str) -> None:
        # 제거할 엣지의 반대쪽 노드에서도 참조 정리
        for e in self._out.get(episode_id, []):
            self._in[e.target] = [x for x in self._in.get(e.target, [])
                                   if x.source != episode_id]
        for e in self._in.get(episode_id, []):
            self._out[e.source] = [x for x in self._out.get(e.source, [])
                                   if x.target != episode_id]
        self._edges = [e for e in self._edges
                       if e.source != episode_id and e.target != episode_id]
        self._out.pop(episode_id, None)
        self._in.pop(episode_id, None)

    # ── 인과 연쇄 자동 추론 ──────────────────────────────────────
    def infer_causal_edges(self) -> List[ArcPlotEdge]:
        """
        ArcPlotNode.causal_inputs 선언을 기반으로 CAUSAL 엣지 자동 생성.
        이미 존재하는 엣지는 중복 추가하지 않는다.
        """
        existing = {(e.source, e.target, e.edge_type) for e in self._edges}
        new_edges: List[ArcPlotEdge] = []
        for node in self._nodes.values():
            for src_id in node.causal_inputs:
                key = (src_id, node.episode_id, ArcPlotEdgeType.CAUSAL)
                if key not in existing and src_id in self._nodes:
                    edge = ArcPlotEdge(
                        source=src_id,
                        target=node.episode_id,
                        edge_type=ArcPlotEdgeType.CAUSAL,
                        weight=1.0,
                        description=f"{src_id}→{node.episode_id} 인과 연쇄",
                    )
                    self.add_edge(edge)
                    existing.add(key)
                    new_edges.append(edge)
        return new_edges

    def infer_foreshadow_edges(self) -> List[ArcPlotEdge]:
        """
        reveal_budget > 0 인 에피소드에서 이전 에피소드의 복선 심기 엣지를 자동 추론.
        기/승 구간 → 전/결 구간으로의 FORESHADOW 엣지 생성.
        """
        existing = {(e.source, e.target, e.edge_type) for e in self._edges}
        new_edges: List[ArcPlotEdge] = []
        gi_seung = [n for n in self._nodes.values()
                    if n.act in (ArcAct.GI, ArcAct.SEUNG)]
        jeon_gyeol = [n for n in self._nodes.values()
                      if n.act in (ArcAct.JEON, ArcAct.GYEOL) and n.reveal_budget > 0]

        for payoff_node in jeon_gyeol:
            # 인덱스가 이전인 기/승 에피소드 중 하나를 복선 출발점으로 선택
            candidates = [n for n in gi_seung
                          if n.episode_index < payoff_node.episode_index]
            if not candidates:
                continue
            # 회수 화 기준 절반 이전에서 복선 심기
            mid_idx = payoff_node.episode_index // 2
            source_node = min(
                candidates,
                key=lambda n: abs(n.episode_index - mid_idx)
            )
            key = (source_node.episode_id, payoff_node.episode_id,
                   ArcPlotEdgeType.FORESHADOW)
            if key not in existing:
                edge = ArcPlotEdge(
                    source=source_node.episode_id,
                    target=payoff_node.episode_id,
                    edge_type=ArcPlotEdgeType.FORESHADOW,
                    weight=payoff_node.reveal_budget,
                    description=f"{source_node.episode_id}에서 심은 복선 → {payoff_node.episode_id}에서 회수",
                )
                self.add_edge(edge)
                existing.add(key)
                new_edges.append(edge)
                # CALLBACK 역방향도 추가
                cb_key = (payoff_node.episode_id, source_node.episode_id,
                          ArcPlotEdgeType.CALLBACK)
                if cb_key not in existing:
                    cb_edge = ArcPlotEdge(
                        source=payoff_node.episode_id,
                        target=source_node.episode_id,
                        edge_type=ArcPlotEdgeType.CALLBACK,
                        weight=payoff_node.reveal_budget,
                        description=f"{payoff_node.episode_id} 복선 회수 → {source_node.episode_id} 참조",
                    )
                    self.add_edge(cb_edge)
                    existing.add(cb_key)
        return new_edges

    def infer_emotional_escalation_edges(self) -> List[ArcPlotEdge]:
        """
        인접 에피소드 간 텐션 상승 구간에서 EMOTIONAL_ESCALATION 엣지 생성.
        """
        existing = {(e.source, e.target, e.edge_type) for e in self._edges}
        nodes = self.all_nodes()
        new_edges: List[ArcPlotEdge] = []
        for i in range(len(nodes) - 1):
            curr = nodes[i]
            nxt  = nodes[i + 1]
            if nxt.tension_level > curr.tension_level:
                key = (curr.episode_id, nxt.episode_id,
                       ArcPlotEdgeType.EMOTIONAL_ESCALATION)
                if key not in existing:
                    edge = ArcPlotEdge(
                        source=curr.episode_id,
                        target=nxt.episode_id,
                        edge_type=ArcPlotEdgeType.EMOTIONAL_ESCALATION,
                        weight=nxt.tension_level - curr.tension_level,
                        description=f"텐션 상승 {curr.tension_level:.2f}→{nxt.tension_level:.2f}",
                    )
                    self.add_edge(edge)
                    existing.add(key)
                    new_edges.append(edge)
        return new_edges

    # ── 텐션 곡선 ────────────────────────────────────────────────
    def tension_curve(self) -> List[Tuple[str, float]]:
        """(episode_id, tension_level) 순서 리스트 반환."""
        return [(n.episode_id, n.tension_level) for n in self.all_nodes()]

    # ── 구조 검증 ─────────────────────────────────────────────────
    def validate_act_structure(self) -> Dict[str, object]:
        """
        4막 구조 검증.
        Returns:
            {"valid": bool, "act_counts": dict, "issues": list}
        """
        act_counts: Dict[str, int] = {a.value: 0 for a in ArcAct}
        for node in self._nodes.values():
            act_counts[node.act.value] += 1

        issues: List[str] = []
        total = len(self._nodes)
        if total == 0:
            issues.append("에피소드가 없음")
        else:
            for act, count in act_counts.items():
                if count == 0:
                    issues.append(f"'{act}' 막 에피소드 없음")

        return {
            "valid":      len(issues) == 0,
            "act_counts": act_counts,
            "total":      total,
            "issues":     issues,
        }

    def summary(self) -> Dict[str, object]:
        """그래프 요약 정보."""
        edge_type_counts: Dict[str, int] = defaultdict(int)
        for e in self._edges:
            edge_type_counts[e.edge_type.value] += 1
        return {
            "total_episodes": len(self._nodes),
            "total_edges":    len(self._edges),
            "edge_types":     dict(edge_type_counts),
            "act_structure":  self.validate_act_structure()["act_counts"],
        }

    # ── NKGGraphStore 동기화 ───────────────────────────────────────
    def sync_to_nkg(self, nkg_store: object) -> int:
        """
        ArcPlotNode들을 NKGGraphStore에 EpisodeNode/ArcNode로 동기화.
        nkg_store: NKGGraphStore 인스턴스 (타입 힌트 순환 방지로 object 사용)
        Returns: 동기화된 노드 수
        """
        from literary_system.nkg.schema import (
            EpisodeNode,
            NKGEdge,
            NKGEdgeType,
            NKGNodeType,
        )
        count = 0
        for arc_node in self._nodes.values():
            ep_node = EpisodeNode(
                node_type=NKGNodeType.EPISODE,
                node_id=arc_node.episode_id,
                label=arc_node.title or arc_node.episode_id,
                episode_index=arc_node.episode_index,
                metadata={
                    "act":              arc_node.act.value,
                    "reveal_budget":    arc_node.reveal_budget,
                    "emotional_target": arc_node.emotional_target,
                    "tension_level":    arc_node.tension_level,
                },
            )
            nkg_store.add_node(ep_node)
            count += 1

        # CAUSAL 엣지 → NKG CausalLink
        for edge in self._edges:
            if edge.edge_type == ArcPlotEdgeType.CAUSAL:
                nkg_edge = NKGEdge(
                    source=edge.source,
                    target=edge.target,
                    edge_type=NKGEdgeType.CAUSAL_LINK,
                    weight=edge.weight,
                )
                nkg_store.add_edge(nkg_edge)
            elif edge.edge_type == ArcPlotEdgeType.FORESHADOW:
                nkg_edge = NKGEdge(
                    source=edge.source,
                    target=edge.target,
                    edge_type=NKGEdgeType.FORESHADOWING,
                    weight=edge.weight,
                )
                nkg_store.add_edge(nkg_edge)
        return count
