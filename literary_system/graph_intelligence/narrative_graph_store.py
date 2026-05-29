"""V527 — NarrativeGraphStore: 인메모리 BFS 서사 그래프 저장소"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, Iterable, List, Optional, Set, Tuple

from literary_system.graph_intelligence.narrative_graph_schema import (
    NarrativeEdge,
    NarrativeEdgeType,
    NarrativeNode,
    NarrativeNodeType,
)


class NarrativeGraphStore:
    def __init__(self):
        self._nodes: Dict[str,NarrativeNode] = {}
        self._edges: Dict[str,NarrativeEdge] = {}
        self._adj:  Dict[str,List[Tuple[str,str]]] = defaultdict(list)
        self._radj: Dict[str,List[Tuple[str,str]]] = defaultdict(list)
        self._ecnt: int = 0

    def add_node(self, node: NarrativeNode) -> None:
        self._nodes[node.node_id] = node

    def add_edge(self, edge: NarrativeEdge) -> None:
        if edge.src_id not in self._nodes or edge.dst_id not in self._nodes:
            raise ValueError(f"Edge {edge.edge_id}: nodes not in graph")
        self._edges[edge.edge_id] = edge
        self._adj[edge.src_id].append((edge.dst_id, edge.edge_id))
        self._radj[edge.dst_id].append((edge.src_id, edge.edge_id))

    def remove_node(self, node_id: str) -> bool:
        if node_id not in self._nodes: return False
        for _,eid in list(self._adj.get(node_id,[])): self._del_edge(eid)
        for _,eid in list(self._radj.get(node_id,[])): self._del_edge(eid)
        del self._nodes[node_id]; self._adj.pop(node_id,None); self._radj.pop(node_id,None)
        return True

    def _del_edge(self, eid: str) -> None:
        e = self._edges.pop(eid, None)
        if e:
            self._adj[e.src_id]  = [(d,i) for d,i in self._adj[e.src_id]  if i!=eid]
            self._radj[e.dst_id] = [(s,i) for s,i in self._radj[e.dst_id] if i!=eid]

    def get_node(self, nid: str) -> Optional[NarrativeNode]: return self._nodes.get(nid)
    def get_edge(self, eid: str) -> Optional[NarrativeEdge]: return self._edges.get(eid)

    def nodes_by_type(self, t: NarrativeNodeType) -> List[NarrativeNode]:
        return [n for n in self._nodes.values() if n.node_type==t]
    def edges_by_type(self, t: NarrativeEdgeType) -> List[NarrativeEdge]:
        return [e for e in self._edges.values() if e.edge_type==t]
    def edges_from(self, nid: str) -> List[NarrativeEdge]:
        return [self._edges[eid] for _,eid in self._adj.get(nid,[])]
    def edges_to(self, nid: str) -> List[NarrativeEdge]:
        return [self._edges[eid] for _,eid in self._radj.get(nid,[])]

    def neighbors(self, nid: str, depth: int=1,
                  edge_types: Optional[Iterable[NarrativeEdgeType]]=None) -> Set[str]:
        allowed = set(edge_types) if edge_types else None
        visited: Set[str] = set(); q: deque[Tuple[str,int]] = deque([(nid,0)])
        while q:
            cur, d = q.popleft()
            if cur in visited: continue
            visited.add(cur)
            if d >= depth: continue
            for dst,eid in self._adj.get(cur,[]):
                e = self._edges[eid]
                if (allowed is None or e.edge_type in allowed) and dst not in visited:
                    q.append((dst, d+1))
        visited.discard(nid); return visited

    def reverse_neighbors(self, nid: str, depth: int=1,
                          edge_types: Optional[Iterable[NarrativeEdgeType]]=None) -> Set[str]:
        allowed = set(edge_types) if edge_types else None
        visited: Set[str] = set(); q: deque[Tuple[str,int]] = deque([(nid,0)])
        while q:
            cur, d = q.popleft()
            if cur in visited: continue
            visited.add(cur)
            if d >= depth: continue
            for src,eid in self._radj.get(cur,[]):
                e = self._edges[eid]
                if (allowed is None or e.edge_type in allowed) and src not in visited:
                    q.append((src, d+1))
        visited.discard(nid); return visited

    def connected_scenes(self, sid: str, depth: int=2) -> Set[str]:
        all_n = self.neighbors(sid,depth) | self.reverse_neighbors(sid,depth)
        return {n for n in all_n if n in self._nodes and self._nodes[n].node_type==NarrativeNodeType.SCENE}

    def make_edge_id(self) -> str:
        self._ecnt += 1; return f"E{self._ecnt:06d}"

    @property
    def node_count(self) -> int: return len(self._nodes)
    @property
    def edge_count(self) -> int: return len(self._edges)

    def stats(self) -> Dict[str,int]:
        nc: Dict[str,int] = defaultdict(int)
        for n in self._nodes.values(): nc[n.node_type.value] += 1
        ec: Dict[str,int] = defaultdict(int)
        for e in self._edges.values(): ec[e.edge_type.value] += 1
        return {"nodes_total": self.node_count, "edges_total": self.edge_count,
                **{f"node_{k}":v for k,v in nc.items()}, **{f"edge_{k}":v for k,v in ec.items()}}
