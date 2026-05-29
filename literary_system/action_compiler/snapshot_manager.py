"""
V323 — SnapshotManager
Layer 1.5 / Layer 2: RelationGraphStore JSON 스냅샷 & 롤백 히스토리

설계 원칙 (CSA/CSC/CPE 합의):
  - Gemini StateEngine.history 재해석.
  - model_copy(deep=True) 방식 대신 JSON 직렬화 스냅샷 사용.
  - 메모리(스택) + 디스크(선택) 이중 퍼시스턴스.
  - RelationGraphStore.to_json() / from_json() API 완전 활용.
  - push_snapshot() / pop_snapshot() / peek_snapshot() 인터페이스.
  - LearnedCoefficientStore(Phase 2)와 연동: 계수 갱신 롤백도 지원.

LLM 0회. 완전 로컬.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Snapshot:
    """단일 스냅샷 레코드."""
    snapshot_id: str
    timestamp: float
    label: str                           # 식별 레이블 (예: "before_scene_5")
    graph_json: str                      # RelationGraphStore.to_json() 결과
    coefficient_json: str | None = None  # LearnedCoefficientStore JSON (선택)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "label": self.label,
            "graph_json": self.graph_json,
            "coefficient_json": self.coefficient_json,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Snapshot":
        return cls(
            snapshot_id=d["snapshot_id"],
            timestamp=d["timestamp"],
            label=d["label"],
            graph_json=d["graph_json"],
            coefficient_json=d.get("coefficient_json"),
            metadata=d.get("metadata", {}),
        )


class SnapshotManager:
    """
    V323 스냅샷 관리자.

    사용 패턴:
        manager = SnapshotManager()
        manager.push_snapshot(graph, label="before_action")
        try:
            # 검증 로직...
            manager.commit()   # 성공: 스냅샷 확정
        except Exception:
            graph = manager.pop_snapshot(graph)  # 실패: 롤백

    디스크 퍼시스턴스:
        snapshot_dir 지정 시 각 스냅샷을 JSON 파일로 저장.
        세션 간 롤백 가능.
    """

    def __init__(
        self,
        snapshot_dir: str | Path | None = None,
        max_stack_size: int = 50,
    ):
        self._stack: list[Snapshot] = []
        self._max_size = max_stack_size
        self._snapshot_dir = Path(snapshot_dir) if snapshot_dir else None
        if self._snapshot_dir:
            self._snapshot_dir.mkdir(parents=True, exist_ok=True)

    # ── 핵심 API ──────────────────────────────────────────────────

    def push_snapshot(
        self,
        graph_store,                     # RelationGraphStore
        label: str = "",
        coefficient_store=None,          # LearnedCoefficientStore (Phase 2)
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        현재 그래프 상태를 스냅샷으로 저장.

        Returns:
            snapshot_id (롤백 시 참조용)
        """
        import uuid
        snap_id = str(uuid.uuid4())[:8]

        graph_json = graph_store.to_json()
        coeff_json = None
        if coefficient_store is not None:
            coeff_json = coefficient_store.to_json()

        snap = Snapshot(
            snapshot_id=snap_id,
            timestamp=time.time(),
            label=label or f"snapshot_{len(self._stack)}",
            graph_json=graph_json,
            coefficient_json=coeff_json,
            metadata=metadata or {},
        )

        # 스택 크기 제한
        if len(self._stack) >= self._max_size:
            self._stack.pop(0)

        self._stack.append(snap)

        # 디스크 저장
        if self._snapshot_dir:
            self._save_to_disk(snap)

        return snap_id

    def pop_snapshot(
        self,
        graph_store,                     # RelationGraphStore
        coefficient_store=None,          # LearnedCoefficientStore (선택)
    ):
        """
        가장 최근 스냅샷으로 롤백.

        Returns:
            (graph_store, coefficient_store | None)
            복원된 객체 튜플.
        """
        if not self._stack:
            raise RuntimeError("SnapshotManager: 롤백할 스냅샷이 없습니다.")

        snap = self._stack.pop()

        # 그래프 복원
        from literary_system.relation_graph.relation_graph_store import RelationGraphStore
        restored_graph = RelationGraphStore.from_json(snap.graph_json)
        # 기존 store에 상태 복사
        graph_store._graph = restored_graph._graph
        graph_store._nodes = restored_graph._nodes

        # 계수 복원 (있으면)
        restored_coeff = None
        if coefficient_store is not None and snap.coefficient_json:
            coefficient_store.from_json_inplace(snap.coefficient_json)
            restored_coeff = coefficient_store

        return graph_store, restored_coeff

    def peek_snapshot(self) -> Snapshot | None:
        """스택 최상위 스냅샷 확인 (pop하지 않음)."""
        return self._stack[-1] if self._stack else None

    def commit(self) -> None:
        """
        현재 스냅샷 확정 — 스택 유지 (다음 push를 위해).
        명시적 커밋이 없어도 push가 쌓이면 자동으로 오래된 것부터 삭제됨.
        """
        pass  # 현재는 no-op. 향후 WAL 패턴 지원 시 활용.

    def clear(self) -> None:
        """스냅샷 스택 초기화."""
        self._stack.clear()

    # ── 상태 조회 ──────────────────────────────────────────────────

    @property
    def depth(self) -> int:
        return len(self._stack)

    @property
    def is_empty(self) -> bool:
        return len(self._stack) == 0

    def list_snapshots(self) -> list[dict[str, Any]]:
        return [
            {
                "snapshot_id": s.snapshot_id,
                "label": s.label,
                "timestamp": s.timestamp,
                "has_coefficient": s.coefficient_json is not None,
            }
            for s in self._stack
        ]

    def stats(self) -> dict[str, Any]:
        return {
            "stack_depth": self.depth,
            "max_stack_size": self._max_size,
            "has_disk_persistence": self._snapshot_dir is not None,
            "disk_dir": str(self._snapshot_dir) if self._snapshot_dir else None,
        }

    # ── 디스크 I/O ────────────────────────────────────────────────

    def _save_to_disk(self, snap: Snapshot) -> None:
        path = self._snapshot_dir / f"snapshot_{snap.snapshot_id}.json"
        path.write_text(json.dumps(snap.to_dict(), ensure_ascii=False), encoding="utf-8")

    def load_from_disk(self, snapshot_id: str) -> Snapshot | None:
        """디스크에서 특정 스냅샷 로드."""
        if not self._snapshot_dir:
            return None
        path = self._snapshot_dir / f"snapshot_{snapshot_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return Snapshot.from_dict(data)
