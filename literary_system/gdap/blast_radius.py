"""V360: BlastRadiusCalculator v2 — DKG+NKG 통합."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from literary_system.nkg.graph_store import NKGGraphStore


@dataclass
class BlastRadius:
    changed_files:     List[str]
    upstream_nodes:    List[str]
    downstream_nodes:  List[str]
    blast_ratio:       float
    total_nodes:       int

class BlastRadiusCalculator:
    def __init__(self, nkg: Optional[NKGGraphStore] = None,
                 dkg: Optional[object] = None) -> None:
        self._nkg = nkg; self._dkg = dkg

    def calculate(self, changed_files: List[str], depth: int = 2) -> BlastRadius:
        if not self._nkg:
            return BlastRadius(changed_files, [], [], 0.0, 0)
        all_nodes = self._nkg.all_nodes()
        total = max(len(all_nodes), 1)
        affected: Set[str] = set(changed_files)
        upstream = self._bfs(changed_files, direction="up", depth=depth)
        downstream = self._bfs(changed_files, direction="down", depth=depth)
        affected |= upstream | downstream
        ratio = len(affected) / total
        return BlastRadius(changed_files, list(upstream), list(downstream), min(ratio, 1.0), total)

    def _bfs(self, starts: List[str], direction: str, depth: int) -> Set[str]:
        visited: Set[str] = set(); q = deque((s, 0) for s in starts)
        while q:
            nid, d = q.popleft()
            if d >= depth: continue
            if direction == "down":
                edges = self._nkg.edges_from(nid)
            else:
                edges = self._nkg.edges_to(nid)
            for e in edges:
                nb = e.target if direction == "down" else e.source
                if nb not in visited: visited.add(nb); q.append((nb, d+1))
        return visited
