"""V350: GDAP — DKGGraphStore.

설계도 섹션 2·4 구현.
networkx DiGraph 기반 개발 지식 그래프 저장소.
nx 미설치 시 dict 기반 fallback.
"""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

from literary_system.gdap.schema import (
    CONTRACT_EDGES,
    DEPENDENCY_EDGES,
    REFERENCE_EDGES,
    VERIFICATION_EDGES,
    DKGClassNode,
    DKGConfigNode,
    DKGEdge,
    DKGEdgeType,
    DKGFileNode,
    DKGFunctionNode,
    DKGModuleNode,
    DKGNodeType,
    DKGSchemaNode,
    DKGTestNode,
    node_type_of,
)

try:
    import networkx as nx
    _NX_AVAILABLE = True
except ImportError:
    nx = None  # type: ignore
    _NX_AVAILABLE = False


class DKGGraphStore:
    """DKG 저장 및 조회 인터페이스.

    내부적으로 networkx.DiGraph 사용 (미설치 시 dict fallback).
    엣지는 (source_id, target_id, edge_type) 키로 중복 방지.
    """

    def __init__(self) -> None:
        if _NX_AVAILABLE:
            self._g = nx.DiGraph()
        else:
            self._g = None
        # Fallback 구조
        self._nodes: Dict[str, Any] = {}
        self._edges: Dict[tuple, DKGEdge] = {}   # (src, tgt, type) → DKGEdge

    # ── 노드 추가 ────────────────────────────────────────────

    def add_node(self, node: Any) -> None:
        nid = node.node_id()
        self._nodes[nid] = node
        if _NX_AVAILABLE:
            self._g.add_node(nid, data=node, node_type=node_type_of(node).value)

    def add_file_node(self, path: str, lang: str = "python") -> DKGFileNode:
        n = DKGFileNode(path=path, lang=lang)
        self.add_node(n)
        return n

    def add_module_node(self, module_id: str, package: str = "") -> DKGModuleNode:
        n = DKGModuleNode(module_id=module_id, package=package)
        self.add_node(n)
        return n

    def add_function_node(self, func_id: str, file_path: str,
                          signature: str = "") -> DKGFunctionNode:
        n = DKGFunctionNode(func_id=func_id, file_path=file_path, signature=signature)
        self.add_node(n)
        return n

    def add_class_node(self, class_id: str, file_path: str) -> DKGClassNode:
        n = DKGClassNode(class_id=class_id, file_path=file_path)
        self.add_node(n)
        return n

    def add_schema_node(self, schema_id: str, fields: List[str] = None) -> DKGSchemaNode:
        n = DKGSchemaNode(schema_id=schema_id, fields=fields or [])
        self.add_node(n)
        return n

    def add_test_node(self, test_id: str, file_path: str,
                      target_func: str = "") -> DKGTestNode:
        n = DKGTestNode(test_id=test_id, file_path=file_path, target_func=target_func)
        self.add_node(n)
        return n

    def add_config_node(self, config_id: str, fmt: str = "toml") -> DKGConfigNode:
        n = DKGConfigNode(config_id=config_id, format=fmt)
        self.add_node(n)
        return n

    # ── 엣지 추가 ────────────────────────────────────────────

    def add_edge(self, edge: DKGEdge) -> bool:
        """DKGEdge 추가. 중복이면 False."""
        key = (edge.source_id, edge.target_id, edge.edge_type.value)
        if key in self._edges:
            return False
        self._edges[key] = edge
        if _NX_AVAILABLE:
            if not self._g.has_node(edge.source_id):
                self._g.add_node(edge.source_id)
            if not self._g.has_node(edge.target_id):
                self._g.add_node(edge.target_id)
            self._g.add_edge(edge.source_id, edge.target_id,
                             edge_type=edge.edge_type.value,
                             weight=edge.weight,
                             confidence=edge.confidence)
        return True

    def add_edge_raw(self, source_id: str, target_id: str,
                     edge_type: DKGEdgeType,
                     weight: float = 1.0,
                     confidence: float = 1.0) -> bool:
        edge = DKGEdge(source_id=source_id, target_id=target_id,
                       edge_type=edge_type, weight=weight, confidence=confidence)
        return self.add_edge(edge)

    # ── 조회 ─────────────────────────────────────────────────

    def get_node(self, node_id: str) -> Optional[Any]:
        return self._nodes.get(node_id)

    def has_node(self, node_id: str) -> bool:
        return node_id in self._nodes

    def all_node_ids(self) -> List[str]:
        return list(self._nodes.keys())

    def nodes_by_type(self, node_type: DKGNodeType) -> List[Any]:
        return [n for n in self._nodes.values()
                if node_type_of(n) == node_type]

    def successors(self, node_id: str) -> List[str]:
        if _NX_AVAILABLE and self._g.has_node(node_id):
            return list(self._g.successors(node_id))
        return [e.target_id for e in self._edges.values()
                if e.source_id == node_id]

    def predecessors(self, node_id: str) -> List[str]:
        if _NX_AVAILABLE and self._g.has_node(node_id):
            return list(self._g.predecessors(node_id))
        return [e.source_id for e in self._edges.values()
                if e.target_id == node_id]

    def neighbors(self, node_id: str) -> List[str]:
        seen: Set[str] = set()
        result = []
        for n in self.successors(node_id) + self.predecessors(node_id):
            if n not in seen and n != node_id:
                seen.add(n)
                result.append(n)
        return result

    def edges_from(self, node_id: str) -> List[DKGEdge]:
        return [e for e in self._edges.values() if e.source_id == node_id]

    def edges_to(self, node_id: str) -> List[DKGEdge]:
        return [e for e in self._edges.values() if e.target_id == node_id]

    def edges_by_type(self, edge_type: DKGEdgeType) -> List[DKGEdge]:
        return [e for e in self._edges.values()
                if e.edge_type == edge_type]

    # ── 레이어별 서브그래프 뷰 ───────────────────────────────

    def dependency_edges(self) -> List[DKGEdge]:
        return [e for e in self._edges.values()
                if e.edge_type.value in DEPENDENCY_EDGES]

    def contract_edges(self) -> List[DKGEdge]:
        return [e for e in self._edges.values()
                if e.edge_type.value in CONTRACT_EDGES]

    def verification_edges(self) -> List[DKGEdge]:
        return [e for e in self._edges.values()
                if e.edge_type.value in VERIFICATION_EDGES]

    def reference_edges(self) -> List[DKGEdge]:
        return [e for e in self._edges.values()
                if e.edge_type.value in REFERENCE_EDGES]

    # ── 직접 의존 노드 조회 ──────────────────────────────────

    def direct_dependencies(self, node_id: str) -> List[str]:
        """node_id가 즉시 의존하는 노드 목록 (IMPORTS/CALLS/INHERITS)."""
        return [e.target_id for e in self.edges_from(node_id)
                if e.edge_type.value in DEPENDENCY_EDGES]

    def test_nodes_for(self, node_id: str) -> List[str]:
        """node_id를 테스트하는 TEST 노드 목록."""
        return [e.source_id for e in self.edges_to(node_id)
                if e.edge_type == DKGEdgeType.TESTS]

    # ── 저장/불러오기 ────────────────────────────────────────

    def save(self, path: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "wb") as f:
            pickle.dump({"nodes": self._nodes, "edges": self._edges}, f)

    @classmethod
    def load(cls, path: str) -> "DKGGraphStore":
        store = cls()
        with open(path, "rb") as f:
            data = pickle.load(f)
        for nid, node in data["nodes"].items():
            store.add_node(node)
        for edge in data["edges"].values():
            store.add_edge(edge)
        return store

    # ── 통계 ─────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        type_counts: Dict[str, int] = {}
        for n in self._nodes.values():
            t = node_type_of(n).value
            type_counts[t] = type_counts.get(t, 0) + 1
        edge_counts: Dict[str, int] = {}
        for e in self._edges.values():
            t = e.edge_type.value
            edge_counts[t] = edge_counts.get(t, 0) + 1
        return {
            "nodes":      len(self._nodes),
            "edges":      len(self._edges),
            "node_types": type_counts,
            "edge_types": edge_counts,
            "nx_available": _NX_AVAILABLE,
        }
