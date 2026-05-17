"""
Literary OS V461 -- DRController

ADR-011 DR 정책:
  RPO 1h: Qdrant 1h snapshot + PostgreSQL WAL streaming + Redis AOF
  RTO 4h

ADR-018 SubPhase Rollback Policy:
  Tag-based revert -- 각 SP 배포에 태그를 부착하고 문제 시 이전 태그로 롤백

LLM-0: snapshot_fn / restore_fn / wal_fn 주입으로 실 인프라 호출 격리.
"""
from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# 예외
# ---------------------------------------------------------------------------

class DRSnapshotError(RuntimeError):
    """스냅샷 생성 실패."""

class DRRestoreError(RuntimeError):
    """복원 실패."""

class RollbackError(RuntimeError):
    """롤백 실패."""


# ---------------------------------------------------------------------------
# 열거형
# ---------------------------------------------------------------------------

class DRStatus(str, Enum):
    IDLE        = "IDLE"
    SNAPSHOTTING = "SNAPSHOTTING"
    RESTORING   = "RESTORING"
    RESTORED    = "RESTORED"
    FAILED      = "FAILED"


class DRComponent(str, Enum):
    QDRANT    = "QDRANT"     # 벡터 DB (1h snapshot)
    POSTGRES  = "POSTGRES"   # WAL streaming
    REDIS     = "REDIS"      # AOF


# ---------------------------------------------------------------------------
# DR 스냅샷
# ---------------------------------------------------------------------------

@dataclass
class DRSnapshot:
    """DR 스냅샷 메타데이터."""
    snapshot_id:   str
    component:     DRComponent
    tenant_id:     Optional[str]   # None = 전체 인스턴스
    taken_at:      datetime
    size_bytes:    int
    storage_path:  str
    checksum:      str

    @property
    def age_minutes(self) -> float:
        delta = datetime.now(timezone.utc) - self.taken_at
        return delta.total_seconds() / 60

    def to_dict(self) -> dict:
        return {
            "snapshot_id":  self.snapshot_id,
            "component":    self.component.value,
            "tenant_id":    self.tenant_id,
            "taken_at":     self.taken_at.isoformat(),
            "age_minutes":  round(self.age_minutes, 1),
            "size_bytes":   self.size_bytes,
            "storage_path": self.storage_path,
        }


# ---------------------------------------------------------------------------
# DR 복원 결과
# ---------------------------------------------------------------------------

@dataclass
class DRRestoreResult:
    """복원 결과."""
    restore_id:    str
    snapshot_id:   str
    component:     DRComponent
    started_at:    datetime
    completed_at:  Optional[datetime] = None
    success:       bool = False
    rto_minutes:   float = 0.0
    error_msg:     str = ""

    def to_dict(self) -> dict:
        return {
            "restore_id":   self.restore_id,
            "snapshot_id":  self.snapshot_id,
            "component":    self.component.value,
            "success":      self.success,
            "rto_minutes":  round(self.rto_minutes, 1),
            "error_msg":    self.error_msg,
        }


# ---------------------------------------------------------------------------
# ADR-018 Rollback Tag
# ---------------------------------------------------------------------------

@dataclass
class RollbackTag:
    """SubPhase 배포 태그 (ADR-018)."""
    tag_id:       str
    subphase:     str        # "SP1", "SP2", ...
    version:      str        # "V456", "V462", ...
    description:  str
    created_at:   datetime
    snapshot_ids: List[str] = field(default_factory=list)
    is_current:   bool = False

    def to_dict(self) -> dict:
        return {
            "tag_id":      self.tag_id,
            "subphase":    self.subphase,
            "version":     self.version,
            "description": self.description,
            "created_at":  self.created_at.isoformat(),
            "is_current":  self.is_current,
        }


@dataclass
class RollbackPolicy:
    """ADR-018 롤백 정책."""
    max_rollback_depth:  int   = 3       # 최대 이전 SP 수까지 롤백 허용
    require_approval:    bool  = True    # 프로덕션 롤백 시 승인 필요
    auto_rollback_on_gate_fail: bool = True  # Gate 실패 시 자동 롤백


@dataclass
class RollbackResult:
    """롤백 결과."""
    rollback_id:   str
    from_tag:      str
    to_tag:        str
    success:       bool
    started_at:    datetime
    completed_at:  Optional[datetime] = None
    message:       str = ""

    def to_dict(self) -> dict:
        return {
            "rollback_id":  self.rollback_id,
            "from_tag":     self.from_tag,
            "to_tag":       self.to_tag,
            "success":      self.success,
            "message":      self.message,
        }


# ---------------------------------------------------------------------------
# DRPolicy
# ---------------------------------------------------------------------------

@dataclass
class DRPolicy:
    """DR 정책 설정."""
    rpo_minutes:          int   = 60    # RPO 목표: 1h
    rto_minutes:          int   = 240   # RTO 목표: 4h
    snapshot_interval_min: int  = 60    # Qdrant/Redis 스냅샷 주기
    wal_enabled:          bool  = True  # PostgreSQL WAL streaming
    aof_enabled:          bool  = True  # Redis AOF
    geo_redundancy:       bool  = False # 멀티-리전 복제 (Phase 4+)


