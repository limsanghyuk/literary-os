"""
literary_system/db/schema_registry.py
V581 — SchemaRegistry: LOSDB 스키마 버전 관리 단일 진실 원천
ADR-040: Multi-backend MigrationManager 기반 스키마 레지스트리
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class BackendType(str, Enum):
    SQL    = "sql"
    GRAPH  = "graph"
    VECTOR = "vector"


@dataclass
class SchemaVersion:
    backend:     BackendType
    major:       int
    minor:       int
    patch:       int
    description: str = ""
    checksum:    str = ""
    applied_at:  Optional[str] = None

    @property
    def version_string(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def is_compatible_with(self, other: "SchemaVersion") -> bool:
        return (
            self.backend == other.backend
            and self.major == other.major
            and other.minor <= self.minor
        )

    def to_dict(self) -> dict:
        return {
            "backend":     self.backend.value,
            "version":     self.version_string,
            "description": self.description,
            "checksum":    self.checksum,
            "applied_at":  self.applied_at,
        }


@dataclass
class MigrationRecord:
    migration_id: str
    backend:      BackendType
    from_version: str
    to_version:   str
    description:  str = ""
    applied_at:   Optional[str] = None
    success:      bool = True
    error_msg:    str  = ""

    def to_dict(self) -> dict:
        return {
            "migration_id": self.migration_id,
            "backend":      self.backend.value,
            "from_version": self.from_version,
            "to_version":   self.to_version,
            "description":  self.description,
            "applied_at":   self.applied_at,
            "success":      self.success,
            "error_msg":    self.error_msg,
        }


class SchemaRegistry:
    """LOSDB 스키마 버전 레지스트리 — SQL/Graph/Vector 통합 관리."""

    _instance: Optional["SchemaRegistry"] = None

    def __init__(self) -> None:
        self._versions: Dict[BackendType, SchemaVersion] = {
            BackendType.SQL:    SchemaVersion(BackendType.SQL,    0, 0, 0),
            BackendType.GRAPH:  SchemaVersion(BackendType.GRAPH,  0, 0, 0),
            BackendType.VECTOR: SchemaVersion(BackendType.VECTOR, 0, 0, 0),
        }
        self._history: List[MigrationRecord] = []

    @classmethod
    def get_instance(cls) -> "SchemaRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """테스트용 싱글턴 초기화."""
        cls._instance = None

    def current_version(self, backend: BackendType) -> SchemaVersion:
        return self._versions[backend]

    def all_versions(self) -> Dict[str, dict]:
        return {b.value: v.to_dict() for b, v in self._versions.items()}

    def register(
        self,
        backend:     BackendType,
        major:       int,
        minor:       int,
        patch:       int,
        description: str = "",
        schema_def:  Optional[str] = None,
    ) -> SchemaVersion:
        checksum = ""
        if schema_def:
            checksum = hashlib.sha256(schema_def.encode()).hexdigest()[:16]
        applied_at = datetime.now(timezone.utc).isoformat()
        sv = SchemaVersion(
            backend=backend, major=major, minor=minor, patch=patch,
            description=description, checksum=checksum, applied_at=applied_at,
        )
        prev = self._versions[backend]
        self._versions[backend] = sv
        logger.info("SchemaRegistry: %s %s→%s", backend.value,
                    prev.version_string, sv.version_string)
        return sv

    def record_migration(self, record: MigrationRecord) -> None:
        self._history.append(record)
        logger.info("Migration %s (%s): %s→%s success=%s",
                    record.migration_id, record.backend.value,
                    record.from_version, record.to_version, record.success)

    def migration_history(
        self, backend: Optional[BackendType] = None
    ) -> List[MigrationRecord]:
        if backend is None:
            return list(self._history)
        return [r for r in self._history if r.backend == backend]

    def is_compatible(
        self,
        backend:        BackendType,
        required_major: int,
        required_minor: int,
    ) -> Tuple[bool, str]:
        cur = self._versions[backend]
        if cur.major != required_major:
            return False, (f"{backend.value} major 불일치: "
                           f"현재={cur.major}, 요구={required_major}")
        if cur.minor < required_minor:
            return False, (f"{backend.value} minor 부족: "
                           f"현재={cur.minor}, 요구={required_minor}")
        return True, "OK"

    def to_snapshot(self) -> dict:
        return {
            "versions":    self.all_versions(),
            "history":     [r.to_dict() for r in self._history],
            "snapshot_at": datetime.now(timezone.utc).isoformat(),
        }

    def __repr__(self) -> str:  # pragma: no cover
        parts = [f"{b.value}={v.version_string}" for b, v in self._versions.items()]
        return f"SchemaRegistry({', '.join(parts)})"
