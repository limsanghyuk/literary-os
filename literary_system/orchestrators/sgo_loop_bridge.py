"""V328 Task15: SGOLoopBridge — E2ELoop ↔ SGO 통합 (단절 C)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

MAX_RERENDERS = 2

@dataclass
class SGOLoopResult:
    project_id:       str
    episode_no:       int
    final_text:       str        = ""
    scenes_generated: int        = 0
    rerenders:        int        = 0
    gate_decision:    str        = "commit"
    reader_metrics:   dict       = field(default_factory=dict)
    success:          bool       = True
    error:            str        = ""

class SGOLoopBridge:
    def __init__(self, sgo=None, reader_simulator=None, conditional_gate=None):
        self._sgo    = sgo
        self._reader = reader_simulator
        self._gate   = conditional_gate

    def run_episode(self, sequence_plans: list, project_id: str,
                    episode_no: int = 1,
                    character_states: Optional[dict] = None) -> SGOLoopResult:
        if self._sgo is None:
            return SGOLoopResult(project_id=project_id, episode_no=episode_no,
                                 success=False, error="SGO not configured")
        rerenders = 0
        result    = SGOLoopResult(project_id=project_id, episode_no=episode_no)
        try:
            e2e = self._sgo.run_episode(
                sequence_plans, episode_no=episode_no,
                character_states=character_states or {})
            scenes = getattr(e2e, "scenes", []) or getattr(e2e, "scene_records", [])
            result.scenes_generated = len(scenes)
            result.final_text       = "\n\n".join(
                getattr(s, "text", "") or getattr(s, "draft_text", "")
                for s in scenes)

            while rerenders < MAX_RERENDERS:
                gate_ok = True
                if self._gate is not None:
                    try:
                        gate_ok = self._gate.should_commit(result.final_text)
                    except Exception:
                        pass
                if gate_ok:
                    result.gate_decision = "commit"
                    break
                rerenders += 1
                result.gate_decision = "rerender"
                e2e = self._sgo.run_episode(
                    sequence_plans, episode_no=episode_no,
                    character_states=character_states or {})
                scenes = getattr(e2e, "scenes", []) or getattr(e2e, "scene_records", [])
                result.final_text = "\n\n".join(
                    getattr(s, "text", "") or getattr(s, "draft_text", "")
                    for s in scenes)
                result.gate_decision = "commit"
            result.rerenders = rerenders
        except Exception as exc:
            result.success = False
            result.error   = str(exc)
        return result
