"""
literary_system/physics/__init__.py
V383 NarrativePhysics Engine Layer

4개 물리 엔진을 통합 실행하는 파사드 클래스.
모든 엔진은 LLM 0회 — 순수 결정론적.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from literary_system.physics.conflict_collision import ConflictCollisionCalculus, ConflictCollisionResult
from literary_system.physics.scene_energy import SceneEnergyConservationAudit, EnergyAuditResult, SceneEnergyViolation
from literary_system.physics.motif_residue import MotifResidueGraphBuilder, MotifResidueGraph, MotifOrphanWarning
from literary_system.physics.curiosity_gradient import AudienceCuriosityGradientEngine, CuriosityResult, CuriosityCollapseError
from literary_system.physics.fitness_score import NarrativeFitnessScore, NarrativeFitnessComponents
from literary_system.physics.coefficient_store import PhysicsCoefficientStore


@dataclass
class PhysicsRunResult:
    """NarrativePhysicsEngine.run() 결과."""
    conflict:            ConflictCollisionResult
    energy:              EnergyAuditResult
    motif_graph:         MotifResidueGraph
    curiosity:           CuriosityResult
    components:          NarrativeFitnessComponents
    fitness:             float
    energy_violations:   List[SceneEnergyViolation]  = field(default_factory=list)
    curiosity_collapses: List[CuriosityCollapseError] = field(default_factory=list)
    motif_orphan_warnings: List[MotifOrphanWarning]  = field(default_factory=list)


class NarrativePhysicsEngine:
    """4개 물리 엔진 통합 실행 파사드."""

    def __init__(self, coefficient_store: PhysicsCoefficientStore | None = None):
        self._store   = coefficient_store or PhysicsCoefficientStore()
        self._conflict  = ConflictCollisionCalculus()
        self._energy    = SceneEnergyConservationAudit()
        self._motif     = MotifResidueGraphBuilder()
        self._curiosity = AudienceCuriosityGradientEngine()
        self._fitness   = NarrativeFitnessScore(self._store)

    def run(self, scene_context: dict) -> PhysicsRunResult:
        """
        Args:
            scene_context: {
                'character_ids': list[str],
                'cluster_weights': dict[str, float],
                'conflict_edges': list[tuple[str,str]],
                'energy_input': float,
                'energy_output': float,
                'motif_appearances': dict[str, int],  # motif_id → count
                'motif_last_seen': dict[str, int],    # motif_id → episode_idx
                'episode_idx': int,
                'reader_uncertainty': float,
                'reveal_ratio': float,
                'arc_tension': float,
                'reader_surface_score': float,
                'arc_tension_score': float,
            }
        """
        energy_violations:    list = []
        curiosity_collapses:  list = []

        # 1. 갈등 충돌
        conflict = self._conflict.calculate(
            character_ids   = scene_context.get('character_ids', []),
            conflict_edges  = scene_context.get('conflict_edges', []),
            cluster_weights = scene_context.get('cluster_weights', {}),
        )

        # 2. 에너지 보존
        energy = self._energy.audit(
            energy_input  = scene_context.get('energy_input', 0.5),
            energy_output = scene_context.get('energy_output', 0.5),
            scene_id      = scene_context.get('scene_id', 'unknown'),
        )
        if energy.violation:
            energy_violations.append(energy.violation)

        # 3. 모티프 잔상
        motif_graph = self._motif.build(
            motif_appearances = scene_context.get('motif_appearances', {}),
            motif_last_seen   = scene_context.get('motif_last_seen', {}),
            current_episode   = scene_context.get('episode_idx', 0),
        )

        # 4. 호기심 기울기
        curiosity = self._curiosity.calculate(
            reader_uncertainty = scene_context.get('reader_uncertainty', 0.5),
            reveal_ratio       = scene_context.get('reveal_ratio', 0.3),
            arc_tension        = scene_context.get('arc_tension', 0.5),
            episode_idx        = scene_context.get('episode_idx', 0),
        )
        if curiosity.collapse_error:
            curiosity_collapses.append(curiosity.collapse_error)

        # 5. NarrativeFitnessScore
        components = NarrativeFitnessComponents(
            conflict_intensity   = conflict.conflict_intensity,
            scene_energy_ratio   = energy.energy_ratio,
            motif_residue_score  = motif_graph.average_residue,
            curiosity_gradient   = max(curiosity.gradient, 0.0),
            reader_surface_score = scene_context.get('reader_surface_score', 0.5),
            arc_tension_score    = scene_context.get('arc_tension_score', 0.5),
        )
        fitness = self._fitness.calculate(components)

        return PhysicsRunResult(
            conflict             = conflict,
            energy               = energy,
            motif_graph          = motif_graph,
            curiosity            = curiosity,
            components           = components,
            fitness              = fitness,
            energy_violations    = energy_violations,
            curiosity_collapses  = curiosity_collapses,
            motif_orphan_warnings = motif_graph.orphan_warnings,
        )
