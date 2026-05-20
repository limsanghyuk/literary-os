"""V586 테스트 — LOSDBClient (ADR-045, Gate G45).

44개 테스트:
  TC01~TC08  LOSDBClientRecord
  TC09~TC20  LOSDBClient 기본 동작
  TC21~TC27  query_by_label (SQL/Vector/Graph)
  TC28~TC33  cross_query
  TC34~TC38  check_all_connections / schema_info
  TC39~TC44  Gate G45 + GATE_REGISTRY
"""
from __future__ import annotations

import pytest
from literary_system.db.losdb_client import LOSDBClient, LOSDBClientRecord
from literary_system.db.schema_registry import BackendType
from literary_system.db.graph_real_adapter import GraphRealAdapter
from literary_system.db.vector_real_adapter import VectorRealAdapter
from literary_system.db.sql_real_adapter import SQLiteRealAdapter


# ---------------------------------------------------------------------------
# TC01~TC08 — LOSDBClientRecord
# ---------------------------------------------------------------------------

class TestLOSDBClientRecord:
    def test_tc01_basic_creation(self):
        r = LOSDBClientRecord(id="r1", backend=BackendType.GRAPH, label="chapter")
        assert r.id == "r1"
        assert r.backend == BackendType.GRAPH
        assert r.label == "chapter"
        assert r.metadata == {}

    def test_tc02_with_metadata(self):
        r = LOSDBClientRecord(id="r2", backend=BackendType.SQL, label="scene",
                               metadata={"key": "val"})
        assert r.metadata["key"] == "val"

    def test_tc03_to_dict(self):
        r = LOSDBClientRecord(id="r3", backend=BackendType.VECTOR, label="node",
                               metadata={"x": 1})
        d = r.to_dict()
        assert d["id"] == "r3"
        assert d["backend"] == "vector"
        assert d["label"] == "node"
        assert d["metadata"]["x"] == 1

    def test_tc04_from_dict_graph(self):
        d = {"id": "r4", "backend": "graph", "label": "edge", "metadata": {}}
        r = LOSDBClientRecord.from_dict(d)
        assert r.backend == BackendType.GRAPH

    def test_tc05_from_dict_sql(self):
        d = {"id": "r5", "backend": "sql", "label": "table", "metadata": {}}
        r = LOSDBClientRecord.from_dict(d)
        assert r.backend == BackendType.SQL

    def test_tc06_from_dict_vector(self):
        d = {"id": "r6", "backend": "vector", "label": "embed", "metadata": {}}
        r = LOSDBClientRecord.from_dict(d)
        assert r.backend == BackendType.VECTOR

    def test_tc07_roundtrip(self):
        r = LOSDBClientRecord(id="r7", backend=BackendType.GRAPH,
                               label="arc", metadata={"w": 3.14})
        r2 = LOSDBClientRecord.from_dict(r.to_dict())
        assert r2.id == r.id
        assert r2.backend == r.backend
        assert r2.label == r.label

    def test_tc08_default_metadata_independent(self):
        r1 = LOSDBClientRecord(id="a", backend=BackendType.SQL, label="x")
        r2 = LOSDBClientRecord(id="b", backend=BackendType.SQL, label="y")
        r1.metadata["z"] = 99
        assert "z" not in r2.metadata


# ---------------------------------------------------------------------------
# TC09~TC20 — LOSDBClient 기본 동작
# ---------------------------------------------------------------------------

class TestLOSDBClientBasic:
    def test_tc09_empty_client(self):
        c = LOSDBClient()
        assert c.available_backends() == []

    def test_tc10_single_sql_backend(self):
        sql = SQLiteRealAdapter(":memory:")
        c = LOSDBClient(sql=sql)
        assert BackendType.SQL in c.available_backends()
        assert len(c.available_backends()) == 1

    def test_tc11_single_vector_backend(self):
        vec = VectorRealAdapter(dim=2)
        c = LOSDBClient(vector=vec)
        assert BackendType.VECTOR in c.available_backends()

    def test_tc12_single_graph_backend(self):
        gr = GraphRealAdapter()
        c = LOSDBClient(graph=gr)
        assert BackendType.GRAPH in c.available_backends()

    def test_tc13_all_three_backends(self):
        sql = SQLiteRealAdapter(":memory:")
        vec = VectorRealAdapter(dim=2)
        gr = GraphRealAdapter()
        c = LOSDBClient(sql=sql, vector=vec, graph=gr)
        backends = c.available_backends()
        assert BackendType.SQL in backends
        assert BackendType.VECTOR in backends
        assert BackendType.GRAPH in backends
        assert len(backends) == 3

    def test_tc14_get_backend_existing(self):
        gr = GraphRealAdapter()
        c = LOSDBClient(graph=gr)
        assert c.get_backend(BackendType.GRAPH) is gr

    def test_tc15_get_backend_missing(self):
        c = LOSDBClient()
        assert c.get_backend(BackendType.SQL) is None

    def test_tc16_register_backend(self):
        c = LOSDBClient()
        gr = GraphRealAdapter()
        c.register_backend(BackendType.GRAPH, gr)
        assert BackendType.GRAPH in c.available_backends()

    def test_tc17_unregister_backend(self):
        gr = GraphRealAdapter()
        c = LOSDBClient(graph=gr)
        result = c.unregister_backend(BackendType.GRAPH)
        assert result is True
        assert BackendType.GRAPH not in c.available_backends()

    def test_tc18_unregister_missing_returns_false(self):
        c = LOSDBClient()
        assert c.unregister_backend(BackendType.SQL) is False

    def test_tc19_query_inactive_backend_returns_empty(self):
        c = LOSDBClient()
        recs = c.query_by_label(BackendType.GRAPH, "chapter")
        assert recs == []

    def test_tc20_cross_query_empty_backends(self):
        c = LOSDBClient()
        recs = c.cross_query([], "chapter")
        assert recs == []


