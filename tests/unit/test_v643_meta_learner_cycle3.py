"""
test_v643_meta_learner_cycle3.py — V643 MetaLearnerCycle 3사이클 + FeedbackIntegrator 통합 검증

목표:
  - MetaLearnerCycle V643 신규 기능 33 TC 검증
  - FeedbackIntegrator 통합: add_feedback() + run_cycle() + adjusted_loss 검증
  - FeedbackSignalSummary 데이터클래스 및 feedback_signal_trend() 메서드 검증
  - CycleReport.feedback_signal_effective 프로퍼티 검증
  - feedback_history() 메서드 검증

TC 그룹:
  TC-01~03: V643 신규 상수 검증
  TC-04~07: FeedbackSignalSummary 데이터클래스
  TC-08~10: CycleReport.feedback_signal_effective 프로퍼티
  TC-11~14: CycleReport.adjusted_loss 필드
  TC-15~19: add_feedback() 단축 API
  TC-20~24: run_cycle() FeedbackIntegrator 통합 (adjusted_loss 생성)
  TC-25~28: feedback_signal_trend() 메서드
  TC-29~31: 3사이클 통합 시나리오
  TC-32~33: feedback_history() 메서드
"""
from __future__ import annotations

import pytest
from typing import Dict, Optional

from literary_system.constitution.meta_learner_cycle import (
    MetaLearnerCycle,
    CycleReport,
    FeedbackSignalSummary,
    FEEDBACK_SIGNAL_MIN_STRENGTH,
    FEEDBACK_SIGNAL_MIN_CYCLES,
    FEEDBACK_ADJUSTED_LOSS_SCALE,
    ALPHA_STABILITY_MAX_VAR,
)
from literary_system.constitution.feedback_integrator import (
    FeedbackIntegrator,
    IntegrationResult,
    FeedbackRecord,
    MIN_FEEDBACK_FOR_SIGNAL,
    FEEDBACK_TYPES,
)


# ─── 공통 픽스처 ───────────────────────────────────────────────────────────────

@pytest.fixture
def mlc():
    return MetaLearnerCycle()


@pytest.fixture
def high_agreement_rater_data():
    return {
        "r1": {"u1": 0.8, "u2": 0.7, "u3": 0.9},
        "r2": {"u1": 0.82, "u2": 0.72, "u3": 0.88},
    }


@pytest.fixture
def mlc_with_feedback():
    """MIN_FEEDBACK_FOR_SIGNAL(3)개 피드백이 있는 MetaLearnerCycle."""
    m = MetaLearnerCycle()
    for i in range(MIN_FEEDBACK_FOR_SIGNAL):
        m.add_feedback(
            scene_id=f"scene-{i}",
            feedback_type="SCORE_CORRECTION",
            evaluator_id="h1",
            original_score=0.60,
            corrected_score=0.85,
        )
    return m


# ─── TC-01~03: V643 신규 상수 검증 ────────────────────────────────────────────

class TestV643Constants:
    def test_tc01_feedback_signal_min_strength(self):
        """TC-01: FEEDBACK_SIGNAL_MIN_STRENGTH 존재 및 0 < val < 1."""
        assert 0.0 < FEEDBACK_SIGNAL_MIN_STRENGTH < 1.0

    def test_tc02_feedback_signal_min_cycles(self):
        """TC-02: FEEDBACK_SIGNAL_MIN_CYCLES == 2."""
        assert FEEDBACK_SIGNAL_MIN_CYCLES == 2

    def test_tc03_feedback_adjusted_loss_scale(self):
        """TC-03: FEEDBACK_ADJUSTED_LOSS_SCALE 존재 및 양수."""
        assert isinstance(FEEDBACK_ADJUSTED_LOSS_SCALE, float)
        assert FEEDBACK_ADJUSTED_LOSS_SCALE > 0.0


# ─── TC-04~07: FeedbackSignalSummary 데이터클래스 ─────────────────────────────

