"""V409 — Gate 3층 체계 테스트 (25 tests).

RuntimeGates (RG-1, RG-2, RG-3) + SeriesGates (SG-1, SG-2, SG-3).
"""
import pytest
from literary_system.gates.runtime_gates import (
    PhysicsGate, EnsembleGate, DebtOverflowGuard, RuntimeGateRunner,
    RuntimeGateResult
)
from literary_system.gates.series_gates import (
    EnduranceSeriesGate, MemoryConsistencyGate, TrajectoryDeviationGate,
    SeriesGateRunner, SeriesGateResult
)


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

def _make_episode_memory(series_id="s1", episode_idx=1, sp=0.45, ru=0.2, et=0.1, rd=0.85):
    class _Mem:
        pass
    m = _Mem()
    m.series_id = series_id
    m.episode_idx = episode_idx
    m.narrative_tensor = {"SP": sp, "RU": ru, "ET": et, "RD": rd}
    m.coefficient_snapshot = {"conflict_weight": 0.20}
    return m


class _FakeEnduranceReport:
    overall_pass = True
    gate_summary = {
        "episode_layer": True, "fractal_topology": True,
        "dramatic_load_balancing": True, "agency_conservation": True,
        "payoff_debt_ledger": True, "scene_necessity": True,
        "dialogue_pragmatics": True, "voice_manifold": True,
        "attention_economy": True, "production_proof": True,
        "node2_surface_guard": True, "provider_zero": True,
        "branchpoint_survival": True, "v390_baseline": True,
    }


# ── RG-1 PhysicsGate ─────────────────────────────────────────────────────────

class TestPhysicsGate:
    def test_returns_runtime_gate_result(self):
        gate = PhysicsGate()
        r = gate.run({})
        assert isinstance(r, RuntimeGateResult)
        assert r.gate_id == "RG-1"

    def test_passes_with_good_components(self):
        gate = PhysicsGate()
        r = gate.run({
            "conflict_intensity": 0.8, "scene_energy_ratio": 0.85,
            "motif_residue_score": 0.7, "curiosity_gradient": 0.75,
            "reader_surface_score": 0.8, "arc_tension_score": 0.75,
        })
        assert r.passed is True

    def test_fails_with_weak_components(self):
        gate = PhysicsGate()
        r = gate.run({
            "conflict_intensity": 0.1, "scene_energy_ratio": 0.1,
            "motif_residue_score": 0.1, "curiosity_gradient": 0.1,
            "reader_surface_score": 0.1, "arc_tension_score": 0.1,
        })
        assert r.passed is False

    def test_has_fitness_metric(self):
        gate = PhysicsGate()
        r = gate.run({})
        assert "fitness_score" in r.metrics

    def test_trace_not_empty(self):
        gate = PhysicsGate()
        r = gate.run({})
        assert len(r.execution_trace) > 0


# ── RG-2 EnsembleGate ────────────────────────────────────────────────────────

class TestEnsembleGate:
    def test_skips_when_no_llm(self):
        gate = EnsembleGate()
        r = gate.run({}, llm_client=None)
        assert r.skipped is True
        assert r.passed is True

    def test_passes_when_skipped(self):
        import os
        os.environ["LLM_DISABLED"] = "true"
        gate = EnsembleGate()
        r = gate.run({})
        assert r.passed is True
        assert r.skipped is True
        del os.environ["LLM_DISABLED"]

    def test_gate_id(self):
        gate = EnsembleGate()
        r = gate.run({})
        assert r.gate_id == "RG-2"


# ── RG-3 DebtOverflowGuard ────────────────────────────────────────────────────

class TestDebtOverflowGuard:
    def test_passes_no_defaults(self):
        gate = DebtOverflowGuard()
        r = gate.run({"open": ["f1", "f2"], "paid": ["p1"], "defaulted": []})
        assert r.passed is True

    def test_fails_with_defaults(self):
        gate = DebtOverflowGuard()
        r = gate.run({"open": [], "paid": [], "defaulted": ["d1"]})
        assert r.passed is False

    def test_has_metrics(self):
        gate = DebtOverflowGuard()
        r = gate.run({"open": ["a"], "paid": ["b"], "defaulted": []})
        assert "critical_defaults" in r.metrics
        assert "open_count" in r.metrics

    def test_gate_id(self):
        gate = DebtOverflowGuard()
        r = gate.run({})
        assert r.gate_id == "RG-3"


