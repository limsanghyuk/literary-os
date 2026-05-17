"""
V431 — LLMAdapterContract v2 테스트
ADR-004 6요소 표준 계약 검증.

테스트 항목:
  1. KeyConfig — resolve(), from_env(), from_direct(), is_set
  2. RetryPolicy — delay_for_attempt(), should_retry(), retry_budget_id
  3. execute_with_retry() — 성공 / 재시도 소진 / retryable 예외
  4. TimeoutConfig — for_tier(), total
  5. TokenBudget — count_input_tokens(), would_exceed(), record_usage()
  6. ResponseValidator — validate() 정상/빈/길이/키워드
  7. CostConfig — is_over_daily(), is_over_monthly()
  8. AdapterContractV2 — for_tier() 3개 티어, to_dict(), validate_response()
  9. LLMBridgeInterface — get_contract() / set_contract() 기본 동작 (하위 호환)
"""
from __future__ import annotations

import os
import pytest


# ─────────────────────────────────────────────────────────────────────────────
# 1. KeyConfig
# ─────────────────────────────────────────────────────────────────────────────

class TestKeyConfig:
    def test_from_direct_resolves(self):
        from literary_system.llm_bridge.adapter_contract import KeyConfig
        kc = KeyConfig.from_direct("sk-test-key")
        assert kc.resolve() == "sk-test-key"
        assert kc.is_set is True

    def test_from_env_resolves(self, monkeypatch):
        from literary_system.llm_bridge.adapter_contract import KeyConfig
        monkeypatch.setenv("TEST_API_KEY_V431", "env-value")
        kc = KeyConfig.from_env("TEST_API_KEY_V431")
        assert kc.resolve() == "env-value"
        assert kc.is_set is True

    def test_missing_env_returns_empty(self, monkeypatch):
        from literary_system.llm_bridge.adapter_contract import KeyConfig
        monkeypatch.delenv("MISSING_KEY_V431", raising=False)
        kc = KeyConfig.from_env("MISSING_KEY_V431")
        assert kc.resolve() == ""
        assert kc.is_set is False

    def test_direct_overrides_env(self, monkeypatch):
        from literary_system.llm_bridge.adapter_contract import KeyConfig
        monkeypatch.setenv("TEST_API_KEY_V431", "env-value")
        kc = KeyConfig(env_var="TEST_API_KEY_V431", _direct_key="direct-value")
        assert kc.resolve() == "direct-value"

    def test_repr_hides_direct_key(self):
        from literary_system.llm_bridge.adapter_contract import KeyConfig
        kc = KeyConfig.from_direct("secret-key-123")
        assert "secret-key-123" not in repr(kc)


# ─────────────────────────────────────────────────────────────────────────────
# 2. RetryPolicy
# ─────────────────────────────────────────────────────────────────────────────

class TestRetryPolicy:
    def test_delay_grows_exponentially(self):
        from literary_system.llm_bridge.adapter_contract import RetryPolicy
        policy = RetryPolicy(base_delay=1.0, backoff_factor=2.0, jitter=False)
        assert policy.delay_for_attempt(0) == 1.0
        assert policy.delay_for_attempt(1) == 2.0
        assert policy.delay_for_attempt(2) == 4.0

    def test_delay_capped_at_max(self):
        from literary_system.llm_bridge.adapter_contract import RetryPolicy
        policy = RetryPolicy(base_delay=1.0, backoff_factor=10.0, max_delay=5.0, jitter=False)
        assert policy.delay_for_attempt(3) <= 5.0

    def test_should_retry_within_max(self):
        from literary_system.llm_bridge.adapter_contract import RetryPolicy
        policy = RetryPolicy(max_attempts=3, retryable_exceptions=[])
        assert policy.should_retry(0, Exception("err")) is True
        assert policy.should_retry(1, Exception("err")) is True
        assert policy.should_retry(2, Exception("err")) is False  # max-1

    def test_should_not_retry_non_retryable(self):
        from literary_system.llm_bridge.adapter_contract import RetryPolicy
        policy = RetryPolicy(max_attempts=3, retryable_exceptions=["RateLimitError"])
        err = ValueError("not retryable")
        assert policy.should_retry(0, err) is False

    def test_retry_budget_id_field(self):
        from literary_system.llm_bridge.adapter_contract import RetryPolicy
        policy = RetryPolicy(retry_budget_id="budget-001")
        assert policy.retry_budget_id == "budget-001"

    def test_default_retry_budget_id_empty(self):
        from literary_system.llm_bridge.adapter_contract import RetryPolicy
        policy = RetryPolicy()
        assert policy.retry_budget_id == ""


