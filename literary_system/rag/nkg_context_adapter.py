"""
V439 -- NKGContextAdapter
Serializes NKG node/edge data into LLM context windows with priority
ordering and token-budget-aware compression.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Priority
# ---------------------------------------------------------------------------

class PriorityLevel(IntEnum):
    CRITICAL   = 0
    HIGH       = 1
    MEDIUM     = 2
    LOW        = 3
    BACKGROUND = 4


# ---------------------------------------------------------------------------
# Snapshots
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NKGNodeSnapshot:
    """Immutable view of a single NKG node."""
    node_id:  str
    label:    str
    content:  str
    priority: PriorityLevel = PriorityLevel.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict, compare=False, hash=False)

    def word_count(self) -> int:
        return len(self.content.split())

    def char_count(self) -> int:
        return len(self.content)


@dataclass(frozen=True)
class NKGEdgeSnapshot:
    """Immutable view of a single NKG edge."""
    edge_id:  str
    source_id: str
    target_id: str
    relation:  str
    weight:    float = 1.0
    priority:  PriorityLevel = PriorityLevel.LOW
    metadata:  Dict[str, Any] = field(default_factory=dict, compare=False, hash=False)

    def description(self) -> str:
        return self.source_id + " --[" + self.relation + "]--> " + self.target_id


# ---------------------------------------------------------------------------
# ContextSerializer
# ---------------------------------------------------------------------------

class ContextSerializer:
    """Renders NKG snapshots as structured plain-text for LLM injection."""

    HEADER = "=== NKG CONTEXT ==="
    FOOTER = "=== END NKG CONTEXT ==="
    EDGE_SEPARATOR = "--- RELATIONS ---"

    def serialize(
        self,
        nodes: List[NKGNodeSnapshot],
        edges: List[NKGEdgeSnapshot],
    ) -> str:
        out = [self.HEADER]
        for node in nodes:
            pname = PriorityLevel(node.priority).name
            out.append("[" + pname + "] " + node.node_id + ": " + node.label)
            out.append("  " + node.content)
        if edges:
            out.append(self.EDGE_SEPARATOR)
            for edge in edges:
                out.append(
                    edge.edge_id + ": " + edge.description() +
                    " (weight=" + format(edge.weight, ".3f") + ")"
                )
        out.append(self.FOOTER)
        return chr(10).join(out)

    def serialize_node(self, node: NKGNodeSnapshot) -> str:
        pname = PriorityLevel(node.priority).name
        return "[" + pname + "] " + node.node_id + ": " + node.label + chr(10) + "  " + node.content

    def serialize_edge(self, edge: NKGEdgeSnapshot) -> str:
        return edge.edge_id + ": " + edge.description() + " (weight=" + format(edge.weight, ".3f") + ")"

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough token estimate: chars / 4."""
        return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# ContextCompressor
# ---------------------------------------------------------------------------

class ContextCompressor:
    """Prune / truncate context to fit within a token budget."""

    def __init__(self, max_tokens: int = 2048) -> None:
        if max_tokens < 1:
            raise ValueError("max_tokens must be >= 1")
        self.max_tokens = max_tokens

    def compress(
        self,
        nodes: List[NKGNodeSnapshot],
        edges: List[NKGEdgeSnapshot],
        serializer: Optional[ContextSerializer] = None,
    ) -> Tuple[List[NKGNodeSnapshot], List[NKGEdgeSnapshot]]:
        ser = serializer or ContextSerializer()
        sorted_nodes = sorted(nodes, key=lambda n: n.priority)
        remaining_edges = list(edges)

        def total_tokens(ns, es):
            return ser.estimate_tokens(ser.serialize(ns, es))

        # drop edges first
        while remaining_edges and total_tokens(sorted_nodes, remaining_edges) > self.max_tokens:
            remaining_edges.pop()

        # drop low-priority nodes
        while len(sorted_nodes) > 1 and total_tokens(sorted_nodes, remaining_edges) > self.max_tokens:
            sorted_nodes.pop()

        # truncate single node if still over budget
        if sorted_nodes and total_tokens(sorted_nodes, remaining_edges) > self.max_tokens:
            node = sorted_nodes[0]
            overhead = ser.estimate_tokens(ser.serialize([], remaining_edges)) + 20
            allowed_chars = max(4, (self.max_tokens - overhead) * 4)
            truncated = node.content[:allowed_chars] + ("..." if len(node.content) > allowed_chars else "")
            sorted_nodes[0] = NKGNodeSnapshot(
                node_id=node.node_id,
                label=node.label,
                content=truncated,
                priority=node.priority,
                metadata=node.metadata,
            )
        return sorted_nodes, remaining_edges

    def fits(self, text: str) -> bool:
        return ContextSerializer.estimate_tokens(text) <= self.max_tokens


# ---------------------------------------------------------------------------
# NKGContextAdapter
# ---------------------------------------------------------------------------

class NKGContextAdapter:
    """Main adapter: prioritizes, serializes, compresses NKG snapshots."""

    def __init__(
        self,
        max_tokens: int = 2048,
        serializer: Optional[ContextSerializer] = None,
        compressor: Optional[ContextCompressor] = None,
    ) -> None:
        self.max_tokens = max_tokens
        self._serializer = serializer or ContextSerializer()
        self._compressor = compressor or ContextCompressor(max_tokens=max_tokens)
        self._nodes: List[NKGNodeSnapshot] = []
        self._edges: List[NKGEdgeSnapshot] = []

    def add_node(self, node: NKGNodeSnapshot) -> None:
        self._nodes.append(node)

    def add_edge(self, edge: NKGEdgeSnapshot) -> None:
        self._edges.append(edge)

    def add_nodes(self, nodes: List[NKGNodeSnapshot]) -> None:
        self._nodes.extend(nodes)

    def add_edges(self, edges: List[NKGEdgeSnapshot]) -> None:
        self._edges.extend(edges)

    def clear(self) -> None:
        self._nodes.clear()
        self._edges.clear()

    def build_context(self, compress: bool = True) -> str:
        nodes = list(self._nodes)
        edges = list(self._edges)
        if compress:
            nodes, edges = self._compressor.compress(nodes, edges, self._serializer)
        return self._serializer.serialize(nodes, edges)

    def build_compressed(self) -> str:
        return self.build_context(compress=True)

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return len(self._edges)

    def estimated_tokens(self) -> int:
        text = self._serializer.serialize(self._nodes, self._edges)
        return ContextSerializer.estimate_tokens(text)

    def stats(self) -> Dict[str, Any]:
        raw_text = self._serializer.serialize(self._nodes, self._edges)
        cn, ce = self._compressor.compress(list(self._nodes), list(self._edges), self._serializer)
        compressed_text = self._serializer.serialize(cn, ce)
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "raw_tokens": ContextSerializer.estimate_tokens(raw_text),
            "compressed_tokens": ContextSerializer.estimate_tokens(compressed_text),
            "max_tokens": self.max_tokens,
            "fits_budget": ContextSerializer.estimate_tokens(compressed_text) <= self.max_tokens,
        }

    @staticmethod
    def rank_nodes_by_priority(nodes: List[NKGNodeSnapshot]) -> List[NKGNodeSnapshot]:
        return sorted(nodes, key=lambda n: n.priority)

    @staticmethod
    def filter_by_priority(
        nodes: List[NKGNodeSnapshot],
        max_priority: PriorityLevel,
    ) -> List[NKGNodeSnapshot]:
        return [n for n in nodes if n.priority <= max_priority]
