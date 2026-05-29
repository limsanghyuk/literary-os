"""
V484 SceneGenerationPipeline 테스트
SceneGenerationResult.episode_idx / structure 필수, SceneGenerationPipeline.run() API 기준.
"""
import pytest
from unittest.mock import MagicMock
import sys

sys.path.insert(0, '/tmp/v481_work/literary_os_v430_COMPLETE')


def _make_cfg(ep_idx=0):
    from literary_system.episode.episode_structure_calculator import EpisodeStructureConfig
    return EpisodeStructureConfig(total_episodes=16, episode_idx=ep_idx, runtime_min=60)


def _make_structure(ep_idx=0):
    from literary_system.episode.episode_structure_calculator import EpisodeStructureCalculator
    return EpisodeStructureCalculator().calculate(_make_cfg(ep_idx))


def _make_cadences(structure=None):
    from literary_system.prose.korean_cadence_planner import KoreanCadencePlanner
    structure = structure or _make_structure()
    return KoreanCadencePlanner().plan_episode(structure)


def _make_mock_gw(text="씬 텍스트", provider="haiku"):
    gw = MagicMock()
    resp = MagicMock()
    resp.text = text
    resp.provider_id = provider
    gw.call.return_value = resp
    return gw


def _make_pipeline(max_scenes=2, gw=None):
    from literary_system.pipelines.scene_generation_pipeline import SceneGenerationPipeline
    return SceneGenerationPipeline(
        gateway=gw or _make_mock_gw(),
        structure_config=_make_cfg(),
        max_scenes=max_scenes,
    )


# ─────────────────────────────────────────────
# ScenePromptAssembler
# ─────────────────────────────────────────────
class TestScenePromptAssembler:
    def test_assemble_returns_string(self):
        from literary_system.pipelines.scene_generation_pipeline import ScenePromptAssembler
        structure = _make_structure()
        cadences = _make_cadences(structure)
        asm = ScenePromptAssembler()
        result = asm.assemble(structure.scenes[0], cadences[0], {})
        assert isinstance(result, str) and len(result) > 20

    def test_assemble_with_context(self):
        from literary_system.pipelines.scene_generation_pipeline import ScenePromptAssembler
        structure = _make_structure()
        cadences = _make_cadences(structure)
        asm = ScenePromptAssembler()
        result = asm.assemble(structure.scenes[1], cadences[1], {"title": "별빛 아래서"})
        assert len(result) > 50

    def test_assemble_no_raise_empty_context(self):
        from literary_system.pipelines.scene_generation_pipeline import ScenePromptAssembler
        structure = _make_structure()
        cadences = _make_cadences(structure)
        asm = ScenePromptAssembler()
        # 빈 컨텍스트에서도 예외 없어야 함
        result = asm.assemble(structure.scenes[2], cadences[2], {})
        assert isinstance(result, str)

    def test_assemble_all_slots(self):
        from literary_system.pipelines.scene_generation_pipeline import ScenePromptAssembler
        structure = _make_structure()
        cadences = _make_cadences(structure)
        asm = ScenePromptAssembler()
        for slot, cadence in zip(structure.scenes[:5], cadences[:5]):
            assert isinstance(asm.assemble(slot, cadence, {}), str)


# ─────────────────────────────────────────────
# GeneratedScene
# ─────────────────────────────────────────────
class TestGeneratedScene:
    def _make(self, **kw):
        from literary_system.pipelines.scene_generation_pipeline import GeneratedScene
        structure = _make_structure()
        cadences = _make_cadences(structure)
        defaults = dict(
            scene_idx=0, slot=structure.scenes[0], cadence=cadences[0],
            prompt="프롬프트", text="씬 텍스트",
            provider_id="haiku", latency_ms=100.0, error=""
        )
        defaults.update(kw)
        return GeneratedScene(**defaults)

    def test_text_stored(self):
        assert self._make(text="특별한 내용").text == "특별한 내용"

    def test_provider_id(self):
        assert self._make(provider_id="sonnet").provider_id == "sonnet"

    def test_latency(self):
        assert self._make(latency_ms=500.0).latency_ms == 500.0

    def test_no_error_success_true(self):
        s = self._make(text="내용 있음", error="")
        assert s.success is True

    def test_error_success_false(self):
        s = self._make(text="", error="timeout")
        assert s.success is False

    def test_word_count(self):
        s = self._make(text="하나 둘 셋")
        assert s.word_count == 3

    def test_scene_idx(self):
        s = self._make(scene_idx=7)
        assert s.scene_idx == 7

    def test_prompt_stored(self):
        s = self._make(prompt="특별 프롬프트")
        assert s.prompt == "특별 프롬프트"