# ─────────────────────────────────────────────────────────────────────────────
# 3. execute_with_retry
# ─────────────────────────────────────────────────────────────────────────────

class TestExecuteWithRetry:
    def test_success_on_first_attempt(self):
        from literary_system.llm_bridge.adapter_contract import execute_with_retry, RetryPolicy
        policy = RetryPolicy(max_attempts=3, base_delay=0.001, jitter=False)
        result = execute_with_retry(lambda: "ok", policy)
        assert result == "ok"

    def test_retries_until_success(self):
        from literary_system.llm_bridge.adapter_contract import execute_with_retry, RetryPolicy
        calls = []

        def flaky():
            calls.append(1)
            if len(calls) < 3:
                raise ConnectionError("flaky")
            return "recovered"

        policy = RetryPolicy(max_attempts=3, base_delay=0.001, jitter=False,
                             retryable_exceptions=["ConnectionError"])
        result = execute_with_retry(flaky, policy)
        assert result == "recovered"
        assert len(calls) == 3

    def test_raises_after_max_attempts(self):
        from literary_system.llm_bridge.adapter_contract import execute_with_retry, RetryPolicy
        policy = RetryPolicy(max_attempts=2, base_delay=0.001, jitter=False,
                             retryable_exceptions=[])

        with pytest.raises(RuntimeError, match="always fails"):
            execute_with_retry(lambda: (_ for _ in ()).throw(RuntimeError("always fails")), policy)

    def test_non_retryable_raises_immediately(self):
        from literary_system.llm_bridge.adapter_contract import execute_with_retry, RetryPolicy
        calls = []

        def raises_value_error():
            calls.append(1)
            raise ValueError("not retryable")

        policy = RetryPolicy(max_attempts=5, base_delay=0.001, jitter=False,
                             retryable_exceptions=["RateLimitError"])

        with pytest.raises(ValueError):
            execute_with_retry(raises_value_error, policy)
        assert len(calls) == 1  # 즉시 중단


# ─────────────────────────────────────────────────────────────────────────────
# 4. TimeoutConfig
# ─────────────────────────────────────────────────────────────────────────────

class TestTimeoutConfig:
    def test_total_property(self):
        from literary_system.llm_bridge.adapter_contract import TimeoutConfig
        tc = TimeoutConfig(connect_timeout=5.0, read_timeout=20.0)
        assert tc.total == 25.0

    def test_for_tier_local(self):
        from literary_system.llm_bridge.adapter_contract import TimeoutConfig
        tc = TimeoutConfig.for_tier("local")
        assert tc.read_timeout >= 60.0  # 로컬은 느림

    def test_for_tier_speed(self):
        from literary_system.llm_bridge.adapter_contract import TimeoutConfig
        tc = TimeoutConfig.for_tier("speed")
        assert tc.read_timeout <= 60.0

    def test_for_tier_quality(self):
        from literary_system.llm_bridge.adapter_contract import TimeoutConfig
        tc = TimeoutConfig.for_tier("quality")
        assert 30.0 <= tc.read_timeout <= 120.0

    def test_unknown_tier_returns_default(self):
        from literary_system.llm_bridge.adapter_contract import TimeoutConfig
        tc = TimeoutConfig.for_tier("unknown_tier")
        assert isinstance(tc, TimeoutConfig)


# ─────────────────────────────────────────────────────────────────────────────
# 5. TokenBudget
# ─────────────────────────────────────────────────────────────────────────────

class TestTokenBudget:
    def test_count_input_tokens_non_empty(self):
        from literary_system.llm_bridge.adapter_contract import TokenBudget
        tb = TokenBudget()
        count = tb.count_input_tokens("안녕하세요 세계")
        assert count > 0

    def test_would_exceed_true(self):
        from literary_system.llm_bridge.adapter_contract import TokenBudget
        tb = TokenBudget(max_input_tokens=100)
        assert tb.would_exceed(101) is True

    def test_would_exceed_false(self):
        from literary_system.llm_bridge.adapter_contract import TokenBudget
        tb = TokenBudget(max_input_tokens=100)
        assert tb.would_exceed(100) is False

    def test_record_usage_accumulates(self):
        from literary_system.llm_bridge.adapter_contract import TokenBudget
        tb = TokenBudget()
        tb.record_usage(100, 50)
        tb.record_usage(200, 100)
        d = tb.to_dict()
        assert d["input_used"] == 300
        assert d["output_used"] == 150

    def test_to_dict_structure(self):
        from literary_system.llm_bridge.adapter_contract import TokenBudget
        tb = TokenBudget(max_input_tokens=4096, max_output_tokens=1024)
        d = tb.to_dict()
        assert "max_input_tokens" in d
        assert "max_output_tokens" in d
        assert d["max_input_tokens"] == 4096


