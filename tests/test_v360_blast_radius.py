"""V360: BlastRadiusCalculator v2 + 통합 테스트."""
import sys
sys.path.insert(0, "/tmp/v360_build")
import pytest
from literary_system.nkg.schema import NKGNodeType, NKGEdgeType, SceneNode, NKGEdge
from literary_system.nkg.graph_store import NKGGraphStore
from literary_system.gdap.blast_radius import BlastRadiusCalculator, BlastRadius


def build_chain(n=5):
    g = NKGGraphStore()
    for i in range(n):
        g.add_node(SceneNode(node_type=NKGNodeType.SCENE, node_id=f"s{i}", label=f"씬{i}"))
    for i in range(n-1):
        g.add_edge(NKGEdge(f"s{i}", f"s{i+1}", NKGEdgeType.CAUSAL_LINK, weight=1.0, confidence=1.0))
    return g


class TestBlastRadiusBasic:
    def test_no_nkg_returns_zero(self):
        calc = BlastRadiusCalculator()
        r = calc.calculate(["f1"])
        assert r.blast_ratio == 0.0

    def test_changed_files_preserved(self):
        g = build_chain(5)
        calc = BlastRadiusCalculator(nkg=g)
        r = calc.calculate(["s0"])
        assert "s0" in r.changed_files

    def test_downstream_found(self):
        g = build_chain(5)
        calc = BlastRadiusCalculator(nkg=g)
        r = calc.calculate(["s0"], depth=2)
        assert len(r.downstream_nodes) >= 1

    def test_upstream_found(self):
        g = build_chain(5)
        calc = BlastRadiusCalculator(nkg=g)
        r = calc.calculate(["s4"], depth=2)
        assert len(r.upstream_nodes) >= 1

    def test_blast_ratio_between_0_and_1(self):
        g = build_chain(5)
        calc = BlastRadiusCalculator(nkg=g)
        r = calc.calculate(["s2"])
        assert 0.0 <= r.blast_ratio <= 1.0

    def test_total_nodes_correct(self):
        g = build_chain(5)
        calc = BlastRadiusCalculator(nkg=g)
        r = calc.calculate(["s0"])
        assert r.total_nodes == 5

    def test_empty_changed_files(self):
        g = build_chain(3)
        calc = BlastRadiusCalculator(nkg=g)
        r = calc.calculate([])
        assert r.blast_ratio >= 0.0

    def test_depth_0_no_propagation(self):
        g = build_chain(5)
        calc = BlastRadiusCalculator(nkg=g)
        r = calc.calculate(["s2"], depth=0)
        assert len(r.downstream_nodes) == 0 and len(r.upstream_nodes) == 0

    def test_returns_blast_radius_type(self):
        g = build_chain(3)
        calc = BlastRadiusCalculator(nkg=g)
        r = calc.calculate(["s0"])
        assert isinstance(r, BlastRadius)

    def test_all_nodes_changed_max_ratio(self):
        g = build_chain(4)
        calc = BlastRadiusCalculator(nkg=g)
        r = calc.calculate([f"s{i}" for i in range(4)], depth=5)
        assert r.blast_ratio == pytest.approx(1.0, abs=0.01)


class TestBlastRadiusDepth:
    def test_depth_1_limited(self):
        g = build_chain(10)
        r1 = BlastRadiusCalculator(nkg=g).calculate(["s0"], depth=1)
        r2 = BlastRadiusCalculator(nkg=g).calculate(["s0"], depth=3)
        assert len(r2.downstream_nodes) >= len(r1.downstream_nodes)

    def test_isolated_node_no_propagation(self):
        g = NKGGraphStore()
        g.add_node(SceneNode(node_type=NKGNodeType.SCENE, node_id="s0", label="씬0"))
        g.add_node(SceneNode(node_type=NKGNodeType.SCENE, node_id="s1", label="씬1"))
        calc = BlastRadiusCalculator(nkg=g)
        r = calc.calculate(["s0"], depth=2)
        assert len(r.downstream_nodes) == 0
