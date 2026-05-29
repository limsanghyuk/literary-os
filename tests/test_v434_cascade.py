"""
V434 -- SemanticCache + StreamingNormalizer + CascadeOrchestrator tests
"""
from __future__ import annotations

import time
import pytest
from unittest.mock import MagicMock

from literary_system.llm_bridge.cascade import (
    CacheEntry, SemanticCache, ChunkEvent, StreamingNormalizer, CascadeOrchestrator,
)


# ---------------------------------------------------------------------------
# CacheEntry
# ---------------------------------------------------------------------------

class TestCacheEntry:
    def test_not_expired(self):
        entry = CacheEntry(response="ok")
        assert entry.is_expired(60.0) is False

    def test_expired(self):
        entry = CacheEntry(response="ok", created_at=time.time() - 100)
        assert entry.is_expired(60.0) is True


# ---------------------------------------------------------------------------
# SemanticCache
# ---------------------------------------------------------------------------

class TestSemanticCache:
    def test_cache_key_deterministic(self):
        k1 = SemanticCache.cache_key("hello", "model")
        k2 = SemanticCache.cache_key("hello", "model")
        assert k1 == k2

    def test_cache_key_different_inputs(self):
        k1 = SemanticCache.cache_key("hello")
        k2 = SemanticCache.cache_key("world")
        assert k1 != k2

    def test_miss_on_empty(self):
        cache = SemanticCache()
        assert cache.get("any_key") is None

    def test_set_and_get(self):
        cache = SemanticCache()
        cache.set("k", "response_text")
        assert cache.get("k") == "response_text"

    def test_expired_entry_returns_none(self):
        cache = SemanticCache(ttl=0.01)
        cache.set("k", "value")
        time.sleep(0.02)
        assert cache.get("k") is None

    def test_hit_rate(self):
        cache = SemanticCache()
        cache.set("k", "v")
        cache.get("k")   # hit
        cache.get("no")  # miss
        assert cache.hit_rate == 0.5

    def test_stats(self):
        cache = SemanticCache()
        cache.set("k", "v")
        cache.get("k")
        s = cache.stats()
        assert s["hits"] == 1
        assert "size" in s
        assert "ttl" in s

    def test_invalidate(self):
        cache = SemanticCache()
        cache.set("k", "v")
        cache.invalidate("k")
        assert cache.get("k") is None

    def test_clear(self):
        cache = SemanticCache()
        cache.set("a", "1")
        cache.set("b", "2")
        cache.clear()
        assert cache.size == 0


# ---------------------------------------------------------------------------
# StreamingNormalizer
# ---------------------------------------------------------------------------

class TestStreamingNormalizer:
    def test_unsupported_provider_raises(self):
        with pytest.raises(ValueError):
            StreamingNormalizer(provider="unknown")

    def test_normalize_text_single_chunk(self):
        n = StreamingNormalizer(provider="plain")
        events = n.normalize_text("hello world")
        assert len(events) == 1
        assert events[0].text == "hello world"
        assert events[0].is_final is True

    def test_normalize_plain(self):
        n = StreamingNormalizer(provider="plain")
        events = list(n.normalize(iter(["chunk1", "chunk2"])))
        texts = [e.text for e in events]
        assert "chunk1" in texts
        assert "chunk2" in texts
        assert events[-1].is_final is True

    def test_normalize_anthropic_dict(self):
        n = StreamingNormalizer(provider="anthropic")
        chunks = [
            {"type": "content_block_delta", "delta": {"text": "Hello"}},
            {"type": "content_block_delta", "delta": {"text": " World"}},
            {"type": "message_stop"},
        ]
        events = list(n.normalize(iter(chunks)))
        texts = [e.text for e in events]
        assert "Hello" in texts
        assert " World" in texts
        assert events[-1].is_final is True

    def test_normalize_openai_dict(self):
        n = StreamingNormalizer(provider="openai")
        chunks = [
            {"choices": [{"delta": {"content": "Hi"}, "finish_reason": None}]},
            {"choices": [{"delta": {"content": "!"}, "finish_reason": "stop"}]},
        ]
        events = list(n.normalize(iter(chunks)))
        assert events[0].text == "Hi"
        assert events[1].is_final is True

    def test_normalize_ollama_sets_provider(self):
        n = StreamingNormalizer(provider="ollama")
        chunks = [
            {"choices": [{"delta": {"content": "data"}, "finish_reason": "stop"}]},
        ]
        events = list(n.normalize(iter(chunks)))
        assert all(e.provider == "ollama" for e in events)

    def test_normalize_anthropic_object(self):
        n = StreamingNormalizer(provider="anthropic")
        delta = MagicMock()
        delta.text = "chunk"
        chunk = MagicMock()
        chunk.type = "content_block_delta"
        chunk.delta = delta
        stop = MagicMock()
        stop.type = "message_stop"
        events = list(n.normalize(iter([chunk, stop])))
        assert events[0].text == "chunk"
        assert events[-1].is_final is True


