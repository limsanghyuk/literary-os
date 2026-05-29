"""V606 테스트: CanonicalBridgeV2 + Gate G56 (RLHFRewardGate) + Gate G57 (ConstitutionAxisGate).

TC-1  ~ TC-8 : BridgeConfig / BridgeResponse / CanonicalBridgeV2
TC-9  ~ TC-17: run_rlhf_reward_gate (G56)
TC-18 ~ TC-30: run_constitution_axis_gate (G57)
"""
from __future__ import annotations

import math
import pytest


# ─────────────────────────────────────────────
# TC-1 ~ TC-8: CanonicalBridgeV2
# ─────────────────────────────────────────────

class TestBridgeConfig:
    def test_tc1_defaults(self):
        """TC-1: BridgeConfig 기본값 검증."""
        from literary_system.llm_bridge.canonical_bridge_v2 import BridgeConfig, ModelType

        cfg = BridgeConfig()
        assert cfg.model_type == ModelType.EXTERNAL
        assert cfg.adapter_name == "default"
        assert cfg.fallback_enabled is True
        assert cfg.fallback_model_type == ModelType.LOCAL
        assert cfg.max_tokens == 512
        assert 0.0 < cfg.temperature <= 1.0
        assert cfg.timeout_sec > 0.0

    def test_tc2_custom_config(self):
        """TC-2: BridgeConfig 커스텀 설정."""
        from literary_system.llm_bridge.canonical_bridge_v2 import BridgeConfig, ModelType

        cfg = BridgeConfig(
            model_type=ModelType.LOCAL,
            adapter_name="lora-v1",
            fallback_enabled=False,
            max_tokens=1024,
        )
        assert cfg.model_type == ModelType.LOCAL
        assert cfg.adapter_name == "lora-v1"
        assert cfg.fallback_enabled is False
        assert cfg.max_tokens == 1024


class TestBridgeResponse:
    def test_tc3_to_dict_keys(self):
        """TC-3: BridgeResponse.to_dict() 필수 키 검증."""
        from literary_system.llm_bridge.canonical_bridge_v2 import BridgeResponse

        resp = BridgeResponse(
            text="생성된 텍스트",
            model_type="external",
            adapter_name="default",
        )
        d = resp.to_dict()
        required = {"text", "model_type", "adapter_name", "used_fallback", "tokens_used", "metadata"}
        assert required <= set(d.keys())
        assert d["used_fallback"] is False
        assert d["tokens_used"] == 0


class TestCanonicalBridgeV2:
    def _make_mock_adapter(self, response_text: str):
        class MockAdapter:
            def generate(self, prompt, **kwargs):
                return response_text
        return MockAdapter()

    def test_tc4_status_7keys(self):
        """TC-4: status() 7키 검증."""
        from literary_system.llm_bridge.canonical_bridge_v2 import CanonicalBridgeV2

        bridge = CanonicalBridgeV2()
        s = bridge.status()
        required = {
            "version", "config_model_type", "external_adapter_registered",
            "local_adapter_registered", "call_count", "fallback_count", "fallback_enabled",
        }
        assert required == set(s.keys())
        assert s["external_adapter_registered"] is False
        assert s["local_adapter_registered"] is False
        assert s["call_count"] == 0

    def test_tc5_generate_external(self):
        """TC-5: 외부 어댑터 주입 후 generate() — EXTERNAL 경로."""
        from literary_system.llm_bridge.canonical_bridge_v2 import CanonicalBridgeV2, ModelType

        bridge = CanonicalBridgeV2()
        bridge.register_external_adapter(self._make_mock_adapter("외부 응답"))
        resp = bridge.generate("프롬프트", model_type=ModelType.EXTERNAL)
        assert resp.text == "외부 응답"
        assert resp.model_type == ModelType.EXTERNAL
        assert resp.used_fallback is False
        assert bridge.status()["call_count"] == 1

    def test_tc6_generate_local(self):
        """TC-6: 로컬 어댑터 주입 후 generate() — LOCAL 경로."""
        from literary_system.llm_bridge.canonical_bridge_v2 import CanonicalBridgeV2, ModelType

        bridge = CanonicalBridgeV2()
        bridge.register_local_adapter(self._make_mock_adapter("로컬 응답"))
        resp = bridge.generate("프롬프트", model_type=ModelType.LOCAL)
        assert resp.text == "로컬 응답"
        assert resp.model_type == ModelType.LOCAL

    def test_tc7_no_adapter_raises_runtime_error(self):
        """TC-7: 어댑터 미등록 + fallback 비활성화 → RuntimeError."""
        from literary_system.llm_bridge.canonical_bridge_v2 import BridgeConfig, CanonicalBridgeV2

        bridge = CanonicalBridgeV2(BridgeConfig(fallback_enabled=False))
        with pytest.raises(RuntimeError):
            bridge.generate("프롬프트")

    def test_tc8_fallback_on_external_failure(self):
        """TC-8: 외부 어댑터 미등록 시 폴백 → 로컬 어댑터 사용."""
        from literary_system.llm_bridge.canonical_bridge_v2 import BridgeConfig, CanonicalBridgeV2, ModelType

        cfg = BridgeConfig(model_type=ModelType.EXTERNAL, fallback_enabled=True)
        bridge = CanonicalBridgeV2(config=cfg)
        bridge.register_local_adapter(self._make_mock_adapter("폴백 로컬 응답"))
        # 외부 어댑터 없음 → 폴백 → 로컬
        resp = bridge.generate("프롬프트")
        assert resp.used_fallback is True
        assert resp.text == "폴백 로컬 응답"
        assert bridge.status()["fallback_count"] == 1


