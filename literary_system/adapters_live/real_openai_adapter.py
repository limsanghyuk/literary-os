"""
V452 — RealOpenAIAdapter
OpenAI API 실 연결 어댑터 (gpt-4o / gpt-4o-mini).
LLM-0 원칙: call_fn 주입으로 CI에서 실 API 호출 없음 보장.
function_calling 패스스루, 스트리밍 지원.
"""
from __future__ import annotations

import os
import time
import uuid
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from literary_system.adapters_live.real_claude_adapter import (
    RealLLMResponse,
    LiveAdapterCall,
    _count_tokens,
    _backoff_delay,
)


# ---------------------------------------------------------------------------
# 설정
# ---------------------------------------------------------------------------

@dataclass
class RealOpenAIAdapterConfig:
    """RealOpenAIAdapter 설정."""
    model: str = "gpt-4o-mini"
    max_tokens: int = 4096
    max_retries: int = 5
    base_delay: float = 1.0
    max_delay: float = 32.0
    timeout_s: float = 30.0
    # gpt-4o-mini 기본 가격
    input_price_per_1k: float = 0.000150
    output_price_per_1k: float = 0.000600
    api_key_env: str = "OPENAI_API_KEY"

    SUPPORTED_MODELS = frozenset({"gpt-4o", "gpt-4o-mini"})

    def price_for_model(self, model: str):
        """모델별 입출력 가격 반환 (input_per_1k, output_per_1k)."""
        prices = {
            "gpt-4o":      (0.002500, 0.010000),
            "gpt-4o-mini": (0.000150, 0.000600),
        }
        return prices.get(model, (self.input_price_per_1k, self.output_price_per_1k))


# ---------------------------------------------------------------------------
# 어댑터
# ---------------------------------------------------------------------------

