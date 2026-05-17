"""V383 — PhysicsValidationGate (Gate 7) 테스트."""
import pytest
from literary_system.pipeline.gate7_physics import PhysicsValidationGate, PhysicsGateFailure, GateResult
from literary_system.pipeline.pipeline_state import LiteraryPipelineState


def good_ctx():
    return {
        'character_ids': ['A', 'B'],
        'conflict_edges': [('A', 'B')],
        'cluster_weights': {'A': 0.8, 'B': 0.7},
        'energy_input': 0.9,
        'energy_output': 0.8,
        'motif_appearances': {'sword': 3},
        'motif_last_seen': {'sword': 9},
        'episode_idx': 10,
        'reader_uncertainty': 0.7,
        'reveal_ratio': 0.3,
        'arc_tension': 0.6,
        'reader_surface_score': 0.75,
        'arc_tension_score': 0.65,
    }


@pytest.fixture
def gate():
    return PhysicsValidationGate(min_fitness=3.0)


@pytest.fixture
def state():
    return LiteraryPipelineState()


class TestGate7:
    def test_passes_good_context(self, gate, state):
        result = gate.run(good_ctx(), state)
        assert isinstance(result, GateResult)
        assert result.passed is True

    def test_fitness_in_result(self, gate, state):
        result = gate.run(good_ctx(), state)
        assert 0.0 <= result.fitness <= 10.0

    def test_trace_recorded(self, gate, state):
        gate.run(good_ctx(), state)
        assert len(state.physics_trace) > 0

    def test_trace_has_gate7(self, gate, state):
        gate.run(good_ctx(), state)
        assert state.physics_trace[0]['gate'] == 'gate7'

    def test_trace_has_fitness(self, gate, state):
        gate.run(good_ctx(), state)
        assert 'fitness' in state.physics_trace[0]

    def test_execution_trace_updated(self, gate, state):
        gate.run(good_ctx(), state)
        assert any('gate7' in t for t in state.execution_trace)

    def test_fails_on_low_fitness(self, state):
        strict = PhysicsValidationGate(min_fitness=9.99)
        with pytest.raises(PhysicsGateFailure):
            strict.run(good_ctx(), state)

    def test_failure_contains_reason(self, state):
        strict = PhysicsValidationGate(min_fitness=9.99)
        with pytest.raises(PhysicsGateFailure) as exc:
            strict.run(good_ctx(), state)
        assert 'NarrativeFitness' in str(exc.value)

    def test_energy_violation_fails(self, state):
        gate = PhysicsValidationGate(min_fitness=0.0)
        ctx = good_ctx()
        ctx['energy_input'] = 1.0
        ctx['energy_output'] = 0.5   # 50% 손실 > 30%
        with pytest.raises(PhysicsGateFailure):
            gate.run(ctx, state)

    def test_curiosity_collapse_fails(self, state):
        gate = PhysicsValidationGate(min_fitness=0.0)
        ctx = good_ctx()
        ctx['reader_uncertainty'] = 0.0   # gradient = 0 → collapse
        ctx['reveal_ratio'] = 1.0
        ctx['arc_tension'] = 0.0
        with pytest.raises(PhysicsGateFailure):
            gate.run(ctx, state)

    def test_checkpoint_saved_on_failure(self, state):
        strict = PhysicsValidationGate(min_fitness=9.99)
        with pytest.raises(PhysicsGateFailure):
            strict.run(good_ctx(), state)
        assert 'gate7_fail' in state.checkpoints

    def test_motif_orphan_count_in_result(self, gate, state):
        ctx = good_ctx()
        ctx['motif_appearances'] = {'dead_motif': 5}
        ctx['motif_last_seen'] = {'dead_motif': 0}
        ctx['episode_idx'] = 50
        result = gate.run(ctx, state)
        assert result.motif_orphan_count >= 0

    def test_trace_passed_field(self, gate, state):
        gate.run(good_ctx(), state)
        assert state.physics_trace[0]['passed'] is True
