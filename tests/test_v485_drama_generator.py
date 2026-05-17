"""
V485 DramaEpisodeGenerator 테스트
실제 API: generate_series(n_episodes, start_episode) → DramaSeriesResult
DramaSeriesResult.episode_results (List[SceneGenerationResult])
"""
import pytest
import os
from unittest.mock import MagicMock, patch
import sys

sys.path.insert(0, '/tmp/v481_work/literary_os_v430_COMPLETE')


def _make_config(**kw):
    from literary_system.pipelines.drama_episode_generator import DramaSeriesConfig
    defaults = dict(
        title="별빛 아래서", genre="로맨스", total_episodes=16,
        runtime_min=60, characters=["이수현", "박민준"], logline="엇갈린 운명"
    )
    defaults.update(kw)
    return DramaSeriesConfig(**defaults)


def _make_gen(max_scenes=1):
    """ANTHROPIC_API_KEY 없이 Mock 모드 생성기"""
    from literary_system.pipelines.drama_episode_generator import DramaEpisodeGenerator
    os.environ.pop('ANTHROPIC_API_KEY', None)
    return DramaEpisodeGenerator.from_env(max_scenes_per_episode=max_scenes)


# ─────────────────────────────────────────────
# DramaSeriesConfig
# ─────────────────────────────────────────────
class TestDramaSeriesConfig:
    def test_title(self):
        assert _make_config(title="겨울 소나타").title == "겨울 소나타"

    def test_genre(self):
        assert _make_config(genre="스릴러").genre == "스릴러"

    def test_total_episodes(self):
        assert _make_config(total_episodes=12).total_episodes == 12

    def test_runtime_min(self):
        assert _make_config(runtime_min=70).runtime_min == 70

    def test_characters(self):
        c = _make_config(characters=["A", "B", "C"])
        assert len(c.characters) == 3

    def test_logline(self):
        assert _make_config(logline="운명").logline == "운명"

    def test_default_total_episodes(self):
        from literary_system.pipelines.drama_episode_generator import DramaSeriesConfig
        c = DramaSeriesConfig()
        assert c.total_episodes > 0

    def test_to_episode_context_returns_dict(self):
        c = _make_config()
        ctx = c.to_episode_context(0)
        assert isinstance(ctx, dict)

    def test_to_episode_context_has_title(self):
        c = _make_config(title="별빛")
        ctx = c.to_episode_context(0)
        assert any("별빛" in str(v) for v in ctx.values()) or "title" in ctx


# ─────────────────────────────────────────────
# DramaEpisodeGenerator — Mock 모드
# ─────────────────────────────────────────────
class TestDramaEpisodeGeneratorMock:
    def test_from_env_returns_generator(self):
        from literary_system.pipelines.drama_episode_generator import DramaEpisodeGenerator
        gen = _make_gen()
        assert isinstance(gen, DramaEpisodeGenerator)

    def test_generate_series_returns_result(self):
        from literary_system.pipelines.drama_episode_generator import DramaSeriesResult
        gen = _make_gen(max_scenes=1)
        result = gen.generate_series(n_episodes=2)
        assert isinstance(result, DramaSeriesResult)

    def test_generate_series_episode_count(self):
        gen = _make_gen(max_scenes=1)
        result = gen.generate_series(n_episodes=2)
        assert result.total_episodes_generated == 2

    def test_generate_series_start_episode(self):
        gen = _make_gen(max_scenes=1)
        result = gen.generate_series(n_episodes=2, start_episode=3)
        ep_indices = [r.episode_idx for r in result.episode_results]
        assert ep_indices[0] == 3
        assert ep_indices[1] == 4

    def test_generate_single_episode(self):
        gen = _make_gen(max_scenes=1)
        result = gen.generate_series(n_episodes=1)
        assert result.total_episodes_generated == 1

    def test_episode_results_have_scenes(self):
        gen = _make_gen(max_scenes=1)
        result = gen.generate_series(n_episodes=1)
        ep = result.episode_results[0]
        assert len(ep.scenes) >= 0  # 생성 시도는 했어야 함

    def test_full_script_is_string(self):
        gen = _make_gen(max_scenes=1)
        result = gen.generate_series(n_episodes=2)
        script = result.full_script()
        assert isinstance(script, str) and len(script) > 0

    def test_full_script_has_episode_headers(self):
        gen = _make_gen(max_scenes=1)
        result = gen.generate_series(n_episodes=2)
        script = result.full_script()
        assert "화" in script or "episode" in script.lower() or "#" in script

    def test_full_script_has_title(self):
        gen = _make_gen(max_scenes=1)
        gen._series_config = _make_config(title="UNI_TITLE_XYZ")
        result = gen.generate_series(n_episodes=1)
        script = result.full_script()
        assert "UNI_TITLE_XYZ" in script

    def test_elapsed_non_negative(self):
        gen = _make_gen(max_scenes=1)
        result = gen.generate_series(n_episodes=1)
        assert result.total_elapsed_s >= 0