# ─────────────────────────────────────────────
# SceneGenerationResult
# ─────────────────────────────────────────────
class TestSceneGenerationResult:
    def _run_pipeline(self, max_scenes=3, fail_gw=False):
        gw = _make_mock_gw() if not fail_gw else MagicMock(
            **{"call.side_effect": RuntimeError("fail")}
        )
        pipeline = _make_pipeline(max_scenes=max_scenes, gw=gw)
        return pipeline.run(config=_make_cfg(), episode_context={})

    def test_episode_idx_set(self):
        result = self._run_pipeline(max_scenes=2)
        assert result.episode_idx == 0

    def test_structure_attached(self):
        from literary_system.episode.episode_structure_calculator import EpisodeStructure
        result = self._run_pipeline(max_scenes=2)
        assert isinstance(result.structure, EpisodeStructure)

    def test_scenes_produced(self):
        result = self._run_pipeline(max_scenes=2)
        assert len(result.scenes) > 0

    def test_success_count_with_good_gw(self):
        result = self._run_pipeline(max_scenes=2)
        assert result.success_count == len(result.scenes)

    def test_failure_count_with_bad_gw(self):
        result = self._run_pipeline(max_scenes=2, fail_gw=True)
        assert result.failure_count > 0

    def test_full_text_string(self):
        result = self._run_pipeline(max_scenes=2)
        assert isinstance(result.full_text(), str)

    def test_elapsed_non_negative(self):
        result = self._run_pipeline(max_scenes=2)
        assert result.total_elapsed_s >= 0


# ─────────────────────────────────────────────
# SceneGenerationPipeline
# ─────────────────────────────────────────────
class TestSceneGenerationPipeline:
    def test_run_returns_result(self):
        from literary_system.pipelines.scene_generation_pipeline import SceneGenerationResult
        result = _make_pipeline(max_scenes=2).run(config=_make_cfg(), episode_context={})
        assert isinstance(result, SceneGenerationResult)

    def test_run_produces_scenes(self):
        result = _make_pipeline(max_scenes=2).run(config=_make_cfg(), episode_context={})
        assert len(result.scenes) > 0

    def test_max_scenes_respected(self):
        result = _make_pipeline(max_scenes=1).run(config=_make_cfg(), episode_context={})
        assert len(result.scenes) <= 1

    def test_gateway_call_invoked(self):
        gw = _make_mock_gw()
        _make_pipeline(max_scenes=2, gw=gw).run(config=_make_cfg(), episode_context={})
        assert gw.call.call_count >= 1

    def test_no_gateway_runs(self):
        from literary_system.pipelines.scene_generation_pipeline import SceneGenerationPipeline
        pipeline = SceneGenerationPipeline(gateway=None, structure_config=_make_cfg(), max_scenes=2)
        result = pipeline.run(config=_make_cfg(), episode_context={})
        assert result is not None

    def test_skip_roles_cold_open(self):
        from literary_system.pipelines.scene_generation_pipeline import SceneGenerationPipeline
        pipeline = SceneGenerationPipeline(
            gateway=_make_mock_gw(), structure_config=_make_cfg(),
            max_scenes=6, skip_roles=["cold_open", "preview"]
        )
        result = pipeline.run(config=_make_cfg(), episode_context={})
        for s in result.scenes:
            assert s.slot.role.value not in ("cold_open", "preview")

    def test_gateway_error_captured(self):
        gw = MagicMock()
        gw.call.side_effect = RuntimeError("LLM 다운")
        pipeline = _make_pipeline(max_scenes=2, gw=gw)
        result = pipeline.run(config=_make_cfg(), episode_context={})
        assert result.failure_count >= 1

    def test_provider_id_in_results(self):
        result = _make_pipeline(max_scenes=2).run(config=_make_cfg(), episode_context={})
        for s in result.scenes:
            assert isinstance(s.provider_id, str)

    def test_scene_idx_sequential(self):
        result = _make_pipeline(max_scenes=3).run(config=_make_cfg(), episode_context={})
        idxs = [s.scene_idx for s in result.scenes]
        assert idxs == sorted(idxs)
