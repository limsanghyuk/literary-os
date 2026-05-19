"""
literary_system/pipelines/drama_episode_generator.py
V485 — DramaEpisodeGenerator

시리즈 설정과 UnifiedLLMGateway를 받아 N화 연속 생성.
ANTHROPIC_API_KEY 설정 시 실 Claude API, 미설정 시 Mock 자동 폴백.

인터페이스:
  DramaEpisodeGenerator.generate_series(n_episodes) → DramaSeriesResult
  DramaEpisodeGenerator.generate_episode(ep_idx)   → SceneGenerationResult

사용:
  gen = DramaEpisodeGenerator.from_env(series_config)
  result = gen.generate_series(5)
  logger.debug(result.full_script())
"""
from __future__ import annotations

import os
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from literary_system.episode.episode_structure_calculator import EpisodeStructureConfig
from literary_system.pipelines.scene_generation_pipeline import (
    SceneGenerationPipeline, SceneGenerationResult,
)

logger = logging.getLogger(__name__)


# ── 시리즈 설정 ───────────────────────────────────────────────────

@dataclass
class DramaSeriesConfig:
    """드라마 시리즈 메타데이터."""
    title: str = "Literary OS 시범 드라마"
    genre: str = "로맨틱 스릴러"
    total_episodes: int = 16
    runtime_min: float = 60.0
    act_structure: str = "5act"
    characters: List[str] = field(default_factory=lambda: [
        "강서준 (남주, 검사)", "이도아 (여주, 법의학자)",
        "박기연 (악역, 재벌 2세)", "최유진 (서브, 형사)",
    ])
    logline: str = "진실을 추적하는 검사와 죽음의 비밀을 풀어가는 법의학자의 엇갈린 사랑."

    def to_episode_context(self, ep_idx: int) -> Dict[str, Any]:
        return {
            "series_title": self.title,
            "genre": self.genre,
            "episode_idx": ep_idx,
            "characters": self.characters,
            "logline": self.logline,
            "total_episodes": self.total_episodes,
        }


# ── 시리즈 결과 ────────────────────────────────────────────────────

@dataclass
class DramaSeriesResult:
    """N화 연속 생성 결과."""
    series_config: DramaSeriesConfig
    episode_results: List[SceneGenerationResult] = field(default_factory=list)
    total_elapsed_s: float = 0.0

    @property
    def total_episodes_generated(self) -> int:
        return len(self.episode_results)

    @property
    def total_scenes_generated(self) -> int:
        return sum(r.success_count for r in self.episode_results)

    @property
    def total_word_count(self) -> int:
        return sum(r.total_word_count for r in self.episode_results)

    @property
    def success_rate(self) -> float:
        total = sum(len(r.scenes) for r in self.episode_results)
        if total == 0:
            return 0.0
        success = sum(r.success_count for r in self.episode_results)
        return round(success / total, 3)

    def episode_summary(self) -> List[dict]:
        return [
            {
                "episode": r.episode_idx + 1,
                "scenes": r.success_count,
                "words": r.total_word_count,
                "elapsed_s": r.total_elapsed_s,
            }
            for r in self.episode_results
        ]

    def full_script(self) -> str:
        """전체 시리즈 스크립트 합본."""
        parts = [
            f"{'='*70}",
            f"  {self.series_config.title}",
            f"  장르: {self.series_config.genre}",
            f"  로그라인: {self.series_config.logline}",
            f"{'='*70}\n",
        ]
        for r in self.episode_results:
            parts.append(f"\n{'#'*70}")
            parts.append(f"  {r.episode_idx + 1}화")
            parts.append(f"{'#'*70}")
            parts.append(r.full_text())
        return "\n".join(parts)

    def to_dict(self) -> dict:
        return {
            "series_title": self.series_config.title,
            "total_episodes_generated": self.total_episodes_generated,
            "total_scenes_generated": self.total_scenes_generated,
            "total_word_count": self.total_word_count,
            "success_rate": self.success_rate,
            "total_elapsed_s": round(self.total_elapsed_s, 2),
            "episodes": self.episode_summary(),
        }


# ── 메인 생성기 ────────────────────────────────────────────────────

