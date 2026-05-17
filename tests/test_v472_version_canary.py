"""
test_v472_version_canary.py — ModelVersionManager v2 + CanaryKPIMonitor 테스트 (V472)

ADR-006: ModelLifecycle (30일 롤백, CANARY_STEPS=[1,5,25,100])
ADR-017: Canary Deployment (5분 슬라이딩 윈도우, 자동 롤백)
"""
import uuid
import pytest
from literary_system.finetune.model_version_manager import (
    ModelVersionManager, ModelArtifact, ModelStage, CANARY_STEPS,
)
from literary_system.finetune.canary_kpi_monitor import (
    CanaryKPIMonitor, KPI_THRESHOLDS,
)


def _make_artifact(model_id: str = "test-model") -> ModelArtifact:
    return ModelArtifact(
        artifact_id=f"art-{str(uuid.uuid4())[:8]}",
        model_id=model_id,
        base_model="mock-base-v1",
        method="mock",
        checksum="abc123",
        size_mb=256.0,
    )


# ─────────────────────────────────────────────
# ModelVersionManager
# ─────────────────────────────────────────────

class TestModelVersionManagerRegister:
    """버전 등록"""

    def test_register_returns_version_id(self):
        mgr = ModelVersionManager()
        art = _make_artifact()
        vid = mgr.register("model-a", art)
        assert vid is not None
        assert vid != ""

    def test_registered_stage_is_registered(self):
        mgr = ModelVersionManager()
        art = _make_artifact()
        vid = mgr.register("model-b", art)
        v = mgr.get_version(vid)
        assert v.stage == ModelStage.REGISTERED

    def test_canary_pct_zero_after_register(self):
        mgr = ModelVersionManager()
        vid = mgr.register("model-c", _make_artifact())
        v = mgr.get_version(vid)
        assert v.canary_pct == 0

    def test_rollback_deadline_30_days(self):
        mgr = ModelVersionManager()
        vid = mgr.register("model-d", _make_artifact())
        v = mgr.get_version(vid)
        assert v.rollback_deadline != ""
        assert v.is_rollback_available is True

    def test_custom_version_tag(self):
        mgr = ModelVersionManager()
        vid = mgr.register("model-e", _make_artifact(), version_tag="v2.0-custom")
        v = mgr.get_version(vid)
        assert v.version_tag == "v2.0-custom"

    def test_auto_version_tag(self):
        mgr = ModelVersionManager()
        vid = mgr.register("model-f", _make_artifact())
        v = mgr.get_version(vid)
        assert v.version_tag.startswith("v")


class TestModelVersionManagerCanary:
    """카나리 승격 (ADR-006: CANARY_STEPS=[1,5,25,100])"""

    def test_canary_steps_defined(self):
        assert CANARY_STEPS == [1, 5, 25, 100]

    def test_promote_1pct(self):
        mgr = ModelVersionManager()
        vid = mgr.register("model-canary", _make_artifact())
        v = mgr.canary_promote(vid, 1)
        assert v.stage == ModelStage.CANARY
        assert v.canary_pct == 1

    def test_promote_5pct(self):
        mgr = ModelVersionManager()
        vid = mgr.register("model-canary", _make_artifact())
        mgr.canary_promote(vid, 1)
        v = mgr.canary_promote(vid, 5)
        assert v.canary_pct == 5

    def test_promote_25pct(self):
        mgr = ModelVersionManager()
        vid = mgr.register("model-canary", _make_artifact())
        mgr.canary_promote(vid, 25)
        v = mgr.get_version(vid)
        assert v.canary_pct == 25

    def test_promote_100pct_becomes_production(self):
        mgr = ModelVersionManager()
        vid = mgr.register("model-canary", _make_artifact())
        v = mgr.canary_promote(vid, 100)
        assert v.stage == ModelStage.PRODUCTION
        assert v.canary_pct == 100

    def test_invalid_canary_pct_raises(self):
        mgr = ModelVersionManager()
        vid = mgr.register("model-canary", _make_artifact())
        with pytest.raises(ValueError):
            mgr.canary_promote(vid, 50)  # 50은 CANARY_STEPS에 없음

    def test_promote_retired_raises(self):
        mgr = ModelVersionManager()
        vid = mgr.register("model-ret", _make_artifact())
        mgr.retire(vid)
        with pytest.raises(ValueError):
            mgr.canary_promote(vid, 1)

    def test_promotion_history_recorded(self):
        mgr = ModelVersionManager()
        vid = mgr.register("model-hist", _make_artifact())
        mgr.canary_promote(vid, 1)
        mgr.canary_promote(vid, 5)
        v = mgr.get_version(vid)
        assert len(v.promotion_history) >= 2


