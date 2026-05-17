"""V370: ClosedLoopRenderOrchestratorV2 — 7단계 산문 렌더링 루프."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from literary_system.prose.contract import (
    ProseRenderContract, ReaderScoreBelowThresholdError
)
from literary_system.prose.anti_llm_filter import KoreanAntiLLMFilter
from literary_system.prose.emotion_behavior import EmotionToBehaviorRenderer, EmotionalDelta
from literary_system.prose.sensory_anchor import SensoryAnchorInjector, SettingSeed
from literary_system.prose.rhythm_rewriter import KoreanRhythmRewriter
from literary_system.prose.surface_scorer import ReaderSurfaceScorer, SurfaceScore
from literary_system.prose.style_dna import StyleDNA


@dataclass
class RenderInput:
    """CLRO v2 입력 IR."""
    scene_id:    str
    base_text:   str
    genre_id:    str            = "literary"
    char_id:     str            = ""
    emotion:     EmotionalDelta = field(default_factory=EmotionalDelta)
    setting:     SettingSeed    = field(default_factory=SettingSeed)
    metadata:    Dict[str, Any] = field(default_factory=dict)


@dataclass
class FinalRenderedProseIR:
    """CLRO v2 최종 출력 IR."""
    scene_id:    str
    prose:       str
    score:       SurfaceScore
    attempts:    int            = 1
    genre_id:    str            = "literary"
    min_score:   float          = 9.0
    metadata:    Dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.score.passes(self.min_score)


class ClosedLoopRenderOrchestratorV2:
    """
    V370 산문 렌더링 7단계 루프.
    ProseRenderContract 없이 진입 불가.
    ReaderSurfaceScorer avg < min_surface_score 시 최대 max_retries 재시도.
    """

    def __init__(
        self,
        contract:    Optional[ProseRenderContract]    = None,
        anti_filter: Optional[KoreanAntiLLMFilter]    = None,
        emotion_rend:Optional[EmotionToBehaviorRenderer] = None,
        sensory:     Optional[SensoryAnchorInjector]  = None,
        rhythm:      Optional[KoreanRhythmRewriter]   = None,
        scorer:      Optional[ReaderSurfaceScorer]    = None,
        style_dna:   Optional[StyleDNA]               = None,
    ) -> None:
        self._contract    = contract    or ProseRenderContract.default()
        self._anti        = anti_filter
        self._emotion     = emotion_rend or EmotionToBehaviorRenderer()
        self._sensory     = sensory     or SensoryAnchorInjector()
        self._rhythm      = rhythm      or KoreanRhythmRewriter()
        self._scorer      = scorer      or ReaderSurfaceScorer(
                                min_score=self._contract.min_surface_score)
        self._style_dna   = style_dna   or StyleDNA()

    # ── PUBLIC ─────────────────────────────────────────────────────────
    def render(self, inp: RenderInput,
               max_retries: int = 3) -> FinalRenderedProseIR:
        """
        7단계 렌더링 루프 실행.
        contract.assert_valid() 없이 진입 불가.
        """
        # [1] CONTRACT
        self._contract.assert_valid()

        # [2] SCOPE — StyleDNA에서 genre 정보 로드
        dna = self._style_dna.get(inp.genre_id)
        self._rhythm.set_rhythm(dna.scene_rhythm)

        # anti_llm_filter를 장르에 맞게 초기화
        anti = self._anti or KoreanAntiLLMFilter(genre_id=inp.genre_id)

        for attempt in range(1, max_retries + 1):
            # [3] ANCHOR
            anchored = SensoryAnchorInjector(genre_id=inp.genre_id).inject(
                inp.scene_id, inp.base_text, inp.setting
            )

            # [4] RENDER + AntiLLM 1차 필터
            filter_result = anti.filter(anchored.injected_text or inp.base_text)
            draft = filter_result.filtered

            # [5] EMOTION — 행동 표현 삽입
            behavior = self._emotion.render(inp.emotion, inp.char_id)
            if behavior.text and behavior.text not in draft:
                draft = draft.rstrip("。.") + " " + behavior.text

            # [6] RHYTHM
            sentences   = KoreanRhythmRewriter._split_static(draft)
            rhythm_res  = self._rhythm.rewrite(sentences)
            rhythmed    = rhythm_res.joined

            # [7] VERIFY
            score = self._scorer.score(
                anti_llm_score    = filter_result.score,
                emotion_intensity = behavior.intensity,
                sensory_density   = anchored.density,
                rhythm_score      = rhythm_res.rhythm_score,
                consistency_score = 9.0,   # ContractBridge 연동 시 실측값으로 대체
                pipeline_passed   = True,
            )

            if score.passes(self._contract.min_surface_score):
                return FinalRenderedProseIR(
                    scene_id=inp.scene_id,
                    prose=rhythmed,
                    score=score,
                    attempts=attempt,
                    genre_id=inp.genre_id,
                    min_score=self._contract.min_surface_score,
                )

        # max_retries 초과 — 최후 점수로 예외
        raise ReaderScoreBelowThresholdError(score.avg, self._contract.min_surface_score)

    def render_safe(self, inp: RenderInput,
                    max_retries: int = 3) -> FinalRenderedProseIR:
        """예외 없이 최선의 결과를 반환하는 안전 버전."""
        try:
            return self.render(inp, max_retries)
        except ReaderScoreBelowThresholdError as e:
            # 점수 미달이어도 결과 반환
            dna  = self._style_dna.get(inp.genre_id)
            anti = self._anti or KoreanAntiLLMFilter(genre_id=inp.genre_id)
            fr   = anti.filter(inp.base_text)
            sc   = self._scorer.score(
                anti_llm_score=fr.score, pipeline_passed=False
            )
            return FinalRenderedProseIR(
                scene_id=inp.scene_id, prose=fr.filtered,
                score=sc, attempts=max_retries, genre_id=inp.genre_id,
                metadata={"score_below_threshold": True, "error": str(e)},
            )
