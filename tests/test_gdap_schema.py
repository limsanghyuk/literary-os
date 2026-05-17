"""tests/test_gdap_schema.py — GDAP 스키마 단위 테스트 (30 tests).

DKGNodeType, DKGEdgeType, 레이어 frozenset,
각 노드 dataclass, DKGEdge, propagation_speed, 헬퍼 함수 검증.
"""
import pytest
from literary_system.gdap.schema import (
    DKGNodeType, DKGEdgeType,
    DEPENDENCY_EDGES, CONTRACT_EDGES, VERIFICATION_EDGES, REFERENCE_EDGES,
    IMMEDIATE_PROPAGATION, DEFERRED_PROPAGATION, BUILD_PROPAGATION,
    DKGEdge,
    DKGFileNode, DKGModuleNode, DKGFunctionNode, DKGClassNode,
    DKGSchemaNode, DKGTestNode, DKGConfigNode,
    node_type_of, _sha256_short, _path_hash,
)


# ──────────────────────────────────────────────────────────────
# 헬퍼 함수
# ──────────────────────────────────────────────────────────────

class TestHelpers:
    def test_sha256_short_length(self):
        h = _sha256_short("hello world")
        assert len(h) == 16

    def test_sha256_short_deterministic(self):
        h1 = _sha256_short("test")
        h2 = _sha256_short("test")
        assert h1 == h2

    def test_sha256_short_distinct(self):
        assert _sha256_short("a") != _sha256_short("b")

    def test_sha256_short_empty_string(self):
        h = _sha256_short("")
        assert isinstance(h, str) and len(h) == 16

    def test_path_hash_nonexistent_path(self):
        # 존재하지 않는 경로 → OSError → 경로 자체 해시
        h = _path_hash("/nonexistent/path/file.py")
        assert isinstance(h, str) and len(h) == 16


# ──────────────────────────────────────────────────────────────
# DKGNodeType / DKGEdgeType
# ──────────────────────────────────────────────────────────────

class TestEnums:
    def test_node_type_count(self):
        assert len(DKGNodeType) == 7

    def test_edge_type_count(self):
        assert len(DKGEdgeType) == 9

    def test_node_type_values(self):
        vals = {e.value for e in DKGNodeType}
        assert "file" in vals
        assert "test" in vals
        assert "config" in vals

    def test_edge_type_values(self):
        vals = {e.value for e in DKGEdgeType}
        assert "Imports" in vals
        assert "Tests" in vals
        assert "Configures" in vals

    def test_layer_frozensets_cover_all_edges(self):
        all_edges = (DEPENDENCY_EDGES | CONTRACT_EDGES |
                     VERIFICATION_EDGES | REFERENCE_EDGES)
        defined = {e.value for e in DKGEdgeType}
        assert all_edges == defined

    def test_layer_frozensets_no_overlap(self):
        layers = [DEPENDENCY_EDGES, CONTRACT_EDGES,
                  VERIFICATION_EDGES, REFERENCE_EDGES]
        total = sum(len(l) for l in layers)
        union = set().union(*layers)
        assert total == len(union)

    def test_propagation_frozensets_partition(self):
        # 9개 엣지 = IMMEDIATE(3) + BUILD(2) + DEFERRED(2) + CONTRACT(2)
        all_prop = (IMMEDIATE_PROPAGATION | BUILD_PROPAGATION |
                    DEFERRED_PROPAGATION | CONTRACT_EDGES)
        defined  = {e.value for e in DKGEdgeType}
        assert all_prop == defined


# ──────────────────────────────────────────────────────────────
# DKGEdge
# ──────────────────────────────────────────────────────────────

