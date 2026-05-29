"""V383 — AudienceCuriosityGradientEngine 테스트."""
import pytest
from literary_system.physics.curiosity_gradient import (
    AudienceCuriosityGradientEngine, CuriosityResult, CuriosityCollapseError
)


@pytest.fixture
def engine():
    return AudienceCuriosityGradientEngine()


class TestCuriosityGradient:
    def test_returns_result(self, engine):
        r = engine.calculate(0.5, 0.3, 0.7)
        assert isinstance(r, CuriosityResult)

    def test_gradient_positive(self, engine):
        r = engine.calculate(0.8, 0.2, 0.9)
        assert r.gradient > 0.0

    def test_gradient_formula(self, engine):
        r = engine.calculate(0.6, 0.4, 0.5)
        expected = 0.6 * (1 - 0.4) * 0.5
        assert abs(r.gradient - expected) < 0.001

    def test_collapse_zero_uncertainty(self, engine):
        r = engine.calculate(0.0, 0.3, 0.7, episode_idx=3)
        assert r.collapse_error is not None

    def test_collapse_full_reveal(self, engine):
        r = engine.calculate(0.8, 1.0, 0.7, episode_idx=5)
        assert r.collapse_error is not None

    def test_collapse_zero_tension(self, engine):
        r = engine.calculate(0.8, 0.2, 0.0, episode_idx=2)
        assert r.collapse_error is not None

    def test_no_collapse_normal(self, engine):
        r = engine.calculate(0.6, 0.3, 0.7)
        assert r.collapse_error is None

    def test_collapse_error_type(self, engine):
        r = engine.calculate(0.0, 0.0, 0.0, episode_idx=7)
        assert isinstance(r.collapse_error, CuriosityCollapseError)

    def test_collapse_contains_episode(self, engine):
        r = engine.calculate(0.0, 0.0, 0.8, episode_idx=11)
        assert r.collapse_error.episode_idx == 11

    def test_gradient_clamped_input(self, engine):
        # 범위 초과 입력도 안전하게 처리
        r = engine.calculate(2.0, -0.5, 1.5)
        assert 0.0 <= r.gradient <= 1.0

    def test_deterministic(self, engine):
        args = (0.7, 0.3, 0.6, 0)
        r1 = engine.calculate(*args)
        r2 = engine.calculate(*args)
        assert r1.gradient == r2.gradient

    def test_reveal_ratio_stored(self, engine):
        r = engine.calculate(0.5, 0.4, 0.7)
        assert r.reveal_ratio == pytest.approx(0.4)

    def test_arc_tension_stored(self, engine):
        r = engine.calculate(0.5, 0.4, 0.65)
        assert r.arc_tension == pytest.approx(0.65)

    def test_gradient_near_zero_no_collapse(self, engine):
        # 매우 작지만 양수 gradient → collapse 아님 (> 0.0)
        r = engine.calculate(0.001, 0.999, 0.001, episode_idx=4)
        assert r.gradient > 0.0  # tiny positive, not collapsed