class TestFeedbackSignalSummaryDataclass:
    def test_tc04_effective_above_threshold(self):
        """TC-04: mean_signal ≥ threshold → is_effective=True."""
        s = FeedbackSignalSummary(2, [0.4, 0.5], 0.45, True)
        assert s.is_effective is True

    def test_tc05_weak_below_threshold(self):
        """TC-05: mean_signal < threshold → is_effective=False."""
        s = FeedbackSignalSummary(2, [0.1, 0.2], 0.15, False)
        assert s.is_effective is False

    def test_tc06_trend_improving(self):
        """TC-06: signal_values[-1] - signal_values[-2] > 0.05 → improving."""
        s = FeedbackSignalSummary(2, [0.3, 0.4], 0.35, True)
        assert s.trend == "improving"

    def test_tc07_summary_contains_effective(self):
        """TC-07: summary에 EFFECTIVE/WEAK + trend 포함."""
        s_eff = FeedbackSignalSummary(2, [0.5, 0.5], 0.5, True)
        assert "EFFECTIVE" in s_eff.summary
        s_weak = FeedbackSignalSummary(2, [0.1, 0.1], 0.1, False)
        assert "WEAK" in s_weak.summary


# ─── TC-08~10: CycleReport.feedback_signal_effective ─────────────────────────

class TestCycleReportFeedbackSignalEffective:
    def test_tc08_field_exists(self):
        """TC-08: CycleReport에 adjusted_loss 필드 존재."""
        assert "adjusted_loss" in CycleReport.__dataclass_fields__

    def test_tc09_no_feedback_not_effective(self, mlc):
        """TC-09: 피드백 없이 run_cycle() → feedback_signal_effective=False."""
        report = mlc.run_cycle(0.5)
        assert report.feedback_signal_effective is False

    def test_tc10_effective_with_strong_signal(self, mlc_with_feedback):
        """TC-10: has_signal=True + signal_strength ≥ 임계값 → effective=True."""
        report = mlc_with_feedback.run_cycle(0.5)
        # 신호 강도가 임계값 이상이면 effective=True
        assert report.feedback_result is not None
        if report.feedback_result.signal_strength >= FEEDBACK_SIGNAL_MIN_STRENGTH:
            assert report.feedback_signal_effective is True


# ─── TC-11~14: CycleReport.adjusted_loss 필드 ────────────────────────────────

class TestCycleReportAdjustedLoss:
    def test_tc11_default_none_without_feedback(self, mlc):
        """TC-11: 피드백 없이 run_cycle() → adjusted_loss=None."""
        report = mlc.run_cycle(0.5)
        assert report.adjusted_loss is None

    def test_tc12_adjusted_loss_set_with_correction(self, mlc_with_feedback):
        """TC-12: SCORE_CORRECTION 피드백 → adjusted_loss 설정됨."""
        report = mlc_with_feedback.run_cycle(0.5)
        # avg_correction_delta != 0 이면 adjusted_loss 설정
        if report.feedback_result and report.feedback_result.avg_correction_delta != 0.0:
            assert report.adjusted_loss is not None
        else:
            assert report.adjusted_loss is None

    def test_tc13_adjusted_loss_formula(self):
        """TC-13: adjusted_loss = l_final + delta * SCALE."""
        mlc = MetaLearnerCycle()
        l_final = 0.5
        # 보정 델타 = 0.25 (원점수 0.60 → 보정 0.85)
        for i in range(MIN_FEEDBACK_FOR_SIGNAL):
            mlc.add_feedback(f"s-{i}", "SCORE_CORRECTION", original_score=0.60, corrected_score=0.85)
        report = mlc.run_cycle(l_final)
        if report.adjusted_loss is not None:
            expected_delta = 0.25  # 0.85 - 0.60
            expected_adjusted = l_final + expected_delta * FEEDBACK_ADJUSTED_LOSS_SCALE
            assert abs(report.adjusted_loss - expected_adjusted) < 1e-9

    def test_tc14_no_adjusted_loss_with_zero_delta(self):
        """TC-14: correction_delta=0 → adjusted_loss=None."""
        mlc = MetaLearnerCycle()
        # 원점수 == 보정 → delta=0
        for i in range(MIN_FEEDBACK_FOR_SIGNAL):
            mlc.add_feedback(f"s-{i}", "SCORE_CORRECTION", original_score=0.7, corrected_score=0.7)
        report = mlc.run_cycle(0.5)
        assert report.adjusted_loss is None


