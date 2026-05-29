"""
test_v640_feedback_integrator.py
V640 FeedbackIntegrator 단위 테스트 — TC-01~33 (33/33)

ADR-082: SP-C.1 인간 피드백 통합기
"""
from pathlib import Path

import pytest

from literary_system.constitution.feedback_integrator import (
    CORRECTION_WEIGHT,
    FEEDBACK_TYPES,
    MIN_FEEDBACK_FOR_SIGNAL,
    REJECTION_PENALTY,
    FeedbackIntegrator,
    FeedbackRecord,
    IntegrationResult,
)

SCENE_IDS = ["scene-001", "scene-002", "scene-003"]


def make_fi(**kwargs) -> FeedbackIntegrator:
    return FeedbackIntegrator(**kwargs)


# ─────────────────────────────────────────────
# TC-01~05: 상수 및 초기 상태
# ─────────────────────────────────────────────
class TestConstants:
    def test_tc01_feedback_types(self):
        """TC-01: FEEDBACK_TYPES 4종 정의"""
        assert len(FEEDBACK_TYPES) == 4
        assert "SCORE_CORRECTION" in FEEDBACK_TYPES
        assert "LABEL_REVISION" in FEEDBACK_TYPES
        assert "STYLE_ANNOTATION" in FEEDBACK_TYPES
        assert "REJECTION" in FEEDBACK_TYPES

    def test_tc02_min_feedback_signal(self):
        """TC-02: MIN_FEEDBACK_FOR_SIGNAL = 3"""
        assert MIN_FEEDBACK_FOR_SIGNAL == 3

    def test_tc03_correction_weight(self):
        """TC-03: CORRECTION_WEIGHT = 0.8"""
        assert CORRECTION_WEIGHT == 0.8

    def test_tc04_rejection_penalty(self):
        """TC-04: REJECTION_PENALTY = 0.5"""
        assert REJECTION_PENALTY == 0.5

    def test_tc05_initial_state(self):
        """TC-05: 초기 상태 — count=0, feedbacks=[], last_result=None"""
        fi = make_fi()
        assert fi.count() == 0
        assert fi.feedbacks() == []
        assert fi.last_result() is None
        assert fi.integration_history() == []


# ─────────────────────────────────────────────
# TC-06~10: record_feedback() 기본 동작
# ─────────────────────────────────────────────
class TestRecordFeedback:
    def test_tc06_returns_feedback_record(self):
        """TC-06: record_feedback()는 FeedbackRecord 반환"""
        fi = make_fi()
        r = fi.record_feedback("scene-1", "SCORE_CORRECTION", "h1", 0.6, 0.8)
        assert isinstance(r, FeedbackRecord)
        assert r.record_id
        assert r.created_at

    def test_tc07_count_increments(self):
        """TC-07: 피드백 수집 후 count=1"""
        fi = make_fi()
        fi.record_feedback("scene-1", "SCORE_CORRECTION")
        assert fi.count() == 1

    def test_tc08_delta_calculated(self):
        """TC-08: correction_delta() = corrected - original"""
        fi = make_fi()
        r = fi.record_feedback("scene-1", "SCORE_CORRECTION",
                               original_score=0.60, corrected_score=0.85)
        assert abs(r.correction_delta() - 0.25) < 1e-9

    def test_tc09_negative_delta(self):
        """TC-09: 하향 보정 — delta 음수"""
        fi = make_fi()
        r = fi.record_feedback("scene-1", "SCORE_CORRECTION",
                               original_score=0.90, corrected_score=0.60)
        assert r.correction_delta() < 0

    def test_tc10_all_fields_stored(self):
        """TC-10: 모든 필드 저장"""
        fi = make_fi()
        r = fi.record_feedback(
            scene_id="scene-x", feedback_type="LABEL_REVISION",
            evaluator_id="h-1", original_score=0.5, corrected_score=0.7,
            label_before="NEGATIVE", label_after="POSITIVE",
            annotation="오해의 소지", note="재검토 필요"
        )
        assert r.scene_id == "scene-x"
        assert r.feedback_type == "LABEL_REVISION"
        assert r.evaluator_id == "h-1"
        assert r.label_before == "NEGATIVE"
        assert r.label_after == "POSITIVE"
        assert r.annotation == "오해의 소지"
        assert r.note == "재검토 필요"


