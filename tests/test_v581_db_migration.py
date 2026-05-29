"""
tests/test_v581_db_migration.py
V581 — SchemaRegistry + Multi-backend MigrationManager 단위 테스트
ADR-040 검증
"""
import pytest
from literary_system.db.schema_registry import (
    BackendType, SchemaRegistry, SchemaVersion, MigrationRecord,
)
from literary_system.db.migration_manager import (
    Migration, MigrationManager, MigrationResult,
    SQLMigrationAdapter, GraphMigrationAdapter, VectorMigrationAdapter,
)


# ── Fixture ────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_registry():
    """각 테스트 전후 싱글턴 초기화."""
    SchemaRegistry.reset()
    yield
    SchemaRegistry.reset()


@pytest.fixture
def registry():
    return SchemaRegistry.get_instance()


@pytest.fixture
def manager():
    return MigrationManager(mock=True)


# ── SchemaVersion 단위 테스트 ──────────────────────────────────────────────────

class TestSchemaVersion:
    def test_version_string(self):
        sv = SchemaVersion(BackendType.SQL, 1, 2, 3)
        assert sv.version_string == "1.2.3"

    def test_compatibility_same_major_higher_minor(self):
        current = SchemaVersion(BackendType.SQL, 1, 5, 0)
        required = SchemaVersion(BackendType.SQL, 1, 3, 0)
        assert current.is_compatible_with(required)

    def test_compatibility_different_major(self):
        current = SchemaVersion(BackendType.SQL, 2, 0, 0)
        required = SchemaVersion(BackendType.SQL, 1, 0, 0)
        assert not current.is_compatible_with(required)

    def test_compatibility_lower_minor(self):
        current = SchemaVersion(BackendType.SQL, 1, 2, 0)
        required = SchemaVersion(BackendType.SQL, 1, 5, 0)
        assert not current.is_compatible_with(required)

    def test_to_dict_keys(self):
        sv = SchemaVersion(BackendType.VECTOR, 1, 0, 0, description="test")
        d = sv.to_dict()
        assert {"backend", "version", "description", "checksum", "applied_at"} == set(d.keys())
        assert d["backend"] == "vector"
        assert d["version"] == "1.0.0"


# ── SchemaRegistry 단위 테스트 ─────────────────────────────────────────────────

class TestSchemaRegistry:
    def test_singleton(self, registry):
        reg2 = SchemaRegistry.get_instance()
        assert registry is reg2

    def test_initial_versions_zero(self, registry):
        for b in BackendType:
            assert registry.current_version(b).version_string == "0.0.0"

    def test_register_updates_version(self, registry):
        registry.register(BackendType.SQL, 1, 0, 0, description="초기 스키마")
        v = registry.current_version(BackendType.SQL)
        assert v.version_string == "1.0.0"
        assert v.description == "초기 스키마"
        assert v.applied_at is not None

    def test_register_checksum_generated(self, registry):
        registry.register(BackendType.GRAPH, 1, 0, 0, schema_def="CREATE NODE ...")
        v = registry.current_version(BackendType.GRAPH)
        assert len(v.checksum) == 16

    def test_register_no_schema_def_empty_checksum(self, registry):
        registry.register(BackendType.VECTOR, 1, 0, 0)
        v = registry.current_version(BackendType.VECTOR)
        assert v.checksum == ""

    def test_all_versions_keys(self, registry):
        d = registry.all_versions()
        assert set(d.keys()) == {"sql", "graph", "vector"}

    def test_record_migration(self, registry):
        rec = MigrationRecord(
            migration_id="V581_001",
            backend=BackendType.SQL,
            from_version="0.0.0",
            to_version="1.0.0",
        )
        registry.record_migration(rec)
        history = registry.migration_history(BackendType.SQL)
        assert len(history) == 1
        assert history[0].migration_id == "V581_001"

    def test_migration_history_all(self, registry):
        for b in BackendType:
            registry.record_migration(MigrationRecord(
                f"m_{b.value}", b, "0.0.0", "1.0.0"
            ))
        assert len(registry.migration_history()) == 3

    def test_is_compatible_ok(self, registry):
        registry.register(BackendType.SQL, 1, 2, 0)
        ok, msg = registry.is_compatible(BackendType.SQL, 1, 1)
        assert ok
        assert msg == "OK"

    def test_is_compatible_major_mismatch(self, registry):
        registry.register(BackendType.SQL, 2, 0, 0)
        ok, msg = registry.is_compatible(BackendType.SQL, 1, 0)
        assert not ok
        assert "major" in msg

    def test_is_compatible_minor_insufficient(self, registry):
        registry.register(BackendType.SQL, 1, 1, 0)
        ok, msg = registry.is_compatible(BackendType.SQL, 1, 3)
        assert not ok
        assert "minor" in msg

    def test_to_snapshot_structure(self, registry):
        snap = registry.to_snapshot()
        assert "versions" in snap
        assert "history" in snap
        assert "snapshot_at" in snap

    def test_reset_clears_singleton(self):
        reg1 = SchemaRegistry.get_instance()
        SchemaRegistry.reset()
        reg2 = SchemaRegistry.get_instance()
        assert reg1 is not reg2


