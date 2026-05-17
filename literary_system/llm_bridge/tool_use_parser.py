"""
V325 - ToolUseParser  (Phase 1)
Anthropic tool_use 응답 블록 → ActionPacket 변환.

설계 원칙 (P2 외과적 통합):
  - ClaudeAdapter.parse_action_packet()에서 호출
  - tool_use 블록의 input 딕셔너리를 ActionPacket으로 변환
  - ActionPacketParser(V323)와 동일한 출력 타입 보장
  - 파싱 실패 시 raw_text fallback (서비스 중단 방지)
  - LLM 0회. 완전 로컬.
"""
from __future__ import annotations

from typing import Any

from literary_system.action_compiler.action_packet import Action, ActionPacket
from literary_system.llm_bridge.scene_draft_tool import TOOL_NAME


# ────────────────────────────────────────────────────────────────
# ToolUseParser
# ────────────────────────────────────────────────────────────────

class ToolUseParser:
    """
    Anthropic tool_use 응답 블록 → ActionPacket.

    입력 형식 (tool_use block input):
      {
        "narrative_text": "씬 텍스트...",
        "actions": [
          {"actor": "고애신", "action_type": "MOVE", "location": "교회"},
          {"actor": "유진", "action_type": "INTERACT", "target": "고애신"},
        ],
        "literary_state": {"SP": 0.72, "RU": 0.45, "ET": 0.60, "RD": 0.55}
      }
    """

    def parse_tool_input(self, tool_input: dict[str, Any]) -> ActionPacket:
        """
        tool_use 블록의 input dict → ActionPacket.

        Args:
            tool_input: Anthropic API tool_use 블록의 input 필드

        Returns:
            ActionPacket (실패 시 narrative_text만 포함한 fallback 패킷)
        """
        narrative_text = tool_input.get("narrative_text", "")
        raw_actions = tool_input.get("actions", [])
        literary_state = tool_input.get("literary_state", {})

        actions: list[Action] = []
        for raw in raw_actions:
            try:
                action = Action(
                    actor=str(raw.get("actor", "")),
                    action_type=str(raw.get("action_type", "INTERACT")),
                    target=raw.get("target"),
                    location=raw.get("location"),
                    metadata=raw.get("metadata", {}),
                )
                actions.append(action)
            except Exception:
                # 개별 액션 파싱 실패 시 스킵 (전체 실패 방지)
                continue

        return ActionPacket(
            narrative_text=narrative_text,
            actions=actions,
            literary_state=literary_state if literary_state else {},
            parse_meta={
                "method": "tool_use",
                "tool_name": TOOL_NAME,
                "action_count": len(actions),
                "parse_success": True,
                "source": "ClaudeAdapter",
            },
        )

    def parse_raw_response(self, response: Any) -> ActionPacket:
        """
        Anthropic API 전체 응답 객체 → ActionPacket.

        Args:
            response: anthropic.types.Message 또는 dict

        Returns:
            ActionPacket
        """
        # dict 형태 응답 처리 (Mock/테스트 호환)
        if isinstance(response, dict):
            return self._parse_dict_response(response)

        # Anthropic Message 객체 처리
        content = getattr(response, "content", [])
        for block in content:
            block_type = getattr(block, "type", None) or (block.get("type") if isinstance(block, dict) else None)
            if block_type == "tool_use":
                tool_name = getattr(block, "name", None) or (block.get("name") if isinstance(block, dict) else None)
                if tool_name == TOOL_NAME:
                    tool_input = getattr(block, "input", {}) or (block.get("input", {}) if isinstance(block, dict) else {})
                    return self.parse_tool_input(tool_input)

        # tool_use 블록 없음 → text fallback
        text_content = self._extract_text(response)
        return self._fallback_packet(text_content)

    # ── 내부 메서드 ────────────────────────────────────────────

    def _parse_dict_response(self, d: dict) -> ActionPacket:
        """dict 형태 응답 처리 (테스트/Mock 호환)."""
        # 직접 tool_input 형태인 경우
        if "narrative_text" in d:
            return self.parse_tool_input(d)

        # content 배열 포함
        content = d.get("content", [])
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                if block.get("name") == TOOL_NAME:
                    return self.parse_tool_input(block.get("input", {}))

        # fallback
        text = d.get("text", d.get("narrative_text", str(d)))
        return self._fallback_packet(text)

    def _extract_text(self, response: Any) -> str:
        """응답에서 텍스트 추출."""
        content = getattr(response, "content", [])
        for block in content:
            block_type = getattr(block, "type", None)
            if block_type == "text":
                return getattr(block, "text", "")
        return ""

    def _fallback_packet(self, text: str) -> ActionPacket:
        """파싱 실패 시 안전 fallback ActionPacket."""
        return ActionPacket(
            narrative_text=text,
            actions=[],
            literary_state={},
            parse_meta={
                "method": "fallback_text",
                "tool_name": TOOL_NAME,
                "action_count": 0,
                "parse_success": False,
                "source": "ClaudeAdapter.fallback",
            },
        )