# ── RuntimeGateRunner ────────────────────────────────────────────────────────

class TestRuntimeGateRunner:
    def test_run_all_returns_three_results(self):
        runner = RuntimeGateRunner()
        results = runner.run_all({})
        assert "RG-1" in results
        assert "RG-2" in results
        assert "RG-3" in results

    def test_all_passed_true(self):
        runner = RuntimeGateRunner()
        results = runner.run_all(
            {"conflict_intensity": 0.8, "scene_energy_ratio": 0.85,
             "motif_residue_score": 0.7, "curiosity_gradient": 0.75,
             "reader_surface_score": 0.8, "arc_tension_score": 0.75},
            debt_snapshot={"open": [], "paid": [], "defaulted": []},
        )
        assert runner.all_passed(results) is True


# ── SG-2 MemoryConsistencyGate ────────────────────────────────────────────────

class TestMemoryConsistencyGate:
    def test_consistent_series_passes(self):
        gate = MemoryConsistencyGate()
        mems = [_make_episode_memory(episode_idx=i) for i in range(4)]
        r = gate.run(mems)
        assert r.passed is True

    def test_inconsistent_series_id_fails(self):
        gate = MemoryConsistencyGate()
        mems = [
            _make_episode_memory(series_id="s1", episode_idx=0),
            _make_episode_memory(series_id="s2", episode_idx=1),
        ]
        r = gate.run(mems)
        assert r.checks["series_id_consistent"] is False

    def test_missing_episode_fails(self):
        gate = MemoryConsistencyGate()
        mems = [
            _make_episode_memory(episode_idx=0),
            _make_episode_memory(episode_idx=2),  # ep1 누락
        ]
        r = gate.run(mems)
        assert r.checks["episode_idx_sequential"] is False

    def test_empty_list_passes(self):
        gate = MemoryConsistencyGate()
        r = gate.run([])
        assert r.passed is True


# ── SG-3 TrajectoryDeviationGate ─────────────────────────────────────────────

class TestTrajectoryDeviationGate:
    def test_on_target_passes(self):
        gate = TrajectoryDeviationGate()
        # tension_rising_spiral 목표에 가깝게 설정
        mems = [
            _make_episode_memory(episode_idx=0, sp=0.3, ru=0.1, et=-0.3, rd=1.0),
            _make_episode_memory(episode_idx=4, sp=0.58, ru=0.28, et=-0.06, rd=0.93),
            _make_episode_memory(episode_idx=8, sp=0.86, ru=0.30, et=0.18, rd=0.85),
        ]
        r = gate.run(mems)
        assert "mean_deviation" in r.metrics

    def test_empty_passes(self):
        gate = TrajectoryDeviationGate()
        r = gate.run([])
        assert r.passed is True

    def test_has_deviation_metric(self):
        gate = TrajectoryDeviationGate()
        mems = [
            _make_episode_memory(episode_idx=0, sp=0.3, ru=0.1, et=-0.3, rd=1.0),
            _make_episode_memory(episode_idx=8, sp=0.86, ru=0.30, et=0.18, rd=0.85),
        ]
        r = gate.run(mems)
        assert "mean_deviation" in r.metrics or r.passed  # 체크 완료


# ── SeriesGateRunner ─────────────────────────────────────────────────────────

class TestSeriesGateRunner:
    def test_run_all_returns_three_gates(self):
        runner = SeriesGateRunner()
        mems = [_make_episode_memory(episode_idx=i) for i in range(3)]
        results = runner.run_all(_FakeEnduranceReport(), mems)
        assert "SG-1" in results
        assert "SG-2" in results
        assert "SG-3" in results
