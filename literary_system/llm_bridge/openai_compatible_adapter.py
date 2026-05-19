"""
V411-B — OpenAICompatibleAdapter
단일 클래스로 OpenAI REST API 호환 엔드포인트를 모두 지원한다.

지원 대상:
  - Ollama:    base_url="http://localhost:11434/v1"
  - LM Studio: base_url="http://localhost:1234/v1"
  - vLLM:      base_url="http://localhost:8000/v1"
  - OpenAI:    base_url="https://api.openai.com/v1"

설계 원칙:
  - LLMBridgeInterface 완전 준수 (generate signature, is_available, get_provider_id)
  - base_url 파라미터 하나로 모든 OpenAI-호환 엔드포인트 통합
  - Ollama는 api_key="ollama" (임의값 허용)
  - 네트워크 의존성: urllib.request만 사용 (표준 라이브러리)
  - 오프라인 시 fallback 문자열 반환 (예외 방어)
  - LLM-0 원칙: 수치 판정 로직 없음, 텍스트 생성만 수행
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Optional, Union

from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface
from literary_system.llm_bridge.llm_context import LLMContext, coerce_context

# ────────────────────────────────────────────────────────────────
# 프리셋 URL 상수
# ────────────────────────────────────────────────────────────────

PRESET_URLS: dict[str, str] = {
    "ollama":   "http://localhost:11434/v1",
    "lmstudio": "http://localhost:1234/v1",
    "vllm":     "http://localhost:8000/v1",
    "openai":   "https://api.openai.com/v1",
}


# ────────────────────────────────────────────────────────────────
# OpenAICompatibleAdapter
# ────────────────────────────────────────────────────────────────

class OpenAICompatibleAdapter(LLMBridgeInterface):
    """
    OpenAI /v1/chat/completions REST API 호환 어댑터.

    Args:
        base_url:    엔드포인트 기본 URL (예: "http://localhost:11434/v1")
        model:       모델명 (예: "llama3.2", "gpt-4o")
        api_key:     API 키 (Ollama는 임의값 허용)
        provider_id: 프로바이더 식별자 (미입력 시 base_url에서 추론)
    """

    HEALTH_CHECK_TIMEOUT: int = 5   # /models 헬스체크 타임아웃 (초)

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str = "ollama",
        provider_id: str = "",
    ) -> None:
        self._base_url   = base_url.rstrip("/")
        self._model      = model
        self._api_key    = api_key
        self._provider_id = provider_id or self._infer_provider_id(base_url)

    # ── LLMBridgeInterface 구현 ──────────────────────────────────

    @property
    def provider_name(self) -> str:
        return self._provider_id

    def get_provider_id(self) -> str:
        return self._provider_id

    def generate(self, prompt: str, context: Union[LLMContext, dict] = None) -> str:
        """
        /v1/chat/completions 호출 후 assistant 메시지 반환.
        오프라인/오류 시 fallback 문자열 반환 (예외 전파 없음).
        """
        ctx = coerce_context(context or {})
        payload = json.dumps({
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": ctx.max_tokens,
            "temperature": ctx.temperature,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self._base_url}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=ctx.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[{self._provider_id}:fallback] prompt_len={len(prompt)} err={type(e).__name__}"

    def parse_action_packet(self, raw: str):
        """ActionPacket 파싱 위임."""
        try:
            from literary_system.llm_bridge.tool_use_parser import ToolUseParser
            return ToolUseParser().parse(raw)
        except Exception:
            return None

    def is_available(self) -> bool:
        """GET /models 로 가용성 확인 (HEALTH_CHECK_TIMEOUT 초)."""
        try:
            req = urllib.request.Request(
                f"{self._base_url}/models",
                headers={"Authorization": f"Bearer {self._api_key}"},
                method="GET",
            )
            urllib.request.urlopen(req, timeout=self.HEALTH_CHECK_TIMEOUT)
            return True
        except Exception:
            return False

    # ── 팩토리 메서드 ────────────────────────────────────────────

    @classmethod
    def for_ollama(
        cls,
        model: str = "llama3.2",
        base_url: str = PRESET_URLS["ollama"],
    ) -> "OpenAICompatibleAdapter":
        """Ollama 전용 어댑터 팩토리."""
        return cls(base_url=base_url, model=model, api_key="ollama",
                   provider_id="ollama")

    @classmethod
    def for_lmstudio(
        cls,
        model: str = "local-model",
    ) -> "OpenAICompatibleAdapter":
        """LM Studio 전용 어댑터 팩토리."""
        return cls(base_url=PRESET_URLS["lmstudio"], model=model,
                   api_key="lmstudio", provider_id="lmstudio")

    @classmethod
    def for_openai(
        cls,
        model: str,
        api_key: str,
    ) -> "OpenAICompatibleAdapter":
        """OpenAI 전용 어댑터 팩토리."""
        return cls(base_url=PRESET_URLS["openai"], model=model,
                   api_key=api_key, provider_id="openai")

    @classmethod
    def from_preset(
        cls,
        preset: str,
        model: str,
        api_key: str = "ollama",
    ) -> "OpenAICompatibleAdapter":
        """
        프리셋 이름으로 어댑터 생성.
        preset: "ollama" | "lmstudio" | "vllm" | "openai"
        """
        url = PRESET_URLS.get(preset, preset)
        return cls(base_url=url, model=model, api_key=api_key,
                   provider_id=preset)

    # ── 내부 헬퍼 ────────────────────────────────────────────────

    def _infer_provider_id(self, base_url: str) -> str:
        """base_url에서 프로바이더 ID 추론."""
        lower = base_url.lower()
        for name, url in PRESET_URLS.items():
            if url.split("/")[2] in lower:
                return name
        return "custom"

    def __repr__(self) -> str:
        return (f"OpenAICompatibleAdapter("
                f"provider={self._provider_id}, model={self._model}, "
                f"base_url={self._base_url})")
