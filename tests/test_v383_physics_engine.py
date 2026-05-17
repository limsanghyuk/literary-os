"""V383 — NarrativePhysicsEngine 통합 테스트."""
import pytest
from literary_system.physics import NarrativePhysicsEngine, PhysicsRunResult


def base_ctx():
    return {
        'character_ids': ['hero', 'villain'],
        'conflict_edges': [('hero', 'villain')],
        'cluster_weights': {'hero': 0.9, 'villain': 0.8},
        'energy_input': 0.85,
        'energy_output': 0.7,
        'motif_appearances': {'sword': 4, 'crown': 2},
        'motif_last_seen': {'sword': 8, 'crown': 3},
        'episode_idx': 10,
        'reader_uncertainty': 0.65,
        'reveal_ratio': 0.25,
        'arc_tension': 0.7,
        'reader_surface_score': 0.75,
        'arc_tension_score': 0.65,
        'scene_id': 'ep10_s1',
    }


@pytest.fixture
def engine():
    return NarrativePhysicsEngine()


class TestNarrativePhysicsEngine:
    def test_returns_run_result(self, engine):
        r = engine.run(base_ctx())
        assert isinstance(r, PhysicsRunResult)

    def test_fitness_range(self, engine):
        r = engine.run(base_ctx())
        assert 0.0 <= r.fitness <= 10.0

    def test_conflict_result_present(self, engine):
        r = engine.run(base_ctx())
        assert r.conflict is not None
        assert 0.0 <= r.conflict.conflict_intensity <= 1.0

    def test_energy_result_present(self, engine):
        r = engine.run(base_ctx())
        assert r.energy is not None

    def test_motif_graph_present(self, engine):
        r = engine.run(base_ctx())
        assert r.motif_graph is not None
        assert 'sword' in r.motif_graph.nodes

    def test_curiosity_result_present(self, engine):
        r = engine.run(base_ctx())
        assert r.curiosity is not None

    def test_components_all_set(self, engine):
        r = engine.run(base_ctx())
        c = r.components
        assert c.conflict_intensity   >= 0.0
        assert c.scene_energy_ratio   >= 0.0
        assert c.motif_residue_score  >= 0.0
        assert c.curiosity_gradient   >= 0.0
        assert c.reader_surface_score >= 0.0
        assert c.arc_tension_score    >= 0.0

    def test_no_violations_normal(self, engine):
        r = engine.run(base_ctx())
        # 에너지 손실 ~17% < 30% → 위반 없음
        assert r.energy_violations == []

    def test_energy_violation_collected(self, engine):
        ctx = base_ctx()
        ctx['energy_input'] = 1.0
        ctx['energy_output'] = 0.5  # 50% 손실
        r = engine.run(ctx)
        assert len(r.energy_violations) == 1

    def test_curiosity_collapse_collected(self, engine):
        ctx = base_ctx()
        ctx['reader_uncertainty'] = 0.0
        ctx['arc_tension'] = 0.0
        ctx['reveal_ratio'] = 1.0
        r = engine.run(ctx)
        assert len(r.curiosity_collapses) == 1

    def test_empty_context_safe(self, engine):
        r = engine.run({})
        assert isinstance(r, PhysicsRunResult)

    def test_deterministic(self, engine):
        ctx = base_ctx()
        r1 = engine.run(ctx)
        r2 = engine.run(ctx)
        assert r1.fitness == r2.fitness

    def test_fitness_improves_with_better_inputs(self, engine):
        low_ctx  = base_ctx()
        high_ctx = base_ctx()
        high_ctx['reader_surface_score'] = 0.95
        high_ctx['arc_tension_score']    = 0.95
        low_ctx['reader_surface_score']  = 0.1
        low_ctx['arc_tension_score']     = 0.1
        r_low  = engine.run(low_ctx)
        r_high = engine.run(high_ctx)
        assert r_high.fitness > r_low.fitness
