"""
literary_system/llm_bridge/adapters/ollama_adapter.py
V484 — OllamaAdapter

로컬 Ollama REST API(/api/generate)와 연결하는 LLMBridgeInterface 구현체.

환경변수:
  OLLAMA_BASE_URL  — 기본값: http://localhost:11434
  OLLAMA_MODEL     — 기본값: llama3.2 (또는 qwen2.5)
  OLLAMA_TIMEOUT   — 기본값: 120 (초)

LLM-0 원칙: generate()만 LLM 호출, 라우팅·계획 로직 없음.
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Union

from literary_system.action_compiler.action_packet import ActionPacket, ActionPacketParser
from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface
from literary_system.llm_bridge.llm_context import LLMContext, coerce_context

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "http://localhost:11434"
_DEFAULT_MODEL    = "llama3.2"
_DEFAULT_TIMEOUT  = 120


class OllamaAdapterLegacy(LLMBridgeInterface):
    """
    Ollama 로컬 LLM 어댑터.

    사용:
        adapter = OllamaAdapter()                     # 환경변수 기본값
        adapter = OllamaAdapter(model="qwen2.5")      # 모델 지정
        text = adapter.generate("씬을 써줘", context)
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
        system_prompt: str | None = None,
    ) -> None:
        self._base_url = (base_url or os.environ.get("OLLAMA_BASE_URL", _DEFAULT_BASE_URL)).rstrip("/")
        self._model    = model or os.environ.get("OLLAMA_MODEL", _DEFAULT_MODEL)
        self._timeout  = timeout or int(os.environ.get("OLLAMA_TIMEOUT", _DEFAULT_TIMEOUT))
        self._system   = system_prompt or (
            "당신은 한국 드라마 전문 작가입니다. "
            "지시한 씬을 한국어로 작성하세요."
        )
        self._parser   = ActionPacketParser()

        # V577 ADR-035 Deprecation 경고
        logging.getLogger(__name__).warning(
            "[DEPRECATED V577] OllamaAdapter(G1_sub)는 구세대 어댑터입니다. "
            "V578 이후 제거 예정. literary_system.llm_bridge.canonical_adapter."
            "make_canonical_ollama() 사용을 권장합니다."
        )

    # ── LLMBridgeInterface 구현 ─────────────────────────────────

    @property
    def provider_name(self) -> str:
        return "ollama"

    def get_provider_id(self) -> str:
        return "ollama"

    def is_available(self) -> bool:
        """Ollama 서버가 응답하는지 확인 (GET /api/tags)."""
        try:
            url = f"{self._base_url}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def generate(self, prompt: str, context: Union[LLMContext, dict] = None) -> str:
        """
        Ollama /api/generate 엔드포인트에 요청 → 텍스트 응답.

        Ollama 미실행 시 RuntimeError.
        stream=False로 전체 응답 일괄 수신.
        """
        ctx = coerce_context(context) if context else None
        full_prompt = prompt
        if self._system:
            full_prompt = f"{self._system}\n\n{prompt}"
        if ctx and ctx.metadata:
            full_prompt += f"\n\n[컨텍스트]\n{ctx.metadata}"

        payload = json.dumps({
            "model": self._model,
            "prompt": full_prompt,
            "stream": False,
        }).encode("utf-8")

        url = f"{self._base_url}/api/generate"
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return body.get("response", "")
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"OllamaAdapter: Ollama 서버 연결 실패 ({self._base_url}). "
                f"ollama serve 를 먼저 실행하세요. 오류: {exc}"
            ) from exc
        except Exception as exc:
            logger.error("OllamaAdapter.generate() 오류: %s", exc)
            raise

    def parse_action_packet(self, raw: str) -> ActionPacket:
        return self._parser.parse(raw)

    def list_models(self) -> list:
        """설치된 모델 목록 반환."""
        try:
            url = f"{self._base_url}/api/tags"
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = json.loads(resp.read())
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

OllamaAdapter = OllamaAdapterLegacy  # V579 backward-compat alias
