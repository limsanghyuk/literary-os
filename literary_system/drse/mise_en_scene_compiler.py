"""V328 Task12: MiseEnSceneCompiler — DRSEEngine 직접 배선 (단절 E)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class DirectorialNote:
    tension_score:    float = 0.5
    spatial_clarity:  float = 0.5
    sensory_hints:    list  = field(default_factory=list)
    dominant_node:    str   = ""

    def to_prompt_hint(self) -> str:
        hints = ", ".join(self.sensory_hints[:3]) if self.sensory_hints else ""
        return (f"[MiseEnScene] tension={self.tension_score:.2f} "
                f"dominant={self.dominant_node} hints=[{hints}]")


class MiseEnSceneCompiler:
    def __init__(self, drse_engine=None, relation_store=None):
        self._drse  = drse_engine
        self._store = relation_store

    def compile(self, scene_id: str, scene_goal: str,
                characters: list[str]) -> DirectorialNote:
        note = DirectorialNote()
        if self._drse is None:
            return note
        try:
            scores = self._drse.score_all(scene_id=scene_id, characters=characters)
            if scores:
                dominant = max(scores, key=lambda x: x.get("tension", 0))
                note.tension_score = dominant.get("tension", 0.5)
                note.dominant_node = dominant.get("node_id", "")
                note.sensory_hints = [
                    s.get("hint", "") for s in scores if s.get("hint")
                ][:5]
        except Exception:
            pass
        return note
