"""V390 — FullSceneOrchestrator E2E 테스트."""
import pytest
from literary_system.orchestrators.full_scene_orchestrator import (
    FullSceneOrchestrator, SceneDraftInput, FinalSceneOutput, OrchestratorConfig
)
from literary_system.physics.coefficient_store import PhysicsCoefficientStore


def base_draft(scene_id='ep1_s1', episode_idx=1, with_ensemble=False):
    ctx = {
        'character_ids': ['hero', 'villain'],
        'conflict_edges': [('hero', 'villain')],
        'cluster_weights': {'hero': 0.9, 'villain': 0.8},
        'energy_input': 0.85,
        'energy_output': 0.72,
        'motif_appearances': {'sword': 4},
        'motif_last_seen': {'sword': episode_idx},
        'episode_idx': episode_idx,
        'reader_uncertainty': 0.7,
        'reveal_ratio': 0.25,
        'arc_tension': 0.7,
        'reader_surface_score': 0.75,
        'arc_tension_score': 0.65,
        'scene_id': scene_id,
    }
    candidates = [
        {'name': 'claude-sonnet', 'reader_surface': 0.75, 'agent_benchmark': 0.7,
         'reliability': 0.9, 'cost_efficiency': 0.65,
         'leakage_risk': 0.0, 'branchpoint_regression': 0.0, 'style_drift': 0.0},
        {'name': 'gpt-4o', 'reader_surface': 0.72, 'agent_benchmark': 0.68,
         'reliability': 0.85, 'cost_efficiency': 0.6,
         'leakage_risk': 0.0, 'branchpoint_regression': 0.0, 'style_drift': 0.0},
    ] if with_ensemble else []
    return SceneDraftInput(
        scene_id=scene_id,
        episode_idx=episode_idx,
        scene_context=ctx,
        provider_candidates=candidates,
    )


class TestFullSceneOrchestrator:
    def test_returns_output(self):
        orch = FullSceneOrchestrator(OrchestratorConfig(min_physics_fitness=0.0))
        result = orch.run(base_draft())
        assert isinstance(result, FinalSceneOutput)

    def test_passed_true(self):
        orch = FullSceneOrchestrator(OrchestratorConfig(min_physics_fitness=0.0))
        result = orch.run(base_draft())
        assert result.passed is True

    def test_fitness_in_result(self):
        orch = FullSceneOrchestrator(OrchestratorConfig(min_physics_fitness=0.0))
        result = orch.run(base_draft())
        assert 0.0 <= result.fitness <= 10.0

    def test_scene_id_preserved(self):
        orch = FullSceneOrchestrator(OrchestratorConfig(min_physics_fitness=0.0))
        result = orch.run(base_draft(scene_id='ep5_s3'))
        assert result.scene_id == 'ep5_s3'

    def test_trace_populated(self):
        orch = FullSceneOrchestrator(OrchestratorConfig(min_physics_fitness=0.0))
        result = orch.run(base_draft())
        assert len(result.trace) > 0

    def test_physics_trace_populated(self):
        orch = FullSceneOrchestrator(OrchestratorConfig(min_physics_fitness=0.0))
        result = orch.run(base_draft())
        assert len(result.physics_trace) > 0

    def test_decision_single_no_ensemble(self):
        cfg = OrchestratorConfig(min_physics_fitness=0.0, enable_ensemble=False)
        orch = FullSceneOrchestrator(cfg)
        result = orch.run(base_draft())
        assert result.decision == 'SINGLE'

    def test_ensemble_decision_populated(self):
        cfg = OrchestratorConfig(min_physics_fitness=0.0, enable_ensemble=True)
        orch = FullSceneOrchestrator(cfg)
        result = orch.run(base_draft(with_ensemble=True))
        assert result.decision in ('SELECT', 'MERGE', 'REJECT', 'SINGLE')

    def test_fails_on_strict_fitness(self):
        from literary_system.pipeline.gate7_physics import PhysicsGateFailure
        cfg = OrchestratorConfig(min_physics_fitness=9.99)
        orch = FullSceneOrchestrator(cfg)
        with pytest.raises(PhysicsGateFailure):
            orch.run(base_draft())

    def test_custom_store(self):
        store = PhysicsCoefficientStore()
        cfg = OrchestratorConfig(min_physics_fitness=0.0)
        orch = FullSceneOrchestrator(cfg, physics_store=store)
        result = orch.run(base_draft())
        assert result.passed is True

    def test_multiple_scenes_sequential(self):
        cfg = OrchestratorConfig(min_physics_fitness=0.0)
        orch = FullSceneOrchestrator(cfg)
        for i in range(5):
            result = orch.run(base_draft(scene_id=f'ep1_s{i}', episode_idx=i))
            assert result.passed is True

    def test_gate8_select_logged(self):
        cfg = OrchestratorConfig(min_physics_fitness=0.0, enable_ensemble=True)
        orch = FullSceneOrchestrator(cfg)
        result = orch.run(base_draft(with_ensemble=True))
        assert any('gate8' in str(t) for t in result.trace)
