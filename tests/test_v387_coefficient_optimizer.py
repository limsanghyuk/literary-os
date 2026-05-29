"""V387 — CoefficientOptimizer Layer 테스트."""
import pytest
from literary_system.optimizer.extended_coefficient_store import ExtendedPhysicsCoefficientStore
from literary_system.optimizer.update_coordinator import UpdateCoordinator, CoordinationError


class TestExtendedCoefficientStore:
    def test_inherits_base_6(self):
        store = ExtendedPhysicsCoefficientStore()
        base = store.as_dict()
        assert len(base) == 6

    def test_all_14_dict_has_14(self):
        store = ExtendedPhysicsCoefficientStore()
        d = store.all_14_dict()
        assert len(d) == 14

    def test_extended_initial_values(self):
        store = ExtendedPhysicsCoefficientStore()
        assert store.leakage_penalty_weight       == pytest.approx(0.10)
        assert store.branchpoint_survival_weight  == pytest.approx(0.08)
        assert store.style_drift_penalty          == pytest.approx(0.05)
        assert store.arc_escalation_bonus         == pytest.approx(0.07)
        assert store.reveal_entropy_weight        == pytest.approx(0.06)
        assert store.character_agency_weight      == pytest.approx(0.07)
        assert store.temporal_coherence_weight    == pytest.approx(0.05)
        assert store.motif_echo_weight            == pytest.approx(0.06)

    def test_update_extended(self):
        store = ExtendedPhysicsCoefficientStore()
        store.update_extended(leakage_penalty_weight=0.15)
        assert store.leakage_penalty_weight == pytest.approx(0.15)

    def test_update_extended_clamp_upper(self):
        store = ExtendedPhysicsCoefficientStore()
        store.update_extended(leakage_penalty_weight=0.99)
        assert store.leakage_penalty_weight <= 0.45

    def test_update_extended_clamp_lower(self):
        store = ExtendedPhysicsCoefficientStore()
        store.update_extended(style_drift_penalty=0.001)
        assert store.style_drift_penalty >= 0.02

    def test_ledger_records_extended_change(self):
        store = ExtendedPhysicsCoefficientStore()
        store.update_extended(motif_echo_weight=0.10)
        entries = [e for e in store.ledger.entries if e['coeff'] == 'motif_echo_weight']
        assert len(entries) == 1

    def test_all_14_keys_present(self):
        store = ExtendedPhysicsCoefficientStore()
        d = store.all_14_dict()
        expected_keys = {
            'conflict_weight', 'scene_energy_weight', 'motif_weight', 'curiosity_weight',
            'arc_pressure_coupling', 'prose_physics_bridge',
            'leakage_penalty_weight', 'branchpoint_survival_weight',
            'style_drift_penalty', 'arc_escalation_bonus',
            'reveal_entropy_weight', 'character_agency_weight',
            'temporal_coherence_weight', 'motif_echo_weight',
        }
        assert set(d.keys()) == expected_keys

    def test_base_update_still_works(self):
        store = ExtendedPhysicsCoefficientStore()
        store.update(conflict_weight=0.30)
        assert store.conflict_weight == pytest.approx(0.30)


class TestUpdateCoordinator:
    def test_tick_returns_false_before_interval(self):
        store = ExtendedPhysicsCoefficientStore()
        coord = UpdateCoordinator(store)
        for _ in range(99):
            result = coord.tick_and_sync()
        assert result is False

    def test_tick_returns_true_at_interval(self):
        store = ExtendedPhysicsCoefficientStore()
        coord = UpdateCoordinator(store)
        for _ in range(99):
            coord.tick_and_sync()
        result = coord.tick_and_sync()
        assert result is True

    def test_synced_count_increments(self):
        store = ExtendedPhysicsCoefficientStore()
        coord = UpdateCoordinator(store)
        for _ in range(100):
            coord.tick_and_sync()
        assert coord.synced_count == 1

    def test_assert_synced_no_mae(self):
        store = ExtendedPhysicsCoefficientStore()
        coord = UpdateCoordinator(store, mae_store=None)
        coord.assert_synced()  # mae 없으면 예외 없음

    def test_assert_synced_large_gap_raises(self):
        store = ExtendedPhysicsCoefficientStore()
        mae = ExtendedPhysicsCoefficientStore()
        coord = UpdateCoordinator(store, mae_store=mae)
        # physics_store만 200 tick
        for _ in range(200):
            store.tick_episode()
        with pytest.raises(CoordinationError):
            coord.assert_synced()