# ---------------------------------------------------------------------------
# TC21~TC27 — query_by_label
# ---------------------------------------------------------------------------

class TestQueryByLabel:
    def test_tc21_vector_query_found(self):
        vec = VectorRealAdapter(dim=2)
        vec.upsert("v1", [0.1, 0.2], {"label": "chapter"})
        c = LOSDBClient(vector=vec)
        recs = c.query_by_label(BackendType.VECTOR, "chapter")
        assert len(recs) == 1
        assert recs[0].id == "v1"
        assert recs[0].backend == BackendType.VECTOR

    def test_tc22_vector_query_not_found(self):
        vec = VectorRealAdapter(dim=2)
        vec.upsert("v1", [0.1, 0.2], {"label": "scene"})
        c = LOSDBClient(vector=vec)
        recs = c.query_by_label(BackendType.VECTOR, "chapter")
        assert recs == []

    def test_tc23_vector_query_multiple(self):
        vec = VectorRealAdapter(dim=2)
        vec.upsert("v1", [0.1, 0.2], {"label": "chapter"})
        vec.upsert("v2", [0.3, 0.4], {"label": "chapter"})
        vec.upsert("v3", [0.5, 0.6], {"label": "scene"})
        c = LOSDBClient(vector=vec)
        recs = c.query_by_label(BackendType.VECTOR, "chapter")
        assert len(recs) == 2
        ids = {r.id for r in recs}
        assert "v1" in ids and "v2" in ids

    def test_tc24_graph_query_found(self):
        gr = GraphRealAdapter()
        gr.add_node("n1", "chapter")
        c = LOSDBClient(graph=gr)
        recs = c.query_by_label(BackendType.GRAPH, "chapter")
        assert len(recs) == 1
        assert recs[0].id == "n1"
        assert recs[0].backend == BackendType.GRAPH

    def test_tc25_graph_query_not_found(self):
        gr = GraphRealAdapter()
        gr.add_node("n1", "scene")
        c = LOSDBClient(graph=gr)
        recs = c.query_by_label(BackendType.GRAPH, "chapter")
        assert recs == []

    def test_tc26_graph_query_multiple(self):
        gr = GraphRealAdapter()
        gr.add_node("n1", "chapter")
        gr.add_node("n2", "chapter")
        gr.add_node("n3", "scene")
        c = LOSDBClient(graph=gr)
        recs = c.query_by_label(BackendType.GRAPH, "chapter")
        assert len(recs) == 2

    def test_tc27_sql_query_empty_table(self):
        sql = SQLiteRealAdapter(":memory:")
        c = LOSDBClient(sql=sql)
        # 존재하지 않는 테이블 → 빈 리스트
        recs = c.query_by_label(BackendType.SQL, "nonexistent_table")
        assert recs == []


# ---------------------------------------------------------------------------
# TC28~TC33 — cross_query
# ---------------------------------------------------------------------------

