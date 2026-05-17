"""V389 — ProviderEnsemble Layer 테스트."""
import pytest
from literary_system.ensemble.narrative_fitness_arbiter import (
    NarrativeFitnessArbiter, CandidateScore, EnsembleDecision, EnsembleDecisionType
)
from literary_system.ensemble.gate8_ensemble import EnsembleGate, EnsembleGateFailure, EnsembleGateResult
from literary_system.pipeline.pipeline_state import LiteraryPipelineState


def make_candidate(name: str, fitness: float = 7.0, reliability: float = 0.85) -> CandidateScore:
    return CandidateScore(
        provider_name          = name,
        narrative_fitness      = fitness,
        reader_surface         = 0.7,
        agent_benchmark        = 0.6,
        provider_reliability   = reliability,
        cost_efficiency        = 0.7,
        leakage_risk           = 0.0,
        branchpoint_regression = 0.0,
        style_drift            = 0.0,
    )


class TestCandidateScore:
    def test_total_score_computed(self):
        c = make_candidate('a', fitness=8.0)
        assert c.total_score > 0.0

    def test_total_score_formula(self):
        c = CandidateScore(
            provider_name='x', narrative_fitness=10.0,
            reader_surface=1.0, agent_benchmark=1.0,
            provider_reliability=1.0, cost_efficiency=1.0,
            leakage_risk=0.0, branchpoint_regression=0.0, style_drift=0.0,
        )
        # (1.0)*0.28 + 1.0*0.16 + 1.0*0.12 + 1.0*0.18 + 1.0*0.08 = 0.82
        assert abs(c.total_score - 0.82) < 0.01

    def test_penalties_reduce_score(self):
        base = make_candidate('base')
        penalized = CandidateScore(
            provider_name='penalized', narrative_fitness=7.0,
            reader_surface=0.7, agent_benchmark=0.6,
            provider_reliability=0.85, cost_efficiency=0.7,
            leakage_risk=0.2, branchpoint_regression=0.1, style_drift=0.1,
        )
        assert penalized.total_score < base.total_score


class TestNarrativeFitnessArbiter:
    def test_empty_candidates_reject(self):
        arb = NarrativeFitnessArbiter()
        d = arb.arbitrate([])
        assert d.decision_type == EnsembleDecisionType.REJECT

    def test_low_score_reject(self):
        arb = NarrativeFitnessArbiter(reject_threshold=0.9)
        c = make_candidate('low', fitness=1.0)
        d = arb.arbitrate([c])
        assert d.decision_type == EnsembleDecisionType.REJECT

    def test_single_candidate_select(self):
        arb = NarrativeFitnessArbiter()
        c = make_candidate('a', fitness=8.0)
        d = arb.arbitrate([c])
        assert d.decision_type == EnsembleDecisionType.SELECT
        assert d.selected == 'a'

    def test_clear_winner_select(self):
        arb = NarrativeFitnessArbiter(select_margin=0.05)
        c1 = make_candidate('winner', fitness=9.0)
        c2 = make_candidate('loser',  fitness=5.0)
        d = arb.arbitrate([c1, c2])
        assert d.decision_type == EnsembleDecisionType.SELECT
        assert d.selected == 'winner'

    def test_close_scores_merge(self):
        arb = NarrativeFitnessArbiter(select_margin=0.50)
        c1 = make_candidate('a', fitness=7.5)
        c2 = make_candidate('b', fitness=7.4)
        d = arb.arbitrate([c1, c2])
        assert d.decision_type == EnsembleDecisionType.MERGE

    def test_merge_map_present(self):
        arb = NarrativeFitnessArbiter(select_margin=0.50)
        c1 = make_candidate('a', fitness=7.5)
        c2 = make_candidate('b', fitness=7.4)
        d = arb.arbitrate([c1, c2])
        assert isinstance(d.merge_map, dict)
        assert len(d.merge_map) > 0

    def test_scores_in_decision(self):
        arb = NarrativeFitnessArbiter()
        candidates = [make_candidate('a', 8.0), make_candidate('b', 6.0)]
        d = arb.arbitrate(candidates)
        assert len(d.scores) == 2

    def test_reason_present(self):
        arb = NarrativeFitnessArbiter()
        d = arb.arbitrate([make_candidate('x', 8.0)])
        assert isinstance(d.reason, str)
        assert len(d.reason) > 0


class TestEnsembleGate:
    def test_select_passes(self):
        gate = EnsembleGate()
        state = LiteraryPipelineState()
        candidates = [make_candidate('best', fitness=8.0)]
        result = gate.run(candidates, state)
        assert isinstance(result, EnsembleGateResult)
        assert result.passed is True

    def test_reject_raises(self):
        gate = EnsembleGate()
        state = LiteraryPipelineState()
        with pytest.raises(EnsembleGateFailure):
            gate.run([], state)

    def test_trace_recorded(self):
        gate = EnsembleGate()
        state = LiteraryPipelineState()
        gate.run([make_candidate('a', 8.0)], state)
        assert any('gate8' in str(t) for t in state.execution_trace)

    def test_checkpoint_on_reject(self):
        gate = EnsembleGate()
        state = LiteraryPipelineState()
        try:
            gate.run([], state)
        except EnsembleGateFailure:
            pass
        assert 'gate8_reject' in state.checkpoints

    def test_decision_in_result(self):
        gate = EnsembleGate()
        state = LiteraryPipelineState()
        result = gate.run([make_candidate('a', 8.0)], state)
        assert result.decision is not None

    def test_merge_passes(self):
        gate = EnsembleGate()
        state = LiteraryPipelineState()
        # 두 후보가 가깝지만 threshold 이상이면 MERGE로 pass
        candidates = [make_candidate('a', 7.5), make_candidate('b', 7.4)]
        result = gate.run(candidates, state)
        assert result.passed is True
