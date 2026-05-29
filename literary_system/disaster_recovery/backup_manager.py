"""DR Backup Manager (V741, D-M-11, ADR-202).

Handles snapshot creation, interval enforcement, and RPO validation.

RPO (Recovery Point Objective) invariant:
    backup_interval_seconds ≤ 3600  (1 hour)

ADR-202: Disaster Recovery Backup Strategy
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class BackupStatus(str, Enum):
    """Lifecycle state of a backup record."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class BackupRecord:
    """Metadata for a single backup snapshot."""

    backup_id: str
    tenant_id: str
    status: BackupStatus
    created_at: float          # Unix timestamp (seconds)
    completed_at: Optional[float]
    size_bytes: int
    checksum: Optional[str]
    path: Optional[str]
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "backup_id": self.backup_id,
            "tenant_id": self.tenant_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "size_bytes": self.size_bytes,
            "checksum": self.checksum,
            "path": self.path,
            "error": self.error,
        }


class DRBackupManager:
    """Manages disaster-recovery backups with RPO ≤ 1h guarantee.

    Args:
        backup_interval_seconds: How often backups are taken (must be ≤ 3600).
        max_retained_backups: Maximum number of backups retained per tenant.
        storage_root: Base path for storing backup files.

    Raises:
        ValueError: If backup_interval_seconds > 3600 (RPO violation).
    """

    _MAX_RPO_SECONDS: int = 3600  # 1 hour

    def __init__(
        self,
        backup_interval_seconds: int = 3600,
        max_retained_backups: int = 24,
        storage_root: Optional[str] = None,
    ) -> None:
        self._validate_rpo(backup_interval_seconds)
        self._interval = backup_interval_seconds
        self._max_retained = max_retained_backups
        self._storage_root = Path(storage_root) if storage_root else Path("/tmp/dr_backups")
        self._records: Dict[str, List[BackupRecord]] = {}   # tenant_id → records

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_backup(
        self, tenant_id: str, data: bytes, path_hint: Optional[str] = None
    ) -> BackupRecord:
        """Create a new backup snapshot for the given tenant.

        Args:
            tenant_id: Identifier of the tenant being backed up.
            data: Raw bytes to back up.
            path_hint: Optional storage path hint.

        Returns:
            A BackupRecord with status SUCCESS or FAILED.
        """
        backup_id = str(uuid.uuid4())
        now = time.time()
        record = BackupRecord(
            backup_id=backup_id,
            tenant_id=tenant_id,
            status=BackupStatus.IN_PROGRESS,
            created_at=now,
            completed_at=None,
            size_bytes=len(data),
            checksum=None,
            path=path_hint or f"{tenant_id}/{backup_id}.bak",
        )

        try:
            checksum = hashlib.sha256(data).hexdigest()
            record.checksum = checksum
            record.status = BackupStatus.SUCCESS
            record.completed_at = time.time()
        except Exception as exc:
            record.status = BackupStatus.FAILED
            record.error = str(exc)
            record.completed_at = time.time()

        # Register and prune
        if tenant_id not in self._records:
            self._records[tenant_id] = []
        self._records[tenant_id].append(record)
        self._prune(tenant_id)
        return record

    def list_backups(self, tenant_id: str) -> List[BackupRecord]:
        """Return all backup records for a tenant (most recent first)."""
        records = self._records.get(tenant_id, [])
        return sorted(records, key=lambda r: r.created_at, reverse=True)

    def latest_backup(self, tenant_id: str) -> Optional[BackupRecord]:
        """Return the most recent successful backup for a tenant."""
        for r in self.list_backups(tenant_id):
            if r.status == BackupStatus.SUCCESS:
                return r
        return None

    def rpo_compliant(self, tenant_id: str, reference_time: Optional[float] = None) -> bool:
        """Check if the latest backup is within the RPO window.

        Args:
            tenant_id: Tenant to check.
            reference_time: Timestamp to compare against (defaults to now).

        Returns:
            True if the most recent successful backup is ≤ backup_interval_seconds old.
        """
        latest = self.latest_backup(tenant_id)
        if latest is None:
            return False
        t = reference_time if reference_time is not None else time.time()
        age = t - latest.created_at
        return age <= self._interval

    def backup_count(self, tenant_id: str) -> int:
        """Return total backup count for a tenant."""
        return len(self._records.get(tenant_id, []))

    @property
    def interval(self) -> int:
        return self._interval

    @property
    def max_retained(self) -> int:
        return self._max_retained

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_rpo(self, backup_interval_seconds: int) -> None:
        """Enforce RPO invariant: interval must be ≤ MAX_RPO_SECONDS."""
        if backup_interval_seconds <= 0:
            raise ValueError(
                f"backup_interval_seconds must be > 0, got {backup_interval_seconds}"
            )
        if backup_interval_seconds > self._MAX_RPO_SECONDS:
            raise ValueError(
                f"RPO violation: backup_interval_seconds={backup_interval_seconds} "
                f"exceeds MAX_RPO_SECONDS={self._MAX_RPO_SECONDS}. "
                "Reduce interval to ≤ 3600 to comply with the 1-hour RPO requirement."
            )

    def _prune(self, tenant_id: str) -> None:
        """Remove oldest backups beyond max_retained limit."""
        records = self._records[tenant_id]
        if len(records) > self._max_retained:
            # Sort by created_at ascending, drop the oldest
            records.sort(key=lambda r: r.created_at)
            self._records[tenant_id] = records[-self._max_retained :]
