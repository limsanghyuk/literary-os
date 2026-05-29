"""V360: NKGProcessDetector — BFS 씬 흐름 탐지."""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from literary_system.nkg.graph_store import NKGGraphStore
from literary_system.nkg.schema import (
    ForeshadowNode,
    NarrativeProcessNode,
    NKGEdge,
    NKGEdgeType,
    NKGNodeType,
    SceneNode,
    make_process_id,
)

BFS_MAX_DEPTH      = 8
MIN_CHAIN_LENGTH   = 3
FORESHADOW_TENSION = 0.7

@dataclass
class ProcessDetectionResult:
    processes:   List[NarrativeProcessNode]
    step_edges:  List[NKGEdge]
    foreshadows: List[ForeshadowNode]
    duration_ms: float

class NKGProcessDetector:
    def __init__(self, graph: NKGGraphStore,
                 max_depth: int = BFS_MAX_DEPTH,
                 min_chain: int = MIN_CHAIN_LENGTH) -> None:
        self._g = graph; self._max_depth = max_depth; self._min_chain = min_chain

    def detect(self) -> ProcessDetectionResult:
        t0 = time.perf_counter()
        scenes = self._g.nodes_by_type(NKGNodeType.SCENE)
        if not scenes:
            return ProcessDetectionResult([], [], [], round((time.perf_counter()-t0)*1000, 2))
        entries = self._find_entry_scenes(scenes)
        processes = []; step_edges = []; foreshadows = []; proc_idx = 0
        visited_global: Set[str] = set()
        for entry in entries:
            chain = self._bfs_chain(entry, visited_global)
            if len(chain) < self._min_chain: continue
            visited_global.update(chain)
            tension_arc = self._compute_tension_arc(chain)
            fc = self._find_foreshadow_candidates(chain, tension_arc)
            pn = NarrativeProcessNode(
                node_type=NKGNodeType.NARRATIVE_PROCESS,
                node_id=make_process_id(proc_idx),
                label=f"Process-{proc_idx}",
                process_id=make_process_id(proc_idx),
                entry_scene=chain[0],
                resolution_scene=chain[-1],
                steps=chain,
                foreshadow_candidates=fc,
                tension_arc=tension_arc,
            )
            processes.append(pn)
            self._g.add_node(pn)
            for i in range(len(chain)-1):
                e = NKGEdge(source=chain[i], target=chain[i+1],
                            edge_type=NKGEdgeType.STEP_IN_NARRATIVE, weight=1.0, confidence=0.9)
                step_edges.append(e)
                try: self._g.add_edge(e)
                except Exception: pass
            for sid in fc:
                scene = self._g.get_node(sid)
                fn = ForeshadowNode(
                    node_type=NKGNodeType.FORESHADOW,
                    node_id=f"foreshadow_{sid}",
                    label=f"Foreshadow@{sid}",
                    planted_scene=sid, payoff_scene=chain[-1],
                    reveal_budget=0.3, is_candidate=True,
                )
                foreshadows.append(fn)
                try: self._g.add_node(fn)
                except Exception: pass
            proc_idx += 1
        return ProcessDetectionResult(processes, step_edges, foreshadows,
                                      round((time.perf_counter()-t0)*1000, 2))

    def _find_entry_scenes(self, scenes) -> List[str]:
        has_causal_in = set()
        for s in scenes:
            for e in self._g.edges_to(s.node_id):
                if e.edge_type in (NKGEdgeType.CAUSAL_LINK, NKGEdgeType.ENABLES,
                                   NKGEdgeType.STEP_IN_NARRATIVE):
                    has_causal_in.add(s.node_id)
        entries = [s.node_id for s in scenes if s.node_id not in has_causal_in]
        if not entries: entries = [scenes[0].node_id]
        scenes_map = {s.node_id: s for s in scenes}
        entries.sort(key=lambda sid: getattr(scenes_map.get(sid), "scene_order", 0))
        return entries

    def _bfs_chain(self, entry: str, visited_global: Set[str]) -> List[str]:
        chain = []; q = deque([(entry, 0)]); visited = {entry}
        while q:
            nid, depth = q.popleft()
            if depth > self._max_depth: break
            chain.append(nid)
            nexts = []
            for e in self._g.edges_from(nid):
                if e.edge_type in (NKGEdgeType.CAUSAL_LINK, NKGEdgeType.ENABLES,
                                   NKGEdgeType.STEP_IN_NARRATIVE):
                    tgt = e.target
                    if tgt not in visited and tgt not in visited_global:
                        tgt_node = self._g.get_node(tgt)
                        if tgt_node and tgt_node.node_type == NKGNodeType.SCENE:
                            visited.add(tgt); nexts.append((tgt, depth+1))
            nexts.sort(key=lambda x: getattr(self._g.get_node(x[0]), "scene_order", 0))
            q.extend(nexts)
        return chain

    def _compute_tension_arc(self, chain: List[str]) -> List[float]:
        arc = []
        for sid in chain:
            node = self._g.get_node(sid)
            tension = getattr(node, "tension_value", 0.5) if node else 0.5
            arc.append(tension)
        return arc

    def _find_foreshadow_candidates(self, chain: List[str], tension_arc: List[float]) -> List[str]:
        candidates = []
        for i, (sid, tension) in enumerate(zip(chain, tension_arc)):
            if tension >= FORESHADOW_TENSION and i < len(chain) - 1:
                candidates.append(sid)
        return candidates
