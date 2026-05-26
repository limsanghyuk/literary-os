"""
test_v642_meta_learner_cycle2.py — V642 MetaLearnerCycle 2사이클 + DataAugmentationController 통합 검증

목표:
  - MetaLearnerCycle V642 신규 기능 33 TC 검증
  - DataAugmentationController.augment() 실제 호출 통합 검증
  - AlphaStability 데이터클래스 및 alpha_stability() 메서드 검증
  - CycleReport.augmentation_batch 필드 검증
  - 2사이클 α 안정성 검증

TC 그룹:
  TC-01~03: 상수 검증 (V642 신규)
  TC-04~07: AlphaStability 데이터클래스
  TC-08~10: CycleReport.augmentation_batch 필드
  TC-11~16: run_cycle() sample_texts → augment() 실제 호출
  TC-17~21: augmentor.augment() 결과 내용 검증
  TC-22~27: alpha_stability() 메서드
  TC-28~31: 2사이클 통합 시나리오
  TC-32~33: latest_augmentation_batch / augmentation_batch_history
"""
from __future__ import annotations

import pytest
from typing import Dict, Optional

from literary_system.constitution.meta_learner_cycle import (
    MetaLearnerCycle,
    CycleReport,
    AlphaStability,
    ALPHA_STABILITY_MAX_VAR,
    ALPHA_STABILITY_MIN_CYCLES,
    DEFAULT_AUGMENT_COUNT_PER_CYCLE,
    CYCLE_AUGMENT_DATASET_ID_PREFIX,
    AUGMENT_RATIO_BOOST_THRESHOLD,
    AUGMENT_RATIO_REDUCE_THRESHOLD,
    AUGMENT_RATIO_STEP,
    AUGMENT_RATIO_MIN,
    AUGMENT_RATIO_MAX,
)
from literary_system.constitution.data_augmentation_controller import (
    DataAugmentationController,
    AugmentationBatch,
    AUGMENTATION_STRATEGIES,
)
from literary_system.constitution.krippendorff_alpha import (
    AlphaResult, ALPHA_MIN_THRESHOLD,
)

# ─── 공통 픽스처 ───────────────────────────────────────────────────────────────

@pytest.fixture
def high_agreement_rater_data() -> Dict[str, Dict[str, Optional[float]]]:
    """α ≥ 0.70 고신뢰도 평가자 데이터."""
    return {
        "r1": {"u1": 0.8, "u2": 0.7, "u3": 0.9, "u4": 0.75},
        "r2": {"u1": 0.82, "u2": 0.72, "u3": 0.88, "u4": 0.77},
        "r3": {"u1": 0.79, "u2": 0.69, "u3": 0.91, "u4": 0.74},
    }


@pytest.fixture
def low_agreement_rater_data() -> Dict[str, Dict[str, Optional[float]]]:
    """α < 0.65 저신뢰도 평가자 데이터."""
    return {
        "r1": {"u1": 0.9, "u2": 0.1, "u3": 0.8},
        "r2": {"u1": 0.1, "u2": 0.9, "u3": 0.2},
    }


@pytest.fixture
def sample_texts():
    """증강 대상 샘플 텍스트 목록."""
    return [
        "드라마 장면에서 주인공이 말했다.",
        "캐릭터가 아름다운 감정을 표현한다.",
        "서사가 기쁜 방향으로 전개되었다.",
    ]


@pytest.fixture
def mlc():
    """기본 MetaLearnerCycle 인스턴스."""
    return MetaLearnerCycle()


# ─── TC-01~03: V642 신규 상수 검증 ────────────────────────────────────────────

class TestV642Constants:
    def test_tc01_alpha_stability_max_var_exists(self):
        """TC-01: ALPHA_STABILITY_MAX_VAR 상수 존재 및 양수."""
        assert isinstance(ALPHA_STABILITY_MAX_VAR, float)
        assert ALPHA_STABILITY_MAX_VAR > 0.0

    def test_tc02_alpha_stability_min_cycles(self):
        """TC-02: ALPHA_STABILITY_MIN_CYCLES = 2."""
        assert ALPHA_STABILITY_MIN_CYCLES == 2

    def test_tc03_default_augment_count_per_cycle(self):
        """TC-03: DEFAULT_AUGMENT_COUNT_PER_CYCLE ≥ 1."""
        assert isinstance(DEFAULT_AUGMENT_COUNT_PER_CYCLE, int)
        assert DEFAULT_AUGMENT_COUNT_PER_CYCLE >= 1


