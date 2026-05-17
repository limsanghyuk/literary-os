"""
V431 — LLMBridgeInterface (갱신)
V411 기반 + AdapterContractV2 수용 인터페이스 추가.

변경 이력:
  V411: generate() 시그니처 LLMContext 강타입 계약, is_available(), get_provider_id()
  V431: get_contract() 선택적 메서드 추가 (ADR-004 계약 조회)
        set_contract() 선택적 메서드 추가 (런타임 계약 교체)
        하위 호환 유지: get_contract() 기본 반환값 None
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Union, Optional, TYPE_CHECKING

from literary_system.llm_bridge.llm_context import LLMContext, LLMResponse, coerce_context

if TYPE_CHECKING:
    from literary_system.llm_bridge.adapter_contract import AdapterContractV2


class LLMBridgeInterface(ABC):
    """
    LLM 프로바이더 추상 기반 클래스.
    모든 구체 구현체는 이 인터페이스를 상속해야 한다.

    V411 강화 계약:
      - generate(prompt, context: LLMContext) -> str
      - is_available() -> bool
      - get_provider_id() -> str
    V431 확장:
      - get_contract() -> Optional[AdapterContractV2]
      - set_contract(contract) -> None
    """

    @abstractmethod
    def generate(self, prompt: str, context: Union[LLMContext, dict]) -> str:
        """LLM에 프롬프트를 전송하고 텍스트 응답을 반환한다."""

    @abstractmethod
    def parse_action_packet(self, raw: str):
        """LLM 원시 출력 -> ActionPacket 변환."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """프로바이더 식별자 ('claude', 'ollama', 'mock' 등)."""

    def is_available(self) -> bool:
        """프로바이더 가용성 확인. 기본값 True."""
        return True

    def get_provider_id(self) -> str:
        """프로바이더 고유 식별자 반환. 기본값: provider_name."""
        return self.provider_name

    # ── V431: AdapterContractV2 수용 인터페이스 ───────────────────────────────

    def get_contract(self) -> "Optional[AdapterContractV2]":
        """
        어댑터 현재 계약(AdapterContractV2) 반환.
        V431 이전 어댑터(하위 호환): None.
        V431+ 어댑터: 실제 계약 인스턴스.
        """
        return None

    def set_contract(self, contract: "AdapterContractV2") -> None:
        """
        런타임 계약 교체.
        V431+ 어댑터에서 재정의. 기본 구현은 무시(하위 호환).
        """
        pass

    # ── 편의 메서드 (구체 클래스에서 재정의 불필요) ───────────────────────────

    def generate_with_response(
        self, prompt: str, context: Union[LLMContext, dict]
    ) -> LLMResponse:
        """generate()를 호출하고 LLMResponse 래퍼로 반환."""
        import time
        ctx = coerce_context(context)
        t0 = time.monotonic()
        text = self.generate(prompt, ctx)
        latency = (time.monotonic() - t0) * 1000.0
        return LLMResponse(
            text=text,
            provider_id=self.get_provider_id(),
            latency_ms=round(latency, 2),
        )
