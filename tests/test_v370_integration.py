"""test_v370_integration.py — V370 prose/ 레이어 E2E 통합 테스트."""
import pytest
from literary_system.prose.contract import ProseRenderContract
from literary_system.prose.anti_llm_filter import KoreanAntiLLMFilter
from literary_system.prose.emotion_behavior import EmotionToBehaviorRenderer, EmotionalDelta
from literary_system.prose.sensory_anchor import SensoryAnchorInjector, SettingSeed
from literary_system.prose.rhythm_rewriter import KoreanRhythmRewriter
from literary_system.prose.surface_scorer import ReaderSurfaceScorer, SurfaceScore
from literary_system.prose.style_dna import StyleDNA
from literary_system.prose.momentum_tracker import EmotionalMomentumTrackerV2
from literary_system.prose.render_orchestrator import (
    ClosedLoopRenderOrchestratorV2, RenderInput, FinalRenderedProseIR
)


CLICHE_TEXT = "복잡한 감정이 밀려왔다. 가슴이 먹먹했다. 눈물이 핑 돌았다."
CLEAN_TEXT  = "그가 창문을 열었다. 바람이 들어왔다. 그녀가 돌아봤다."


# ── 파이프라인 통합 시나리오 ─────────────────────────────────────────
class TestFullPipelineLiterary:
    """literary 장르 전체 파이프라인."""

    def test_clro_produces_prose(self):
        clro = ClosedLoopRenderOrchestratorV2(contract=ProseRenderContract.relaxed())
        r    = clro.render(RenderInput(scene_id="s1", base_text=CLEAN_TEXT, genre_id="literary"))
        assert len(r.prose) > 0

    def test_clro_scene_id_correct(self):
        clro = ClosedLoopRenderOrchestratorV2(contract=ProseRenderContract.relaxed())
        r    = clro.render(RenderInput(scene_id="test_scene", base_text=CLEAN_TEXT))
        assert r.scene_id == "test_scene"

    def test_cliche_filtered_in_prose(self):
        clro = ClosedLoopRenderOrchestratorV2(contract=ProseRenderContract.relaxed())
        r    = clro.render(RenderInput(scene_id="s1", base_text=CLICHE_TEXT))
        assert "복잡한 감정이 밀려왔다" not in r.prose

    def test_score_avg_positive(self):
        clro = ClosedLoopRenderOrchestratorV2(contract=ProseRenderContract.relaxed())
        r    = clro.render(RenderInput(scene_id="s1", base_text=CLEAN_TEXT))
        assert r.score.avg > 0.0

    def test_relaxed_passes(self):
        clro = ClosedLoopRenderOrchestratorV2(contract=ProseRenderContract.relaxed())
        r    = clro.render(RenderInput(scene_id="s1", base_text=CLEAN_TEXT))
        assert r.passed is True


class TestAllFiveGenres:
    """5개 장르 전부 렌더링 성공 확인."""

    @pytest.mark.parametrize("genre", ["literary", "noir", "fantasy", "romance", "historical"])
    def test_genre_renders(self, genre):
        clro = ClosedLoopRenderOrchestratorV2(contract=ProseRenderContract.relaxed())
        r    = clro.render(RenderInput(scene_id="s1", base_text=CLEAN_TEXT, genre_id=genre))
        assert r.genre_id == genre
        assert len(r.prose) > 0

    @pytest.mark.parametrize("genre", ["literary", "noir", "fantasy", "romance", "historical"])
    def test_genre_score_positive(self, genre):
        clro = ClosedLoopRenderOrchestratorV2(contract=ProseRenderContract.relaxed())
        r    = clro.render(RenderInput(scene_id="s1", base_text=CLEAN_TEXT, genre_id=genre))
        assert r.score.avg > 0.0


class TestMomentumTrackerIntegration:
    """EmotionalMomentumTrackerV2 + EmotionToBehaviorRenderer 연동."""

    def test_momentum_feeds_renderer(self):
        tracker  = EmotionalMomentumTrackerV2()
        renderer = EmotionToBehaviorRenderer()
        tracker.register_cluster_weight("hero", 0.9)
        renderer.register_cluster("hero", 0.9)
        tracker.update("s1", EmotionalDelta(tension=0.8), "hero")
        state = tracker.get_weighted_state("hero")
        b = renderer.render(state, "hero")
        assert len(b.text) > 0

    def test_arc_across_scenes(self):
        tracker = EmotionalMomentumTrackerV2()
        for i in range(5):
            tracker.update(f"s{i}", EmotionalDelta(tension=i/4), "hero")
        arc = tracker.momentum_arc("hero", n_scenes=5)
        assert len(arc) == 5

    def test_stats_after_multiple_updates(self):
        tracker = EmotionalMomentumTrackerV2()
        for i in range(3):
            tracker.update(f"s{i}", EmotionalDelta(tension=0.5), "hero")
        s = tracker.stats("hero")
        assert s["count"] == 3


class TestSensoryFilterChain:
    """SensoryAnchorInjector → KoreanAntiLLMFilter 체인."""

    def test_chain_produces_clean_text(self):
        inj    = SensoryAnchorInjector()
        filt   = KoreanAntiLLMFilter("literary")
        seed   = SettingSeed(visual="창문으로 빛이 들었다.")
        anch   = inj.inject("s1", CLICHE_TEXT, seed)
        result = filt.filter(anch.injected_text)
        assert "복잡한 감정이 밀려왔다" not in result.filtered

    def test_density_after_injection(self):
        inj  = SensoryAnchorInjector()
        anch = inj.inject("s1", CLEAN_TEXT)
        assert anch.density > 0.0


class TestStyleDNAWithAntiLLM:
    """StyleDNA v2 + KoreanAntiLLMFilter 연동."""

    def test_literary_strict_filter(self):
        dna    = StyleDNA()
        p      = dna.get("literary")
        assert p.anti_llm_strictness == "strict"
        filt   = KoreanAntiLLMFilter("literary")
        result = filt.filter(CLICHE_TEXT)
        assert result.n_cliches >= 1

    def test_sensory_priority_list_valid(self):
        dna = StyleDNA()
        for genre in dna.available_genres():
            pri = dna.sensory_priority(genre)
            assert set(pri) == {"visual", "audio", "tactile"}


class TestScorerIntegration:
    """ReaderSurfaceScorer 통합."""

    def test_all_signals_integrated(self):
        scorer = ReaderSurfaceScorer(9.0)
        filt   = KoreanAntiLLMFilter()
        inj    = SensoryAnchorInjector()
        rw     = KoreanRhythmRewriter("slow")

        fr     = filt.filter(CLEAN_TEXT)
        anch   = inj.inject("s1", CLEAN_TEXT)
        sents  = rw._split(fr.filtered)
        rr     = rw.rewrite(sents)

        sc = scorer.score(
            anti_llm_score=fr.score,
            sensory_density=anch.density,
            rhythm_score=rr.rhythm_score,
            pipeline_passed=True,
        )
        assert sc.avg > 0.0
        assert isinstance(sc, SurfaceScore)
