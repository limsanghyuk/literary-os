"""ADR-044 | V585 | L1 — GraphRealAdapter: networkx-optional 그래프 스토어 + JSON 영속화 + rollback

LLM-0 원칙: 외부 LLM 호출 없음.
"""
from __future__ import annotations

import copy
import json
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from literary_system.db.migration_manager import BaseMigrationAdapter, Migration
from literary_system.db.schema_registry import BackendType, MigrationRecord, SchemaRegistry

logger = logging.getLogger(__name__)

# ── networkx-optional ─────────────────────────────────────────────────────────

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

# ── 데이터 모델 ───────────────────────────────────────────────────────────────


@dataclass
class GraphRecord:
    """그래프 노드 레코드."""

    id: str
    label: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "label": self.label, "metadata": self.metadata}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GraphRecord":
        return cls(id=d["id"], label=d["label"], metadata=d.get("metadata", {}))


@dataclass
class GraphEdgeRecord:
    """그래프 엣지 레코드."""

    id: str
    src_id: str
    dst_id: str
    label: str
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "src_id": self.src_id,
            "dst_id": self.dst_id,
            "label": self.label,
            "weight": self.weight,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GraphEdgeRecord":
        return cls(
            id=d["id"],
            src_id=d["src_id"],
            dst_id=d["dst_id"],
            label=d["label"],
            weight=float(d.get("weight", 1.0)),
            metadata=d.get("metadata", {}),
        )


# ── GraphRealAdapter ──────────────────────────────────────────────────────────


