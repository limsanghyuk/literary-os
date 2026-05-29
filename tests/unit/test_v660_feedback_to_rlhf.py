"""V660 FeedbackToRLHF Adapter 테스트 (ADR-120) — 33 TC."""
from __future__ import annotations

import pytest

from literary_system.feedback import (
    AnonymizedFeedback,
    ConsentLevel,
    FeedbackToRLHFAdapter,
    FeedbackType,
    OutlierPolicy,
    ReaderFeedbackCollector,
    RLHFBatch,
    RLHFSample,
)


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def adapter():
    return FeedbackToRLHFAdapter(OutlierPolicy(z_threshold=2.0, min_samples_after_filter=5))


@pytest.fixture
def collector():
    col = ReaderFeedbackCollector()
    texts = [
        "감동적인 씬이었습니다.", "캐릭터가 생생합니다.", "문체가 아름답습니다.",
        "플롯이 탄탄합니다.", "긴장감이 훌륭합니다.", "대화가 자연스럽습니다.",
        "씬의 묘사가 뛰어납니다.", "감정이 잘 전달됩니다.",
    ]
    scores = [4.0, 4.5, 3.8, 4.2, 4.6, 3.9, 4.1, 4.3]
    for i, (t, s) in enumerate(zip(texts, scores)):
        col.collect(f"r{i}", t, s, consent=ConsentLevel.ANONYMOUS)
    return col


def _make_feedbacks(scores: list[float]) -> list[AnonymizedFeedback]:
    col = ReaderFeedbackCollector()
    result = []
    for i, s in enumerate(scores):
        fb = col.collect(f"r{i}", f"피드백 {i}번입니다.", s)
        result.append(fb)
    return result


# ── TC-01~06: 기본 변환 ───────────────────────────────────────────────────

class TestConvert:
    def test_returns_rlhf_batch(self, adapter, collector):                 # TC-01
        fbs = collector.get_feedback()
        batch = adapter.convert(fbs)
        assert isinstance(batch, RLHFBatch)

    def test_batch_id_prefix(self, adapter, collector):                    # TC-02
        fbs = collector.get_feedback()
        batch = adapter.convert(fbs)
        assert batch.batch_id.startswith("batch_")

    def test_samples_are_rlhf_sample(self, adapter, collector):            # TC-03
        fbs = collector.get_feedback()
        batch = adapter.convert(fbs)
        assert all(isinstance(s, RLHFSample) for s in batch.samples)

    def test_normalized_score_range(self, adapter, collector):             # TC-04
        fbs = collector.get_feedback()
        batch = adapter.convert(fbs)
        for s in batch.samples:
            assert 0.0 <= s.normalized_score <= 1.0

    def test_raw_score_preserved(self, adapter, collector):                # TC-05
        fbs = collector.get_feedback()
        batch = adapter.convert(fbs)
        for s in batch.samples:
            assert 1.0 <= s.raw_score <= 5.0

    def test_batch_size_positive(self, adapter, collector):                # TC-06
        fbs = collector.get_feedback()
        batch = adapter.convert(fbs)
        assert batch.size > 0


# ── TC-07~13: z-score 이상치 제거 ─────────────────────────────────────────

class TestOutlierRemoval:
    def test_outlier_removed(self, adapter):                               # TC-07
        # 이상치: 1.0 (평균≈4, std≈0.2 → z>>2)
        scores = [4.0, 4.1, 3.9, 4.2, 4.0, 4.1, 3.8, 1.0]
        fbs = _make_feedbacks(scores)
        batch = adapter.convert(fbs)
        assert batch.outliers_removed >= 1

    def test_normal_data_no_outlier(self, adapter):                        # TC-08
        scores = [4.0, 4.1, 3.9, 4.2, 4.0, 4.1]
        fbs = _make_feedbacks(scores)
        batch = adapter.convert(fbs)
        assert batch.outliers_removed == 0

    def test_outlier_count_in_batch(self, adapter):                        # TC-09
        scores = [4.0, 4.0, 4.0, 4.0, 4.0, 1.0, 5.0]  # 양쪽 극단
        fbs = _make_feedbacks(scores)
        batch = adapter.convert(fbs)
        assert batch.outliers_removed >= 1

    def test_mean_score_in_batch(self, adapter):                           # TC-10
        scores = [4.0, 4.0, 4.0, 4.0, 4.0]
        fbs = _make_feedbacks(scores)
        batch = adapter.convert(fbs)
        assert abs(batch.mean_score - 4.0) < 0.1

    def test_std_score_in_batch(self, adapter):                            # TC-11
        scores = [4.0, 4.0, 4.0, 4.0, 4.0]
        fbs = _make_feedbacks(scores)
        batch = adapter.convert(fbs)
        assert batch.std_score == 0.0

    def test_z_threshold_respected(self, adapter):                         # TC-12
        assert adapter._policy.z_threshold == 2.0

    def test_custom_z_threshold(self):                                     # TC-13
        strict = FeedbackToRLHFAdapter(OutlierPolicy(z_threshold=1.0, min_samples_after_filter=3))
        scores = [4.0, 4.0, 4.0, 4.0, 2.0, 4.0]
        fbs = _make_feedbacks(scores)
        batch = strict.convert(fbs)
        assert batch.outliers_removed >= 1


