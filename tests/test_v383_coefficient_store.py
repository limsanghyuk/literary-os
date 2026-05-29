"""V383 — PhysicsCoefficientStore 테스트."""
import pytest
from literary_system.physics.coefficient_store import PhysicsCoefficientStore


@pytest.fixture
def store():
    return PhysicsCoefficientStore()


class TestCoefficientStore:
    def test_initial_values(self, store):
        d = store.as_dict()
        assert abs(d['conflict_weight']       - 0.20) < 0.001
        assert abs(d['scene_energy_weight']   - 0.15) < 0.001
        assert abs(d['motif_weight']          - 0.15) < 0.001
        assert abs(d['curiosity_weight']      - 0.20) < 0.001
        assert abs(d['arc_pressure_coupling'] - 0.12) < 0.001
        assert abs(d['prose_physics_bridge']  - 0.18) < 0.001

    def test_six_coefficients(self, store):
        assert len(store.as_dict()) == 6

    def test_update_applies(self, store):
        store.update(conflict_weight=0.30)
        assert store.conflict_weight == pytest.approx(0.30)

    def test_clamp_lower(self, store):
        store.update(conflict_weight=0.001)
        assert store.conflict_weight >= 0.05

    def test_clamp_upper(self, store):
        store.update(conflict_weight=0.99)
        assert store.conflict_weight <= 0.45

    def test_ledger_records_change(self, store):
        store.update(motif_weight=0.25)
        assert len(store.ledger.entries) == 1
        assert store.ledger.entries[0]['coeff'] == 'motif_weight'

    def test_ledger_old_new_values(self, store):
        old_val = store.curiosity_weight
        store.update(curiosity_weight=0.30)
        entry = store.ledger.entries[-1]
        assert entry['old'] == pytest.approx(old_val)
        assert entry['new'] == pytest.approx(0.30)

    def test_update_interval_100(self, store):
        assert store.UPDATE_INTERVAL == 100

    def test_tick_false_before_100(self, store):
        for _ in range(99):
            result = store.tick_episode()
        assert result is False

    def test_tick_true_at_100(self, store):
        for _ in range(99):
            store.tick_episode()
        result = store.tick_episode()
        assert result is True

    def test_tick_true_at_200(self, store):
        for _ in range(200):
            result = store.tick_episode()
        assert result is True

    def test_unknown_attr_ignored(self, store):
        # 존재하지 않는 계수 업데이트는 무시
        store.update(nonexistent_coeff=0.5)
        assert not hasattr(store, 'nonexistent_coeff')

    def test_multiple_updates(self, store):
        store.update(conflict_weight=0.25, motif_weight=0.20)
        assert store.conflict_weight == pytest.approx(0.25)
        assert store.motif_weight == pytest.approx(0.20)