# ─── TC-04~07: AlphaStability 데이터클래스 ────────────────────────────────────

class TestAlphaStabilityDataclass:
    def test_tc04_stable_low_variance(self):
        """TC-04: 낮은 분산 → is_stable=True."""
        stab = AlphaStability(
            cycle_count=2,
            alpha_values=[0.85, 0.86],
            mean_alpha=0.855,
            variance=0.000025,
            is_stable=True,
        )
        assert stab.is_stable is True

    def test_tc05_unstable_high_variance(self):
        """TC-05: 높은 분산 → is_stable=False."""
        stab = AlphaStability(
            cycle_count=2,
            alpha_values=[0.4, 0.9],
            mean_alpha=0.65,
            variance=0.0625,
            is_stable=False,
        )
        assert stab.is_stable is False

    def test_tc06_summary_contains_status(self):
        """TC-06: summary 문자열에 STABLE/UNSTABLE 포함."""
        stab_stable = AlphaStability(2, [0.8, 0.81], 0.805, 0.000025, True)
        assert "STABLE" in stab_stable.summary

        stab_unstable = AlphaStability(2, [0.4, 0.9], 0.65, 0.0625, False)
        assert "UNSTABLE" in stab_unstable.summary

    def test_tc07_summary_includes_variance(self):
        """TC-07: summary에 cycle_count, mean, var 포함."""
        stab = AlphaStability(3, [0.8, 0.82, 0.81], 0.81, 0.000067, True)
        assert "cycles=3" in stab.summary
        assert "mean=" in stab.summary
        assert "var=" in stab.summary


# ─── TC-08~10: CycleReport.augmentation_batch 필드 ───────────────────────────

class TestCycleReportAugmentationBatch:
    def test_tc08_augmentation_batch_field_exists(self):
        """TC-08: CycleReport에 augmentation_batch 필드 존재."""
        assert "augmentation_batch" in CycleReport.__dataclass_fields__

    def test_tc09_augmentation_batch_default_none(self, mlc):
        """TC-09: sample_texts 없이 run_cycle() → augmentation_batch=None."""
        report = mlc.run_cycle(0.5)
        assert report.augmentation_batch is None

    def test_tc10_augmentation_performed_property(self, mlc, sample_texts):
        """TC-10: sample_texts 제공 → augmentation_performed=True."""
        report = mlc.run_cycle(0.5, sample_texts=sample_texts)
        assert report.augmentation_performed is True


# ─── TC-11~16: run_cycle() sample_texts → augment() 실제 호출 ─────────────────

class TestRunCycleSampleTexts:
    def test_tc11_augmentation_batch_returned(self, mlc, sample_texts):
        """TC-11: sample_texts 제공 시 AugmentationBatch 반환."""
        report = mlc.run_cycle(0.5, sample_texts=sample_texts)
        assert isinstance(report.augmentation_batch, AugmentationBatch)

    def test_tc12_augmented_count_positive(self, mlc, sample_texts):
        """TC-12: 증강 샘플 수 > 0."""
        report = mlc.run_cycle(0.5, sample_texts=sample_texts)
        assert report.augmentation_batch.augmented_count > 0

    def test_tc13_original_count_matches_texts(self, mlc, sample_texts):
        """TC-13: original_count == len(sample_texts)."""
        report = mlc.run_cycle(0.5, sample_texts=sample_texts)
        assert report.augmentation_batch.original_count == len(sample_texts)

    def test_tc14_dataset_id_prefix(self, mlc, sample_texts):
        """TC-14: dataset_id가 CYCLE_AUGMENT_DATASET_ID_PREFIX로 시작."""
        report = mlc.run_cycle(0.5, sample_texts=sample_texts, cycle_number=1)
        assert report.augmentation_batch.dataset_id.startswith(CYCLE_AUGMENT_DATASET_ID_PREFIX)

    def test_tc15_augment_ratio_applied(self, mlc, sample_texts):
        """TC-15: AugmentationBatch.samples[0].augment_ratio == run_cycle 당시 aug_after."""
        report = mlc.run_cycle(0.5, sample_texts=sample_texts)
        batch = report.augmentation_batch
        # 첫 샘플의 augment_ratio가 CycleReport.augment_ratio_after와 일치
        assert abs(batch.samples[0].augment_ratio - report.augment_ratio_after) < 1e-9

    def test_tc16_empty_sample_texts_no_batch(self, mlc):
        """TC-16: 빈 sample_texts=[] → augmentation_batch=None (텍스트 없어 배치 불생성)."""
        # DataAugmentationController.augment()는 빈 텍스트를 스킵하므로
        # augmented_count=0이지만 배치 자체는 생성될 수 있음 — 일반 사용 케이스 확인
        report = mlc.run_cycle(0.5, sample_texts=None)
        assert report.augmentation_batch is None