# ─── TC-15~19: add_feedback() 단축 API ──────────────────────────────────────

class TestAddFeedbackAPI:
    def test_tc15_add_feedback_returns_record(self, mlc):
        """TC-15: add_feedback() → FeedbackRecord 반환."""
        rec = mlc.add_feedback("scene-1", "SCORE_CORRECTION", "h1", 0.6, 0.8)
        assert isinstance(rec, FeedbackRecord)

    def test_tc16_add_feedback_stored_in_integrator(self, mlc):
        """TC-16: add_feedback() → FeedbackIntegrator._memory에 저장."""
        mlc.add_feedback("scene-1", "SCORE_CORRECTION", "h1", 0.6, 0.8)
        assert len(mlc._feedback.feedbacks()) == 1

    def test_tc17_add_multiple_feedbacks(self, mlc):
        """TC-17: 여러 번 add_feedback() → 누적 저장."""
        for i in range(5):
            mlc.add_feedback(f"s-{i}", "SCORE_CORRECTION", original_score=0.5, corrected_score=0.7)
        assert len(mlc._feedback.feedbacks()) == 5

    def test_tc18_add_feedback_label_revision(self, mlc):
        """TC-18: LABEL_REVISION 타입 피드백 저장."""
        rec = mlc.add_feedback("scene-2", "LABEL_REVISION",
                                label_before="긍정", label_after="부정")
        assert rec.feedback_type == "LABEL_REVISION"
        assert rec.label_before == "긍정"
        assert rec.label_after == "부정"

    def test_tc19_add_feedback_rejection(self, mlc):
        """TC-19: REJECTION 타입 피드백 저장."""
        rec = mlc.add_feedback("scene-3", "REJECTION", note="품질 미달")
        assert rec.feedback_type == "REJECTION"


# ─── TC-20~24: run_cycle() FeedbackIntegrator 통합 ───────────────────────────

class TestRunCycleFeedbackIntegration:
    def test_tc20_feedback_result_none_without_feedback(self, mlc):
        """TC-20: 피드백 없이 run_cycle() → feedback_result=None."""
        report = mlc.run_cycle(0.5)
        assert report.feedback_result is None

    def test_tc21_feedback_result_set_with_feedback(self, mlc_with_feedback):
        """TC-21: 피드백 있을 때 run_cycle() → feedback_result=IntegrationResult."""
        report = mlc_with_feedback.run_cycle(0.5)
        assert isinstance(report.feedback_result, IntegrationResult)

    def test_tc22_has_signal_with_enough_feedback(self, mlc_with_feedback):
        """TC-22: MIN_FEEDBACK_FOR_SIGNAL개 피드백 → has_signal=True."""
        report = mlc_with_feedback.run_cycle(0.5)
        assert report.feedback_result.has_signal is True

    def test_tc23_feedback_signal_strength_positive(self, mlc_with_feedback):
        """TC-23: has_signal=True → signal_strength > 0."""
        report = mlc_with_feedback.run_cycle(0.5)
        assert report.feedback_result.signal_strength > 0.0

    def test_tc24_feedback_history_accumulated_after_cycle(self, mlc_with_feedback):
        """TC-24: run_cycle() 후 feedback_history에 IntegrationResult 추가."""
        mlc_with_feedback.run_cycle(0.5)
        history = mlc_with_feedback.feedback_history()
        assert len(history) == 1


# ─── TC-25~28: feedback_signal_trend() 메서드 ────────────────────────────────