# ─────────────────────────────────────────────────────────────────────────────
# 6. ResponseValidator
# ─────────────────────────────────────────────────────────────────────────────

class TestResponseValidator:
    def test_valid_response(self):
        from literary_system.llm_bridge.adapter_contract import ResponseValidator
        rv = ResponseValidator()
        ok, reason = rv.validate("정상 응답입니다.")
        assert ok is True
        assert reason == ""

    def test_empty_response_rejected(self):
        from literary_system.llm_bridge.adapter_contract import ResponseValidator
        rv = ResponseValidator(allow_empty=False)
        ok, reason = rv.validate("")
        assert ok is False
        assert "빈 응답" in reason

    def test_empty_response_allowed(self):
        from literary_system.llm_bridge.adapter_contract import ResponseValidator
        rv = ResponseValidator(allow_empty=True, min_length=0)
        ok, _ = rv.validate("")
        assert ok is True

    def test_too_short_rejected(self):
        from literary_system.llm_bridge.adapter_contract import ResponseValidator
        rv = ResponseValidator(min_length=10)
        ok, reason = rv.validate("짧음")
        assert ok is False
        assert "길이 부족" in reason

    def test_too_long_rejected(self):
        from literary_system.llm_bridge.adapter_contract import ResponseValidator
        rv = ResponseValidator(max_length=5)
        ok, reason = rv.validate("이것은 너무 긴 응답입니다")
        assert ok is False
        assert "길이 초과" in reason

    def test_safety_keyword_rejected(self):
        from literary_system.llm_bridge.adapter_contract import ResponseValidator
        rv = ResponseValidator(safety_keywords=["BLOCKED_WORD"])
        ok, reason = rv.validate("여기에 BLOCKED_WORD 가 있습니다")
        assert ok is False
        assert "BLOCKED_WORD" in reason

    def test_safety_keyword_case_insensitive(self):
        from literary_system.llm_bridge.adapter_contract import ResponseValidator
        rv = ResponseValidator(safety_keywords=["DANGER"])
        ok, _ = rv.validate("danger word included")
        assert ok is False


# ─────────────────────────────────────────────────────────────────────────────
# 7. CostConfig
# ─────────────────────────────────────────────────────────────────────────────

class TestCostConfig:
    def test_not_over_daily(self):
        from literary_system.llm_bridge.adapter_contract import CostConfig
        cc = CostConfig(daily_budget_usd=10.0)
        assert cc.is_over_daily(5.0) is False

    def test_over_daily(self):
        from literary_system.llm_bridge.adapter_contract import CostConfig
        cc = CostConfig(daily_budget_usd=10.0)
        assert cc.is_over_daily(10.0) is True

    def test_over_monthly(self):
        from literary_system.llm_bridge.adapter_contract import CostConfig
        cc = CostConfig(monthly_budget_usd=100.0)
        assert cc.is_over_monthly(150.0) is True

    def test_disabled_never_over(self):
        from literary_system.llm_bridge.adapter_contract import CostConfig
        cc = CostConfig(enabled=False, daily_budget_usd=0.0)
        assert cc.is_over_daily(999.0) is False
        assert cc.is_over_monthly(999.0) is False


# ─────────────────────────────────────────────────────────────────────────────
# 8. AdapterContractV2
# ─────────────────────────────────────────────────────────────────────────────