# ---------------------------------------------------------------------------
# CascadeOrchestrator
# ---------------------------------------------------------------------------

def _make_mock_adapter(response: str):
    adapter = MagicMock()
    adapter.generate.return_value = response
    return adapter


class TestCascadeOrchestrator:
    def test_draft_only_when_no_escalation(self):
        speed = _make_mock_adapter("speed draft")
        quality = _make_mock_adapter("quality polish")
        orch = CascadeOrchestrator(speed, quality, escalate_fn=None, use_cache=False)
        result = orch.generate("prompt")
        assert result == "speed draft"
        quality.generate.assert_not_called()

    def test_escalates_when_fn_returns_true(self):
        speed = _make_mock_adapter("short")
        quality = _make_mock_adapter("polished long text")
        orch = CascadeOrchestrator(
            speed, quality,
            escalate_fn=lambda draft: len(draft) < 10,
            use_cache=False,
        )
        result = orch.generate("prompt")
        assert result == "polished long text"
        assert orch.stats["polish_count"] == 1

    def test_no_escalation_when_fn_returns_false(self):
        speed = _make_mock_adapter("a long enough draft text")
        quality = _make_mock_adapter("quality")
        orch = CascadeOrchestrator(
            speed, quality,
            escalate_fn=lambda draft: len(draft) < 5,
            use_cache=False,
        )
        result = orch.generate("prompt")
        assert result == "a long enough draft text"
        assert orch.stats["polish_count"] == 0

    def test_fallback_to_draft_if_polish_empty(self):
        speed = _make_mock_adapter("draft text")
        quality = _make_mock_adapter("")  # quality fails
        orch = CascadeOrchestrator(
            speed, quality,
            escalate_fn=lambda d: True,
            use_cache=False,
        )
        result = orch.generate("prompt")
        assert result == "draft text"

    def test_cache_hit_skips_adapters(self):
        speed = _make_mock_adapter("speed response")
        quality = _make_mock_adapter("quality response")
        cache = SemanticCache()
        orch = CascadeOrchestrator(speed, quality, cache=cache, use_cache=True)

        result1 = orch.generate("same prompt")
        result2 = orch.generate("same prompt")  # should hit cache

        assert result1 == result2
        assert orch.stats["cache_hits"] == 1
        assert speed.generate.call_count == 1  # only called once

    def test_empty_draft_returns_empty(self):
        speed = _make_mock_adapter("")
        quality = _make_mock_adapter("quality")
        orch = CascadeOrchestrator(speed, quality, use_cache=False)
        result = orch.generate("prompt")
        assert result == ""
        quality.generate.assert_not_called()

    def test_stats_escalation_rate(self):
        speed = _make_mock_adapter("draft")
        quality = _make_mock_adapter("polished")
        orch = CascadeOrchestrator(
            speed, quality,
            escalate_fn=lambda d: True,
            use_cache=False,
        )
        orch.generate("p1")
        orch.generate("p2")
        s = orch.stats
        assert s["draft_count"] == 2
        assert s["polish_count"] == 2
        assert s["escalation_rate"] == 1.0
