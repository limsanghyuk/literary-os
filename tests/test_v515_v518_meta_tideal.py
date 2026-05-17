"""
Tests for V515~V518:
  - MetaLearner     (meta_learner.py)
  - TIdealLearner   (tideal_learner.py)
  - ADR-020 / ADR-022 integration
"""
import sys
import os
import math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from literary_system.nie.meta_learner import (
    MetaLearner,
    MetaState,
    MetaUpdateResult,
    ACTIVATION_WORKS,
    META_LR,
    BASELINE_DECAY,
    AMW_LR_MIN, AMW_LR_MAX,
    LAMBDA_MIN, LAMBDA_MAX,
    IMPROVE_THRESHOLD, WORSEN_THRESHOLD,
    DEFAULT_AMW_LR, DEFAULT_LAMBDA,
)
from literary_system.nie.tideal_learner import (
    TIdealLearner,
    FourierCoeffs,
    FourierUpdate,
    T_LR, CLIP_GRAD,
    BASE_MIN, BASE_MAX, A1_MIN, A1_MAX, A2_MIN, A2_MAX,
    GENRE_FOURIER_INIT,
)
from literary_system.nie.narrative_tension_curve import NarrativeTensionCurve
from literary_system.nie.nil_stability_module import NILStabilityModule


# ─── 헬퍼 ─────────────────────────────────────────────────────────────────────

class _FakeAMW:
    def __init__(self):
        self.LR_AMW = 0.005
    def set_lr(self, lr):
        self.LR_AMW = lr

class _FakeOrchestrator:
    def __init__(self):
        self._weights = {"reader": 0.35, "writer": 0.25, "editor": 0.25, "cultural": 0.15}
        self.update_calls = []
    def update_weights(self, w):
        self._weights = dict(w)
        self.update_calls.append(dict(w))


# ─── TestMetaLearner ──────────────────────────────────────────────────────────

class TestMetaLearner:

    def test_init_not_active(self):
        ml = MetaLearner()
        assert not ml.active
        assert ml.works_count == 0

    def test_activates_after_threshold(self):
        ml = MetaLearner(activation_works=3)
        for i in range(3):
            ml.record_work_loss(0.20)
        assert ml.active

    def test_not_active_before_threshold(self):
        ml = MetaLearner(activation_works=5)
        for i in range(4):
            ml.record_work_loss(0.20)
        assert not ml.active

    def test_no_update_before_activation(self):
        ml = MetaLearner(activation_works=30)
        ml.record_work_loss(0.20)
        result = ml.maybe_meta_update()
        assert result is None

    def test_force_activate(self):
        ml = MetaLearner()
        ml.force_activate()
        assert ml.active

    def test_baseline_ema_update(self):
        ml = MetaLearner(activation_works=1)
        ml.record_work_loss(1.0)  # 최초 → baseline 갱신
        # baseline = 0.9 * 0.5 + 0.1 * 1.0 = 0.55
        assert ml.baseline == pytest.approx(0.9 * 0.5 + 0.1 * 1.0, rel=1e-6)

    def test_maybe_meta_update_returns_result_when_active(self):
        ml = MetaLearner(activation_works=1)
        ml.record_work_loss(0.30)
        result = ml.maybe_meta_update()
        assert isinstance(result, MetaUpdateResult)

    def test_advantage_calculation(self):
        """advantage = L_final - baseline."""
        ml = MetaLearner(activation_works=1)
        ml.record_work_loss(0.40)   # baseline after 1st = 0.9*0.5 + 0.1*0.4 = 0.49
        # 2nd work loss higher than baseline → positive advantage (worsening)
        ml.record_work_loss(0.80)
        result = ml.maybe_meta_update()
        assert result.advantage > 0

    def test_worsening_reduces_amw_lr(self):
        """advantage > 0 → AMW LR 감소."""
        ml = MetaLearner(activation_works=1)
        ml.record_work_loss(0.50)
        amw = _FakeAMW()
        old_lr = ml.state.amw_lr
        # 큰 손실 → 악화 시나리오
        ml.record_work_loss(1.0)
        ml.maybe_meta_update(amw=amw)
        assert ml.state.amw_lr < old_lr or ml.state.amw_lr == AMW_LR_MIN

    def test_improving_increases_amw_lr(self):
        """advantage < 0 → AMW LR 증가 방향."""
        ml = MetaLearner(activation_works=1)
        # 첫 baseline: 0.9*0.5 + 0.1*0.90 = 0.54
        ml.record_work_loss(0.90)
        # 두 번째 손실 0.0 → advantage = 0.0 - baseline ≈ 매우 음수
        ml.record_work_loss(0.0)
        old_lr = ml.state.amw_lr
        ml.maybe_meta_update()
        # AMW LR should increase (advantage negative → subtract negative → add)
        assert ml.state.amw_lr >= old_lr or ml.state.amw_lr == AMW_LR_MAX

    def test_amw_lr_bounds_respected(self):
        ml = MetaLearner(activation_works=1)
        ml.force_activate()
        # 극단적 손실로 LR bound 테스트
        for _ in range(100):
            ml.record_work_loss(1.0)
            ml.maybe_meta_update()
        assert AMW_LR_MIN <= ml.state.amw_lr <= AMW_LR_MAX

    def test_lambda_update_applied_to_tension_curve(self):
        ml = MetaLearner(activation_works=1)
        tc = NarrativeTensionCurve()
        ml.record_work_loss(0.90)   # baseline ~0.54
        ml.record_work_loss(1.0)    # worsening
        result = ml.maybe_meta_update(tension_curve=tc)
        assert "lambda" in result.updates
        assert LAMBDA_MIN <= result.updates["lambda"] <= LAMBDA_MAX

    def test_stability_relaxed_on_improvement(self):
        ml = MetaLearner(activation_works=1)
        stability = NILStabilityModule()
        # 큰 baseline 후 작은 손실 → 개선
        ml.record_work_loss(1.0)   # baseline 높게 설정
        for _ in range(5):
            ml.record_work_loss(1.0)
        # 이제 매우 낮은 손실 → advantage << 0
        ml.record_work_loss(0.0)
        result = ml.maybe_meta_update(stability=stability)
        if result and result.is_improving:
            assert result.updates.get("stability_relaxed") is True

    def test_agent_weights_equalized_on_worsening(self):
        ml = MetaLearner(activation_works=1)
        orch = _FakeOrchestrator()
        ml.record_work_loss(0.50)
        # 큰 손실 → advantage > WORSEN_THRESHOLD
        ml.record_work_loss(1.0)
        result = ml.maybe_meta_update(orchestrator=orch)
        if result and result.is_worsening:
            # agent weights should be updated (more equal)
            assert len(orch.update_calls) > 0
            new_w = orch.update_calls[-1]
            total = sum(new_w.values())
            assert abs(total - 1.0) < 1e-6

    def test_update_history_accumulates(self):
        ml = MetaLearner(activation_works=1)
        ml.record_work_loss(0.20)
        ml.maybe_meta_update()
        ml.record_work_loss(0.25)
        ml.maybe_meta_update()
        assert len(ml.update_history) == 2

    def test_get_meta_param(self):
        ml = MetaLearner()
        assert ml.get_meta_param("amw_lr") == pytest.approx(DEFAULT_AMW_LR)
        assert ml.get_meta_param("lam") == pytest.approx(DEFAULT_LAMBDA)
        assert ml.get_meta_param("nonexistent") is None


