"""V585 테스트 — GraphRealAdapter (ADR-044)

43개 테스트 케이스:
  TC01~TC08  : GraphRecord 데이터클래스
  TC09~TC16  : GraphEdgeRecord 데이터클래스
  TC17~TC25  : GraphRealAdapter 기본 CRUD
  TC26~TC30  : 탐색 (neighbors / BFS / DFS)
  TC31~TC34  : JSON 영속화 (save / load)
  TC35~TC37  : apply / rollback / graph_ops
  TC38~TC40  : Gate G44 + Gate Registry
  TC41~TC43  : 통합 (MigrationEngine + export + schema_info)
"""
from __future__ import annotations

import os
import tempfile

import pytest

from literary_system.db.graph_real_adapter import (
    GraphEdgeRecord,
    GraphRealAdapter,
    GraphRecord,
    HAS_NETWORKX,
)
from literary_system.db.migration_manager import Migration
from literary_system.db.schema_registry import BackendType
from literary_system.gates.gate_registry import GATE_REGISTRY
from literary_system.gates.release_gate import GATES, run_release_gate


# ── TC01~TC08: GraphRecord ────────────────────────────────────────────────────


class TestGraphRecord:
    def test_tc01_create_basic(self):
        r = GraphRecord(id="n1", label="Character")
        assert r.id == "n1"
        assert r.label == "Character"
        assert r.metadata == {}

    def test_tc02_create_with_metadata(self):
        r = GraphRecord(id="n2", label="Event", metadata={"scene": 3})
        assert r.metadata["scene"] == 3

    def test_tc03_to_dict(self):
        r = GraphRecord(id="n3", label="Location", metadata={"country": "KR"})
        d = r.to_dict()
        assert d["id"] == "n3"
        assert d["label"] == "Location"
        assert d["metadata"]["country"] == "KR"

    def test_tc04_from_dict(self):
        d = {"id": "n4", "label": "Theme", "metadata": {"tag": "love"}}
        r = GraphRecord.from_dict(d)
        assert r.id == "n4"
        assert r.label == "Theme"
        assert r.metadata["tag"] == "love"

    def test_tc05_from_dict_no_metadata(self):
        d = {"id": "n5", "label": "Scene"}
        r = GraphRecord.from_dict(d)
        assert r.metadata == {}

    def test_tc06_roundtrip(self):
        r = GraphRecord(id="n6", label="Plot", metadata={"order": 1})
        assert GraphRecord.from_dict(r.to_dict()).label == "Plot"

    def test_tc07_empty_label(self):
        r = GraphRecord(id="n7", label="")
        assert r.label == ""

    def test_tc08_metadata_default_factory(self):
        r1 = GraphRecord(id="a", label="X")
        r2 = GraphRecord(id="b", label="Y")
        r1.metadata["key"] = "val"
        assert "key" not in r2.metadata


# ── TC09~TC16: GraphEdgeRecord ────────────────────────────────────────────────


class TestGraphEdgeRecord:
    def test_tc09_create_basic(self):
        e = GraphEdgeRecord(id="e1", src_id="A", dst_id="B", label="causes")
        assert e.id == "e1"
        assert e.src_id == "A"
        assert e.dst_id == "B"
        assert e.weight == 1.0

    def test_tc10_create_with_weight(self):
        e = GraphEdgeRecord(id="e2", src_id="X", dst_id="Y", label="link", weight=0.5)
        assert e.weight == 0.5

    def test_tc11_to_dict(self):
        e = GraphEdgeRecord(id="e3", src_id="A", dst_id="C", label="before")
        d = e.to_dict()
        assert d["src_id"] == "A"
        assert d["weight"] == 1.0

    def test_tc12_from_dict(self):
        d = {"id": "e4", "src_id": "P", "dst_id": "Q", "label": "meets", "weight": 2.0, "metadata": {}}
        e = GraphEdgeRecord.from_dict(d)
        assert e.weight == 2.0

    def test_tc13_from_dict_no_weight(self):
        d = {"id": "e5", "src_id": "A", "dst_id": "B", "label": "x"}
        e = GraphEdgeRecord.from_dict(d)
        assert e.weight == 1.0

    def test_tc14_roundtrip(self):
        e = GraphEdgeRecord(id="e6", src_id="S", dst_id="T", label="follows", weight=3.0)
        e2 = GraphEdgeRecord.from_dict(e.to_dict())
        assert e2.weight == 3.0

    def test_tc15_metadata(self):
        e = GraphEdgeRecord(id="e7", src_id="A", dst_id="B", label="z", metadata={"k": "v"})
        assert e.metadata["k"] == "v"

    def test_tc16_metadata_default_factory(self):
        e1 = GraphEdgeRecord(id="ea", src_id="A", dst_id="B", label="x")
        e2 = GraphEdgeRecord(id="eb", src_id="C", dst_id="D", label="y")
        e1.metadata["k"] = "v"
        assert "k" not in e2.metadata


