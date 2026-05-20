"""
tests/test_v582_sql_real_adapter.py
V582 — SQLiteRealAdapter + LOSDB CLI 테스트 스위트 (ADR-041)

Group A (TC01-08): SQLiteRealAdapter MOCK 모드
Group B (TC09-16): SQLiteRealAdapter REAL :memory: 모드
Group C (TC17-22): 고급 기능 (close, table_exists, 상속 확인)
Group D (TC23-30): LOSDB CLI 명령
Group E (TC31-37): Gate G41 + 전체 41게이트 PASS
"""
from __future__ import annotations

import io
import json
import sys

import pytest

from literary_system.db import (
    BackendType,
    BaseMigrationAdapter,
    Migration,
    SchemaRegistry,
    SQLiteRealAdapter,
)
from literary_system.db.cli import build_parser, main

# ── 공통 픽스처 ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_schema_registry():
    """각 테스트 전 SchemaRegistry 초기화."""
    SchemaRegistry.reset()
    yield
    SchemaRegistry.reset()


def _make_migration(
    version: str = "1.0.0",
    mid: str = "test_001",
    up: str = "",
    down: str = "",
) -> Migration:
    return Migration(
        migration_id=mid,
        backend=BackendType.SQL,
        from_version="0.0.0",
        to_version=version,
        description=f"테스트 마이그레이션 → {version}",
        up_script=up,
        down_script=down,
    )


def _capture_main(argv: list) -> tuple[int, str, str]:
    """main() 실행 후 (returncode, stdout, stderr) 반환."""
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    try:
        rc = main(argv)
        out = sys.stdout.getvalue()
        err = sys.stderr.getvalue()
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return rc, out, err


# ═══════════════════════════════════════════════════════════════════════════════
# Group A — MOCK 모드
# ═══════════════════════════════════════════════════════════════════════════════

class TestGroupA_Mock:
    """TC01-08: SQLiteRealAdapter MOCK 모드."""

    def test_tc01_instantiate_mock(self):
        """TC01: MOCK=True 기본 생성."""
        a = SQLiteRealAdapter(mock=True)
        assert a.mock is True

    def test_tc02_check_connection_mock(self):
        """TC02: MOCK check_connection → True."""
        a = SQLiteRealAdapter(mock=True)
        assert a.check_connection() is True

    def test_tc03_apply_mock(self):
        """TC03: MOCK apply → True."""
        a = SQLiteRealAdapter(mock=True)
        mig = _make_migration()
        assert a.apply(mig) is True

    def test_tc04_rollback_mock(self):
        """TC04: MOCK rollback → True."""
        a = SQLiteRealAdapter(mock=True)
        mig = _make_migration()
        assert a.rollback(mig) is True

    def test_tc05_list_applied_mock_empty(self):
        """TC05: MOCK list_applied → []."""
        a = SQLiteRealAdapter(mock=True)
        assert a.list_applied() == []

    def test_tc06_table_exists_mock_false(self):
        """TC06: MOCK table_exists → False."""
        a = SQLiteRealAdapter(mock=True)
        assert a.table_exists("anything") is False

    def test_tc07_schema_info_mock(self):
        """TC07: schema_info mock=True 반영."""
        a = SQLiteRealAdapter(mock=True)
        info = a.schema_info()
        assert info["mock"] is True
        assert info["adapter"] == "SQLiteRealAdapter"
        assert info["adr"] == "ADR-041"

    def test_tc08_inherits_base(self):
        """TC08: BaseMigrationAdapter 상속 확인."""
        a = SQLiteRealAdapter(mock=True)
        assert isinstance(a, BaseMigrationAdapter)


# ═══════════════════════════════════════════════════════════════════════════════
# Group B — REAL :memory: 모드
# ═══════════════════════════════════════════════════════════════════════════════