class RealOpenAIAdapter:
    """
    OpenAI API 실 연결 어댑터 (V452).

    Parameters
    ----------
    config : RealOpenAIAdapterConfig, optional
    call_fn : Callable, optional
        LLM-0 주입 함수. 시그니처: (**kwargs) → dict
        kwargs keys: messages, model, max_tokens, timeout, tools, tool_choice, stream
        반환: {"content": str, "input_tokens": int, "output_tokens": int,
               "tool_calls": list|None}
    tenant_id : str
    """

    def __init__(
        self,
        config: Optional[RealOpenAIAdapterConfig] = None,
        call_fn: Optional[Callable] = None,
        tenant_id: str = "default",
    ) -> None:
        self.config = config or RealOpenAIAdapterConfig()
        self._call_fn = call_fn
        self.tenant_id = tenant_id

        # 통계
        self._total_calls: int = 0
        self._total_input_tokens: int = 0
        self._total_output_tokens: int = 0
        self._total_cost_usd: float = 0.0
        self._total_latency_ms: float = 0.0
        self._error_count: int = 0
        self._call_log: List[LiveAdapterCall] = []

    # ------------------------------------------------------------------
    # 핵심 인터페이스
    # ------------------------------------------------------------------

    def call(self, ctx) -> RealLLMResponse:
        """
        LLM 호출.

        ctx.extra 키:
          - user_prompt  : str  (필수)
          - history      : list (선택)
          - tools        : list (function_calling)
          - tool_choice  : str|dict (function_calling)
          - stream       : bool (스트리밍)
        """
        extra = ctx.extra or {}
        user_prompt: str = extra.get("user_prompt", "")
        history: List[Dict] = extra.get("history", [])
        tools = extra.get("tools")
        tool_choice = extra.get("tool_choice")
        stream: bool = extra.get("stream", False)

        model = self.config.model
        max_tokens = getattr(ctx, "max_tokens", None) or self.config.max_tokens
        timeout = getattr(ctx, "timeout", None) or self.config.timeout_s

        messages: List[Dict] = list(history)
        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})

        call_id = str(uuid.uuid4())
        start_ms = time.monotonic() * 1000
        retries = 0
        last_error = ""

        call_kwargs: Dict[str, Any] = {
            "messages": messages,
            "model": model,
            "max_tokens": max_tokens,
            "timeout": timeout,
        }
        if tools:
            call_kwargs["tools"] = tools
        if tool_choice:
            call_kwargs["tool_choice"] = tool_choice
        if stream:
            call_kwargs["stream"] = True

        for attempt in range(self.config.max_retries + 1):
            try:
                raw = self._do_call(**call_kwargs)
                latency_ms = time.monotonic() * 1000 - start_ms

                in_tok = raw.get("input_tokens", _count_tokens(user_prompt, model))
                out_tok = raw.get("output_tokens", _count_tokens(raw.get("content", ""), model))
                cost = self._calc_cost(model, in_tok, out_tok)

                self._record(call_id, model, in_tok, out_tok, cost, latency_ms, retries, True)

                resp = RealLLMResponse(
                    text=raw.get("content", ""),
                    provider="openai",
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    tokens_used=in_tok + out_tok,
                    cost_usd=cost,
                    latency_ms=latency_ms,
                    call_id=call_id,
                    retries=retries,
                    success=True,
                )
                # function_calling 결과 첨부
                if raw.get("tool_calls"):
                    resp.text = raw.get("content") or ""
                    resp.__dict__["tool_calls"] = raw["tool_calls"]
                return resp

            except Exception as exc:
                last_error = str(exc)
                retries += 1
                if attempt < self.config.max_retries:
                    time.sleep(_backoff_delay(attempt, self.config.base_delay, self.config.max_delay))

        latency_ms = time.monotonic() * 1000 - start_ms
        self._record(call_id, model, 0, 0, 0.0, latency_ms, retries, False, last_error)
        return RealLLMResponse(
            text="",
            provider="openai",
            latency_ms=latency_ms,
            call_id=call_id,
            retries=retries,
            success=False,
            error=last_error,
        )

    def cost_estimate(self, ctx) -> float:
        user_prompt = (ctx.extra or {}).get("user_prompt", "")
        in_tok = _count_tokens(user_prompt)
        out_tok_est = getattr(ctx, "max_tokens", self.config.max_tokens) // 2
        return self._calc_cost(self.config.model, in_tok, out_tok_est)

    def health_check(self) -> bool:
        if self._call_fn is not None:
            return True
        api_key = os.environ.get(self.config.api_key_env, "")
        return bool(api_key)

    def get_provider_name(self) -> str:
        return "openai"

    def get_model_info(self) -> Dict[str, Any]:
        inp, out = self.config.price_for_model(self.config.model)
        return {
            "model": self.config.model,
            "provider": "openai",
            "version": "v1",
            "phase": "3-SP1",
            "max_tokens": self.config.max_tokens,
            "input_price_per_1k": inp,
            "output_price_per_1k": out,
            "supported_models": sorted(self.config.SUPPORTED_MODELS),
        }

    def get_rate_limits(self) -> Dict[str, Any]:
        return {
            "max_retries": self.config.max_retries,
            "base_delay": self.config.base_delay,
            "max_delay": self.config.max_delay,
            "timeout_s": self.config.timeout_s,
        }

    def stats(self) -> Dict[str, Any]:
        calls = self._total_calls
        avg_latency = self._total_latency_ms / calls if calls else 0.0
        return {
            "total_calls": calls,
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_cost_usd": round(self._total_cost_usd, 6),
            "avg_latency_ms": round(avg_latency, 2),
            "error_count": self._error_count,
            "tenant_id": self.tenant_id,
        }

    def reset_stats(self) -> None:
        self._total_calls = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cost_usd = 0.0
        self._total_latency_ms = 0.0
        self._error_count = 0
        self._call_log.clear()

    # ------------------------------------------------------------------
    # 내부
    # ------------------------------------------------------------------

    def _do_call(self, **kwargs) -> Dict[str, Any]:
        """실제 LLM 호출 (call_fn 주입 또는 OpenAI SDK)."""
        if self._call_fn is not None:
            return self._call_fn(**kwargs)

        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:
            raise RuntimeError("openai SDK 미설치. pip install openai") from exc

        api_key = os.environ.get(self.config.api_key_env)
        if not api_key:
            raise RuntimeError(f"환경변수 {self.config.api_key_env} 미설정")

        client = OpenAI(api_key=api_key)
        stream = kwargs.pop("stream", False)
        timeout = kwargs.pop("timeout", self.config.timeout_s)

        if stream:
            return self._call_streaming({**kwargs, "stream": True}, client, timeout)

        resp = client.chat.completions.create(timeout=timeout, **kwargs)
        return self._normalize_response(resp)

    def _call_streaming(self, kwargs: Dict, client=None, timeout: float = 30.0) -> Dict[str, Any]:
        """스트리밍 호출 — 청크 결합 후 단일 텍스트 반환."""
        if self._call_fn is not None:
            return self._call_fn(**kwargs)

        chunks = []
        with client.chat.completions.create(timeout=timeout, **kwargs) as stream:
            for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    chunks.append(delta.content)
        full_text = "".join(chunks)
        return {
            "content": full_text,
            "input_tokens": _count_tokens(kwargs.get("messages", [{}])[-1].get("content", ""), kwargs.get("model", "")),
            "output_tokens": _count_tokens(full_text, kwargs.get("model", "")),
            "tool_calls": None,
        }

    def _normalize_response(self, resp) -> Dict[str, Any]:
        choice = resp.choices[0] if resp.choices else None
        content = ""
        tool_calls = None
        if choice:
            msg = choice.message
            content = msg.content or ""
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_calls = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ]
        usage = resp.usage if hasattr(resp, "usage") and resp.usage else None
        return {
            "content": content,
            "input_tokens": usage.prompt_tokens if usage else 0,
            "output_tokens": usage.completion_tokens if usage else 0,
            "tool_calls": tool_calls,
        }

    def _calc_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        inp_price, out_price = self.config.price_for_model(model)
        cost = (
            input_tokens / 1000.0 * inp_price
            + output_tokens / 1000.0 * out_price
        )
        return round(cost, 8)

    def _record(
        self,
        call_id: str,
        model: str,
        in_tok: int,
        out_tok: int,
        cost: float,
        latency_ms: float,
        retries: int,
        success: bool,
        error: str = "",
    ) -> None:
        self._total_calls += 1
        self._total_input_tokens += in_tok
        self._total_output_tokens += out_tok
        self._total_cost_usd += cost
        self._total_latency_ms += latency_ms
        if not success:
            self._error_count += 1
        self._call_log.append(LiveAdapterCall(
            call_id=call_id,
            model=model,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=cost,
            latency_ms=latency_ms,
            retries=retries,
            success=success,
            error=error,
            provider="openai",
        ))
