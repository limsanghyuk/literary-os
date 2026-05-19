"""V370: ReaderSurfaceScorer — 6개 축 산문 표면 품질 실측 점수화."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class SurfaceScore:
    anti_llm:    float = 0.0   # AI 클리셰 없음 (KoreanAntiLLMFilter)
    emotion:     float = 0.0   # 감정→행동 변환 구체성
    sensory:     float = 0.0   # 감각 앵커 밀도
    rhythm:      float = 0.0   # 문장 리듬 균일성
    consistency: float = 0.0   # NKG 구조 일관성
    structure:   float = 0.0   # DKGPipeline 통과 여부
    metadata:    Dict[str, Any] = field(default_factory=dict)

    @property
    def avg(self) -> float:
        vals = [self.anti_llm, self.emotion, self.sensory,
                self.rhythm, self.consistency, self.structure]
        return round(sum(vals) / len(vals), 3)

    @property
    def min_score(self) -> float:
        return min(self.anti_llm, self.emotion, self.sensory,
                   self.rhythm, self.consistency, self.structure)

    def passes(self, threshold: float = 9.0) -> bool:
        return self.avg >= threshold

    def report(self) -> Dict[str, float]:
        return {
            "anti_llm":    self.anti_llm,
            "emotion":     self.emotion,
            "sensory":     self.sensory,
            "rhythm":      self.rhythm,
            "consistency": self.consistency,
            "structure":   self.structure,
            "avg":         self.avg,
        }


class ReaderSurfaceScorer:
    """
    산문 표면 품질을 6개 축으로 실측 점수화.
    CLRO v2의 7단계 [VERIFY] 게이트 담당.
    """

    def __init__(self, min_score: float = 9.0) -> None:
        self.min_score = min_score

    def score(
        self,
        *,
        anti_llm_score:    Optional[float] = None,  # FilterResult.score
        emotion_intensity: Optional[float] = None,  # BehaviorText.intensity
        sensory_density:   Optional[float] = None,  # AnchoredSceneIR.density
        rhythm_score:      Optional[float] = None,  # RhythmResult.rhythm_score
        consistency_score: Optional[float] = None,  # CrossValidationResult 기반
        pipeline_passed:   Optional[bool]  = None,  # DKGPipeline 통과 여부
    ) -> SurfaceScore:
        """
        각 모듈에서 받은 신호를 통합하여 SurfaceScore를 산출한다.
        None인 항목은 기본값(5.0)으로 처리한다.
        """
        anti  = self._clamp(anti_llm_score)     if anti_llm_score is not None    else 5.0
        emo   = self._emotion_to_score(emotion_intensity)
        sens  = self._density_to_score(sensory_density)
        rhy   = self._clamp(rhythm_score)       if rhythm_score is not None       else 5.0
        cons  = self._clamp(consistency_score)  if consistency_score is not None  else 5.0
        struct= 10.0 if pipeline_passed else (5.0 if pipeline_passed is None else 0.0)

        return SurfaceScore(
            anti_llm=anti, emotion=emo, sensory=sens,
            rhythm=rhy, consistency=cons, structure=struct,
        )

    @staticmethod
    def _clamp(v: float, lo: float = 0.0, hi: float = 10.0) -> float:
        return round(max(lo, min(hi, v)), 3)

    @staticmethod
    def _emotion_to_score(intensity: Optional[float]) -> float:
        if intensity is None:
            return 5.0
        # intensity 0.0~1.0 → 점수 5.0~10.0 (선형 매핑)
        return round(5.0 + intensity * 5.0, 3)

    @staticmethod
    def _density_to_score(density: Optional[float]) -> float:
        if density is None:
            return 5.0
        # density 0.0~1.0 → 점수 (최적 0.2~0.4에서 10점, 양극단 감점)
        if 0.15 <= density <= 0.45:
            return 10.0
        elif density < 0.15:
            return round(5.0 + density / 0.15 * 5.0, 3)
        else:
            return round(max(5.0, 10.0 - (density - 0.45) / 0.55 * 5.0), 3)

    def passes(self, ss: SurfaceScore) -> bool:
        return ss.avg >= self.min_score
