"""
V577 — CanonicalLLMBridge
ADR-035: G3 어댑터(adapters_live/)를 LLMBridgeInterface 계약으로 래핑하는 캐노니컬 어댑터.

설계 원칙:
  - G3(adapters_live/) 어댑터는 .call(ctx) -> RealLLMResponse 인터페이스를 사용
  - LLMBridgeInterface는 .generate(prompt, ctx) -> str 계약을 요구
  - 본 모듈이 두 인터페이스 간의 단일 어댑터 계층을 제공 (Adapter Pattern)
  - LLM-0 원칙: 외부 LLM 호출은 call_fn 주입으로만 허용 (CI 환경 보호)
  - G1/G2 어댑터는 Deprecation 경고 발생 후 V578 이후 제거 예정

사용 예시:
    from literary_system.adapters_live import RealClaudeAdapter
    from literary_system.llm_bridge.canonical_adapter import CanonicalLLMBridge

    g3 = RealClaudeAdapter(call_fn=mock_fn)
    bridge = CanonicalLLMBridge(g3, provider_id="claude")
    text = bridge.generate("안녕하세요", ctx)
"""
from __future__ import annotations

import logging
from typing import Any, Optional, Union

from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface
from literary_system.llm_bridge.llm_context import LLMContext, coerce_context

logger = logging.getLogger(__name__)


class CanonicalLLMBridge(LLMBridgeInterface):
    """
    G3 어댑터를 LLMBridgeInterface 계약으로 감싸는 캐노니컬 어댑터.

    Parameters
    ----------
    g3_adapter : G3 어댑터 인스턴스
        RealClaudeAdapter | RealOpenAIAdapter | RealOllamaAdapter
    provider_id : str, optional
        명시적 provider ID. 미입력 시 g3_adapter.get_provider_name() 사용.

    Notes
    -----
    generate(prompt, ctx) 호출 시:
      1. ctx.extra["user_prompt"] = prompt 주입
      2. g3_adapter.call(ctx) 호출
      3. response.text 반환
    """

    def __init__(
        self,
        g3_adapter: Any,
        provider_id: str = "",
    ) -> None:
        self._g3 = g3_adapter
        self._provider_id = provider_id or getattr(g3_adapter, "get_provider_name", lambda: "canonical")()

    # ------------------------------------------------------------------
    # LLMBridgeInterface 필수 구현
    # ------------------------------------------------------------------

    def generate(self, prompt: str, context: Union[LLMContext, dict]) -> str:
        """프롬프트를 G3 어댑터로 전달하고 텍스트 응답 반환."""
        ctx = coerce_context(context)
        if ctx.extra is None:
            ctx.extra = {}
        ctx.extra["user_prompt"] = prompt
        try:
            response = self._g3.call(ctx)
            return response.text
        except Exception as exc:
            logger.error(
                "CanonicalLLMBridge.generate 실패 [provider=%s]: %s",
                self._provider_id, exc,
            )
            return ""

    def parse_action_packet(self, raw: str):
        """LLM 원시 출력 -> ActionPacket 변환. G3 위임 또는 None."""
        if hasattr(self._g3, "parse_action_packet"):
            return self._g3.parse_action_packet(raw)
        return None

    @property
    def provider_name(self) -> str:
        return self._provider_id

    def is_available(self) -> bool:
        try:
            if hasattr(self._g3, "health_check"):
                return self._g3.health_check()
            return True
        except Exception:
            return False

    def get_provider_id(self) -> str:
        return self._provider_id

    # ------------------------------------------------------------------
    # 추가 편의 메서드
    # ------------------------------------------------------------------

    def get_g3_adapter(self) -> Any:
        """내부 G3 어댑터 직접 접근 (테스트 목적)."""
        return self._g3

    def cost_estimate(self, prompt: str, context: Union[LLMContext, dict] = None) -> float:
        """G3 어댑터 cost_estimate 위임."""
        if hasattr(self._g3, "cost_estimate") and context is not None:
            ctx = coerce_context(context)
            try:
                return self._g3.cost_estimate(ctx)
            except Exception:
                pass
        return 0.0


# ---------------------------------------------------------------------------
# 팩토리 함수
# ---------------------------------------------------------------------------

def make_canonical_claude(
    model: str = "claude-haiku-4-5-20251001",
    call_fn=None,
    tenant_id: str = "default",
) -> CanonicalLLMBridge:
    """RealClaudeAdapter 기반 캐노니컬 브릿지 생성. LLM-0: call_fn 주입."""
    from literary_system.adapters_live.real_claude_adapter import (
        RealClaudeAdapter,
        RealClaudeAdapterConfig,
    )
    config = RealClaudeAdapterConfig(model=model)
    g3 = RealClaudeAdapter(config=config, call_fn=call_fn, tenant_id=tenant_id)
    return CanonicalLLMBridge(g3, provider_id=f"claude/{model}")


def make_canonical_ollama(
    model: str = "llama3",
    base_url: str = "http://localhost:11434",
    call_fn=None,
) -> CanonicalLLMBridge:
    """RealOllamaAdapter 기반 캐노니컬 브릿지 생성. LLM-0: call_fn 주입."""
    from literary_system.adapters_live.real_ollama_adapter import (
        RealOllamaAdapter,
        RealOllamaAdapterConfig,
    )
    config = RealOllamaAdapterConfig(model=model, base_url=base_url)
    g3 = RealOllamaAdapter(config=config, call_fn=call_fn)
    return CanonicalLLMBridge(g3, provider_id=f"ollama/{model}")


def make_canonical_openai(
    model: str = "gpt-4o-mini",
    call_fn=None,
    tenant_id: str = "default",
) -> CanonicalLLMBridge:
    """RealOpenAIAdapter 기반 캐노니컬 브릿지 생성. LLM-0: call_fn 주입."""
    from literary_system.adapters_live.real_openai_adapter import (
        RealOpenAIAdapter,
        RealOpenAIAdapterConfig,
    )
    config = RealOpenAIAdapterConfig(model=model)
    g3 = RealOpenAIAdapter(config=config, call_fn=call_fn, tenant_id=tenant_id)
    return CanonicalLLMBridge(g3, provider_id=f"openai/{model}")