# ─────────────────────────────────────────────
# TC-11~17: integrate() 집계 동작
# ─────────────────────────────────────────────
class TestIntegrate:
    def test_tc11_no_signal_below_min(self):
        """TC-11: 피드백 수 < MIN_FEEDBACK_FOR_SIGNAL → has_signal=False"""
        fi = make_fi()
        fi.record_feedback("s1", "SCORE_CORRECTION", original_score=0.6, corrected_score=0.8)
        fi.record_feedback("s2", "SCORE_CORRECTION", original_score=0.5, corrected_score=0.7)
        result = fi.integrate()
        assert not result.has_signal
        assert result.signal_strength == 0.0

    def test_tc12_signal_at_min_threshold(self):
        """TC-12: 피드백 수 = MIN_FEEDBACK_FOR_SIGNAL → has_signal=True"""
        fi = make_fi()
        for i in range(MIN_FEEDBACK_FOR_SIGNAL):
            fi.record_feedback(f"s{i}", "SCORE_CORRECTION",
                               original_score=0.5, corrected_score=0.8)
        result = fi.integrate()
        assert result.has_signal

    def test_tc13_avg_correction_delta(self):
        """TC-13: avg_correction_delta = 평균 보정 델타"""
        fi = make_fi()
        fi.record_feedback("s1", "SCORE_CORRECTION", original_score=0.5, corrected_score=0.7)
        fi.record_feedback("s2", "SCORE_CORRECTION", original_score=0.6, corrected_score=0.8)
        fi.record_feedback("s3", "SCORE_CORRECTION", original_score=0.7, corrected_score=0.9)
        result = fi.integrate()
        # 델타: 0.2, 0.2, 0.2 → 평균 0.2
        assert abs(result.avg_correction_delta - 0.2) < 1e-9

    def test_tc14_rejection_rate(self):
        """TC-14: rejection_rate = 거부 수 / 전체 피드백 수"""
        fi = make_fi()
        fi.record_feedback("s1", "REJECTION")
        fi.record_feedback("s2", "SCORE_CORRECTION", original_score=0.5, corrected_score=0.8)
        fi.record_feedback("s3", "SCORE_CORRECTION", original_score=0.6, corrected_score=0.8)
        result = fi.integrate()
        assert abs(result.rejection_rate - 1/3) < 1e-9

    def test_tc15_label_revision_rate(self):
        """TC-15: label_revision_rate = 레이블 수정 수 / 전체"""
        fi = make_fi()
        fi.record_feedback("s1", "LABEL_REVISION")
        fi.record_feedback("s2", "LABEL_REVISION")
        fi.record_feedback("s3", "SCORE_CORRECTION", original_score=0.5, corrected_score=0.8)
        result = fi.integrate()
        assert abs(result.label_revision_rate - 2/3) < 1e-9

    def test_tc16_scene_filter(self):
        """TC-16: scene_ids 필터 — 지정 장면만 집계"""
        fi = make_fi()
        fi.record_feedback("scene-A", "SCORE_CORRECTION", original_score=0.5, corrected_score=0.9)
        fi.record_feedback("scene-A", "SCORE_CORRECTION", original_score=0.5, corrected_score=0.9)
        fi.record_feedback("scene-A", "SCORE_CORRECTION", original_score=0.5, corrected_score=0.9)
        fi.record_feedback("scene-B", "REJECTION")
        result = fi.integrate(scene_ids=["scene-A"])
        assert result.feedback_count == 3
        assert result.rejection_rate == 0.0

    def test_tc17_integrate_result_stored(self):
        """TC-17: integrate() 결과는 integration_history()에 저장"""
        fi = make_fi()
        fi.record_feedback("s1", "SCORE_CORRECTION", original_score=0.5, corrected_score=0.8)
        result = fi.integrate()
        assert result in fi.integration_history()
        assert fi.last_result() == result