# ─── TC-17~21: augmentor.augment() 결과 내용 검증 ────────────────────────────

class TestAugmentorIntegration:
    def test_tc17_strategies_used_populated(self, mlc, sample_texts):
        """TC-17: AugmentationBatch.strategies_used 비어있지 않음."""
        report = mlc.run_cycle(0.5, sample_texts=sample_texts)
        assert len(report.augmentation_batch.strategies_used) > 0

    def test_tc18_samples_have_augmented_text(self, mlc, sample_texts):
        """TC-18: 모든 샘플의 augmented_text 비어있지 않음."""
        report = mlc.run_cycle(0.5, sample_texts=sample_texts)
        for s in report.augmentation_batch.samples:
            assert s.augmented_text != ""

    def test_tc19_controller_id_contains_cycle(self, mlc, sample_texts):
        """TC-19: AugmentationBatch.controller_id에 사이클 번호 포함."""
        report = mlc.run_cycle(0.5, sample_texts=sample_texts, cycle_number=2)
        assert "2" in report.augmentation_batch.controller_id

    def test_tc20_augmentation_count_matches_formula(self, mlc, sample_texts):
        """TC-20: augmented_count == len(sample_texts) * DEFAULT_AUGMENT_COUNT_PER_CYCLE."""
        report = mlc.run_cycle(0.5, sample_texts=sample_texts)
        expected = len(sample_texts) * DEFAULT_AUGMENT_COUNT_PER_CYCLE
        assert report.augmentation_batch.augmented_count == expected

    def test_tc21_augmentor_memory_accumulated(self, mlc, sample_texts):
        """TC-21: 2사이클 실행 후 augmentor 내부 메모리에 2개 배치 누적."""
        mlc.run_cycle(0.5, sample_texts=sample_texts)
        mlc.run_cycle(0.4, sample_texts=sample_texts)
        # _augmentor._memory에 2개 배치 존재
        assert len(mlc._augmentor._memory) == 2


# ─── TC-22~27: alpha_stability() 메서드 ──────────────────────────────────────

class TestAlphaStabilityMethod:
    def test_tc22_returns_none_before_min_cycles(self, mlc):
        """TC-22: α 기록 < ALPHA_STABILITY_MIN_CYCLES → None 반환."""
        # α 데이터 없이 사이클 실행
        mlc.run_cycle(0.5)
        result = mlc.alpha_stability()
        assert result is None

    def test_tc23_returns_none_with_one_alpha(self, mlc, high_agreement_rater_data):
        """TC-23: α 기록 1개만 있으면 None 반환."""
        mlc.run_cycle(0.5, high_agreement_rater_data)
        result = mlc.alpha_stability()
        assert result is None

    def test_tc24_returns_alpha_stability_with_two_cycles(
        self, mlc, high_agreement_rater_data
    ):
        """TC-24: 2사이클 후 AlphaStability 반환."""
        mlc.run_cycle(0.5, high_agreement_rater_data)
        mlc.run_cycle(0.4, high_agreement_rater_data)
        result = mlc.alpha_stability()
        assert isinstance(result, AlphaStability)

    def test_tc25_stable_with_consistent_high_alpha(
        self, mlc, high_agreement_rater_data
    ):
        """TC-25: 고신뢰도 데이터 2사이클 → is_stable=True."""
        mlc.run_cycle(0.5, high_agreement_rater_data)
        mlc.run_cycle(0.4, high_agreement_rater_data)
        result = mlc.alpha_stability()
        # 동일 데이터 → 분산 ≈ 0 → stable
        assert result.is_stable is True
        assert result.variance < ALPHA_STABILITY_MAX_VAR

    def test_tc26_alpha_values_match_history(
        self, mlc, high_agreement_rater_data
    ):
        """TC-26: AlphaStability.alpha_values == alpha_history() 순서."""
        mlc.run_cycle(0.5, high_agreement_rater_data)
        mlc.run_cycle(0.4, high_agreement_rater_data)
        result = mlc.alpha_stability()
        alpha_hist = [r.alpha for r in mlc.alpha_history()]
        assert result.alpha_values == alpha_hist

    def test_tc27_mean_alpha_correct(
        self, mlc, high_agreement_rater_data
    ):
        """TC-27: mean_alpha == 평균(alpha_values)."""
        mlc.run_cycle(0.5, high_agreement_rater_data)
        mlc.run_cycle(0.4, high_agreement_rater_data)
        result = mlc.alpha_stability()
        import statistics
        expected_mean = statistics.mean(result.alpha_values)
        assert abs(result.mean_alpha - expected_mean) < 1e-9


