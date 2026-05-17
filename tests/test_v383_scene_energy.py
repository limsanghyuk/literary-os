"""V383 — SceneEnergyConservationAudit 테스트."""
import pytest
from literary_system.physics.scene_energy import SceneEnergyConservationAudit, SceneEnergyViolation, EnergyAuditResult


@pytest.fixture
def audit():
    return SceneEnergyConservationAudit()


class TestSceneEnergyBasic:
    def test_returns_result_type(self, audit):
        r = audit.audit(1.0, 0.8)
        assert isinstance(r, EnergyAuditResult)

    def test_no_violation_normal(self, audit):
        r = audit.audit(1.0, 0.8)
        assert r.violation is None

    def test_violation_above_threshold(self, audit):
        # 손실 40% > 30% threshold
        r = audit.audit(1.0, 0.6, scene_id='s1')
        assert r.violation is not None
        assert isinstance(r.violation, SceneEnergyViolation)

    def test_violation_threshold_boundary(self, audit):
        # 29% 손실은 통과 (0.71 = 29% 손실, threshold 30% 미만)
        r = audit.audit(1.0, 0.71)
        assert r.violation is None
        # 31% 손실은 위반 (0.69 = 31% 손실, threshold 초과)
        r2 = audit.audit(1.0, 0.69)
        assert r2.violation is not None

    def test_violation_just_over(self, audit):
        r = audit.audit(1.0, 0.699)
        assert r.violation is not None

    def test_violation_contains_scene_id(self, audit):
        r = audit.audit(1.0, 0.5, scene_id='ep3_s2')
        assert 'ep3_s2' in r.violation.message

    def test_zero_input_no_violation(self, audit):
        r = audit.audit(0.0, 0.0)
        assert r.violation is None
        assert r.energy_ratio == 0.0

    def test_energy_ratio_calculation(self, audit):
        r = audit.audit(1.0, 0.9)
        assert abs(r.energy_ratio - 0.9) < 0.001

    def test_loss_ratio_calculation(self, audit):
        r = audit.audit(1.0, 0.6)
        assert abs(r.loss_ratio - 0.4) < 0.001

    def test_energy_surplus(self, audit):
        # output > input → 음수 손실, energy_ratio = 1.0
        r = audit.audit(0.5, 0.8)
        assert r.energy_ratio >= 0.0
        assert r.violation is None  # 에너지 과잉은 위반 아님

    def test_custom_threshold(self):
        strict = SceneEnergyConservationAudit(loss_threshold=0.10)
        r = strict.audit(1.0, 0.85)
        assert r.violation is not None

    def test_violation_loss_ratio_in_result(self, audit):
        r = audit.audit(1.0, 0.5, scene_id='x')
        assert r.violation.loss_ratio == pytest.approx(0.5)

    def test_energy_fields_preserved(self, audit):
        r = audit.audit(0.8, 0.6)
        assert r.energy_input == pytest.approx(0.8)
        assert r.energy_output == pytest.approx(0.6)

    def test_deterministic(self, audit):
        r1 = audit.audit(1.0, 0.65)
        r2 = audit.audit(1.0, 0.65)
        assert r1.energy_ratio == r2.energy_ratio