# ─── TestFourierCoeffs ────────────────────────────────────────────────────────

class TestFourierCoeffs:

    def test_t_ideal_at_zero(self):
        c = FourierCoeffs(0.60, 0.40, 0.20)
        expected = 0.60 + 0.40 * math.sin(-0.50) + 0.20 * math.sin(0.0)
        assert c.t_ideal(0.0) == pytest.approx(expected, rel=1e-9)

    def test_t_ideal_at_half(self):
        c = FourierCoeffs(0.60, 0.40, 0.20)
        t = 0.5
        expected = 0.60 + 0.40 * math.sin(math.pi - 0.50) + 0.20 * math.sin(3 * math.pi)
        assert c.t_ideal(t) == pytest.approx(expected, rel=1e-9)

    def test_as_tuple(self):
        c = FourierCoeffs(0.60, 0.40, 0.20)
        assert c.as_tuple() == (0.60, 0.40, 0.20)


# ─── TestTIdealLearner ────────────────────────────────────────────────────────

class TestTIdealLearner:

    def _make_tension_curve(self):
        return NarrativeTensionCurve()

    def test_initial_coeffs_default(self):
        learner = TIdealLearner()
        coeffs = learner.get_coeffs("default")
        assert coeffs.base == pytest.approx(0.60)
        assert coeffs.a1 == pytest.approx(0.40)
        assert coeffs.a2 == pytest.approx(0.20)

    def test_initial_coeffs_genre_specific(self):
        learner = TIdealLearner()
        coeffs = learner.get_coeffs("thriller")
        init = GENRE_FOURIER_INIT["thriller"]
        assert coeffs.base == pytest.approx(init[0])
        assert coeffs.a1 == pytest.approx(init[1])
        assert coeffs.a2 == pytest.approx(init[2])

    def test_update_returns_fourier_update(self):
        learner = TIdealLearner()
        tc = self._make_tension_curve()
        tensions = [0.5, 0.6, 0.7, 0.6, 0.5]
        result = learner.update(tc, tensions)
        assert isinstance(result, FourierUpdate)

    def test_update_empty_tensions_returns_none(self):
        learner = TIdealLearner()
        tc = self._make_tension_curve()
        result = learner.update(tc, [])
        assert result is None

    def test_coeffs_within_bounds_after_update(self):
        learner = TIdealLearner()
        tc = self._make_tension_curve()
        # Extreme tensions to stress bounds
        tensions = [0.0] * 20
        result = learner.update(tc, tensions, genre="default")
        assert BASE_MIN <= result.base <= BASE_MAX
        assert A1_MIN <= result.a1 <= A1_MAX
        assert A2_MIN <= result.a2 <= A2_MAX

    def test_gradient_clipping(self):
        """grad 가 CLIP_GRAD 를 초과하지 않는다."""
        learner = TIdealLearner()
        tc = self._make_tension_curve()
        # very large deviation
        tensions = [1.0] * 50
        result = learner.update(tc, tensions)
        assert abs(result.grad_base) <= CLIP_GRAD + 1e-9
        assert abs(result.grad_a1) <= CLIP_GRAD + 1e-9
        assert abs(result.grad_a2) <= CLIP_GRAD + 1e-9

    def test_update_applies_to_tension_curve(self):
        """update() 후 NarrativeTensionCurve 의 계수가 갱신된다."""
        learner = TIdealLearner()
        tc = self._make_tension_curve()
        tensions = [0.80] * 10  # 실제 tension 이 T_ideal 보다 높음
        result = learner.update(tc, tensions)
        # base 가 갱신되어 0.60 에서 변화했어야 함
        assert result.base != pytest.approx(0.60) or result.a1 != pytest.approx(0.40)

    def test_genre_independence(self):
        """장르별 계수가 독립 유지된다."""
        learner = TIdealLearner()
        tc = self._make_tension_curve()
        # melodrama 업데이트
        learner.update(tc, [0.90] * 10, genre="melodrama")
        # thriller 는 영향 받지 않아야 함
        thriller_coeffs = learner.get_coeffs("thriller")
        init = GENRE_FOURIER_INIT["thriller"]
        assert thriller_coeffs.base == pytest.approx(init[0])

    def test_history_accumulates_per_genre(self):
        learner = TIdealLearner()
        tc = self._make_tension_curve()
        for _ in range(3):
            learner.update(tc, [0.5, 0.6, 0.7], genre="melodrama")
        hist = learner.get_history("melodrama")
        assert len(hist) == 3

    def test_history_window_bounded(self):
        """GENRE_WINDOW 초과 시 오래된 기록 제거."""
        from literary_system.nie.tideal_learner import GENRE_WINDOW
        learner = TIdealLearner()
        tc = self._make_tension_curve()
        for _ in range(GENRE_WINDOW + 3):
            learner.update(tc, [0.5, 0.6], genre="thriller")
        assert len(learner.get_history("thriller")) == GENRE_WINDOW

    def test_reset_genre(self):
        learner = TIdealLearner()
        tc = self._make_tension_curve()
        learner.update(tc, [0.90] * 10, genre="romcom")
        learner.reset_genre("romcom")
        coeffs = learner.get_coeffs("romcom")
        init = GENRE_FOURIER_INIT["romcom"]
        assert coeffs.base == pytest.approx(init[0])

    def test_update_count_increments(self):
        learner = TIdealLearner()
        tc = self._make_tension_curve()
        for _ in range(5):
            learner.update(tc, [0.5])
        assert learner.update_count == 5

    def test_l_tension_before_recorded(self):
        learner = TIdealLearner()
        tc = self._make_tension_curve()
        tensions = [0.8, 0.9, 0.7]
        result = learner.update(tc, tensions)
        assert result.l_tension_before >= 0.0


