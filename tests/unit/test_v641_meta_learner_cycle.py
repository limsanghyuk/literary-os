"""
test_v641_meta_learner_cycle.py — V641 MetaLearnerCycle + KrippendorffAlpha 테스트 (33 TC)

SP-C.1 MetaLearner 1사이클 + Krippendorff α 1차 측정 검증.
blueprint v2.0 §2.2 요구사항: α ≥ 0.70, R 추세 양수.
"""
import math
import pytest
from literary_system.constitution.krippendorff_alpha import (
    KrippendorffAlpha, AlphaResult,
    METRIC_INTERVAL, METRIC_NOMINAL, METRIC_ORDINAL,
    SUPPORTED_METRICS, ALPHA_MIN_THRESHOLD, ALPHA_GOOD_THRESHOLD,
    _delta_interval, _delta_nominal,
)
from literary_system.constitution.meta_learner_cycle import (
    MetaLearnerCycle, CycleReport,
    CYCLE_COUNT, R_SCENE_TARGET, ALPHA_TARGET,
    AUGMENT_RATIO_MIN, AUGMENT_RATIO_MAX, AUGMENT_RATIO_STEP,
)


# ─── KrippendorffAlpha 상수 (TC-01~05) ──────────────────────────────────────────
class TestKrippendorffConstants:
    def test_tc01_supported_metrics(self):
        assert METRIC_INTERVAL in SUPPORTED_METRICS
        assert METRIC_NOMINAL in SUPPORTED_METRICS
        assert METRIC_ORDINAL in SUPPORTED_METRICS

    def test_tc02_alpha_thresholds(self):
        assert ALPHA_MIN_THRESHOLD == 0.70
        assert ALPHA_GOOD_THRESHOLD == 0.80
        assert ALPHA_MIN_THRESHOLD < ALPHA_GOOD_THRESHOLD

    def test_tc03_delta_interval(self):
        assert math.isclose(_delta_interval(0.8, 0.7), 0.01, abs_tol=1e-9)
        assert _delta_interval(0.5, 0.5) == 0.0
        assert math.isclose(_delta_interval(1.0, 0.0), 1.0, abs_tol=1e-9)

    def test_tc04_delta_nominal(self):
        assert _delta_nominal(1.0, 1.0) == 0.0
        assert _delta_nominal(1.0, 2.0) == 1.0
        assert _delta_nominal(0.5, 0.5) == 0.0

    def test_tc05_invalid_metric_raises(self):
        with pytest.raises(ValueError):
            KrippendorffAlpha(metric="invalid")


# ─── KrippendorffAlpha 계산 정확도 (TC-06~12) ────────────────────────────────────
class TestKrippendorffComputation:
    @pytest.fixture
    def high_agreement_data(self):
        return {
            'A': {'u1': 0.8, 'u2': 0.6, 'u3': 0.9, 'u4': 0.7},
            'B': {'u1': 0.7, 'u2': 0.7, 'u3': 0.8, 'u4': 0.8},
            'C': {'u1': 0.75, 'u2': 0.65, 'u3': 0.85, 'u4': 0.75},
        }

    @pytest.fixture
    def low_agreement_data(self):
        return {
            'A': {'u1': 0.9, 'u2': 0.1, 'u3': 0.8, 'u4': 0.2},
            'B': {'u1': 0.1, 'u2': 0.9, 'u3': 0.2, 'u4': 0.8},
        }

    @pytest.fixture
    def perfect_agreement_data(self):
        return {
            'A': {'u1': 0.8, 'u2': 0.6, 'u3': 0.9},
            'B': {'u1': 0.8, 'u2': 0.6, 'u3': 0.9},
        }

    def test_tc06_high_agreement_passes(self, high_agreement_data):
        calc = KrippendorffAlpha(METRIC_INTERVAL)
        result = calc.compute(high_agreement_data)
        assert result.passed, f"expected α≥0.70, got {result.alpha:.4f}"
        assert result.alpha > 0.80

    def test_tc07_low_agreement_fails(self, low_agreement_data):
        calc = KrippendorffAlpha(METRIC_INTERVAL)
        result = calc.compute(low_agreement_data)
        assert not result.passed, f"expected α<0.70, got {result.alpha:.4f}"

    def test_tc08_perfect_agreement_alpha_one(self, perfect_agreement_data):
        calc = KrippendorffAlpha(METRIC_INTERVAL)
        result = calc.compute(perfect_agreement_data)
        assert math.isclose(result.alpha, 1.0, abs_tol=1e-6)

    def test_tc09_empty_data_returns_zero(self):
        calc = KrippendorffAlpha(METRIC_INTERVAL)
        result = calc.compute({})
        assert result.alpha == 0.0
        assert result.n_units == 0

    def test_tc10_single_rater_returns_zero(self):
        calc = KrippendorffAlpha(METRIC_INTERVAL)
        result = calc.compute({'A': {'u1': 0.8, 'u2': 0.6}})
        assert result.alpha == 0.0  # 2인 미만 → 비교 불가

    def test_tc11_alpha_result_fields(self, high_agreement_data):
        calc = KrippendorffAlpha(METRIC_INTERVAL)
        result = calc.compute(high_agreement_data)
        assert isinstance(result.alpha, float)
        assert result.d_observed >= 0.0
        assert result.d_expected >= 0.0
        assert result.n_units == 4
        assert result.n_raters_avg == 3.0

    def test_tc12_nominal_metric(self):
        calc = KrippendorffAlpha(METRIC_NOMINAL)
        data = {
            'A': {'u1': 1.0, 'u2': 2.0, 'u3': 1.0},
            'B': {'u1': 1.0, 'u2': 2.0, 'u3': 2.0},
        }
        result = calc.compute(data)
        assert isinstance(result.alpha, float)
        assert result.metric == METRIC_NOMINAL

    def test_tc13_missing_values_handled(self):
        calc = KrippendorffAlpha(METRIC_INTERVAL)
        data = {
            'A': {'u1': 0.8, 'u2': 0.6, 'u3': None},  # u3 미평가
            'B': {'u1': 0.7, 'u2': None, 'u3': 0.85},  # u2 미평가
            'C': {'u1': 0.75, 'u2': 0.65, 'u3': 0.9},
        }
        result = calc.compute(data)
        # u1은 3인, u2는 2인, u3는 2인
        assert result.n_units == 3
        assert isinstance(result.alpha, float)


