"""V360: ContractBridge v1 — GPT-Claude SceneIntentIR 공유."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

class SceneIntent(Enum):
    REVEAL       = "reveal"
    CONCEAL      = "conceal"
    FORESHADOW   = "foreshadow"
    TURN         = "turn"
    ESTABLISH    = "establish"
    RESOLVE      = "resolve"

@dataclass
class SceneIntentIR:
    scene_id:       str
    intent:         SceneIntent
    emotional_delta: float = 0.0
    style_directive: str   = ""
    reveal_budget:   float = 0.3
    pov_character:   str   = ""
    target_tension:  float = 0.5
    metadata:        Dict[str, Any] = field(default_factory=dict)

@dataclass
class CrossValidationResult:
    scene_id:        str
    gpt_ir:          Optional[SceneIntentIR]
    claude_ir:       Optional[SceneIntentIR]
    is_consistent:   bool
    conflicts:       List[str]
    consensus_ir:    Optional[SceneIntentIR] = None

class ContractBridge:
    def __init__(self) -> None:
        self._gpt_contracts:    Dict[str, SceneIntentIR] = {}
        self._claude_contracts: Dict[str, SceneIntentIR] = {}

    def register_gpt_contract(self, scene_id: str, ir: SceneIntentIR) -> None:
        self._gpt_contracts[scene_id] = ir

    def register_claude_contract(self, scene_id: str, ir: SceneIntentIR) -> None:
        self._claude_contracts[scene_id] = ir

    def cross_validate(self, scene_id: str) -> CrossValidationResult:
        gpt_ir    = self._gpt_contracts.get(scene_id)
        claude_ir = self._claude_contracts.get(scene_id)
        conflicts: List[str] = []
        if gpt_ir is None or claude_ir is None:
            return CrossValidationResult(scene_id, gpt_ir, claude_ir, True, [])
        if gpt_ir.intent != claude_ir.intent:
            conflicts.append(f"intent: GPT={gpt_ir.intent.value} / Claude={claude_ir.intent.value}")
        delta = abs(gpt_ir.target_tension - claude_ir.target_tension)
        if delta > 0.3:
            conflicts.append(f"tension 차이: {delta:.2f}")
        delta_b = abs(gpt_ir.reveal_budget - claude_ir.reveal_budget)
        if delta_b > 0.2:
            conflicts.append(f"reveal_budget 차이: {delta_b:.2f}")
        is_consistent = len(conflicts) == 0
        consensus = None
        if is_consistent:
            consensus = SceneIntentIR(
                scene_id=scene_id,
                intent=gpt_ir.intent,
                emotional_delta=(gpt_ir.emotional_delta + claude_ir.emotional_delta) / 2,
                reveal_budget=(gpt_ir.reveal_budget + claude_ir.reveal_budget) / 2,
                target_tension=(gpt_ir.target_tension + claude_ir.target_tension) / 2,
            )
        return CrossValidationResult(scene_id, gpt_ir, claude_ir, is_consistent, conflicts, consensus)

    def validate_all(self) -> Dict[str, CrossValidationResult]:
        all_ids = set(self._gpt_contracts) | set(self._claude_contracts)
        return {sid: self.cross_validate(sid) for sid in all_ids}

    def scene_ids(self) -> List[str]:
        return list(set(self._gpt_contracts) | set(self._claude_contracts))