class TestCrossQuery:
    def test_tc28_vector_and_graph(self):
        vec = VectorRealAdapter(dim=2)
        vec.upsert("v1", [0.1, 0.2], {"label": "chapter"})
        gr = GraphRealAdapter()
        gr.add_node("n1", "chapter")
        c = LOSDBClient(vector=vec, graph=gr)
        recs = c.cross_query([BackendType.VECTOR, BackendType.GRAPH], "chapter")
        assert len(recs) == 2
        backends = {r.backend for r in recs}
        assert BackendType.VECTOR in backends
        assert BackendType.GRAPH in backends

    def test_tc29_all_three_backends(self):
        sql = SQLiteRealAdapter(":memory:")
        vec = VectorRealAdapter(dim=2)
        vec.upsert("v1", [0.1, 0.2], {"label": "arc"})
        gr = GraphRealAdapter()
        gr.add_node("n1", "arc")
        c = LOSDBClient(sql=sql, vector=vec, graph=gr)
        recs = c.cross_query([BackendType.SQL, BackendType.VECTOR, BackendType.GRAPH], "arc")
        # SQL: arc 테이블 없으므로 0, VECTOR: 1, GRAPH: 1 → 최소 2
        assert len(recs) >= 2

    def test_tc30_inactive_backend_skipped(self):
        vec = VectorRealAdapter(dim=2)
        vec.upsert("v1", [0.1, 0.2], {"label": "chapter"})
        c = LOSDBClient(vector=vec)  # graph 없음
        recs = c.cross_query([BackendType.VECTOR, BackendType.GRAPH], "chapter")
        assert len(recs) == 1  # VECTOR만
        assert recs[0].backend == BackendType.VECTOR

    def test_tc31_empty_label_cross_query(self):
        gr = GraphRealAdapter()
        gr.add_node("n1", "chapter")
        c = LOSDBClient(graph=gr)
        recs = c.cross_query([BackendType.GRAPH], "nonexistent")
        assert recs == []

    def test_tc32_cross_query_order_preserved(self):
        vec = VectorRealAdapter(dim=2)
        vec.upsert("v1", [0.1, 0.2], {"label": "chapter"})
        gr = GraphRealAdapter()
        gr.add_node("n1", "chapter")
        c = LOSDBClient(vector=vec, graph=gr)
        recs = c.cross_query([BackendType.VECTOR, BackendType.GRAPH], "chapter")
        # VECTOR 결과가 먼저 오는지 확인
        assert recs[0].backend == BackendType.VECTOR
        assert recs[1].backend == BackendType.GRAPH

    def test_tc33_cross_query_returns_list(self):
        c = LOSDBClient()
        result = c.cross_query([BackendType.SQL], "any")
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# TC34~TC38 — check_all_connections / schema_info
# ---------------------------------------------------------------------------

class TestConnectionAndSchema:
    def test_tc34_check_all_connections_graph(self):
        gr = GraphRealAdapter()
        c = LOSDBClient(graph=gr)
        status = c.check_all_connections()
        assert isinstance(status, dict)
        assert "graph" in status
        assert status["graph"] is True

    def test_tc35_check_all_connections_empty(self):
        c = LOSDBClient()
        status = c.check_all_connections()
        assert status == {}

    def test_tc36_check_all_connections_multi(self):
        vec = VectorRealAdapter(dim=2)
        gr = GraphRealAdapter()
        c = LOSDBClient(vector=vec, graph=gr)
        status = c.check_all_connections()
        assert "vector" in status
        assert "graph" in status

    def test_tc37_schema_info_structure(self):
        gr = GraphRealAdapter()
        c = LOSDBClient(graph=gr)
        info = c.schema_info()
        assert "client_version" in info
        assert "active_backends" in info
        assert "backends" in info
        assert isinstance(info["active_backends"], list)

    def test_tc38_schema_info_backends_key(self):
        gr = GraphRealAdapter()
        c = LOSDBClient(graph=gr)
        info = c.schema_info()
        assert "graph" in info["backends"]


# ---------------------------------------------------------------------------
# TC39~TC44 — Gate G45 + GATE_REGISTRY
# ---------------------------------------------------------------------------

class TestGateG45:
    def test_tc39_gates_count(self):
        from literary_system.gates.release_gate import GATES
        assert len(GATES) == 45  # V587: G46 추가로 45개

    def test_tc40_gate_registry_count(self):
        from literary_system.gates.gate_registry import GATE_REGISTRY
        assert len(GATE_REGISTRY) == 45  # V587: G46 추가로 45개

    def test_tc41_run_release_gate_all_pass(self):
        from literary_system.gates.release_gate import run_release_gate
        result = run_release_gate()
        assert result["total_gates"] == 45  # V587: G46 추가로 45개
        assert result["pass"] is True

    def test_tc42_gate_registry_g45_adr(self):
        from literary_system.gates.gate_registry import GATE_REGISTRY
        assert GATE_REGISTRY["losdb_client_g45"].adr_ref == "ADR-045"

    def test_tc43_gate_registry_g45_version(self):
        from literary_system.gates.gate_registry import GATE_REGISTRY
        assert GATE_REGISTRY["losdb_client_g45"].version_added == "V586"

    def test_tc44_gate_registry_g45_layer(self):
        from literary_system.gates.gate_registry import GATE_REGISTRY
        assert GATE_REGISTRY["losdb_client_g45"].layer == "L1"
