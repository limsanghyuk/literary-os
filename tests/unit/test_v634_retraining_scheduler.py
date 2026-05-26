"""
test_v634_retraining_scheduler.py — V634 RetrainingScheduler TC-01~33
SP-C.1 ADR-076: F1 drift 기반 재학습 스케줄러 검증

LLM-0 준수: 외부 LLM 호출 없음
"""
from __future__ import annotations

import json
import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from literary_system.constitution.retraining_scheduler import (
    RetrainingScheduler,
    ScheduleRecord,
    DRIFT_THRESHOLD,
    MIN_INTERVAL_DAYS,
)
from literary_system.constitution import (
    RetrainingScheduler as RSFromInit,
    ScheduleRecord as SRFromInit,
    DRIFT_THRESHOLD as DT_FROM_INIT,
    MIN_INTERVAL_DAYS as MI_FROM_INIT,
)

# ─────────────────────────────────────────────
# 픽스처
# ─────────────────────────────────────────────
@pytest.fixture
def sched():
    """메모리 모드 스케줄러."""
    return RetrainingScheduler(store_path=":memory:")


@pytest.fixture
def t0():
    """기준 시각 — UTC."""
    return datetime(2026, 5, 26, 0, 0, 0, tzinfo=timezone.utc)


# ─────────────────────────────────────────────
# TC-01~05: 기본 상수 및 초기 상태
# ─────────────────────────────────────────────
class TestConstants:
    def test_tc01_drift_threshold_default(self):
        """TC-01: DRIFT_THRESHOLD 기본값 0.03."""
        assert DRIFT_THRESHOLD == pytest.approx(0.03)

    def test_tc02_min_interval_days_default(self):
        """TC-02: MIN_INTERVAL_DAYS 기본값 7."""
        assert MIN_INTERVAL_DAYS == 7

    def test_tc03_initial_count_zero(self, sched):
        """TC-03: 초기 이력 0건."""
        assert sched.count() == 0

    def test_tc04_initial_history_empty(self, sched):
        """TC-04: 초기 history() 빈 리스트."""
        assert sched.history() == []

    def test_tc05_initial_last_scheduled_none(self, sched):
        """TC-05: 초기 last_scheduled() None."""
        assert sched.last_scheduled() is None


# ─────────────────────────────────────────────
# TC-06~10: should_retrain 판단 로직
# ─────────────────────────────────────────────
class TestShouldRetrain:
    def test_tc06_no_drift_returns_false(self, sched, t0):
        """TC-06: drift < threshold → False."""
        ok, reason = sched.should_retrain(0.80, 0.80, now=t0)
        assert ok is False
        assert "재학습 불필요" in reason

    def test_tc07_small_drift_below_threshold(self, sched, t0):
        """TC-07: drift = 0.029 < 0.03 → False."""
        ok, _ = sched.should_retrain(0.771, 0.800, now=t0)
        assert ok is False

    def test_tc08_drift_exactly_threshold_returns_true(self, sched, t0):
        """TC-08: |drift| = threshold → True (>= 조건으로 재학습 트리거)."""
        ok, _ = sched.should_retrain(0.770, 0.800, now=t0)
        assert ok is True

    def test_tc09_drift_above_threshold_no_history(self, sched, t0):
        """TC-09: |drift| > threshold, 이전 기록 없음 → True."""
        ok, reason = sched.should_retrain(0.760, 0.800, now=t0)
        assert ok is True
        assert "재학습 필요" in reason

    def test_tc10_positive_drift_above_threshold(self, sched, t0):
        """TC-10: F1 상승 drift > threshold → True."""
        ok, reason = sched.should_retrain(0.860, 0.800, now=t0)
        assert ok is True
        assert "상승" in reason


# ─────────────────────────────────────────────
# TC-11~15: MIN_INTERVAL 검사
# ─────────────────────────────────────────────
class TestMinInterval:
    def test_tc11_interval_not_met_returns_false(self, sched, t0):
        """TC-11: 마지막 스케줄 3일 전 → interval 미충족 → False."""
        sched.schedule(0.760, 0.800, now=t0)
        later = t0 + timedelta(days=3)
        ok, reason = sched.should_retrain(0.750, 0.800, now=later)
        assert ok is False
        assert "최소 간격 미충족" in reason

    def test_tc12_interval_exactly_7_days_allowed(self, sched, t0):
        """TC-12: 정확히 7일 후 → True (timedelta 7일 = 충족)."""
        sched.schedule(0.760, 0.800, now=t0)
        later = t0 + timedelta(days=7)
        ok, _ = sched.should_retrain(0.750, 0.800, now=later)
        assert ok is True

    def test_tc13_interval_6days_23h_blocked(self, sched, t0):
        """TC-13: 6일 23시간 → 아직 미충족 → False."""
        sched.schedule(0.760, 0.800, now=t0)
        later = t0 + timedelta(days=6, hours=23)
        ok, _ = sched.should_retrain(0.750, 0.800, now=later)
        assert ok is False

    def test_tc14_min_interval_zero_always_allowed(self, t0):
        """TC-14: min_interval_days=0 이면 즉시 재스케줄 가능."""
        s = RetrainingScheduler(store_path=":memory:", min_interval_days=0)
        s.schedule(0.760, 0.800, now=t0)
        ok, _ = s.should_retrain(0.750, 0.800, now=t0)
        assert ok is True

    def test_tc15_remaining_days_in_reason(self, sched, t0):
        """TC-15: 거부 사유에 잔여 일수 정보 포함."""
        sched.schedule(0.760, 0.800, now=t0)
        later = t0 + timedelta(days=2)
        ok, reason = sched.should_retrain(0.750, 0.800, now=later)
        assert ok is False
        assert "잔여" in reason


