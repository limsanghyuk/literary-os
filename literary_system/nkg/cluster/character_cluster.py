"""V360: CharacterClusterDetector — Leiden 알고리즘."""
from __future__ import annotations
import math, random, time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from literary_system.nkg.schema import (
    NKGEdgeType, NKGNodeType, CharacterNode, ConflictClusterNode,
    ConflictType, NKGEdge, make_cluster_id,
)
from literary_system.nkg.graph_store import NKGGraphStore

LEIDEN_RESOLUTION = 0.5; LEIDEN_ITERATIONS = 10; LEIDEN_RANDOM_SEED = 42

@dataclass
class ClusterResult:
    clusters:      List[ConflictClusterNode]
    cluster_edges: List[NKGEdge]
    partition:     Dict[str, int]
    modularity:    float
    duration_ms:   float

class CharacterClusterDetector:
    def __init__(self, graph: NKGGraphStore, resolution: float = LEIDEN_RESOLUTION,
                 iterations: int = LEIDEN_ITERATIONS, seed: int = LEIDEN_RANDOM_SEED) -> None:
        self._graph = graph; self._resolution = resolution
        self._iterations = iterations; self._seed = seed

    def detect(self) -> ClusterResult:
        t0 = time.perf_counter()
        chars = self._graph.nodes_by_type(NKGNodeType.CHARACTER)
        if not chars:
            return ClusterResult([], [], {}, 0.0, round((time.perf_counter()-t0)*1000, 2))
        char_ids = [c.node_id for c in chars]
        adj = self._build_adjacency(char_ids)
        partition = self._leiden(char_ids, adj)
        clusters, cluster_edges = self._build_clusters(chars, partition)
        self._merge_into_graph(clusters, cluster_edges, chars, partition)
        modularity = self._compute_modularity(char_ids, adj, partition)
        return ClusterResult(clusters, cluster_edges, partition, modularity,
                             round((time.perf_counter()-t0)*1000, 2))

    def _build_adjacency(self, char_ids):
        id_set = set(char_ids)
        adj = defaultdict(lambda: defaultdict(float))
        for nid in char_ids:
            for edge in self._graph.edges_from(nid):
                if edge.target in id_set:
                    adj[nid][edge.target] += edge.weight
                    adj[edge.target][nid] += edge.weight
            for edge in self._graph.edges_to(nid):
                if edge.edge_type == NKGEdgeType.INVOLVES and edge.source in id_set:
                    adj[nid][edge.source] += 0.5
                    adj[edge.source][nid] += 0.5
        return adj

    def _leiden(self, char_ids, adj):
        rng = random.Random(self._seed)
        n = len(char_ids)
        if n == 0: return {}
        if n == 1: return {char_ids[0]: 0}
        partition = {nid: i for i, nid in enumerate(char_ids)}
        for _ in range(self._iterations):
            improved = False
            order = char_ids[:]
            rng.shuffle(order)
            for nid in order:
                cur = partition[nid]
                nb_clusters = defaultdict(float)
                for nb, w in adj.get(nid, {}).items():
                    nb_clusters[partition[nb]] += w
                best_c = cur; best_g = 0.0
                cur_sz = sum(1 for v in partition.values() if v == cur) - 1
                for cid, w in nb_clusters.items():
                    if cid == cur: continue
                    tgt_sz = sum(1 for v in partition.values() if v == cid)
                    gain = w - self._resolution * tgt_sz * cur_sz
                    if gain > best_g: best_g = gain; best_c = cid
                if best_c != cur: partition[nid] = best_c; improved = True
            cluster_sizes = defaultdict(int)
            for cid in partition.values(): cluster_sizes[cid] += 1
            for nid in char_ids:
                cid = partition[nid]
                if cluster_sizes[cid] == 1:
                    best_nb = -1; best_w = -1.0
                    for nb, w in adj.get(nid, {}).items():
                        if partition[nb] != cid and w > best_w: best_w = w; best_nb = partition[nb]
                    if best_nb >= 0: partition[nid] = best_nb; improved = True
            if not improved: break
        cmap = {}; idx = 0
        for cid in partition.values():
            if cid not in cmap: cmap[cid] = idx; idx += 1
        return {nid: cmap[cid] for nid, cid in partition.items()}

    def _build_clusters(self, chars, partition):
        char_map = {c.node_id: c for c in chars}
        members = defaultdict(list)
        for nid, cid in partition.items(): members[cid].append(nid)
        cluster_nodes = []
        for cid, mbs in members.items():
            cn = ConflictClusterNode(
                node_type=NKGNodeType.CONFLICT_CLUSTER,
                node_id=make_cluster_id(cid), label=f"Cluster-{cid}",
                cluster_id=make_cluster_id(cid), member_ids=mbs,
                conflict_type=self._infer_conflict_type(mbs),
                cohesion_score=self._compute_cohesion(mbs, partition),
                primary_scene="")
            cluster_nodes.append(cn)
        cluster_edges = []
        cids = list(members.keys())
        for i, ci in enumerate(cids):
            for cj in cids[i+1:]:
                w = self._inter_cluster_weight(members[ci], members[cj], partition)
                if w > 0.1:
                    cluster_edges.append(NKGEdge(
                        source=make_cluster_id(ci), target=make_cluster_id(cj),
                        edge_type=NKGEdgeType.CLUSTER_LINK, weight=w, confidence=0.8))
        return cluster_nodes, cluster_edges

    def _merge_into_graph(self, clusters, cluster_edges, chars, partition):
        for cn in clusters: self._graph.add_node(cn)
        for e in cluster_edges:
            try: self._graph.add_edge(e)
            except Exception: pass
        char_map = {c.node_id: c for c in chars}
        for nid, cid in partition.items():
            cnode_id = make_cluster_id(cid)
            c = char_map.get(nid)
            if c and isinstance(c, CharacterNode): c.cluster_id = cnode_id
            try:
                self._graph.add_edge(NKGEdge(source=nid, target=cnode_id,
                    edge_type=NKGEdgeType.IN_CLUSTER, weight=1.0, confidence=1.0))
            except Exception: pass

    def _infer_conflict_type(self, members):
        if len(members) <= 1: return ConflictType.NEUTRAL
        if len(members) == 2: return ConflictType.RIVAL
        for mid in members:
            node = self._graph.get_node(mid)
            if node and hasattr(node, "role") and ("antag" in node.role.lower() or "villain" in node.role.lower()):
                return ConflictType.ANTAGONIST
        return ConflictType.COMPLEX

    def _compute_cohesion(self, members, partition):
        n = len(members)
        if n <= 1: return 1.0
        max_e = n * (n - 1)
        if max_e == 0: return 0.0
        ms = set(members); internal = 0
        for mid in members:
            for e in self._graph.edges_from(mid):
                if e.target in ms: internal += 1
        return min(1.0, internal / max_e)

    def _inter_cluster_weight(self, m1, m2, partition):
        s2 = set(m2); total = 0.0
        for nid in m1:
            for e in self._graph.edges_from(nid):
                if e.target in s2: total += e.weight
        return total

    def _compute_modularity(self, char_ids, adj, partition):
        total = sum(sum(nb.values()) for nb in adj.values()) / 2.0
        if total == 0: return 0.0
        q = 0.0
        for i in char_ids:
            ki = sum(adj.get(i, {}).values())
            for j, wij in adj.get(i, {}).items():
                if partition.get(i) == partition.get(j):
                    kj = sum(adj.get(j, {}).values())
                    q += wij - self._resolution * ki * kj / (2 * total)
        return q / (2 * total) if total > 0 else 0.0
