"""V360: NKGGraphStore — 군집/프로세스 노드 지원 추가."""
from __future__ import annotations
from collections import defaultdict
from typing import Dict, List, Optional, Set, Any
from literary_system.nkg.schema import (
    NKGNode, NKGEdge, NKGNodeType, NKGEdgeType,
    CharacterNode, SceneNode, ForeshadowNode,
    ConflictClusterNode, NarrativeProcessNode,
)

class NKGGraphStore:
    def __init__(self) -> None:
        self._nodes: Dict[str, NKGNode]          = {}
        self._edges: List[NKGEdge]               = []
        self._out:   Dict[str, List[NKGEdge]]    = defaultdict(list)
        self._in:    Dict[str, List[NKGEdge]]    = defaultdict(list)

    # ── 노드 ──────────────────────────────────────────────────
    def add_node(self, node: NKGNode) -> None:
        self._nodes[node.node_id] = node

    def get_node(self, node_id: str) -> Optional[NKGNode]:
        return self._nodes.get(node_id)

    def remove_node(self, node_id: str) -> None:
        self._nodes.pop(node_id, None)

    def all_nodes(self) -> List[NKGNode]:
        return list(self._nodes.values())

    def nodes_by_type(self, ntype: NKGNodeType) -> List[NKGNode]:
        return [n for n in self._nodes.values() if n.node_type == ntype]

    # ── 엣지 ──────────────────────────────────────────────────
    def add_edge(self, edge: NKGEdge) -> None:
        self._edges.append(edge)
        self._out[edge.source].append(edge)
        self._in[edge.target].append(edge)

    def all_edges(self) -> List[NKGEdge]:
        return list(self._edges)

    def edges_from(self, node_id: str, edge_type: Optional[NKGEdgeType] = None) -> List[NKGEdge]:
        edges = self._out.get(node_id, [])
        if edge_type:
            edges = [e for e in edges if e.edge_type == edge_type]
        return edges

    def edges_to(self, node_id: str, edge_type: Optional[NKGEdgeType] = None) -> List[NKGEdge]:
        edges = self._in.get(node_id, [])
        if edge_type:
            edges = [e for e in edges if e.edge_type == edge_type]
        return edges

    def remove_edges_for(self, node_id: str) -> None:
        self._edges = [e for e in self._edges
                       if e.source != node_id and e.target != node_id]
        self._out.pop(node_id, None)
        self._in.pop(node_id, None)
        for src, lst in self._out.items():
            self._out[src] = [e for e in lst if e.target != node_id]
        for tgt, lst in self._in.items():
            self._in[tgt] = [e for e in lst if e.source != node_id]

    # ── V360 전용 쿼리 ─────────────────────────────────────────
    def clusters(self) -> List[ConflictClusterNode]:
        return [n for n in self._nodes.values()
                if isinstance(n, ConflictClusterNode)]

    def processes(self) -> List[NarrativeProcessNode]:
        return [n for n in self._nodes.values()
                if isinstance(n, NarrativeProcessNode)]

    def cluster_members(self, cluster_id: str) -> List[CharacterNode]:
        cn = self._nodes.get(cluster_id)
        if not isinstance(cn, ConflictClusterNode):
            return []
        return [self._nodes[mid] for mid in cn.member_ids
                if mid in self._nodes and isinstance(self._nodes[mid], CharacterNode)]

    def process_steps(self, process_id: str) -> List[SceneNode]:
        pn = self._nodes.get(process_id)
        if not isinstance(pn, NarrativeProcessNode):
            return []
        return [self._nodes[sid] for sid in pn.steps
                if sid in self._nodes and isinstance(self._nodes[sid], SceneNode)]

    def foreshadow_candidates(self) -> List[ForeshadowNode]:
        return [n for n in self._nodes.values()
                if isinstance(n, ForeshadowNode) and n.is_candidate]

    def node_count(self) -> int:
        return len(self._nodes)

    def edge_count(self) -> int:
        return len(self._edges)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "node_count": self.node_count(),
            "edge_count": self.edge_count(),
            "cluster_count": len(self.clusters()),
            "process_count": len(self.processes()),
        }
