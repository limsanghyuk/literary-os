"""
V383 — PhysicsValidationGate (Gate 7)
Gate 6 통과 후 실행. NarrativeFitnessScore + 물리 엔진 결과 검증.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING

from literary_system.physics import NarrativePhysicsEngine, PhysicsRunResult
from literary_system.physics.coefficient_store import PhysicsCoefficientStore

if TYPE_CHECKING:
    from literary_system.pipeline.pipeline_state import LiteraryPipelineState


class PhysicsGateFailure(Exception):
    def __init__(self, failures: list):
        self.failures = failures
        msgs = "; ".join(str(f) for f in failures)
        super().__init__(f"Gate 7 PhysicsValidation failed: {msgs}")


@dataclass
class GateResult:
    passed:  bool
    fitness: float
    motif_orphan_count: int = 0


class PhysicsValidationGate:
    """
    Gate 7 통과 기준:
      - NarrativeFitnessScore >= min_fitness (기본 6.0)
      - SceneEnergyViolation 0건
      - CuriosityCollapseError 0건
      - MotifOrphanWarning <= max_motif_orphans (기본 2건, 경고만)
    """

    def __init__(
        self,
        min_fitness:       float = 6.0,
        max_motif_orphans: int   = 2,
        coefficient_store: PhysicsCoefficientStore | None = None,
    ) -> None:
        self._min_fitness    = min_fitness
        self._max_orphans    = max_motif_orphans
        self._engine         = NarrativePhysicsEngine(coefficient_store)

    def run(
        self,
        scene_context:   dict,
        pipeline_state,          # LiteraryPipelineState
    ) -> GateResult:
        result: PhysicsRunResult = self._engine.run(scene_context)
        failures = []

        if result.fitness < self._min_fitness:
            failures.append(
                f"NarrativeFitness={result.fitness:.2f} < {self._min_fitness}"
            )
        if result.energy_violations:
            failures.append(
                f"SceneEnergyViolation x{len(result.energy_violations)}"
            )
        if result.curiosity_collapses:
            failures.append(
                f"CuriosityCollapseError x{len(result.curiosity_collapses)}"
            )

        orphan_count = len(result.motif_orphan_warnings)

        # execution_trace 기록
        trace_data = {
            "fitness":              result.fitness,
            "passed":               len(failures) == 0,
            "energy_violations":    len(result.energy_violations),
            "curiosity_collapses":  len(result.curiosity_collapses),
            "motif_orphans":        orphan_count,
            "conflict_intensity":   result.conflict.conflict_intensity,
        }
        if hasattr(pipeline_state, 'append_trace'):
            pipeline_state.append_trace('gate7', trace_data)

        if failures:
            if hasattr(pipeline_state, 'save_literary_checkpoint'):
                pipeline_state.save_literary_checkpoint('gate7_fail')
            raise PhysicsGateFailure(failures)

        return GateResult(
            passed           = True,
            fitness          = result.fitness,
            motif_orphan_count = orphan_count,
        )
