"""literary_system/db — V583 LOSDB 기반 레이어 (SchemaRegistry + MigrationManager + SQLiteRealAdapter + MigrationEngine)."""
from .migration_engine import MigrationEngine, MigrationExecutionRecord, MigrationPlan
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
from .vector_real_adapter import VectorRealAdapter, VectorRecord

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
    "VectorRealAdapter",
    "VectorRecord",
    "MigrationEngine",
    "MigrationPlan",
    "MigrationExecutionRecord",
]
