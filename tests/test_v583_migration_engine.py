"""tests/test_v583_migration_engine.py — V583 MigrationEngine 테스트 (ADR-042)

TC01~TC40: MigrationEngine, MigrationPlan, MigrationExecutionRecord 검증
"""
from __future__ import annotations

import json

import pytest

from literary_system.db import (
    BackendType,
    Migration,
    MigrationEngine,
    MigrationExecutionRecord,
    MigrationPlan,
    SQLiteRealAdapter,
)
from literary_system.db.migration_manager import (
    GraphMigrationAdapter,
    SQLMigrationAdapter,
    VectorMigrationAdapter,
)
from literary_system.gates.gate_registry import GATE_REGISTRY
from literary_system.gates.release_gate import GATES

# ─────────────────────────────────────────────────────────────────────────────
# 공통 픽스처
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def sql_real():
    """SQLiteRealAdapter REAL 인스턴스 (in-memory)."""
    return SQLiteRealAdapter(connection_url="sqlite:///:memory:", mock=False)


@pytest.fixture
def sql_mock():
    return SQLMigrationAdapter(mock=True)


@pytest.fixture
def graph_mock():
    return GraphMigrationAdapter(mock=True)


@pytest.fixture
def vector_mock():
    return VectorMigrationAdapter(mock=True)


@pytest.fixture
def simple_migration():
    return Migration(
        migration_id="test_v583_001",
        backend=BackendType.SQL,
        from_version="0.0.0",
        to_version="1.0.0",
        description="V583 단순 테스트 마이그레이션",
        up_script="CREATE TABLE IF NOT EXISTS v583_test (id INTEGER PRIMARY KEY, name TEXT)",
        down_script="DROP TABLE IF EXISTS v583_test",
    )


@pytest.fixture
def multi_migration():
    """두 개의 마이그레이션 목록."""
    m1 = Migration(
        migration_id="test_v583_m1",
        backend=BackendType.SQL,
        from_version="0.0.0",
        to_version="1.0.0",
        description="마이그레이션 1",
        up_script="CREATE TABLE IF NOT EXISTS m1_tbl (id INTEGER PRIMARY KEY)",
        down_script="DROP TABLE IF EXISTS m1_tbl",
    )
    m2 = Migration(
        migration_id="test_v583_m2",
        backend=BackendType.SQL,
        from_version="1.0.0",
        to_version="2.0.0",
        description="마이그레이션 2",
        up_script="CREATE TABLE IF NOT EXISTS m2_tbl (id INTEGER PRIMARY KEY)",
        down_script="DROP TABLE IF EXISTS m2_tbl",
    )
    return [m1, m2]


# ─────────────────────────────────────────────────────────────────────────────
# A. MigrationPlan
# ─────────────────────────────────────────────────────────────────────────────

class TestMigrationPlan:
    def test_tc01_basic_creation(self, simple_migration):
        """TC01: MigrationPlan 기본 생성."""
        plan = MigrationPlan(
            plan_id="plan_001",
            migrations=[simple_migration],
            target_adapters=["sql"],
            description="기본 계획",
        )
        assert plan.plan_id == "plan_001"
        assert len(plan.migrations) == 1
        assert plan.target_adapters == ["sql"]
        assert plan.description == "기본 계획"

    def test_tc02_empty_plan_id_raises(self, simple_migration):
        """TC02: plan_id 빈 문자열 → ValueError."""
        with pytest.raises(ValueError, match="plan_id"):
            MigrationPlan(plan_id="", migrations=[simple_migration], target_adapters=["sql"])

    def test_tc03_empty_migrations_raises(self):
        """TC03: migrations 빈 목록 → ValueError."""
        with pytest.raises(ValueError, match="migrations"):
            MigrationPlan(plan_id="p1", migrations=[], target_adapters=["sql"])

    def test_tc04_empty_target_adapters_raises(self, simple_migration):
        """TC04: target_adapters 빈 목록 → ValueError."""
        with pytest.raises(ValueError, match="target_adapters"):
            MigrationPlan(plan_id="p1", migrations=[simple_migration], target_adapters=[])

    def test_tc05_multi_adapters(self, simple_migration):
        """TC05: 복수 target_adapters 지원."""
        plan = MigrationPlan(
            plan_id="p_multi",
            migrations=[simple_migration],
            target_adapters=["sql", "graph", "vector"],
        )
        assert len(plan.target_adapters) == 3

    def test_tc06_multi_migrations(self, multi_migration):
        """TC06: 복수 migrations 지원."""
        plan = MigrationPlan(
            plan_id="p_multi_mig",
            migrations=multi_migration,
            target_adapters=["sql"],
        )
        assert len(plan.migrations) == 2

    def test_tc07_default_description(self, simple_migration):
        """TC07: description 기본값 빈 문자열."""
        plan = MigrationPlan(
            plan_id="p1", migrations=[simple_migration], target_adapters=["sql"]
        )
        assert plan.description == ""