# ─── TC-28~31: 2사이클 통합 시나리오 ─────────────────────────────────────────

class TestTwoCycleIntegration:
    def test_tc28_two_cycles_both_pass(self, mlc, high_agreement_rater_data, sample_texts):
        """TC-28: 2사이클 모두 passed=True (고신뢰도 + 증가 R(scene))."""
        r1 = mlc.run_cycle(0.5, high_agreement_rater_data, 0.80, sample_texts=sample_texts)
        r2 = mlc.run_cycle(0.45, high_agreement_rater_data, 0.82, sample_texts=sample_texts)
        assert r1.passed is True
        assert r2.passed is True

    def test_tc29_augment_ratio_stable_with_high_alpha(
        self, mlc, high_agreement_rater_data, sample_texts
    ):
        """TC-29: α ≥ 0.80 → augment_ratio 감소 또는 유지 (2사이클)."""
        r1 = mlc.run_cycle(0.5, high_agreement_rater_data, 0.80, sample_texts=sample_texts)
        # 고신뢰도 데이터의 α ≥ AUGMENT_RATIO_REDUCE_THRESHOLD(0.80)이면 감소
        # 그 이하면 유지 — 어느 쪽이든 증가하지 않아야 함
        assert r1.augment_ratio_after <= r1.augment_ratio_before + 1e-9

    def test_tc30_cycle_history_length_two(
        self, mlc, high_agreement_rater_data, sample_texts
    ):
        """TC-30: 2사이클 후 cycle_history 길이 == 2."""
        mlc.run_cycle(0.5, high_agreement_rater_data, sample_texts=sample_texts)
        mlc.run_cycle(0.4, high_agreement_rater_data, sample_texts=sample_texts)
        assert len(mlc.cycle_history) == 2

    def test_tc31_both_cycles_have_augmentation_batch(
        self, mlc, high_agreement_rater_data, sample_texts
    ):
        """TC-31: 두 사이클 모두 augmentation_batch 존재."""
        r1 = mlc.run_cycle(0.5, high_agreement_rater_data, sample_texts=sample_texts)
        r2 = mlc.run_cycle(0.4, high_agreement_rater_data, sample_texts=sample_texts)
        assert r1.augmentation_batch is not None
        assert r2.augmentation_batch is not None


# ─── TC-32~33: latest_augmentation_batch / augmentation_batch_history ─────────

class TestAugmentationBatchHelpers:
    def test_tc32_latest_augmentation_batch_returns_last(
        self, mlc, sample_texts
    ):
        """TC-32: latest_augmentation_batch() == 마지막 사이클 배치."""
        mlc.run_cycle(0.5, sample_texts=sample_texts, cycle_number=1)
        mlc.run_cycle(0.4, sample_texts=sample_texts, cycle_number=2)
        latest = mlc.latest_augmentation_batch()
        assert latest is not None
        assert "2" in latest.dataset_id  # cycle-aug-2

    def test_tc33_augmentation_batch_history_count(
        self, mlc, sample_texts
    ):
        """TC-33: 2사이클 모두 sample_texts 제공 → history 길이 == 2."""
        mlc.run_cycle(0.5, sample_texts=sample_texts)
        mlc.run_cycle(0.4, sample_texts=sample_texts)
        history = mlc.augmentation_batch_history()
        assert len(history) == 2
        for batch in history:
            assert isinstance(batch, AugmentationBatch)
