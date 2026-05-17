"""V383 — NarrativeFitnessScore 테스트."""
import pytest
from literary_system.physics.fitness_score import NarrativeFitnessScore, NarrativeFitnessComponents
from literary_system.physics.coefficient_store import PhysicsCoefficientStore


def make_components(**kwargs):
    defaults = dict(
        conflict_intensity=0.5,
        scene_energy_ratio=0.8,
        motif_residue_score=0.5,
        curiosity_gradient=0.6,
        reader_surface_score=0.7,
        arc_tension_score=0.6,
    )
    defaults.update(kwargs)
    return NarrativeFitnessComponents(**defaults)


@pytest.fixture
def scorer():
    return NarrativeFitnessScore()


class TestNarrativeFitnessScore:
    def test_returns_float(self, scorer):
        c = make_components()
        assert isinstance(scorer.calculate(c), float)

    def test_range_0_to_10(self, scorer):
        c = make_components()
        s = scorer.calculate(c)
        assert 0.0 <= s <= 10.0

    def test_all_zero_gives_zero(self, scorer):
        c = make_components(
            conflict_intensity=0.0, scene_energy_ratio=0.0,
            motif_residue_score=0.0, curiosity_gradient=0.0,
            reader_surface_score=0.0, arc_tension_score=0.0
        )
        assert scorer.calculate(c) == pytest.approx(0.0)

    def test_all_one_gives_ten(self, scorer):
        c = make_components(
            conflict_intensity=1.0, scene_energy_ratio=1.0,
            motif_residue_score=1.0, curiosity_gradient=1.0,
            reader_surface_score=1.0, arc_tension_score=1.0
        )
        assert scorer.calculate(c) == pytest.approx(10.0)

    def test_weighted_sum_formula(self, scorer):
        store = PhysicsCoefficientStore()
        c = make_components(
            conflict_intensity=1.0, scene_energy_ratio=0.0,
            motif_residue_score=0.0, curiosity_gradient=0.0,
            reader_surface_score=0.0, arc_tension_score=0.0
        )
        # conflict_weight=0.20 / total=1.0 * 10 = 2.0
        expected = (0.20 / store.weight_sum()) * 10.0
        assert scorer.calculate(c) == pytest.approx(expected)

    def test_higher_components_higher_score(self, scorer):
        low  = scorer.calculate(make_components(conflict_intensity=0.2))
        high = scorer.calculate(make_components(conflict_intensity=0.9))
        assert high > low

    def test_deterministic(self, scorer):
        c = make_components()
        assert scorer.calculate(c) == scorer.calculate(c)

    def test_custom_store(self):
        store = PhysicsCoefficientStore()
        store.update(conflict_weight=0.40)
        scorer = NarrativeFitnessScore(store)
        c = make_components(conflict_intensity=1.0)
        s = scorer.calculate(c)
        assert s > 0.0

    def test_clamp_upper(self):
        store = PhysicsCoefficientStore()
        scorer = NarrativeFitnessScore(store)
        c = make_components(
            conflict_intensity=100.0, scene_energy_ratio=100.0,
            motif_residue_score=100.0, curiosity_gradient=100.0,
            reader_surface_score=100.0, arc_tension_score=100.0
        )
        assert scorer.calculate(c) <= 10.0

    def test_clamp_lower(self, scorer):
        c = make_components(
            conflict_intensity=-1.0, scene_energy_ratio=-1.0,
            motif_residue_score=-1.0, curiosity_gradient=-1.0,
            reader_surface_score=-1.0, arc_tension_score=-1.0
        )
        assert scorer.calculate(c) >= 0.0

    def test_components_dataclass_fields(self):
        c = make_components()
        assert hasattr(c, 'conflict_intensity')
        assert hasattr(c, 'scene_energy_ratio')
        assert hasattr(c, 'motif_residue_score')
        assert hasattr(c, 'curiosity_gradient')
        assert hasattr(c, 'reader_surface_score')
        assert hasattr(c, 'arc_tension_score')

    def test_mid_values_mid_score(self, scorer):
        c = make_components(
            conflict_intensity=0.5, scene_energy_ratio=0.5,
            motif_residue_score=0.5, curiosity_gradient=0.5,
            reader_surface_score=0.5, arc_tension_score=0.5
        )
        s = scorer.calculate(c)
        assert 3.0 <= s <= 7.0
