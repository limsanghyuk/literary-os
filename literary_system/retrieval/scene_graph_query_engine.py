"""V328 Task13: SceneGraphQueryEngine — GraphRAG 기반 씬 컨텍스트 검색 (단절 D)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class GraphDoc:
    node_id:   str   = ""
    node_type: str   = ""
    text:      str   = ""
    relevance: float = 0.0

class SceneGraphQueryEngine:
    def __init__(self, relation_store=None):
        self._store = relation_store

    def query(self, characters: list[str], scene_goal: str,
              tension: float = 0.5, top_k: int = 5) -> list[GraphDoc]:
        if self._store is None:
            return []
        docs: list[GraphDoc] = []
        try:
            for char in characters[:3]:
                node = getattr(self._store, "get_node", None)
                if node:
                    n = node(char)
                    if n:
                        docs.append(GraphDoc(node_id=char, node_type="character",
                                             text=str(n), relevance=0.8))
            edges_fn = getattr(self._store, "get_edges", None)
            if edges_fn and len(characters) >= 2:
                edges = edges_fn(characters[0], characters[1])
                for e in (edges or [])[:2]:
                    docs.append(GraphDoc(node_id=str(e), node_type="edge",
                                         text=str(e), relevance=0.7))
        except Exception:
            pass
        return docs[:top_k]

    @staticmethod
    def to_retrieved_docs(docs: list[GraphDoc]) -> list[str]:
        return [f"[GraphRAG:{d.node_type}] {d.text}" for d in docs]