class TestGroupB_Real:
    """TC09-16: SQLiteRealAdapter REAL :memory: 모드."""

    def test_tc09_instantiate_real(self):
        """TC09: REAL 모드 생성."""
        a = SQLiteRealAdapter(connection_url="sqlite:///:memory:", mock=False)
        assert a.mock is False
        assert a._db_path == ":memory:"

    def test_tc10_check_connection_real(self):
        """TC10: REAL check_connection → True."""
        a = SQLiteRealAdapter(connection_url="sqlite:///:memory:", mock=False)
        assert a.check_connection() is True

    def test_tc11_apply_real(self):
        """TC11: REAL apply → True, 이력 기록."""
        a = SQLiteRealAdapter(connection_url="sqlite:///:memory:", mock=False)
        mig = _make_migration(
            version="2.0.0",
            mid="tc11_test",
            up="CREATE TABLE IF NOT EXISTS tc11_tbl (id INTEGER PRIMARY KEY)",
        )
        ok = a.apply(mig)
        assert ok is True

    def test_tc12_list_applied_real(self):
        """TC12: REAL apply 후 list_applied에서 버전 확인."""
        a = SQLiteRealAdapter(connection_url="sqlite:///:memory:", mock=False)
        mig = _make_migration(version="1.5.0", mid="tc12_test")
        a.apply(mig)
        rows = a.list_applied()
        assert len(rows) >= 1
        versions = [r["version"] for r in rows]
        assert "1.5.0" in versions

    def test_tc13_rollback_real(self):
        """TC13: REAL rollback → True."""
        a = SQLiteRealAdapter(connection_url="sqlite:///:memory:", mock=False)
        mig = _make_migration(version="3.0.0", mid="tc13_test")
        a.apply(mig)
        ok = a.rollback(mig)
        assert ok is True

    def test_tc14_schema_registry_updated(self):
        """TC14: REAL apply 후 SchemaRegistry 버전 갱신 확인."""
        a = SQLiteRealAdapter(connection_url="sqlite:///:memory:", mock=False)
        mig = _make_migration(version="4.2.1", mid="tc14_test")
        a.apply(mig)
        reg = SchemaRegistry.get_instance()
        versions = reg.all_versions()
        assert "sql" in versions
        ver_str = versions["sql"]["version"]
        parts = ver_str.split(".")
        assert parts[0] == "4"
        assert parts[1] == "2"
        assert parts[2] == "1"

    def test_tc15_table_exists_real(self):
        """TC15: REAL apply 후 테이블 존재 확인."""
        a = SQLiteRealAdapter(connection_url="sqlite:///:memory:", mock=False)
        mig = _make_migration(
            version="1.0.0",
            mid="tc15_test",
            up="CREATE TABLE IF NOT EXISTS tc15_check (id INTEGER PRIMARY KEY)",
        )
        a.apply(mig)
        assert a.table_exists("tc15_check") is True
        assert a.table_exists("no_such_table") is False

    def test_tc16_migration_table_created(self):
        """TC16: apply 호출 후 losdb_migrations 테이블 생성 확인."""
        a = SQLiteRealAdapter(connection_url="sqlite:///:memory:", mock=False)
        mig = _make_migration()
        a.apply(mig)
        assert a.table_exists("losdb_migrations") is True


# ═══════════════════════════════════════════════════════════════════════════════
# Group C — 고급 기능
# ═══════════════════════════════════════════════════════════════════════════════

class TestGroupC_Advanced:
    """TC17-22: 고급 기능."""

    def test_tc17_close_reopen(self):
        """TC17: close 후 재연결 가능."""
        a = SQLiteRealAdapter(connection_url="sqlite:///:memory:", mock=False)
        a.check_connection()
        a.close()
        assert a._conn is None
        assert a.check_connection() is True

    def test_tc18_parse_path_memory(self):
        """TC18: :memory: URL 파싱."""
        assert SQLiteRealAdapter._parse_path("sqlite:///:memory:") == ":memory:"
        assert SQLiteRealAdapter._parse_path("") == ":memory:"

    def test_tc19_parse_path_file(self):
        """TC19: 파일 경로 URL 파싱."""
        path = SQLiteRealAdapter._parse_path("sqlite:///tmp/test.db")
        assert path == "tmp/test.db"

    def test_tc20_repr(self):
        """TC20: __repr__ 정상 출력."""
        a = SQLiteRealAdapter(mock=True)
        r = repr(a)
        assert "SQLiteRealAdapter" in r
        assert "mock=True" in r

    def test_tc21_multiple_migrations(self):
        """TC21: 연속 apply → list_applied 순서 보장."""
        a = SQLiteRealAdapter(connection_url="sqlite:///:memory:", mock=False)
        for ver in ["1.0.0", "1.1.0", "1.2.0"]:
            SchemaRegistry.reset()
            mig = _make_migration(version=ver, mid=f"multi_{ver}")
            assert a.apply(mig) is True
        rows = a.list_applied()
        applied_versions = [r["version"] for r in rows]
        assert "1.0.0" in applied_versions
        assert "1.1.0" in applied_versions
        assert "1.2.0" in applied_versions

    def test_tc22_schema_info_real(self):
        """TC22: schema_info REAL 모드 정보."""
        a = SQLiteRealAdapter(connection_url="sqlite:///:memory:", mock=False)
        info = a.schema_info()
        assert info["mock"] is False
        assert info["db_path"] == ":memory:"
        assert info["version"] == "V582"


# ═══════════════════════════════════════════════════════════════════════════════
# Group D — LOSDB CLI
# ═══════════════════════════════════════════════════════════════════════════════

