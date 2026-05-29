"""V405 — EnduranceRunReport 확장 + EnduranceGate 체크 #15 테스트 (22 tests)."""
import pytest
from literary_system.orchestrators.longform_endurance_orchestrator import EnduranceRunReport
from literary_system.gates.endurance_gate import EnduranceGate, GateResult
from literary_system.physics.narrative_physics_snapshot import (
    PhysicsSnapshot, NarrativePhysicsSnapshotEngine, SnapshotRunResult
)
import datetime


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

def _make_snap(ep: int, fitness: float) -> PhysicsSnapshot:
    return PhysicsSnapshot(
        episode_idx=ep, fitness_score=fitness,
        energy_violations=0, curiosity_collapse=0,
        snapshot_timestamp=datetime.datetime.utcnow().isoformat()
    )


class _FakeProofPack:
    """EnduranceGate.run()이 요구하는 최소 ProofPack."""
    def __init__(self, physics_snapshots=None):
        self.summary = {"episode_count": 16, "total_microplots": 64}
        self.fractal_report = {"orphan_microplot_count": 0, "episode_function_coverage": 1.0}
        self.gate_results = {"load_balancing": True, "agency_conservation": True}
        self.debt_summary = {"critical_defaults": 0}
        self.necessity_weak_ratio = 0.05
        self.dialogue_consistent = True
        self.voice_drift_blocked = 0
        self.fatigue_mid_risk = 0.2
        self.fatigue_finale_risk = 0.2
        self.overall_pass = True
        self.physics_snapshots = physics_snapshots or []


# ── EnduranceRunReport 필드 테스트 ────────────────────────────────────────────

class TestEnduranceRunReportV405:
    def test_physics_snapshots_field_exists(self):
        report = EnduranceRunReport(series_title="테스트", episode_count=16)
        assert hasattr(report, "physics_snapshots")

    def test_physics_snapshots_default_empty(self):
        report = EnduranceRunReport(series_title="테스트", episode_count=16)
        assert report.physics_snapshots == []

    def test_physics_snapshots_assignable(self):
        snaps = [_make_snap(1, 7.5), _make_snap(4, 8.0)]
        report = EnduranceRunReport(
            series_title="테스트", episode_count=16,
            physics_snapshots=snaps
        )
        assert len(report.physics_snapshots) == 2

    def test_physics_snapshots_not_affect_other_fields(self):
        snaps = [_make_snap(8, 7.0)]
        report = EnduranceRunReport(
            series_title="테스트", episode_count=16,
            physics_snapshots=snaps, overall_pass=True
        )
        assert report.overall_pass is True
        assert report.episode_count == 16


# ── EnduranceGate 체크 #15 테스트 ─────────────────────────────────────────────

class TestEnduranceGateCheck15:
    def test_no_snapshots_skips_check(self):
        """physics_snapshots 없으면 체크 #15 건너뜀 (backward-compatible)."""
        gate = EnduranceGate()
        pack = _FakeProofPack(physics_snapshots=[])
        result = gate.run(pack)
        assert "physics_fitness_mean" not in result.checks

    def test_snapshots_above_threshold_passes(self):
        """mean_fitness >= 6.0 → pass."""
        gate = EnduranceGate()
        snaps = [_make_snap(ep, 7.0) for ep in [1, 4, 8, 12, 16]]
        pack = _FakeProofPack(physics_snapshots=snaps)
        result = gate.run(pack)
        assert result.checks["physics_fitness_mean"] is True
        assert result.passed is True

    def test_snapshots_below_threshold_fails(self):
        """mean_fitness < 6.0 → check fail."""
        gate = EnduranceGate()
        snaps = [_make_snap(ep, 4.5) for ep in [1, 4, 8, 12, 16]]
        pack = _FakeProofPack(physics_snapshots=snaps)
        result = gate.run(pack)
        assert result.checks["physics_fitness_mean"] is False
        assert result.passed is False

    def test_mixed_fitness_uses_mean(self):
        """일부는 높고 일부는 낮을 때 mean 기준으로 판단."""
        gate = EnduranceGate()
        # mean = (8.0 + 8.0 + 8.0 + 8.0 + 4.0) / 5 = 7.2 → pass
        fitnesses = [8.0, 8.0, 8.0, 8.0, 4.0]
        snaps = [_make_snap(ep, f) for ep, f in zip([1,4,8,12,16], fitnesses)]
        pack = _FakeProofPack(physics_snapshots=snaps)
        result = gate.run(pack)
        assert result.checks["physics_fitness_mean"] is True

    def test_boundary_exactly_60_passes(self):
        """fitness = 6.0 정확히 경계값 → pass."""
        gate = EnduranceGate()
        snaps = [_make_snap(1, 6.0)]
        pack = _FakeProofPack(physics_snapshots=snaps)
        result = gate.run(pack)
        assert result.checks["physics_fitness_mean"] is True

    def test_gate_result_has_failures_on_fail(self):
        """체크 #15 실패 시 failures 목록에 포함."""
        gate = EnduranceGate()
        snaps = [_make_snap(ep, 3.0) for ep in [1, 4]]
        pack = _FakeProofPack(physics_snapshots=snaps)
        result = gate.run(pack)
        assert any("physics_fitness_mean" in f for f in result.failures)

    def test_legacy_pack_without_attribute_compatible(self):
        """physics_snapshots 속성이 아예 없는 구형 pack도 오류 없이 처리."""
        gate = EnduranceGate()
        pack = _FakeProofPack()
        del pack.physics_snapshots  # 속성 제거로 구형 시뮬레이션
        # getattr 방어 코드 확인
        result = gate.run(pack)
        assert "physics_fitness_mean" not in result.checks


# ── 통합: SnapshotEngine → EnduranceGate ─────────────────────────────────────

class TestSnapshotEngineIntegration:
    class _FakeSeriesConfig:
        total_episodes = 16
        coefficient_store = None

    def test_engine_output_to_gate(self):
        """SnapshotEngine 결과 → EnduranceGate 체크 #15 통과."""
        eng = NarrativePhysicsSnapshotEngine()
        cfg = self._FakeSeriesConfig()
        run_result = eng.run_series(cfg)

        gate = EnduranceGate()
        pack = _FakeProofPack(physics_snapshots=run_result.snapshots)
        gate_result = gate.run(pack)

        # 체크 존재 확인
        assert "physics_fitness_mean" in gate_result.checks
        # 기본 SeriesConfig로는 fitness ≥ 6.0 → pass
        assert gate_result.checks["physics_fitness_mean"] is True
