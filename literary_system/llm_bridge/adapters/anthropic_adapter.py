"""
literary_system/llm_bridge/adapters/anthropic_adapter.py
V484 — AnthropicAdapter

Claude API(claude-sonnet-4-6 / claude-haiku-4-5-20251001)와 연결하는
LLMBridgeInterface 구현체.

환경변수:
  ANTHROPIC_API_KEY  — 필수 (없으면 is_available()=False)
  ANTHROPIC_MODEL    — 기본값: claude-sonnet-4-6
  ANTHROPIC_MAX_TOKENS — 기본값: 2048

LLM-0 원칙: generate()만 LLM 호출, 라우팅·계획 로직은 없음.
"""
from __future__ import annotations

import logging
import os
from typing import Union

from literary_system.action_compiler.action_packet import ActionPacket, ActionPacketParser
from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface
from literary_system.llm_bridge.llm_context import LLMContext, coerce_context

logger = logging.getLogger(__name__)

# 기본 모델 상수
_DEFAULT_MODEL  = "claude-sonnet-4-6"
_HAIKU_MODEL    = "claude-haiku-4-5-20251001"
_DEFAULT_MAX_TOKENS = 2048


class AnthropicAdapter(LLMBridgeInterface):
    """
    Anthropic Claude API 어댑터.

    사용:
        adapter = AnthropicAdapter()         # 환경변수에서 API 키 읽기
        adapter = AnthropicAdapter(api_key="sk-...", model="claude-haiku-4-5-20251001")
        text = adapter.generate("씬을 써줘", context)
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> None:
        self._api_key    = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._model      = model or os.environ.get("ANTHROPIC_MODEL", _DEFAULT_MODEL)
        self._max_tokens = max_tokens or int(os.environ.get("ANTHROPIC_MAX_TOKENS", _DEFAULT_MAX_TOKENS))
        self._system     = system_prompt or (
            "당신은 한국 드라마 전문 작가입니다. "
            "지시한 씬을 한국어로 작성하세요. "
            "대사, 지문, 감정 묘사를 포함하여 완성된 씬을 출력하세요."
        )
        self._parser     = ActionPacketParser()
        self._client     = None  # lazy init

        # V577 ADR-035 Deprecation 경고
        logging.getLogger(__name__).warning(
            "[DEPRECATED V577] AnthropicAdapter(G1_sub)는 구세대 어댑터입니다. "
            "V578 이후 제거 예정. literary_system.llm_bridge.canonical_adapter."
            "make_canonical_claude() 사용을 권장합니다."
        )

    # ── LLMBridgeInterface 구현 ─────────────────────────────────

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def get_provider_id(self) -> str:
        # 모델명 기반: sonnet → "sonnet", haiku → "haiku"
        if "haiku" in self._model.lower():
            return "haiku"
        if "opus" in self._model.lower():
            return "opus"
        return "sonnet"

    def is_available(self) -> bool:
        """API 키가 설정되어 있고 anthropic 패키지가 설치되어 있는지 확인."""
        if not self._api_key:
            return False
        try:
            import anthropic  # noqa: F401
            return True
        except ImportError:
            return False

    def generate(self, prompt: str, context: Union[LLMContext, dict] = None) -> str:
        """
        Claude API에 프롬프트 전송 → 텍스트 응답.

        anthropic 패키지 미설치 또는 API 키 없으면 RuntimeError.
        """
        if not self._api_key:
            raise RuntimeError(
                "AnthropicAdapter: ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다. "
                "export ANTHROPIC_API_KEY=sk-... 후 재시도하세요."
            )
        try:
            import anthropic
        except ImportError as e:
            raise RuntimeError(
                "AnthropicAdapter: 'anthropic' 패키지가 필요합니다. "
                "pip install anthropic --break-system-packages"
            ) from e

        ctx = coerce_context(context) if context else None

        # 시스템 프롬프트 + 컨텍스트 메타데이터 결합
        system = self._system
        if ctx and ctx.metadata:
            system += f"\n\n[컨텍스트]\n{ctx.metadata}"

        if self._client is None:
            self._client = anthropic.Anthropic(api_key=self._api_key)

        try:
            message = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except Exception as exc:
            logger.error("AnthropicAdapter.generate() 오류: %s", exc)
            raise

    def parse_action_packet(self, raw: str) -> ActionPacket:
        return self._parser.parse(raw)


class AnthropicHaikuAdapter(AnthropicAdapter):
    """Claude Haiku 전용 어댑터 (speed 티어)."""

    def __init__(self, api_key: str | None = None, **kwargs) -> None:
        super().__init__(api_key=api_key, model=_HAIKU_MODEL, **kwargs)

    def get_provider_id(self) -> str:
        return "haiku"


class AnthropicSonnetAdapter(AnthropicAdapter):
    """Claude Sonnet 전용 어댑터 (quality 티어)."""

    def __init__(self, api_key: str | None = None, **kwargs) -> None:
        super().__init__(api_key=api_key, model=_DEFAULT_MODEL, **kwargs)

    def get_provider_id(self) -> str:
        return "sonnet"