# ── TC17~TC25: GraphRealAdapter 기본 CRUD ────────────────────────────────────


class TestGraphRealAdapterCRUD:
    def setup_method(self):
        self.g = GraphRealAdapter()

    def test_tc17_empty_state(self):
        assert self.g.node_count() == 0
        assert self.g.edge_count() == 0
        assert self.g.check_connection() is True

    def test_tc18_add_node(self):
        self.g.add_node("A", label="Char")
        assert self.g.node_count() == 1
        assert self.g.get_node("A").label == "Char"

    def test_tc19_add_node_overwrite(self):
        self.g.add_node("A", label="V1")
        self.g.add_node("A", label="V2")
        assert self.g.node_count() == 1
        assert self.g.get_node("A").label == "V2"

    def test_tc20_add_edge(self):
        self.g.add_node("A", label="A")
        self.g.add_node("B", label="B")
        self.g.add_edge("e1", src_id="A", dst_id="B", label="link")
        assert self.g.edge_count() == 1
        assert self.g.get_edge("e1").src_id == "A"

    def test_tc21_add_edge_auto_creates_nodes(self):
        self.g.add_edge("e1", src_id="X", dst_id="Y", label="auto")
        assert self.g.node_count() == 2
        assert self.g.get_node("X") is not None

    def test_tc22_remove_node(self):
        self.g.add_node("A", label="A")
        result = self.g.remove_node("A")
        assert result is True
        assert self.g.get_node("A") is None
        assert self.g.node_count() == 0

    def test_tc23_remove_node_cascade_edges(self):
        self.g.add_node("A", label="A")
        self.g.add_node("B", label="B")
        self.g.add_edge("e1", src_id="A", dst_id="B", label="x")
        self.g.remove_node("A")
        assert self.g.edge_count() == 0

    def test_tc24_remove_edge(self):
        self.g.add_edge("e1", src_id="A", dst_id="B", label="x")
        result = self.g.remove_edge("e1")
        assert result is True
        assert self.g.get_edge("e1") is None
        assert self.g.edge_count() == 0

    def test_tc25_get_missing(self):
        assert self.g.get_node("NONE") is None
        assert self.g.get_edge("NONE") is None
        assert self.g.remove_node("NONE") is False
        assert self.g.remove_edge("NONE") is False


# ── TC26~TC30: 탐색 ──────────────────────────────────────────────────────────


class TestGraphTraversal:
    def setup_method(self):
        self.g = GraphRealAdapter()
        self.g.add_node("A", label="A")
        self.g.add_node("B", label="B")
        self.g.add_node("C", label="C")
        self.g.add_node("D", label="D")
        self.g.add_edge("e1", src_id="A", dst_id="B", label="ab")
        self.g.add_edge("e2", src_id="B", dst_id="C", label="bc")
        self.g.add_edge("e3", src_id="A", dst_id="D", label="ad")

    def test_tc26_neighbors_out(self):
        out = self.g.neighbors("A", direction="out")
        assert set(out) == {"B", "D"}

    def test_tc27_neighbors_in(self):
        in_ = self.g.neighbors("B", direction="in")
        assert "A" in in_

    def test_tc28_neighbors_both(self):
        # B: in=A, out=C
        both = self.g.neighbors("B", direction="both")
        assert "A" in both and "C" in both

    def test_tc29_bfs(self):
        result = self.g.bfs("A")
        assert result[0] == "A"
        assert set(result) == {"A", "B", "C", "D"}

    def test_tc30_dfs(self):
        result = self.g.dfs("A")
        assert result[0] == "A"
        assert set(result) == {"A", "B", "C", "D"}