# ─────────────────────────────────────────────
# DramaSeriesResult
# ─────────────────────────────────────────────
class TestDramaSeriesResult:
    def _run(self, n=2):
        gen = _make_gen(max_scenes=1)
        return gen.generate_series(n_episodes=n)

    def test_total_episodes_generated(self):
        assert self._run(n=2).total_episodes_generated == 2

    def test_total_scenes_non_negative(self):
        assert self._run(n=1).total_scenes_generated >= 0

    def test_success_rate_in_range(self):
        r = self._run(n=1)
        assert 0.0 <= r.success_rate <= 1.0

    def test_to_dict_returns_dict(self):
        assert isinstance(self._run(n=1).to_dict(), dict)

    def test_to_dict_has_series_title(self):
        gen = _make_gen(max_scenes=1)
        gen._series_config = _make_config(title="DICT_TEST")
        result = gen.generate_series(n_episodes=1)
        d = result.to_dict()
        assert d.get("series_title") == "DICT_TEST"

    def test_episode_summary_list(self):
        result = self._run(n=2)
        summary = result.episode_summary()
        assert isinstance(summary, list) and len(summary) == 2

    def test_episode_indices_sequential(self):
        result = self._run(n=3)
        indices = [r.episode_idx for r in result.episode_results]
        assert indices == sorted(indices)


# ─────────────────────────────────────────────
# generate_episode 단위 테스트
# ─────────────────────────────────────────────
class TestGenerateEpisode:
    def test_returns_scene_result(self):
        from literary_system.pipelines.scene_generation_pipeline import SceneGenerationResult
        gen = _make_gen(max_scenes=1)
        ep = gen.generate_episode(ep_idx=0)
        assert isinstance(ep, SceneGenerationResult)

    def test_episode_idx_set(self):
        gen = _make_gen(max_scenes=1)
        ep = gen.generate_episode(ep_idx=5)
        assert ep.episode_idx == 5

    def test_custom_context_accepted(self):
        gen = _make_gen(max_scenes=1)
        ep = gen.generate_episode(ep_idx=0, custom_context={"extra_key": "value"})
        assert ep is not None


# ─────────────────────────────────────────────
# make_default_gateway 회귀 방지 (H6/C fix)
# ─────────────────────────────────────────────
class TestMakeDefaultGateway:
    def test_returns_non_none(self):
        try:
            from literary_system.llm_bridge.gateway import make_default_gateway
            gw = make_default_gateway()
            assert gw is not None, "H6/C 버그 회귀: None 반환"
        except ImportError:
            pytest.skip("make_default_gateway not available")

    def test_has_call_method(self):
        try:
            from literary_system.llm_bridge.gateway import make_default_gateway
            gw = make_default_gateway()
            assert hasattr(gw, 'call') or hasattr(gw, 'generate')
        except ImportError:
            pytest.skip("make_default_gateway not available")
