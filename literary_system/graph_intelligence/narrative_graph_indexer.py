"""V528 — NarrativeGraphIndexer
Auto-indexes NIL loop outputs into NarrativeGraphStore.
LLM-0 compliant: zero LLM calls.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from literary_system.graph_intelligence.narrative_graph_schema import (
    NarrativeEdgeType, NarrativeNodeType,
    CharacterNode, SceneNode, EventNode, SecretNode, RevealNode,
    MotifNode, RelationshipNode, EmotionPressureNode, TimeDeltaNode,
    DialogueIntentNode, NarrativeEdge,
)
from literary_system.graph_intelligence.narrative_graph_store import NarrativeGraphStore


@dataclass
class IndexInput:
    """Structured input for NarrativeGraphIndexer.
    All fields optional — partial data can be indexed incrementally.
    """
    scene_id: str = ""
    scene_title: str = ""
    scene_chapter: str = ""
    scene_episode: int = 1
    scene_idx: int = 0
    scene_position: float = 0.0          # t_position 0.0–1.0

    character_ids: List[str] = field(default_factory=list)
    character_names: Dict[str, str] = field(default_factory=dict)  # id → name

    event_ids: List[str] = field(default_factory=list)
    event_descriptions: Dict[str, str] = field(default_factory=dict)

    secrets_introduced: List[str] = field(default_factory=list)
    secrets_resolved: List[str] = field(default_factory=list)
    reveals_triggered: List[str] = field(default_factory=list)

    motif_ids: List[str] = field(default_factory=list)
    motif_labels: Dict[str, str] = field(default_factory=dict)

    # [{from_char, to_char, rel_type, delta_strength}]
    relationship_updates: List[Dict[str, Any]] = field(default_factory=list)

    # [{scene_id, character_id, emotion, intensity}]
    emotion_peaks: List[Dict[str, Any]] = field(default_factory=list)

    time_delta_minutes: Optional[float] = None
    time_label: str = ""

    # [{speaker_id, intent_type, target_id}]
    dialogue_intents: List[Dict[str, Any]] = field(default_factory=list)

    caused_event_ids: List[str] = field(default_factory=list)
    depends_on_scene_ids: List[str] = field(default_factory=list)
    foreshadow_links: Dict[str, str] = field(default_factory=dict)  # motif_id → future_scene_id


@dataclass
class IndexResult:
    nodes_added: int = 0
    edges_added: int = 0
    nodes_updated: int = 0
    warnings: List[str] = field(default_factory=list)

    def merge(self, other: "IndexResult") -> None:
        self.nodes_added   += other.nodes_added
        self.edges_added   += other.edges_added
        self.nodes_updated += other.nodes_updated
        self.warnings.extend(other.warnings)


class NarrativeGraphIndexer:
    """Translates IndexInput records into NarrativeGraphStore mutations.

    Idempotent, LLM-0, incremental.
    """

    def __init__(self, store: NarrativeGraphStore) -> None:
        self._store = store

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def index(self, inp: IndexInput) -> IndexResult:
        result = IndexResult()
        if not inp.scene_id:
            result.warnings.append("IndexInput.scene_id is empty — skipped")
            return result
        self._ensure_scene(inp, result)
        self._ensure_characters(inp, result)
        self._ensure_events(inp, result)
        self._ensure_secrets_reveals(inp, result)
        self._ensure_motifs(inp, result)
        self._ensure_relationships(inp, result)
        self._ensure_emotion_peaks(inp, result)
        self._ensure_time_delta(inp, result)
        self._ensure_dialogue_intents(inp, result)
        self._wire_causal_edges(inp, result)
        self._wire_dependency_edges(inp, result)
        self._wire_foreshadow_edges(inp, result)
        return result

    def index_batch(self, inputs: List[IndexInput]) -> IndexResult:
        merged = IndexResult()
        for inp in inputs:
            merged.merge(self.index(inp))
        return merged

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _upsert_node(self, node, result: IndexResult) -> bool:
        if self._store.get_node(node.node_id) is None:
            self._store.add_node(node)
            result.nodes_added += 1
            return True
        result.nodes_updated += 1
        return False

    def _add_edge(
        self,
        src_id: str,
        dst_id: str,
        edge_type: NarrativeEdgeType,
        weight: float = 1.0,
        meta: Optional[Dict[str, Any]] = None,
        result: Optional[IndexResult] = None,
    ) -> None:
        """Add edge, deduplicated by (src, dst, edge_type)."""
        for e in self._store.edges_from(src_id):
            if e.dst_id == dst_id and e.edge_type == edge_type:
                return
        eid = self._store.make_edge_id()
        edge = NarrativeEdge(
            edge_id=eid,
            src_id=src_id,
            dst_id=dst_id,
            edge_type=edge_type,
            weight=weight,
            meta=meta or {},
        )
        self._store.add_edge(edge)
        if result is not None:
            result.edges_added += 1

    # ------------------------------------------------------------------
    # Node / edge builders (field names must match schema exactly)
    # ------------------------------------------------------------------

    def _ensure_scene(self, inp: IndexInput, result: IndexResult) -> None:
        # SceneNode fields: episode, scene_idx, t_position
        node = SceneNode(
            node_id=inp.scene_id,
            node_type=NarrativeNodeType.SCENE,
            label=inp.scene_title or inp.scene_id,
            episode=inp.scene_episode,
            scene_idx=inp.scene_idx,
            t_position=inp.scene_position,
            meta={"chapter": inp.scene_chapter},
        )
        self._upsert_node(node, result)

    def _ensure_characters(self, inp: IndexInput, result: IndexResult) -> None:
        # CharacterNode fields: role, episode_first, episode_last
        for char_id in inp.character_ids:
            name = inp.character_names.get(char_id, char_id)
            node = CharacterNode(
                node_id=char_id,
                node_type=NarrativeNodeType.CHARACTER,
                label=name,
                episode_first=inp.scene_episode,
                meta={"name": name},
            )
            self._upsert_node(node, result)
            self._add_edge(char_id, inp.scene_id, NarrativeEdgeType.DEPENDS_ON, result=result)

    def _ensure_events(self, inp: IndexInput, result: IndexResult) -> None:
        # EventNode fields: episode, scene_id, impact
        for ev_id in inp.event_ids:
            desc = inp.event_descriptions.get(ev_id, ev_id)
            node = EventNode(
                node_id=ev_id,
                node_type=NarrativeNodeType.EVENT,
                label=desc,
                episode=inp.scene_episode,
                scene_id=inp.scene_id,
            )
            self._upsert_node(node, result)
            self._add_edge(inp.scene_id, ev_id, NarrativeEdgeType.CAUSES, result=result)

    def _ensure_secrets_reveals(self, inp: IndexInput, result: IndexResult) -> None:
        # SecretNode fields: holder_ids, reveal_episode
        for sec_id in inp.secrets_introduced:
            node = SecretNode(
                node_id=sec_id,
                node_type=NarrativeNodeType.SECRET,
                label=sec_id,
                meta={"introduced_in": inp.scene_id},
            )
            self._upsert_node(node, result)
            self._add_edge(inp.scene_id, sec_id, NarrativeEdgeType.HIDES, result=result)
        for sec_id in inp.secrets_resolved:
            if self._store.get_node(sec_id) is None:
                node = SecretNode(
                    node_id=sec_id, node_type=NarrativeNodeType.SECRET, label=sec_id
                )
                self._upsert_node(node, result)
            self._add_edge(inp.scene_id, sec_id, NarrativeEdgeType.RELIEVES, result=result)
        # RevealNode fields: secret_id, reveal_episode, reveal_scene, audience_only
        for rev_id in inp.reveals_triggered:
            node = RevealNode(
                node_id=rev_id,
                node_type=NarrativeNodeType.REVEAL,
                label=rev_id,
                reveal_episode=inp.scene_episode,
                reveal_scene=inp.scene_id,
            )
            self._upsert_node(node, result)
            self._add_edge(inp.scene_id, rev_id, NarrativeEdgeType.REVEALS, result=result)

    def _ensure_motifs(self, inp: IndexInput, result: IndexResult) -> None:
        # MotifNode fields: symbol, appearances
        for mot_id in inp.motif_ids:
            label = inp.motif_labels.get(mot_id, mot_id)
            node = MotifNode(
                node_id=mot_id,
                node_type=NarrativeNodeType.MOTIF,
                label=label,
                symbol=label,
                appearances=[inp.scene_id],
            )
            self._upsert_node(node, result)
            self._add_edge(inp.scene_id, mot_id, NarrativeEdgeType.ECHOES, result=result)

    def _ensure_relationships(self, inp: IndexInput, result: IndexResult) -> None:
        # RelationshipNode fields: char_a_id, char_b_id, rel_type, episode
        for upd in inp.relationship_updates:
            from_c   = upd.get("from_char", "")
            to_c     = upd.get("to_char", "")
            if not from_c or not to_c:
                continue
            rel_id   = f"rel_{from_c}_{to_c}"
            delta    = float(upd.get("delta_strength", 0.0))
            rel_type = upd.get("rel_type", "neutral")
            node = RelationshipNode(
                node_id=rel_id,
                node_type=NarrativeNodeType.RELATIONSHIP,
                label=f"{from_c}↔{to_c}",
                char_a_id=from_c,
                char_b_id=to_c,
                rel_type=rel_type,
                episode=inp.scene_episode,
            )
            self._upsert_node(node, result)
            w = max(0.0, 1.0 + delta)
            self._add_edge(from_c, rel_id, NarrativeEdgeType.KNOWS, weight=w, result=result)
            self._add_edge(to_c,   rel_id, NarrativeEdgeType.KNOWS, weight=w, result=result)
            if delta > 0:
                self._add_edge(inp.scene_id, rel_id, NarrativeEdgeType.ESCALATES, result=result)
            elif delta < 0:
                self._add_edge(inp.scene_id, rel_id, NarrativeEdgeType.RELIEVES, result=result)

    def _ensure_emotion_peaks(self, inp: IndexInput, result: IndexResult) -> None:
        # EmotionPressureNode fields: char_id, pressure, episode
        for peak in inp.emotion_peaks:
            scene_id  = peak.get("scene_id", inp.scene_id)
            char_id   = peak.get("character_id", "")
            emotion   = peak.get("emotion", "unknown")
            intensity = float(peak.get("intensity", 0.5))
            ep_id = f"ep_{scene_id}_{char_id}_{emotion}"
            node = EmotionPressureNode(
                node_id=ep_id,
                node_type=NarrativeNodeType.EMOTION_PRESSURE,
                label=f"{emotion}@{char_id}",
                char_id=char_id,
                pressure=intensity,
                episode=inp.scene_episode,
            )
            self._upsert_node(node, result)
            self._add_edge(scene_id, ep_id, NarrativeEdgeType.ESCALATES, weight=intensity, result=result)
            if char_id and self._store.get_node(char_id) is not None:
                self._add_edge(char_id, ep_id, NarrativeEdgeType.CAUSES, result=result)

    def _ensure_time_delta(self, inp: IndexInput, result: IndexResult) -> None:
        # TimeDeltaNode fields: from_scene, to_scene, delta_days
        if inp.time_delta_minutes is None:
            return
        td_id = f"td_{inp.scene_id}"
        node = TimeDeltaNode(
            node_id=td_id,
            node_type=NarrativeNodeType.TIME_DELTA,
            label=inp.time_label or f"+{inp.time_delta_minutes}m",
            from_scene=inp.scene_id,
            delta_days=int(inp.time_delta_minutes // 1440),
        )
        self._upsert_node(node, result)
        self._add_edge(inp.scene_id, td_id, NarrativeEdgeType.CAUSES, result=result)

    def _ensure_dialogue_intents(self, inp: IndexInput, result: IndexResult) -> None:
        # DialogueIntentNode fields: scene_id, char_id, surface_text, hidden_intent
        for di in inp.dialogue_intents:
            speaker = di.get("speaker_id", "")
            intent  = di.get("intent_type", "unknown")
            target  = di.get("target_id", "")
            if not speaker:
                continue
            di_id = f"di_{inp.scene_id}_{speaker}_{intent}"
            node = DialogueIntentNode(
                node_id=di_id,
                node_type=NarrativeNodeType.DIALOGUE_INTENT,
                label=f"{intent}:{speaker}→{target}",
                scene_id=inp.scene_id,
                char_id=speaker,
                hidden_intent=intent,
            )
            self._upsert_node(node, result)
            self._add_edge(inp.scene_id, di_id, NarrativeEdgeType.CAUSES, result=result)

    def _wire_causal_edges(self, inp: IndexInput, result: IndexResult) -> None:
        for ev_id in inp.caused_event_ids:
            if self._store.get_node(ev_id) is None:
                node = EventNode(
                    node_id=ev_id, node_type=NarrativeNodeType.EVENT, label=ev_id
                )
                self._upsert_node(node, result)
            self._add_edge(inp.scene_id, ev_id, NarrativeEdgeType.CAUSES, result=result)

    def _wire_dependency_edges(self, inp: IndexInput, result: IndexResult) -> None:
        for dep_id in inp.depends_on_scene_ids:
            if self._store.get_node(dep_id) is None:
                node = SceneNode(
                    node_id=dep_id, node_type=NarrativeNodeType.SCENE, label=dep_id
                )
                self._upsert_node(node, result)
            self._add_edge(inp.scene_id, dep_id, NarrativeEdgeType.DEPENDS_ON, result=result)

    def _wire_foreshadow_edges(self, inp: IndexInput, result: IndexResult) -> None:
        for mot_id, future_scene_id in inp.foreshadow_links.items():
            if self._store.get_node(mot_id) is None:
                node = MotifNode(
                    node_id=mot_id, node_type=NarrativeNodeType.MOTIF, label=mot_id
                )
                self._upsert_node(node, result)
            if self._store.get_node(future_scene_id) is None:
                node = SceneNode(
                    node_id=future_scene_id, node_type=NarrativeNodeType.SCENE,
                    label=future_scene_id
                )
                self._upsert_node(node, result)
            self._add_edge(mot_id, future_scene_id, NarrativeEdgeType.FORESHADOWS, result=result)