# ── TC31~TC34: JSON 영속화 ────────────────────────────────────────────────────


class TestGraphPersistence:
    def test_tc31_save_and_load(self, tmp_path):
        path = str(tmp_path / "graph.json")
        g = GraphRealAdapter(path=path)
        g.add_node("A", label="Char")
        g.add_edge("e1", src_id="A", dst_id="A", label="self")
        g.save()
        g2 = GraphRealAdapter(path=path)
        assert g2.node_count() == 1
        assert g2.edge_count() == 1
        assert g2.get_node("A").label == "Char"

    def test_tc32_load_on_init(self, tmp_path):
        path = str(tmp_path / "graph2.json")
        g1 = GraphRealAdapter(path=path)
        g1.add_node("X", label="X")
        g1.save()
        g2 = GraphRealAdapter(path=path)
        assert g2.get_node("X") is not None

    def test_tc33_save_no_path(self):
        g = GraphRealAdapter()
        g.add_node("A", label="A")
        g.save()  # path 없음 — 예외 없이 경고만

    def test_tc34_load_missing_file(self, tmp_path):
        path = str(tmp_path / "nonexistent.json")
        g = GraphRealAdapter(path=path)  # 파일 없어도 예외 없음
        assert g.node_count() == 0


# ── TC35~TC37: apply / rollback / graph_ops ──────────────────────────────────


class TestGraphApplyRollback:
    def _make_migration(self, ops, mid="test_001"):
        return Migration(
            migration_id=mid,
            backend=BackendType.GRAPH,
            from_version="0.0.0",
            to_version="1.0.0",
            graph_ops=ops,
        )

    def test_tc35_apply_add_node(self):
        g = GraphRealAdapter()
        m = self._make_migration([{"op": "add_node", "node": {"id": "N", "label": "New"}}])
        assert g.apply(m) is True
        assert g.get_node("N") is not None

    def test_tc36_apply_and_rollback(self):
        g = GraphRealAdapter()
        g.add_node("base", label="Base")
        m = self._make_migration([{"op": "add_node", "node": {"id": "tmp", "label": "Tmp"}}])
        g.apply(m)
        assert g.get_node("tmp") is not None
        assert g.rollback(m) is True
        assert g.get_node("tmp") is None
        assert g.get_node("base") is not None

    def test_tc37_apply_multi_ops(self):
        g = GraphRealAdapter()
        ops = [
            {"op": "add_node", "node": {"id": "A", "label": "A"}},
            {"op": "add_node", "node": {"id": "B", "label": "B"}},
            {"op": "add_edge", "edge": {"id": "e1", "src_id": "A", "dst_id": "B", "label": "x"}},
        ]
        m = self._make_migration(ops)
        assert g.apply(m) is True
        assert g.node_count() == 2
        assert g.edge_count() == 1


# ── TC38~TC40: Gate G44 + Registry ───────────────────────────────────────────


class TestGateG44:
    def test_tc38_gates_count(self):
        assert len(GATES) == 45  # V587: G46 추가로 45개

    def test_tc39_gate_registry_count(self):
        assert len(GATE_REGISTRY) == 45  # V587: G46 추가로 45개

    def test_tc40_run_release_gate_all_pass(self):
        result = run_release_gate()
        assert result["total_gates"] == 45  # V587: G46 추가로 45개
        assert result["pass"] is True


class TestGateRegistry:
    def test_tc41_gate_registry_g44_adr(self):
        assert GATE_REGISTRY["graph_real_adapter_g44"].adr_ref == "ADR-044"

    def test_tc42_gate_registry_g44_version(self):
        assert GATE_REGISTRY["graph_real_adapter_g44"].version_added == "V585"

    def test_tc43_gate_registry_g44_layer(self):
        assert GATE_REGISTRY["graph_real_adapter_g44"].layer == "L1"
