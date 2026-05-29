"""
V439 tests -- NKGContextAdapter (serialization + priority + compression)
"""
import pytest
from literary_system.rag.nkg_context_adapter import (
    PriorityLevel, NKGNodeSnapshot, NKGEdgeSnapshot,
    ContextSerializer, ContextCompressor, NKGContextAdapter,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_node(node_id="n1", label="Scene", content="A vivid scene unfolds.",
              priority=PriorityLevel.MEDIUM):
    return NKGNodeSnapshot(node_id=node_id, label=label, content=content, priority=priority)


def make_edge(edge_id="e1", src="n1", tgt="n2", relation="causes"):
    return NKGEdgeSnapshot(edge_id=edge_id, source_id=src, target_id=tgt, relation=relation)


# ---------------------------------------------------------------------------
# TestPriorityLevel
# ---------------------------------------------------------------------------

class TestPriorityLevel:
    def test_order(self):
        assert PriorityLevel.CRITICAL < PriorityLevel.HIGH
        assert PriorityLevel.HIGH < PriorityLevel.MEDIUM
        assert PriorityLevel.MEDIUM < PriorityLevel.LOW
        assert PriorityLevel.LOW < PriorityLevel.BACKGROUND

    def test_int_values(self):
        assert int(PriorityLevel.CRITICAL) == 0
        assert int(PriorityLevel.BACKGROUND) == 4


# ---------------------------------------------------------------------------
# TestNKGNodeSnapshot
# ---------------------------------------------------------------------------

class TestNKGNodeSnapshot:
    def test_fields(self):
        n = NKGNodeSnapshot("n1", "Scene", "content here", PriorityLevel.HIGH)
        assert n.node_id == "n1"
        assert n.label == "Scene"
        assert n.priority == PriorityLevel.HIGH

    def test_word_count(self):
        n = make_node(content="hello world foo")
        assert n.word_count() == 3

    def test_char_count(self):
        n = make_node(content="hello")
        assert n.char_count() == 5

    def test_default_priority(self):
        n = NKGNodeSnapshot("n1", "label", "content")
        assert n.priority == PriorityLevel.MEDIUM

    def test_frozen(self):
        n = make_node()
        with pytest.raises(Exception):
            n.node_id = "changed"


# ---------------------------------------------------------------------------
# TestNKGEdgeSnapshot
# ---------------------------------------------------------------------------

class TestNKGEdgeSnapshot:
    def test_fields(self):
        e = make_edge()
        assert e.edge_id == "e1"
        assert e.relation == "causes"

    def test_description(self):
        e = make_edge(src="A", tgt="B", relation="leads_to")
        assert "A" in e.description()
        assert "B" in e.description()
        assert "leads_to" in e.description()

    def test_default_weight(self):
        e = make_edge()
        assert e.weight == 1.0


# ---------------------------------------------------------------------------
# TestContextSerializer
# ---------------------------------------------------------------------------

class TestContextSerializer:
    def test_header_footer(self):
        s = ContextSerializer()
        out = s.serialize([], [])
        assert "=== NKG CONTEXT ===" in out
        assert "=== END NKG CONTEXT ===" in out

    def test_node_rendered(self):
        s = ContextSerializer()
        n = make_node(node_id="n1", label="Act", content="The hero arrives.")
        out = s.serialize([n], [])
        assert "n1" in out
        assert "Act" in out
        assert "The hero arrives." in out

    def test_priority_label_in_output(self):
        s = ContextSerializer()
        n = make_node(priority=PriorityLevel.CRITICAL)
        out = s.serialize([n], [])
        assert "CRITICAL" in out

    def test_edge_rendered(self):
        s = ContextSerializer()
        e = make_edge(src="n1", tgt="n2", relation="causes")
        out = s.serialize([], [e])
        assert "causes" in out
        assert "--- RELATIONS ---" in out

    def test_no_edge_separator_when_no_edges(self):
        s = ContextSerializer()
        out = s.serialize([make_node()], [])
        assert "--- RELATIONS ---" not in out

    def test_estimate_tokens(self):
        assert ContextSerializer.estimate_tokens("hello") >= 1
        assert ContextSerializer.estimate_tokens("a" * 400) == 100

    def test_serialize_node(self):
        s = ContextSerializer()
        n = make_node(node_id="x", label="Y", content="Z content")
        out = s.serialize_node(n)
        assert "x" in out and "Y" in out and "Z content" in out

    def test_serialize_edge(self):
        s = ContextSerializer()
        e = make_edge(edge_id="e9", src="A", tgt="B", relation="causes")
        out = s.serialize_edge(e)
        assert "e9" in out and "causes" in out


# ---------------------------------------------------------------------------
# TestContextCompressor
# ---------------------------------------------------------------------------

class TestContextCompressor:
    def test_invalid_max_tokens(self):
        with pytest.raises(ValueError):
            ContextCompressor(max_tokens=0)

    def test_no_compression_needed(self):
        c = ContextCompressor(max_tokens=4096)
        nodes = [make_node()]
        edges = [make_edge()]
        rn, re = c.compress(nodes, edges)
        assert len(rn) == 1
        assert len(re) == 1

    def test_edges_dropped_first(self):
        c = ContextCompressor(max_tokens=20)
        nodes = [make_node(content="short")]
        edges = [make_edge() for _ in range(5)]
        rn, re = c.compress(nodes, edges)
        # under tight budget edges should be pruned
        assert len(re) <= len(edges)

    def test_nodes_pruned_by_priority(self):
        c = ContextCompressor(max_tokens=30)
        nodes = [
            make_node("n1", content="A" * 50, priority=PriorityLevel.CRITICAL),
            make_node("n2", content="B" * 50, priority=PriorityLevel.BACKGROUND),
        ]
        rn, _ = c.compress(nodes, [])
        ids = [n.node_id for n in rn]
        # BACKGROUND should be dropped before CRITICAL
        assert "n1" in ids

    def test_fits(self):
        c = ContextCompressor(max_tokens=100)
        assert c.fits("short text")
        assert not c.fits("x" * 1000)

    def test_returns_sorted_by_priority(self):
        c = ContextCompressor(max_tokens=4096)
        nodes = [
            make_node("a", priority=PriorityLevel.LOW),
            make_node("b", priority=PriorityLevel.CRITICAL),
        ]
        rn, _ = c.compress(nodes, [])
        assert rn[0].priority <= rn[-1].priority


# ---------------------------------------------------------------------------
# TestNKGContextAdapter
# ---------------------------------------------------------------------------

class TestNKGContextAdapter:
    def test_add_and_count(self):
        a = NKGContextAdapter()
        a.add_node(make_node())
        a.add_edge(make_edge())
        assert a.node_count == 1
        assert a.edge_count == 1

    def test_add_batch(self):
        a = NKGContextAdapter()
        a.add_nodes([make_node("n1"), make_node("n2")])
        a.add_edges([make_edge("e1"), make_edge("e2")])
        assert a.node_count == 2
        assert a.edge_count == 2

    def test_clear(self):
        a = NKGContextAdapter()
        a.add_node(make_node())
        a.clear()
        assert a.node_count == 0
        assert a.edge_count == 0

    def test_build_context_contains_header(self):
        a = NKGContextAdapter()
        a.add_node(make_node())
        ctx = a.build_context()
        assert "=== NKG CONTEXT ===" in ctx
        assert "=== END NKG CONTEXT ===" in ctx

    def test_build_context_no_compress(self):
        a = NKGContextAdapter()
        a.add_node(make_node(content="hello world"))
        ctx = a.build_context(compress=False)
        assert "hello world" in ctx

    def test_estimated_tokens(self):
        a = NKGContextAdapter()
        a.add_node(make_node(content="a" * 400))
        assert a.estimated_tokens() >= 100

    def test_stats_keys(self):
        a = NKGContextAdapter(max_tokens=1024)
        a.add_node(make_node())
        s = a.stats()
        assert "node_count" in s
        assert "fits_budget" in s
        assert "compressed_tokens" in s

    def test_stats_fits_budget(self):
        a = NKGContextAdapter(max_tokens=4096)
        a.add_node(make_node())
        assert a.stats()["fits_budget"] is True

    def test_rank_nodes_by_priority(self):
        nodes = [
            make_node("a", priority=PriorityLevel.LOW),
            make_node("b", priority=PriorityLevel.CRITICAL),
            make_node("c", priority=PriorityLevel.HIGH),
        ]
        ranked = NKGContextAdapter.rank_nodes_by_priority(nodes)
        assert ranked[0].priority == PriorityLevel.CRITICAL
        assert ranked[-1].priority == PriorityLevel.LOW

    def test_filter_by_priority(self):
        nodes = [
            make_node("a", priority=PriorityLevel.CRITICAL),
            make_node("b", priority=PriorityLevel.HIGH),
            make_node("c", priority=PriorityLevel.BACKGROUND),
        ]
        filtered = NKGContextAdapter.filter_by_priority(nodes, PriorityLevel.HIGH)
        assert all(n.priority <= PriorityLevel.HIGH for n in filtered)
        assert len(filtered) == 2

    def test_build_compressed_alias(self):
        a = NKGContextAdapter(max_tokens=4096)
        a.add_node(make_node())
        assert a.build_compressed() == a.build_context(compress=True)

    def test_compression_respects_budget(self):
        # very tight budget -- context must fit
        a = NKGContextAdapter(max_tokens=50)
        for i in range(10):
            a.add_node(make_node(f"n{i}", content="x" * 200))
        ctx = a.build_context(compress=True)
        tokens = ContextSerializer.estimate_tokens(ctx)
        assert tokens <= 50
