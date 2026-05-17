"""V536 — NILGraphBridge
Translates NILResult outputs from NILOrchestrator into NarrativeGraph mutations
via NarrativeGraphIndexer.
LLM-0 compliant: zero LLM calls.

This is the wiring layer that connects:
  NILOrchestrator.process_scene() → NILGraphBridge → NarrativeGraphIndexer → NarrativeGraphStore
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from literary_system.graph_intelligence.narrative_graph_indexer import (
    IndexInput, IndexResult, NarrativeGraphIndexer,
)
from literary_system.graph_intelligence.narrative_graph_store import NarrativeGraphStore


@dataclass
class NILGraphBridgeConfig:
    """Configuration for NILGraphBridge behaviour."""
    # Tension threshold above which we create an EmotionPressure node
    tension_pressure_threshold: float = 0.65
    # AMW weight key used to infer character relationship delta
    amw_relationship_key: str = "sympathy"
    # Maximum relationship delta to record (clip extreme AMW values)
    max_rel_delta: float = 2.0
    # Whether to record time delta nodes
    record_time_delta: bool = True
    # Minutes per scene slot (used when recording time delta)
    minutes_per_scene: float = 5.0


class NILGraphBridge:
    """Converts NILResult objects into NarrativeGraphStore mutations.

    Usage::

        store   = NarrativeGraphStore()
        indexer = NarrativeGraphIndexer(store)
        bridge  = NILGraphBridge(indexer)

        # Inside the NIL loop:
        nil_result = orchestrator.process_scene(scene_input)
        index_result = bridge.ingest(nil_result, scene_input)

    Design
    ------
    * All NILResult fields are mapped to IndexInput fields.
    * Character interaction updates (CIM deltas) become relationship_updates.
    * High-tension moments become emotion_peaks.
    * RAG intent (if present) becomes a dialogue_intent entry.
    * LLM-0: zero LLM calls; all inference is arithmetic.
    """

    def __init__(
        self,
        indexer: NarrativeGraphIndexer,
        config: Optional[NILGraphBridgeConfig] = None,
    ) -> None:
        self._indexer = indexer
        self._cfg     = config or NILGraphBridgeConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest(self, nil_result, scene_input) -> IndexResult:
        """Translate one NILResult + SceneInput into IndexInput and index it.

        Parameters
        ----------
        nil_result : NILResult (from literary_system.nie.nil_orchestrator)
        scene_input: SceneInput (from literary_system.nie.nil_orchestrator)

        Returns
        -------
        IndexResult with nodes/edges added counts.
        """
        inp = self._build_index_input(nil_result, scene_input)
        return self._indexer.index(inp)

    def ingest_batch(self, pairs: List[Tuple]) -> IndexResult:
        """Ingest a list of (nil_result, scene_input) pairs."""
        merged = IndexResult()
        for nil_result, scene_input in pairs:
            r = self.ingest(nil_result, scene_input)
            merged.merge(r)
        return merged

    # ------------------------------------------------------------------
    # Translation logic
    # ------------------------------------------------------------------

    def _build_index_input(self, nil_result, scene_input) -> IndexInput:
        inp = IndexInput(
            scene_id=nil_result.scene_id,
            scene_title=f"Scene-{nil_result.scene_id}",
            scene_episode=getattr(scene_input, "episode_idx", 0),
            scene_idx=getattr(scene_input, "episode_idx", 0),
            scene_position=self._compute_position(scene_input),
        )

        # --- Characters from CIM updates ---
        char_ids, char_names, rel_updates = self._extract_characters(nil_result, scene_input)
        inp.character_ids         = char_ids
        inp.character_names       = char_names
        inp.relationship_updates  = rel_updates

        # --- Emotion peaks from tension metric ---
        inp.emotion_peaks = self._extract_emotion_peaks(nil_result, scene_input)

        # --- Dialogue intent from RAG intent ---
        if getattr(nil_result, "step6_rag_intent", None):
            inp.dialogue_intents = [{
                "speaker_id": "narrator",
                "intent_type": nil_result.step6_rag_intent,
                "target_id": "",
            }]

        # --- Time delta ---
        if self._cfg.record_time_delta:
            inp.time_delta_minutes = self._cfg.minutes_per_scene
            inp.time_label = f"+{self._cfg.minutes_per_scene:.0f}m"

        # --- MAE stability event as a secret (unresolved tension) ---
        if getattr(nil_result, "stability_event", None) is not None:
            sec_id = f"stab_{nil_result.scene_id}"
            inp.secrets_introduced = [sec_id]

        return inp

    @staticmethod
    def _compute_position(scene_input) -> float:
        idx   = getattr(scene_input, "episode_idx", 0)
        total = getattr(scene_input, "total_scenes", 1) or 1
        return round(idx / total, 4)

    def _extract_characters(
        self, nil_result, scene_input
    ) -> Tuple[List[str], Dict[str, str], List[Dict]]:
        char_updates = getattr(scene_input, "char_updates", []) or []
        char_set: Dict[str, str] = {}
        rel_updates = []

        for item in char_updates:
            if len(item) < 3:
                continue
            ci, cj, delta = item[0], item[1], float(item[2])
            char_set[ci] = ci
            char_set[cj] = cj
            delta_clipped = max(-self._cfg.max_rel_delta,
                                min(delta, self._cfg.max_rel_delta))
            rel_updates.append({
                "from_char": ci,
                "to_char":   cj,
                "rel_type":  self._cfg.amw_relationship_key,
                "delta_strength": delta_clipped,
            })

        # Infer characters from AMW vector keys if no explicit updates
        amw = getattr(nil_result, "step3_amw_vector", {}) or {}
        for k in amw:
            if "_" in k:
                parts = k.split("_", 1)
                for p in parts:
                    if p and p not in char_set:
                        char_set[p] = p

        return list(char_set.keys()), char_set, rel_updates

    def _extract_emotion_peaks(self, nil_result, scene_input) -> List[Dict]:
        peaks = []
        metrics = getattr(scene_input, "metrics", {}) or {}
        tension = metrics.get("tension", getattr(nil_result, "actual_tension", 0.0))
        if tension >= self._cfg.tension_pressure_threshold:
            # Associate with all known characters from char_updates
            char_updates = getattr(scene_input, "char_updates", []) or []
            seen = set()
            for item in char_updates:
                for c in item[:2]:
                    if c not in seen:
                        peaks.append({
                            "scene_id":     nil_result.scene_id,
                            "character_id": c,
                            "emotion":      "tension",
                            "intensity":    round(float(tension), 4),
                        })
                        seen.add(c)
            if not seen:
                peaks.append({
                    "scene_id":     nil_result.scene_id,
                    "character_id": "ensemble",
                    "emotion":      "tension",
                    "intensity":    round(float(tension), 4),
                })
        return peaks
