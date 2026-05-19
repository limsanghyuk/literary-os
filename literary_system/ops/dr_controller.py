"""
literary_system/ops/dr_controller.py
V477 — OpsDRController (Disaster Recovery, RPO 1h)

설계 (Phase 3 v2 ADR-018):
  - RPO 1h: 스냅샷 + WAL 스트리밍 mock
  - RTO 4h: 복원 시뮬레이션
  - 스냅샷 주기: 60분
  - WAL 스트리밍: 실시간 (mock)

LLM-0 준수: snapshot_fn / restore_fn / wal_fn 주입 가능
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

# ── 열거형 ───────────────────────────────────────────────────

class OpsDRStatus(str, Enum):
    IDLE       = "idle"
    SNAPSHOTTING = "snapshotting"
    STREAMING  = "streaming"
    RESTORING  = "restoring"
    FAILED     = "failed"


class DRTestResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"


# ── 데이터 모델 ──────────────────────────────────────────────

@dataclass
class OpsDRSnapshot:
    snapshot_id: str
    timestamp:   float
    size_mb:     float
    metadata:    Dict[str, Any] = field(default_factory=dict)


@dataclass
class WALEntry:
    entry_id:    str
    timestamp:   float
    operation:   str
    data:        Dict[str, Any] = field(default_factory=dict)


@dataclass
class RestoreReport:
    restore_id:      str
    snapshot_id:     str
    started_at:      float
    completed_at:    float
    rpo_actual_s:    float
    rto_actual_s:    float
    rpo_target_s:    float = 3600.0   # 1h
    rto_target_s:    float = 14400.0  # 4h
    wal_entries_replayed: int = 0
    result:          DRTestResult = DRTestResult.PASS

    @property
    def rpo_ok(self) -> bool:
        return self.rpo_actual_s <= self.rpo_target_s

    @property
    def rto_ok(self) -> bool:
        return self.rto_actual_s <= self.rto_target_s


# ── OpsDRController ─────────────────────────────────────────────

class OpsDRController:
    """
    재해 복구 컨트롤러.

    snapshot_fn: () → float  (snapshot 크기 MB 반환)
    restore_fn:  (snapshot_id) → float  (복원 소요 시간 초)
    wal_fn:      () → List[WALEntry]    (WAL 항목 반환)
    clock_fn:    () → float             (테스트용 시계)
    """

    SNAPSHOT_INTERVAL_S = 3600.0  # 1h

    def __init__(
        self,
        snapshot_fn: Optional[Callable[[], float]] = None,
        restore_fn:  Optional[Callable[[str], float]] = None,
        wal_fn:      Optional[Callable[[], List[WALEntry]]] = None,
        clock_fn:    Optional[Callable[[], float]] = None,
    ) -> None:
        self._snapshot_fn = snapshot_fn or (lambda: 128.0)
        self._restore_fn  = restore_fn  or (lambda sid: 300.0)
        self._wal_fn      = wal_fn      or (lambda: [])
        self._clock       = clock_fn    or time.time

        self._snapshots: List[OpsDRSnapshot] = []
        self._wal:       List[WALEntry] = []
        self._status     = OpsDRStatus.IDLE
        self._last_snapshot_time: Optional[float] = None

    # ── 스냅샷 ──────────────────────────────────────────────

    def take_snapshot(self) -> OpsDRSnapshot:
        """스냅샷 생성."""
        self._status = OpsDRStatus.SNAPSHOTTING
        size_mb = self._snapshot_fn()
        snap = OpsDRSnapshot(
            snapshot_id=f"snap_{uuid.uuid4().hex[:8]}",
            timestamp=self._clock(),
            size_mb=float(size_mb),
        )
        self._snapshots.append(snap)
        self._last_snapshot_time = snap.timestamp
        self._status = OpsDRStatus.IDLE
        return snap

    def latest_snapshot(self) -> Optional[OpsDRSnapshot]:
        if not self._snapshots:
            return None
        return max(self._snapshots, key=lambda s: s.timestamp)

    def snapshot_count(self) -> int:
        return len(self._snapshots)

    # ── WAL 스트리밍 ─────────────────────────────────────────

    def stream_wal(self) -> List[WALEntry]:
        """WAL 항목 수집 (streaming mock)."""
        self._status = OpsDRStatus.STREAMING
        entries = self._wal_fn()
        self._wal.extend(entries)
        self._status = OpsDRStatus.IDLE
        return entries

    def append_wal(self, operation: str, data: Dict[str, Any] = None) -> WALEntry:
        """WAL에 수동 항목 추가."""
        entry = WALEntry(
            entry_id=f"wal_{uuid.uuid4().hex[:8]}",
            timestamp=self._clock(),
            operation=operation,
            data=data or {},
        )
        self._wal.append(entry)
        return entry

    def wal_entry_count(self) -> int:
        return len(self._wal)

    # ── 복원 테스트 ──────────────────────────────────────────

    def dr_restore_test(
        self,
        target_snapshot: Optional[OpsDRSnapshot] = None,
    ) -> RestoreReport:
        """
        DR 복원 테스트 시뮬레이션.
        RPO ≤ 1h, RTO ≤ 4h 검증.
        """
        snap = target_snapshot or self.latest_snapshot()
        if snap is None:
            raise RuntimeError("dr_restore_test: 스냅샷 없음 — 먼저 take_snapshot() 실행")

        self._status = OpsDRStatus.RESTORING
        restore_id   = f"rst_{uuid.uuid4().hex[:8]}"
        started_at   = self._clock()

        # RPO 계산: 현재 시각 - 스냅샷 시각 + WAL 마지막 항목까지의 보호
        now = self._clock()
        wal_since_snap = [w for w in self._wal if w.timestamp >= snap.timestamp]
        if wal_since_snap:
            last_wal_ts = max(w.timestamp for w in wal_since_snap)
            rpo_actual  = now - last_wal_ts
        else:
            rpo_actual = now - snap.timestamp

        # RTO 계산: restore_fn 호출 (시뮬레이션)
        rto_actual = self._restore_fn(snap.snapshot_id)
        completed_at = started_at + rto_actual

        self._status = OpsDRStatus.IDLE

        result_flag = (
            DRTestResult.PASS
            if rpo_actual <= 3600.0 and rto_actual <= 14400.0
            else DRTestResult.FAIL
        )

        return RestoreReport(
            restore_id=restore_id,
            snapshot_id=snap.snapshot_id,
            started_at=started_at,
            completed_at=completed_at,
            rpo_actual_s=round(rpo_actual, 2),
            rto_actual_s=round(rto_actual, 2),
            wal_entries_replayed=len(wal_since_snap),
            result=result_flag,
        )

    # ── 주기 스냅샷 확인 ─────────────────────────────────────

    def needs_snapshot(self) -> bool:
        """스냅샷 주기(1h) 초과 여부."""
        if self._last_snapshot_time is None:
            return True
        return (self._clock() - self._last_snapshot_time) >= self.SNAPSHOT_INTERVAL_S

    def status(self) -> str:
        return self._status.value





Snapshot = OpsDRSnapshot  # V579 backward-compat alias

DRController = OpsDRController  # V579 backward-compat alias

DRStatus = OpsDRStatus  # V579 backward-compat alias

DRSnapshot = OpsDRSnapshot  # V579 backward-compat alias
