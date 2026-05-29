"""
V411-C 테스트 — OllamaAdapter 마이그레이션.

검증 항목:
  1~3:   make_ollama_adapter() 팩토리 함수
  4~6:   OllamaAdapter 클래스 하위 호환
  7~9:   시그니처 계약 (generate context: LLMContext|dict 허용)
  10~12: OllamaAdapter → OpenAICompatibleAdapter 상속
  13~15: LLMBridgeInterface 완전 준수
"""
from __future__ import annotations
import pytest
from literary_system.llm_bridge.ollama_adapter import OllamaAdapter, make_ollama_adapter
from literary_system.llm_bridge.openai_compatible_adapter import OpenAICompatibleAdapter
from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface
from literary_system.llm_bridge.llm_context import LLMContext


# ── 1. make_ollama_adapter 기본 생성 ────────────────────────────
def test_make_ollama_adapter_default():
    adapter = make_ollama_adapter()
    assert isinstance(adapter, OpenAICompatibleAdapter)
    assert adapter.get_provider_id() == "ollama"


# ── 2. make_ollama_adapter 모델 지정 ────────────────────────────
def test_make_ollama_adapter_model():
    adapter = make_ollama_adapter(model="mistral")
    assert adapter._model == "mistral"


# ── 3. make_ollama_adapter base_url 지정 ────────────────────────
def test_make_ollama_adapter_custom_url():
    adapter = make_ollama_adapter(base_url="http://192.168.1.10:11434/v1")
    assert "192.168.1.10" in adapter._base_url


# ── 4. OllamaAdapter 클래스 하위 호환 ───────────────────────────
def test_ollama_adapter_class_instantiation():
    adapter = OllamaAdapter()
    assert isinstance(adapter, OllamaAdapter)
    assert isinstance(adapter, OpenAICompatibleAdapter)


# ── 5. OllamaAdapter 기본 모델 ──────────────────────────────────
def test_ollama_adapter_default_model():
    adapter = OllamaAdapter()
    assert adapter._model == "llama3.2"


# ── 6. OllamaAdapter 모델 지정 ──────────────────────────────────
def test_ollama_adapter_custom_model():
    adapter = OllamaAdapter(model="gemma2")
    assert adapter._model == "gemma2"


# ── 7. 시그니처 — LLMContext 수용 ───────────────────────────────
def test_generate_accepts_llm_context():
    adapter = OllamaAdapter(base_url="http://localhost:19999/v1")
    ctx = LLMContext(narrative_fitness=5.0, timeout=1)
    result = adapter.generate("test", ctx)
    assert isinstance(result, str)


# ── 8. 시그니처 — dict context 하위 호환 ────────────────────────
def test_generate_accepts_dict():
    adapter = OllamaAdapter(base_url="http://localhost:19999/v1")
    result = adapter.generate("test", {"scene_id": "s1"})
    assert isinstance(result, str)


# ── 9. 시그니처 — **kwargs 없음 (계약 준수) ──────────────────────
def test_generate_no_kwargs():
    """generate() 시그니처에 **kwargs가 없음을 확인."""
    import inspect
    adapter = OllamaAdapter()
    sig = inspect.signature(adapter.generate)
    params = list(sig.parameters.keys())
    assert "kwargs" not in params
    assert "context" in params


# ── 10. 상속 체계 확인 ──────────────────────────────────────────
def test_inheritance_chain():
    adapter = OllamaAdapter()
    assert isinstance(adapter, OllamaAdapter)
    assert isinstance(adapter, OpenAICompatibleAdapter)
    assert isinstance(adapter, LLMBridgeInterface)


# ── 11. provider_name ───────────────────────────────────────────
def test_provider_name():
    adapter = OllamaAdapter()
    assert adapter.provider_name.startswith("ollama")


# ── 12. get_provider_id ─────────────────────────────────────────
def test_get_provider_id():
    adapter = OllamaAdapter()
    assert adapter.get_provider_id() == "ollama"


# ── 13. is_available 메서드 존재 ────────────────────────────────
def test_is_available_exists():
    adapter = OllamaAdapter()
    assert hasattr(adapter, "is_available")
    assert callable(adapter.is_available)


# ── 14. is_available 오프라인 ────────────────────────────────────
def test_is_available_offline():
    adapter = OllamaAdapter(base_url="http://localhost:19999/v1")
    assert adapter.is_available() == False


# ── 15. generate_with_response LLMResponse 반환 ─────────────────
def test_generate_with_response():
    adapter = OllamaAdapter(base_url="http://localhost:19999/v1")
    from literary_system.llm_bridge.llm_context import LLMResponse
    resp = adapter.generate_with_response("test", LLMContext(timeout=1))
    assert isinstance(resp, LLMResponse)
    assert resp.provider_id == "ollama"
    assert resp.latency_ms >= 0
