"""
literary_system/db/migration_manager.py
V581 — Multi-backend MigrationManager
ADR-040: SQL(Alembic-style) + Graph(Cypher-style) + Vector(Qdrant collection) 3-어댑터

설계:
  - MigrationManager: 세 백엔드 어댑터 통합 오케스트레이터
  - SQLMigrationAdapter:    DDL/Alembic 스타일 마이그레이션
  - GraphMigrationAdapter:  Cypher/NetworkX 스타일 스키마 마이그레이션
  - VectorMigrationAdapter: Qdrant 컬렉션 생성/재인덱싱
  - 모든 어댑터는 MOCK 모드 기본 (ADR-059 MOCK-REAL 등가 원칙)
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .schema_registry import BackendType, MigrationRecord, SchemaRegistry, SchemaVersion

logger = logging.getLogger(__name__)


# ── 마이그레이션 정의 ──────────────────────────────────────────────────────────

@dataclass
class Migration:
    """단일 마이그레이션 명세."""
    migration_id: str            # "V581_001_sql_initial"
    backend:      BackendType
    from_version: str            # "0.0.0"
    to_version:   str            # "1.0.0"
    description:  str = ""
    up_script:    str = ""       # 업그레이드 스크립트 (DDL/Cypher/JSON)
    down_script:  str = ""       # 롤백 스크립트


# ── 어댑터 추상 기반 ───────────────────────────────────────────────────────────

class BaseMigrationAdapter(ABC):
    """단일 백엔드 마이그레이션 어댑터 기반 클래스."""

    def __init__(self, mock: bool = True) -> None:
        self.mock = mock

    @abstractmethod
    def apply(self, migration: Migration) -> bool:
        """마이그레이션 적용. True=성공, False=실패."""

    @abstractmethod
    def rollback(self, migration: Migration) -> bool:
        """마이그레이션 롤백. True=성공, False=실패."""

    @abstractmethod
    def check_connection(self) -> bool:
        """백엔드 연결 상태 확인."""


# ── SQL 어댑터 ─────────────────────────────────────────────────────────────────

class SQLMigrationAdapter(BaseMigrationAdapter):
    """
    SQL 백엔드 마이그레이션 어댑터 (Alembic-style).
    MOCK 모드: DDL 실행 없이 성공 시뮬레이션.
    REAL 모드: 실제 SQLAlchemy/Alembic 실행 (향후 구현).
    """

    def __init__(self, connection_url: str = "", mock: bool = True) -> None:
        super().__init__(mock=mock)
        self.connection_url = connection_url
        logger.info("SQLMigrationAdapter 초기화 (mock=%s)", mock)

    def check_connection(self) -> bool:
        if self.mock:
            return True
        try:
            # REAL: sqlalchemy engine ping
            raise NotImplementedError("REAL SQL 연결은 V596+ 구현 예정 (ADR-059)")
        except Exception as e:
            logger.error("SQL 연결 실패: %s", e)
            return False

    def apply(self, migration: Migration) -> bool:
        if self.mock:
            logger.info("[MOCK-SQL] apply %s: %s",
                        migration.migration_id, migration.up_script[:60])
            return True
        raise NotImplementedError("REAL SQL 마이그레이션은 V596+ 구현 예정")

    def rollback(self, migration: Migration) -> bool:
        if self.mock:
            logger.info("[MOCK-SQL] rollback %s", migration.migration_id)
            return True
        raise NotImplementedError("REAL SQL 롤백은 V596+ 구현 예정")


# ── Graph 어댑터 ───────────────────────────────────────────────────────────────

class GraphMigrationAdapter(BaseMigrationAdapter):
    """
    Graph 백엔드 마이그레이션 어댑터 (Cypher/NetworkX-style).
    MOCK 모드: Cypher 실행 없이 성공 시뮬레이션.
    """

    def __init__(self, endpoint: str = "", mock: bool = True) -> None:
        super().__init__(mock=mock)
        self.endpoint = endpoint
        logger.info("GraphMigrationAdapter 초기화 (mock=%s)", mock)

    def check_connection(self) -> bool:
        if self.mock:
            return True
        raise NotImplementedError("REAL Graph 연결은 V596+ 구현 예정")

    def apply(self, migration: Migration) -> bool:
        if self.mock:
            logger.info("[MOCK-GRAPH] apply %s: %s",
                        migration.migration_id, migration.up_script[:60])
            return True
        raise NotImplementedError("REAL Graph 마이그레이션은 V596+ 구현 예정")

    def rollback(self, migration: Migration) -> bool:
        if self.mock:
            logger.info("[MOCK-GRAPH] rollback %s", migration.migration_id)
            return True
        raise NotImplementedError("REAL Graph 롤백은 V596+ 구현 예정")


# ── Vector 어댑터 ──────────────────────────────────────────────────────────────

class VectorMigrationAdapter(BaseMigrationAdapter):
    """
    Vector 백엔드 마이그레이션 어댑터 (Qdrant collection 생성/재인덱싱).
    MOCK 모드: 컬렉션 작업 없이 성공 시뮬레이션.
    """

    def __init__(self, host: str = "localhost", port: int = 6333,
                 mock: bool = True) -> None:
        super().__init__(mock=mock)
        self.host = host
        self.port = port
        logger.info("VectorMigrationAdapter 초기화 (mock=%s, %s:%s)",
                    mock, host, port)

    def check_connection(self) -> bool:
        if self.mock:
            return True
        raise NotImplementedError("REAL Qdrant 연결은 V596+ 구현 예정")

    def apply(self, migration: Migration) -> bool:
        if self.mock:
            logger.info("[MOCK-VECTOR] apply %s: %s",
                        migration.migration_id, migration.up_script[:60])
            return True
        raise NotImplementedError("REAL Vector 마이그레이션은 V596+ 구현 예정")

    def rollback(self, migration: Migration) -> bool:
        if self.mock:
            logger.info("[MOCK-VECTOR] rollback %s", migration.migration_id)
            return True
        raise NotImplementedError("REAL Vector 롤백은 V596+ 구현 예정")


# ── MigrationManager ──────────────────────────────────────────────────────────

@dataclass
class MigrationResult:
    migration_id:  str
    backend:       BackendType
    success:       bool
    from_version:  str
    to_version:    str
    error_msg:     str = ""
    applied_at:    str = field(default_factory=lambda:
                               datetime.now(timezone.utc).isoformat())


class MigrationManager:
    """
    Multi-backend MigrationManager.
    세 어댑터(SQL/Graph/Vector)를 통합 관리하고
    SchemaRegistry에 버전 기록을 위임한다.
    """

    def __init__(
        self,
        sql_adapter:    Optional[SQLMigrationAdapter]    = None,
        graph_adapter:  Optional[GraphMigrationAdapter]  = None,
        vector_adapter: Optional[VectorMigrationAdapter] = None,
        registry:       Optional[SchemaRegistry]         = None,
        mock: bool = True,
    ) -> None:
        self._adapters: Dict[BackendType, BaseMigrationAdapter] = {
            BackendType.SQL:    sql_adapter    or SQLMigrationAdapter(mock=mock),
            BackendType.GRAPH:  graph_adapter  or GraphMigrationAdapter(mock=mock),
            BackendType.VECTOR: vector_adapter or VectorMigrationAdapter(mock=mock),
        }
        self._registry = registry or SchemaRegistry.get_instance()
        self._mock = mock
        logger.info("MigrationManager 초기화 (mock=%s)", mock)

    # ── 연결 확인 ────────────────────────────────────────────────────────────
    def health_check(self) -> Dict[str, bool]:
        return {
            b.value: adapter.check_connection()
            for b, adapter in self._adapters.items()
        }

    # ── 단일 마이그레이션 적용 ───────────────────────────────────────────────
    def apply(self, migration: Migration) -> MigrationResult:
        adapter = self._adapters[migration.backend]
        prev_version = self._registry.current_version(migration.backend).version_string
        success = False
        error_msg = ""

        try:
            success = adapter.apply(migration)
        except Exception as e:
            error_msg = str(e)
            logger.error("Migration %s 실패: %s", migration.migration_id, e)

        # 레지스트리 업데이트 (성공 시만)
        if success:
            parts = migration.to_version.split(".")
            self._registry.register(
                backend     = migration.backend,
                major       = int(parts[0]),
                minor       = int(parts[1]),
                patch       = int(parts[2]),
                description = migration.description,
            )

        # 히스토리 기록 (성공/실패 무관)
        rec = MigrationRecord(
            migration_id = migration.migration_id,
            backend      = migration.backend,
            from_version = prev_version,
            to_version   = migration.to_version if success else prev_version,
            description  = migration.description,
            applied_at   = datetime.now(timezone.utc).isoformat(),
            success      = success,
            error_msg    = error_msg,
        )
        self._registry.record_migration(rec)

        return MigrationResult(
            migration_id = migration.migration_id,
            backend      = migration.backend,
            success      = success,
            from_version = prev_version,
            to_version   = migration.to_version if success else prev_version,
            error_msg    = error_msg,
        )

    # ── 배치 마이그레이션 ─────────────────────────────────────────────────────
    def apply_batch(
        self, migrations: List[Migration], stop_on_failure: bool = True
    ) -> List[MigrationResult]:
        results: List[MigrationResult] = []
        for m in migrations:
            result = self.apply(m)
            results.append(result)
            if not result.success and stop_on_failure:
                logger.error(
                    "Batch 중단: %s 실패 — stop_on_failure=True",
                    m.migration_id,
                )
                break
        return results

    # ── 호환성 검증 ──────────────────────────────────────────────────────────
    def verify_compatibility(
        self,
        backend:        BackendType,
        required_major: int,
        required_minor: int,
    ) -> Tuple[bool, str]:
        from typing import Tuple  # local import for type hint
        return self._registry.is_compatible(backend, required_major, required_minor)

    # ── 상태 보고 ─────────────────────────────────────────────────────────────
    def status(self) -> dict:
        health = self.health_check()
        versions = self._registry.all_versions()
        history_count = {
            b.value: len(self._registry.migration_history(b))
            for b in BackendType
        }
        return {
            "mock":           self._mock,
            "health":         health,
            "versions":       versions,
            "history_counts": history_count,
        }
