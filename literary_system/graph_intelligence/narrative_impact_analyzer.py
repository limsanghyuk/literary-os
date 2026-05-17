"""V529 — NarrativeImpactAnalyzer
Computes blast radius and risk score for a proposed scene change.
LLM-0 compliant: zero LLM calls.

Risk formula
------------
  risk_score = min(
      direct_count   * 0.20
    + indirect_count * 0.08
    + reveal_count   * 0.30
    + foreshadow_breaks * 0.25,
    1.0
  )

Risk levels   →  decision
  critical >= 0.80  →  hold
  high     >= 0.55  →  split_required
  medium   >= 0.30  →  review
  low       < 0.30  →  proceed
"""
from __future__ import annotations

from typing import Dict, List, Set

from literary_system.graph_intelligence.narrative_graph_schema import (
    NarrativeEdgeType, NarrativeImpactReport, NarrativeNodeType,
)
from literary_system.graph_intelligence.narrative_graph_store import NarrativeGraphStore

_CRITICAL = 0.80
_HIGH     = 0.55
_MEDIUM   = 0.30

_W_DIRECT           = 0.20
_W_INDIRECT         = 0.08
_W_REVEAL           = 0.30
_W_FORESHADOW_BREAK = 0.25


class NarrativeImpactAnalyzer:
    """Computes the narrative blast radius of a proposed scene change.

    Usage::

        analyzer = NarrativeImpactAnalyzer(store)
        report = analyzer.analyze("scene_03")
    """

    def __init__(self, store: NarrativeGraphStore) -> None:
        self._store = store

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, scene_id: str, max_depth: int = 2) -> NarrativeImpactReport:
        """Return a NarrativeImpactReport for a proposed change to *scene_id*."""
        if self._store.get_node(scene_id) is None:
            return NarrativeImpactReport(
                target_scene_id=scene_id,
                decision="proceed",
                reason="scene not in graph",
            )

        direct_ids:   Set[str] = self._store.neighbors(scene_id, depth=1)
        visited_all:  Set[str] = {scene_id} | direct_ids

        indirect_ids: Set[str] = set()
        if max_depth >= 2:
            for d1_id in direct_ids:
                for nb in self._store.neighbors(d1_id, depth=1):
                    if nb not in visited_all:
                        indirect_ids.add(nb)
            visited_all |= indirect_ids

        # Reveal nodes in blast radius
        reveal_ids: List[str] = [
            nid for nid in (direct_ids | indirect_ids)
            if self._store.get_node(nid) is not None
            and self._store.get_node(nid).node_type == NarrativeNodeType.REVEAL
        ]

        # Motif nodes in blast radius
        motif_ids: List[str] = [
            nid for nid in (direct_ids | indirect_ids)
            if self._store.get_node(nid) is not None
            and self._store.get_node(nid).node_type == NarrativeNodeType.MOTIF
        ]

        # Foreshadow breaks: MOTIF→future_scene where future_scene in blast radius
        foreshadow_breaks: List[str] = []
        for edge in self._store.edges_by_type(NarrativeEdgeType.FORESHADOWS):
            if edge.dst_id in visited_all and edge.dst_id != scene_id:
                if edge.src_id not in foreshadow_breaks:
                    foreshadow_breaks.append(edge.src_id)

        # Risk score
        risk_score = round(
            min(
                len(direct_ids)       * _W_DIRECT
                + len(indirect_ids)   * _W_INDIRECT
                + len(reveal_ids)     * _W_REVEAL
                + len(foreshadow_breaks) * _W_FORESHADOW_BREAK,
                1.0,
            ),
            4,
        )

        risk_level, decision = self._classify(risk_score)

        return NarrativeImpactReport(
            target_scene_id=scene_id,
            direct_impact=sorted(direct_ids),
            indirect_impact=sorted(indirect_ids),
            reveal_impacts=reveal_ids,
            motif_impacts=motif_ids,
            foreshadow_breaks=foreshadow_breaks,
            risk_score=risk_score,
            risk_level=risk_level,
            decision=decision,
        )

    def bulk_analyze(
        self, scene_ids: List[str], max_depth: int = 2
    ) -> Dict[str, NarrativeImpactReport]:
        return {sid: self.analyze(sid, max_depth) for sid in scene_ids}

    @staticmethod
    def _classify(risk_score: float):
        if risk_score >= _CRITICAL:
            return "critical", "hold"
        if risk_score >= _HIGH:
            return "high", "split_required"
        if risk_score >= _MEDIUM:
            return "medium", "review"
        return "low", "proceed"
