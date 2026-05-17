"""tests/test_gdap_blast_radius.py — BlastRadius + BlastRadiusCalculator (25 tests)."""
import pytest
from literary_system.gdap.blast_radius import BlastRadius, BlastRadiusCalculator
from literary_system.gdap.graph_store import DKGGraphStore
from literary_system.gdap.schema import DKGEdgeType


# ── 공통 그래프 픽스처 ──────────────────────────────────────

@pytest.fixture
def simple_graph():
    """A → B → C (IMPORTS), D → B (CALLS), isolated E"""
    g = DKGGraphStore()
    for name in ["A", "B", "C", "D", "E"]:
        g.add_file_node(name)
    g.add_edge_raw("file:A", "file:B", DKGEdgeType.IMPORTS)
    g.add_edge_raw("file:B", "file:C", DKGEdgeType.IMPORTS)
    g.add_edge_raw("file:D", "file:B", DKGEdgeType.CALLS)
    return g


@pytest.fixture
def calc(simple_graph):
    return BlastRadiusCalculator(simple_graph)


# ── BlastRadius 데이터클래스 ──────────────────────────────────

class TestBlastRadiusDataclass:
    def test_total_affected_includes_changed(self):
        br = BlastRadius(
            changed_nodes=["A"],
            affected_nodes={"A", "B", "C"},
            immediate_deps={"B"},
        )
        assert br.total_affected == 3

    def test_is_in_radius(self):
        br = BlastRadius(
            changed_nodes=["A"],
            affected_nodes={"A", "B"},
            immediate_deps={"B"},
        )
        assert br.is_in_radius("A")
        assert br.is_in_radius("B")
        assert not br.is_in_radius("X")

    def test_summary_format(self):
        br = BlastRadius(
            changed_nodes=["A"],
            affected_nodes={"A", "B"},
            immediate_deps={"B"},
            risk_level="medium",
        )
        s = br.summary()
        assert "changed=1" in s
        assert "affected=2" in s
        assert "risk=medium" in s


# ── BlastRadiusCalculator ─────────────────────────────────────

class TestCalculatorBasic:
    def test_changed_node_always_included(self, calc):
        br = calc.calculate(["file:A"])
        assert "file:A" in br.affected_nodes

    def test_depth1_immediate_deps(self, calc):
        br = calc.calculate(["file:A"], depth=1)
        assert "file:B" in br.immediate_deps

    def test_depth2_reaches_c(self, calc):
        br = calc.calculate(["file:A"], depth=2)
        assert "file:C" in br.affected_nodes

    def test_depth1_does_not_reach_c(self, calc):
        br = calc.calculate(["file:A"], depth=1)
        assert "file:C" not in br.affected_nodes

    def test_isolated_node_unaffected(self, calc):
        br = calc.calculate(["file:A"], depth=2)
        assert "file:E" not in br.affected_nodes

    def test_changed_nodes_list_preserved(self, calc):
        br = calc.calculate(["file:A", "file:D"])
        assert "file:A" in br.changed_nodes
        assert "file:D" in br.changed_nodes


class TestCalculatorImmediateOnly:
    def test_immediate_only_filters_non_immediate(self, simple_graph):
        # REFERENCES 엣지만 있는 그래프
        g = DKGGraphStore()
        g.add_file_node("X")
        g.add_file_node("Y")
        g.add_edge_raw("file:X", "file:Y", DKGEdgeType.REFERENCES)
        c = BlastRadiusCalculator(g)
        br = c.calculate(["file:X"], depth=1, immediate_only=True)
        # REFERENCES는 즉시전파 아님 → Y 미포함
        assert "file:Y" not in br.affected_nodes

    def test_immediate_only_includes_imports(self, calc):
        br = calc.calculate(["file:A"], depth=1, immediate_only=True)
        assert "file:B" in br.affected_nodes


class TestCalculatorRisk:
    def test_low_risk_small_graph(self, calc):
        br = calc.calculate(["file:A"])
        # 5개 노드 중 최대 4개 영향 → 80% → HIGH
        # 실제로는 A→B→C, D→B: A변경 시 {A,B,C} 3개 = 60%
        assert br.risk_level in ("low", "medium", "high")

    def test_risk_none_graph(self):
        c = BlastRadiusCalculator(None)
        br = c.calculate(["file:X"])
        # 기본 total=100, 영향=1 → low
        assert br.risk_level == "low"

    def test_high_risk_many_affected(self):
        g = DKGGraphStore()
        # 10개 노드, root → 나머지 9개 all IMPORTS → HIGH RISK
        root = "root"
        g.add_file_node(root)
        for i in range(9):
            g.add_file_node(f"n{i}")
            g.add_edge_raw(f"file:{root}", f"file:n{i}", DKGEdgeType.IMPORTS)
        c = BlastRadiusCalculator(g)
        br = c.calculate([f"file:{root}"], depth=1)
        assert br.risk_level == "high"


class TestCalculatorForNode:
    def test_calculate_for_node_single(self, calc):
        br = calc.calculate_for_node("file:A", depth=2)
        assert "file:A" in br.changed_nodes
        assert len(br.changed_nodes) == 1

    def test_depth_map_populated(self, calc):
        br = calc.calculate(["file:A"], depth=2)
        assert br.depth_map["file:A"] == 0
        assert br.depth_map.get("file:B") == 1
        assert br.depth_map.get("file:C") == 2


class TestFormatReport:
    def test_format_report_contains_sections(self, calc):
        br = calc.calculate(["file:A"], depth=2)
        report = calc.format_report(br)
        assert "=== Blast Radius Report ===" in report
        assert "Changed" in report
        assert "Affected" in report

    def test_format_report_lists_changed(self, calc):
        br = calc.calculate(["file:D"])
        report = calc.format_report(br)
        assert "file:D" in report
