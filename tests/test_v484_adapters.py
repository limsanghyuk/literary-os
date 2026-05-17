"""
V484 LLM Adapter 테스트
- AnthropicAdapter (haiku/sonnet/opus provider_id)
- OllamaAdapter (urllib 기반, is_available/generate mock)
"""
import pytest
from unittest.mock import patch, MagicMock, call
import sys
import io
import json

sys.path.insert(0, '/tmp/v481_work/literary_os_v430_COMPLETE')


# ─────────────────────────────────────────────
# AnthropicAdapter
# ─────────────────────────────────────────────
class TestAnthropicAdapterProviderID:
    def _make(self, model):
        from literary_system.llm_bridge.adapters.anthropic_adapter import AnthropicAdapter
        return AnthropicAdapter(api_key="sk-test", model=model)

    def test_haiku_provider_id(self):
        a = self._make("claude-haiku-3-5")
        assert a.get_provider_id() == "haiku"

    def test_sonnet_provider_id(self):
        a = self._make("claude-sonnet-3-5")
        assert a.get_provider_id() == "sonnet"

    def test_opus_provider_id(self):
        a = self._make("claude-opus-4")
        assert a.get_provider_id() == "opus"

    def test_unknown_model_fallback(self):
        a = self._make("claude-future-model")
        pid = a.get_provider_id()
        assert isinstance(pid, str)
        assert len(pid) > 0

    def test_provider_id_lowercase(self):
        a = self._make("claude-haiku-3-5")
        assert a.get_provider_id() == a.get_provider_id().lower()


class TestAnthropicAdapterAvailability:
    def test_is_available_no_key(self):
        from literary_system.llm_bridge.adapters.anthropic_adapter import AnthropicAdapter
        a = AnthropicAdapter(api_key="", model="claude-haiku-3-5")
        assert a.is_available() is False

    def test_is_available_with_key_returns_bool(self):
        from literary_system.llm_bridge.adapters.anthropic_adapter import AnthropicAdapter
        a = AnthropicAdapter(api_key="sk-real", model="claude-haiku-3-5")
        result = a.is_available()
        assert isinstance(result, bool)

    def test_generate_raises_without_key(self):
        from literary_system.llm_bridge.adapters.anthropic_adapter import AnthropicAdapter
        a = AnthropicAdapter(api_key="", model="claude-haiku-3-5")
        with pytest.raises((RuntimeError, Exception)):
            a.generate("test prompt")


class TestAnthropicSubclasses:
    def test_haiku_adapter_exists(self):
        from literary_system.llm_bridge.adapters.anthropic_adapter import AnthropicHaikuAdapter
        a = AnthropicHaikuAdapter(api_key="sk-test")
        assert a.get_provider_id() == "haiku"

    def test_sonnet_adapter_exists(self):
        from literary_system.llm_bridge.adapters.anthropic_adapter import AnthropicSonnetAdapter
        a = AnthropicSonnetAdapter(api_key="sk-test")
        assert a.get_provider_id() == "sonnet"

    def test_haiku_default_model_contains_haiku(self):
        from literary_system.llm_bridge.adapters.anthropic_adapter import AnthropicHaikuAdapter
        a = AnthropicHaikuAdapter(api_key="sk-test")
        model_attr = getattr(a, 'model', None) or getattr(a, '_model', '')
        assert "haiku" in model_attr.lower()

    def test_sonnet_default_model_contains_sonnet(self):
        from literary_system.llm_bridge.adapters.anthropic_adapter import AnthropicSonnetAdapter
        a = AnthropicSonnetAdapter(api_key="sk-test")
        model_attr = getattr(a, 'model', None) or getattr(a, '_model', '')
        assert "sonnet" in model_attr.lower()

    def test_haiku_inherits_anthropic_adapter(self):
        from literary_system.llm_bridge.adapters.anthropic_adapter import (
            AnthropicAdapter, AnthropicHaikuAdapter
        )
        a = AnthropicHaikuAdapter(api_key="sk-test")
        assert isinstance(a, AnthropicAdapter)

    def test_system_prompt_passthrough(self):
        from literary_system.llm_bridge.adapters.anthropic_adapter import AnthropicAdapter
        a = AnthropicAdapter(api_key="sk-test", model="claude-haiku-3-5",
                             system_prompt="You are a novelist.")
        sys_attr = getattr(a, 'system_prompt', None) or getattr(a, '_system', '')
        assert "novelist" in sys_attr


