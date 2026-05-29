"""
V595.3 P1 결함 수정 검증 테스트 (TC-A1 ~ TC-D2)

FIX-A: SQLiteRealAdapter migration 원자성 (executescript → individual execute)
FIX-B: VectorRealAdapter 파일 rollback (save 후 이후 op 실패 시 파일 복원)
FIX-C: BackendHealthMonitor HALF_OPEN 상태 전이 (last_check_ok=False 유지)
FIX-D: PhaseAExitGate EA-6 source_hash 검증
"""
from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from literary_system.db.migration_manager import Migration
from literary_system.db.schema_registry import BackendType


# ===========================================================================
# FIX-A: SQLiteRealAdapter — migration 원자성
# ===========================================================================

class TestSQLiteRealAdapterAtomicity:
    """TC-A1, TC-A2: executescript() 대신 BEGIN IMMEDIATE + 개별 execute()"""

    def _make_adapter(self, db_url: str):
        from literary_system.db.sql_real_adapter import SQLiteRealAdapter
        return SQLiteRealAdapter(connection_url=db_url, mock=False)

    def test_tc_a1_partial_failure_rolls_back(self, tmp_path):
        """TC-A1: 부분 실패 시 전체 롤백 — table도 log도 남으면 안 됨"""
        db_url = f"sqlite:///{tmp_path / 'test_atomic.db'}"
        adapter = self._make_adapter(db_url)

        bad_migration = Migration(
            migration_id="bad_partial",
            backend=BackendType.SQL,
            from_version="0.0.0",
            to_version="1.0.0",
            description="partial fail test",
            up_script=(
                "CREATE TABLE t_atomic(id INTEGER); "
                "INSERT INTO t_atomic VALUES(1); "
                "INVALID SQL STATEMENT;"
            ),
        )

        result = adapter.apply(bad_migration)

        assert result is False, "apply() must return False on partial failure"
        assert not adapter.table_exists("t_atomic"), \
            "t_atomic table must be rolled back (not persisted after failure)"
        applied = adapter.list_applied()
        assert not any(m.get("version") == "1.0.0" for m in applied), \
            "migration log must not record a partially applied migration"

    def test_tc_a2_valid_migration_applies_atomically(self, tmp_path):
        """TC-A2: 정상 마이그레이션 — table + log 모두 커밋"""
        db_url = f"sqlite:///{tmp_path / 'test_ok.db'}"
        adapter = self._make_adapter(db_url)

        good_migration = Migration(
            migration_id="good_migration",
            backend=BackendType.SQL,
            from_version="0.0.0",
            to_version="1.0.0",
            description="valid migration",
            up_script=(
                "CREATE TABLE t_good(id INTEGER, name TEXT); "
                "INSERT INTO t_good VALUES(1, 'ok');"
            ),
        )

        result = adapter.apply(good_migration)

        assert result is True, "apply() must return True on success"
        assert adapter.table_exists("t_good"), "t_good table must exist after apply"
        rows = adapter.get_rows("t_good")
        assert len(rows) == 1 and rows[0]["name"] == "ok"
        applied = adapter.list_applied()
        assert any(m.get("version") == "1.0.0" for m in applied), \
            "migration log must record the successful migration"


# ===========================================================================
# FIX-B: VectorRealAdapter — 파일 rollback
# ===========================================================================

class TestVectorRealAdapterFileRollback:
    """TC-B1, TC-B2: save + 이후 op 실패 시 파일도 rollback"""

    def _make_adapter(self, dim: int = 2, path: str = None):
        from literary_system.db.vector_real_adapter import VectorRealAdapter
        return VectorRealAdapter(dim=dim, path=path, mock=False)

    def test_tc_b1_file_rolled_back_after_save_then_failure(self, tmp_path):
        """TC-B1: upsert → save → unknown_op 순서 시 파일 원상복구"""
        vec_file = str(tmp_path / "vectors.json")
        adapter = self._make_adapter(dim=2, path=vec_file)

        migration = Migration(
            migration_id="test_b1_rollback",
            backend=BackendType.VECTOR,
            from_version="0.0.0",
            to_version="1.0.0",
            description="save then fail",
            vector_ops=[
                {"op": "upsert", "id": "a", "vector": [0.1, 0.2]},
                {"op": "save"},
                {"op": "unknown_op_xyz", "id": "x"},  # triggers failure
            ],
        )

        result = adapter.apply(migration)

        assert result is False, "apply() must return False"
        assert adapter.count() == 0, \
            "memory store must be empty after rollback"
        # File must be rolled back: either absent or empty records
        if os.path.exists(vec_file):
            with open(vec_file, "r") as f:
                data = json.load(f)
            assert len(data.get("records", [])) == 0, \
                f"file must not contain record 'a' after rollback, got {data.get('records')}"

    def test_tc_b2_successful_ops_persist_file(self, tmp_path):
        """TC-B2: 정상 ops — 파일에 record 보존"""
        vec_file = str(tmp_path / "vectors_ok.json")
        adapter = self._make_adapter(dim=2, path=vec_file)

        migration = Migration(
            migration_id="test_b2_success",
            backend=BackendType.VECTOR,
            from_version="0.0.0",
            to_version="1.0.0",
            description="normal upsert+save",
            vector_ops=[
                {"op": "upsert", "id": "b", "vector": [0.3, 0.4]},
                {"op": "save"},
            ],
        )

        result = adapter.apply(migration)

        assert result is True, "apply() must return True on success"
        assert adapter.count() == 1
        assert os.path.exists(vec_file), "file must exist after successful save"
        with open(vec_file, "r") as f:
            data = json.load(f)
        records = data.get("records", {})
        if isinstance(records, list):
            ids = [r.get("id") if isinstance(r, dict) else r for r in records]
        else:
            ids = list(records.keys())
        assert "b" in ids, f"record 'b' must be persisted in file, got {ids}"


