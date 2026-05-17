"""
V325 - ClaudeAdapter  (Phase 1)
Anthropic Claude API → LLMBridgeInterface 구현체.

설계 원칙 (P2 외과적 통합):
  - LLMBridgeInterface 상속 → 기존 코드 무수정
  - Anthropic Tool Use API: tools=[SCENE_DRAFT_TOOL] + tool_choice 강제
  - generate() → narrative_text 반환 + 내부에 원본 Message 저장
  - parse_action_packet() → ToolUseParser로 전체 ActionPacket 복원
  - anthropic 패키지 미설치 시 ImportError → is_available() = False
  - LLM 0회 평가 원칙 준수 (생성만 LLM, 판정은 로컬)
"""
from __future__ import annotations

import os
from typing import Any

from literary_system.action_compiler.action_packet import ActionPacket
from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface
from literary_system.llm_bridge.llm_context import LLMContext, coerce_context
from literary_system.llm_bridge.scene_draft_tool import SCENE_DRAFT_TOOL, TOOL_NAME
from literary_system.llm_bridge.tool_use_parser import ToolUseParser


# ────────────────────────────────────────────────────────────────
# Anthropic 패키지 지연 임포트 (optional dependency)
# ────────────────────────────────────────────────────────────────

try:
    import anthropic as _anthropic_pkg
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _anthropic_pkg = None  # type: ignore[assignment]
    _ANTHROPIC_AVAILABLE = False


# ────────────────────────────────────────────────────────────────
# ClaudeAdapter
# ────────────────────────────────────────────────────────────────

class ClaudeAdapter(LLMBridgeInterface):
    """
    Anthropic Claude API LLM 브릿지 구현체.

    Args:
        model:       Anthropic 모델명 (기본: claude-sonnet-4-6)
        api_key:     Anthropic API 키 (None이면 환경변수 ANTHROPIC_API_KEY 사용)
        max_tokens:  최대 토큰 수 (기본 4096)
        temperature: 생성 온도 (기본 1.0 — Anthropic 권장값)
        system_prompt: 시스템 프롬프트 (None이면 기본 씬 작가 지시문 사용)
    """

    DEFAULT_MODEL      = "claude-sonnet-4-6"
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_TEMPERATURE = 1.0

    _DEFAULT_SYSTEM = (
        "당신은 한국 문학 작가입니다. "
        "주어진 씬 컨텍스트를 바탕으로 완성도 높은 씬 텍스트를 생성하세요. "
        "반드시 submit_scene_draft 도구를 호출하여 결과를 제출해야 합니다."
    )

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        system_prompt: str | None = None,
    ) -> None:
        self._model       = model
        self._api_key     = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._max_tokens  = max_tokens
        self._temperature = temperature
        self._system      = system_prompt or self._DEFAULT_SYSTEM

        self._parser: ToolUseParser = ToolUseParser()
        self._last_response: Any    = None   # 최근 Anthropic Message 저장
        self._call_count: int       = 0

        # 패키지가 있으면 클라이언트 초기화
        self._client: Any = None
        if _ANTHROPIC_AVAILABLE:
            try:
                self._client = _anthropic_pkg.Anthropic(api_key=self._api_key)
            except Exception:
                self._client = None

    # ── LLMBridgeInterface 구현 ──────────────────────────────────

    def generate(self, prompt: str, context=None) -> str:
        """
        Anthropic API 호출 → narrative_text 반환.

        Tool Use 강제:
          - tools=[SCENE_DRAFT_TOOL]
          - tool_choice={"type": "tool", "name": "submit_scene_draft"}

        내부적으로 원본 Message 객체를 self._last_response에 보존.
        parse_action_packet()이 후속 호출로 전체 ActionPacket을 복원한다.

        Args:
            prompt:  씬 생성 지시문 (PromptAssembler 출력)
            context: 씬 컨텍스트 dict (scene_id, chars, literary_state 등)

        Returns:
            narrative_text 문자열 (생성 실패 시 빈 문자열)
        """
        if not self._client:
            return ""

        # context → 사용자 메시지에 포함
        user_content = self._build_user_message(prompt, context)

        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                system=self._system,
                tools=[SCENE_DRAFT_TOOL],
                tool_choice={"type": "tool", "name": TOOL_NAME},
                messages=[{"role": "user", "content": user_content}],
            )
            self._last_response = response
            self._call_count   += 1

            # tool_use 블록에서 narrative_text 빠르게 추출
            return self._extract_narrative(response)

        except Exception as e:
            # API 오류 시 빈 문자열 반환 (서비스 중단 방지)
            self._last_response = None
            return ""

    def parse_action_packet(self, raw: str) -> ActionPacket:
        """
        직전 generate() 응답 → 전체 ActionPacket 복원.

        self._last_response(Anthropic Message)가 있으면 ToolUseParser로
        narrative_text + actions[] + literary_state 전부를 복원한다.
        없으면 raw 텍스트로 fallback ActionPacket을 구성한다.

        Args:
            raw: generate()가 반환한 narrative_text (fallback 용)

        Returns:
            ActionPacket
        """
        if self._last_response is not None:
            return self._parser.parse_raw_response(self._last_response)

        # last_response 없음 → raw fallback
        return self._parser._fallback_packet(raw)

    @property
    def provider_name(self) -> str:
        return self._model

    # ── 상태 조회 ────────────────────────────────────────────────

    @property
    def call_count(self) -> int:
        """generate() 호출 횟수."""
        return self._call_count

    def is_available(self) -> bool:
        """Anthropic 패키지 + 클라이언트 초기화 여부."""
        return _ANTHROPIC_AVAILABLE and self._client is not None

    def reset(self) -> None:
        """호출 카운터 및 캐시 초기화."""
        self._call_count    = 0
        self._last_response = None

    def get_status(self) -> dict[str, Any]:
        """어댑터 상태 요약."""
        return {
            "provider":          self.provider_name,
            "model":             self._model,
            "available":         self.is_available(),
            "call_count":        self._call_count,
            "anthropic_package": _ANTHROPIC_AVAILABLE,
            "client_ready":      self._client is not None,
        }

    # ── 내부 헬퍼 ────────────────────────────────────────────────

    def _build_user_message(self, prompt: str, context: dict) -> str:
        """prompt + context → 사용자 메시지 문자열 조합."""
        parts = [prompt]
        if context:
            ctx_lines = []
            for k, v in context.items():
                if k not in ("raw_prompt",):   # 중복 방지
                    ctx_lines.append(f"  {k}: {v}")
            if ctx_lines:
                parts.append("\n[씬 컨텍스트]\n" + "\n".join(ctx_lines))
        return "\n".join(parts)

    def _extract_narrative(self, response: Any) -> str:
        """Anthropic Message에서 narrative_text 빠르게 추출."""
        content = getattr(response, "content", [])
        for block in content:
            block_type = getattr(block, "type", None)
            if block_type == "tool_use":
                tool_name = getattr(block, "name", None)
                if tool_name == TOOL_NAME:
                    tool_input = getattr(block, "input", {}) or {}
                    return tool_input.get("narrative_text", "")
        return ""
