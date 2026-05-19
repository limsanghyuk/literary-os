"""
V411-C — OllamaAdapter (갱신)
V328 OllamaAdapter → OpenAICompatibleAdapter 기반으로 마이그레이션.

변경 사항:
  - generate(**kwargs) 시그니처 불일치 해소
  - generate(prompt, context: LLMContext|dict) → OpenAI /v1/chat/completions
  - is_available() → /v1/models 헬스체크
  - OllamaAdapter 클래스는 하위 호환 별칭으로 유지
  - make_ollama_adapter() 팩토리 함수 제공

Ollama API 노트:
  - /v1/chat/completions: OpenAI 호환 (Ollama 0.1.14+)
  - /api/generate: 구 Ollama API (V328에서 사용, V411에서 폐기)
  - api_key는 임의 문자열 허용 ("ollama" 관례)
"""
from __future__ import annotations

import logging

from literary_system.llm_bridge.openai_compatible_adapter import (
    PRESET_URLS,
    OpenAICompatibleAdapter,
)


def make_ollama_adapter(
    model: str = "llama3.2",
    base_url: str = PRESET_URLS["ollama"],
) -> OpenAICompatibleAdapter:
    """
    Ollama 연동용 어댑터 팩토리 함수 (권장).

    Args:
        model:    Ollama 모델명 (예: "llama3.2", "mistral", "gemma2")
        base_url: Ollama 서버 URL (기본: http://localhost:11434/v1)

    Returns:
        OpenAICompatibleAdapter 인스턴스
    """
    return OpenAICompatibleAdapter.for_ollama(model=model, base_url=base_url)


# 하위 호환 별칭 — 신규 코드는 make_ollama_adapter() 사용 권장
class OllamaAdapter(OpenAICompatibleAdapter):
    """
    하위 호환용 OllamaAdapter.

    V328 OllamaAdapter를 대체하며, 내부적으로 OpenAICompatibleAdapter 사용.
    신규 코드는 make_ollama_adapter() 팩토리 함수를 사용할 것.
    """

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = PRESET_URLS["ollama"],
        timeout: int = 60,
    ) -> None:
        super().__init__(
            base_url=base_url,
            model=model,
            api_key="ollama",
            provider_id="ollama",
        )
        # timeout은 LLMContext에서 관리하지만 __init__ 호환성 유지
        self._default_timeout = timeout

        # V577 ADR-035 Deprecation 경고
        logging.getLogger(__name__).warning(
            "[DEPRECATED V577] OllamaAdapter(G1)는 구세대 어댑터입니다. "
            "V578 이후 제거 예정. literary_system.llm_bridge.canonical_adapter."
            "make_canonical_ollama() 사용을 권장합니다."
        )

    @property
    def provider_name(self) -> str:
        """하위 호환: "ollama:{model}" 형식 반환 (V328 테스트 호환)."""
        return f"ollama:{self._model}"

    @property
    def model(self) -> str:
        """하위 호환: _model 공개 접근자."""
        return self._model

    @property
    def base_url(self) -> str:
        """하위 호환: _base_url 공개 접근자."""
        return self._base_url