# ─────────────────────────────────────────────
# TC-16~20: schedule() 메서드
# ─────────────────────────────────────────────
class TestSchedule:
    def test_tc16_schedule_returns_record(self, sched, t0):
        """TC-16: schedule() → ScheduleRecord 반환."""
        rec = sched.schedule(0.760, 0.800, now=t0)
        assert isinstance(rec, ScheduleRecord)

    def test_tc17_record_fields_correct(self, sched, t0):
        """TC-17: 레코드 필드 값 정확성."""
        rec = sched.schedule(0.760, 0.800, note="test", now=t0)
        assert rec.current_f1 == pytest.approx(0.760)
        assert rec.baseline_f1 == pytest.approx(0.800)
        assert rec.drift == pytest.approx(-0.040)
        assert rec.note == "test"
        assert rec.record_id  # UUID4 non-empty

    def test_tc18_schedule_raises_if_no_retrain_needed(self, sched, t0):
        """TC-18: should_retrain False이면 RuntimeError."""
        with pytest.raises(RuntimeError, match="재학습 스케줄 거부"):
            sched.schedule(0.800, 0.800, now=t0)

    def test_tc19_force_bypasses_all_checks(self, sched, t0):
        """TC-19: force=True 이면 drift/interval 무관 스케줄 등록."""
        sched.schedule(0.760, 0.800, now=t0)
        later = t0 + timedelta(days=1)
        rec = sched.schedule(0.799, 0.800, force=True, now=later)
        assert rec is not None
        assert sched.count() == 2

    def test_tc20_count_increments(self, sched, t0):
        """TC-20: 스케줄 후 count 증가."""
        assert sched.count() == 0
        sched.schedule(0.760, 0.800, now=t0)
        assert sched.count() == 1
        sched.schedule(0.740, 0.800, now=t0 + timedelta(days=7))
        assert sched.count() == 2


# ─────────────────────────────────────────────
# TC-21~24: history / last_scheduled
# ─────────────────────────────────────────────
class TestHistory:
    def test_tc21_history_order(self, sched, t0):
        """TC-21: history() 오래된 순."""
        sched.schedule(0.760, 0.800, now=t0)
        sched.schedule(0.740, 0.800, now=t0 + timedelta(days=7))
        h = sched.history()
        assert h[0].current_f1 == pytest.approx(0.760)
        assert h[1].current_f1 == pytest.approx(0.740)

    def test_tc22_last_scheduled_most_recent(self, sched, t0):
        """TC-22: last_scheduled() 가장 최근 레코드."""
        sched.schedule(0.760, 0.800, now=t0)
        sched.schedule(0.740, 0.800, now=t0 + timedelta(days=7))
        assert sched.last_scheduled().current_f1 == pytest.approx(0.740)

    def test_tc23_history_returns_copy(self, sched, t0):
        """TC-23: history() 반환값 수정이 내부 상태에 영향 없음."""
        sched.schedule(0.760, 0.800, now=t0)
        h = sched.history()
        h.clear()
        assert sched.count() == 1

    def test_tc24_record_id_unique(self, sched, t0):
        """TC-24: 각 레코드의 record_id가 고유."""
        sched.schedule(0.760, 0.800, now=t0)
        sched.schedule(0.750, 0.800, now=t0 + timedelta(days=7))
        ids = [r.record_id for r in sched.history()]
        assert len(set(ids)) == 2


