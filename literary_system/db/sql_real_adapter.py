"""
literary_system/db/sql_real_adapter.py
V582 — SQLiteRealAdapter: sqlite3 기반 REAL 마이그레이션 어댑터
ADR-041: LOSDB Phase A — SQL REAL 어댑터 + LOSDB CLI
"""
from __future__ import annotations

import logging
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Generator, List

from .migration_manager import BaseMigrationAdapter, Migration
from .schema_registry import BackendType, MigrationRecord, SchemaRegistry

logger = logging.getLogger(__name__)


_IDENTIFIER_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def _quote_identifier(name: str) -> str:
    """SQL 식별자 안전 인용 — injection 방지 (BUG-09 fix: SQLite table name safety)."""
    if not _IDENTIFIER_RE.match(name):
        raise ValueError(f"Unsafe SQL identifier: {name!r}")
    return f'"{name}"'


class SQLiteRealAdapter(BaseMigrationAdapter):
    """sqlite3 기반 REAL 마이그레이션 어댑터 (ADR-041, V582)."""

    SUPPORTED_SCHEME = "sqlite"
    MIGRATION_TABLE = "losdb_migrations"

    def __init__(
        self,
        connection_url: str = "sqlite:///:memory:",
        mock: bool = False,
    ) -> None:
        super().__init__(mock=mock)
        self._connection_url = connection_url
        self._db_path = self._parse_path(connection_url)
        self._conn: sqlite3.Connection | None = None
        self._initialized = False
        logger.info("SQLiteRealAdapter 초기화 (mock=%s, path=%s)", mock, self._db_path)

    @staticmethod
    def _parse_path(url: str) -> str:
        if not url:
            return ":memory:"
        if ":memory:" in url:
            return ":memory:"
        m = re.match(r"sqlite:///(.+)", url)
        if m:
            return m.group(1)
        return ":memory:"

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            self._initialized = False

    @contextmanager
    def _transaction(self) -> Generator[sqlite3.Cursor, None, None]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def _ensure_migration_table(self) -> None:
        if self._initialized:
            return
        conn = self._get_connection()
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.MIGRATION_TABLE} (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                version     TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                backend     TEXT NOT NULL DEFAULT 'sql',
                applied_at  TEXT NOT NULL,
                rolled_back INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.commit()
        self._initialized = True

    def check_connection(self) -> bool:
        if self.mock:
            return True
        try:
            conn = self._get_connection()
            conn.execute("SELECT 1")
            return True
        except Exception as exc:
            logger.error("SQLiteRealAdapter.check_connection 실패: %s", exc)
            return False

    def apply(self, migration: Migration) -> bool:
        if self.mock:
            logger.info("[MOCK-SQLite] apply %s → %s", migration.from_version, migration.to_version)
            return True
        conn = self._get_connection()
        try:
            self._ensure_migration_table()
            # FIX-A (V595.3): executescript()는 내부에서 자동 COMMIT 발생 → 원자성 없음.
            # BEGIN IMMEDIATE + 개별 execute() 로 전체 migration을 단일 트랜잭션으로 묶는다.
            conn.execute("BEGIN IMMEDIATE")
            if migration.up_script:
                stmts = [s.strip() for s in migration.up_script.split(";") if s.strip()]
                for stmt in stmts:
                    conn.execute(stmt)
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                f"INSERT INTO {self.MIGRATION_TABLE} "
                "(version, description, backend, applied_at, rolled_back) VALUES (?, ?, ?, ?, 0)",
                (migration.to_version, migration.description, "sql", now),
            )
            conn.commit()
            reg = SchemaRegistry.get_instance()
            parts = migration.to_version.split(".")
            major = int(parts[0]) if len(parts) > 0 else 1
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            reg.register(BackendType.SQL, major, minor, patch, migration.description)
            record = MigrationRecord(
                migration_id=migration.migration_id,
                backend=BackendType.SQL,
                from_version=migration.from_version,
                to_version=migration.to_version,
                description=migration.description,
                applied_at=now,
                success=True,
            )
            reg.record_migration(record)
            logger.info("SQLiteRealAdapter.apply OK: %s → %s", migration.from_version, migration.to_version)
            return True
        except Exception as exc:
            conn.rollback()
            logger.exception("SQLiteRealAdapter.apply 실패 (롤백 완료): %s", exc)
            return False

    def rollback(self, migration: Migration) -> bool:
        if self.mock:
            logger.info("[MOCK-SQLite] rollback %s → %s", migration.to_version, migration.from_version)
            return True
        try:
            self._ensure_migration_table()
            if migration.down_script:
                # FIX-A (V595.3): rollback도 동일하게 원자 트랜잭션으로 처리
                conn = self._get_connection()
                conn.execute("BEGIN IMMEDIATE")
                stmts = [s.strip() for s in migration.down_script.split(";") if s.strip()]
                for stmt in stmts:
                    conn.execute(stmt)
                conn.commit()
            with self._transaction() as cur:
                cur.execute(
                    f"UPDATE {self.MIGRATION_TABLE} SET rolled_back=1 WHERE version=? AND backend='sql'",
                    (migration.to_version,),
                )
            logger.info("SQLiteRealAdapter.rollback OK: %s → %s", migration.to_version, migration.from_version)
            return True
        except Exception as exc:
            logger.exception("SQLiteRealAdapter.rollback 실패: %s", exc)
            return False

    def list_applied(self) -> List[dict]:
        if self.mock:
            return []
        try:
            self._ensure_migration_table()
            conn = self._get_connection()
            rows = conn.execute(
                f"SELECT version, description, applied_at, rolled_back "
                f"FROM {self.MIGRATION_TABLE} ORDER BY id"
            ).fetchall()
            return [dict(row) for row in rows]
        except Exception as exc:
            logger.warning("SQLiteRealAdapter.list_applied 실패: %s", exc)
            return []

    def table_exists(self, table_name: str) -> bool:
        if self.mock:
            return False
        try:
            conn = self._get_connection()
            row = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            ).fetchone()
            return row is not None
        except Exception:
            return False

    def get_rows(self, table_name: str) -> list:
        """테이블에서 모든 행을 dict 리스트로 반환 (label=table_name 으로 LOSDBClient 호환)."""
        if self.mock or not self.table_exists(table_name):
            return []
        try:
            conn = self._get_connection()
            cur = conn.execute(f"SELECT * FROM {_quote_identifier(table_name)}")  # noqa: S608
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        except Exception:
            return []

    def schema_info(self) -> dict:
        return {
            "adapter": "SQLiteRealAdapter",
            "version": "V582",
            "adr": "ADR-041",
            "mock": self.mock,
            "db_path": self._db_path,
            "connection_url": self._connection_url,
        }

    def __repr__(self) -> str:
        return (
            f"SQLiteRealAdapter(mock={self.mock}, "
            f"db_path={self._db_path!r}, "
            f"initialized={self._initialized})"
        )