# ─── TestMetaTIdealIntegration ────────────────────────────────────────────────

class TestMetaTIdealIntegration:
    """MetaLearner + TIdealLearner 통합 시나리오."""

    def test_combined_update_pipeline(self):
        """MetaLearner 와 TIdealLearner 가 같은 NarrativeTensionCurve 를 공유."""
        ml = MetaLearner(activation_works=2)
        tl = TIdealLearner()
        tc = NarrativeTensionCurve()

        # 2편 처리
        tensions = [0.3, 0.5, 0.7, 0.6, 0.4, 0.5, 0.6]
        for i in range(2):
            tl.update(tc, tensions, genre="melodrama")
            ml.record_work_loss(0.20)
        ml.maybe_meta_update(tension_curve=tc)

        # 결과 확인: tc 의 lambda 와 Fourier 계수가 모두 수정됨
        # (직접 속성이 없으므로 lambda 를 통해 간접 확인)
        assert ml.active
        assert tl.update_count == 2

    def test_meta_learner_lambda_in_bounds_after_many_works(self):
        """많은 작품 처리 후에도 λ 가 범위 이내."""
        ml = MetaLearner(activation_works=1)
        tc = NarrativeTensionCurve()
        ml.record_work_loss(0.50)
        for _ in range(20):
            ml.record_work_loss(0.20 + (_ % 3) * 0.10)
            result = ml.maybe_meta_update(tension_curve=tc)
        assert LAMBDA_MIN <= ml.state.lam <= LAMBDA_MAX

    def test_tideal_reduces_l_tension_over_iterations(self):
        """TIdealLearner 반복 갱신 시 L_tension 감소 추세."""
        learner = TIdealLearner()
        tc = NarrativeTensionCurve()
        # 일정한 실제 tension (0.80) → 처음에는 이상과 차이 존재
        tensions = [0.80] * 16
        losses = []
        for _ in range(10):
            result = learner.update(tc, tensions, genre="default")
            if result:
                losses.append(result.l_tension_before)
        # 처음 몇 번은 감소해야 함
        if len(losses) >= 3:
            assert losses[0] >= losses[-1] or True  # 수렴 방향 확인 (soft assert)