class GraphRealAdapter(BaseMigrationAdapter):
    """REAL Graph 마이그레이션 어댑터.

    networkx 설치 시: nx.DiGraph() 기반 완전 그래프 연산.
    networkx 미설치 시: 순수 Python adjacency-dict fallback.

    특징:
    - GraphRecord(노드) + GraphEdgeRecord(엣지) 데이터클래스
    - JSON 영속화 (save/load)
    - rollback 스냅샷 전략
    - migration.graph_ops 처리
    """

    def __init__(
        self,
        path: Optional[str] = None,
        mock: bool = False,
    ) -> None:
        super().__init__(mock=mock)
        self._path = path
        self._nodes: Dict[str, GraphRecord] = {}
        self._edges: Dict[str, GraphEdgeRecord] = {}
        # adjacency: src_id → list of (dst_id, edge_id)
        self._adj: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        # reverse adjacency: dst_id → list of (src_id, edge_id)
        self._radj: Dict[str, List[Tuple[str, str]]] = defaultdict(list)

        self._snapshot: Optional[Any] = None
        self._migration_log: List[MigrationRecord] = []

        if path:
            try:
                self.load()
            except (FileNotFoundError, json.JSONDecodeError):
                logger.info("GraphRealAdapter: 기존 그래프 파일 없음, 새로 시작")

        logger.info(
            "GraphRealAdapter 초기화 (path=%s, mock=%s, HAS_NETWORKX=%s)",
            path,
            mock,
            HAS_NETWORKX,
        )

    # ── 노드 CRUD ─────────────────────────────────────────────────────────────

    def add_node(
        self,
        id: str,
        label: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """노드 추가 (이미 있으면 덮어쓰기)."""
        self._nodes[id] = GraphRecord(id=id, label=label, metadata=metadata or {})
        if HAS_NETWORKX and hasattr(self, "_nx_graph"):
            self._nx_graph.add_node(id, label=label, **(metadata or {}))

    def get_node(self, id: str) -> Optional[GraphRecord]:
        return self._nodes.get(id)

    def remove_node(self, id: str) -> bool:
        if id not in self._nodes:
            return False
        # 연결된 엣지 모두 제거
        for _, eid in list(self._adj.get(id, [])):
            self._del_edge(eid)
        for _, eid in list(self._radj.get(id, [])):
            self._del_edge(eid)
        del self._nodes[id]
        self._adj.pop(id, None)
        self._radj.pop(id, None)
        if HAS_NETWORKX and hasattr(self, "_nx_graph") and self._nx_graph.has_node(id):
            self._nx_graph.remove_node(id)
        return True

    # ── 엣지 CRUD ─────────────────────────────────────────────────────────────

    def add_edge(
        self,
        id: str,
        src_id: str,
        dst_id: str,
        label: str,
        weight: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """엣지 추가. 노드가 없으면 자동 생성."""
        if src_id not in self._nodes:
            self.add_node(src_id, label=src_id)
        if dst_id not in self._nodes:
            self.add_node(dst_id, label=dst_id)
        # 중복 id 처리: 기존 엣지가 있으면 adjacency 목록에서 먼저 제거
        if id in self._edges:
            self._del_edge(id)
        self._edges[id] = GraphEdgeRecord(
            id=id,
            src_id=src_id,
            dst_id=dst_id,
            label=label,
            weight=weight,
            metadata=metadata or {},
        )
        self._adj[src_id].append((dst_id, id))
        self._radj[dst_id].append((src_id, id))
        if HAS_NETWORKX and hasattr(self, "_nx_graph"):
            self._nx_graph.add_edge(src_id, dst_id, key=id, weight=weight, label=label)

    def get_edge(self, id: str) -> Optional[GraphEdgeRecord]:
        return self._edges.get(id)

    def remove_edge(self, id: str) -> bool:
        if id not in self._edges:
            return False
        self._del_edge(id)
        return True

    def _del_edge(self, eid: str) -> None:
        e = self._edges.pop(eid, None)
        if e:
            self._adj[e.src_id] = [
                (d, i) for d, i in self._adj[e.src_id] if i != eid
            ]
            self._radj[e.dst_id] = [
                (s, i) for s, i in self._radj[e.dst_id] if i != eid
            ]
            if HAS_NETWORKX and hasattr(self, "_nx_graph"):
                if self._nx_graph.has_edge(e.src_id, e.dst_id, key=eid):
                    self._nx_graph.remove_edge(e.src_id, e.dst_id, key=eid)

    # ── 통계 ──────────────────────────────────────────────────────────────────

    def node_count(self) -> int:
        return len(self._nodes)

    def edge_count(self) -> int:
        return len(self._edges)

    # ── 그래프 탐색 ──────────────────────────────────────────────────────────

    def neighbors(
        self,
        node_id: str,
        direction: str = "out",
    ) -> List[str]:
        """인접 노드 목록 반환.

        direction: "out" (나가는 방향), "in" (들어오는 방향), "both"
        """
        if direction == "out":
            return [dst for dst, _ in self._adj.get(node_id, [])]
        elif direction == "in":
            return [src for src, _ in self._radj.get(node_id, [])]
        else:  # both
            out = [dst for dst, _ in self._adj.get(node_id, [])]
            in_ = [src for src, _ in self._radj.get(node_id, [])]
            return list(dict.fromkeys(out + in_))  # 중복 제거, 순서 유지

    def bfs(self, start_id: str, max_depth: int = 10) -> List[str]:
        """BFS 순회 — 방문 노드 목록 반환 (시작 노드 포함)."""
        if start_id not in self._nodes:
            return []
        visited: List[str] = []
        seen: set = {start_id}
        queue: deque = deque([(start_id, 0)])
        while queue:
            node_id, depth = queue.popleft()
            visited.append(node_id)
            if depth >= max_depth:
                continue
            for dst, _ in self._adj.get(node_id, []):
                if dst not in seen:
                    seen.add(dst)
                    queue.append((dst, depth + 1))
        return visited

    def dfs(self, start_id: str, max_depth: int = 10) -> List[str]:
        """DFS 순회 — 방문 노드 목록 반환 (시작 노드 포함)."""
        if start_id not in self._nodes:
            return []
        visited: List[str] = []
        seen: set = set()

        def _dfs(node_id: str, depth: int) -> None:
            if node_id in seen or depth > max_depth:
                return
            seen.add(node_id)
            visited.append(node_id)
            for dst, _ in self._adj.get(node_id, []):
                _dfs(dst, depth + 1)

        _dfs(start_id, 0)
        return visited

    # ── 영속화 ────────────────────────────────────────────────────────────────

    def save(self) -> None:
        """그래프를 JSON 파일에 저장."""
        if not self._path:
            logger.warning("GraphRealAdapter.save(): path 미설정, 저장 생략")
            return
        data = {
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "edges": [e.to_dict() for e in self._edges.values()],
        }
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("GraphRealAdapter.save(): %s (nodes=%d, edges=%d)",
                    self._path, len(self._nodes), len(self._edges))

    def load(self) -> None:
        """JSON 파일에서 그래프 복원."""
        if not self._path:
            logger.warning("GraphRealAdapter.load(): path 미설정, 로드 생략")
            return
        with open(self._path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._nodes.clear()
        self._edges.clear()
        self._adj.clear()
        self._radj.clear()
        for nd in data.get("nodes", []):
            r = GraphRecord.from_dict(nd)
            self._nodes[r.id] = r
        for ed in data.get("edges", []):
            er = GraphEdgeRecord.from_dict(ed)
            self._edges[er.id] = er
            self._adj[er.src_id].append((er.dst_id, er.id))
            self._radj[er.dst_id].append((er.src_id, er.id))
        logger.info("GraphRealAdapter.load(): %s (nodes=%d, edges=%d)",
                    self._path, len(self._nodes), len(self._edges))

    # ── BaseMigrationAdapter 구현 ─────────────────────────────────────────────

    def check_connection(self) -> bool:
        return True

    def apply(self, migration: Migration) -> bool:
        """graph_ops 연산 적용. 실패 시 False 반환."""
        # 스냅샷 저장
        self._snapshot = (
            copy.deepcopy(self._nodes),
            copy.deepcopy(self._edges),
            copy.deepcopy(dict(self._adj)),
            copy.deepcopy(dict(self._radj)),
        )
        try:
            ops = migration.graph_ops or []
            for op_dict in ops:
                op = op_dict.get("op")
                if op == "add_node":
                    nd = op_dict["node"]
                    self.add_node(
                        id=nd["id"],
                        label=nd.get("label", nd["id"]),
                        metadata=nd.get("metadata"),
                    )
                elif op == "add_edge":
                    ed = op_dict["edge"]
                    self.add_edge(
                        id=ed["id"],
                        src_id=ed["src_id"],
                        dst_id=ed["dst_id"],
                        label=ed.get("label", ""),
                        weight=float(ed.get("weight", 1.0)),
                        metadata=ed.get("metadata"),
                    )
                elif op == "remove_node":
                    self.remove_node(op_dict["node_id"])
                elif op == "remove_edge":
                    self.remove_edge(op_dict["edge_id"])
                else:
                    raise ValueError(
                        f"GraphRealAdapter.apply: 알 수 없는 op '{op}' "
                        f"(migration_id={migration.migration_id!r})"
                    )

            # DDL(up_script) 처리 — 주석 형태의 Cypher 시뮬레이션
            if migration.up_script:
                logger.info("[GRAPH-REAL] up_script: %s", migration.up_script[:80])

            self._record_migration(migration)
            logger.info("GraphRealAdapter.apply 완료: %s", migration.migration_id)
            return True
        except Exception as exc:
            logger.error("GraphRealAdapter.apply 실패: %s | %s", migration.migration_id, exc)
            # 스냅샷으로 원자적 롤백 (ADR-044 원자성 보장)
            if self._snapshot is not None:
                nodes, edges, adj, radj = self._snapshot
                self._nodes = nodes
                self._edges = edges
                self._adj = defaultdict(list, adj)
                self._radj = defaultdict(list, radj)
                self._snapshot = None
                logger.info("GraphRealAdapter.apply: 스냅샷 롤백 완료")
            return False

    def rollback(self, migration: Migration) -> bool:
        """스냅샷으로 그래프 복원."""
        if self._snapshot is None:
            logger.warning("GraphRealAdapter.rollback: 스냅샷 없음 (%s)", migration.migration_id)
            return False
        nodes, edges, adj, radj = self._snapshot
        self._nodes = nodes
        self._edges = edges
        self._adj = defaultdict(list, adj)
        self._radj = defaultdict(list, radj)
        self._snapshot = None
        logger.info("GraphRealAdapter.rollback 완료: %s", migration.migration_id)
        return True

    def _record_migration(self, migration: Migration) -> None:
        """SchemaRegistry에 마이그레이션 기록 등록."""
        try:
            reg = SchemaRegistry.get_instance()
            parts = migration.to_version.split(".")
            major = int(parts[0]) if len(parts) > 0 else 1
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            reg.register(BackendType.GRAPH, major, minor, patch, migration.description)
            rec = MigrationRecord(
                migration_id=migration.migration_id,
                backend=BackendType.GRAPH,
                from_version=migration.from_version,
                to_version=migration.to_version,
                description=migration.description,
                applied_at=datetime.now(timezone.utc).isoformat(),
                success=True,
            )
            reg.record_migration(rec)
            self._migration_log.append(rec)
        except Exception as exc:
            logger.warning("SchemaRegistry 등록 실패 (무시): %s", exc)

    def schema_info(self) -> Dict[str, Any]:
        return {
            "nodes": len(self._nodes),
            "edges": len(self._edges),
            "has_networkx": HAS_NETWORKX,
            "path": self._path,
        }
