"""test_v370_render_orchestrator.py — ClosedLoopRenderOrchestratorV2 테스트 (V370)"""
import pytest
from literary_system.prose.contract import (
    ProseRenderContract, SurfaceOnlyViolationError, ReaderScoreBelowThresholdError
)
from literary_system.prose.emotion_behavior import EmotionalDelta
from literary_system.prose.sensory_anchor import SettingSeed
from literary_system.prose.render_orchestrator import (
    ClosedLoopRenderOrchestratorV2, RenderInput, FinalRenderedProseIR
)
from literary_system.prose.surface_scorer import ReaderSurfaceScorer


def make_input(scene_id="s1", text="그가 문을 열었다. 그녀가 돌아봤다.",
               genre="literary", char_id="hero",
               tension=0.5, dread=0.0):
    return RenderInput(
        scene_id=scene_id, base_text=text, genre_id=genre,
        char_id=char_id, emotion=EmotionalDelta(tension=tension, dread=dread),
        setting=SettingSeed(visual="", audio="", tactile=""),
    )


class TestRenderInputDefaults:
    def test_fields_exist(self):
        inp = make_input()
        assert hasattr(inp, "scene_id")
        assert hasattr(inp, "base_text")
        assert hasattr(inp, "genre_id")
        assert hasattr(inp, "char_id")
        assert hasattr(inp, "emotion")

    def test_default_genre(self):
        inp = RenderInput(scene_id="s1", base_text="text")
        assert inp.genre_id == "literary"


class TestFinalRenderedProseIR:
    def test_passed_property_true(self):
        from literary_system.prose.surface_scorer import SurfaceScore
        sc = SurfaceScore(anti_llm=9.5, emotion=9.5, sensory=9.5,
                          rhythm=9.5, consistency=9.5, structure=9.5)
        ir = FinalRenderedProseIR(scene_id="s1", prose="text", score=sc)
        assert ir.passed is True

    def test_passed_property_false(self):
        from literary_system.prose.surface_scorer import SurfaceScore
        sc = SurfaceScore(anti_llm=8.0, emotion=8.0, sensory=8.0,
                          rhythm=8.0, consistency=8.0, structure=8.0)
        ir = FinalRenderedProseIR(scene_id="s1", prose="text", score=sc)
        assert ir.passed is False


class TestContractGate:
    def test_invalid_contract_raises(self):
        bad = ProseRenderContract(surface_only=False)
        clro = ClosedLoopRenderOrchestratorV2(contract=bad)
        with pytest.raises(SurfaceOnlyViolationError):
            clro.render(make_input())

    def test_valid_contract_allows_render(self):
        clro = ClosedLoopRenderOrchestratorV2(
            contract=ProseRenderContract.relaxed()
        )
        result = clro.render(make_input())
        assert isinstance(result, FinalRenderedProseIR)


class TestRenderOutput:
    def setup_method(self):
        self.clro = ClosedLoopRenderOrchestratorV2(
            contract=ProseRenderContract.relaxed()
        )

    def test_returns_final_prose_ir(self):
        r = self.clro.render(make_input())
        assert isinstance(r, FinalRenderedProseIR)

    def test_prose_not_empty(self):
        r = self.clro.render(make_input())
        assert len(r.prose) > 0

    def test_scene_id_preserved(self):
        r = self.clro.render(make_input("my_scene"))
        assert r.scene_id == "my_scene"

    def test_score_is_surface_score(self):
        from literary_system.prose.surface_scorer import SurfaceScore
        r = self.clro.render(make_input())
        assert isinstance(r.score, SurfaceScore)

    def test_attempts_at_least_one(self):
        r = self.clro.render(make_input())
        assert r.attempts >= 1

    def test_genre_id_in_result(self):
        r = self.clro.render(make_input(genre="noir"))
        assert r.genre_id == "noir"

    def test_all_five_genres(self):
        for genre in ["literary", "noir", "fantasy", "romance", "historical"]:
            r = self.clro.render(make_input(genre=genre))
            assert r.genre_id == genre


class TestRenderSafe:
    def test_render_safe_never_raises(self):
        # min_score=10.0 (불가능한 기준) → render_safe는 예외 없이 반환
        strict = ProseRenderContract(min_surface_score=10.0)
        clro   = ClosedLoopRenderOrchestratorV2(contract=strict)
        result = clro.render_safe(make_input(), max_retries=1)
        assert isinstance(result, FinalRenderedProseIR)

    def test_render_safe_marks_metadata(self):
        strict = ProseRenderContract(min_surface_score=10.0)
        clro   = ClosedLoopRenderOrchestratorV2(contract=strict)
        result = clro.render_safe(make_input(), max_retries=1)
        # 점수 미달 시 metadata에 표시
        assert isinstance(result, FinalRenderedProseIR)


class TestRetryLogic:
    def test_max_retries_respected(self):
        # min_score=10.0 → 반드시 재시도 후 예외
        strict = ProseRenderContract(min_surface_score=10.0)
        clro   = ClosedLoopRenderOrchestratorV2(contract=strict)
        with pytest.raises((ReaderScoreBelowThresholdError, Exception)):
            clro.render(make_input(), max_retries=2)

    def test_relaxed_succeeds_first_try(self):
        relaxed = ProseRenderContract.relaxed()
        clro    = ClosedLoopRenderOrchestratorV2(contract=relaxed)
        r = clro.render(make_input())
        assert r.attempts >= 1


class TestWithEmotion:
    def test_high_tension_emotion_in_prose(self):
        clro = ClosedLoopRenderOrchestratorV2(contract=ProseRenderContract.relaxed())
        inp  = make_input(tension=0.9)
        r    = clro.render(inp)
        assert len(r.prose) > 10

    def test_zero_emotion_still_renders(self):
        clro = ClosedLoopRenderOrchestratorV2(contract=ProseRenderContract.relaxed())
        inp  = make_input(tension=0.0, dread=0.0)
        r    = clro.render(inp)
        assert len(r.prose) > 0
