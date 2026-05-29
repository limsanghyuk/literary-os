"""tests/unit/test_v605_canary_controller.py

V605 — CanaryController + ModelServingEndpoint 단위 테스트 (27 TC)
ADR-065 참조.
"""

from __future__ import annotations

import pytest

from literary_system.serving.canary_controller import (
    STAGE_WEIGHTS,
    CanaryConfig,
    CanaryController,
    CanaryStage,
    CanaryStatus,
    StageMetrics,
)
from literary_system.serving.model_serving_endpoint import (
    EndpointConfig,
    ModelCard,
    ModelServingEndpoint,
)

# ===========================================================================
# TC-1: STAGE_WEIGHTS 상수
# ===========================================================================


class TestStageWeights:
    def test_tc1_stage_weights_values(self) -> None:
        """TC-1: STAGE_WEIGHTS = [5, 25, 50, 100]."""
        assert STAGE_WEIGHTS == [5, 25, 50, 100]

    def test_tc1_stage_weights_length(self) -> None:
        """TC-1b: 4단계."""
        assert len(STAGE_WEIGHTS) == 4


# ===========================================================================
# TC-2: CanaryConfig 기본값
# ===========================================================================


class TestCanaryConfig:
    def test_tc2_defaults(self) -> None:
        """TC-2: CanaryConfig 기본값 확인."""
        cfg = CanaryConfig()
        assert cfg.model_id == "default-model"
        assert cfg.min_requests_per_stage == 10
        assert cfg.error_rate_threshold == pytest.approx(0.05)
        assert cfg.latency_p95_threshold_ms == pytest.approx(1500.0)
        assert cfg.reward_threshold == pytest.approx(0.75)

    def test_tc2_custom_config(self) -> None:
        """TC-2b: 커스텀 설정 반영."""
        cfg = CanaryConfig(model_id="ppo-v1", min_requests_per_stage=5)
        assert cfg.model_id == "ppo-v1"
        assert cfg.min_requests_per_stage == 5


# ===========================================================================
# TC-3: StageMetrics 속성
# ===========================================================================


class TestStageMetrics:
    def test_tc3_error_rate_zero_requests(self) -> None:
        """TC-3: 요청 0건 → error_rate = 0.0."""
        m = StageMetrics(stage=0)
        assert m.error_rate == pytest.approx(0.0)

    def test_tc3_error_rate_calculation(self) -> None:
        """TC-3b: 오류율 계산."""
        m = StageMetrics(stage=0, requests=10, errors=2)
        assert m.error_rate == pytest.approx(0.2)

    def test_tc3_latency_p95_empty(self) -> None:
        """TC-3c: 빈 latencies → p95 = 0.0."""
        m = StageMetrics(stage=0)
        assert m.latency_p95 == pytest.approx(0.0)

    def test_tc3_latency_p95_calculation(self) -> None:
        """TC-3d: P95 레이턴시 계산."""
        m = StageMetrics(stage=0, latencies_ms=list(range(1, 101)))
        # sorted [1..100], idx = int(100*0.95)-1 = 94 → value 95
        assert m.latency_p95 == pytest.approx(95.0)

    def test_tc3_mean_reward_empty(self) -> None:
        """TC-3e: 빈 rewards → mean_reward = 0.0."""
        m = StageMetrics(stage=0)
        assert m.mean_reward == pytest.approx(0.0)

    def test_tc3_mean_reward_calculation(self) -> None:
        """TC-3f: 보상 평균 계산."""
        m = StageMetrics(stage=0, rewards=[0.8, 0.9, 0.7])
        assert m.mean_reward == pytest.approx(0.8)


# ===========================================================================
# TC-4: CanaryController 생명주기
# ===========================================================================


class TestCanaryControllerLifecycle:
    def _make_ctrl(self) -> CanaryController:
        cfg = CanaryConfig(model_id="test-model", min_requests_per_stage=3)
        return CanaryController(cfg)

    def test_tc4_initial_status(self) -> None:
        """TC-4: 초기 상태 PENDING."""
        ctrl = self._make_ctrl()
        assert ctrl.state.status == CanaryStatus.PENDING

    def test_tc4_start(self) -> None:
        """TC-4b: start() → IN_PROGRESS, stage=0."""
        ctrl = self._make_ctrl()
        ctrl.start()
        assert ctrl.state.status == CanaryStatus.IN_PROGRESS
        assert ctrl.state.current_stage == 0

    def test_tc4_reset(self) -> None:
        """TC-4c: reset() → 초기 상태 복원."""
        ctrl = self._make_ctrl()
        ctrl.start()
        ctrl.reset()
        assert ctrl.state.status == CanaryStatus.PENDING
        assert ctrl.state.current_stage == 0
        assert ctrl.state.total_promoted == 0


# ===========================================================================
# TC-5: record_request
# ===========================================================================


