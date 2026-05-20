"""tests/test_v584_vector_real_adapter.py — V584 VectorRealAdapter 테스트 (TC01~TC40).

ADR-043 | V584 | Gate G43
"""
from __future__ import annotations

import json
import math
import os
import tempfile
from typing import List

import pytest

from literary_system.db.migration_manager import Migration
from literary_system.db.schema_registry import BackendType
from literary_system.db.vector_real_adapter import (
    HAS_NUMPY,
    VectorRealAdapter,
    VectorRecord,
    _cosine_similarity,
    _l2_distance,
)
from literary_system.gates.gate_registry import GATE_REGISTRY
from literary_system.gates.release_gate import GATES

# ─────────────────────────────────────────────────────────────────────────────
# 공통 fixture
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def adapter4():
    return VectorRealAdapter(dim=4)


@pytest.fixture
def adapter2():
    return VectorRealAdapter(dim=2)


@pytest.fixture
def migration_upsert():
    return Migration(
        migration_id="V584_test_upsert",
        backend=BackendType.VECTOR,
        from_version="0.0.0",
        to_version="1.0.0",
        description="test upsert",
        vector_ops=[
            {"op": "upsert", "id": "m1", "vector": [1.0, 0.0, 0.0, 0.0]},
            {"op": "upsert", "id": "m2", "vector": [0.0, 1.0, 0.0, 0.0]},
        ],
    )


@pytest.fixture
def migration_no_ops():
    return Migration(
        migration_id="V584_no_ops",
        backend=BackendType.VECTOR,
        from_version="0.0.0",
        to_version="1.0.0",
    )


# ─────────────────────────────────────────────────────────────────────────────
# TC01~TC05: 생성 + 기본 속성
# ─────────────────────────────────────────────────────────────────────────────

class TestVectorRealAdapterInit:
    def test_tc01_create_default(self):
        a = VectorRealAdapter(dim=4)
        assert a.count() == 0

    def test_tc02_create_with_metric_l2(self):
        a = VectorRealAdapter(dim=3, metric="l2")
        assert a.count() == 0

    def test_tc03_invalid_dim_raises(self):
        with pytest.raises(ValueError):
            VectorRealAdapter(dim=0)

    def test_tc04_invalid_metric_raises(self):
        with pytest.raises(ValueError):
            VectorRealAdapter(dim=4, metric="manhattan")

    def test_tc05_check_connection(self, adapter4):
        assert adapter4.check_connection() is True


# ─────────────────────────────────────────────────────────────────────────────
# TC06~TC12: upsert / get / delete / count
# ─────────────────────────────────────────────────────────────────────────────

class TestCRUD:
    def test_tc06_upsert_single(self, adapter4):
        adapter4.upsert("v1", [1.0, 0.0, 0.0, 0.0])
        assert adapter4.count() == 1

    def test_tc07_upsert_multiple(self, adapter4):
        adapter4.upsert("v1", [1.0, 0.0, 0.0, 0.0])
        adapter4.upsert("v2", [0.0, 1.0, 0.0, 0.0])
        assert adapter4.count() == 2

    def test_tc08_upsert_overwrite(self, adapter4):
        adapter4.upsert("v1", [1.0, 0.0, 0.0, 0.0])
        adapter4.upsert("v1", [0.5, 0.5, 0.0, 0.0])
        assert adapter4.count() == 1
        assert adapter4.get("v1").vector == [0.5, 0.5, 0.0, 0.0]

    def test_tc09_get_existing(self, adapter4):
        adapter4.upsert("v1", [1.0, 0.0, 0.0, 0.0], metadata={"src": "test"})
        rec = adapter4.get("v1")
        assert rec is not None
        assert rec.id == "v1"
        assert rec.metadata == {"src": "test"}

    def test_tc10_get_missing(self, adapter4):
        assert adapter4.get("nonexistent") is None

    def test_tc11_delete_existing(self, adapter4):
        adapter4.upsert("v1", [1.0, 0.0, 0.0, 0.0])
        result = adapter4.delete("v1")
        assert result is True
        assert adapter4.count() == 0

    def test_tc12_delete_missing(self, adapter4):
        result = adapter4.delete("nonexistent")
        assert result is False

    def test_tc12b_upsert_dim_mismatch(self, adapter4):
        with pytest.raises(ValueError):
            adapter4.upsert("bad", [1.0, 2.0])  # dim=2, adapter dim=4


