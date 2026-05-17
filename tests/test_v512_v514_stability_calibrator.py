"""
Tests for V512~V514:
  - NILStabilityModule  (nil_stability_module.py)
  - AgentCalibrator     (agent_calibrator.py)
  - ADR-019 integration
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from literary_system.nie.nil_stability_module import (
    NILStabilityModule,
    StabilityEventType,
    DIVERGE_THRESHOLD,
    DIVERGE_CONSECUTIVE,
    LR_DIVERGE_FACTOR,
    OSCILLATION_SIGN_CROSS,
    LR_OSC_FACTOR,
    BOUNDARY_INNER_LOW,
    BOUNDARY_INNER_HIGH,
)
from literary_system.nie.agent_calibrator import (
    AgentCalibrator,
    CalibratorPhase,
    RubricCalibrator,
    PHASE2_ACTIVATION_WORKS,
    BIWEEKLY_INTERVAL_WORKS,
    MIN_WEIGHT,
    WEIGHT_ADJUST_CAP,
)


# ─── 헬퍼 ──────────────────────────────────────────────────────────────────────

class _FakeOrchestrator:
    """MAEOrchestratorV2 의 경량 스텁."""
    def __init__(self, weights=None):
        self._weights = weights or {
            "reader": 0.35, "writer": 0.25, "editor": 0.25, "cultural": 0.15
        }
        self.update_weights_calls = []

    def update_weights(self, new_weights):
        self._weights = dict(new_weights)
        self.update_weights_calls.append(dict(new_weights))


# ─── TestNILStabilityModule ────────────────────────────────────────────────────

class TestNILStabilityModule:

    def test_init_returns_normal_event(self):
        mod = NILStabilityModule()
        evt = mod.update("tension", 0.50, 0.50)
        assert evt.event_type == StabilityEventType.NORMAL
        assert evt.dim == "tension"

    def test_small_delta_no_diverge(self):
        mod = NILStabilityModule()
        for _ in range(5):
            evt = mod.update("tension", 0.55, 0.52)  # delta=0.03 < 0.10
        assert evt.event_type == StabilityEventType.NORMAL

    def test_divergence_triggers_after_consecutive(self):
        """|Δα| > 0.10 연속 3회 → DIVERGENCE 이벤트."""
        mod = NILStabilityModule()
        alpha = 0.50
        events = []
        for _ in range(DIVERGE_CONSECUTIVE):
            new_a = alpha + 0.15          # delta=0.15 > 0.10
            events.append(mod.update("tension", new_a, alpha))
            alpha = new_a
        assert events[-1].event_type == StabilityEventType.DIVERGENCE

    def test_divergence_reduces_lr_factor(self):
        mod = NILStabilityModule()
        alpha = 0.50
        for _ in range(DIVERGE_CONSECUTIVE):
            new_a = alpha + 0.15
            mod.update("tension", new_a, alpha)
            alpha = new_a
        factor = mod.get_dim_lr_factor("tension")
        assert factor < 1.0
        assert abs(factor - LR_DIVERGE_FACTOR) < 1e-9 or factor <= LR_DIVERGE_FACTOR

    def test_divergence_counter_resets_after_trigger(self):
        """발산 트리거 후 소규모 변화가 이어져도 바로 재발산하지 않는다."""
        mod = NILStabilityModule()
        # delta=0.11 × 3 → 시작 0.40 → 0.73; 이후 +0.005 × 2 = 0.74 (경계 0.795 이내)
        alpha = 0.40
        for _ in range(DIVERGE_CONSECUTIVE):
            new_a = alpha + 0.11
            mod.update("tension", new_a, alpha)
            alpha = new_a
        # 작은 delta 2회 — 발산 카운터 리셋 후 NORMAL 이어야 함
        for _ in range(2):
            new_a = alpha + 0.005
            evt = mod.update("tension", new_a, alpha)
            alpha = new_a
        assert evt.event_type == StabilityEventType.NORMAL

    def test_lr_floor_not_zero(self):
        """LR 계수가 0.05 미만으로 내려가지 않는다."""
        mod = NILStabilityModule()
        alpha = 0.50
        # 대량 반복 발산
        for _ in range(50):
            new_a = alpha + 0.15
            mod.update("tension", new_a, alpha)
            alpha = new_a
        factor = mod.get_dim_lr_factor("tension")
        assert factor >= 0.05

    def test_oscillation_sign_cross_detection(self):
        """부호 교차 OSCILLATION_SIGN_CROSS 회 이상 → OSCILLATION 이벤트."""
        mod = NILStabilityModule()
        alpha = 0.50
        # +0.05 / -0.05 교번 → sign 교차 발생
        events = []
        signs = [+0.05, -0.05] * 10
        for d in signs:
            new_a = alpha + d
            events.append(mod.update("tension", new_a, alpha))
            alpha = new_a
        osc_events = [e for e in events if e.event_type == StabilityEventType.OSCILLATION]
        assert len(osc_events) >= 1

    def test_oscillation_reduces_lr(self):
        mod = NILStabilityModule()
        alpha = 0.50
        signs = [+0.05, -0.05] * 10
        for d in signs:
            mod.update("tension", alpha + d, alpha)
            alpha += d
        factor = mod.get_dim_lr_factor("tension")
        assert factor < 1.0

    def test_boundary_low_alarm(self):
        """α ≤ 0.305 → BOUNDARY_LOW."""
        mod = NILStabilityModule()
        evt = mod.check_boundary("tension", BOUNDARY_INNER_LOW - 0.001)
        assert evt is not None
        assert evt.event_type == StabilityEventType.BOUNDARY_LOW

    def test_boundary_high_alarm(self):
        """α ≥ 0.795 → BOUNDARY_HIGH."""
        mod = NILStabilityModule()
        evt = mod.check_boundary("tension", BOUNDARY_INNER_HIGH + 0.001)
        assert evt is not None
        assert evt.event_type == StabilityEventType.BOUNDARY_HIGH

    def test_boundary_normal_inside(self):
        mod = NILStabilityModule()
        evt = mod.check_boundary("tension", 0.50)
        assert evt is None

    def test_get_effective_lr_no_alarm(self):
        """알람 없을 때 get_effective_lr 는 base_lr 그대로."""
        mod = NILStabilityModule()
        lr = mod.get_effective_lr("physics", 0.01)
        assert lr == pytest.approx(0.01, rel=1e-6)

    def test_get_effective_lr_after_diverge(self):
        """발산 후 get_effective_lr("amw") 는 감소된 값."""
        mod = NILStabilityModule()
        alpha = 0.50
        for _ in range(DIVERGE_CONSECUTIVE):
            new_a = alpha + 0.15
            mod.update("tension", new_a, alpha)
            alpha = new_a
        lr = mod.get_effective_lr("amw", 0.005)
        assert lr < 0.005

    def test_set_module_lr_factor(self):
        mod = NILStabilityModule()
        mod.set_module_lr_factor("physics", 0.5)
        lr = mod.get_effective_lr("physics", 0.01)
        assert lr == pytest.approx(0.005, rel=1e-6)

    def test_reset_dim(self):
        """reset_dim 후 해당 차원 LR 계수 1.0 복원."""
        mod = NILStabilityModule()
        alpha = 0.50
        for _ in range(DIVERGE_CONSECUTIVE):
            new_a = alpha + 0.15
            mod.update("tension", new_a, alpha)
            alpha = new_a
        mod.reset_dim("tension")
        factor = mod.get_dim_lr_factor("tension")
        assert factor == pytest.approx(1.0)

    def test_reset_all(self):
        mod = NILStabilityModule()
        mod.update("tension", 0.55, 0.50)
        mod.update("sympathy", 0.60, 0.50)
        mod.reset_all()
        assert mod.get_effective_lr("amw", 1.0) == pytest.approx(1.0)
        assert len(mod.events) == 0

    def test_multiple_dims_independent(self):
        """차원별 LR 계수가 독립적으로 관리된다."""
        mod = NILStabilityModule()
        # tension 에서만 발산 유발
        alpha = 0.50
        for _ in range(DIVERGE_CONSECUTIVE):
            new_a = alpha + 0.15
            mod.update("tension", new_a, alpha)
            alpha = new_a
        factor_t = mod.get_dim_lr_factor("tension")
        factor_s = mod.get_dim_lr_factor("sympathy")  # 0회 업데이트
        assert factor_t < factor_s
        assert factor_s == pytest.approx(1.0)

    def test_alarm_events_filtered(self):
        mod = NILStabilityModule()
        mod.update("tension", 0.50, 0.50)  # NORMAL
        mod.check_boundary("tension", 0.30)  # not stored in events list via check_boundary
        # update 로 boundary 통과
        mod.update("tension", 0.30, 0.50)   # BOUNDARY_LOW (0.30 ≤ 0.305)
        alarms = mod.alarm_events()
        alarm_types = {e.event_type for e in alarms}
        assert StabilityEventType.BOUNDARY_LOW in alarm_types


# ─── TestRubricCalibrator ──────────────────────────────────────────────────────

class TestRubricCalibrator:

    def _make_records(self, pass_rate_map: dict):
        from literary_system.nie.agent_calibrator import AgentRecord
        records = {}
        for agent, (passes, fails) in pass_rate_map.items():
            r = AgentRecord(agent=agent, pass_count=passes, fail_count=fails)
            records[agent] = r
        return records

    def test_evaluate_returns_scores_for_all_agents(self):
        rubric = RubricCalibrator()
        records = self._make_records({
            "reader": (8, 2), "writer": (7, 3), "editor": (6, 4), "cultural": (9, 1)
        })
        weights = {"reader": 0.35, "writer": 0.25, "editor": 0.25, "cultural": 0.15}
        scores = rubric.evaluate(records, weights)
        assert len(scores) == 4
        agents = {s.agent for s in scores}
        assert agents == {"reader", "writer", "editor", "cultural"}

    def test_high_pass_rate_positive_delta(self):
        rubric = RubricCalibrator()
        from literary_system.nie.agent_calibrator import AgentRecord
        rec = AgentRecord(agent="reader", pass_count=10, fail_count=0)
        scores = rubric.evaluate({"reader": rec}, {"reader": 0.35})
        assert scores[0].weight_delta > 0

    def test_low_pass_rate_negative_delta(self):
        rubric = RubricCalibrator()
        from literary_system.nie.agent_calibrator import AgentRecord
        rec = AgentRecord(agent="reader", pass_count=0, fail_count=10)
        scores = rubric.evaluate({"reader": rec}, {"reader": 0.35})
        assert scores[0].weight_delta < 0

    def test_compute_new_weights_sums_to_1(self):
        rubric = RubricCalibrator()
        from literary_system.nie.agent_calibrator import AgentRecord, RubricScore
        scores = [
            RubricScore("reader", 0.80, +0.05),
            RubricScore("writer", 0.60, +0.01),
            RubricScore("editor", 0.40, -0.03),
            RubricScore("cultural", 0.50, 0.00),
        ]
        weights = {"reader": 0.35, "writer": 0.25, "editor": 0.25, "cultural": 0.15}
        new_w = rubric.compute_new_weights(scores, weights)
        assert abs(sum(new_w.values()) - 1.0) < 1e-9

    def test_no_weight_below_min(self):
        rubric = RubricCalibrator()
        from literary_system.nie.agent_calibrator import RubricScore
        # editor 에 극도로 부정적 delta
        scores = [
            RubricScore("reader", 0.90, +0.15),
            RubricScore("writer", 0.90, +0.15),
            RubricScore("editor", 0.00, -0.15),
            RubricScore("cultural", 0.00, -0.15),
        ]
        weights = {"reader": 0.35, "writer": 0.25, "editor": 0.25, "cultural": 0.15}
        new_w = rubric.compute_new_weights(scores, weights)
        for w in new_w.values():
            assert w >= MIN_WEIGHT


# ─── TestAgentCalibrator ──────────────────────────────────────────────────────

class TestAgentCalibrator:

    def test_initial_phase_is_phase1(self):
        cal = AgentCalibrator()
        assert cal.phase == CalibratorPhase.PHASE1

    def test_record_result_increments_pass(self):
        cal = AgentCalibrator()
        cal.record_result("reader", True)
        cal.record_result("reader", True)
        cal.record_result("reader", False)
        rec = cal.get_record("reader")
        assert rec.pass_count == 2
        assert rec.fail_count == 1

    def test_sigma_escalation_recorded(self):
        from literary_system.nie.agent_calibrator import SIGMA_ESCALATION_THRESHOLD
        cal = AgentCalibrator()
        cal.record_result("writer", True, sigma=SIGMA_ESCALATION_THRESHOLD + 0.01)
        rec = cal.get_record("writer")
        assert rec.sigma_escalations == 1

    def test_phase2_activates_after_works_threshold(self):
        cal = AgentCalibrator()
        for _ in range(PHASE2_ACTIVATION_WORKS):
            cal.complete_work()
        assert cal.phase == CalibratorPhase.PHASE2

    def test_no_calibration_in_phase1(self):
        cal = AgentCalibrator()
        orch = _FakeOrchestrator()
        cal.record_result("reader", True)
        result = cal.maybe_calibrate(orch)
        assert result is None
        assert len(orch.update_weights_calls) == 0

    def test_no_calibration_before_interval(self):
        cal = AgentCalibrator()
        orch = _FakeOrchestrator()
        cal.activate_phase2()
        cal.record_result("reader", True)
        # 작품 1편만 완료 (interval=2 미충족)
        cal.complete_work()
        result = cal.maybe_calibrate(orch)
        assert result is None

    def test_calibration_triggers_at_interval(self):
        """격주(BIWEEKLY_INTERVAL_WORKS) 도달 시 calibration 실행."""
        cal = AgentCalibrator()
        orch = _FakeOrchestrator()
        cal.activate_phase2()
        # 에이전트 기록
        for agent in ["reader", "writer", "editor", "cultural"]:
            for _ in range(5):
                cal.record_result(agent, True)
        # 격주 간격 충족
        for _ in range(BIWEEKLY_INTERVAL_WORKS):
            cal.complete_work()
        result = cal.maybe_calibrate(orch)
        assert result is not None
        assert len(orch.update_weights_calls) == 1

    def test_calibration_result_weights_sum_to_1(self):
        cal = AgentCalibrator()
        orch = _FakeOrchestrator()
        cal.activate_phase2()
        for agent in ["reader", "writer", "editor", "cultural"]:
            for _ in range(5):
                cal.record_result(agent, True)
        result = cal.force_calibrate(orch)
        assert abs(sum(result.new_weights.values()) - 1.0) < 1e-9

    def test_force_calibrate_ignores_phase(self):
        """force_calibrate 는 Phase 1 에서도 동작한다."""
        cal = AgentCalibrator()
        orch = _FakeOrchestrator()
        cal.record_result("reader", True)
        result = cal.force_calibrate(orch)
        assert result is not None

    def test_calibration_history_accumulates(self):
        cal = AgentCalibrator()
        orch = _FakeOrchestrator()
        cal.activate_phase2()
        for agent in ["reader", "writer", "editor", "cultural"]:
            cal.record_result(agent, True)
        cal.force_calibrate(orch)
        cal.force_calibrate(orch)
        assert len(cal.calibration_history) == 2

    def test_old_weights_preserved_in_result(self):
        cal = AgentCalibrator()
        orch = _FakeOrchestrator({"reader": 0.35, "writer": 0.25, "editor": 0.25, "cultural": 0.15})
        cal.activate_phase2()
        for agent in ["reader", "writer", "editor", "cultural"]:
            cal.record_result(agent, True)
        result = cal.force_calibrate(orch)
        assert result.old_weights["reader"] == pytest.approx(0.35)

    def test_maybe_calibrate_no_repeat_before_next_interval(self):
        """한 번 calibration 후 interval 충족 전 재실행 방지."""
        cal = AgentCalibrator()
        orch = _FakeOrchestrator()
        cal.activate_phase2()
        for agent in ["reader", "writer", "editor", "cultural"]:
            cal.record_result(agent, True)
        for _ in range(BIWEEKLY_INTERVAL_WORKS):
            cal.complete_work()
        cal.maybe_calibrate(orch)                    # 1회 실행
        result2 = cal.maybe_calibrate(orch)          # 즉시 재호출 → None
        assert result2 is None


# ─── TestStabilityCalibratorsIntegration ──────────────────────────────────────

class TestStabilityCalibratorsIntegration:
    """NILStabilityModule + AgentCalibrator 통합 점검."""

    def test_stability_module_set_factor_via_calibrator(self):
        """AgentCalibrator 재보정 결과를 stability_module 에 반영 가능."""
        mod = NILStabilityModule()
        cal = AgentCalibrator()
        orch = _FakeOrchestrator()

        # reader 성과 훌륭, editor 저조 → 재보정 후 weights 변화
        for _ in range(10):
            cal.record_result("reader", True)
        for _ in range(10):
            cal.record_result("editor", False)
        for _ in range(2):
            cal.record_result("writer", True)
            cal.record_result("cultural", True)

        cal.activate_phase2()
        result = cal.force_calibrate(orch)

        # reader 가중치 증가 확인
        assert result.new_weights["reader"] >= result.old_weights["reader"] - 1e-9

        # stability 모듈에 physics LR 계수 반영 (외부 연동 시나리오)
        mod.set_module_lr_factor("physics", 0.8)
        lr = mod.get_effective_lr("physics", 0.01)
        assert lr == pytest.approx(0.008, rel=1e-5)

    def test_adr019_lr_hierarchy(self):
        """ADR-019 LR 계층 구조: effective = base × diverge × osc."""
        mod = NILStabilityModule()
        # 발산만 유발
        alpha = 0.50
        for _ in range(DIVERGE_CONSECUTIVE):
            new_a = alpha + 0.15
            mod.update("tension", new_a, alpha)
            alpha = new_a
        div_factor = mod.get_dim_lr_factor("tension")
        effective = mod.get_effective_lr("amw", 0.005)
        # amw factor = min over all dims; only tension changed
        assert effective < 0.005
        assert effective == pytest.approx(0.005 * div_factor, rel=1e-5)
