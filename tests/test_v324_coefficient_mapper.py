"""
V324 - test_v324_coefficient_mapper.py
CoefficientMapper 단위 테스트 (25개)
"""
import json
import pytest

from literary_system.validation.learned_coefficient_store import LearnedCoefficients
from literary_system.validation.coefficient_mapper import (
    CoefficientMapper, MAEWeights, ChangeLedgerEntry,
)


@pytest.fixture
def default_coeff():
    return LearnedCoefficients()

@pytest.fixture
def mapper():
    return CoefficientMapper()


class TestMAEWeights:
    def test_default_values_in_range(self):
        w = MAEWeights()
        assert 0.2 <= w.alpha_logic <= 0.9
        assert 0.2 <= w.beta_char <= 0.9
        assert 0.2 <= w.gamma_tension <= 0.9

    def test_custom_values(self):
        w = MAEWeights(alpha_logic=0.5, beta_char=0.6, gamma_tension=0.7)
        assert w.alpha_logic == 0.5
        assert w.beta_char == 0.6
        assert w.gamma_tension == 0.7

    def test_clamp_enforced_on_creation(self):
        w = MAEWeights(alpha_logic=2.0, beta_char=-0.5, gamma_tension=1.5)
        assert w.alpha_logic == 0.9
        assert w.beta_char == 0.2
        assert w.gamma_tension == 0.9

    def test_to_dict_roundtrip(self):
        w = MAEWeights(alpha_logic=0.5, beta_char=0.6, gamma_tension=0.7)
        d = w.to_dict()
        w2 = MAEWeights.from_dict(d)
        assert w2.alpha_logic == pytest.approx(0.5)
        assert w2.beta_char == pytest.approx(0.6)
        assert w2.gamma_tension == pytest.approx(0.7)


class TestMapToMAE:
    def test_returns_mae_weights(self, mapper, default_coeff):
        result = mapper.map_to_mae(default_coeff)
        assert isinstance(result, MAEWeights)

    def test_alpha_from_decay_lambda(self, mapper):
        c = LearnedCoefficients(decay_lambda=0.05)
        w = mapper.map_to_mae(c)
        expected = min(0.9, max(0.2, c.decay_lambda * 10.0))
        assert w.alpha_logic == pytest.approx(expected, abs=1e-6)

    def test_beta_from_residue_boost(self, mapper):
        c = LearnedCoefficients(residue_boost=1.5)
        w = mapper.map_to_mae(c)
        expected = min(0.9, max(0.2, c.residue_boost / 3.0))
        assert w.beta_char == pytest.approx(expected, abs=1e-6)

    def test_gamma_from_arc_pressure(self, mapper):
        c = LearnedCoefficients(arc_pressure_boost=1.2)
        w = mapper.map_to_mae(c)
        expected = min(0.9, max(0.2, c.arc_pressure_boost / 2.5))
        assert w.gamma_tension == pytest.approx(expected, abs=1e-6)

    def test_output_always_in_valid_range(self, mapper):
        c = LearnedCoefficients(decay_lambda=0.5, residue_boost=3.0, arc_pressure_boost=2.5)
        w = mapper.map_to_mae(c)
        assert 0.2 <= w.alpha_logic <= 0.9
        assert 0.2 <= w.beta_char <= 0.9
        assert 0.2 <= w.gamma_tension <= 0.9

    def test_min_coeff_gives_min_alpha(self, mapper):
        c = LearnedCoefficients(decay_lambda=0.001, residue_boost=1.0, arc_pressure_boost=1.0)
        w = mapper.map_to_mae(c)
        # decay_lambda=0.001 -> 0.001*10=0.01 -> clamped to 0.2
        assert w.alpha_logic == pytest.approx(0.2, abs=1e-6)
        # residue_boost=1.0 -> 1.0/3.0=0.333 (above min 0.2, no clamp)
        assert w.beta_char == pytest.approx(1.0 / 3.0, abs=1e-6)
        # arc_pressure_boost=1.0 -> 1.0/2.5=0.4 (above min 0.2, no clamp)
        assert w.gamma_tension == pytest.approx(1.0 / 2.5, abs=1e-6)


