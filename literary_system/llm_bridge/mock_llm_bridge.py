"""
V411-A — MockLLMBridge (갱신)
V324 기반 + LLMContext 강타입 시그니처 적용.

변경: generate(prompt, context: dict) → generate(prompt, context: LLMContext|dict)
"""
from __future__ import annotations

from typing import List, Optional, Union

from literary_system.action_compiler.action_packet import ActionPacket, ActionPacketParser
from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface
from literary_system.llm_bridge.llm_context import LLMContext, coerce_context

_DEFAULT_RESPONSE = (
    '{"action": "MOVE", "source": "char_default", "target": "loc_default"}'
)


class MockLLMBridge(LLMBridgeInterface):
    """
    테스트 전용 LLM 브릿지.

    Args:
        scripted_response:  단일 고정 응답 문자열
        scripted_responses: 순서대로 반환할 응답 리스트 (소진 시 마지막 반복)
        scripted_packet:    parse_action_packet() 반환값 오버라이드
    """

    def __init__(
        self,
        scripted_response: str | None = None,
        scripted_responses: List[str] | None = None,
        scripted_packet: ActionPacket | None = None,
    ) -> None:
        self._responses: List[str] = []
        if scripted_responses:
            self._responses = list(scripted_responses)
        elif scripted_response is not None:
            self._responses = [scripted_response]
        else:
            self._responses = [_DEFAULT_RESPONSE]

        self._scripted_packet = scripted_packet
        self._parser = ActionPacketParser()
        self._call_count = 0

    # ── LLMBridgeInterface 구현 ─────────────────────────────────

    @property
    def provider_name(self) -> str:
        return "mock"

    def get_provider_id(self) -> str:
        return "mock"

    def is_available(self) -> bool:
        return True

    def generate(self, prompt: str, context: Union[LLMContext, dict] = None) -> str:
        """스크립트된 응답 반환. LLM 호출 없음 (LLM-0 원칙)."""
        # context 타입 정규화 (하위 호환)
        _ = coerce_context(context or {})
        idx = min(self._call_count, len(self._responses) - 1)
        self._call_count += 1
        return self._responses[idx]

    def parse_action_packet(self, raw: str) -> Optional[ActionPacket]:
        if self._scripted_packet is not None:
            return self._scripted_packet
        try:
            return self._parser.parse(raw)
        except Exception:
            return None

    # ── 테스트 유틸 ─────────────────────────────────────────────

    @property
    def call_count(self) -> int:
        return self._call_count

    def reset(self) -> None:
        self._call_count = 0

    def set_responses(self, responses: List[str]) -> None:
        self._responses = list(responses)
        self._call_count = 0