# ─────────────────────────────────────────────
# TC-18~22: IntegrationResult 필드 검증
# ─────────────────────────────────────────────
class TestIntegrationResult:
    def test_tc18_summary_signal(self):
        """TC-18: summary() — SIGNAL 포함"""
        fi = make_fi()
        for i in range(3):
            fi.record_feedback(f"s{i}", "SCORE_CORRECTION",
                               original_score=0.5, corrected_score=0.8)
        result = fi.integrate()
        assert "SIGNAL" in result.summary()

    def test_tc19_summary_no_signal(self):
        """TC-19: summary() — NO_SIGNAL 포함"""
        fi = make_fi()
        fi.record_feedback("s1", "SCORE_CORRECTION", original_score=0.5, corrected_score=0.8)
        result = fi.integrate()
        assert "NO_SIGNAL" in result.summary()

    def test_tc20_signal_strength_bounded(self):
        """TC-20: signal_strength는 0.0~1.0"""
        fi = make_fi()
        for i in range(10):
            fi.record_feedback(f"s{i}", "REJECTION")
        result = fi.integrate()
        assert 0.0 <= result.signal_strength <= 1.0

    def test_tc21_to_dict_from_dict(self):
        """TC-21: IntegrationResult to_dict/from_dict 왕복"""
        fi = make_fi()
        for i in range(3):
            fi.record_feedback(f"s{i}", "SCORE_CORRECTION",
                               original_score=0.5, corrected_score=0.8)
        r = fi.integrate(note="test", now="2026-05-26T00:00:00+00:00")
        r2 = IntegrationResult.from_dict(r.to_dict())
        assert r2.result_id == r.result_id
        assert r2.has_signal == r.has_signal
        assert abs(r2.avg_correction_delta - r.avg_correction_delta) < 1e-9

    def test_tc22_feedback_count_in_result(self):
        """TC-22: result.feedback_count = 집계된 피드백 수"""
        fi = make_fi()
        for i in range(5):
            fi.record_feedback(f"s{i}", "STYLE_ANNOTATION")
        result = fi.integrate()
        assert result.feedback_count == 5


# ─────────────────────────────────────────────
# TC-23~27: 조회 API
# ─────────────────────────────────────────────
class TestQueryAPI:
    def test_tc23_feedbacks_by_scene(self):
        """TC-23: feedbacks_by_scene() — 특정 장면 필터"""
        fi = make_fi()
        fi.record_feedback("scene-A", "SCORE_CORRECTION")
        fi.record_feedback("scene-B", "LABEL_REVISION")
        fi.record_feedback("scene-A", "REJECTION")
        assert len(fi.feedbacks_by_scene("scene-A")) == 2
        assert len(fi.feedbacks_by_scene("scene-B")) == 1

    def test_tc24_feedbacks_by_type(self):
        """TC-24: feedbacks_by_type() — 유형 필터"""
        fi = make_fi()
        fi.record_feedback("s1", "SCORE_CORRECTION")
        fi.record_feedback("s2", "REJECTION")
        fi.record_feedback("s3", "SCORE_CORRECTION")
        assert len(fi.feedbacks_by_type("SCORE_CORRECTION")) == 2

    def test_tc25_feedbacks_by_evaluator(self):
        """TC-25: feedbacks_by_evaluator() — 검증자 필터"""
        fi = make_fi()
        fi.record_feedback("s1", "SCORE_CORRECTION", evaluator_id="h-1")
        fi.record_feedback("s2", "SCORE_CORRECTION", evaluator_id="h-2")
        fi.record_feedback("s3", "REJECTION", evaluator_id="h-1")
        assert len(fi.feedbacks_by_evaluator("h-1")) == 2

    def test_tc26_batch_record(self):
        """TC-26: batch_record() — 배치 수집"""
        fi = make_fi()
        items = [
            {"scene_id": "s1", "feedback_type": "SCORE_CORRECTION",
             "original_score": 0.5, "corrected_score": 0.8},
            {"scene_id": "s2", "feedback_type": "REJECTION"},
            {"scene_id": "s3", "feedback_type": "LABEL_REVISION",
             "label_before": "A", "label_after": "B"},
        ]
        records = fi.batch_record(items, evaluator_id="h-batch")
        assert len(records) == 3
        assert fi.count() == 3

    def test_tc27_multiple_integrate_history(self):
        """TC-27: integration_history() — 여러 집계 이력 보존"""
        fi = make_fi()
        for i in range(3):
            fi.record_feedback(f"s{i}", "SCORE_CORRECTION",
                               original_score=0.5, corrected_score=0.8)
        fi.integrate(note="1차")
        fi.integrate(note="2차")
        assert len(fi.integration_history()) == 2


