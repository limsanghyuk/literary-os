"""
V321-A: RelationGraph Layer
StoryNode / StoryEdge / RelationGraphStore

설계 원칙 (3인 합의):
  - NetworkX DiGraph 채택 (AETHER 제안 수용)
  - numpy 제거 — pydantic JSON 직렬화 가능
  - KnowledgeStateTracker와 역할 분담:
      KST: 인물 지식 상태 + 압력 연산
      RGS: 방향성 관계 그래프 + 엣지 타입 탐색
  - 14종 엣지 타입 (인과/지식/서사/문학 관계)

LLM 0회. 완전 로컬.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Iterator

try:
    import networkx as nx
    _NX_AVAILABLE = True
except ImportError:
    _NX_AVAILABLE = False


# ── 엣지 타입 14종 ─────────────────────────────────────────────────
class RelationType(str, Enum):
    # 인과/지식 관계
    KNOWS          = "knows"
    DOES_NOT_KNOW  = "does_not_know"
    SUSPECTS       = "suspects"
    MISBELIEVES    = "misbelieves"
    HIDES_FROM     = "hides_from"
    CAUSED_BY      = "caused_by"
    REVEALED_TO    = "revealed_to"
    # 서사/문학 관계
    FORESHADOWS    = "foreshadows"
    RESOLVES       = "resolves"
    ECHOES         = "echoes"
    CONTRADICTS    = "contradicts"
    SYMBOLIZES     = "symbolizes"
    MIRRORS        = "mirrors"
    TRANSFORMS_INTO= "transforms_into"


# ── 노드 타입 ──────────────────────────────────────────────────────
class NodeType(str, Enum):
    CHARACTER      = "CHARACTER"
    FACT_SECRET    = "FACT_SECRET"
    FACT_PUBLIC    = "FACT_PUBLIC"
    EVENT_PAST     = "EVENT_PAST"
    OBJECT_RESIDUE = "OBJECT_RESIDUE"
    WORLD_RULE     = "WORLD_RULE"
    FORESHADOWING  = "FORESHADOWING"
    THEME          = "THEME"


# ── 데이터 클래스 ───────────────────────────────────────────────────
@dataclass
class StoryNode:
    """
    지식 그래프의 노드.
    numpy 없이 JSON 직렬화 가능.
    """
    node_id: str
    node_type: str            # NodeType 값 또는 자유 문자열
    content: str
    origin_episode: int = 1
    reveal_episode: int | None = None   # 공개 허용 에피소드
    is_resolved: bool = False           # 복선 회수 여부
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "StoryNode":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class StoryEdge:
    """
    방향성 엣지: source → target.
    [이준서] --(hides_from)--> [김지수] 처럼
    시점에 따라 다르게 작동하는 알고리즘 스위치.
    """
    source_id: str
    target_id: str
    relation_type: str        # RelationType 값 또는 자유 문자열
    strength: float = 1.0     # 관계 강도 [0.1, 2.0]
    episode_created: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "StoryEdge":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ── RelationGraphStore ────────────────────────────────────────────
class LocalRelationGraphStore:
    """
    NetworkX DiGraph 기반 방향성 지식 그래프.

    역할:
      - 노드(StoryNode)와 방향성 엣지(StoryEdge) 저장
      - 인물 시점 기반 관련 노드 필터링
      - 엣지 타입별 탐색
      - JSON 직렬화/역직렬화

    KnowledgeStateTracker와의 분업:
      KST → 인물 지식 상태값 + 압력 수치 연산
      RGS → 방향성 관계 구조 + 그래프 탐색
    """

    def __init__(self, store_path: str | Path | None = None):
        if not _NX_AVAILABLE:
            raise ImportError("networkx가 필요합니다: pip install networkx")
        self._graph: nx.DiGraph = nx.DiGraph()
        self._nodes: dict[str, StoryNode] = {}
        self.store_path = Path(store_path) if store_path else None
        if self.store_path and self.store_path.exists():
            self._load()

    # ── 노드 관리 ──────────────────────────────────────────────────
    def add_node(self, node: StoryNode) -> None:
        self._nodes[node.node_id] = node
        self._graph.add_node(node.node_id, **node.to_dict())
        if self.store_path:
            self._save()

    def get_node(self, node_id: str) -> StoryNode | None:
        return self._nodes.get(node_id)

    def all_nodes(self) -> list[StoryNode]:
        return list(self._nodes.values())

    # ── 엣지 관리 ──────────────────────────────────────────────────
    def add_edge(self, edge: StoryEdge) -> None:
        self._graph.add_edge(
            edge.source_id, edge.target_id,
            relation=edge.relation_type,
            strength=edge.strength,
            episode_created=edge.episode_created,
        )
        if self.store_path:
            self._save()

    def get_edge_relation(self, source_id: str, target_id: str) -> str | None:
        """A→B 방향 엣지의 relation_type 반환. 없으면 None."""
        if self._graph.has_edge(source_id, target_id):
            return self._graph[source_id][target_id].get("relation")
        return None

    def get_edge_strength(self, source_id: str, target_id: str) -> float:
        if self._graph.has_edge(source_id, target_id):
            return float(self._graph[source_id][target_id].get("strength", 1.0))
        return 1.0

    # ── 핵심: 인물 시점 필터링 ─────────────────────────────────────
    def get_knowledge_status(
        self, character_id: str, target_node_id: str
    ) -> str:
        """
        인물(character_id)이 특정 노드(target_node_id)에 대해
        어떤 관계(엣지)를 갖고 있는지 반환.

        반환값:
          "knows" / "does_not_know" / "suspects" / "misbelieves" /
          "hides_from" / "UNAWARE" (엣지 없음)
        """
        rel = self.get_edge_relation(character_id, target_node_id)
        if rel is None:
            return "UNAWARE"
        return rel

    def nodes_by_type(self, node_type: str) -> list[StoryNode]:
        return [n for n in self._nodes.values() if n.node_type == node_type]

    def unresolved_foreshadowings(self) -> list[StoryNode]:
        """미회수 복선 목록."""
        return [n for n in self._nodes.values()
                if n.node_type in (NodeType.FORESHADOWING, NodeType.OBJECT_RESIDUE)
                and not n.is_resolved]

    def nodes_hidden_from(self, character_id: str) -> list[StoryNode]:
        """character_id에게 숨겨진 노드 목록 (hides_from 엣지 기준)."""
        result = []
        for src, tgt, data in self._graph.edges(data=True):
            if tgt == character_id and data.get("relation") == RelationType.HIDES_FROM:
                node = self._nodes.get(src)
                if node:
                    result.append(node)
        return result

    def neighbors_by_relation(
        self, node_id: str, relation: str
    ) -> Iterator[StoryNode]:
        """특정 relation 타입의 이웃 노드 순회."""
        for src, tgt, data in self._graph.edges(data=True):
            if src == node_id and data.get("relation") == relation:
                n = self._nodes.get(tgt)
                if n:
                    yield n

    def stats(self) -> dict[str, int]:
        return {
            "nodes": len(self._nodes),
            "edges": self._graph.number_of_edges(),
            "unresolved_foreshadowings": len(self.unresolved_foreshadowings()),
        }

    # ── 직렬화 ─────────────────────────────────────────────────────
    def _save(self) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "nodes": {nid: n.to_dict() for nid, n in self._nodes.items()},
            "edges": [
                {"source": s, "target": t, **d}
                for s, t, d in self._graph.edges(data=True)
            ],
        }
        self.store_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def _load(self) -> None:
        try:
            data = json.loads(self.store_path.read_text())
            for nid, nd in data.get("nodes", {}).items():
                self._nodes[nid] = StoryNode.from_dict(nd)
                self._graph.add_node(nid, **nd)
            for ed in data.get("edges", []):
                s, t = ed.pop("source"), ed.pop("target")
                self._graph.add_edge(s, t, **ed)
        except Exception:
            pass

    def to_json(self) -> str:
        data = {
            "nodes": {nid: n.to_dict() for nid, n in self._nodes.items()},
            "edges": [
                {"source": s, "target": t, **d}
                for s, t, d in self._graph.edges(data=True)
            ],
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "RelationGraphStore":
        store = cls()
        data = json.loads(json_str)
        for nd in data.get("nodes", {}).values():
            store.add_node(StoryNode.from_dict(nd))
        for ed in data.get("edges", []):
            s, t = ed.pop("source"), ed.pop("target")
            store._graph.add_edge(s, t, **ed)
        return store

RelationGraphStore = LocalRelationGraphStore  # V579 backward-compat alias