class TestMapFromMAE:
    def test_returns_learned_coefficients(self, mapper):
        w = MAEWeights()
        result = mapper.map_from_mae(w)
        assert isinstance(result, LearnedCoefficients)

    def test_decay_lambda_from_alpha(self, mapper):
        w = MAEWeights(alpha_logic=0.5)
        c = mapper.map_from_mae(w)
        expected = min(0.5, max(0.001, w.alpha_logic / 10.0))
        assert c.decay_lambda == pytest.approx(expected, abs=1e-6)

    def test_residue_boost_from_beta(self, mapper):
        w = MAEWeights(beta_char=0.5)
        c = mapper.map_from_mae(w)
        expected = min(3.0, max(1.0, w.beta_char * 3.0))
        assert c.residue_boost == pytest.approx(expected, abs=1e-6)

    def test_arc_pressure_from_gamma(self, mapper):
        w = MAEWeights(gamma_tension=0.6)
        c = mapper.map_from_mae(w)
        expected = min(2.5, max(1.0, w.gamma_tension * 2.5))
        assert c.arc_pressure_boost == pytest.approx(expected, abs=1e-6)

    def test_clamp_all_applied(self, mapper):
        w = MAEWeights(alpha_logic=0.2, beta_char=0.2, gamma_tension=0.2)
        c = mapper.map_from_mae(w)
        assert c.decay_lambda >= 0.001
        assert c.residue_boost >= 1.0
        assert c.arc_pressure_boost >= 1.0


class TestRoundtripAccuracy:
    FIELDS = ["decay_lambda", "residue_boost", "arc_pressure_boost"]

    def test_roundtrip_error_under_5_percent(self, mapper):
        original = LearnedCoefficients(decay_lambda=0.05, residue_boost=1.5, arc_pressure_boost=1.2)
        mae = mapper.map_to_mae(original)
        reconstructed = mapper.map_from_mae(mae)
        for field in self.FIELDS:
            orig_val = getattr(original, field)
            recon_val = getattr(reconstructed, field)
            if orig_val != 0:
                err = abs(orig_val - recon_val) / abs(orig_val)
                assert err < 0.05, f"{field}: {err:.4f} >= 0.05"

    def test_roundtrip_preserves_direction(self, mapper):
        c_high = LearnedCoefficients(decay_lambda=0.3, residue_boost=2.5, arc_pressure_boost=2.0)
        c_low = LearnedCoefficients(decay_lambda=0.01, residue_boost=1.1, arc_pressure_boost=1.1)
        w_high = mapper.map_to_mae(c_high)
        w_low = mapper.map_to_mae(c_low)
        assert w_high.alpha_logic > w_low.alpha_logic
        assert w_high.beta_char > w_low.beta_char
        assert w_high.gamma_tension > w_low.gamma_tension


class TestChangeLedger:
    def test_record_change_adds_entry(self, mapper):
        before = LearnedCoefficients(decay_lambda=0.05)
        after = LearnedCoefficients(decay_lambda=0.07)
        mapper.record_change(before, after, reason="test_reason")
        assert len(mapper.get_ledger()) == 1

    def test_ledger_entry_fields(self, mapper):
        before = LearnedCoefficients(decay_lambda=0.05)
        after = LearnedCoefficients(decay_lambda=0.07)
        mapper.record_change(before, after, reason="precision_drop")
        entry = mapper.get_ledger()[0]
        assert isinstance(entry, ChangeLedgerEntry)
        assert entry.reason == "precision_drop"
        assert entry.before_decay_lambda == pytest.approx(0.05)
        assert entry.after_decay_lambda == pytest.approx(0.07)

    def test_multiple_entries_accumulated(self, mapper):
        for i in range(5):
            before = LearnedCoefficients(decay_lambda=0.04 + i * 0.01)
            after = LearnedCoefficients(decay_lambda=0.05 + i * 0.01)
            mapper.record_change(before, after, reason=f"step_{i}")
        assert len(mapper.get_ledger()) == 5

    def test_get_ledger_returns_copy(self, mapper):
        before = LearnedCoefficients()
        after = LearnedCoefficients(decay_lambda=0.08)
        mapper.record_change(before, after, reason="test")
        ledger = mapper.get_ledger()
        ledger.clear()
        assert len(mapper.get_ledger()) == 1


class TestSerialization:
    def test_to_json_valid_json(self, mapper):
        before = LearnedCoefficients()
        after = LearnedCoefficients(decay_lambda=0.08)
        mapper.record_change(before, after, reason="test")
        s = mapper.to_json()
        data = json.loads(s)
        assert "ledger" in data

    def test_from_json_inplace_restores_ledger(self, mapper):
        before = LearnedCoefficients()
        after = LearnedCoefficients(decay_lambda=0.08)
        mapper.record_change(before, after, reason="test_restore")
        s = mapper.to_json()
        mapper2 = CoefficientMapper()
        mapper2.from_json_inplace(s)
        ledger = mapper2.get_ledger()
        assert len(ledger) == 1
        assert ledger[0].reason == "test_restore"

    def test_empty_mapper_serializes(self, mapper):
        s = mapper.to_json()
        data = json.loads(s)
        assert data["ledger"] == []