# ─────────────────────────────────────────────────────────────────────────────
# TC13~TC20: search
# ─────────────────────────────────────────────────────────────────────────────

class TestSearch:
    def test_tc13_search_cosine_top1(self, adapter4):
        adapter4.upsert("v1", [1.0, 0.0, 0.0, 0.0])
        adapter4.upsert("v2", [0.0, 1.0, 0.0, 0.0])
        results = adapter4.search([1.0, 0.0, 0.0, 0.0], top_k=1)
        assert len(results) == 1
        assert results[0][0] == "v1"

    def test_tc14_search_cosine_returns_scores(self, adapter4):
        adapter4.upsert("v1", [1.0, 0.0, 0.0, 0.0])
        results = adapter4.search([1.0, 0.0, 0.0, 0.0], top_k=1)
        assert abs(results[0][1] - 1.0) < 1e-6

    def test_tc15_search_l2_top1(self, adapter4):
        adapter4.upsert("near", [1.0, 0.0, 0.0, 0.0])
        adapter4.upsert("far",  [10.0, 10.0, 10.0, 10.0])
        results = adapter4.search([1.0, 0.0, 0.0, 0.0], top_k=1, metric="l2")
        assert results[0][0] == "near"

    def test_tc16_search_topk_limit(self, adapter4):
        for i in range(5):
            adapter4.upsert(f"v{i}", [float(i), 0.0, 0.0, 0.0])
        results = adapter4.search([1.0, 0.0, 0.0, 0.0], top_k=3)
        assert len(results) == 3

    def test_tc17_search_empty_store(self, adapter4):
        results = adapter4.search([1.0, 0.0, 0.0, 0.0])
        assert results == []

    def test_tc18_search_dim_mismatch(self, adapter4):
        adapter4.upsert("v1", [1.0, 0.0, 0.0, 0.0])
        with pytest.raises(ValueError):
            adapter4.search([1.0, 0.0])  # dim=2 != 4

    def test_tc19_search_invalid_metric(self, adapter4):
        adapter4.upsert("v1", [1.0, 0.0, 0.0, 0.0])
        with pytest.raises(ValueError):
            adapter4.search([1.0, 0.0, 0.0, 0.0], metric="dot")

    def test_tc20_search_with_metadata(self, adapter4):
        adapter4.upsert("v1", [1.0, 0.0, 0.0, 0.0], metadata={"label": "A"})
        adapter4.upsert("v2", [0.0, 1.0, 0.0, 0.0], metadata={"label": "B"})
        results = adapter4.search([1.0, 0.0, 0.0, 0.0], top_k=1)
        rec = adapter4.get(results[0][0])
        assert rec.metadata["label"] == "A"


# ─────────────────────────────────────────────────────────────────────────────
# TC21~TC26: 유사도 함수
# ─────────────────────────────────────────────────────────────────────────────

class TestSimilarityFunctions:
    def test_tc21_cosine_same_vector(self):
        score = _cosine_similarity([1.0, 0.0, 0.0], [1.0, 0.0, 0.0])
        assert abs(score - 1.0) < 1e-6

    def test_tc22_cosine_perpendicular(self):
        score = _cosine_similarity([1.0, 0.0], [0.0, 1.0])
        assert abs(score) < 1e-6

    def test_tc23_cosine_opposite(self):
        score = _cosine_similarity([1.0, 0.0], [-1.0, 0.0])
        assert abs(score - (-1.0)) < 1e-6

    def test_tc24_l2_known_distance(self):
        d = _l2_distance([0.0, 0.0], [3.0, 4.0])
        assert abs(d - 5.0) < 1e-6

    def test_tc25_l2_same_point(self):
        d = _l2_distance([1.0, 2.0], [1.0, 2.0])
        assert abs(d) < 1e-10

    def test_tc26_cosine_zero_vector(self):
        score = _cosine_similarity([0.0, 0.0], [1.0, 0.0])
        assert score == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# TC27~TC29: JSON 영속화
# ─────────────────────────────────────────────────────────────────────────────