# ---------------------------------------------------------------------------
# DRController
# ---------------------------------------------------------------------------

class DRController:
    """
    Literary OS V461 DR 컨트롤러.

    책임:
      - 주기적 스냅샷 트리거 (Qdrant 1h, Redis AOF)
      - WAL 스트리밍 모니터링
      - RPO 준수 여부 검증
      - ADR-018 태그 기반 롤백 관리
      - Gate16 검증 지원

    LLM-0:
      snapshot_fn(component, tenant_id) -> {"path": str, "size_bytes": int, "checksum": str}
      restore_fn(snapshot_id, component) -> {"success": bool, "rto_minutes": float}
      wal_fn(operation) -> dict
    """

    def __init__(
        self,
        policy:       Optional[DRPolicy]       = None,
        rollback_policy: Optional[RollbackPolicy] = None,
        snapshot_fn:  Optional[Callable] = None,
        restore_fn:   Optional[Callable] = None,
        wal_fn:       Optional[Callable] = None,
    ):
        self._policy   = policy or DRPolicy()
        self._rb_policy = rollback_policy or RollbackPolicy()
        self._snap_fn  = snapshot_fn or self._default_snapshot_fn
        self._rest_fn  = restore_fn  or self._default_restore_fn
        self._wal_fn   = wal_fn      or self._default_wal_fn

        self._snapshots: Dict[str, DRSnapshot]   = {}
        self._restores:  Dict[str, DRRestoreResult] = {}
        self._tags:      List[RollbackTag]       = []
        self._rollbacks: List[RollbackResult]    = []
        self._status = DRStatus.IDLE
        self._lock = threading.Lock()

    # ── 스냅샷 ───────────────────────────────────────────────────────────────

    def take_snapshot(
        self,
        component:  DRComponent,
        tenant_id:  Optional[str] = None,
    ) -> DRSnapshot:
        """스냅샷 생성."""
        with self._lock:
            self._status = DRStatus.SNAPSHOTTING

        try:
            result = self._snap_fn(
                component=component.value,
                tenant_id=tenant_id,
            )
        except Exception as e:
            with self._lock:
                self._status = DRStatus.FAILED
            raise DRSnapshotError(f"스냅샷 실패 [{component.value}]: {e}") from e

        snap = DRSnapshot(
            snapshot_id=f"SNAP-{component.value[:3]}-{uuid.uuid4().hex[:8].upper()}",
            component=component,
            tenant_id=tenant_id,
            taken_at=datetime.now(timezone.utc),
            size_bytes=result.get("size_bytes", 0),
            storage_path=result.get("path", ""),
            checksum=result.get("checksum", ""),
        )

        with self._lock:
            self._snapshots[snap.snapshot_id] = snap
            self._status = DRStatus.IDLE

        return snap

    def take_full_snapshot(self) -> Dict[str, DRSnapshot]:
        """모든 컴포넌트 전체 스냅샷."""
        results = {}
        for comp in DRComponent:
            try:
                results[comp.value] = self.take_snapshot(comp)
            except DRSnapshotError as e:
                results[comp.value] = None
        return results

    # ── 복원 ─────────────────────────────────────────────────────────────────

    def restore(self, snapshot_id: str) -> DRRestoreResult:
        """스냅샷으로 복원."""
        with self._lock:
            if snapshot_id not in self._snapshots:
                raise DRRestoreError(f"스냅샷 없음: {snapshot_id}")
            snap = self._snapshots[snapshot_id]
            self._status = DRStatus.RESTORING

        restore_id = f"RST-{uuid.uuid4().hex[:8].upper()}"
        started = datetime.now(timezone.utc)

        try:
            result = self._rest_fn(
                snapshot_id=snapshot_id,
                component=snap.component.value,
            )
        except Exception as e:
            res = DRRestoreResult(
                restore_id=restore_id,
                snapshot_id=snapshot_id,
                component=snap.component,
                started_at=started,
                completed_at=datetime.now(timezone.utc),
                success=False,
                error_msg=str(e),
            )
            with self._lock:
                self._restores[restore_id] = res
                self._status = DRStatus.FAILED
            raise DRRestoreError(str(e)) from e

        completed = datetime.now(timezone.utc)
        rto = (completed - started).total_seconds() / 60

        res = DRRestoreResult(
            restore_id=restore_id,
            snapshot_id=snapshot_id,
            component=snap.component,
            started_at=started,
            completed_at=completed,
            success=result.get("success", False),
            rto_minutes=result.get("rto_minutes", rto),
        )

        with self._lock:
            self._restores[restore_id] = res
            self._status = DRStatus.RESTORED if res.success else DRStatus.FAILED

        return res

    # ── RPO 검증 ─────────────────────────────────────────────────────────────

    def verify_rpo(self, component: DRComponent) -> dict:
        """최신 스냅샷이 RPO 기준 내에 있는지 확인."""
        with self._lock:
            snaps = [s for s in self._snapshots.values() if s.component == component]

        if not snaps:
            return {
                "component":  component.value,
                "rpo_ok":     False,
                "reason":     "스냅샷 없음",
                "age_minutes": None,
            }

        latest = max(snaps, key=lambda s: s.taken_at)
        age    = latest.age_minutes
        rpo_ok = age <= self._policy.rpo_minutes

        return {
            "component":    component.value,
            "rpo_ok":       rpo_ok,
            "age_minutes":  round(age, 1),
            "rpo_target_m": self._policy.rpo_minutes,
            "snapshot_id":  latest.snapshot_id,
        }

    def verify_all_rpo(self) -> dict:
        """전체 컴포넌트 RPO 검증."""
        results = {c.value: self.verify_rpo(c) for c in DRComponent}
        all_ok = all(v["rpo_ok"] for v in results.values())
        return {"all_ok": all_ok, "components": results}

    # ── ADR-018 태그 기반 롤백 ────────────────────────────────────────────────

    def register_tag(
        self,
        subphase:    str,
        version:     str,
        description: str = "",
    ) -> RollbackTag:
        """SubPhase 배포 태그 등록."""
        # 전체 스냅샷 후 태그에 연결
        snaps = self.take_full_snapshot()
        snap_ids = [s.snapshot_id for s in snaps.values() if s is not None]

        tag = RollbackTag(
            tag_id=f"TAG-{subphase}-{version}-{uuid.uuid4().hex[:6].upper()}",
            subphase=subphase,
            version=version,
            description=description,
            created_at=datetime.now(timezone.utc),
            snapshot_ids=snap_ids,
            is_current=True,
        )
        with self._lock:
            # 기존 태그는 is_current=False
            for t in self._tags:
                t.is_current = False
            self._tags.append(tag)

        return tag

    def rollback_to_tag(self, tag_id: str) -> RollbackResult:
        """태그로 롤백 실행 (ADR-018)."""
        with self._lock:
            current = next((t for t in self._tags if t.is_current), None)
            target  = next((t for t in self._tags if t.tag_id == tag_id), None)

        if not target:
            raise RollbackError(f"태그 없음: {tag_id}")

        rollback_id = f"RBK-{uuid.uuid4().hex[:8].upper()}"
        started = datetime.now(timezone.utc)

        success_count = 0
        for snap_id in target.snapshot_ids:
            try:
                res = self.restore(snap_id)
                if res.success:
                    success_count += 1
            except DRRestoreError:
                pass

        overall_success = success_count == len(target.snapshot_ids) and len(target.snapshot_ids) > 0

        result = RollbackResult(
            rollback_id=rollback_id,
            from_tag=current.tag_id if current else "UNKNOWN",
            to_tag=tag_id,
            success=overall_success,
            started_at=started,
            completed_at=datetime.now(timezone.utc),
            message=f"복원 {success_count}/{len(target.snapshot_ids)} 성공",
        )

        with self._lock:
            self._rollbacks.append(result)
            if overall_success:
                for t in self._tags:
                    t.is_current = (t.tag_id == tag_id)

        return result

    # ── 조회 ─────────────────────────────────────────────────────────────────

    def list_snapshots(self, component: Optional[DRComponent] = None) -> List[DRSnapshot]:
        with self._lock:
            snaps = list(self._snapshots.values())
        if component:
            snaps = [s for s in snaps if s.component == component]
        return sorted(snaps, key=lambda s: s.taken_at)

    def list_tags(self) -> List[RollbackTag]:
        with self._lock:
            return list(self._tags)

    def get_current_tag(self) -> Optional[RollbackTag]:
        with self._lock:
            return next((t for t in self._tags if t.is_current), None)

    @property
    def status(self) -> DRStatus:
        return self._status

    def summary(self) -> dict:
        with self._lock:
            snap_count = len(self._snapshots)
            tag_count  = len(self._tags)
            rb_count   = len(self._rollbacks)
            current_tag = next((t.version for t in self._tags if t.is_current), None)
        rpo_check = self.verify_all_rpo()
        return {
            "status":         self._status.value,
            "snapshots":      snap_count,
            "tags":           tag_count,
            "rollbacks":      rb_count,
            "current_tag":    current_tag,
            "rpo_all_ok":     rpo_check["all_ok"],
            "rpo_target_min": self._policy.rpo_minutes,
        }

    # ── 기본 Mock fn ─────────────────────────────────────────────────────────

    @staticmethod
    def _default_snapshot_fn(**kwargs) -> dict:
        comp = kwargs.get("component", "UNKNOWN")
        return {
            "path":       f"s3://literary-dr/{comp}/{uuid.uuid4().hex}.snap",
            "size_bytes": 1024 * 1024 * 100,   # 100MB mock
            "checksum":   uuid.uuid4().hex,
        }

    @staticmethod
    def _default_restore_fn(**kwargs) -> dict:
        return {"success": True, "rto_minutes": 15.0}  # 15분 복원 mock

    @staticmethod
    def _default_wal_fn(**kwargs) -> dict:
        return {"status": "ok", "lag_ms": 50}