# ─────────────────────────────────────────────
# TC-25~28: 파일 모드 영속화
# ─────────────────────────────────────────────
class TestFilePersistence:
    def test_tc25_file_created_on_schedule(self, tmp_path, t0):
        """TC-25: schedule() 후 JSONL 파일 생성됨."""
        p = tmp_path / "sub" / "sched.jsonl"
        s = RetrainingScheduler(store_path=str(p))
        s.schedule(0.760, 0.800, now=t0)
        assert p.exists()

    def test_tc26_jsonl_format(self, tmp_path, t0):
        """TC-26: JSONL 파일 각 줄이 유효한 JSON."""
        p = tmp_path / "sched.jsonl"
        s = RetrainingScheduler(store_path=str(p))
        s.schedule(0.760, 0.800, note="v1", now=t0)
        s.schedule(0.740, 0.800, note="v2", now=t0 + timedelta(days=7))
        lines = p.read_text().strip().splitlines()
        assert len(lines) == 2
        for line in lines:
            obj = json.loads(line)
            assert "record_id" in obj
            assert "drift" in obj

    def test_tc27_reload_from_file(self, tmp_path, t0):
        """TC-27: 파일 모드 재로드 시 이력 복원."""
        p = tmp_path / "sched.jsonl"
        s1 = RetrainingScheduler(store_path=str(p))
        s1.schedule(0.760, 0.800, now=t0)
        s1.schedule(0.740, 0.800, now=t0 + timedelta(days=7))

        s2 = RetrainingScheduler(store_path=str(p))
        assert s2.count() == 2
        assert s2.last_scheduled().current_f1 == pytest.approx(0.740)

    def test_tc28_clear_removes_file(self, tmp_path, t0):
        """TC-28: clear() 후 파일 삭제됨."""
        p = tmp_path / "sched.jsonl"
        s = RetrainingScheduler(store_path=str(p))
        s.schedule(0.760, 0.800, now=t0)
        s.clear()
        assert s.count() == 0
        assert not p.exists()


# ─────────────────────────────────────────────
# TC-29~30: 파라미터 검증
# ─────────────────────────────────────────────
class TestParameterValidation:
    def test_tc29_invalid_drift_threshold_zero(self):
        """TC-29: drift_threshold=0 → ValueError."""
        with pytest.raises(ValueError):
            RetrainingScheduler(store_path=":memory:", drift_threshold=0.0)

    def test_tc30_invalid_drift_threshold_over_one(self):
        """TC-30: drift_threshold=1.5 → ValueError."""
        with pytest.raises(ValueError):
            RetrainingScheduler(store_path=":memory:", drift_threshold=1.5)

    def test_tc30b_invalid_min_interval_negative(self):
        """TC-30b: min_interval_days=-1 → ValueError."""
        with pytest.raises(ValueError):
            RetrainingScheduler(store_path=":memory:", min_interval_days=-1)


# ─────────────────────────────────────────────
# TC-31~33: 공개 API + 직렬화 + 통합
# ─────────────────────────────────────────────
class TestPublicApiAndIntegration:
    def test_tc31_public_api_imports(self):
        """TC-31: constitution/__init__.py 에서 직접 임포트 가능."""
        assert RSFromInit is RetrainingScheduler
        assert SRFromInit is ScheduleRecord
        assert DT_FROM_INIT == pytest.approx(0.03)
        assert MI_FROM_INIT == 7

    def test_tc32_to_dict_from_dict_roundtrip(self, sched, t0):
        """TC-32: ScheduleRecord to_dict/from_dict 라운드트립."""
        rec = sched.schedule(0.760, 0.800, note="rt", now=t0)
        d = rec.to_dict()
        restored = ScheduleRecord.from_dict(d)
        assert restored.record_id == rec.record_id
        assert restored.current_f1 == pytest.approx(rec.current_f1)
        assert restored.drift == pytest.approx(rec.drift)
        assert restored.note == rec.note

    def test_tc33_full_integration_scenario(self, t0):
        """TC-33: 전체 시나리오 — 2사이클 재학습."""
        s = RetrainingScheduler(store_path=":memory:", drift_threshold=0.03,
                                min_interval_days=7)

        # 1차: F1 하락 → 재학습
        ok1, _ = s.should_retrain(0.750, 0.800, now=t0)
        assert ok1 is True
        r1 = s.schedule(0.750, 0.800, note="1차", now=t0)
        assert r1.drift == pytest.approx(-0.05)

        # interval 미충족 → 거부
        ok_mid, reason_mid = s.should_retrain(0.740, 0.800, now=t0 + timedelta(days=3))
        assert ok_mid is False
        assert "최소 간격 미충족" in reason_mid

        # 7일 후 → 2차 재학습
        t1 = t0 + timedelta(days=7)
        ok2, _ = s.should_retrain(0.740, 0.800, now=t1)
        assert ok2 is True
        r2 = s.schedule(0.740, 0.800, note="2차", now=t1)

        assert s.count() == 2
        assert s.last_scheduled().note == "2차"
        h = s.history()
        assert h[0].note == "1차"
        assert h[1].note == "2차"