# ── TC-14~19: 정규화 ──────────────────────────────────────────────────────

class TestNormalization:
    def test_score_1_maps_to_0(self, adapter):                             # TC-14
        fbs = _make_feedbacks([1.0] * 6)
        batch = adapter.convert(fbs)
        assert all(s.normalized_score == 0.0 for s in batch.samples)

    def test_score_5_maps_to_1(self, adapter):                             # TC-15
        fbs = _make_feedbacks([5.0] * 6)
        batch = adapter.convert(fbs)
        assert all(s.normalized_score == 1.0 for s in batch.samples)

    def test_score_3_maps_to_half(self, adapter):                          # TC-16
        fbs = _make_feedbacks([3.0] * 6)
        batch = adapter.convert(fbs)
        assert all(abs(s.normalized_score - 0.5) < 0.01 for s in batch.samples)

    def test_extreme_weight_reduced(self, adapter):                        # TC-17
        fbs = _make_feedbacks([1.0] * 6)
        batch = adapter.convert(fbs)
        assert all(s.weight == 0.85 for s in batch.samples)

    def test_mid_weight_normal(self, adapter):                             # TC-18
        fbs = _make_feedbacks([3.0] * 6)
        batch = adapter.convert(fbs)
        assert all(s.weight == 1.0 for s in batch.samples)

    def test_meta_has_hashed_id(self, adapter):                            # TC-19
        fbs = _make_feedbacks([4.0] * 6)
        batch = adapter.convert(fbs)
        for s in batch.samples:
            assert "hashed_reader_id" in s.meta


# ── TC-20~25: 배치 검증 ───────────────────────────────────────────────────

class TestBatchValidation:
    def test_batch_is_valid(self, adapter, collector):                     # TC-20
        fbs = collector.get_feedback()
        batch = adapter.convert(fbs)
        assert batch.is_valid is True

    def test_too_few_after_filter_raises(self):                            # TC-21
        strict = FeedbackToRLHFAdapter(OutlierPolicy(z_threshold=0.1, min_samples_after_filter=5))
        fbs = _make_feedbacks([4.0, 3.0, 5.0, 2.0, 1.0])
        with pytest.raises(ValueError, match="Insufficient samples"):
            strict.convert(fbs)

    def test_convert_by_type(self, adapter, collector):                    # TC-22
        fbs = collector.get_feedback()
        for fb in fbs:
            fb.feedback_type = FeedbackType.EMOTIONAL_IMPACT
        batch = adapter.convert_by_type(fbs, FeedbackType.EMOTIONAL_IMPACT)
        assert batch.size > 0

    def test_batch_id_increments(self, adapter, collector):                # TC-23
        fbs = collector.get_feedback()
        b1 = adapter.convert(fbs)
        b2 = adapter.convert(fbs)
        assert b1.batch_id != b2.batch_id

    def test_batch_z_threshold_stored(self, adapter, collector):           # TC-24
        fbs = collector.get_feedback()
        batch = adapter.convert(fbs)
        assert batch.z_threshold == 2.0

    def test_empty_input_raises(self, adapter):                            # TC-25
        with pytest.raises(ValueError):
            adapter.convert([])


# ── TC-26~33: 통계 ────────────────────────────────────────────────────────

class TestStats:
    def test_stats_total_input(self, adapter, collector):                  # TC-26
        fbs = collector.get_feedback()
        n = len(fbs)
        adapter.convert(fbs)
        assert adapter.stats.total_input >= n

    def test_stats_total_output(self, adapter, collector):                 # TC-27
        fbs = collector.get_feedback()
        adapter.convert(fbs)
        assert adapter.stats.total_output > 0

    def test_stats_batches_created(self, adapter, collector):              # TC-28
        fbs = collector.get_feedback()
        adapter.convert(fbs)
        adapter.convert(fbs)
        assert adapter.stats.batches_created == 2

    def test_outlier_rate(self, adapter):                                  # TC-29
        scores = [4.0, 4.0, 4.0, 4.0, 4.0, 1.0]
        fbs = _make_feedbacks(scores)
        adapter.convert(fbs)
        assert 0.0 <= adapter.stats.outlier_rate <= 1.0

    def test_pass_rate(self, adapter, collector):                          # TC-30
        fbs = collector.get_feedback()
        adapter.convert(fbs)
        assert 0.0 < adapter.stats.pass_rate <= 1.0

    def test_reset_stats(self, adapter, collector):                        # TC-31
        fbs = collector.get_feedback()
        adapter.convert(fbs)
        adapter.reset_stats()
        assert adapter.stats.total_input == 0
        assert adapter.stats.batches_created == 0

    def test_outlier_policy_attrs(self):                                   # TC-32
        policy = OutlierPolicy(z_threshold=1.5, min_samples_after_filter=3)
        assert policy.z_threshold == 1.5
        assert policy.strategy == "remove"

    def test_rlhf_sample_feedback_type(self, adapter, collector):          # TC-33
        fbs = collector.get_feedback()
        batch = adapter.convert(fbs)
        for s in batch.samples:
            assert isinstance(s.feedback_type, FeedbackType)
