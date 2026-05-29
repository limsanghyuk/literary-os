"""
Gate 21: SceneGenerationPipeline + LLM Adapter Layer 생존 검증 (V484 신설)
"""
from __future__ import annotations


def _gate_scene_pipeline() -> dict:
    """SceneGenerationPipeline, AnthropicAdapters, OllamaAdapter 심볼 생존 검증."""
    try:
        # V484 어댑터 레이어
        from literary_system.llm_bridge.adapters.anthropic_adapter import (
            AnthropicHaikuAdapter,
            AnthropicSonnetAdapter,
        )
        from literary_system.llm_bridge.adapters.ollama_adapter import OllamaAdapter
        from literary_system.llm_bridge.gateway.unified_llm_gateway import UnifiedLLMGateway

        # LLMContext + UnifiedLLMGateway (Phase 2 핵심)
        from literary_system.llm_bridge.llm_context import LLMContext

        # V484 SceneGenerationPipeline
        from literary_system.pipelines.scene_generation_pipeline import (
            GeneratedScene,
            SceneGenerationPipeline,
            SceneGenerationResult,
        )

        symbols_verified = [
            "AnthropicHaikuAdapter",
            "AnthropicSonnetAdapter",
            "OllamaAdapter",
            "SceneGenerationPipeline",
            "GeneratedScene",
            "SceneGenerationResult",
            "LLMContext",
            "UnifiedLLMGateway",
        ]

        # 기본 인스턴스화 스모크 테스트
        assert hasattr(AnthropicHaikuAdapter, 'generate'), "AnthropicHaikuAdapter.generate 없음"
        assert hasattr(AnthropicSonnetAdapter, 'generate'), "AnthropicSonnetAdapter.generate 없음"
        assert hasattr(OllamaAdapter, 'generate'), "OllamaAdapter.generate 없음"
        assert hasattr(SceneGenerationPipeline, 'run'), "SceneGenerationPipeline.run 없음"

        return {
            "pass": True,
            "symbols_verified": symbols_verified,
            "count": len(symbols_verified),
            "gate": "Gate 21: SceneGenerationPipeline + LLM Adapter Layer",
        }

    except Exception as e:
        import traceback
        return {
            "pass": False,
            "reason": str(e),
            "traceback": traceback.format_exc(),
        }