class TestPersistence:
    def test_tc27_save_and_load(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            a = VectorRealAdapter(dim=3, path=path)
            a.upsert("x1", [1.0, 0.0, 0.0])
            a.upsert("x2", [0.0, 1.0, 0.0])
            a.save()
            b = VectorRealAdapter(dim=3, path=path)
            b.load()
            assert b.count() == 2
            assert b.get("x1") is not None
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_tc28_load_nonexistent_path(self):
        a = VectorRealAdapter(dim=3, path="/tmp/nonexistent_v584_test.json")
        a.load()  # 예외 없이 통과 (파일 없으면 무시)
        assert a.count() == 0

    def test_tc29_save_no_path(self, adapter4):
        adapter4.upsert("v1", [1.0, 0.0, 0.0, 0.0])
        adapter4.save()  # path=None 이면 예외 없이 스킵
        assert adapter4.count() == 1

    def test_tc29b_load_dim_mismatch(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w') as f:
            json.dump({"dim": 10, "metric": "cosine", "records": {}}, f)
            path = f.name
        try:
            a = VectorRealAdapter(dim=3, path=path)
            with pytest.raises(ValueError):
                a.load()
        finally:
            os.unlink(path)


# ─────────────────────────────────────────────────────────────────────────────
# TC30~TC34: apply / rollback
# ─────────────────────────────────────────────────────────────────────────────

class TestApplyRollback:
    def test_tc30_apply_vector_ops(self, adapter4, migration_upsert):
        result = adapter4.apply(migration_upsert)
        assert result is True
        assert adapter4.count() == 2
        assert adapter4.get("m1") is not None

    def test_tc31_apply_no_ops(self, adapter4, migration_no_ops):
        result = adapter4.apply(migration_no_ops)
        assert result is True
        assert adapter4.count() == 0

    def test_tc32_apply_delete_op(self, adapter4):
        adapter4.upsert("to_del", [1.0, 0.0, 0.0, 0.0])
        m = Migration(
            migration_id="del_test",
            backend=BackendType.VECTOR,
            from_version="0.0.0",
            to_version="1.0.0",
            vector_ops=[{"op": "delete", "id": "to_del"}],
        )
        result = adapter4.apply(m)
        assert result is True
        assert adapter4.get("to_del") is None

    def test_tc33_rollback_restores_state(self, adapter4, migration_upsert):
        adapter4.upsert("pre_existing", [1.0, 0.0, 0.0, 0.0])
        adapter4.apply(migration_upsert)
        assert adapter4.count() == 3  # pre_existing + m1 + m2
        adapter4.rollback(migration_upsert)
        # rollback → apply 이전 상태 복원
        assert adapter4.get("m1") is None
        assert adapter4.get("m2") is None
        assert adapter4.get("pre_existing") is not None

    def test_tc34_apply_invalid_op_returns_false(self, adapter4):
        m = Migration(
            migration_id="bad_op",
            backend=BackendType.VECTOR,
            from_version="0.0.0",
            to_version="1.0.0",
            vector_ops=[{"op": "unknown_op", "id": "x"}],
        )
        result = adapter4.apply(m)
        assert result is False
        # 자동 롤백 확인 (apply 전 상태 유지)
        assert adapter4.count() == 0

    def test_tc34b_mock_mode_apply(self):
        a = VectorRealAdapter(dim=4, mock=True)
        m = Migration(
            migration_id="mock_test",
            backend=BackendType.VECTOR,
            from_version="0.0.0",
            to_version="1.0.0",
        )
        assert a.apply(m) is True
        assert a.rollback(m) is True
        assert a.count() == 0  # mock 모드라 실제 적용 없음


# ─────────────────────────────────────────────────────────────────────────────
# TC35~TC37: GATE_REGISTRY G43 속성
# ─────────────────────────────────────────────────────────────────────────────

class TestGateRegistry:
    def test_tc35_gate_registry_g43_adr(self):
        assert GATE_REGISTRY["vector_real_adapter_g43"].adr_ref == "ADR-043"

    def test_tc36_gate_registry_g43_version(self):
        assert GATE_REGISTRY["vector_real_adapter_g43"].version_added == "V584"

    def test_tc37_gate_registry_g43_layer(self):
        assert GATE_REGISTRY["vector_real_adapter_g43"].layer == "L1"


# ─────────────────────────────────────────────────────────────────────────────
# TC38~TC40: Gate 카운트 및 Release Gate 실행
# ─────────────────────────────────────────────────────────────────────────────

class TestGateG43:
    def test_tc38_gates_count(self):
        assert len(GATES) == 43

    def test_tc39_gate_registry_count(self):
        assert len(GATE_REGISTRY) == 43

    def test_tc40_run_release_gate_all_pass(self):
        from literary_system.gates.release_gate import run_release_gate
        result = run_release_gate()
        assert result["total_gates"] == 43
        assert result["pass"] is True