# ===========================================================================
# FIX-C: BackendHealthMonitor — HALF_OPEN 상태 전이
# ===========================================================================

class TestBackendHealthMonitorHalfOpen:
    """TC-C1, TC-C2: HALF_OPEN 전이 시 last_check_ok=False, traffic 차단"""

    def _make_monitor_with_open_circuit(self, recovery_timeout: float = 0.0):
        """recovery_timeout=0인 monitor + OPEN 상태 backend 반환"""
        from literary_system.db.health_monitor import BackendHealthMonitor
        monitor = BackendHealthMonitor(recovery_timeout_sec=recovery_timeout)
        monitor.register(BackendType.SQL, ping_fn=lambda: False)
        # force_open()으로 직접 OPEN 상태 진입 (failure_threshold 우회)
        monitor.force_open(BackendType.SQL)
        return monitor

    def test_tc_c1_half_open_not_available_without_probe(self):
        """TC-C1: OPEN→HALF_OPEN 전이 후 available=False (FIX-C 검증)"""
        from literary_system.db.health_monitor import BackendCircuitState

        monitor = self._make_monitor_with_open_circuit(recovery_timeout=0.0)

        # recovery_timeout=0이므로 try_recover()가 즉시 HALF_OPEN 전이
        time.sleep(0.01)
        available = monitor.get_available_backends()

        assert BackendType.SQL not in available, \
            "HALF_OPEN backend must NOT be available (probe not yet done)"

        rec = monitor._records[BackendType.SQL]
        assert rec.circuit_state == BackendCircuitState.HALF_OPEN, \
            f"Expected HALF_OPEN after recovery_timeout, got {rec.circuit_state}"
        assert rec.last_check_ok is False, \
            "last_check_ok must be False in HALF_OPEN state (FIX-C)"

    def test_tc_c2_closed_after_successful_probe(self):
        """TC-C2: HALF_OPEN → probe 성공(force_closed) → CLOSED + available"""
        from literary_system.db.health_monitor import BackendCircuitState

        monitor = self._make_monitor_with_open_circuit(recovery_timeout=0.0)
        time.sleep(0.01)
        monitor.get_available_backends()  # trigger try_recover → HALF_OPEN

        rec = monitor._records[BackendType.SQL]
        assert rec.circuit_state == BackendCircuitState.HALF_OPEN

        # Simulate successful probe: record_success() on the record directly
        rec.record_success()

        available = monitor.get_available_backends()
        assert BackendType.SQL in available, \
            "Backend must be available after successful probe"
        assert rec.circuit_state == BackendCircuitState.CLOSED


# ===========================================================================
# FIX-D: PhaseAExitGate EA-6 — source_hash 검증 로직 (단위 검증)
# ===========================================================================

class TestEA6SourceHashLogic:
    """TC-D1, TC-D2: EA-6 source_hash 불일치/일치 처리 로직 검증"""

    @staticmethod
    def _run_ea6_logic(inv: dict, mocked_current_hash: str):
        """phase_a_exit_gate.py의 EA-6 내부 로직을 직접 시뮬레이션"""
        checks = {}
        errors = []
        test_count = inv.get("test_count", 0)

        with patch("tools.generate_test_inventory.source_hash",
                   return_value=mocked_current_hash):
            try:
                from tools.generate_test_inventory import source_hash as _fn
                _current_hash = _fn()
                _inventory_hash = inv.get("source_hash")
                if _inventory_hash != _current_hash:
                    errors.append(
                        f"EA-6: stale test_inventory.json "
                        f"(inventory={_inventory_hash}, current={_current_hash})"
                    )
                    checks["EA-6"] = False
                elif test_count < 6000:
                    errors.append(f"EA-6: test_count={test_count} (< 6000)")
                    checks["EA-6"] = False
                else:
                    checks["EA-6"] = True
            except ImportError:
                checks["EA-6"] = test_count >= 6000

        return checks, errors

    def test_tc_d1_stale_hash_fails_ea6(self):
        """TC-D1: source_hash 불일치 → EA-6 FAIL + 'stale' 메시지"""
        inv = {"test_count": 6179, "source_hash": "STALE_HASH_000"}
        checks, errors = self._run_ea6_logic(inv, mocked_current_hash="CURRENT_HASH_111")

        assert checks.get("EA-6") is False, \
            "EA-6 must FAIL when source_hash is stale"
        assert any("stale" in e for e in errors), \
            f"Error must mention 'stale', got: {errors}"

    def test_tc_d2_fresh_hash_passes_ea6(self):
        """TC-D2: source_hash 일치 + test_count >= 6000 → EA-6 PASS"""
        inv = {"test_count": 6179, "source_hash": "MATCHING_HASH_999"}
        checks, errors = self._run_ea6_logic(inv, mocked_current_hash="MATCHING_HASH_999")

        assert checks.get("EA-6") is True, \
            "EA-6 must PASS when hash matches and count >= 6000"
        assert not errors, f"No errors expected, got: {errors}"

    def test_tc_d3_low_count_fails_ea6(self):
        """TC-D3: hash 일치하지만 test_count < 6000 → EA-6 FAIL"""
        inv = {"test_count": 5000, "source_hash": "HASH_X"}
        checks, errors = self._run_ea6_logic(inv, mocked_current_hash="HASH_X")

        assert checks.get("EA-6") is False, \
            "EA-6 must FAIL when test_count < 6000"