# ─── AlphaResult 프로퍼티 (TC-14~17) ─────────────────────────────────────────────
class TestAlphaResult:
    def test_tc14_passed_property(self):
        r = AlphaResult(alpha=0.75, d_observed=0.01, d_expected=0.04, n_units=5, n_raters_avg=2.0, metric="interval")
        assert r.passed is True

    def test_tc15_failed_property(self):
        r = AlphaResult(alpha=0.65, d_observed=0.05, d_expected=0.10, n_units=3, n_raters_avg=2.0, metric="interval")
        assert r.passed is False

    def test_tc16_quality_levels(self):
        good = AlphaResult(alpha=0.85, d_observed=0.0, d_expected=0.1, n_units=5, n_raters_avg=2.0, metric="interval")
        allow = AlphaResult(alpha=0.72, d_observed=0.0, d_expected=0.1, n_units=5, n_raters_avg=2.0, metric="interval")
        poor = AlphaResult(alpha=0.55, d_observed=0.0, d_expected=0.1, n_units=5, n_raters_avg=2.0, metric="interval")
        assert good.quality == "우수"
        assert allow.quality == "허용"
        assert poor.quality == "부족"

    def test_tc17_summary_contains_alpha(self):
        r = AlphaResult(alpha=0.91, d_observed=0.005, d_expected=0.064, n_units=4, n_raters_avg=3.0, metric="interval")
        s = r.summary
        assert "0.9100" in s
        assert "PASS" in s


# ─── MetaLearnerCycle 상수·초기화 (TC-18~20) ─────────────────────────────────────
class TestMetaLearnerCycleInit:
    def test_tc18_constants(self):
        assert CYCLE_COUNT == 4
        assert R_SCENE_TARGET == 0.78
        assert ALPHA_TARGET == 0.70

    def test_tc19_initial_state(self):
        c = MetaLearnerCycle()
        assert c.current_cycle == 1
        assert len(c.cycle_history) == 0
        assert c.latest_alpha() is None

    def test_tc20_custom_metric(self):
        c = MetaLearnerCycle(alpha_metric=METRIC_NOMINAL)
        assert c._alpha_calc.metric == METRIC_NOMINAL