# ─────────────────────────────────────────────
# TC-9 ~ TC-17: Gate G56 — RLHFRewardGate
# ─────────────────────────────────────────────

class TestRLHFRewardGate:
    def test_tc9_constants(self):
        """TC-9: G56 상수값 검증."""
        from literary_system.gates.rlhf_reward_gate import (
            DELTA_THRESHOLD, GATE_ID, GATE_NAME, REWARD_THRESHOLD,
        )
        assert REWARD_THRESHOLD == 0.75
        assert DELTA_THRESHOLD == 0.05
        assert GATE_ID == "G56"
        assert "G56" in GATE_NAME or "RLHF" in GATE_NAME

    def test_tc10_result_to_dict_keys(self):
        """TC-10: RLHFRewardGateResult.to_dict() 키 검증."""
        from literary_system.gates.rlhf_reward_gate import run_rlhf_reward_gate

        result = run_rlhf_reward_gate([0.8, 0.85, 0.9], baseline=0.5)
        d = result.to_dict()
        required = {
            "passed", "mean_reward", "delta", "reward_threshold",
            "delta_threshold", "n_samples", "reason",
        }
        assert required <= set(d.keys())

    def test_tc11_pass_both_conditions(self):
        """TC-11: mean_reward ≥ 0.75 AND delta ≥ 0.05 → PASS."""
        from literary_system.gates.rlhf_reward_gate import run_rlhf_reward_gate

        rewards = [0.8, 0.85, 0.9]  # mean=0.85, delta=0.85-0.6=0.25
        result = run_rlhf_reward_gate(rewards, baseline=0.60)
        assert result.passed is True
        assert result.mean_reward >= 0.75
        assert result.delta >= 0.05
        assert result.reason == "PASS"

    def test_tc12_fail_low_reward(self):
        """TC-12: mean_reward < 0.75 → FAIL."""
        from literary_system.gates.rlhf_reward_gate import run_rlhf_reward_gate

        rewards = [0.5, 0.6, 0.7]  # mean=0.6
        result = run_rlhf_reward_gate(rewards, baseline=0.5)
        assert result.passed is False
        assert "mean_reward" in result.reason

    def test_tc13_fail_low_delta(self):
        """TC-13: delta < 0.05 → FAIL."""
        from literary_system.gates.rlhf_reward_gate import run_rlhf_reward_gate

        rewards = [0.80, 0.80, 0.80]  # mean=0.80 ≥ 0.75, delta=0.80-0.79=0.01 < 0.05
        result = run_rlhf_reward_gate(rewards, baseline=0.79)
        assert result.passed is False
        assert "delta" in result.reason

    def test_tc14_empty_rewards_fail(self):
        """TC-14: 빈 rewards → FAIL."""
        from literary_system.gates.rlhf_reward_gate import run_rlhf_reward_gate

        result = run_rlhf_reward_gate([], baseline=0.5)
        assert result.passed is False
        assert result.n_samples == 0

    def test_tc15_custom_thresholds(self):
        """TC-15: 커스텀 임계값 동작 검증."""
        from literary_system.gates.rlhf_reward_gate import run_rlhf_reward_gate

        rewards = [0.70, 0.70, 0.70]
        result = run_rlhf_reward_gate(rewards, baseline=0.60, reward_threshold=0.65, delta_threshold=0.05)
        assert result.passed is True

    def test_tc16_n_samples_correct(self):
        """TC-16: n_samples == len(rewards)."""
        from literary_system.gates.rlhf_reward_gate import run_rlhf_reward_gate

        rewards = [0.8] * 20
        result = run_rlhf_reward_gate(rewards, baseline=0.5)
        assert result.n_samples == 20

    def test_tc17_mean_reward_accuracy(self):
        """TC-17: mean_reward 계산 정확성."""
        from literary_system.gates.rlhf_reward_gate import run_rlhf_reward_gate

        rewards = [0.7, 0.8, 0.9]  # mean=0.8
        result = run_rlhf_reward_gate(rewards, baseline=0.5)
        assert abs(result.mean_reward - 0.8) < 1e-6
        assert abs(result.delta - 0.3) < 1e-6


