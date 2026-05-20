"""literary_system/db — V582 LOSDB 기반 레이어 (SchemaRegistry + MigrationManager + SQLiteRealAdapter)."""
from .migration_manager import (
    BaseMigrationAdapter,
    GraphMigrationAdapter,
    Migration,
    MigrationManager,
    MigrationResult,
    SQLMigrationAdapter,
    VectorMigrationAdapter,
)
from .schema_registry import BackendType, MigrationRecord, SchemaRegistry, SchemaVersion
from .sql_real_adapter import SQLiteRealAdapter

__all__ = [
    "BackendType",
    "MigrationRecord",
    "SchemaRegistry",
    "SchemaVersion",
    "BaseMigrationAdapter",
    "Migration",
    "MigrationManager",
    "MigrationResult",
    "SQLMigrationAdapter",
    "GraphMigrationAdapter",
    "VectorMigrationAdapter",
    "SQLiteRealAdapter",
]