# ── 어댑터 단위 테스트 ─────────────────────────────────────────────────────────

class TestAdapters:
    def test_sql_adapter_mock_connection(self):
        a = SQLMigrationAdapter(mock=True)
        assert a.check_connection() is True

    def test_sql_adapter_mock_apply(self):
        a = SQLMigrationAdapter(mock=True)
        m = Migration("m1", BackendType.SQL, "0.0.0", "1.0.0", up_script="CREATE TABLE ...")
        assert a.apply(m) is True

    def test_sql_adapter_mock_rollback(self):
        a = SQLMigrationAdapter(mock=True)
        m = Migration("m1", BackendType.SQL, "1.0.0", "0.0.0", down_script="DROP TABLE ...")
        assert a.rollback(m) is True

    def test_graph_adapter_mock(self):
        a = GraphMigrationAdapter(mock=True)
        assert a.check_connection() is True
        m = Migration("g1", BackendType.GRAPH, "0.0.0", "1.0.0")
        assert a.apply(m) is True

    def test_vector_adapter_mock(self):
        a = VectorMigrationAdapter(mock=True)
        assert a.check_connection() is True
        m = Migration("v1", BackendType.VECTOR, "0.0.0", "1.0.0")
        assert a.apply(m) is True

    def test_sql_real_raises_not_implemented(self):
        a = SQLMigrationAdapter(mock=False)
        m = Migration("m1", BackendType.SQL, "0.0.0", "1.0.0")
        with pytest.raises(NotImplementedError):
            a.apply(m)


# ── MigrationManager 단위 테스트 ──────────────────────────────────────────────

class TestMigrationManager:
    def test_health_check_all_true(self, manager):
        h = manager.health_check()
        assert all(h.values())
        assert set(h.keys()) == {"sql", "graph", "vector"}

    def test_apply_single_success(self, manager):
        m = Migration("V581_001", BackendType.SQL, "0.0.0", "1.0.0", "SQL 초기화")
        result = manager.apply(m)
        assert result.success
        assert result.to_version == "1.0.0"

    def test_apply_updates_registry(self, manager):
        m = Migration("V581_001", BackendType.GRAPH, "0.0.0", "1.0.0")
        manager.apply(m)
        reg = SchemaRegistry.get_instance()
        assert reg.current_version(BackendType.GRAPH).version_string == "1.0.0"

    def test_apply_records_history(self, manager):
        m = Migration("V581_001", BackendType.VECTOR, "0.0.0", "1.0.0")
        manager.apply(m)
        reg = SchemaRegistry.get_instance()
        history = reg.migration_history(BackendType.VECTOR)
        assert len(history) == 1
        assert history[0].success is True

    def test_apply_batch_all_success(self, manager):
        migrations = [
            Migration("V581_001", BackendType.SQL,    "0.0.0", "1.0.0"),
            Migration("V581_002", BackendType.GRAPH,  "0.0.0", "1.0.0"),
            Migration("V581_003", BackendType.VECTOR, "0.0.0", "1.0.0"),
        ]
        results = manager.apply_batch(migrations)
        assert all(r.success for r in results)
        assert len(results) == 3

    def test_apply_batch_stop_on_failure(self):
        """REAL 어댑터로 강제 실패 시 stop_on_failure 동작."""
        sql_real = SQLMigrationAdapter(mock=False)
        mgr = MigrationManager(sql_adapter=sql_real, mock=False)
        migrations = [
            Migration("V581_001", BackendType.SQL,    "0.0.0", "1.0.0"),
            Migration("V581_002", BackendType.GRAPH,  "0.0.0", "1.0.0"),  # 미도달 (SQL 실패로 중단)
        ]
        results = mgr.apply_batch(migrations, stop_on_failure=True)
        # SQL 어댑터 REAL → NotImplementedError → success=False → 중단
        assert len(results) == 1
        assert results[0].success is False

    def test_verify_compatibility(self, manager):
        reg = SchemaRegistry.get_instance()
        reg.register(BackendType.SQL, 1, 2, 0)
        ok, msg = manager.verify_compatibility(BackendType.SQL, 1, 1)
        assert ok

    def test_status_structure(self, manager):
        s = manager.status()
        assert {"mock", "health", "versions", "history_counts"} == set(s.keys())
        assert s["mock"] is True


