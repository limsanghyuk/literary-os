"""DR Restore Manager (V741, D-M-11, ADR-202).

Handles restore operations from backup snapshots with RTO tracking.

RTO (Recovery Time Objective) is logged but not enforced as a hard limit
in this version; enforcement is part of the G91 gate checks.
"""
from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, Optional

from .backup_manager import BackupRecord, BackupStatus


class RestoreStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CHECKSUM_MISMATCH = "checksum_mismatch"


@dataclass
class RestoreRecord:
    """Metadata for a single restore operation."""

    restore_id: str
    backup_id: str
    tenant_id: str
    status: RestoreStatus
    started_at: float
    completed_at: Optional[float]
    duration_seconds: Optional[float]
    restored_bytes: int
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "restore_id": self.restore_id,
            "backup_id": self.backup_id,
            "tenant_id": self.tenant_id,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
            "restored_bytes": self.restored_bytes,
            "error": self.error,
        }


class DRRestoreManager:
    """Performs restore operations from BackupRecord snapshots.

    Args:
        max_restore_seconds: Soft target for restore duration (logged, not enforced).
    """

    def __init__(self, max_restore_seconds: int = 3600) -> None:
        if max_restore_seconds <= 0:
            raise ValueError("max_restore_seconds must be > 0")
        self._max_restore_seconds = max_restore_seconds
        self._history: Dict[str, RestoreRecord] = {}   # restore_id → record

    def restore(
        self,
        backup: BackupRecord,
        data: bytes,
        verify_checksum: bool = True,
    ) -> RestoreRecord:
        """Restore data from a backup record.

        Args:
            backup: The BackupRecord to restore from.
            data: The raw bytes retrieved from storage.
            verify_checksum: If True, verify SHA-256 checksum against stored value.

        Returns:
            A RestoreRecord describing the outcome.
        """
        restore_id = str(uuid.uuid4())
        started_at = time.time()

        record = RestoreRecord(
            restore_id=restore_id,
            backup_id=backup.backup_id,
            tenant_id=backup.tenant_id,
            status=RestoreStatus.IN_PROGRESS,
            started_at=started_at,
            completed_at=None,
            duration_seconds=None,
            restored_bytes=len(data),
        )

        try:
            if backup.status != BackupStatus.SUCCESS:
                raise ValueError(f"Backup {backup.backup_id} is not in SUCCESS state")

            if verify_checksum and backup.checksum is not None:
                actual = hashlib.sha256(data).hexdigest()
                if actual != backup.checksum:
                    record.status = RestoreStatus.CHECKSUM_MISMATCH
                    record.error = f"Checksum mismatch: expected {backup.checksum}, got {actual}"
                    record.completed_at = time.time()
                    record.duration_seconds = record.completed_at - started_at
                    self._history[restore_id] = record
                    return record

            record.status = RestoreStatus.SUCCESS
        except Exception as exc:
            record.status = RestoreStatus.FAILED
            record.error = str(exc)

        record.completed_at = time.time()
        record.duration_seconds = record.completed_at - started_at
        self._history[restore_id] = record
        return record

    def get_record(self, restore_id: str) -> Optional[RestoreRecord]:
        return self._history.get(restore_id)

    def history(self) -> list:
        return list(self._history.values())

    @property
    def max_restore_seconds(self) -> int:
        return self._max_restore_seconds
