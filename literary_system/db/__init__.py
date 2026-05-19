"""literary_system/db — V581 LOSDB 기반 레이어 (SchemaRegistry + MigrationManager)."""
from .migration_manager import (
    GraphMigrationAdapter,
    Migration,
    MigrationManager,
    MigrationResult,
    SQLMigrationAdapter,
    VectorMigrationAdapter,
)
from .schema_registry import BackendType, MigrationRecord, SchemaRegistry, SchemaVersion

__all__ = [
    "BackendType",
    "MigrationRecord",
    "SchemaRegistry",
    "SchemaVersion",
    "Migration",
    "MigrationManager",
    "MigrationResult",
    "SQLMigrationAdapter",
    "GraphMigrationAdapter",
    "VectorMigrationAdapter",
]