# ─────────────────────────────────────────────
# OllamaAdapter — urllib 기반
# ─────────────────────────────────────────────
def _make_ollama(**kwargs):
    from literary_system.llm_bridge.adapters.ollama_adapter import OllamaAdapter
    defaults = dict(base_url="http://localhost:11434", model="llama3")
    defaults.update(kwargs)
    return OllamaAdapter(**defaults)


def _make_urllib_response(data: dict, status: int = 200):
    """urllib.request.urlopen context manager mock"""
    body = json.dumps(data).encode()
    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_cm)
    mock_cm.__exit__ = MagicMock(return_value=False)
    mock_cm.read.return_value = body
    mock_cm.status = status
    return mock_cm


class TestOllamaAdapterInit:
    def test_provider_id(self):
        a = _make_ollama()
        assert a.get_provider_id() == "ollama"

    def test_base_url_stored(self):
        a = _make_ollama(base_url="http://remote:11434")
        url = getattr(a, 'base_url', None) or getattr(a, '_base_url', '')
        assert "remote" in url

    def test_model_stored(self):
        a = _make_ollama(model="mistral")
        model = getattr(a, 'model', None) or getattr(a, '_model', '')
        assert model == "mistral"

    def test_default_timeout_positive(self):
        a = _make_ollama()
        t = getattr(a, 'timeout', None) or getattr(a, '_timeout', 0)
        assert t > 0

    def test_custom_timeout(self):
        a = _make_ollama(timeout=120)
        t = getattr(a, 'timeout', None) or getattr(a, '_timeout', 0)
        assert t == 120


class TestOllamaAdapterAvailability:
    def test_is_available_connection_error(self):
        import urllib.error
        a = _make_ollama()
        with patch('urllib.request.urlopen',
                   side_effect=urllib.error.URLError("connection refused")):
            assert a.is_available() is False

    def test_is_available_timeout(self):
        import urllib.error
        a = _make_ollama()
        with patch('urllib.request.urlopen',
                   side_effect=urllib.error.URLError("timed out")):
            assert a.is_available() is False

    def test_is_available_generic_exception(self):
        a = _make_ollama()
        with patch('urllib.request.urlopen', side_effect=OSError("fail")):
            assert a.is_available() is False

    def test_is_available_success(self):
        a = _make_ollama()
        cm = _make_urllib_response({"models": [{"name": "llama3"}]})
        with patch('urllib.request.urlopen', return_value=cm):
            result = a.is_available()
        assert result is True

    def test_is_available_returns_bool(self):
        a = _make_ollama()
        import urllib.error
        with patch('urllib.request.urlopen',
                   side_effect=urllib.error.URLError("x")):
            result = a.is_available()
        assert isinstance(result, bool)


class TestOllamaAdapterGenerate:
    def test_generate_returns_string(self):
        a = _make_ollama()
        cm = _make_urllib_response({"response": "안녕하세요, 저는 llama입니다."})
        with patch('urllib.request.urlopen', return_value=cm):
            result = a.generate("테스트 프롬프트")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_raises_on_url_error(self):
        import urllib.error
        a = _make_ollama()
        with patch('urllib.request.urlopen',
                   side_effect=urllib.error.URLError("connection refused")):
            with pytest.raises(Exception):
                a.generate("prompt")

    def test_generate_contains_response_text(self):
        a = _make_ollama()
        cm = _make_urllib_response({"response": "특별한 응답 텍스트"})
        with patch('urllib.request.urlopen', return_value=cm):
            result = a.generate("프롬프트")
        assert "특별한 응답 텍스트" in result

    def test_generate_with_system_prompt(self):
        a = _make_ollama(system_prompt="당신은 작가입니다.")
        cm = _make_urllib_response({"response": "네, 작가입니다."})
        with patch('urllib.request.urlopen', return_value=cm):
            result = a.generate("소설을 써주세요")
        assert isinstance(result, str)


class TestOllamaListModels:
    def test_list_models_returns_list(self):
        a = _make_ollama()
        cm = _make_urllib_response({"models": [{"name": "llama3"}, {"name": "mistral"}]})
        with patch('urllib.request.urlopen', return_value=cm):
            models = a.list_models()
        assert isinstance(models, list)
        assert "llama3" in models

    def test_list_models_empty_on_error(self):
        import urllib.error
        a = _make_ollama()
        with patch('urllib.request.urlopen',
                   side_effect=urllib.error.URLError("no server")):
            models = a.list_models()
        assert isinstance(models, list)

    def test_list_models_multiple(self):
        a = _make_ollama()
        cm = _make_urllib_response({
            "models": [{"name": "llama3"}, {"name": "phi3"}, {"name": "mistral"}]
        })
        with patch('urllib.request.urlopen', return_value=cm):
            models = a.list_models()
        assert len(models) == 3
