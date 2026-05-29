"""
V632 — test_v632_constitution_weight_tracker.py
ConstitutionWeightTracker 단위 테스트 TC-01 ~ TC-33

ADR-099 / SP-C.1 검증 범위
- TC-01~05: 기본 save / load_latest
- TC-06~10: 이력(history) 조회
- TC-07~12: 비파괴 롤백
- TC-13~16: 파일 모드 영속화
- TC-17~20: 엔트로피 자동 기록
- TC-21~24: 예외 처리
- TC-25~28: count / latest_record / clear
- TC-29~33: constitution/__init__.py 공개 API 및 통합 시나리오
"""
from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path

import pytest

from literary_system.constitution import (
    ConstitutionWeightTracker,
    ConstitutionWeights,
    WeightRecord,
)
from literary_system.constitution.constitution_weight_tracker import (
    _shannon_entropy,
)


# ---------------------------------------------------------------------------
# 픽스처
# ---------------------------------------------------------------------------

@pytest.fixture
def tracker():
    """메모리 모드 트래커."""
    return ConstitutionWeightTracker(":memory:")


@pytest.fixture
def w_default():
    return ConstitutionWeights(drse=0.30, debt=0.20, arc=0.20, tension=0.15, prose=0.15)


@pytest.fixture
def w_alt():
    return ConstitutionWeights(drse=0.25, debt=0.25, arc=0.20, tension=0.15, prose=0.15)


@pytest.fixture
def w_extreme():
    """한쪽 극단 — 엔트로피가 낮음."""
    return ConstitutionWeights(drse=0.97, debt=0.01, arc=0.01, tension=0.005, prose=0.005)


# ---------------------------------------------------------------------------
# TC-01~05: save / load_latest 기본
# ---------------------------------------------------------------------------

def test_tc01_save_returns_version_id(tracker, w_default):
    vid = tracker.save(w_default)
    assert isinstance(vid, str) and len(vid) == 36  # UUID4


def test_tc02_load_latest_returns_last_saved(tracker, w_default, w_alt):
    tracker.save(w_default)
    tracker.save(w_alt)
    latest = tracker.load_latest()
    assert latest.drse == pytest.approx(0.25)


def test_tc03_save_with_note(tracker, w_default):
    vid = tracker.save(w_default, note="initial")
    rec = tracker.history()[0]
    assert rec.note == "initial"


def test_tc04_save_preserves_weights(tracker, w_alt):
    tracker.save(w_alt)
    latest = tracker.load_latest()
    assert latest.drse == pytest.approx(0.25)
    assert latest.debt == pytest.approx(0.25)
    assert latest.arc == pytest.approx(0.20)
    assert latest.tension == pytest.approx(0.15)
    assert latest.prose == pytest.approx(0.15)


def test_tc05_multiple_saves_distinct_version_ids(tracker, w_default, w_alt):
    v1 = tracker.save(w_default)
    v2 = tracker.save(w_alt)
    assert v1 != v2


# ---------------------------------------------------------------------------
# TC-06~10: history 조회
# ---------------------------------------------------------------------------

def test_tc06_history_empty_initially(tracker):
    assert tracker.history() == []


def test_tc07_history_order_chronological(tracker, w_default, w_alt):
    tracker.save(w_default)
    tracker.save(w_alt)
    h = tracker.history()
    assert len(h) == 2
    assert h[0].weights.drse == pytest.approx(0.30)
    assert h[1].weights.drse == pytest.approx(0.25)


def test_tc08_history_returns_copy(tracker, w_default):
    tracker.save(w_default)
    h = tracker.history()
    h.clear()
    assert tracker.count() == 1  # 원본 영향 없음


def test_tc09_history_contains_weight_records(tracker, w_default):
    tracker.save(w_default)
    h = tracker.history()
    assert isinstance(h[0], WeightRecord)


def test_tc10_history_timestamps_present(tracker, w_default):
    tracker.save(w_default)
    rec = tracker.history()[0]
    # ISO-8601 타임스탬프 — 'T' 포함 여부 확인
    assert "T" in rec.timestamp


# ---------------------------------------------------------------------------
# TC-11~16: rollback
# ---------------------------------------------------------------------------

def test_tc11_rollback_restores_weights(tracker, w_default, w_alt):
    v1 = tracker.save(w_default, note="initial")
    tracker.save(w_alt, note="optimised")
    tracker.rollback(v1)
    assert tracker.load_latest().drse == pytest.approx(0.30)


def test_tc12_rollback_non_destructive(tracker, w_default, w_alt):
    v1 = tracker.save(w_default)
    tracker.save(w_alt)
    tracker.rollback(v1)
    # 롤백 후 이력은 3건 (initial, alt, rollback)
    assert tracker.count() == 3


def test_tc13_rollback_note_contains_version_id(tracker, w_default, w_alt):
    v1 = tracker.save(w_default)
    tracker.save(w_alt)
    tracker.rollback(v1)
    rec = tracker.history()[-1]
    assert "rollback:" in rec.note
    assert v1 in rec.note


def test_tc14_rollback_unknown_version_raises_key_error(tracker, w_default):
    tracker.save(w_default)
    with pytest.raises(KeyError):
        tracker.rollback("00000000-0000-0000-0000-000000000000")


def test_tc15_double_rollback(tracker, w_default, w_alt):
    v1 = tracker.save(w_default)
    v2 = tracker.save(w_alt)
    tracker.rollback(v1)
    tracker.rollback(v2)
    assert tracker.load_latest().drse == pytest.approx(0.25)
    assert tracker.count() == 4