class TestModelVersionManagerRollback:
    """롤백 (ADR-006: 30일 보장)"""

    def test_rollback_within_deadline(self):
        mgr = ModelVersionManager()
        vid = mgr.register("model-roll", _make_artifact())
        mgr.canary_promote(vid, 5)
        result = mgr.rollback(vid)
        assert result is True

    def test_rollback_resets_to_registered(self):
        mgr = ModelVersionManager()
        vid = mgr.register("model-roll2", _make_artifact())
        mgr.canary_promote(vid, 25)
        mgr.rollback(vid)
        v = mgr.get_version(vid)
        assert v.stage == ModelStage.REGISTERED
        assert v.canary_pct == 0


class TestModelVersionManagerRetire:
    """폐기"""

    def test_retire_sets_retired_stage(self):
        mgr = ModelVersionManager()
        vid = mgr.register("model-ret", _make_artifact())
        result = mgr.retire(vid)
        assert result is True
        v = mgr.get_version(vid)
        assert v.stage == ModelStage.RETIRED

    def test_retire_already_retired_returns_false(self):
        mgr = ModelVersionManager()
        vid = mgr.register("model-ret2", _make_artifact())
        mgr.retire(vid)
        result = mgr.retire(vid)
        assert result is False


class TestModelVersionManagerList:
    """버전 조회"""

    def test_list_versions_by_model(self):
        mgr = ModelVersionManager()
        for i in range(3):
            mgr.register("model-list", _make_artifact("model-list"))
        versions = mgr.list_versions("model-list")
        assert len(versions) == 3

    def test_get_production_version(self):
        mgr = ModelVersionManager()
        vid = mgr.register("model-prod", _make_artifact("model-prod"))
        mgr.canary_promote(vid, 100)
        prod = mgr.get_production_version("model-prod")
        assert prod is not None
        assert prod.stage == ModelStage.PRODUCTION

    def test_get_production_version_none_if_not_promoted(self):
        mgr = ModelVersionManager()
        mgr.register("model-noprod", _make_artifact("model-noprod"))
        prod = mgr.get_production_version("model-noprod")
        assert prod is None


# ─────────────────────────────────────────────
# CanaryKPIMonitor
# ─────────────────────────────────────────────

class TestCanaryKPIMonitorRecord:
    """KPI 기록"""

    def test_record_returns_kpi_record(self):
        monitor = CanaryKPIMonitor()
        rec = monitor.record("ver-001", coherence=0.7, hallucination_rate=0.1,
                             safety_violation_rate=0.01)
        assert rec is not None
        assert rec.version_id == "ver-001"

    def test_record_fields(self):
        monitor = CanaryKPIMonitor()
        rec = monitor.record("ver-002", coherence=0.65, hallucination_rate=0.15,
                             safety_violation_rate=0.02, latency_ms=120.0)
        assert rec.coherence == 0.65
        assert rec.hallucination_rate == 0.15
        assert rec.safety_violation_rate == 0.02