class TestGroupD_CLI:
    """TC23-30: LOSDB CLI 명령."""

    def test_tc23_parser_build(self):
        """TC23: build_parser 반환 확인."""
        parser = build_parser()
        assert parser is not None
        assert parser.prog == "losdb"

    def test_tc24_cli_no_args(self):
        """TC24: 인수 없으면 help 출력 후 0 반환."""
        rc, out, err = _capture_main([])
        assert rc == 0

    def test_tc25_cli_status(self):
        """TC25: losdb status 실행."""
        rc, out, err = _capture_main(["status"])
        assert rc == 0
        assert "LOSDB Status" in out

    def test_tc26_cli_status_json(self):
        """TC26: losdb --json status → JSON 출력."""
        rc, out, err = _capture_main(["--json", "status"])
        assert rc == 0
        data = json.loads(out)
        assert data.get("command") == "status"
        assert "schema_versions" in data

    def test_tc27_cli_analyze_json(self):
        """TC27: losdb --json analyze → JSON 출력."""
        rc, out, err = _capture_main(["--json", "analyze"])
        assert rc == 0
        data = json.loads(out)
        assert data.get("command") == "analyze"
        assert "migration_history" in data

    def test_tc28_cli_health(self):
        """TC28: losdb health 실행."""
        rc, out, err = _capture_main(["health"])
        assert rc == 0
        assert "Health" in out

    def test_tc29_cli_migrate(self):
        """TC29: losdb migrate 1.0.0 실행."""
        rc, out, err = _capture_main(["migrate", "1.0.0"])
        assert rc == 0
        assert "Migrate" in out

    def test_tc30_cli_migrate_json(self):
        """TC30: losdb --json migrate 2.0.0 → JSON."""
        rc, out, err = _capture_main(["--json", "migrate", "2.0.0"])
        assert rc == 0
        data = json.loads(out)
        assert data["command"] == "migrate"
        assert data["target_version"] == "2.0.0"
        assert data["success"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# Group E — Gate G41 + 전체 PASS
# ═══════════════════════════════════════════════════════════════════════════════

class TestGroupE_Gates:
    """TC31-37: Gate G41 + 전체 41게이트 PASS."""

    def test_tc31_gate_g41_pass(self):
        """TC31: Gate G41 단독 PASS."""
        from literary_system.gates.release_gate import _gate_sql_real_adapter_g41
        result = _gate_sql_real_adapter_g41()
        assert result["pass"] is True, f"G41 FAIL: {result.get('details', result)}"

    def test_tc32_gate_registry_has_g41(self):
        """TC32: GATE_REGISTRY에 sql_real_adapter_g41 등록 확인."""
        from literary_system.gates.gate_registry import GATE_REGISTRY
        assert "sql_real_adapter_g41" in GATE_REGISTRY

    def test_tc33_gate_registry_g41_meta(self):
        """TC33: G41 메타 (ADR-041, V582, L1) 확인."""
        from literary_system.gates.gate_registry import GATE_REGISTRY
        entry = GATE_REGISTRY["sql_real_adapter_g41"]
        assert entry.adr_ref == "ADR-041"
        assert entry.version_added == "V582"
        assert entry.layer == "L1"

    def test_tc34_gate_registry_has_g40(self):
        """TC34: GATE_REGISTRY에 db_migration_g40 등록 확인."""
        from literary_system.gates.gate_registry import GATE_REGISTRY
        assert "db_migration_g40" in GATE_REGISTRY

    def test_tc35_total_gate_count(self):
        """TC35: 전체 게이트 수 41개 확인."""
        from literary_system.gates.gate_registry import GATE_REGISTRY
        assert len(GATE_REGISTRY) == 44, f"게이트 수: {len(GATE_REGISTRY)}"  # V583: G42 추가로 41개

    def test_tc36_gates_list_has_g41(self):
        """TC36: GATES 리스트에 sql_real_adapter_g41 포함 확인."""
        from literary_system.gates.release_gate import GATES
        gate_ids = {g[0] for g in GATES}
        assert "sql_real_adapter_g41" in gate_ids

    def test_tc37_run_release_gate_41_pass(self):
        """TC37: run_release_gate() 총 41게이트 PASS."""
        from literary_system.gates.release_gate import run_release_gate
        result = run_release_gate()
        total = result.get("total_gates", 0)
        passed = result.get("gates_passed", 0)
        issues = result.get("issues", [])
        assert total == 44, f"총 게이트 수 기대 41, 실제 {total}"  # V583: G42 추가로 41개
        assert passed == 44, (
            f"PASS 기대 41, 실제 {passed}. "
            f"FAIL 게이트: {issues}"
        )  # V583: G42 추가로 41개
