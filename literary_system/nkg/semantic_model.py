"""V360: NKGSemanticModel — 3단계 상태 머신."""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from literary_system.nkg.schema import SemanticModelState, NKGNodeType
from literary_system.nkg.graph_store import NKGGraphStore

class SemanticModelError(Exception): pass
class SemanticModelFrozenError(SemanticModelError): pass
class SemanticModelNotFrozenError(SemanticModelError): pass

@dataclass
class ReconcileReport:
    merged_nodes:   List[Tuple[str, str]]
    conflict_edges: List[str]
    duration_ms:    float

class NKGSemanticModel:
    def __init__(self, graph: NKGGraphStore) -> None:
        self._graph = graph
        self._state = SemanticModelState.WRITE
        self._frozen_at: Optional[float] = None
        self._snapshot: Optional[Dict[str, Any]] = None

    @property
    def state(self) -> SemanticModelState: return self._state
    def is_frozen(self) -> bool: return self._state == SemanticModelState.FROZEN

    def guard_write(self, operation: str = "") -> None:
        if self._state == SemanticModelState.FROZEN:
            raise SemanticModelFrozenError(f"FROZEN 상태 수정 불가: {operation}")

    def reconcile(self) -> ReconcileReport:
        if self._state == SemanticModelState.FROZEN:
            raise SemanticModelFrozenError("FROZEN 상태에서 reconcile 불가.")
        t0 = time.perf_counter()
        self._state = SemanticModelState.RECONCILE
        merged = []; conflict_edges = []
        chars = self._graph.nodes_by_type(NKGNodeType.CHARACTER)
        label_map: Dict[str, list] = {}
        for c in chars:
            key = c.label.lower().strip()
            label_map.setdefault(key, []).append(c)
        for label, nodes in label_map.items():
            if len(nodes) <= 1: continue
            keeper = min(nodes, key=lambda n: n.created_at)
            for dup in nodes:
                if dup.node_id == keeper.node_id: continue
                self._reroute_edges(dup.node_id, keeper.node_id)
                self._graph.remove_node(dup.node_id)
                merged.append((dup.node_id, keeper.node_id))
        return ReconcileReport(merged, conflict_edges, round((time.perf_counter()-t0)*1000, 2))

    def freeze(self) -> Dict[str, Any]:
        if self._state != SemanticModelState.RECONCILE:
            if self._state == SemanticModelState.WRITE:
                self._state = SemanticModelState.RECONCILE
        self._state = SemanticModelState.FROZEN
        self._frozen_at = time.time()
        self._snapshot = self._graph.snapshot()
        self._snapshot["frozen_at"] = self._frozen_at
        return self._snapshot

    def assert_frozen(self) -> None:
        if not self.is_frozen():
            raise SemanticModelNotFrozenError("GR-04: FROZEN 상태가 아닙니다.")

    def _reroute_edges(self, old_id: str, new_id: str) -> None:
        for e in self._graph.edges_from(old_id):
            e.source = new_id
        for e in self._graph.edges_to(old_id):
            e.target = new_id
