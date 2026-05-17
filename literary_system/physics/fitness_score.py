"""V383 — NarrativeFitnessScore. 6컴포넌트 가중합 × 10.0 → [0, 10]."""
from __future__ import annotations
from dataclasses import dataclass
from literary_system.physics.coefficient_store import PhysicsCoefficientStore


@dataclass
class NarrativeFitnessComponents:
    conflict_intensity:   float  # ConflictCollisionCalculus
    scene_energy_ratio:   float  # SceneEnergyConservationAudit (1 - loss_ratio)
    motif_residue_score:  float  # MotifResidueGraphBuilder avg_residue
    curiosity_gradient:   float  # AudienceCuriosityGradientEngine
    reader_surface_score: float  # ReaderSurfaceScorer (기존)
    arc_tension_score:    float  # SeriesArcPlanner.tension_at() (기존)


class NarrativeFitnessScore:
    """
    score = (weighted_sum / weight_total) * 10.0
    가중치 합이 1.0이 아닐 경우 자동 정규화.
    """

    def __init__(self, store: PhysicsCoefficientStore | None = None) -> None:
        self._store = store or PhysicsCoefficientStore()

    def calculate(self, components: NarrativeFitnessComponents) -> float:
        s = self._store
        raw = (
            components.conflict_intensity   * s.conflict_weight       +
            components.scene_energy_ratio   * s.scene_energy_weight   +
            components.motif_residue_score  * s.motif_weight          +
            components.curiosity_gradient   * s.curiosity_weight      +
            components.reader_surface_score * s.arc_pressure_coupling +
            components.arc_tension_score    * s.prose_physics_bridge
        )
        total_weight = s.weight_sum()
        if total_weight <= 0:
            return 0.0
        normalized = raw / total_weight
        return max(0.0, min(10.0, normalized * 10.0))