class TestRecordRequest:
    def _make_ctrl(self) -> CanaryController:
        return CanaryController(CanaryConfig(min_requests_per_stage=3))

    def test_tc5_record_increments_requests(self) -> None:
        """TC-5: record_request → requests 증가."""
        ctrl = self._make_ctrl()
        ctrl.start()
        ctrl.record_request(0, latency_ms=200.0, reward=0.80)
        assert ctrl.state.stage_metrics[0].requests == 1

    def test_tc5_record_error(self) -> None:
        """TC-5b: error=True → errors 증가."""
        ctrl = self._make_ctrl()
        ctrl.start()
        ctrl.record_request(0, latency_ms=100.0, reward=0.50, error=True)
        assert ctrl.state.stage_metrics[0].errors == 1

    def test_tc5_record_latency_reward_stored(self) -> None:
        """TC-5c: latency와 reward가 올바르게 저장된다."""
        ctrl = self._make_ctrl()
        ctrl.start()
        ctrl.record_request(0, latency_ms=300.0, reward=0.82)
        m = ctrl.state.stage_metrics[0]
        assert m.latencies_ms == [300.0]
        assert m.rewards == [pytest.approx(0.82)]


# ===========================================================================
# TC-6: evaluate_stage — Gate 통과
# ===========================================================================


def _fill_stage(ctrl: CanaryController, stage: int, n: int = 10) -> None:
    """단계 메트릭을 Gate 통과 조건으로 채운다."""
    for _ in range(n):
        ctrl.record_request(stage, latency_ms=300.0, reward=0.85)


class TestEvaluateStage:
    def test_tc6_gate_pass(self) -> None:
        """TC-6: 조건 충족 → gate_passed=True, promoted=True."""
        ctrl = CanaryController(CanaryConfig(min_requests_per_stage=5))
        ctrl.start()
        _fill_stage(ctrl, 0, n=5)
        result = ctrl.evaluate_stage(0)
        assert result["gate_passed"] is True
        assert result["promoted"] is True
        assert result["fail_reasons"] == []

    def test_tc6_gate_fail_insufficient_requests(self) -> None:
        """TC-6b: 요청 수 부족 → gate_passed=False."""
        ctrl = CanaryController(CanaryConfig(min_requests_per_stage=10))
        ctrl.start()
        _fill_stage(ctrl, 0, n=3)
        result = ctrl.evaluate_stage(0)
        assert result["gate_passed"] is False
        assert any("requests" in r for r in result["fail_reasons"])

    def test_tc6_gate_fail_high_error_rate(self) -> None:
        """TC-6c: 오류율 초과 → gate_passed=False."""
        ctrl = CanaryController(
            CanaryConfig(min_requests_per_stage=5, error_rate_threshold=0.05)
        )
        ctrl.start()
        for i in range(5):
            ctrl.record_request(0, latency_ms=200.0, reward=0.85, error=(i < 2))
        result = ctrl.evaluate_stage(0)
        assert result["gate_passed"] is False
        assert any("error_rate" in r for r in result["fail_reasons"])

    def test_tc6_gate_fail_high_latency(self) -> None:
        """TC-6d: P95 레이턴시 초과 → gate_passed=False."""
        ctrl = CanaryController(
            CanaryConfig(min_requests_per_stage=5, latency_p95_threshold_ms=500.0)
        )
        ctrl.start()
        for _ in range(5):
            ctrl.record_request(0, latency_ms=2000.0, reward=0.85)
        result = ctrl.evaluate_stage(0)
        assert result["gate_passed"] is False
        assert any("latency_p95" in r for r in result["fail_reasons"])

    def test_tc6_gate_fail_low_reward(self) -> None:
        """TC-6e: 보상 미달 → gate_passed=False."""
        ctrl = CanaryController(
            CanaryConfig(min_requests_per_stage=5, reward_threshold=0.75)
        )
        ctrl.start()
        for _ in range(5):
            ctrl.record_request(0, latency_ms=200.0, reward=0.50)
        result = ctrl.evaluate_stage(0)
        assert result["gate_passed"] is False
        assert any("mean_reward" in r for r in result["fail_reasons"])

    def test_tc6_evaluate_result_keys(self) -> None:
        """TC-6f: evaluate_stage 반환 딕셔너리 필수 키 확인."""
        ctrl = CanaryController(CanaryConfig(min_requests_per_stage=3))
        ctrl.start()
        _fill_stage(ctrl, 0, n=3)
        result = ctrl.evaluate_stage(0)
        required = {
            "stage", "traffic_pct", "requests", "error_rate",
            "latency_p95", "mean_reward", "gate_passed", "promoted", "fail_reasons",
        }
        assert required.issubset(result.keys())


# ===========================================================================
# TC-7: advance + rollback
# ===========================================================================


