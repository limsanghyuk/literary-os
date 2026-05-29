"""V328 Task16: CausalContinuationPlanBuilder — 핸드오프 기반 인과 연속 계획 (단절 F)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CausalPlan:
    episode_no:  int
    seeds:       list[str] = field(default_factory=list)
    tension_fwd: float     = 0.5
    key_events:  list[str] = field(default_factory=list)
    built:       bool      = False

class CausalContinuationPlanBuilder:
    def __init__(self, handoff_store=None):
        self._store = handoff_store

    def build(self, episode_no: int, handoff_data: dict | None = None) -> CausalPlan:
        plan = CausalPlan(episode_no=episode_no)
        data = handoff_data or {}
        if not data and self._store is not None:
            try:
                data = self._store.get_handoff(episode_no - 1) or {}
            except Exception:
                pass
        plan.seeds       = data.get("seeds", [])
        plan.tension_fwd = float(data.get("tension_forward", 0.5))
        plan.key_events  = data.get("key_events", [])
        plan.built       = True
        return plan