# ─────────────────────────────────────────────────────────────────────────────
# B. MigrationExecutionRecord
# ─────────────────────────────────────────────────────────────────────────────

class TestMigrationExecutionRecord:
    def test_tc08_basic_creation(self):
        """TC08: MigrationExecutionRecord 기본 생성."""
        rec = MigrationExecutionRecord(
            plan_id="p1",
            executed_at="2026-05-20T00:00:00+00:00",
            results=[],
            success=True,
            rolled_back=False,
        )
        assert rec.plan_id == "p1"
        assert rec.success is True
        assert rec.rolled_back is False
        assert rec.error is None

    def test_tc09_to_json(self):
        """TC09: to_json() JSON 직렬화."""
        rec = MigrationExecutionRecord(
            plan_id="p_json",
            executed_at="2026-05-20T00:00:00+00:00",
            results=[{"adapter": "sql", "migration_id": "m1", "ok": True}],
            success=True,
            rolled_back=False,
        )
        j = rec.to_json()
        assert isinstance(j, str)
        data = json.loads(j)
        assert data["plan_id"] == "p_json"
        assert data["success"] is True
        assert len(data["results"]) == 1

    def test_tc10_from_json(self):
        """TC10: from_json() JSON 역직렬화."""
        rec = MigrationExecutionRecord(
            plan_id="p_restore",
            executed_at="2026-05-20T00:00:00+00:00",
            results=[],
            success=False,
            rolled_back=True,
            error="테스트 오류",
        )
        restored = MigrationExecutionRecord.from_json(rec.to_json())
        assert restored.plan_id == rec.plan_id
        assert restored.success == rec.success
        assert restored.rolled_back == rec.rolled_back
        assert restored.error == rec.error

    def test_tc11_json_roundtrip_with_results(self):
        """TC11: results 포함 JSON 왕복 직렬화."""
        results = [
            {"adapter": "sql", "migration_id": "m1", "ok": True},
            {"adapter": "graph", "migration_id": "m1", "ok": True},
        ]
        rec = MigrationExecutionRecord(
            plan_id="p_rt", executed_at="2026-05-20T00:00:00+00:00",
            results=results, success=True, rolled_back=False,
        )
        restored = MigrationExecutionRecord.from_json(rec.to_json())
        assert len(restored.results) == 2
        assert restored.results[0]["adapter"] == "sql"

    def test_tc12_json_contains_executed_at(self):
        """TC12: JSON에 executed_at 포함."""
        rec = MigrationExecutionRecord(
            plan_id="p1", executed_at="2026-05-20T12:00:00+00:00",
            results=[], success=True, rolled_back=False,
        )
        data = json.loads(rec.to_json())
        assert "executed_at" in data
        assert "2026-05-20" in data["executed_at"]


# ─────────────────────────────────────────────────────────────────────────────
# C. MigrationEngine 생성
# ─────────────────────────────────────────────────────────────────────────────

