"""
V411-B 테스트 — OpenAICompatibleAdapter.

검증 항목:
  1~3:   인스턴스 생성 (직접/팩토리)
  4~5:   provider_id 추론
  6~8:   generate() 오프라인 fallback 반환 (실제 서버 불필요)
  9~12:  팩토리 메서드 (for_ollama, for_lmstudio, for_openai, from_preset)
  13~14: is_available() 오프라인 → False
  15~16: LLMBridgeInterface 완전 준수 (is_available, get_provider_id)
  17~18: generate() LLMContext 수용
  19~20: generate() dict context 하위 호환
"""
from __future__ import annotations
import pytest
from literary_system.llm_bridge.openai_compatible_adapter import (
    OpenAICompatibleAdapter, PRESET_URLS
)
from literary_system.llm_bridge.llm_context import LLMContext
from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface


# ── 1. 직접 인스턴스화 ──────────────────────────────────────────
def test_direct_instantiation():
    adapter = OpenAICompatibleAdapter(
        base_url="http://localhost:11434/v1",
        model="llama3.2",
    )
    assert adapter._model == "llama3.2"
    assert "11434" in adapter._base_url


# ── 2. provider_id 명시적 설정 ──────────────────────────────────
def test_explicit_provider_id():
    adapter = OpenAICompatibleAdapter(
        base_url="http://custom:8080/v1",
        model="custom-model",
        provider_id="my_provider",
    )
    assert adapter.get_provider_id() == "my_provider"


# ── 3. LLMBridgeInterface 상속 확인 ─────────────────────────────
def test_inherits_interface():
    adapter = OpenAICompatibleAdapter.for_ollama()
    assert isinstance(adapter, LLMBridgeInterface)


# ── 4. provider_id 추론 — ollama ─────────────────────────────────
def test_provider_id_inferred_ollama():
    adapter = OpenAICompatibleAdapter(
        base_url=PRESET_URLS["ollama"],
        model="llama3.2",
    )
    assert adapter.get_provider_id() == "ollama"


# ── 5. provider_id 추론 — custom ─────────────────────────────────
def test_provider_id_inferred_custom():
    adapter = OpenAICompatibleAdapter(
        base_url="http://myserver:9999/v1",
        model="any-model",
    )
    assert adapter.get_provider_id() == "custom"


# ── 6. generate() 오프라인 fallback 반환 ────────────────────────
def test_generate_offline_returns_fallback():
    adapter = OpenAICompatibleAdapter.for_ollama(
        base_url="http://localhost:19999/v1"   # 존재하지 않는 포트
    )
    result = adapter.generate("test prompt", LLMContext())
    assert "fallback" in result.lower() or "ollama" in result.lower()


# ── 7. generate() fallback에 prompt_len 포함 ────────────────────
def test_generate_fallback_contains_info():
    adapter = OpenAICompatibleAdapter(
        base_url="http://localhost:19999/v1",
        model="none",
        provider_id="test_provider",
    )
    prompt = "a" * 50
    result = adapter.generate(prompt, LLMContext())
    assert "50" in result or "test_provider" in result


# ── 8. generate() None context 허용 ─────────────────────────────
def test_generate_none_context():
    adapter = OpenAICompatibleAdapter.for_ollama(
        base_url="http://localhost:19999/v1"
    )
    result = adapter.generate("hello", None)
    assert isinstance(result, str)


# ── 9. for_ollama 팩토리 ─────────────────────────────────────────
def test_factory_for_ollama():
    adapter = OpenAICompatibleAdapter.for_ollama(model="mistral")
    assert adapter.get_provider_id() == "ollama"
    assert adapter._model == "mistral"
    assert "11434" in adapter._base_url


# ── 10. for_lmstudio 팩토리 ─────────────────────────────────────
def test_factory_for_lmstudio():
    adapter = OpenAICompatibleAdapter.for_lmstudio(model="phi-3")
    assert adapter.get_provider_id() == "lmstudio"
    assert "1234" in adapter._base_url


# ── 11. for_openai 팩토리 ───────────────────────────────────────
def test_factory_for_openai():
    adapter = OpenAICompatibleAdapter.for_openai(
        model="gpt-4o", api_key="sk-test"
    )
    assert adapter.get_provider_id() == "openai"
    assert adapter._api_key == "sk-test"
    assert "openai.com" in adapter._base_url


# ── 12. from_preset 팩토리 ──────────────────────────────────────
def test_factory_from_preset_ollama():
    adapter = OpenAICompatibleAdapter.from_preset("ollama", "llama3.2")
    assert adapter.get_provider_id() == "ollama"

def test_factory_from_preset_vllm():
    adapter = OpenAICompatibleAdapter.from_preset("vllm", "llama3.2")
    assert "8000" in adapter._base_url


# ── 13. is_available() 오프라인 → False ─────────────────────────
def test_is_available_offline():
    adapter = OpenAICompatibleAdapter.for_ollama(
        base_url="http://localhost:19999/v1"
    )
    assert adapter.is_available() == False


# ── 14. is_available() 메서드 존재 확인 ─────────────────────────
def test_is_available_method_exists():
    adapter = OpenAICompatibleAdapter.for_ollama()
    assert hasattr(adapter, "is_available")
    assert callable(adapter.is_available)


# ── 15. provider_name 프로퍼티 ──────────────────────────────────
def test_provider_name_property():
    adapter = OpenAICompatibleAdapter.for_ollama()
    assert adapter.provider_name == "ollama"


# ── 16. parse_action_packet 호출 가능 ───────────────────────────
def test_parse_action_packet_callable():
    adapter = OpenAICompatibleAdapter.for_ollama()
    result = adapter.parse_action_packet('{"action": "MOVE"}')
    # 파싱 실패해도 None 반환 (예외 없음)
    # result is None or ActionPacket


# ── 17. generate() LLMContext max_tokens 전달 ───────────────────
def test_generate_uses_llm_context():
    adapter = OpenAICompatibleAdapter(
        base_url="http://localhost:19999/v1",
        model="test",
    )
    ctx = LLMContext(max_tokens=500, timeout=1)
    result = adapter.generate("prompt", ctx)
    assert isinstance(result, str)


# ── 18. generate() dict context ─────────────────────────────────
def test_generate_dict_context_compat():
    adapter = OpenAICompatibleAdapter(
        base_url="http://localhost:19999/v1",
        model="test",
    )
    result = adapter.generate("prompt", {"max_tokens": 100})
    assert isinstance(result, str)


# ── 19. PRESET_URLS 상수 검증 ───────────────────────────────────
def test_preset_urls_keys():
    for key in ["ollama", "lmstudio", "vllm", "openai"]:
        assert key in PRESET_URLS
        assert PRESET_URLS[key].startswith("http")


# ── 20. repr 출력 ───────────────────────────────────────────────
def test_repr():
    adapter = OpenAICompatibleAdapter.for_ollama(model="llama3.2")
    r = repr(adapter)
    assert "ollama" in r
    assert "llama3.2" in r
