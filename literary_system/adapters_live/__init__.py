"""
literary_system.adapters_live
Phase 3 SP1 — 실 LLM 어댑터 패키지.

V451: RealClaudeAdapter
V452: RealOpenAIAdapter
V453: RealOllamaAdapter + BGE-M3
"""

from literary_system.adapters_live.real_claude_adapter import (
    LiveAdapterCall,
    RealClaudeAdapter,
    RealClaudeAdapterConfig,
    RealLLMResponse,
)
from literary_system.adapters_live.real_ollama_adapter import (
    GPUMemorySnapshot,
    RealOllamaAdapter,
    RealOllamaAdapterConfig,
)
from literary_system.adapters_live.real_openai_adapter import (
    RealOpenAIAdapter,
    RealOpenAIAdapterConfig,
)

__all__ = [
    # V451
    "RealClaudeAdapter",
    "RealClaudeAdapterConfig",
    "RealLLMResponse",
    "LiveAdapterCall",
    # V452
    "RealOpenAIAdapter",
    "RealOpenAIAdapterConfig",
    # V453
    "RealOllamaAdapter",
    "RealOllamaAdapterConfig",
    "GPUMemorySnapshot",
]