class TestDKGEdge:
    def test_imports_propagation_immediate(self):
        e = DKGEdge("a", "b", DKGEdgeType.IMPORTS)
        assert e.propagation_speed() == "immediate"

    def test_calls_propagation_immediate(self):
        e = DKGEdge("a", "b", DKGEdgeType.CALLS)
        assert e.propagation_speed() == "immediate"

    def test_inherits_propagation_immediate(self):
        e = DKGEdge("a", "b", DKGEdgeType.INHERITS)
        assert e.propagation_speed() == "immediate"

    def test_tests_propagation_build(self):
        e = DKGEdge("a", "b", DKGEdgeType.TESTS)
        assert e.propagation_speed() == "build"

    def test_covers_propagation_build(self):
        e = DKGEdge("a", "b", DKGEdgeType.COVERS)
        assert e.propagation_speed() == "build"

    def test_references_propagation_deferred(self):
        e = DKGEdge("a", "b", DKGEdgeType.REFERENCES)
        assert e.propagation_speed() == "deferred"

    def test_configures_propagation_deferred(self):
        e = DKGEdge("a", "b", DKGEdgeType.CONFIGURES)
        assert e.propagation_speed() == "deferred"

    def test_implements_propagation_schema_change(self):
        e = DKGEdge("a", "b", DKGEdgeType.IMPLEMENTS)
        assert e.propagation_speed() == "schema_change"

    def test_edge_default_weights(self):
        e = DKGEdge("x", "y", DKGEdgeType.CALLS)
        assert e.weight == 1.0
        assert e.confidence == 1.0

    def test_edge_metadata(self):
        e = DKGEdge("x", "y", DKGEdgeType.IMPORTS, metadata={"line": 10})
        assert e.metadata["line"] == 10


# ──────────────────────────────────────────────────────────────
# 노드 dataclasses
# ──────────────────────────────────────────────────────────────

class TestNodeDataclasses:
    def test_file_node_id(self):
        n = DKGFileNode("src/foo.py")
        assert n.node_id() == "file:src/foo.py"

    def test_file_node_hash_set(self):
        n = DKGFileNode("src/foo.py")
        assert isinstance(n.content_hash, str) and len(n.content_hash) == 16

    def test_file_node_stale(self):
        n = DKGFileNode("src/foo.py")
        assert not n.is_stale(n.content_hash)
        assert n.is_stale("deadbeefdeadbeef")

    def test_module_node_id(self):
        n = DKGModuleNode("literary_system.gdap")
        assert n.node_id() == "module:literary_system.gdap"

    def test_function_node_id(self):
        n = DKGFunctionNode("run", "pipeline.py")
        assert n.node_id() == "function:pipeline.py:run"

    def test_function_stale_on_signature_change(self):
        n = DKGFunctionNode("run", "pipeline.py", signature="() -> None")
        assert n.is_stale("() -> int")
        assert not n.is_stale("() -> None")

    def test_class_node_id(self):
        n = DKGClassNode("DKGPipeline", "pipeline.py")
        assert n.node_id() == "class:pipeline.py:DKGPipeline"

    def test_schema_node_id(self):
        n = DKGSchemaNode("WorkDeclaration", fields=["target_files"])
        assert n.node_id() == "schema:WorkDeclaration"

    def test_test_node_id(self):
        n = DKGTestNode("test_run", "tests/test_foo.py")
        assert n.node_id() == "test:tests/test_foo.py:test_run"

    def test_config_node_id(self):
        n = DKGConfigNode("pyproject.toml")
        assert n.node_id() == "config:pyproject.toml"

    def test_node_type_of(self):
        assert node_type_of(DKGFileNode("a.py")) == DKGNodeType.FILE
        assert node_type_of(DKGTestNode("t","b.py")) == DKGNodeType.TEST
        assert node_type_of(DKGConfigNode("c.toml")) == DKGNodeType.CONFIG


# ── 추가 보완 테스트 ──────────────────────────────────────────

class TestEdgeLayerSets:
    def test_dependency_edges_has_imports(self):
        assert "Imports" in DEPENDENCY_EDGES

    def test_contract_edges_has_defines_type(self):
        assert "DefinesType" in CONTRACT_EDGES

    def test_verification_edges_has_covers(self):
        assert "Covers" in VERIFICATION_EDGES

    def test_reference_edges_has_configures(self):
        assert "Configures" in REFERENCE_EDGES

    def test_schema_node_hash_changes_on_fields(self):
        s1 = DKGSchemaNode("S", fields=["a"])
        s2 = DKGSchemaNode("S", fields=["a", "b"])
        assert s1.content_hash != s2.content_hash

    def test_module_node_exports_default_empty(self):
        m = DKGModuleNode("mod.core")
        assert m.exports == []
