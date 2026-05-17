"""V360: NKGSearchEngine — BM25 + LightVector RRF."""
from __future__ import annotations
import hashlib, math, re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from literary_system.nkg.schema import NKGNodeType, NKGNode
from literary_system.nkg.graph_store import NKGGraphStore

@dataclass
class SearchResult:
    node_id:    str; label: str; node_type: str
    score:      float; metadata: Dict[str, Any] = field(default_factory=dict)

def _tokenize(text: str) -> List[str]:
    text = text.lower()
    tokens = re.findall(r"[\w가-힣]+", text)
    return [t for t in tokens if len(t) > 1]

class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1; self.b = b
        self._docs: Dict[str, List[str]] = {}
        self._df: Dict[str, int] = defaultdict(int)
        self._avgdl: float = 0.0; self._N: int = 0

    def add(self, doc_id: str, text: str) -> None:
        tokens = _tokenize(text)
        self._docs[doc_id] = tokens
        for t in set(tokens): self._df[t] += 1
        self._N = len(self._docs)
        self._avgdl = sum(len(d) for d in self._docs.values()) / max(self._N, 1)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        qtokens = _tokenize(query)
        scores: Dict[str, float] = defaultdict(float)
        for t in qtokens:
            if t not in self._df: continue
            idf = math.log((self._N - self._df[t] + 0.5) / (self._df[t] + 0.5) + 1)
            for doc_id, tokens in self._docs.items():
                tf = tokens.count(t)
                dl = len(tokens)
                denom = tf + self.k1 * (1 - self.b + self.b * dl / max(self._avgdl, 1))
                scores[doc_id] += idf * tf * (self.k1 + 1) / denom
        return sorted(scores.items(), key=lambda x: -x[1])[:top_k]

class LightVectorIndex:
    def __init__(self, dim: int = 64) -> None:
        self._dim = dim; self._vecs: Dict[str, List[float]] = {}

    def _embed(self, text: str) -> List[float]:
        tokens = _tokenize(text)
        vec = [0.0] * self._dim
        for t in tokens:
            h = int(hashlib.md5(t.encode()).hexdigest(), 16)
            for i in range(4):
                idx = (h >> (i * 8)) % self._dim
                vec[idx] += 1.0
        norm = math.sqrt(sum(v*v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def add(self, doc_id: str, text: str) -> None:
        self._vecs[doc_id] = self._embed(text)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        qv = self._embed(query)
        sims = []
        for doc_id, vec in self._vecs.items():
            sim = sum(a*b for a, b in zip(qv, vec))
            sims.append((doc_id, sim))
        return sorted(sims, key=lambda x: -x[1])[:top_k]

class NKGSearchEngine:
    RRF_K = 60

    def __init__(self, graph: NKGGraphStore) -> None:
        self._g = graph
        self._bm25 = BM25Index(k1=1.5, b=0.75)
        self._vec  = LightVectorIndex(dim=64)
        self._built = False

    def build_index(self) -> int:
        count = 0
        for node in self._g.all_nodes():
            text = f"{node.label} {node.node_type.value}"
            self._bm25.add(node.node_id, text)
            self._vec.add(node.node_id, text)
            count += 1
        self._built = True; return count

    def search(self, query: str, node_types: Optional[List[NKGNodeType]] = None,
               top_k: int = 10) -> List[SearchResult]:
        if not self._built: self.build_index()
        bm25_res = self._bm25.search(query, top_k * 2)
        vec_res  = self._vec.search(query, top_k * 2)
        fused    = self._rrf_fuse(bm25_res, vec_res, top_k * 2)
        results  = []
        for nid, score in fused:
            node = self._g.get_node(nid)
            if node is None: continue
            if node_types and node.node_type not in node_types: continue
            results.append(SearchResult(node_id=nid, label=node.label,
                                        node_type=node.node_type.value, score=score))
            if len(results) >= top_k: break
        return results

    def search_scenes(self, query: str, top_k: int = 10) -> List[SearchResult]:
        return self.search(query, [NKGNodeType.SCENE], top_k)

    def search_characters(self, query: str, top_k: int = 10) -> List[SearchResult]:
        return self.search(query, [NKGNodeType.CHARACTER], top_k)

    def search_clusters(self, query: str, top_k: int = 10) -> List[SearchResult]:
        return self.search(query, [NKGNodeType.CONFLICT_CLUSTER], top_k)

    def search_processes(self, query: str, top_k: int = 10) -> List[SearchResult]:
        return self.search(query, [NKGNodeType.NARRATIVE_PROCESS], top_k)

    def search_foreshadow(self, payoff_scene_id: str, top_k: int = 10) -> List[SearchResult]:
        return self.search(payoff_scene_id, [NKGNodeType.FORESHADOW], top_k)

    def _rrf_fuse(self, bm25: List, vec: List, top_k: int) -> List[Tuple[str, float]]:
        scores: Dict[str, float] = defaultdict(float)
        for rank, (doc_id, _) in enumerate(bm25):
            scores[doc_id] += 1.0 / (self.RRF_K + rank + 1)
        for rank, (doc_id, _) in enumerate(vec):
            scores[doc_id] += 1.0 / (self.RRF_K + rank + 1)
        return sorted(scores.items(), key=lambda x: -x[1])[:top_k]