# ─────────────────────────────────────────────
# TC-28~30: JSONL 영속화
# ─────────────────────────────────────────────
class TestFilePersistence:
    def test_tc28_file_created(self, tmp_path):
        """TC-28: 피드백 수집 후 JSONL 파일 생성"""
        store = str(tmp_path / "fi.jsonl")
        fi = FeedbackIntegrator(store_path=store)
        fi.record_feedback("s1", "SCORE_CORRECTION", original_score=0.5, corrected_score=0.8)
        assert Path(store).exists()

    def test_tc29_reload_from_disk(self, tmp_path):
        """TC-29: 디스크 재로드 — 피드백 복원"""
        store = str(tmp_path / "fi.jsonl")
        fi1 = FeedbackIntegrator(store_path=store)
        r = fi1.record_feedback("s1", "SCORE_CORRECTION",
                                original_score=0.5, corrected_score=0.8)
        fi2 = FeedbackIntegrator(store_path=store)
        assert fi2.count() == 1
        assert fi2.feedbacks()[0].record_id == r.record_id

    def test_tc30_clear(self, tmp_path):
        """TC-30: clear() — 메모리 및 파일 초기화"""
        store = str(tmp_path / "fi.jsonl")
        fi = FeedbackIntegrator(store_path=store)
        fi.record_feedback("s1", "SCORE_CORRECTION")
        fi.clear()
        assert fi.count() == 0
        assert Path(store).read_text().strip() == ""


# ─────────────────────────────────────────────
# TC-31~33: 통합 시나리오
# ─────────────────────────────────────────────
class TestIntegration:
    def test_tc31_full_feedback_cycle(self):
        """TC-31: 전체 피드백 사이클 — 4종 유형 모두 사용"""
        fi = make_fi()
        fi.record_feedback("s1", "SCORE_CORRECTION", "h1", 0.5, 0.8)
        fi.record_feedback("s2", "LABEL_REVISION", "h1",
                           label_before="NEG", label_after="POS")
        fi.record_feedback("s3", "STYLE_ANNOTATION", "h2",
                           annotation="드라마 톤 강화")
        fi.record_feedback("s4", "REJECTION", "h2")
        result = fi.integrate()
        assert result.has_signal
        assert result.feedback_count == 4
        assert result.rejection_rate == 0.25
        assert result.label_revision_rate == 0.25

    def test_tc32_empty_feedback_integrate(self):
        """TC-32: 피드백 없이 integrate() — 신호 없음"""
        fi = make_fi()
        result = fi.integrate()
        assert not result.has_signal
        assert result.feedback_count == 0
        assert result.signal_strength == 0.0

    def test_tc33_feedbackrecord_roundtrip(self):
        """TC-33: FeedbackRecord to_dict/from_dict 왕복"""
        fi = make_fi()
        r = fi.record_feedback(
            "scene-final", "SCORE_CORRECTION", "h-final",
            0.55, 0.88, note="roundtrip",
            now="2026-05-26T00:00:00+00:00"
        )
        r2 = FeedbackRecord.from_dict(r.to_dict())
        assert r2.record_id == r.record_id
        assert r2.scene_id == "scene-final"
        assert abs(r2.corrected_score - 0.88) < 1e-9
        assert abs(r2.correction_delta() - 0.33) < 1e-9
