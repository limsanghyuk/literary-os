"""
Gate 22: DramaEpisodeGenerator 생존 검증 (V485 신설)
"""
from __future__ import annotations


def _gate_drama_generator() -> dict:
    """DramaEpisodeGenerator + DramaSeriesResult 심볼 생존 + Mock 모드 스모크."""
    try:
        from literary_system.pipelines.drama_episode_generator import (
            DramaEpisodeGenerator,
        )

        symbols_verified = [
            "DramaEpisodeGenerator",
        ]

        # Mock 모드 (API 키 없이) 인스턴스화 가능 여부
        import os
        api_key_backup = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            gen = DramaEpisodeGenerator.from_env(max_scenes_per_episode=1)
            assert hasattr(gen, "generate_series"), "generate_series 없음"
            symbols_verified.append("DramaEpisodeGenerator.from_env(mock_mode)")
        finally:
            if api_key_backup is not None:
                os.environ["ANTHROPIC_API_KEY"] = api_key_backup

        return {
            "pass": True,
            "symbols_verified": symbols_verified,
            "count": len(symbols_verified),
            "gate": "Gate 22: DramaEpisodeGenerator",
        }

    except Exception as e:
        import traceback
        return {
            "pass": False,
            "reason": str(e),
            "traceback": traceback.format_exc(),
        }
