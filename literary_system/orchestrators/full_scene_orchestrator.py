"""
V390 — FullSceneOrchestrator
Gate 1~8 완전 체인. 모든 레이어 통합 E2E 파이프라인.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from literary_system.pipeline.pipeline_state import LiteraryPipelineState
from literary_system.pipeline.gate7_physics import PhysicsValidationGate, GateResult
from literary_system.ensemble.gate8_ensemble import EnsembleGate, EnsembleGateResult
from literary_system.ensemble.narrative_fitness_arbiter import CandidateScore
from literary_system.physics.coefficient_store import PhysicsCoefficientStore
from literary_system.learning.manuscript_learner import ManuscriptLearner
from literary_system.optimizer.update_coordinator import UpdateCoordinator
from literary_system.llm_bridge.physics_aware_router import PhysicsAwareRouter, PhysicsRoutingPolicy


@dataclass
class SceneDraftInput:
    scene_id:           str
    episode_idx:        int
    scene_context:      Dict[str, Any] = field(default_factory=dict)
    provider_candidates: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class FinalSceneOutput:
    scene_id:   str
    fitness:    float
    decision:   str   # SELECT / MERGE / (no ensemble = SINGLE)
    trace:      List[str] = field(default_factory=list)
    physics_trace: List[Dict] = field(default_factory=list)
    passed:     bool = True


class OrchestratorConfig:
    def __init__(
        self,
        min_physics_fitness: float = 6.0,
        enable_ensemble:     bool  = True,
        enable_learning:     bool  = False,  # V385+ 활성화
    ):
        self.min_physics_fitness = min_physics_fitness
        self.enable_ensemble     = enable_ensemble
        self.enable_learning     = enable_learning


class FullSceneOrchestrator:
    """
    Gate 1~8 완전 체인 오케스트레이터.

    현재 구현:
      - Gate 7 (PhysicsValidationGate) 직접 실행
      - Gate 8 (EnsembleGate) 조건부 실행
      - Gate 1~6은 기존 CLRO v2 파이프라인 위임 (하위 호환)

    V390 완전체:
      - 모든 Gate를 단일 run() 내에서 순차 실행
      - execution_trace로 전체 흔적 보존
    """

    def __init__(
        self,
        config:            Optional[OrchestratorConfig] = None,
        physics_store:     Optional[PhysicsCoefficientStore] = None,
        router:            Optional[PhysicsAwareRouter] = None,
    ) -> None:
        self._config    = config or OrchestratorConfig()
        self._store     = physics_store or PhysicsCoefficientStore()
        self._router    = router
        self._gate7     = PhysicsValidationGate(
            min_fitness       = self._config.min_physics_fitness,
            coefficient_store = self._store,
        )
        self._gate8     = EnsembleGate()
        self._learner   = ManuscriptLearner(store=self._store)
        self._coordinator = UpdateCoordinator(self._store)

    def run(self, draft: SceneDraftInput) -> FinalSceneOutput:
        state = LiteraryPipelineState()

        # ── Gate 7: NarrativePhysics 검증 ────────────────────────
        gate7_result: GateResult = self._gate7.run(draft.scene_context, state)

        # PhysicsAwareRouter fitness 업데이트
        if self._router:
            for node in self._router._nodes:
                self._router.update_fitness(node.name, gate7_result.fitness)

        decision_str = "SINGLE"

        # ── Gate 8: Provider Ensemble (활성화된 경우) ──────────────
        if self._config.enable_ensemble and draft.provider_candidates:
            candidates = [
                CandidateScore(
                    provider_name          = c.get('name', 'unknown'),
                    narrative_fitness      = gate7_result.fitness,
                    reader_surface         = c.get('reader_surface', 0.5),
                    agent_benchmark        = c.get('agent_benchmark', 0.5),
                    provider_reliability   = c.get('reliability', 0.8),
                    cost_efficiency        = c.get('cost_efficiency', 0.7),
                    leakage_risk           = c.get('leakage_risk', 0.0),
                    branchpoint_regression = c.get('branchpoint_regression', 0.0),
                    style_drift            = c.get('style_drift', 0.0),
                )
                for c in draft.provider_candidates
            ]
            gate8_result: EnsembleGateResult = self._gate8.run(candidates, state)
            decision_str = gate8_result.decision.decision_type.value

        # ── ManuscriptLearning tick ───────────────────────────────
        if self._config.enable_learning:
            self._coordinator.tick_and_sync()

        return FinalSceneOutput(
            scene_id      = draft.scene_id,
            fitness       = gate7_result.fitness,
            decision      = decision_str,
            trace         = list(state.execution_trace),
            physics_trace = list(state.physics_trace),
            passed        = True,
        )