class TestAdvanceRollback:
    def _ready_ctrl(self) -> CanaryController:
        ctrl = CanaryController(CanaryConfig(min_requests_per_stage=3))
        ctrl.start()
        _fill_stage(ctrl, 0, n=3)
        return ctrl

    def test_tc7_advance_stage(self) -> None:
        """TC-7: advance() → current_stage=1."""
        ctrl = self._ready_ctrl()
        ctrl.advance()
        assert ctrl.state.current_stage == 1
        assert ctrl.state.total_promoted == 1

    def test_tc7_advance_full_pipeline(self) -> None:
        """TC-7b: 4단계 전체 advance → STAGE_3."""
        ctrl = CanaryController(CanaryConfig(min_requests_per_stage=1))
        ctrl.start()
        for stage in range(4):
            ctrl.record_request(stage, latency_ms=100.0, reward=0.90)
            if stage < 3:
                ctrl.advance()
        assert ctrl.state.current_stage == 3

    def test_tc7_advance_at_final_raises(self) -> None:
        """TC-7c: 최종 단계에서 advance() → ValueError."""
        ctrl = CanaryController(CanaryConfig(min_requests_per_stage=1))
        ctrl.start()
        for stage in range(3):
            ctrl.record_request(stage, latency_ms=100.0, reward=0.90)
            ctrl.advance()
        ctrl.record_request(3, latency_ms=100.0, reward=0.90)
        with pytest.raises(ValueError):
            ctrl.advance()

    def test_tc7_rollback(self) -> None:
        """TC-7d: rollback() → status=ROLLED_BACK."""
        ctrl = self._ready_ctrl()
        record = ctrl.rollback(reason="test_fail")
        assert ctrl.state.status == CanaryStatus.ROLLED_BACK
        assert ctrl.state.total_rolled_back == 1
        assert record.promoted is False
        assert record.to_stage == -1

    def test_tc7_complete(self) -> None:
        """TC-7e: complete() → status=COMPLETED."""
        ctrl = self._ready_ctrl()
        ctrl.complete()
        assert ctrl.state.status == CanaryStatus.COMPLETED


# ===========================================================================
# TC-8: summary
# ===========================================================================


class TestSummary:
    def test_tc8_summary_keys(self) -> None:
        """TC-8: summary() 필수 키 7개 확인."""
        ctrl = CanaryController()
        ctrl.start()
        s = ctrl.summary()
        required = {
            "model_id", "status", "current_stage", "current_traffic_pct",
            "total_promoted", "total_rolled_back", "stage_count",
        }
        assert required.issubset(s.keys())

    def test_tc8_summary_traffic_pct(self) -> None:
        """TC-8b: stage=0 → traffic_pct=5."""
        ctrl = CanaryController(CanaryConfig(min_requests_per_stage=1))
        ctrl.start()
        s = ctrl.summary()
        assert s["current_traffic_pct"] == 5


# ===========================================================================
# TC-9: ModelCard
# ===========================================================================


class TestModelCard:
    def test_tc9_defaults(self) -> None:
        """TC-9: ModelCard 기본값."""
        card = ModelCard()
        assert card.model_id == "default-model"
        assert card.gate_passed is False
        assert card.canary_stage == 0
        assert card.traffic_pct == 5

    def test_tc9_to_dict_keys(self) -> None:
        """TC-9b: to_dict() 필수 키 확인."""
        card = ModelCard()
        d = card.to_dict()
        required = {
            "model_id", "version", "framework", "training_method",
            "reward_threshold", "gate_passed", "canary_stage", "traffic_pct",
            "tags", "metadata",
        }
        assert required.issubset(d.keys())


# ===========================================================================
# TC-10: ModelServingEndpoint
# ===========================================================================


class TestModelServingEndpoint:
    def test_tc10_get_model_card_returns_dict(self) -> None:
        """TC-10: get_model_card() → dict 반환."""
        card = ModelCard(model_id="ppo-v1", gate_passed=True)
        ep = ModelServingEndpoint(card)
        result = ep.get_model_card()
        assert isinstance(result, dict)
        assert result["model_id"] == "ppo-v1"
        assert result["gate_passed"] is True

    def test_tc10_update_model_card(self) -> None:
        """TC-10b: update_model_card() 필드 갱신."""
        ep = ModelServingEndpoint()
        ep.update_model_card(canary_stage=2, traffic_pct=50, gate_passed=True)
        assert ep.model_card.canary_stage == 2
        assert ep.model_card.traffic_pct == 50
        assert ep.model_card.gate_passed is True

    def test_tc10_update_invalid_field_raises(self) -> None:
        """TC-10c: 존재하지 않는 필드 갱신 → AttributeError."""
        ep = ModelServingEndpoint()
        with pytest.raises(AttributeError):
            ep.update_model_card(nonexistent_field="x")

    def test_tc10_status_keys(self) -> None:
        """TC-10d: status() 필수 키 확인."""
        ep = ModelServingEndpoint()
        s = ep.status()
        required = {
            "model_id", "endpoint", "canary_stage", "traffic_pct",
            "gate_passed", "fastapi_available",
        }
        assert required.issubset(s.keys())

    def test_tc10_endpoint_config_defaults(self) -> None:
        """TC-10e: EndpointConfig 기본값."""
        cfg = EndpointConfig()
        assert cfg.host == "0.0.0.0"
        assert cfg.port == 8080
        assert cfg.prefix == "/api/v1"