class DramaEpisodeGenerator:
    """
    V485 — 드라마 시리즈 LLM 생성기.

    ANTHROPIC_API_KEY 설정 → AnthropicAdapter (real LLM)
    미설정 → MockLLMBridge (테스트용)
    """

    def __init__(
        self,
        pipeline: SceneGenerationPipeline,
        series_config: Optional[DramaSeriesConfig] = None,
    ) -> None:
        self._pipeline      = pipeline
        self._series_config = series_config or DramaSeriesConfig()

    @classmethod
    def from_env(
        cls,
        series_config: Optional[DramaSeriesConfig] = None,
        max_scenes_per_episode: Optional[int] = None,
    ) -> "DramaEpisodeGenerator":
        """
        환경변수에서 API 키를 읽어 적절한 gateway를 자동 선택.

        ANTHROPIC_API_KEY 있음 → Claude Sonnet + Haiku + Ollama 3-tier
        없음 → MockLLMBridge 폴백
        """
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        sc = series_config or DramaSeriesConfig()

        if api_key:
            gateway = cls._make_real_gateway(api_key)
            logger.info("DramaEpisodeGenerator: 실 LLM 연결 (ANTHROPIC_API_KEY 설정됨)")
        else:
            gateway = cls._make_mock_gateway()
            logger.info("DramaEpisodeGenerator: MockLLMBridge 폴백 (ANTHROPIC_API_KEY 미설정)")

        pipeline = SceneGenerationPipeline(
            gateway=gateway,
            max_scenes=max_scenes_per_episode,
        )
        return cls(pipeline=pipeline, series_config=sc)

    @classmethod
    def _make_real_gateway(cls, api_key: str):
        """AnthropicSonnet + AnthropicHaiku + Ollama 3-tier gateway."""
        from literary_system.llm_bridge.adapters.anthropic_adapter import (
            AnthropicSonnetAdapter, AnthropicHaikuAdapter,
        )
        from literary_system.llm_bridge.adapters.ollama_adapter import OllamaAdapter
        from literary_system.llm_bridge.health.provider_health_monitor import ProviderHealthMonitor
        from literary_system.llm_bridge.routing.task_router import TaskRouter
        from literary_system.llm_bridge.gateway.unified_llm_gateway import UnifiedLLMGateway

        providers = {
            "local":   OllamaAdapter(),
            "speed":   AnthropicHaikuAdapter(api_key=api_key),
            "quality": AnthropicSonnetAdapter(api_key=api_key),
        }
        health = ProviderHealthMonitor({
            p.get_provider_id(): p for p in providers.values()
        })
        router = TaskRouter(providers=providers, health_monitor=health)
        return UnifiedLLMGateway(task_router=router, health_monitor=health)

    @classmethod
    def _make_mock_gateway(cls):
        """MockLLMBridge 기반 테스트용 gateway."""
        from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge
        from literary_system.llm_bridge.routing.task_router import TaskRouter
        from literary_system.llm_bridge.gateway.unified_llm_gateway import UnifiedLLMGateway

        mock_response = (
            "[씬 시작]\n"
            "강서준이 법정 복도를 걷는다. 발소리가 대리석 바닥에 울린다.\n\n"
            "강서준: (낮게) 증거가 사라졌어.\n\n"
            "이도아: (눈이 흔들린다) 무슨 말이에요?\n\n"
            "강서준: (서류를 건네며) 직접 봐. 누군가 조직적으로 지우고 있어.\n\n"
            "이도아는 서류를 훑는다. 손이 미세하게 떨린다.\n\n"
            "이도아: (독백) 이게 끝이 아니야. 시작이야.\n\n"
            "[씬 끝]"
        )
        mock = MockLLMBridge(scripted_response=mock_response)
        providers = {
            "local": mock, "speed": mock, "quality": mock,
        }
        router = TaskRouter(providers=providers)
        return UnifiedLLMGateway(task_router=router, health_monitor=None)

    # ── 공개 API ──────────────────────────────────────────────────

    def generate_episode(
        self,
        ep_idx: int,
        custom_context: Optional[Dict[str, Any]] = None,
    ) -> SceneGenerationResult:
        """단일 에피소드 생성."""
        config = EpisodeStructureConfig(
            episode_idx=ep_idx,
            total_episodes=self._series_config.total_episodes,
            runtime_min=self._series_config.runtime_min,
            act_structure=self._series_config.act_structure,
        )
        ep_ctx = self._series_config.to_episode_context(ep_idx)
        if custom_context:
            ep_ctx.update(custom_context)

        return self._pipeline.run(config=config, episode_context=ep_ctx)

    def generate_series(
        self,
        n_episodes: int = 5,
        start_episode: int = 0,
    ) -> DramaSeriesResult:
        """
        n_episodes개 화 연속 생성.

        Args:
            n_episodes: 생성할 화 수 (기본 5)
            start_episode: 시작 화 인덱스 (0-based, 기본 0)
        """
        t_start = time.monotonic()
        results: List[SceneGenerationResult] = []

        for ep_offset in range(n_episodes):
            ep_idx = start_episode + ep_offset
            logger.info("생성 중: %d화 (%d/%d)", ep_idx + 1, ep_offset + 1, n_episodes)
            try:
                result = self.generate_episode(ep_idx)
                results.append(result)
                logger.info(
                    "  → %d화 완료: %d씬, %d어, %.1fs",
                    ep_idx + 1, result.success_count,
                    result.total_word_count, result.total_elapsed_s,
                )
            except Exception as exc:
                logger.error("  → %d화 생성 실패: %s", ep_idx + 1, exc)

        elapsed = time.monotonic() - t_start
        return DramaSeriesResult(
            series_config=self._series_config,
            episode_results=results,
            total_elapsed_s=round(elapsed, 2),
        )
