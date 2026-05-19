"""V389 — EnsembleGate (Gate 8). REJECT/SELECT/MERGE 결정을 execution_trace에 기록."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from literary_system.ensemble.narrative_fitness_arbiter import (
    CandidateScore,
    EnsembleDecision,
    EnsembleDecisionType,
    NarrativeFitnessArbiter,
)


class EnsembleGateFailure(Exception):
    def __init__(self, decision: EnsembleDecision):
        self.decision = decision
        super().__init__(f"Gate 8 EnsembleGate REJECT: {decision.reason}")


@dataclass
class EnsembleGateResult:
    passed:   bool
    decision: EnsembleDecision


class EnsembleGateV1:
    """
    Gate 8: Provider Ensemble 중재 게이트.
    모든 결정은 execution_trace에 기록. REJECT 시 checkpoint 저장.
    """

    def __init__(self) -> None:
        self._arbiter = NarrativeFitnessArbiter()

    def run(
        self,
        candidates:     List[CandidateScore],
        pipeline_state,
    ) -> EnsembleGateResult:
        decision = self._arbiter.arbitrate(candidates)

        trace_data = {
            "decision": decision.decision_type.value,
            "reason":   decision.reason,
            "top_score": candidates[0].total_score if candidates else 0.0,
            "candidate_count": len(candidates),
        }
        if decision.selected:
            trace_data["selected_provider"] = decision.selected
        if decision.merge_map:
            trace_data["merge_map"] = decision.merge_map

        if hasattr(pipeline_state, 'append_trace'):
            pipeline_state.append_trace('gate8', trace_data)
        elif hasattr(pipeline_state, 'execution_trace'):
            pipeline_state.execution_trace.append(
                f"[gate8] {decision.decision_type.value}: {decision.reason}"
            )

        if decision.decision_type == EnsembleDecisionType.REJECT:
            if hasattr(pipeline_state, 'save_literary_checkpoint'):
                pipeline_state.save_literary_checkpoint('gate8_reject')
            elif hasattr(pipeline_state, 'checkpoints'):
                pipeline_state.checkpoints['gate8_reject'] = {"reason": decision.reason}
            raise EnsembleGateFailure(decision)

        return EnsembleGateResult(passed=True, decision=decision)

EnsembleGate = EnsembleGateV1  # V579 backward-compat alias
