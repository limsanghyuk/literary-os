"""
V432 -- LLM Adapter v2 Suite
AdapterContractV2 6-element standard applied to all three adapters.

Classes:
  ClaudeAdapterV2      -- Anthropic Claude + contract (retry/timeout/token/cost)
  OpenAIAdapterV2      -- OpenAI-compatible REST + contract
  OllamaAdapterV2      -- Local Ollama + circuit breaker + contract
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional, Union

from literary_system.llm_bridge.adapter_contract import (
    AdapterContractV2,
    RetryPolicy,
    execute_with_retry,
)
from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface
from literary_system.llm_bridge.llm_context import LLMContext, coerce_context

# ---------------------------------------------------------------------------
# 1. ClaudeAdapterV2
# ---------------------------------------------------------------------------

class ClaudeAdapterV2(LLMBridgeInterface):
    """
    V432 -- Anthropic Claude adapter with AdapterContractV2.

    generate() flow:
      1. resolve API key from contract.key
      2. count tokens; block if over budget
      3. call Anthropic API with contract timeout
      4. retry on transient errors per contract.retry
      5. validate response via contract.validation
      6. record cost to CostLedger if available
    """

    DEFAULT_MODEL = "claude-haiku-4-5-20251001"

    def __init__(
        self,
        contract: Optional[AdapterContractV2] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> None:
        self._contract = contract or AdapterContractV2.for_tier("speed")
        self._model = model or self.DEFAULT_MODEL
        self._system = system_prompt or (
            "You are a Korean literary writer. "
            "Generate a high-quality scene text based on the given context. "
            "You must call submit_scene_draft to submit the result."
        )
        self._last_response: Any = None
        self._call_count: int = 0
        self._circuit_open = False

        # V577 ADR-035 Deprecation 경고
        logging.getLogger(__name__).warning(
            "[DEPRECATED V577] ClaudeAdapterV2(G2)는 구세대 어댑터입니다. "
            "V578 이후 제거 예정. literary_system.llm_bridge.canonical_adapter."
            "make_canonical_claude() 사용을 권장합니다."
        )

        # Lazy Anthropic client
        self._client: Any = None
        self._anthropic_available = False
        try:
            import anthropic as _a
            self._client = _a.Anthropic(
                api_key=self._contract.key.resolve() or None
            )
            self._anthropic_available = True
        except (ImportError, Exception):
            pass

    # -- LLMBridgeInterface --------------------------------------------------

    @property
    def provider_name(self) -> str:
        return self._model

    def get_contract(self) -> AdapterContractV2:
        return self._contract

    def set_contract(self, contract: AdapterContractV2) -> None:
        self._contract = contract
        # Re-init client if key changed
        if self._anthropic_available:
            try:
                import anthropic as _a
                self._client = _a.Anthropic(
                    api_key=self._contract.key.resolve() or None
                )
            except Exception:
                self._client = None

    def is_available(self) -> bool:
        # Also require a non-empty API key to guard against no-key environments (Gate17)
        return (self._anthropic_available
                and self._client is not None
                and bool(self._contract.key.resolve()))

    def generate(self, prompt: str, context: Union[LLMContext, dict] = None) -> str:
        if not self._client:
            return ""

        # Token budget check
        estimated = self._contract.token.count_input_tokens(prompt)
        if self._contract.token.would_exceed(estimated):
            return ""

        contract = self._contract

        def _call() -> str:
            resp = self._client.messages.create(
                model=self._model,
                max_tokens=contract.token.max_output_tokens,
                system=self._system,
                messages=[{"role": "user", "content": prompt}],
                timeout=contract.timeout.read_timeout,
            )
            self._last_response = resp
            self._call_count += 1

            # Extract text
            text = ""
            if resp.content:
                for block in resp.content:
                    if hasattr(block, "text"):
                        text += block.text

            # Track token usage
            if hasattr(resp, "usage"):
                contract.token.record_usage(
                    resp.usage.input_tokens,
                    resp.usage.output_tokens,
                )

            return text

        try:
            text = execute_with_retry(_call, contract.retry)
        except Exception:
            return ""

        # Validate
        ok, _ = contract.validation.validate(text)
        if not ok:
            return ""

        return text

    def parse_action_packet(self, raw: str):
        try:
            from literary_system.llm_bridge.tool_use_parser import ToolUseParser
            parser = ToolUseParser()
            if self._last_response is not None:
                return parser.parse_raw_response(self._last_response)
            return parser._fallback_packet(raw)
        except Exception:
            return None

    def get_provider_id(self) -> str:
        return f"claude:{self._model}"


# ---------------------------------------------------------------------------
# 2. OpenAIAdapterV2
# ---------------------------------------------------------------------------

class OpenAIAdapterV2(LLMBridgeInterface):
    """
    V432 -- OpenAI-compatible REST adapter with AdapterContractV2.

    Supports: OpenAI, LM Studio, vLLM, and any /v1/chat/completions endpoint.
    Uses stdlib urllib only (no openai package required).
    """

    PRESET_BASE_URLS = {
        "openai": "https://api.openai.com/v1",
        "lmstudio": "http://localhost:1234/v1",
        "vllm": "http://localhost:8000/v1",
    }

    def __init__(
        self,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        contract: Optional[AdapterContractV2] = None,
        provider_id: str = "",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._contract = contract or AdapterContractV2.for_tier("speed")
        self._provider_id = provider_id or self._infer_provider_id(base_url)
        self._call_count = 0

    def _infer_provider_id(self, base_url: str) -> str:
        for name, url in self.PRESET_BASE_URLS.items():
            if url in base_url or name in base_url.lower():
                return name
        return "openai_compat"

    # -- LLMBridgeInterface --------------------------------------------------

    @property
    def provider_name(self) -> str:
        return self._model

    def get_provider_id(self) -> str:
        return f"{self._provider_id}:{self._model}"

    def get_contract(self) -> AdapterContractV2:
        return self._contract

    def set_contract(self, contract: AdapterContractV2) -> None:
        self._contract = contract

    def is_available(self) -> bool:
        import urllib.error
        import urllib.request
        try:
            url = f"{self._base_url}/models"
            api_key = self._contract.key.resolve() or "none"
            req = urllib.request.Request(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
            )
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status == 200
        except Exception:
            return False

    def generate(self, prompt: str, context: Union[LLMContext, dict] = None) -> str:
        import json
        import urllib.error
        import urllib.request

        # Token budget check
        estimated = self._contract.token.count_input_tokens(prompt)
        if self._contract.token.would_exceed(estimated):
            return ""

        contract = self._contract
        api_key = contract.key.resolve() or "none"
        url = f"{self._base_url}/chat/completions"

        payload = json.dumps({
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": contract.token.max_output_tokens,
            "temperature": 1.0,
        }).encode("utf-8")

        def _call() -> str:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=contract.timeout.read_timeout) as r:
                body = json.loads(r.read().decode("utf-8"))
            text = body["choices"][0]["message"]["content"]
            self._call_count += 1
            # Track usage if available
            if "usage" in body:
                contract.token.record_usage(
                    body["usage"].get("prompt_tokens", 0),
                    body["usage"].get("completion_tokens", 0),
                )
            return text

        try:
            text = execute_with_retry(_call, contract.retry)
        except Exception:
            return ""

        ok, _ = contract.validation.validate(text)
        if not ok:
            return ""
        return text

    def parse_action_packet(self, raw: str):
        return None  # OpenAI adapter does not use tool-use ActionPacket

    @classmethod
    def for_openai(cls, model: str = "gpt-4o-mini", contract: Optional[AdapterContractV2] = None) -> "OpenAIAdapterV2":
        return cls(
            base_url=cls.PRESET_BASE_URLS["openai"],
            model=model,
            contract=contract or AdapterContractV2.for_tier("speed"),
            provider_id="openai",
        )


# ---------------------------------------------------------------------------
# 3. OllamaAdapterV2
# ---------------------------------------------------------------------------

_CB_HALF_OPEN_AFTER: float = 60.0   # circuit breaker cool-down seconds


class CircuitBreakerState:
    """Simple 3-state circuit breaker: CLOSED / OPEN / HALF_OPEN."""

    CLOSED    = "closed"
    OPEN      = "open"
    HALF_OPEN = "half_open"

    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = _CB_HALF_OPEN_AFTER):
        self.state = self.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.last_failure_time: float = 0.0
        self.recovery_timeout = recovery_timeout

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = self.CLOSED

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if self.failure_count >= self.failure_threshold:
            self.state = self.OPEN

    def can_pass(self) -> bool:
        if self.state == self.CLOSED:
            return True
        if self.state == self.OPEN:
            elapsed = time.monotonic() - self.last_failure_time
            if elapsed >= self.recovery_timeout:
                self.state = self.HALF_OPEN
                return True
            return False
        # HALF_OPEN: allow one probe
        return True


class OllamaAdapterV2(LLMBridgeInterface):
    """
    V432 -- Ollama local adapter with AdapterContractV2 + Circuit Breaker.

    Circuit Breaker: 3 consecutive failures -> OPEN (60s cool-down).
    Fallback: empty string when circuit is OPEN.
    """

    DEFAULT_BASE_URL = "http://localhost:11434/v1"
    DEFAULT_MODEL    = "llama3.2"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        contract: Optional[AdapterContractV2] = None,
        cb_failure_threshold: int = 3,
    ) -> None:
        self._model    = model
        self._base_url = base_url.rstrip("/")
        self._contract = contract or AdapterContractV2.for_tier("local")
        self._cb       = CircuitBreakerState(
            failure_threshold=cb_failure_threshold,
            recovery_timeout=_CB_HALF_OPEN_AFTER,
        )
        self._call_count = 0

        # V577 ADR-035 Deprecation 경고
        logging.getLogger(__name__).warning(
            "[DEPRECATED V577] OllamaAdapterV2(G2)는 구세대 어댑터입니다. "
            "V578 이후 제거 예정. literary_system.llm_bridge.canonical_adapter."
            "make_canonical_ollama() 사용을 권장합니다."
        )

    # -- LLMBridgeInterface --------------------------------------------------

    @property
    def provider_name(self) -> str:
        return self._model

    def get_provider_id(self) -> str:
        return f"ollama:{self._model}"

    def get_contract(self) -> AdapterContractV2:
        return self._contract

    def set_contract(self, contract: AdapterContractV2) -> None:
        self._contract = contract

    def is_available(self) -> bool:
        if not self._cb.can_pass():
            return False
        import urllib.request
        try:
            with urllib.request.urlopen(
                f"{self._base_url}/models",
                timeout=5,
            ) as r:
                return r.status == 200
        except Exception:
            return False

    def generate(self, prompt: str, context: Union[LLMContext, dict] = None) -> str:
        if not self._cb.can_pass():
            return ""  # circuit open

        import json
        import urllib.request

        contract = self._contract

        estimated = contract.token.count_input_tokens(prompt)
        if contract.token.would_exceed(estimated):
            return ""

        url = f"{self._base_url}/chat/completions"
        payload = json.dumps({
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": contract.token.max_output_tokens,
        }).encode("utf-8")

        def _call() -> str:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer ollama",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=contract.timeout.read_timeout) as r:
                body = json.loads(r.read().decode("utf-8"))
            text = body["choices"][0]["message"]["content"]
            self._call_count += 1
            return text

        try:
            text = execute_with_retry(_call, contract.retry)
            self._cb.record_success()
        except Exception:
            self._cb.record_failure()
            return ""

        ok, _ = contract.validation.validate(text)
        if not ok:
            return ""
        return text

    def parse_action_packet(self, raw: str):
        return None

    @property
    def circuit_state(self) -> str:
        return self._cb.state