def test_tc16_rollback_then_load_latest_consistent(tracker, w_default, w_alt):
    v1 = tracker.save(w_default)
    tracker.save(w_alt)
    restored = tracker.rollback(v1)
    latest = tracker.load_latest()
    assert latest.drse == restored.drse


# ---------------------------------------------------------------------------
# TC-17~20: 파일 모드 영속화
# ---------------------------------------------------------------------------

def test_tc17_file_mode_persists_across_instances(w_default, w_alt):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "weights.jsonl"
        t1 = ConstitutionWeightTracker(path)
        t1.save(w_default)
        t1.save(w_alt)

        t2 = ConstitutionWeightTracker(path)
        assert t2.count() == 2
        assert t2.load_latest().drse == pytest.approx(0.25)


def test_tc18_file_mode_jsonl_format(w_default):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "weights.jsonl"
        t = ConstitutionWeightTracker(path)
        t.save(w_default, note="file_test")
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 1
        d = json.loads(lines[0])
        assert d["weights"]["drse"] == pytest.approx(0.30)
        assert d["note"] == "file_test"


def test_tc19_file_mode_auto_creates_parent_dir(w_default):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "subdir" / "nested" / "weights.jsonl"
        t = ConstitutionWeightTracker(path)
        t.save(w_default)
        assert path.exists()


def test_tc20_file_mode_rollback_persists(w_default, w_alt):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "weights.jsonl"
        t1 = ConstitutionWeightTracker(path)
        v1 = t1.save(w_default)
        t1.save(w_alt)
        t1.rollback(v1)

        t2 = ConstitutionWeightTracker(path)
        assert t2.count() == 3
        assert t2.load_latest().drse == pytest.approx(0.30)


# ---------------------------------------------------------------------------
# TC-21~24: 엔트로피 자동 기록
# ---------------------------------------------------------------------------

def test_tc21_entropy_recorded_on_save(tracker, w_default):
    tracker.save(w_default)
    rec = tracker.history()[0]
    expected = _shannon_entropy(list(w_default.as_dict().values()))
    assert rec.entropy == pytest.approx(expected, abs=1e-6)


def test_tc22_entropy_positive_nonzero(tracker, w_default):
    tracker.save(w_default)
    assert tracker.history()[0].entropy > 0.0


def test_tc23_extreme_weights_lower_entropy(tracker, w_default, w_extreme):
    tracker.save(w_default)
    tracker.save(w_extreme)
    h = tracker.history()
    assert h[0].entropy > h[1].entropy


def test_tc24_shannon_entropy_helper_known_value():
    # 균등 분포 (5축) → H = log2(5) ≈ 2.322
    uniform = [0.2, 0.2, 0.2, 0.2, 0.2]
    h = _shannon_entropy(uniform)
    assert h == pytest.approx(math.log2(5), abs=1e-4)


# ---------------------------------------------------------------------------
# TC-25~28: count / latest_record / clear
# ---------------------------------------------------------------------------

def test_tc25_count_zero_initially(tracker):
    assert tracker.count() == 0


def test_tc26_count_increments_on_save(tracker, w_default, w_alt):
    tracker.save(w_default)
    tracker.save(w_alt)
    assert tracker.count() == 2


def test_tc27_latest_record_none_when_empty(tracker):
    assert tracker.latest_record() is None


def test_tc28_clear_resets_tracker(tracker, w_default):
    tracker.save(w_default)
    tracker.clear()
    assert tracker.count() == 0
    with pytest.raises(RuntimeError):
        tracker.load_latest()


# ---------------------------------------------------------------------------
# TC-29~33: __init__ 공개 API + 통합 시나리오
# ---------------------------------------------------------------------------

def test_tc29_public_api_constitution_weight_tracker_importable():
    from literary_system.constitution import ConstitutionWeightTracker
    assert ConstitutionWeightTracker is not None


def test_tc30_public_api_weight_record_importable():
    from literary_system.constitution import WeightRecord
    assert WeightRecord is not None


def test_tc31_weight_record_to_dict_roundtrip(w_default):
    rec = WeightRecord(
        version_id="test-uuid",
        timestamp="2026-05-26T00:00:00+00:00",
        weights=w_default,
        entropy=2.21,
        note="roundtrip",
    )
    d = rec.to_dict()
    rec2 = WeightRecord.from_dict(d)
    assert rec2.version_id == rec.version_id
    assert rec2.weights.drse == pytest.approx(rec.weights.drse)
    assert rec2.note == rec.note


def test_tc32_integration_optimise_save_load(tracker):
    """Bayesian 최적화 결과를 저장하고 재로드하는 통합 시나리오."""
    # 최적화 후 가중치 3회 갱신 시나리오
    scenarios = [
        ConstitutionWeights(drse=0.30, debt=0.20, arc=0.20, tension=0.15, prose=0.15),
        ConstitutionWeights(drse=0.28, debt=0.22, arc=0.21, tension=0.15, prose=0.14),
        ConstitutionWeights(drse=0.26, debt=0.24, arc=0.22, tension=0.14, prose=0.14),
    ]
    vids = [tracker.save(w, note=f"cycle_{i}") for i, w in enumerate(scenarios)]
    assert tracker.count() == 3
    assert tracker.load_latest().drse == pytest.approx(0.26)
    # 1번 사이클로 롤백
    tracker.rollback(vids[1])
    assert tracker.load_latest().drse == pytest.approx(0.28)


def test_tc33_load_latest_raises_when_empty(tracker):
    with pytest.raises(RuntimeError, match="저장된 가중치 레코드가 없습니다"):
        tracker.load_latest()
