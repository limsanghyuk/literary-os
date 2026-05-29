"""
V451 — RealClaudeAdapter v3
Anthropic Claude API 실 연결 어댑터.
LLM-0 원칙: call_fn 주입으로 CI에서 실 API 호출 없음 보장.
"""
from __future__ import annotations

import os
import random
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

try:
    import tiktoken
    _TIKTOKEN_AVAILABLE = True
except ImportError:
    _TIKTOKEN_AVAILABLE = False


# ---------------------------------------------------------------------------
# 공유 응답 타입 (Phase 3 전용)
# ---------------------------------------------------------------------------

@dataclass
class RealLLMResponse:
    """Phase 3 실 LLM 호출 응답 타입."""
    text: str
    provider: str = "anthropic"
    input_tokens: int = 0
    output_tokens: int = 0
    tokens_used: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    call_id: str = ""
    retries: int = 0
    success: bool = True
    error: str = ""


@dataclass
class LiveAdapterCall:
    """단일 어댑터 호출 기록."""
    call_id: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float
    retries: int
    success: bool
    error: str = ""
    provider: str = "anthropic"


# ---------------------------------------------------------------------------
# 설정
# ---------------------------------------------------------------------------

@dataclass
class RealClaudeAdapterConfig:
    """RealClaudeAdapter 설정."""
    model: str = "claude-haiku-4-5-20251001"
    max_tokens: int = 4096
    max_retries: int = 5
    base_delay: float = 1.0
    max_delay: float = 32.0
    timeout_s: float = 30.0
    input_price_per_1k: float = 0.00025    # claude-haiku-4-5
    output_price_per_1k: float = 0.00125   # claude-haiku-4-5
    api_key_env: str = "ANTHROPIC_API_KEY"


# ---------------------------------------------------------------------------
# 유틸리티
# ---------------------------------------------------------------------------