class TestAdapterContractV2:
    def test_for_tier_local(self):
        from literary_system.llm_bridge.adapter_contract import AdapterContractV2
        c = AdapterContractV2.for_tier("local")
        assert c.tier == "local"
        assert c.cost.enabled is False
        assert c.timeout.read_timeout >= 60.0

    def test_for_tier_speed(self):
        from literary_system.llm_bridge.adapter_contract import AdapterContractV2
        c = AdapterContractV2.for_tier("speed")
        assert c.tier == "speed"
        assert c.cost.enabled is True
        assert c.retry.max_attempts >= 2

    def test_for_tier_quality(self):
        from literary_system.llm_bridge.adapter_contract import AdapterContractV2
        c = AdapterContractV2.for_tier("quality")
        assert c.tier == "quality"
        assert c.token.max_input_tokens > 8192

    def test_for_tier_unknown_defaults_to_speed(self):
        from literary_system.llm_bridge.adapter_contract import AdapterContractV2
        c = AdapterContractV2.for_tier("nonexistent")
        assert isinstance(c, AdapterContractV2)

    def test_for_tier_kwargs_override(self):
        from literary_system.llm_bridge.adapter_contract import AdapterContractV2, KeyConfig
        c = AdapterContractV2.for_tier("speed", adapter_id="test-adapter", model_id="claude-haiku-4-5")
        assert c.adapter_id == "test-adapter"
        assert c.model_id == "claude-haiku-4-5"

    def test_to_dict_structure(self):
        from literary_system.llm_bridge.adapter_contract import AdapterContractV2
        c = AdapterContractV2.for_tier("speed", adapter_id="dict-test")
        d = c.to_dict()
        assert "adapter_id" in d
        assert "model_id" in d
        assert "tier" in d
        assert "key_set" in d
        assert "retry" in d
        assert "timeout" in d
        assert "token" in d
        assert "cost_enabled" in d
        assert d["retry"]["retry_budget_id"] == ""  # v4 보강 필드

    def test_validate_response_delegates(self):
        from literary_system.llm_bridge.adapter_contract import AdapterContractV2
        c = AdapterContractV2.for_tier("speed")
        ok, _ = c.validate_response("정상 응답")
        assert ok is True

    def test_validate_response_empty_fails(self):
        from literary_system.llm_bridge.adapter_contract import AdapterContractV2
        c = AdapterContractV2.for_tier("speed")
        ok, reason = c.validate_response("")
        assert ok is False

    def test_resolve_api_key_delegates(self):
        from literary_system.llm_bridge.adapter_contract import AdapterContractV2, KeyConfig
        c = AdapterContractV2.for_tier("speed")
        c.key = KeyConfig.from_direct("test-key")
        assert c.resolve_api_key() == "test-key"

    def test_all_six_elements_present(self):
        from literary_system.llm_bridge.adapter_contract import (
            AdapterContractV2, KeyConfig, RetryPolicy, TimeoutConfig,
            TokenBudget, ResponseValidator, CostConfig,
        )
        c = AdapterContractV2.for_tier("quality")
        assert isinstance(c.key,        KeyConfig)
        assert isinstance(c.retry,      RetryPolicy)
        assert isinstance(c.timeout,    TimeoutConfig)
        assert isinstance(c.token,      TokenBudget)
        assert isinstance(c.validation, ResponseValidator)
        assert isinstance(c.cost,       CostConfig)


# ─────────────────────────────────────────────────────────────────────────────
# 9. LLMBridgeInterface v2 — get_contract / set_contract 하위 호환
# ─────────────────────────────────────────────────────────────────────────────

class TestLLMBridgeInterfaceV431:
    """
    V431 인터페이스 확장 검증.
    기존 어댑터(하위 호환)에서 get_contract()는 None을 반환해야 한다.
    """

    def _make_minimal_adapter(self):
        """테스트용 최소 구현체."""
        from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface

        class MinimalAdapter(LLMBridgeInterface):
            @property
            def provider_name(self) -> str:
                return "minimal"

            def generate(self, prompt, context):
                return "ok"

            def parse_action_packet(self, raw):
                return None

        return MinimalAdapter()

    def test_get_contract_default_none(self):
        adapter = self._make_minimal_adapter()
        assert adapter.get_contract() is None

    def test_set_contract_default_noop(self):
        from literary_system.llm_bridge.adapter_contract import AdapterContractV2
        adapter = self._make_minimal_adapter()
        contract = AdapterContractV2.for_tier("speed")
        # 기본 구현은 무시 — 예외 없이 실행되어야 함
        adapter.set_contract(contract)
        assert adapter.get_contract() is None  # 여전히 None

    def test_v431_adapter_can_store_contract(self):
        """V431+ 어댑터는 계약을 저장하고 반환할 수 있어야 한다."""
        from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface
        from literary_system.llm_bridge.adapter_contract import AdapterContractV2

        class V431Adapter(LLMBridgeInterface):
            def __init__(self, contract: AdapterContractV2):
                self._contract = contract

            @property
            def provider_name(self) -> str:
                return "v431"

            def generate(self, prompt, context):
                return "v431 response"

            def parse_action_packet(self, raw):
                return None

            def get_contract(self):
                return self._contract

            def set_contract(self, contract):
                self._contract = contract

        contract = AdapterContractV2.for_tier("quality")
        adapter = V431Adapter(contract=contract)
        assert adapter.get_contract() is contract
        assert adapter.get_contract().tier == "quality"

        new_contract = AdapterContractV2.for_tier("speed")
        adapter.set_contract(new_contract)
        assert adapter.get_contract().tier == "speed"
