"""
V434 -- CascadeOrchestrator + SemanticCache + StreamingNormalizer
"""
from __future__ import annotations
import logging

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional

from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface
from literary_system.llm_bridge.adapter_contract import AdapterContractV2

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SemanticCache
# ---------------------------------------------------------------------------

@dataclass
class LLMCacheEntry:
    """Single cache entry with TTL support."""
    response:    str
    created_at:  float = field(default_factory=time.time)
    hit_count:   int   = 0

    def is_expired(self, ttl_seconds: float) -> bool:
        return (time.time() - self.created_at) > ttl_seconds


class SemanticCache:
    """
    In-memory semantic cache keyed by SHA256(prompt).
    TTL default: 86400s (24 hours).
    Interface mirrors Redis-backed implementation (V435 upgrade path).
    """

    DEFAULT_TTL = 86_400.0

    def __init__(self, ttl: float = DEFAULT_TTL) -> None:
        self._store: Dict[str, CacheEntry] = {}
        self.ttl = ttl
        self._hits  = 0
        self._misses = 0

    @staticmethod
    def cache_key(prompt: str, model_id: str = "", extra: str = "") -> str:
        raw = prompt + "|" + model_id + "|" + extra
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[str]:
        entry = self._store.get(key)
        if entry is None:
            self._misses += 1
            return None
        if entry.is_expired(self.ttl):
            del self._store[key]
            self._misses += 1
            return None
        entry.hit_count += 1
        self._hits += 1
        return entry.response

    def set(self, key: str, response: str) -> None:
        self._store[key] = CacheEntry(response=response)

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @property
    def size(self) -> int:
        return len(self._store)

    def stats(self) -> dict:
        return {
            "hits":     self._hits,
            "misses":   self._misses,
            "hit_rate": round(self.hit_rate, 4),
            "size":     self.size,
            "ttl":      self.ttl,
        }


# ---------------------------------------------------------------------------
# StreamingNormalizer
# ---------------------------------------------------------------------------

@dataclass
class ChunkEvent:
    """Standard streaming chunk event (provider-agnostic)."""
    text:        str
    provider:    str  = ""
    is_final:    bool = False
    token_count: int  = 0
    metadata:    dict = field(default_factory=dict)


class StreamingNormalizer:
    """
    Normalize Anthropic / OpenAI / Ollama SSE into standard ChunkEvent.
    Usage:
        normalizer = StreamingNormalizer(provider="anthropic")
        for event in normalizer.normalize(raw_stream):
            logger.debug(event.text, end="")
    """

    SUPPORTED_PROVIDERS = {"anthropic", "openai", "ollama", "plain"}

    def __init__(self, provider: str = "plain") -> None:
        if provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(
                "Unsupported provider: " + provider
            )
        self.provider = provider

    def normalize(self, chunks: Iterator[Any]) -> Iterator[ChunkEvent]:
        handler = getattr(self, "_normalize_" + self.provider)
        yield from handler(chunks)

    def normalize_text(self, full_text: str) -> List[ChunkEvent]:
        """Wrap complete text as single-chunk event list."""
        return [ChunkEvent(text=full_text, provider=self.provider, is_final=True)]

    def _normalize_plain(self, chunks: Iterator[str]) -> Iterator[ChunkEvent]:
        for chunk in chunks:
            text = chunk if isinstance(chunk, str) else str(chunk)
            yield ChunkEvent(text=text, provider="plain")
        yield ChunkEvent(text="", provider="plain", is_final=True)

    def _normalize_anthropic(self, chunks: Iterator[Any]) -> Iterator[ChunkEvent]:
        """Anthropic SSE: content_block_delta -> delta.text, message_stop -> is_final"""
        for chunk in chunks:
            chunk_type = (
                chunk.get("type") if isinstance(chunk, dict)
                else getattr(chunk, "type", "")
            )
            if chunk_type == "content_block_delta":
                delta = (
                    chunk.get("delta", {}) if isinstance(chunk, dict)
                    else getattr(chunk, "delta", {})
                )
                text = (
                    delta.get("text", "") if isinstance(delta, dict)
                    else getattr(delta, "text", "")
                )
                yield ChunkEvent(text=text, provider="anthropic")
            elif chunk_type == "message_stop":
                yield ChunkEvent(text="", provider="anthropic", is_final=True)

    def _normalize_openai(self, chunks: Iterator[Any]) -> Iterator[ChunkEvent]:
        """OpenAI SSE: choices[0].delta.content, finish_reason=stop -> is_final"""
        for chunk in chunks:
            if isinstance(chunk, dict):
                choices = chunk.get("choices", [{}])
                delta = choices[0].get("delta", {}) if choices else {}
                text = delta.get("content", "") or ""
                finish = choices[0].get("finish_reason") if choices else None
                yield ChunkEvent(
                    text=text, provider="openai",
                    is_final=(finish == "stop"),
                )
            else:
                choices = getattr(chunk, "choices", [])
                if choices:
                    delta  = getattr(choices[0], "delta", None)
                    text   = getattr(delta, "content", "") or ""
                    finish = getattr(choices[0], "finish_reason", None)
                    yield ChunkEvent(
                        text=text, provider="openai",
                        is_final=(finish == "stop"),
                    )

    def _normalize_ollama(self, chunks: Iterator[Any]) -> Iterator[ChunkEvent]:
        """Ollama SSE (OpenAI-compatible). Falls through to OpenAI normalizer."""
        for event in self._normalize_openai(chunks):
            event.provider = "ollama"
            yield event


# ---------------------------------------------------------------------------
# CascadeOrchestrator
# ---------------------------------------------------------------------------

class CascadeOrchestrator:
    """
    2-stage cascade: speed adapter draft -> quality adapter polish.
    LLM-0 compliant: escalate_fn is caller-provided, no scoring inside generate().
    """

    def __init__(
        self,
        speed_adapter:   LLMBridgeInterface,
        quality_adapter: LLMBridgeInterface,
        cache:           Optional[SemanticCache] = None,
        escalate_fn:     Optional[Any] = None,
        use_cache:       bool = True,
    ) -> None:
        self._speed   = speed_adapter
        self._quality = quality_adapter
        self._cache   = cache or SemanticCache()
        self._escalate = escalate_fn
        self._use_cache = use_cache
        self._draft_count:  int = 0
        self._polish_count: int = 0
        self._cache_hits:   int = 0

    def generate(
        self,
        prompt: str,
        context: Any = None,
        model_id_hint: str = "",
    ) -> str:
        """Run cascade. Returns polished text if escalated, otherwise draft."""
        if self._use_cache:
            cache_key = SemanticCache.cache_key(prompt, model_id_hint)
            cached = self._cache.get(cache_key)
            if cached is not None:
                self._cache_hits += 1
                return cached

        draft = self._speed.generate(prompt, context)
        self._draft_count += 1

        if not draft:
            return ""

        should_escalate = False
        if self._escalate is not None:
            should_escalate = self._escalate(draft)

        if should_escalate:
            polish_prompt = "Improve and polish the following text:\n\n" + draft
            result = self._quality.generate(polish_prompt, context)
            self._polish_count += 1
            if not result:
                result = draft
        else:
            result = draft

        if self._use_cache:
            self._cache.set(cache_key, result)

        return result

    @property
    def stats(self) -> dict:
        return {
            "draft_count":  self._draft_count,
            "polish_count": self._polish_count,
            "cache_hits":   self._cache_hits,
            "escalation_rate": (
                round(self._polish_count / self._draft_count, 4)
                if self._draft_count > 0 else 0.0
            ),
        }

CacheEntry = LLMCacheEntry  # V579 backward-compat alias
