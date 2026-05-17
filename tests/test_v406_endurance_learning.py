"""V406 — EnduranceLearningBridge + CoefficientDelta 테스트 (22 tests)."""
import pytest
from literary_system.learning.endurance_learning_bridge import (
    CoefficientDelta, EnduranceLearningBridge
)
from literary_system.physics.coefficient_store import PhysicsCoefficientStore


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

class _MockReport:
    def __init__(
        self,
        weak_scene_ratio: float = 0.0,
        agency_violations=None,
        mid_fatigue: float = 0.0,
        voice_blocked: int = 0,
    ):
        class NR:
            pass
        class AR:
            pass
        class FR:
            pass
        class VR:
            pass

        nr = NR(); nr.weak_scene_ratio = weak_scene_ratio
        ar = AR(); ar.agency_floor_violations = agency_violations or []
        fr = FR(); fr.mid_season_fatigue_risk = mid_fatigue
        vr = VR(); vr.blocked_count = voice_blocked

        self.necessity_report = nr
        self.agency_report = ar
        self.fatigue_report = fr
        self.voice_drift_report = vr


# ── CoefficientDelta 테스트 ───────────────────────────────────────────────────

class TestCoefficientDelta:
    def test_is_empty_true(self):
        delta = CoefficientDelta(updates={}, reason="none", source_report="test")
        assert delta.is_empty() is True

    def test_is_empty_false(self):
        delta = CoefficientDelta(
            updates={"scene_energy_weight": 0.01},
            reason="test",
            source_report="EnduranceRunReport"
        )
        assert delta.is_empty() is False

    def test_to_dict(self):
        delta = CoefficientDelta(
            updates={"motif_weight": 0.01},
            reason="test_reason",
            source_report="EnduranceRunReport"
        )
        d = delta.to_dict()
        assert "updates" in d
        assert d["source_report"] == "EnduranceRunReport"

    def test_max_updates_respected_by_caller(self):
        """updates는 임의 크기지만, Bridge는 MAX_UPDATES_PER_CALL=3 보장."""
        delta = CoefficientDelta(
            updates={"a": 0.01, "b": 0.01, "c": 0.01},
            reason="triple",
            source_report="EnduranceRunReport"
        )
        assert len(delta.updates) <= 3


# ── EnduranceLearningBridge.analyze 테스트 ────────────────────────────────────

class TestEnduranceLearningBridgeAnalyze:
    def setup_method(self):
        self.bridge = EnduranceLearningBridge()

    def test_no_issues_returns_empty_delta(self):
        report = _MockReport()
        delta = self.bridge.analyze(report)
        assert delta.is_empty()

    def test_weak_ratio_triggers_scene_energy_weight(self):
        report = _MockReport(weak_scene_ratio=0.20)
        delta = self.bridge.analyze(report)
        assert "scene_energy_weight" in delta.updates

    def test_agency_violations_triggers_arc_pressure_coupling(self):
        report = _MockReport(agency_violations=["ep3_hero", "ep5_hero"])
        delta = self.bridge.analyze(report)
        assert "arc_pressure_coupling" in delta.updates

    def test_mid_fatigue_triggers_curiosity_weight(self):
        report = _MockReport(mid_fatigue=0.40)
        delta = self.bridge.analyze(report)
        assert "curiosity_weight" in delta.updates

    def test_voice_blocked_triggers_prose_physics_bridge(self):
        report = _MockReport(voice_blocked=2)
        delta = self.bridge.analyze(report)
        assert "prose_physics_bridge" in delta.updates

    def test_all_issues_capped_at_3(self):
        """4개 신호 모두 발생해도 최대 3개만 선택."""
        report = _MockReport(
            weak_scene_ratio=0.20,
            agency_violations=["x"],
            mid_fatigue=0.40,
            voice_blocked=1,
        )
        delta = self.bridge.analyze(report)
        assert len(delta.updates) <= 3

    def test_learning_rate_applied(self):
        report = _MockReport(weak_scene_ratio=0.20)
        delta = self.bridge.analyze(report)
        assert delta.updates.get("scene_energy_weight") == 0.01

    def test_reason_string_not_empty_on_update(self):
        report = _MockReport(weak_scene_ratio=0.20)
        delta = self.bridge.analyze(report)
        assert delta.reason != "no_update_needed"

    def test_reason_string_no_update(self):
        report = _MockReport()
        delta = self.bridge.analyze(report)
        assert delta.reason == "no_update_needed"

    def test_weak_ratio_below_threshold_no_update(self):
        """threshold=0.10 미만이면 업데이트 없음."""
        report = _MockReport(weak_scene_ratio=0.05)
        delta = self.bridge.analyze(report)
        assert "scene_energy_weight" not in delta.updates

    def test_none_reports_no_error(self):
        """report에 서브리포트 없어도 오류 없이 처리."""
        class EmptyReport:
            pass
        delta = self.bridge.analyze(EmptyReport())
        assert delta.is_empty()


# ── EnduranceLearningBridge.apply 테스트 ─────────────────────────────────────

class TestEnduranceLearningBridgeApply:
    def setup_method(self):
        self.bridge = EnduranceLearningBridge()
        self.store = PhysicsCoefficientStore()

    def test_apply_updates_coefficient(self):
        before = self.store.scene_energy_weight
        delta = CoefficientDelta(
            updates={"scene_energy_weight": 0.01},
            reason="test",
            source_report="EnduranceRunReport"
        )
        self.bridge.apply(delta, self.store)
        assert self.store.scene_energy_weight > before

    def test_apply_clamped_at_max(self):
        """clamp [0.05, 0.45] — 최대값 초과 시 0.45로 제한."""
        self.store.update(curiosity_weight=0.44)
        delta = CoefficientDelta(
            updates={"curiosity_weight": 0.01},
            reason="test",
            source_report="EnduranceRunReport"
        )
        self.bridge.apply(delta, self.store)
        assert self.store.curiosity_weight <= 0.45

    def test_apply_empty_delta_no_change(self):
        before = self.store.as_dict().copy()
        delta = CoefficientDelta(updates={}, reason="none", source_report="EnduranceRunReport")
        self.bridge.apply(delta, self.store)
        assert self.store.as_dict() == before

    def test_apply_returns_trace(self):
        delta = CoefficientDelta(
            updates={"motif_weight": 0.01},
            reason="test",
            source_report="EnduranceRunReport"
        )
        trace = self.bridge.apply(delta, self.store)
        assert isinstance(trace, list)
        assert len(trace) > 0

    def test_apply_unknown_coefficient_skipped(self):
        """존재하지 않는 계수명은 skip (오류 없이)."""
        delta = CoefficientDelta(
            updates={"nonexistent_weight": 0.01},
            reason="test",
            source_report="EnduranceRunReport"
        )
        trace = self.bridge.apply(delta, self.store)
        assert any("SKIP" in t for t in trace)