class TestCanaryKPIMonitorEvaluate:
    """슬라이딩 윈도우 집계 및 롤백 판단"""

    def test_normal_kpi_no_rollback(self):
        monitor = CanaryKPIMonitor()
        for _ in range(3):
            monitor.record("ver-normal", coherence=0.75, hallucination_rate=0.05,
                           safety_violation_rate=0.01)
        window = monitor.evaluate("ver-normal")
        assert window.rollback_triggered is False

    def test_low_coherence_triggers_rollback(self):
        monitor = CanaryKPIMonitor()
        monitor.record("ver-bad-coh", coherence=0.3, hallucination_rate=0.05,
                       safety_violation_rate=0.01)
        window = monitor.evaluate("ver-bad-coh")
        assert window.rollback_triggered is True
        assert len(window.rollback_reasons) > 0

    def test_high_hallucination_triggers_rollback(self):
        monitor = CanaryKPIMonitor()
        monitor.record("ver-bad-hall", coherence=0.7, hallucination_rate=0.5,
                       safety_violation_rate=0.01)
        window = monitor.evaluate("ver-bad-hall")
        assert window.rollback_triggered is True

    def test_high_safety_violation_triggers_rollback(self):
        monitor = CanaryKPIMonitor()
        monitor.record("ver-bad-safe", coherence=0.7, hallucination_rate=0.1,
                       safety_violation_rate=0.1)
        window = monitor.evaluate("ver-bad-safe")
        assert window.rollback_triggered is True

    def test_empty_window_no_rollback(self):
        monitor = CanaryKPIMonitor()
        window = monitor.evaluate("ver-empty")
        assert window.rollback_triggered is False
        assert window.record_count == 0

    def test_window_metrics_averaged(self):
        monitor = CanaryKPIMonitor()
        monitor.record("ver-avg", coherence=0.6, hallucination_rate=0.1, safety_violation_rate=0.01)
        monitor.record("ver-avg", coherence=0.8, hallucination_rate=0.2, safety_violation_rate=0.02)
        window = monitor.evaluate("ver-avg")
        assert abs(window.avg_coherence - 0.7) < 0.05
        assert window.record_count == 2


class TestCanaryKPIMonitorThresholds:
    """KPI 임계값 (ADR-017)"""

    def test_thresholds_defined(self):
        assert "coherence_min" in KPI_THRESHOLDS
        assert "hallucination_max" in KPI_THRESHOLDS
        assert "safety_violation_max" in KPI_THRESHOLDS

    def test_coherence_min_value(self):
        assert KPI_THRESHOLDS["coherence_min"] > 0
        assert KPI_THRESHOLDS["coherence_min"] < 1.0

    def test_hallucination_max_value(self):
        assert KPI_THRESHOLDS["hallucination_max"] > 0
        assert KPI_THRESHOLDS["hallucination_max"] <= 1.0

    def test_safety_violation_max_value(self):
        assert KPI_THRESHOLDS["safety_violation_max"] > 0
        assert KPI_THRESHOLDS["safety_violation_max"] <= 0.1


class TestCanaryKPIMonitorRollbackEvents:
    """롤백 이벤트 조회"""

    def test_rollback_event_created(self):
        monitor = CanaryKPIMonitor()
        monitor.record("ver-evt", coherence=0.2, hallucination_rate=0.5,
                       safety_violation_rate=0.1)
        monitor.evaluate("ver-evt")
        events = monitor.get_rollback_events("ver-evt")
        assert len(events) >= 1

    def test_is_rollback_required_true(self):
        monitor = CanaryKPIMonitor()
        monitor.record("ver-req", coherence=0.2, hallucination_rate=0.5,
                       safety_violation_rate=0.1)
        assert monitor.is_rollback_required("ver-req") is True

    def test_is_rollback_required_false(self):
        monitor = CanaryKPIMonitor()
        monitor.record("ver-ok", coherence=0.8, hallucination_rate=0.05,
                       safety_violation_rate=0.01)
        assert monitor.is_rollback_required("ver-ok") is False
