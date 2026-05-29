"""V360: NKGChangeDetector — 씬 변경 감지."""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from literary_system.nkg.graph_store import NKGGraphStore
from literary_system.nkg.schema import NKGNodeType


@dataclass
class ChangeDetectionResult:
    changed_ids:     List[str]
    unchanged_ids:   List[str]
    new_ids:         List[str]
    duration_ms:     float

class NKGChangeDetector:
    def __init__(self, graph: NKGGraphStore) -> None:
        self._g = graph
        self._snapshots: Dict[str, str] = {}

    def snapshot_all(self) -> int:
        scenes = self._g.nodes_by_type(NKGNodeType.SCENE)
        for s in scenes:
            self._snapshots[s.node_id] = s.content_hash()
        return len(scenes)

    def scan_changes(self, target_scene_ids: Optional[List[str]] = None) -> ChangeDetectionResult:
        t0 = time.perf_counter()
        scenes = self._g.nodes_by_type(NKGNodeType.SCENE)
        scene_map = {s.node_id: s for s in scenes}
        targets = target_scene_ids or list(scene_map.keys())
        changed = []; unchanged = []; new_ids = []
        for sid in targets:
            node = scene_map.get(sid)
            if node is None: continue
            h = node.content_hash()
            old_h = self._snapshots.get(sid)
            if old_h is None: new_ids.append(sid)
            elif old_h != h: changed.append(sid)
            else: unchanged.append(sid)
        return ChangeDetectionResult(changed, unchanged, new_ids,
                                     round((time.perf_counter()-t0)*1000, 2))

    def rename_dry_run(self, old_id: str, new_id: str) -> Dict:
        affected_edges = []
        for e in self._g.all_edges():
            if e.source == old_id or e.target == old_id:
                affected_edges.append({"source": e.source, "target": e.target,
                                       "type": e.edge_type.value})
        return {"old_id": old_id, "new_id": new_id,
                "affected_edges": len(affected_edges),
                "details": affected_edges, "safe": True}
