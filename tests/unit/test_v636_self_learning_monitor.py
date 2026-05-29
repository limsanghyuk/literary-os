"""
test_v636_self_learning_monitor.py — V636 SelfLearningMonitor TC-01~33
SP-C.1 ADR-078: Self-Learning Loop 파이프라인 상태 모니터 검증

LLM-0 준수: 외부 LLM 호출 없음
"""
from __future__ import annotations

import json
import pytest
from datetime import datetime, timezone

from literary_system.constitution.self_learning_monitor import (
    SelfLearningMonitor,
    MonitorSnapshot,
    ComponentStatus,
    ROLLBACK_SURGE_THRESHOLD,
    F1_DROP_THRESHOLD,
    GATE_FAIL_STREAK_THRESHOLD,
    COMPONENT_NAMES,
)
from literary_system.constitution import (
    SelfLearningMonitor as SLMFromInit,
    MonitorSnapshot as MSFromInit,
    ComponentStatus as CSFromInit,
)


# ─────────────────────────────────────────────
# 픽스처
# ─────────────────────────────────────────────
@pytest.fixture
def mon():
    return SelfLearningMonitor(store_path=":memory:")


@pytest.fixture
def t0():
    return datetime(2026, 5, 26, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def healthy_components():
    return [ComponentStatus(name, True) for name in COMPONENT_NAMES]


@pytest.fixture
def degraded_components():
    comps = [ComponentStatus(name, True) for name in COMPONENT_NAMES]
    comps[1] = ComponentStatus("WeightTracker", False, {"error": "LOSDB read fail"})
    return comps


# ─────────────────────────────────────────────
# TC-01~05: 상수 및 초기 상태
# ─────────────────────────────────────────────
class TestConstants:
    def test_tc01_rollback_surge_threshold(self):
        """TC-01: ROLLBACK_SURGE_THRESHOLD 기본값 3."""
        assert ROLLBACK_SURGE_THRESHOLD == 3

    def test_tc02_f1_drop_threshold(self):
        """TC-02: F1_DROP_THRESHOLD 기본값 0.10."""
        assert F1_DROP_THRESHOLD == pytest.approx(0.10)

    def test_tc03_gate_fail_streak_threshold(self):
        """TC-03: GATE_FAIL_STREAK_THRESHOLD 기본값 3."""
        assert GATE_FAIL_STREAK_THRESHOLD == 3

    def test_tc04_component_names_five(self):
        """TC-04: COMPONENT_NAMES 5개."""
        assert len(COMPONENT_NAMES) == 5
        assert "MetaLearner" in COMPONENT_NAMES
        assert "AutoPromotionGate" in COMPONENT_NAMES

    def test_tc05_initial_state(self, mon):
        """TC-05: 초기 상태 — count=0, last_snapshot=None."""
        assert mon.count() == 0
        assert mon.last_snapshot() is None
        assert mon.history() == []


# ─────────────────────────────────────────────
# TC-06~10: ComponentStatus
# ─────────────────────────────────────────────
class TestComponentStatus:
    def test_tc06_healthy_component(self):
        """TC-06: 정상 컴포넌트 생성."""
        cs = ComponentStatus("MetaLearner", True, {"opt_trials": 50})
        assert cs.healthy is True
        assert cs.name == "MetaLearner"

    def test_tc07_unhealthy_component(self):
        """TC-07: 비정상 컴포넌트."""
        cs = ComponentStatus("WeightTracker", False, {"error": "파일 읽기 실패"})
        assert cs.healthy is False

    def test_tc08_component_to_dict_roundtrip(self):
        """TC-08: ComponentStatus to_dict/from_dict 라운드트립."""
        cs = ComponentStatus("PatternLibraryV2", True, {"pattern_count": 42})
        restored = ComponentStatus.from_dict(cs.to_dict())
        assert restored.name == cs.name
        assert restored.healthy == cs.healthy
        assert restored.details == cs.details

    def test_tc09_component_default_checked_at(self):
        """TC-09: checked_at 자동 설정."""
        cs = ComponentStatus("RetrainingScheduler", True)
        assert cs.checked_at  # non-empty

    def test_tc10_component_empty_details_default(self):
        """TC-10: details 기본값 빈 dict."""
        cs = ComponentStatus("AutoPromotionGate", True)
        assert cs.details == {}


# ─────────────────────────────────────────────
# TC-11~15: capture() 정상 케이스
# ─────────────────────────────────────────────
class TestCaptureHealthy:
    def test_tc11_capture_all_healthy(self, mon, healthy_components, t0):
        """TC-11: 전 컴포넌트 정상, 이상 없음 → healthy=True."""
        snap = mon.capture(healthy_components, now=t0)
        assert snap.healthy is True
        assert snap.anomalies == []

    def test_tc12_snapshot_fields(self, mon, healthy_components, t0):
        """TC-12: 스냅샷 필드 값 검증."""
        snap = mon.capture(healthy_components, note="daily", now=t0)
        assert snap.snapshot_id  # UUID4
        assert snap.note == "daily"
        assert len(snap.components) == 5

    def test_tc13_count_increments(self, mon, healthy_components, t0):
        """TC-13: capture() 후 count 증가."""
        mon.capture(healthy_components, now=t0)
        mon.capture(healthy_components, now=t0)
        assert mon.count() == 2

    def test_tc14_summary_healthy(self, mon, healthy_components, t0):
        """TC-14: 정상 스냅샷 summary에 HEALTHY 포함."""
        snap = mon.capture(healthy_components, now=t0)
        assert "HEALTHY" in snap.summary()
        assert "5/5" in snap.summary()

    def test_tc15_last_snapshot(self, mon, healthy_components, t0):
        """TC-15: last_snapshot() 가장 최근 반환."""
        mon.capture(healthy_components, note="first", now=t0)
        mon.capture(healthy_components, note="second", now=t0)
        assert mon.last_snapshot().note == "second"


# ─────────────────────────────────────────────
# TC-16~20: 이상 감지
# ─────────────────────────────────────────────
class TestAnomalyDetection:
    def test_tc16_rollback_surge(self, mon, healthy_components, t0):
        """TC-16: rollback_count ≥ 3 → ROLLBACK_SURGE."""
        snap = mon.capture(healthy_components, rollback_count=3, now=t0)
        assert snap.healthy is False
        assert any("ROLLBACK_SURGE" in a for a in snap.anomalies)

    def test_tc17_rollback_below_threshold_no_anomaly(self, mon, healthy_components, t0):
        """TC-17: rollback_count=2 < 3 → 이상 없음."""
        snap = mon.capture(healthy_components, rollback_count=2, now=t0)
        assert snap.healthy is True

    def test_tc18_f1_extreme_drop(self, mon, healthy_components, t0):
        """TC-18: recent_drift ≤ -0.10 → F1_EXTREME_DROP."""
        snap = mon.capture(healthy_components, recent_drift=-0.12, now=t0)
        assert any("F1_EXTREME_DROP" in a for a in snap.anomalies)

    def test_tc19_f1_drop_exactly_threshold(self, mon, healthy_components, t0):
        """TC-19: recent_drift = -0.10 → F1_EXTREME_DROP (≤ 조건)."""
        snap = mon.capture(healthy_components, recent_drift=-0.10, now=t0)
        assert any("F1_EXTREME_DROP" in a for a in snap.anomalies)

    def test_tc20_pattern_empty(self, mon, healthy_components, t0):
        """TC-20: pattern_count=0 → PATTERN_EMPTY."""
        snap = mon.capture(healthy_components, pattern_count=0, now=t0)
        assert any("PATTERN_EMPTY" in a for a in snap.anomalies)

    def test_tc21_gate_fail_streak(self, mon, healthy_components, t0):
        """TC-21: gate_fail_streak ≥ 3 → GATE_FAIL_STREAK."""
        snap = mon.capture(healthy_components, gate_fail_streak=3, now=t0)
        assert any("GATE_FAIL_STREAK" in a for a in snap.anomalies)

    def test_tc22_multiple_anomalies(self, mon, healthy_components, t0):
        """TC-22: 여러 이상 동시 감지."""
        snap = mon.capture(
            healthy_components,
            rollback_count=5,
            recent_drift=-0.15,
            pattern_count=0,
            now=t0,
        )
        assert len(snap.anomalies) == 3

    def test_tc23_unhealthy_component_makes_snapshot_degraded(self, mon, degraded_components, t0):
        """TC-23: 비정상 컴포넌트 있으면 healthy=False."""
        snap = mon.capture(degraded_components, now=t0)
        assert snap.healthy is False
        assert "DEGRADED" in snap.summary()


# ─────────────────────────────────────────────
# TC-24~26: history / unhealthy_snapshots
# ─────────────────────────────────────────────
class TestHistory:
    def test_tc24_history_order(self, mon, healthy_components, degraded_components, t0):
        """TC-24: history() 오래된 순."""
        mon.capture(healthy_components, note="a", now=t0)
        mon.capture(degraded_components, note="b", now=t0)
        h = mon.history()
        assert h[0].note == "a"
        assert h[1].note == "b"

    def test_tc25_unhealthy_snapshots_filter(self, mon, healthy_components, degraded_components, t0):
        """TC-25: unhealthy_snapshots() 비정상만 반환."""
        mon.capture(healthy_components, now=t0)
        mon.capture(degraded_components, now=t0)
        mon.capture(healthy_components, rollback_count=5, now=t0)
        uh = mon.unhealthy_snapshots()
        assert len(uh) == 2

    def test_tc26_history_copy_safe(self, mon, healthy_components, t0):
        """TC-26: history() 반환값 수정이 내부에 영향 없음."""
        mon.capture(healthy_components, now=t0)
        mon.history().clear()
        assert mon.count() == 1


# ─────────────────────────────────────────────
# TC-27~29: 파일 모드 영속화
# ─────────────────────────────────────────────
class TestFilePersistence:
    def test_tc27_file_created(self, tmp_path, healthy_components, t0):
        """TC-27: capture() 후 JSONL 파일 생성."""
        p = tmp_path / "monitor.jsonl"
        m = SelfLearningMonitor(store_path=str(p))
        m.capture(healthy_components, now=t0)
        assert p.exists()

    def test_tc28_reload_from_file(self, tmp_path, healthy_components, t0):
        """TC-28: 파일 재로드 후 이력 복원."""
        p = tmp_path / "monitor.jsonl"
        m1 = SelfLearningMonitor(store_path=str(p))
        m1.capture(healthy_components, note="persist", now=t0)

        m2 = SelfLearningMonitor(store_path=str(p))
        assert m2.count() == 1
        assert m2.last_snapshot().note == "persist"

    def test_tc29_clear_removes_file(self, tmp_path, healthy_components, t0):
        """TC-29: clear() 후 파일 삭제."""
        p = tmp_path / "monitor.jsonl"
        m = SelfLearningMonitor(store_path=str(p))
        m.capture(healthy_components, now=t0)
        m.clear()
        assert m.count() == 0
        assert not p.exists()


# ─────────────────────────────────────────────
# TC-30~31: 파라미터 검증
# ─────────────────────────────────────────────
class TestParameterValidation:
    def test_tc30_invalid_rollback_surge_zero(self):
        """TC-30: rollback_surge_threshold=0 → ValueError."""
        with pytest.raises(ValueError):
            SelfLearningMonitor(store_path=":memory:", rollback_surge_threshold=0)

    def test_tc31_invalid_f1_drop_threshold_zero(self):
        """TC-31: f1_drop_threshold=0 → ValueError."""
        with pytest.raises(ValueError):
            SelfLearningMonitor(store_path=":memory:", f1_drop_threshold=0.0)


# ─────────────────────────────────────────────
# TC-32~33: 공개 API + 통합 시나리오
# ─────────────────────────────────────────────
class TestPublicApiAndIntegration:
    def test_tc32_public_api_imports(self):
        """TC-32: constitution/__init__.py 에서 임포트 가능."""
        assert SLMFromInit is SelfLearningMonitor
        assert MSFromInit is MonitorSnapshot
        assert CSFromInit is ComponentStatus

    def test_tc33_full_pipeline_scenario(self, t0):
        """TC-33: SP-C.1 5컴포넌트 전체 모니터링 시나리오."""
        mon = SelfLearningMonitor(store_path=":memory:")

        # 1차: 전체 정상
        comps = [ComponentStatus(n, True, {"ok": True}) for n in COMPONENT_NAMES]
        s1 = mon.capture(comps, rollback_count=0, pattern_count=10, now=t0)
        assert s1.healthy is True

        # 2차: WeightTracker 이상 + 롤백 급증
        comps2 = [ComponentStatus(n, True) for n in COMPONENT_NAMES]
        comps2[1] = ComponentStatus("WeightTracker", False, {"error": "corrupt"})
        s2 = mon.capture(comps2, rollback_count=4, now=t0)
        assert s2.healthy is False
        assert any("ROLLBACK_SURGE" in a for a in s2.anomalies)

        # 3차: F1 극단 하락 + 패턴 소진
        comps3 = [ComponentStatus(n, True) for n in COMPONENT_NAMES]
        s3 = mon.capture(comps3, recent_drift=-0.20, pattern_count=0, now=t0)
        assert len(s3.anomalies) == 2

        assert mon.count() == 3
        assert len(mon.unhealthy_snapshots()) == 2
        # 직렬화 검증
        d = s2.to_dict()
        restored = MonitorSnapshot.from_dict(d)
        assert restored.snapshot_id == s2.snapshot_id
        assert restored.healthy == s2.healthy