class TestMigrationEngineCreation:
    def test_tc13_single_adapter(self, sql_mock):
        """TC13: 단일 어댑터로 엔진 생성."""
        engine = MigrationEngine(adapters={"sql": sql_mock})
        assert engine.adapter_keys() == ["sql"]

    def test_tc14_multi_adapter(self, sql_mock, graph_mock, vector_mock):
        """TC14: 3종 어댑터 조합 엔진."""
        engine = MigrationEngine(adapters={
            "sql": sql_mock, "graph": graph_mock, "vector": vector_mock
        })
        assert set(engine.adapter_keys()) == {"sql", "graph", "vector"}

    def test_tc15_empty_adapters_raises(self):
        """TC15: 빈 adapters 딕셔너리 → ValueError."""
        with pytest.raises(ValueError, match="adapters"):
            MigrationEngine(adapters={})

    def test_tc16_real_sql_adapter(self, sql_real):
        """TC16: SQLiteRealAdapter REAL 어댑터로 엔진 생성."""
        engine = MigrationEngine(adapters={"sql": sql_real})
        assert "sql" in engine.adapter_keys()


# ─────────────────────────────────────────────────────────────────────────────
# D. MigrationEngine.execute()
# ─────────────────────────────────────────────────────────────────────────────

class TestMigrationEngineExecute:
    def test_tc17_execute_single_adapter_success(self, sql_real, simple_migration):
        """TC17: 단일 REAL 어댑터 execute 성공."""
        engine = MigrationEngine(adapters={"sql": sql_real})
        plan = MigrationPlan(
            plan_id="exec_001", migrations=[simple_migration], target_adapters=["sql"]
        )
        record = engine.execute(plan)
        assert record.success is True
        assert record.rolled_back is False
        assert record.error is None

    def test_tc18_execute_returns_execution_record(self, sql_mock, simple_migration):
        """TC18: execute()가 MigrationExecutionRecord 반환."""
        engine = MigrationEngine(adapters={"sql": sql_mock})
        plan = MigrationPlan(
            plan_id="exec_002", migrations=[simple_migration], target_adapters=["sql"]
        )
        record = engine.execute(plan)
        assert isinstance(record, MigrationExecutionRecord)

    def test_tc19_execute_multi_adapter(self, sql_real, graph_mock, simple_migration):
        """TC19: 복수 어댑터 execute (REAL + Mock)."""
        engine = MigrationEngine(adapters={"sql": sql_real, "graph": graph_mock})
        plan = MigrationPlan(
            plan_id="exec_003", migrations=[simple_migration],
            target_adapters=["sql", "graph"]
        )
        record = engine.execute(plan)
        assert record.success is True
        # results에 sql, graph 둘 다 있어야 함
        adapters_in_results = {r["adapter"] for r in record.results}
        assert "sql" in adapters_in_results
        assert "graph" in adapters_in_results

    def test_tc20_execute_results_count(self, sql_real, graph_mock, simple_migration):
        """TC20: results 항목 수 = migrations × adapters."""
        engine = MigrationEngine(adapters={"sql": sql_real, "graph": graph_mock})
        plan = MigrationPlan(
            plan_id="exec_004", migrations=[simple_migration],
            target_adapters=["sql", "graph"]
        )
        record = engine.execute(plan)
        assert len(record.results) == 2  # 1 migration × 2 adapters

    def test_tc21_execute_multi_migrations(self, sql_real, multi_migration):
        """TC21: 복수 마이그레이션 순차 execute."""
        engine = MigrationEngine(adapters={"sql": sql_real})
        plan = MigrationPlan(
            plan_id="exec_005", migrations=multi_migration, target_adapters=["sql"]
        )
        record = engine.execute(plan)
        assert record.success is True
        assert len(record.results) == 2  # 2 migrations × 1 adapter

    def test_tc22_execute_plan_id_in_record(self, sql_mock, simple_migration):
        """TC22: record.plan_id가 plan.plan_id와 일치."""
        engine = MigrationEngine(adapters={"sql": sql_mock})
        plan = MigrationPlan(
            plan_id="my_unique_plan", migrations=[simple_migration], target_adapters=["sql"]
        )
        record = engine.execute(plan)
        assert record.plan_id == "my_unique_plan"

    def test_tc23_execute_executed_at_set(self, sql_mock, simple_migration):
        """TC23: record.executed_at이 ISO 형식 문자열."""
        engine = MigrationEngine(adapters={"sql": sql_mock})
        plan = MigrationPlan(
            plan_id="p_time", migrations=[simple_migration], target_adapters=["sql"]
        )
        record = engine.execute(plan)
        assert isinstance(record.executed_at, str)
        assert "T" in record.executed_at  # ISO 8601 포함

    def test_tc24_unknown_adapter_key_fails(self, sql_mock, simple_migration):
        """TC24: 등록되지 않은 adapter_key → success=False + rolled_back=True."""
        engine = MigrationEngine(adapters={"sql": sql_mock})
        plan = MigrationPlan(
            plan_id="p_unknown", migrations=[simple_migration],
            target_adapters=["nonexistent"]
        )
        record = engine.execute(plan)
        assert record.success is False
        assert record.rolled_back is True

    def test_tc25_invalid_sql_fails_and_rollbacks(self, sql_real):
        """TC25: 잘못된 SQL → success=False, rolled_back=True."""
        bad_mig = Migration(
            migration_id="bad_001",
            backend=BackendType.SQL,
            from_version="0.0.0",
            to_version="9.9.9",
            description="의도적 실패",
            up_script="TOTALLY INVALID SQL !!!",
            down_script="DROP TABLE IF EXISTS bad_tbl",
        )
        engine = MigrationEngine(adapters={"sql": sql_real})
        plan = MigrationPlan(
            plan_id="p_fail", migrations=[bad_mig], target_adapters=["sql"]
        )
        record = engine.execute(plan)
        assert record.success is False
        assert record.rolled_back is True
        assert record.error is not None


