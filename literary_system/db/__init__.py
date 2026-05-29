"""literary_system/db — V586 LOSDB 기반 레이어 (SchemaRegistry + MigrationManager + SQLiteRealAdapter + VectorRealAdapter + GraphRealAdapter + MigrationEngine + LOSDBClient)."""

from .graph_real_adapter import GraphEdgeRecord, GraphRealAdapter, GraphRecord
from .health_monitor import AvailabilityState, BackendCircuitState, BackendHealthMonitor, BackendHealthRecord
from .losdb_client import LOSDBClient, LOSDBClientRecord
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
from .query_interface import AggregateResult, CharacterResult, QueryInterface, SceneResult
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
    "GraphRealAdapter",
    "GraphRecord",
    "GraphEdgeRecord",
    "MigrationEngine",
    "MigrationPlan",
    "MigrationExecutionRecord",
    "LOSDBClient",
    "LOSDBClientRecord",
    "QueryInterface",
    "SceneResult",
    "CharacterResult",
    "AvailabilityState",
    "BackendHealthMonitor",
    "BackendHealthRecord",
    "BackendCircuitState",
    "AggregateResult",
    "LOSDBClientRecord",
]
