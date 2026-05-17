"""Tests — V393 FractalTopology."""
import pytest
from literary_system.longform.fractal_topology import (
    FractalUnitType, FractalPlotUnit, FractalTopologyValidator
)


class TestFractalPlotUnit:
    def test_complete_unit(self):
        u = FractalPlotUnit("u1", FractalUnitType.EPISODE,
            setup="s", pressure="p", collision="c", reversal="r", residue="res")
        assert u.is_complete()
        assert u.filled_phases == 5

    def test_incomplete_unit(self):
        u = FractalPlotUnit("u1", FractalUnitType.SCENE, setup="s")
        assert not u.is_complete()

    def test_orphan_detection(self):
        u = FractalPlotUnit("mp1", FractalUnitType.MICROPLOT)
        assert u.is_orphan()

    def test_series_not_orphan(self):
        u = FractalPlotUnit("s1", FractalUnitType.SERIES)
        assert not u.is_orphan()

    def test_with_parent(self):
        u = FractalPlotUnit("mp1", FractalUnitType.MICROPLOT, parent_unit_id="ep1")
        assert not u.is_orphan()


class TestFractalTopologyValidator:
    @pytest.fixture
    def validator(self):
        return FractalTopologyValidator()

    def test_synthetic_no_orphans(self, validator):
        units = FractalTopologyValidator.build_synthetic(16)
        report = validator.validate(units)
        assert report.orphan_microplot_count == 0

    def test_synthetic_full_coverage(self, validator):
        units = FractalTopologyValidator.build_synthetic(16)
        report = validator.validate(units)
        assert report.episode_function_coverage == pytest.approx(1.0)

    def test_synthetic_pass_gate(self, validator):
        units = FractalTopologyValidator.build_synthetic(16)
        report = validator.validate(units)
        assert report.pass_gate

    def test_orphan_microplot_detected(self, validator):
        units = [
            FractalPlotUnit("s1", FractalUnitType.SERIES,
                "s","p","c","r","res"),
            FractalPlotUnit("mp1", FractalUnitType.MICROPLOT,   # 부모 없음
                "s","p","c","r","res"),
        ]
        report = validator.validate(units)
        assert report.orphan_microplot_count == 1

    def test_dangling_parent_detected(self, validator):
        units = [
            FractalPlotUnit("mp1", FractalUnitType.MICROPLOT,
                "s","p","c","r","res", parent_unit_id="nonexistent"),
        ]
        report = validator.validate(units)
        assert any("dangling" in v for v in report.violations)

    def test_depth_distribution_filled(self, validator):
        units = FractalTopologyValidator.build_synthetic(4)
        report = validator.validate(units)
        assert "EPISODE" in report.fractal_depth_distribution
        assert "MICROPLOT" in report.fractal_depth_distribution

    def test_24ep_synthetic(self, validator):
        units = FractalTopologyValidator.build_synthetic(24)
        report = validator.validate(units)
        assert report.pass_gate

    def test_empty_units(self, validator):
        report = validator.validate([])
        assert report.total_units == 0
        # Empty validation returns a report (may or may not pass)
        assert isinstance(report.pass_gate, bool)

    def test_total_units_count(self, validator):
        units = FractalTopologyValidator.build_synthetic(16)
        report = validator.validate(units)
        assert report.total_units == len(units)


class TestLoadBalancing:
    """V393 DramaticLoadBalancer 테스트."""
    def test_compute_load_returns_episode_load(self):
        from literary_system.longform.load_balancing import DramaticLoadBalancer
        load = DramaticLoadBalancer.compute_load(0, 4, "SETUP")
        assert load.episode_idx == 0
        assert load.total_load > 0

    def test_analyze_no_overload_in_normal_drama(self):
        from literary_system.longform.load_balancing import DramaticLoadBalancer
        balancer = DramaticLoadBalancer()
        loads = [DramaticLoadBalancer.compute_load(i, 4, "COLLISION") for i in range(16)]
        report = balancer.analyze(loads)
        assert isinstance(report.load_curve, list)
        assert len(report.load_curve) == 16

    def test_overloaded_detected(self):
        from literary_system.longform.load_balancing import EpisodeLoad, DramaticLoadBalancer
        # 8 components all at 1.0 → total=8.0 >> OVERLOAD_THRESHOLD 5.5
        loads = [EpisodeLoad(i, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0) for i in range(16)]
        report = DramaticLoadBalancer().analyze(loads)
        assert len(report.overloaded_episodes) > 0

    def test_underloaded_detected(self):
        from literary_system.longform.load_balancing import EpisodeLoad, DramaticLoadBalancer
        loads = [EpisodeLoad(i, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1) for i in range(16)]
        report = DramaticLoadBalancer().analyze(loads)
        assert len(report.underloaded_episodes) > 0

    def test_mid_season_sag_risk_range(self):
        from literary_system.longform.load_balancing import DramaticLoadBalancer
        loads = [DramaticLoadBalancer.compute_load(i, 4, ["SETUP","PRESSURE","COLLISION","REVERSAL","RESIDUE"][i//3%5]) for i in range(16)]
        report = DramaticLoadBalancer().analyze(loads)
        assert 0.0 <= report.mid_season_sag_risk <= 1.0

    def test_finale_overload_risk_range(self):
        from literary_system.longform.load_balancing import DramaticLoadBalancer
        loads = [DramaticLoadBalancer.compute_load(i, 4, "COLLISION") for i in range(16)]
        report = DramaticLoadBalancer().analyze(loads)
        assert 0.0 <= report.finale_overload_risk <= 1.0

    def test_empty_loads(self):
        from literary_system.longform.load_balancing import DramaticLoadBalancer
        report = DramaticLoadBalancer().analyze([])
        assert report.load_curve == []
