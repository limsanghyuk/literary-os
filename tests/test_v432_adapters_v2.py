"""
V432 -- adapters_v2 test suite
ClaudeAdapterV2 / OpenAIAdapterV2 / OllamaAdapterV2 + CircuitBreakerState

All tests: LLM-0 compliant (no real API calls).
Network calls are replaced with mock urllib or direct attribute inspection.
"""
from __future__ import annotations

import json
import time
import urllib.error
from io import BytesIO
from unittest.mock import patch, MagicMock
import pytest

from literary_system.llm_bridge.adapter_contract import (
    AdapterContractV2,
    KeyConfig,
    RetryPolicy,
    TokenBudget,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_openai_response(text: str, prompt_tokens: int = 10, completion_tokens: int = 20) -> bytes:
    return json.dumps({
        "choices": [{"message": {"content": text}}],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
    }).encode("utf-8")


# ---------------------------------------------------------------------------
# CircuitBreakerState
# ---------------------------------------------------------------------------

class TestCircuitBreakerState:
    def test_initial_state_closed(self):
        from literary_system.llm_bridge.adapters_v2 import CircuitBreakerState
        cb = CircuitBreakerState(failure_threshold=3)
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.can_pass() is True

    def test_opens_after_threshold(self):
        from literary_system.llm_bridge.adapters_v2 import CircuitBreakerState
        cb = CircuitBreakerState(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitBreakerState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        assert cb.can_pass() is False

    def test_half_open_after_recovery_timeout(self):
        from literary_system.llm_bridge.adapters_v2 import CircuitBreakerState
        cb = CircuitBreakerState(failure_threshold=1, recovery_timeout=0.01)
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        time.sleep(0.02)
        assert cb.can_pass() is True
        assert cb.state == CircuitBreakerState.HALF_OPEN

    def test_closed_after_success(self):
        from literary_system.llm_bridge.adapters_v2 import CircuitBreakerState
        cb = CircuitBreakerState(failure_threshold=1, recovery_timeout=0.0)
        cb.record_failure()
        cb.record_success()
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0


# ---------------------------------------------------------------------------
# ClaudeAdapterV2
# ---------------------------------------------------------------------------

class TestClaudeAdapterV2:
    def _make_adapter(self, tier: str = "speed") -> object:
        from literary_system.llm_bridge.adapters_v2 import ClaudeAdapterV2
        contract = AdapterContractV2.for_tier(tier)
        contract.key = KeyConfig.from_direct("sk-test-v432")
        adapter = ClaudeAdapterV2(contract=contract)
        return adapter

    def test_provider_name_is_model(self):
        adapter = self._make_adapter()
        assert adapter.provider_name is not None
        assert len(adapter.provider_name) > 0

    def test_get_contract_returns_contract(self):
        adapter = self._make_adapter()
        c = adapter.get_contract()
        assert c is not None
        assert c.tier == "speed"

    def test_set_contract_updates(self):
        from literary_system.llm_bridge.adapters_v2 import ClaudeAdapterV2
        adapter = self._make_adapter("speed")
        new_contract = AdapterContractV2.for_tier("quality")
        adapter.set_contract(new_contract)
        assert adapter.get_contract().tier == "quality"

    def test_generate_returns_empty_when_unavailable(self):
        from literary_system.llm_bridge.adapters_v2 import ClaudeAdapterV2
        contract = AdapterContractV2.for_tier("speed")
        adapter = ClaudeAdapterV2(contract=contract)
        adapter._client = None
        result = adapter.generate("test prompt")
        assert result == ""

    def test_token_budget_exceeded_returns_empty(self):
        from literary_system.llm_bridge.adapters_v2 import ClaudeAdapterV2
        contract = AdapterContractV2.for_tier("speed")
        contract.token = TokenBudget(max_input_tokens=1)  # 1 token limit
        adapter = ClaudeAdapterV2(contract=contract)
        # Manually set client to non-None so it passes client check
        adapter._client = MagicMock()
        result = adapter.generate("This is a prompt with many tokens that will exceed the limit")
        assert result == ""

    def test_generate_with_mock_client(self):
        from literary_system.llm_bridge.adapters_v2 import ClaudeAdapterV2
        contract = AdapterContractV2.for_tier("speed")
        contract.retry = RetryPolicy(max_attempts=1, base_delay=0.001, jitter=False)
        adapter = ClaudeAdapterV2(contract=contract)

        mock_block = MagicMock()
        mock_block.text = "Generated scene text"
        mock_resp = MagicMock()
        mock_resp.content = [mock_block]
        mock_resp.usage.input_tokens = 10
        mock_resp.usage.output_tokens = 30

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_resp
        adapter._client = mock_client
        adapter._anthropic_available = True

        result = adapter.generate("Write a scene")
        assert result == "Generated scene text"
        assert adapter._call_count == 1

    def test_generate_retries_on_exception(self):
        from literary_system.llm_bridge.adapters_v2 import ClaudeAdapterV2
        contract = AdapterContractV2.for_tier("speed")
        contract.retry = RetryPolicy(
            max_attempts=3, base_delay=0.001, jitter=False,
            retryable_exceptions=["ConnectionError"]
        )
        adapter = ClaudeAdapterV2(contract=contract)

        call_count = []
        def side_effect(**kwargs):
            call_count.append(1)
            if len(call_count) < 3:
                raise ConnectionError("flaky")
            mock_block = MagicMock()
            mock_block.text = "recovered"
            mock_resp = MagicMock()
            mock_resp.content = [mock_block]
            mock_resp.usage.input_tokens = 5
            mock_resp.usage.output_tokens = 10
            return mock_resp

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = side_effect
        adapter._client = mock_client

        result = adapter.generate("prompt")
        assert result == "recovered"
        assert len(call_count) == 3

    def test_validation_rejects_empty_response(self):
        from literary_system.llm_bridge.adapters_v2 import ClaudeAdapterV2
        contract = AdapterContractV2.for_tier("speed")
        contract.retry = RetryPolicy(max_attempts=1, base_delay=0.001, jitter=False)
        adapter = ClaudeAdapterV2(contract=contract)

        mock_block = MagicMock()
        mock_block.text = ""   # empty
        mock_resp = MagicMock()
        mock_resp.content = [mock_block]
        mock_resp.usage.input_tokens = 5
        mock_resp.usage.output_tokens = 0
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_resp
        adapter._client = mock_client

        result = adapter.generate("prompt")
        assert result == ""

    def test_is_available_false_when_no_client(self):
        from literary_system.llm_bridge.adapters_v2 import ClaudeAdapterV2
        adapter = ClaudeAdapterV2()
        adapter._client = None
        adapter._anthropic_available = False
        assert adapter.is_available() is False

    def test_get_provider_id_format(self):
        from literary_system.llm_bridge.adapters_v2 import ClaudeAdapterV2
        adapter = ClaudeAdapterV2(model="claude-haiku-4-5-20251001")
        assert "claude" in adapter.get_provider_id()


# ---------------------------------------------------------------------------
# OpenAIAdapterV2
# ---------------------------------------------------------------------------

class TestOpenAIAdapterV2:
    def _make_adapter(self, tier: str = "speed") -> object:
        from literary_system.llm_bridge.adapters_v2 import OpenAIAdapterV2
        contract = AdapterContractV2.for_tier(tier)
        contract.key = KeyConfig.from_direct("sk-test-openai")
        return OpenAIAdapterV2(
            base_url="https://api.openai.com/v1",
            model="gpt-4o-mini",
            contract=contract,
            provider_id="openai",
        )

    def test_provider_name_is_model(self):
        adapter = self._make_adapter()
        assert adapter.provider_name == "gpt-4o-mini"

    def test_get_provider_id_includes_provider(self):
        adapter = self._make_adapter()
        assert "openai" in adapter.get_provider_id()

    def test_get_contract(self):
        adapter = self._make_adapter()
        assert adapter.get_contract().tier == "speed"

    def test_set_contract(self):
        adapter = self._make_adapter()
        new_contract = AdapterContractV2.for_tier("quality")
        adapter.set_contract(new_contract)
        assert adapter.get_contract().tier == "quality"

    def test_generate_with_mock_urlopen(self):
        from literary_system.llm_bridge.adapters_v2 import OpenAIAdapterV2
        contract = AdapterContractV2.for_tier("speed")
        contract.retry = RetryPolicy(max_attempts=1, base_delay=0.001, jitter=False)
        adapter = OpenAIAdapterV2(
            base_url="https://api.openai.com/v1",
            model="gpt-4o-mini",
            contract=contract,
        )

        mock_resp_data = _mock_openai_response("OpenAI generated text")

        class _FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def read(self): return mock_resp_data
            status = 200

        with patch("urllib.request.urlopen", return_value=_FakeResponse()):
            result = adapter.generate("Write something")

        assert result == "OpenAI generated text"
        assert adapter._call_count == 1

    def test_generate_returns_empty_on_network_error(self):
        from literary_system.llm_bridge.adapters_v2 import OpenAIAdapterV2
        contract = AdapterContractV2.for_tier("speed")
        contract.retry = RetryPolicy(
            max_attempts=1, base_delay=0.001, jitter=False,
            retryable_exceptions=[]
        )
        adapter = OpenAIAdapterV2(contract=contract)

        with patch("urllib.request.urlopen", side_effect=Exception("network error")):
            result = adapter.generate("prompt")

        assert result == ""

    def test_for_openai_factory(self):
        from literary_system.llm_bridge.adapters_v2 import OpenAIAdapterV2
        contract = AdapterContractV2.for_tier("speed")
        adapter = OpenAIAdapterV2.for_openai(model="gpt-4o", contract=contract)
        assert adapter.provider_name == "gpt-4o"
        assert "openai" in adapter.get_provider_id()

    def test_token_budget_exceeded_returns_empty(self):
        from literary_system.llm_bridge.adapters_v2 import OpenAIAdapterV2
        contract = AdapterContractV2.for_tier("speed")
        contract.token = TokenBudget(max_input_tokens=1)
        adapter = OpenAIAdapterV2(contract=contract)
        result = adapter.generate("a" * 100)
        assert result == ""


# ---------------------------------------------------------------------------
# OllamaAdapterV2
# ---------------------------------------------------------------------------

class TestOllamaAdapterV2:
    def _make_adapter(self) -> object:
        from literary_system.llm_bridge.adapters_v2 import OllamaAdapterV2
        contract = AdapterContractV2.for_tier("local")
        return OllamaAdapterV2(
            model="llama3.2",
            base_url="http://localhost:11434/v1",
            contract=contract,
            cb_failure_threshold=3,
        )

    def test_provider_name_is_model(self):
        adapter = self._make_adapter()
        assert adapter.provider_name == "llama3.2"

    def test_get_provider_id_format(self):
        adapter = self._make_adapter()
        assert "ollama" in adapter.get_provider_id()

    def test_initial_circuit_state_closed(self):
        adapter = self._make_adapter()
        assert adapter.circuit_state == "closed"

    def test_circuit_opens_after_failures(self):
        from literary_system.llm_bridge.adapters_v2 import OllamaAdapterV2
        contract = AdapterContractV2.for_tier("local")
        contract.retry = RetryPolicy(max_attempts=1, base_delay=0.001, jitter=False)
        adapter = OllamaAdapterV2(contract=contract, cb_failure_threshold=3)

        with patch("urllib.request.urlopen", side_effect=Exception("offline")):
            adapter.generate("p1")
            adapter.generate("p2")
            adapter.generate("p3")

        assert adapter.circuit_state == "open"

    def test_generate_empty_when_circuit_open(self):
        from literary_system.llm_bridge.adapters_v2 import OllamaAdapterV2
        contract = AdapterContractV2.for_tier("local")
        contract.retry = RetryPolicy(max_attempts=1, base_delay=0.001, jitter=False)
        adapter = OllamaAdapterV2(contract=contract, cb_failure_threshold=1)

        with patch("urllib.request.urlopen", side_effect=Exception("offline")):
            adapter.generate("first call")  # opens circuit

        assert adapter.circuit_state == "open"
        result = adapter.generate("second call")  # should be blocked
        assert result == ""

    def test_circuit_resets_after_success(self):
        from literary_system.llm_bridge.adapters_v2 import OllamaAdapterV2
        contract = AdapterContractV2.for_tier("local")
        contract.retry = RetryPolicy(max_attempts=1, base_delay=0.001, jitter=False)
        adapter = OllamaAdapterV2(contract=contract, cb_failure_threshold=2)

        # 1 failure (not yet open)
        with patch("urllib.request.urlopen", side_effect=Exception("err")):
            adapter.generate("fail1")

        mock_resp = _mock_openai_response("success text")

        class _FakeResp:
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def read(self): return mock_resp
            status = 200

        with patch("urllib.request.urlopen", return_value=_FakeResp()):
            result = adapter.generate("success call")

        assert result == "success text"
        assert adapter.circuit_state == "closed"

    def test_get_contract(self):
        adapter = self._make_adapter()
        assert adapter.get_contract().tier == "local"

    def test_set_contract(self):
        from literary_system.llm_bridge.adapters_v2 import OllamaAdapterV2
        adapter = self._make_adapter()
        new = AdapterContractV2.for_tier("speed")
        adapter.set_contract(new)
        assert adapter.get_contract().tier == "speed"

    def test_token_budget_exceeded(self):
        from literary_system.llm_bridge.adapters_v2 import OllamaAdapterV2
        contract = AdapterContractV2.for_tier("local")
        contract.token = TokenBudget(max_input_tokens=1)
        adapter = OllamaAdapterV2(contract=contract)
        result = adapter.generate("a" * 100)
        assert result == ""


# ---------------------------------------------------------------------------
# Interface compliance check: all v2 adapters implement get/set_contract
# ---------------------------------------------------------------------------

class TestV2ContractCompliance:
    def test_all_adapters_have_get_contract(self):
        from literary_system.llm_bridge.adapters_v2 import (
            ClaudeAdapterV2, OpenAIAdapterV2, OllamaAdapterV2,
        )
        for cls in [ClaudeAdapterV2, OpenAIAdapterV2, OllamaAdapterV2]:
            assert hasattr(cls, "get_contract")
            assert hasattr(cls, "set_contract")

    def test_all_adapters_return_contract_v2_instance(self):
        from literary_system.llm_bridge.adapters_v2 import (
            ClaudeAdapterV2, OpenAIAdapterV2, OllamaAdapterV2,
        )
        contract = AdapterContractV2.for_tier("speed")
        adapters = [
            ClaudeAdapterV2(contract=contract),
            OpenAIAdapterV2(contract=contract),
            OllamaAdapterV2(contract=contract),
        ]
        for adapter in adapters:
            c = adapter.get_contract()
            assert isinstance(c, AdapterContractV2), f"{type(adapter).__name__} failed"

    def test_all_adapters_implement_llm_bridge_interface(self):
        from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface
        from literary_system.llm_bridge.adapters_v2 import (
            ClaudeAdapterV2, OpenAIAdapterV2, OllamaAdapterV2,
        )
        for cls in [ClaudeAdapterV2, OpenAIAdapterV2, OllamaAdapterV2]:
            assert issubclass(cls, LLMBridgeInterface), f"{cls.__name__} not subclass"