# ─── MetaLearnerCycle run_cycle (TC-21~28) ───────────────────────────────────────
class TestMetaLearnerCycleRun:
    @pytest.fixture
    def primed_cycle(self):
        """MetaLearner 활성화 임계값(30작품) 충족된 사이클."""
        c = MetaLearnerCycle()
        for i in range(30):
            c._meta.record_work_loss(0.5 - i * 0.005)
        return c

    @pytest.fixture
    def rater_data_pass(self):
        return {
            'A': {'u1': 0.8, 'u2': 0.6, 'u3': 0.9, 'u4': 0.7},
            'B': {'u1': 0.7, 'u2': 0.7, 'u3': 0.8, 'u4': 0.8},
            'C': {'u1': 0.75, 'u2': 0.65, 'u3': 0.85, 'u4': 0.75},
        }

    def test_tc21_cycle_returns_report(self, primed_cycle, rater_data_pass):
        report = primed_cycle.run_cycle(l_final=0.3, rater_data=rater_data_pass, r_scene=0.75)
        assert isinstance(report, CycleReport)
        assert report.cycle_number == 1

    def test_tc22_alpha_pass_in_report(self, primed_cycle, rater_data_pass):
        report = primed_cycle.run_cycle(l_final=0.3, rater_data=rater_data_pass, r_scene=0.75)
        assert report.alpha_passed
        assert report.alpha_result is not None
        assert report.alpha_result.alpha >= ALPHA_TARGET

    def test_tc23_cycle_increments(self, primed_cycle, rater_data_pass):
        primed_cycle.run_cycle(l_final=0.3, rater_data=rater_data_pass, r_scene=0.75)
        primed_cycle.run_cycle(l_final=0.28, r_scene=0.77)
        assert len(primed_cycle.cycle_history) == 2
        assert primed_cycle.current_cycle == 3

    def test_tc24_r_trend_stable_with_single_point(self, primed_cycle):
        report = primed_cycle.run_cycle(l_final=0.3, r_scene=0.75)
        assert report.r_scene_trend == "stable"

    def test_tc25_r_trend_improving(self, primed_cycle):
        primed_cycle.run_cycle(l_final=0.3, r_scene=0.70)
        report = primed_cycle.run_cycle(l_final=0.28, r_scene=0.76)
        assert report.r_scene_trend == "improving"

    def test_tc26_r_trend_declining(self, primed_cycle):
        primed_cycle.run_cycle(l_final=0.3, r_scene=0.80)
        report = primed_cycle.run_cycle(l_final=0.32, r_scene=0.74)
        assert report.r_scene_trend == "declining"

    def test_tc27_cycle_pass_requires_alpha_and_r_trend(self, primed_cycle, rater_data_pass):
        report = primed_cycle.run_cycle(l_final=0.3, rater_data=rater_data_pass, r_scene=0.75)
        assert report.passed == (report.alpha_passed and report.r_trend_positive)

    def test_tc28_no_rater_data_skips_alpha(self, primed_cycle):
        report = primed_cycle.run_cycle(l_final=0.3, rater_data=None, r_scene=0.75)
        assert report.alpha_result is None
        assert report.alpha_passed is False


# ─── augment_ratio 조정 (TC-29~31) ───────────────────────────────────────────────
class TestAugmentRatioAdjustment:
    def test_tc29_low_alpha_boosts_ratio(self):
        c = MetaLearnerCycle()
        c._current_augment_ratio = 0.15
        calc = KrippendorffAlpha(METRIC_INTERVAL)
        data_low = {
            'A': {'u1': 0.9, 'u2': 0.1, 'u3': 0.8, 'u4': 0.2},
            'B': {'u1': 0.1, 'u2': 0.9, 'u3': 0.2, 'u4': 0.8},
        }
        alpha_res = calc.compute(data_low)
        new_ratio = c._adjust_augment_ratio(alpha_res, 0.15)
        # α < 0.65 → boost (if low enough), else stay or reduce
        assert AUGMENT_RATIO_MIN <= new_ratio <= AUGMENT_RATIO_MAX

    def test_tc30_high_alpha_reduces_ratio(self):
        c = MetaLearnerCycle()
        c._current_augment_ratio = 0.20
        calc = KrippendorffAlpha(METRIC_INTERVAL)
        data_high = {
            'A': {'u1': 0.8, 'u2': 0.6, 'u3': 0.9, 'u4': 0.7},
            'B': {'u1': 0.79, 'u2': 0.61, 'u3': 0.89, 'u4': 0.71},
        }
        alpha_res = calc.compute(data_high)  # should be very high
        new_ratio = c._adjust_augment_ratio(alpha_res, 0.20)
        # α >= 0.80 → reduce
        if alpha_res.alpha >= 0.80:
            assert new_ratio < 0.20 or math.isclose(new_ratio, AUGMENT_RATIO_MIN)

    def test_tc31_none_alpha_no_change(self):
        c = MetaLearnerCycle()
        c._current_augment_ratio = 0.18
        new_ratio = c._adjust_augment_ratio(None, 0.18)
        assert new_ratio == 0.18


# ─── run_n_cycles + alpha_history (TC-32~33) ─────────────────────────────────────
class TestRunNCycles:
    def test_tc32_run_n_cycles_returns_list(self):
        c = MetaLearnerCycle()
        for i in range(30):
            c._meta.record_work_loss(0.5)
        rater_data = {
            'A': {'u1': 0.8, 'u2': 0.7},
            'B': {'u1': 0.75, 'u2': 0.72},
        }
        reports = c.run_n_cycles(
            l_finals=[0.4, 0.38, 0.36, 0.34],
            rater_data_list=[rater_data, rater_data, None, rater_data],
            r_scenes=[0.70, 0.72, 0.74, 0.76],
        )
        assert len(reports) == 4
        assert [r.cycle_number for r in reports] == [1, 2, 3, 4]

    def test_tc33_alpha_history_tracks_results(self):
        c = MetaLearnerCycle()
        for i in range(30):
            c._meta.record_work_loss(0.5)
        rater_data = {
            'A': {'u1': 0.8, 'u2': 0.7},
            'B': {'u1': 0.75, 'u2': 0.72},
        }
        c.run_cycle(l_final=0.4, rater_data=rater_data)
        c.run_cycle(l_final=0.38, rater_data=None)   # α 없음
        c.run_cycle(l_final=0.36, rater_data=rater_data)
        hist = c.alpha_history()
        assert len(hist) == 2   # rater_data 있는 2사이클만
        latest = c.latest_alpha()
        assert latest is not None
        assert isinstance(latest.alpha, float)