# ── Gate G40 통합 테스트 ──────────────────────────────────────────────────────

class TestGateG40:
    def test_gate_g40_passes(self):
        from literary_system.gates.release_gate import _gate_db_migration_g40
        result = _gate_db_migration_g40()
        assert result["pass"] is True, f"Gate G40 실패: {result.get('details')}"

    def test_gate_g40_in_gates_list(self):
        from literary_system.gates.release_gate import GATES
        gate_ids = [g[0] for g in GATES]
        assert "db_migration_g40" in gate_ids

    def test_run_release_gate_39_becomes_40(self):
        from literary_system.gates.release_gate import run_release_gate
        result = run_release_gate()
        assert result["total_gates"] >= 45, (
            f"Gate 수 오류: 기대>=45, 실제={result['total_gates']}"
        )  # V583: G42 추가로 41개
        assert result["pass"] is True, f"Release Gate FAIL: {result['issues']}"


# ── B3 회귀 테스트 — 잘못된 버전 형식 처리 ───────────────────────────────────

class TestMigrationManagerRobustness:
    def test_malformed_version_two_parts(self, manager):
        """B3: 'major.minor' 형식 → success=False, 히스토리 기록됨."""
        m = Migration("bad_001", BackendType.SQL, "0.0.0", "1.0", "버전 형식 오류")
        result = manager.apply(m)
        assert result.success is False
        assert result.error_msg != ""
        # 히스토리에는 실패 기록이 남아야 함
        reg = SchemaRegistry.get_instance()
        history = reg.migration_history(BackendType.SQL)
        assert len(history) == 1
        assert history[0].success is False

    def test_malformed_version_with_prefix(self, manager):
        """B3: 'v1.0.0' 형식 → int() 파싱 실패 → success=False."""
        m = Migration("bad_002", BackendType.GRAPH, "0.0.0", "v1.0.0", "v prefix 오류")
        result = manager.apply(m)
        assert result.success is False

    def test_valid_after_malformed(self, manager):
        """B3: 잘못된 마이그레이션 후 올바른 마이그레이션은 성공해야 함."""
        bad = Migration("bad_001", BackendType.SQL, "0.0.0", "bad", "오류")
        good = Migration("good_001", BackendType.SQL, "0.0.0", "1.0.0", "정상")
        manager.apply(bad)
        result = manager.apply(good)
        assert result.success is True
        reg = SchemaRegistry.get_instance()
        assert reg.current_version(BackendType.SQL).version_string == "1.0.0"

    def test_base_adapter_importable(self):
        """B4: BaseMigrationAdapter가 db 패키지에서 직접 임포트 가능해야 함."""
        from literary_system.db import BaseMigrationAdapter
        assert BaseMigrationAdapter is not None