# ─────────────────────────────────────────────────────────────────────────────
# E. MigrationEngine.rollback_plan()
# ─────────────────────────────────────────────────────────────────────────────

class TestMigrationEngineRollback:
    def test_tc26_rollback_single_adapter(self, sql_real, simple_migration):
        """TC26: rollback_plan() 단일 어댑터."""
        engine = MigrationEngine(adapters={"sql": sql_real})
        # 먼저 실행
        plan = MigrationPlan(
            plan_id="rb_001", migrations=[simple_migration], target_adapters=["sql"]
        )
        engine.execute(plan)
        # 롤백
        rb_record = engine.rollback_plan(plan)
        assert isinstance(rb_record, MigrationExecutionRecord)
        assert rb_record.rolled_back is True

    def test_tc27_rollback_returns_record(self, sql_mock, simple_migration):
        """TC27: rollback_plan()이 MigrationExecutionRecord 반환."""
        engine = MigrationEngine(adapters={"sql": sql_mock})
        plan = MigrationPlan(
            plan_id="rb_002", migrations=[simple_migration], target_adapters=["sql"]
        )
        record = engine.rollback_plan(plan)
        assert isinstance(record, MigrationExecutionRecord)

    def test_tc28_rollback_success_flag(self, sql_mock, simple_migration):
        """TC28: Mock 어댑터 rollback_plan success=True."""
        engine = MigrationEngine(adapters={"sql": sql_mock})
        plan = MigrationPlan(
            plan_id="rb_003", migrations=[simple_migration], target_adapters=["sql"]
        )
        record = engine.rollback_plan(plan)
        assert record.success is True

    def test_tc29_rollback_plan_id_preserved(self, sql_mock, simple_migration):
        """TC29: rollback_plan record.plan_id 보존."""
        engine = MigrationEngine(adapters={"sql": sql_mock})
        plan = MigrationPlan(
            plan_id="rb_unique_id", migrations=[simple_migration], target_adapters=["sql"]
        )
        record = engine.rollback_plan(plan)
        assert record.plan_id == "rb_unique_id"

    def test_tc30_rollback_multi_migration_order(self, sql_real, multi_migration):
        """TC30: 복수 마이그레이션 rollback_plan 실행 (순서 무관 결과 확인)."""
        engine = MigrationEngine(adapters={"sql": sql_real})
        plan = MigrationPlan(
            plan_id="rb_multi", migrations=multi_migration, target_adapters=["sql"]
        )
        engine.execute(plan)
        rb_record = engine.rollback_plan(plan)
        assert rb_record.rolled_back is True
        assert len(rb_record.results) == 2