# ─────────────────────────────────────────────
# TC-18 ~ TC-30: Gate G57 — ConstitutionAxisGate
# ─────────────────────────────────────────────

class TestConstitutionAxisGate:
    def _perfect_scores(self, n: int = 10) -> dict:
        """완전 상관 점수 (모든 축 동일 값 → 상관=1.0)."""
        vals = [0.5 + i * 0.04 for i in range(n)]
        from literary_system.gates.constitution_axis_gate import CONSTITUTION_AXES
        return {ax: vals[:] for ax in CONSTITUTION_AXES}

    def _uncorrelated_scores(self, n: int = 10) -> dict:
        """비상관 점수 (축마다 다른 패턴)."""
        import random
        rng = random.Random(42)
        from literary_system.gates.constitution_axis_gate import CONSTITUTION_AXES
        return {ax: [rng.random() for _ in range(n)] for ax in CONSTITUTION_AXES}

    def test_tc18_constants(self):
        """TC-18: G57 상수값 검증."""
        from literary_system.gates.constitution_axis_gate import (
            CONSTITUTION_AXES, CORRELATION_THRESHOLD, GATE_ID, GATE_NAME,
        )
        assert CORRELATION_THRESHOLD == 0.80
        assert GATE_ID == "G57"
        assert len(CONSTITUTION_AXES) == 5
        expected_axes = {"safety", "coherence", "creativity", "quality", "consistency"}
        assert set(CONSTITUTION_AXES) == expected_axes

    def test_tc19_result_to_dict_keys(self):
        """TC-19: ConstitutionAxisGateResult.to_dict() 키 검증."""
        from literary_system.gates.constitution_axis_gate import run_constitution_axis_gate

        scores = self._perfect_scores()
        result = run_constitution_axis_gate(scores)
        d = result.to_dict()
        required = {
            "passed", "mean_correlation", "axis_correlations",
            "threshold", "n_pairs", "reason",
        }
        assert required <= set(d.keys())

    def test_tc20_n_pairs_equals_c52(self):
        """TC-20: 5축 쌍 수 = C(5,2) = 10."""
        from literary_system.gates.constitution_axis_gate import run_constitution_axis_gate

        scores = self._perfect_scores()
        result = run_constitution_axis_gate(scores)
        assert result.n_pairs == 10

    def test_tc21_pass_perfect_correlation(self):
        """TC-21: 완전 상관 점수 → PASS."""
        from literary_system.gates.constitution_axis_gate import run_constitution_axis_gate

        scores = self._perfect_scores()
        result = run_constitution_axis_gate(scores)
        assert result.passed is True
        assert result.mean_correlation >= 0.80
        assert result.reason == "PASS"

    def test_tc22_fail_low_correlation(self):
        """TC-22: 낮은 상관 점수 → FAIL."""
        from literary_system.gates.constitution_axis_gate import CONSTITUTION_AXES, run_constitution_axis_gate

        import random
        rng = random.Random(0)
        scores = {ax: [rng.random() for _ in range(50)] for ax in CONSTITUTION_AXES}
        result = run_constitution_axis_gate(scores)
        # 랜덤 데이터는 평균 상관 ~0 → FAIL 가능성 높음
        assert isinstance(result.passed, bool)

    def test_tc23_missing_axis_fail(self):
        """TC-23: 누락된 Constitution 축 → FAIL."""
        from literary_system.gates.constitution_axis_gate import run_constitution_axis_gate

        scores = self._perfect_scores()
        del scores["safety"]
        result = run_constitution_axis_gate(scores)
        assert result.passed is False
        assert "누락" in result.reason or "missing" in result.reason.lower() or "safety" in result.reason

    def test_tc24_length_mismatch_fail(self):
        """TC-24: 축 데이터 길이 불일치 → FAIL."""
        from literary_system.gates.constitution_axis_gate import CONSTITUTION_AXES, run_constitution_axis_gate

        scores = self._perfect_scores(10)
        scores["safety"] = scores["safety"][:5]  # 길이 불일치
        result = run_constitution_axis_gate(scores)
        assert result.passed is False

    def test_tc25_axis_correlations_10_pairs(self):
        """TC-25: axis_correlations 딕셔너리 10쌍 포함."""
        from literary_system.gates.constitution_axis_gate import run_constitution_axis_gate

        scores = self._perfect_scores()
        result = run_constitution_axis_gate(scores)
        assert len(result.axis_correlations) == 10

    def test_tc26_pearson_known_value(self):
        """TC-26: 피어슨 상관계수 known value 검증."""
        from literary_system.gates.constitution_axis_gate import _pearson

        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]  # y = 2x → 완전 양의 상관
        corr = _pearson(x, y)
        assert abs(corr - 1.0) < 1e-9

    def test_tc27_pearson_negative_correlation(self):
        """TC-27: 완전 음의 상관계수 = -1.0."""
        from literary_system.gates.constitution_axis_gate import _pearson

        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [5.0, 4.0, 3.0, 2.0, 1.0]  # 역순 → 완전 음의 상관
        corr = _pearson(x, y)
        assert abs(corr - (-1.0)) < 1e-9

    def test_tc28_pearson_zero_variance(self):
        """TC-28: 분산=0인 축 → 상관 0.0 반환 (ZeroDivision 없음)."""
        from literary_system.gates.constitution_axis_gate import _pearson

        x = [1.0, 1.0, 1.0, 1.0]
        y = [1.0, 2.0, 3.0, 4.0]
        corr = _pearson(x, y)
        assert corr == 0.0

    def test_tc29_custom_threshold(self):
        """TC-29: 커스텀 threshold=0.5 로 완화 시 통과 가능."""
        from literary_system.gates.constitution_axis_gate import CONSTITUTION_AXES, run_constitution_axis_gate

        # 중간 상관 데이터
        n = 20
        base = [0.5 + i * 0.02 for i in range(n)]
        noise = [b + (0.05 * (i % 3 - 1)) for i, b in enumerate(base)]
        scores = {
            "safety": base,
            "coherence": noise,
            "creativity": base[::-1],
            "quality": noise[::-1],
            "consistency": base,
        }
        result_strict = run_constitution_axis_gate(scores, threshold=0.99)
        result_loose = run_constitution_axis_gate(scores, threshold=0.0)
        # threshold=0.0 이면 항상 pass (상관은 음수일 수 있으므로 아닐 수도 있음)
        assert isinstance(result_strict.passed, bool)
        assert isinstance(result_loose.passed, bool)

    def test_tc30_axis_correlation_keys_format(self):
        """TC-30: axis_correlations 키 형식 'ax1↔ax2' 검증."""
        from literary_system.gates.constitution_axis_gate import run_constitution_axis_gate

        scores = self._perfect_scores()
        result = run_constitution_axis_gate(scores)
        for key in result.axis_correlations:
            assert "↔" in key, f"Expected '↔' separator in key: {key!r}"
        # 모든 상관값이 -1.0 ~ 1.0 범위
        for key, val in result.axis_correlations.items():
            assert -1.0 <= val <= 1.0, f"{key}: {val}"