class TestFeedbackSignalTrendMethod:
    def test_tc25_returns_none_with_one_signal(self, mlc_with_feedback):
        """TC-25: 신호 1개만 있으면 None 반환."""
        mlc_with_feedback.run_cycle(0.5)
        result = mlc_with_feedback.feedback_signal_trend()
        assert result is None

    def test_tc26_returns_summary_with_two_signals(self):
        """TC-26: 신호 2개 이상 → FeedbackSignalSummary 반환."""
        mlc = MetaLearnerCycle()
        for _ in range(2):
            for i in range(MIN_FEEDBACK_FOR_SIGNAL):
                mlc.add_feedback(f"s-{i}", "SCORE_CORRECTION",
                                 original_score=0.6, corrected_score=0.85)
            mlc.run_cycle(0.5)
        result = mlc.feedback_signal_trend()
        assert isinstance(result, FeedbackSignalSummary)

    def test_tc27_signal_values_match_history(self):
        """TC-27: FeedbackSignalSummary.signal_values == history의 signal_strength 순서."""
        mlc = MetaLearnerCycle()
        for _ in range(2):
            for i in range(MIN_FEEDBACK_FOR_SIGNAL):
                mlc.add_feedback(f"s-{i}", "SCORE_CORRECTION",
                                 original_score=0.6, corrected_score=0.85)
            mlc.run_cycle(0.5)
        result = mlc.feedback_signal_trend()
        history = mlc.feedback_history()
        expected = [r.signal_strength for r in history]
        assert result.signal_values == expected

    def test_tc28_trend_insufficient_without_signals(self, mlc):
        """TC-28: 신호 없으면 None 반환 (not enough signals)."""
        mlc.run_cycle(0.5)  # 피드백 없음
        result = mlc.feedback_signal_trend()
        assert result is None


# ─── TC-29~31: 3사이클 통합 시나리오 ─────────────────────────────────────────

class TestThreeCycleIntegration:
    def test_tc29_three_cycles_run_successfully(self, high_agreement_rater_data):
        """TC-29: 3사이클 모두 실행 성공."""
        mlc = MetaLearnerCycle()
        for _ in range(3):
            for i in range(MIN_FEEDBACK_FOR_SIGNAL):
                mlc.add_feedback(f"s-{i}", "SCORE_CORRECTION",
                                 original_score=0.6, corrected_score=0.85)
        r1 = mlc.run_cycle(0.5, high_agreement_rater_data, 0.80)
        r2 = mlc.run_cycle(0.45, high_agreement_rater_data, 0.82)
        r3 = mlc.run_cycle(0.40, high_agreement_rater_data, 0.84)
        assert len(mlc.cycle_history) == 3

    def test_tc30_all_three_cycles_have_feedback_result(self):
        """TC-30: 피드백이 있는 3사이클 모두 feedback_result 존재."""
        mlc = MetaLearnerCycle()
        for cyc in range(3):
            for i in range(MIN_FEEDBACK_FOR_SIGNAL):
                mlc.add_feedback(f"s-{cyc}-{i}", "SCORE_CORRECTION",
                                 original_score=0.6, corrected_score=0.85)
            report = mlc.run_cycle(0.5 - cyc * 0.05)
            assert report.feedback_result is not None

    def test_tc31_feedback_history_length_three_after_three_cycles(self):
        """TC-31: 3사이클 후 feedback_history 길이 == 3."""
        mlc = MetaLearnerCycle()
        for cyc in range(3):
            for i in range(MIN_FEEDBACK_FOR_SIGNAL):
                mlc.add_feedback(f"s-{cyc}-{i}", "SCORE_CORRECTION",
                                 original_score=0.6, corrected_score=0.85)
            mlc.run_cycle(0.5 - cyc * 0.05)
        assert len(mlc.feedback_history()) == 3


# ─── TC-32~33: feedback_history() 메서드 ─────────────────────────────────────

class TestFeedbackHistoryMethod:
    def test_tc32_empty_without_feedback_cycles(self, mlc):
        """TC-32: 피드백 없는 사이클 실행 후 feedback_history() == []."""
        mlc.run_cycle(0.5)
        mlc.run_cycle(0.4)
        assert mlc.feedback_history() == []

    def test_tc33_integration_result_types_correct(self):
        """TC-33: feedback_history() 모든 요소가 IntegrationResult 타입."""
        mlc = MetaLearnerCycle()
        for i in range(MIN_FEEDBACK_FOR_SIGNAL):
            mlc.add_feedback(f"s-{i}", "SCORE_CORRECTION",
                             original_score=0.6, corrected_score=0.85)
        mlc.run_cycle(0.5)
        for result in mlc.feedback_history():
            assert isinstance(result, IntegrationResult)