# ─────────────────────────────────────────────────────────────────────────────
# F. JSON 직렬화 통합
# ─────────────────────────────────────────────────────────────────────────────

class TestJsonSerialization:
    def test_tc31_execute_record_to_json(self, sql_mock, simple_migration):
        """TC31: execute() 결과 JSON 직렬화."""
        engine = MigrationEngine(adapters={"sql": sql_mock})
        plan = MigrationPlan(
            plan_id="json_001", migrations=[simple_migration], target_adapters=["sql"]
        )
        record = engine.execute(plan)
        json_str = record.to_json()
        data = json.loads(json_str)
        assert data["success"] is True
        assert data["plan_id"] == "json_001"

    def test_tc32_rollback_record_to_json(self, sql_mock, simple_migration):
        """TC32: rollback_plan() 결과 JSON 직렬화."""
        engine = MigrationEngine(adapters={"sql": sql_mock})
        plan = MigrationPlan(
            plan_id="json_002", migrations=[simple_migration], target_adapters=["sql"]
        )
        record = engine.rollback_plan(plan)
        data = json.loads(record.to_json())
        assert data["rolled_back"] is True

    def test_tc33_full_roundtrip(self, sql_real, simple_migration):
        """TC33: REAL 어댑터 execute → to_json → from_json 왕복."""
        engine = MigrationEngine(adapters={"sql": sql_real})
        plan = MigrationPlan(
            plan_id="json_003", migrations=[simple_migration], target_adapters=["sql"]
        )
        record = engine.execute(plan)
        restored = MigrationExecutionRecord.from_json(record.to_json())
        assert restored.success == record.success
        assert restored.plan_id == record.plan_id
        assert restored.error == record.error


# ─────────────────────────────────────────────────────────────────────────────
# G. Gate G42 + Registry
# ─────────────────────────────────────────────────────────────────────────────

class TestGateG42:
    def test_tc34_gate_registry_has_g42(self):
        """TC34: GATE_REGISTRY에 G42 등록 확인."""
        assert "migration_engine_g42" in GATE_REGISTRY

    def test_tc35_gate_registry_g42_adr(self):
        """TC35: G42 ADR = ADR-042."""
        assert GATE_REGISTRY["migration_engine_g42"].adr_ref == "ADR-042"

    def test_tc36_gate_registry_g42_version(self):
        """TC36: G42 버전 = V583."""
        assert GATE_REGISTRY["migration_engine_g42"].version_added == "V583"

    def test_tc37_gate_registry_g42_layer(self):
        """TC37: G42 레이어 = L1."""
        assert GATE_REGISTRY["migration_engine_g42"].layer == "L1"

    def test_tc38_total_gates_41(self):
        """TC38: 전체 Gates 수 41개 (G1~G42, V583 G42 추가)."""
        assert len(GATES) >= 45  # V587: G46 추가로 45개

    def test_tc39_gate_registry_total_41(self):
        """TC39: GATE_REGISTRY 총 41개."""
        assert len(GATE_REGISTRY) >= 45

    def test_tc40_run_release_gate_all_pass(self):
        """TC40: run_release_gate() 전체 41 Gates PASS."""
        from literary_system.gates.release_gate import run_release_gate
        result = run_release_gate()
        assert result["total_gates"] >= 45, (
            f"Gate 수 오류: 기대>=45, 실제={result['total_gates']}"
        )
        assert result["pass"] is True, f"Release Gate FAIL: {result['issues']}"