def _count_tokens(text: str, model: str = "") -> int:
    """토큰 수 추정. tiktoken 우선, 미설치 시 len//4."""
    if _TIKTOKEN_AVAILABLE:
        try:
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except Exception:
            pass
    return max(1, len(text) // 4)


def _backoff_delay(attempt: int, base: float = 1.0, max_d: float = 32.0) -> float:
    """지수 백오프 + 랜덤 지터."""
    delay = min(base * (2 ** attempt), max_d)
    jitter = random.uniform(0, delay * 0.1)
    return delay + jitter


# ---------------------------------------------------------------------------
# 어댑터
# ---------------------------------------------------------------------------

class RealClaudeAdapter:
    """
    Anthropic Claude API 실 연결 어댑터 v3.

    Parameters
    ----------
    config : RealClaudeAdapterConfig, optional
    contract : LLMAdapterContract, optional — 기존 계약 객체 (미사용 시 None)
    call_fn : Callable, optional
        LLM-0 주입 함수. 시그니처:
        (messages, model, max_tokens, timeout) -> {"content": str, "input_tokens": int, "output_tokens": int}
        None 이면 실제 Anthropic SDK 호출 시도.
    tenant_id : str
        멀티테넌트 식별자.
    """

    def __init__(
        self,
        config: Optional[RealClaudeAdapterConfig] = None,
        contract=None,
        call_fn: Optional[Callable] = None,
        tenant_id: str = "default",
    ) -> None:
        self.config = config or RealClaudeAdapterConfig()
        self.contract = contract
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
        LLM 호출. ctx.extra["user_prompt"] 로 프롬프트 읽기.

        Parameters
        ----------
        ctx : LLMContext
        """
        user_prompt: str = (ctx.extra or {}).get("user_prompt", "")
        history: List[Dict] = (ctx.extra or {}).get("history", [])
        system_prompt: str = getattr(ctx, "system_prompt", "") or (ctx.extra or {}).get("system_prompt", "")

        model = self.config.model
        max_tokens = getattr(ctx, "max_tokens", None) or self.config.max_tokens
        timeout = getattr(ctx, "timeout", None) or self.config.timeout_s

        # 메시지 조립
        messages: List[Dict[str, str]] = list(history)
        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})

        call_id = str(uuid.uuid4())
        start_ms = time.monotonic() * 1000
        retries = 0
        last_error = ""

        for attempt in range(self.config.max_retries + 1):
            try:
                raw = self._do_call(messages, model, max_tokens, timeout, system_prompt)
                latency_ms = time.monotonic() * 1000 - start_ms

                in_tok = raw.get("input_tokens", _count_tokens(user_prompt, model))
                out_tok = raw.get("output_tokens", _count_tokens(raw.get("content", ""), model))
                cost = self._calc_cost(in_tok, out_tok)

                self._record(call_id, model, in_tok, out_tok, cost, latency_ms, retries, True)

                return RealLLMResponse(
                    text=raw.get("content", ""),
                    provider="anthropic",
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    tokens_used=in_tok + out_tok,
                    cost_usd=cost,
                    latency_ms=latency_ms,
                    call_id=call_id,
                    retries=retries,
                    success=True,
                )

            except Exception as exc:
                last_error = str(exc)
                retries += 1
                if attempt < self.config.max_retries:
                    time.sleep(_backoff_delay(attempt, self.config.base_delay, self.config.max_delay))

        # 모든 재시도 실패
        latency_ms = time.monotonic() * 1000 - start_ms
        self._record(call_id, model, 0, 0, 0.0, latency_ms, retries, False, last_error)
        return RealLLMResponse(
            text="",
            provider="anthropic",
            latency_ms=latency_ms,
            call_id=call_id,
            retries=retries,
            success=False,
            error=last_error,
        )

    def cost_estimate(self, ctx) -> float:
        """입력 토큰 기준 비용 사전 추정."""
        user_prompt = (ctx.extra or {}).get("user_prompt", "")
        in_tok = _count_tokens(user_prompt)
        out_tok_est = getattr(ctx, "max_tokens", self.config.max_tokens) // 2
        return self._calc_cost(in_tok, out_tok_est)

    def health_check(self) -> bool:
        """어댑터 상태 확인. call_fn 주입 시 항상 True."""
        if self._call_fn is not None:
            return True
        api_key = os.environ.get(self.config.api_key_env, "")
        return bool(api_key)

    def get_provider_name(self) -> str:
        return "anthropic"

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model": self.config.model,
            "provider": "anthropic",
            "version": "v3",
            "phase": "3-SP1",
            "max_tokens": self.config.max_tokens,
            "input_price_per_1k": self.config.input_price_per_1k,
            "output_price_per_1k": self.config.output_price_per_1k,
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

    def _do_call(
        self,
        messages: List[Dict],
        model: str,
        max_tokens: int,
        timeout: float,
        system_prompt: str = "",
    ) -> Dict[str, Any]:
        """실제 LLM 호출 (call_fn 주입 또는 SDK)."""
        if self._call_fn is not None:
            return self._call_fn(messages, model, max_tokens, timeout)

        # 실제 Anthropic SDK 호출
        try:
            import anthropic  # type: ignore
        except ImportError as exc:
            raise RuntimeError("anthropic SDK 미설치. pip install anthropic") from exc

        api_key = os.environ.get(self.config.api_key_env)
        if not api_key:
            raise RuntimeError(f"환경변수 {self.config.api_key_env} 미설정")

        client = anthropic.Anthropic(api_key=api_key)
        kwargs: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        resp = client.messages.create(**kwargs)
        content = resp.content[0].text if resp.content else ""
        return {
            "content": content,
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
        }

    def _calc_cost(self, input_tokens: int, output_tokens: int) -> float:
        cost = (
            input_tokens / 1000.0 * self.config.input_price_per_1k
            + output_tokens / 1000.0 * self.config.output_price_per_1k
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
            provider="anthropic",
        ))
