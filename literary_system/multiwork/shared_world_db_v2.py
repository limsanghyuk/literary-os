"""
V607 SharedWorldDB v2.0 — 스냅샷 + 충돌 감지 + 일관성 점수

V564 SharedWorldDB v1 확장:
  - WorldSnapshot      : 불변 월드 상태 스냅샷 (checkpoint / restore)
  - LocationConflict   : 동일 위치 동시 수정 충돌 기록
  - consistency_score  : 타임라인 이벤트 밀도 기반 일관성 0.0~1.0
  - export / import    : 완전 직렬화 JSON

LLM-0: 외부 LLM 호출 없음.
ADR-067
"""

from __future__ import annotations

import hashlib
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .shared_world_db import SharedWorldDB


# ────────────────────────────────────────────────────────────────
# 보조 데이터클래스
# ────────────────────────────────────────────────────────────────

@dataclass
class WorldSnapshot:
    """월드 DB 전체 불변 스냅샷."""
    snapshot_id: str
    label: str
    timestamp: float
    data: Dict[str, Any]   # export_snapshot() 결과

    def checksum(self) -> str:
        import json
        raw = json.dumps(self.data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


@dataclass
class LocationConflict:
    """위치(Location) 동시 수정 충돌 레코드."""
    conflict_id: str
    location_id: str
    project_a: str
    project_b: str
    field_conflicts: List[str]
    detected_at: float = field(default_factory=time.time)
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "location_id": self.location_id,
            "project_a": self.project_a,
            "project_b": self.project_b,
            "field_conflicts": self.field_conflicts,
            "detected_at": self.detected_at,
            "resolved": self.resolved,
        }


# ────────────────────────────────────────────────────────────────
# SharedWorldDBV2
# ────────────────────────────────────────────────────────────────

class SharedWorldDBV2(SharedWorldDB):
    """
    SharedWorldDB v2.0 — 스냅샷 + 충돌 감지 확장.

    v1 API 완전 호환 유지.
    """

    VERSION = "2.0.0"

    def __init__(self) -> None:
        super().__init__()
        # snapshot_id → WorldSnapshot
        self._world_snapshots: Dict[str, WorldSnapshot] = {}
        # 스냅샷 순서 목록
        self._snapshot_order: List[str] = []
        # conflict_id → LocationConflict
        self._location_conflicts: Dict[str, LocationConflict] = {}
        # project_id → Dict[location_id → description_hash]
        self._project_loc_hashes: Dict[str, Dict[str, str]] = {}
        self._lock_v2 = threading.Lock()

    # ── 스냅샷 관리 ──────────────────────────────────────────────

    def _world_data_snapshot(self) -> Dict[str, Any]:
        """현재 월드 상태를 dict으로 추출 (직렬화용)."""
        with self._lock:
            return {
                "locations": {
                    lid: {
                        "name": loc.name,
                        "description": loc.description,
                        "parent_id": loc.parent_id,
                        "tags": list(loc.tags),
                    }
                    for lid, loc in self._locations.items()
                },
                "factions": {
                    fid: {
                        "name": f.name,
                        "ideology": f.ideology,
                        "power_level": f.power_level,
                        "members": list(f.members),
                    }
                    for fid, f in self._factions.items()
                },
                "timeline": [
                    {
                        "event_id": ev.event_id,
                        "title": ev.title,
                        "timestamp": ev.timestamp,
                        "description": ev.description,
                        "affected_locations": list(ev.affected_locations),
                    }
                    for ev in self._timeline.values()
                ],
            }

    def checkpoint(self, label: str = "") -> str:
        """
        현재 월드 상태를 스냅샷으로 저장.

        Returns:
            snapshot_id (str)
        """
        ts = time.time()
        raw_id = f"{label}:{ts}"
        snapshot_id = hashlib.sha256(raw_id.encode()).hexdigest()[:12]
        data = self._world_data_snapshot()

        snap = WorldSnapshot(
            snapshot_id=snapshot_id,
            label=label,
            timestamp=ts,
            data=data,
        )
        with self._lock_v2:
            self._world_snapshots[snapshot_id] = snap
            self._snapshot_order.append(snapshot_id)

        return snapshot_id

    def restore(self, snapshot_id: str) -> None:
        """
        스냅샷에서 월드 상태 복원 (위치·팩션·타임라인 덮어쓰기).

        Raises:
            KeyError: snapshot_id 미존재 시
        """
        with self._lock_v2:
            snap = self._world_snapshots.get(snapshot_id)
        if snap is None:
            raise KeyError(f"snapshot_id={snapshot_id!r} not found")

        data = snap.data
        with self._lock:
            # 위치 복원
            self._locations.clear()
            for lid, ldata in data.get("locations", {}).items():
                from .shared_world_db import Location
                self._locations[lid] = Location(
                    location_id=lid,
                    name=ldata["name"],
                    description=ldata.get("description", ""),
                    parent_id=ldata.get("parent_id"),
                    tags=set(ldata.get("tags", [])),
                )

    def list_snapshots(self) -> List[WorldSnapshot]:
        """모든 스냅샷을 시간순으로 반환."""
        with self._lock_v2:
            return [
                self._world_snapshots[sid]
                for sid in self._snapshot_order
                if sid in self._world_snapshots
            ]

    def get_snapshot(self, snapshot_id: str) -> Optional[WorldSnapshot]:
        with self._lock_v2:
            return self._world_snapshots.get(snapshot_id)

    # ── 일관성 점수 ──────────────────────────────────────────────

    def consistency_score(self) -> float:
        """
        월드 일관성 점수 0.0~1.0.

        타임라인 이벤트 밀도(간격 균등성) 기반.
        이벤트 없음 → 0.5 (중립).
        """
        with self._lock:
            events = list(self._timeline.values())

        if len(events) < 2:
            return 0.5

        # 이벤트 간격의 표준편차 역수
        timestamps = sorted(ev.timestamp for ev in events)
        gaps = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
        mean_gap = sum(gaps) / len(gaps)
        if mean_gap == 0:
            return 1.0
        variance = sum((g - mean_gap) ** 2 for g in gaps) / len(gaps)
        std = variance ** 0.5
        score = 1.0 / (1.0 + std / (mean_gap + 1e-9))
        return round(max(0.0, min(1.0, score)), 4)

    # ── 충돌 감지 ────────────────────────────────────────────────

    def _location_desc_hash(self, location_id: str) -> str:
        """현재 위치 description 의 짧은 해시."""
        with self._lock:
            loc = self._locations.get(location_id)
        if loc is None:
            return ""
        return hashlib.sha256(loc.description.encode()).hexdigest()[:8]

    def register_project_state(self, project_id: str, location_id: str) -> None:
        """프로젝트의 현재 위치 상태를 등록 (충돌 감지 기준점)."""
        with self._lock_v2:
            self._project_loc_hashes.setdefault(project_id, {})[
                location_id
            ] = self._location_desc_hash(location_id)

    def detect_location_conflicts(
        self, location_id: str, project_a: str, project_b: str
    ) -> Optional[LocationConflict]:
        """
        두 프로젝트에서 동일 위치를 서로 다르게 수정했는지 감지.

        Returns:
            LocationConflict if conflict, else None
        """
        with self._lock_v2:
            hash_a = self._project_loc_hashes.get(project_a, {}).get(location_id)
            hash_b = self._project_loc_hashes.get(project_b, {}).get(location_id)

        current_hash = self._location_desc_hash(location_id)
        changed_a = hash_a is not None and hash_a != current_hash
        changed_b = hash_b is not None and hash_b != current_hash
        bases_differ = hash_a != hash_b

        if changed_a and changed_b and bases_differ:
            conflict_id = hashlib.sha256(
                f"{location_id}:{project_a}:{project_b}:{time.time()}".encode()
            ).hexdigest()[:10]
            rec = LocationConflict(
                conflict_id=conflict_id,
                location_id=location_id,
                project_a=project_a,
                project_b=project_b,
                field_conflicts=["description"],
            )
            with self._lock_v2:
                self._location_conflicts[conflict_id] = rec
            return rec
        return None

    def resolve_conflict(self, conflict_id: str) -> bool:
        """충돌을 해결됨으로 표시."""
        with self._lock_v2:
            rec = self._location_conflicts.get(conflict_id)
            if rec is None:
                return False
            rec.resolved = True
            return True

    def list_conflicts(self, resolved: bool = False) -> List[LocationConflict]:
        with self._lock_v2:
            return [r for r in self._location_conflicts.values() if r.resolved == resolved]

    # ── 직렬화 ──────────────────────────────────────────────────

    def export_snapshot(self) -> Dict[str, Any]:
        """전체 DB 상태를 JSON 직렬화 가능 dict으로 내보내기."""
        world_data = self._world_data_snapshot()
        with self._lock_v2:
            snaps = {
                sid: {
                    "snapshot_id": s.snapshot_id,
                    "label": s.label,
                    "timestamp": s.timestamp,
                    "data": s.data,
                }
                for sid, s in self._world_snapshots.items()
            }
            conflicts = {cid: c.to_dict() for cid, c in self._location_conflicts.items()}

        return {
            "version": self.VERSION,
            "exported_at": time.time(),
            "world": world_data,
            "snapshots": snaps,
            "snapshot_order": list(self._snapshot_order),
            "conflicts": conflicts,
        }

    def import_snapshot(self, data: Dict[str, Any]) -> None:
        """export_snapshot() 결과를 DB에 로드."""
        world = data.get("world", {})
        with self._lock:
            for lid, ldata in world.get("locations", {}).items():
                from .shared_world_db import Location
                self._locations[lid] = Location(
                    location_id=lid,
                    name=ldata["name"],
                    description=ldata.get("description", ""),
                    parent_id=ldata.get("parent_id"),
                    tags=set(ldata.get("tags", [])),
                )

        with self._lock_v2:
            for sid, sdata in data.get("snapshots", {}).items():
                self._world_snapshots[sid] = WorldSnapshot(
                    snapshot_id=sdata["snapshot_id"],
                    label=sdata.get("label", ""),
                    timestamp=sdata["timestamp"],
                    data=sdata["data"],
                )
            self._snapshot_order = list(data.get("snapshot_order", []))
            for cid, cdata in data.get("conflicts", {}).items():
                rec = LocationConflict(
                    conflict_id=cdata["conflict_id"],
                    location_id=cdata["location_id"],
                    project_a=cdata["project_a"],
                    project_b=cdata["project_b"],
                    field_conflicts=cdata.get("field_conflicts", []),
                    detected_at=cdata.get("detected_at", time.time()),
                    resolved=cdata.get("resolved", False),
                )
                self._location_conflicts[cid] = rec

    # ── 상태 요약 ────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        with self._lock:
            n_locs = len(self._locations)
            n_events = len(self._timeline)
        with self._lock_v2:
            n_snaps = len(self._world_snapshots)
            n_conflicts = len(self._location_conflicts)
            n_unresolved = sum(1 for c in self._location_conflicts.values() if not c.resolved)
        return {
            "version": self.VERSION,
            "locations": n_locs,
            "timeline_events": n_events,
            "snapshots": n_snaps,
            "conflicts_total": n_conflicts,
            "conflicts_unresolved": n_unresolved,
            "consistency_score": self.consistency_score(),
        }
