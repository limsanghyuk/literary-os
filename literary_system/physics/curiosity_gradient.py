"""
V383 — AudienceCuriosityGradientEngine
독자 호기심 기울기 추적. gradient <= 0 시 CuriosityCollapseError.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class CuriosityCollapseError:
    episode_idx: int
    gradient:    float
    message:     str


@dataclass
class CuriosityResult:
    gradient:       float
    reveal_ratio:   float
    arc_tension:    float
    collapse_error: Optional[CuriosityCollapseError] = None


class AudienceCuriosityGradientEngine:
    """
    gradient = reader_uncertainty × (1 - reveal_ratio) × arc_tension
    
    - reader_uncertainty: ReaderSimulator.reader_uncertainty
    - reveal_ratio: 에피소드 내 공개된 reveal / max_reveals
    - arc_tension: SeriesArcPlanner.tension_at(episode_idx) (S자형 0~1)
    """

    def calculate(
        self,
        reader_uncertainty: float,
        reveal_ratio:       float,
        arc_tension:        float,
        episode_idx:        int = 0,
    ) -> CuriosityResult:
        # 입력 범위 보정
        u  = max(0.0, min(1.0, reader_uncertainty))
        rv = max(0.0, min(1.0, reveal_ratio))
        at = max(0.0, min(1.0, arc_tension))

        gradient = u * (1.0 - rv) * at

        collapse = None
        if gradient <= 0.0:
            collapse = CuriosityCollapseError(
                episode_idx = episode_idx,
                gradient    = gradient,
                message = (
                    f"CuriosityGradient collapsed to {gradient:.4f} "
                    f"at episode {episode_idx}. "
                    f"(uncertainty={u:.3f}, reveal_ratio={rv:.3f}, tension={at:.3f})"
                ),
            )

        return CuriosityResult(
            gradient      = gradient,
            reveal_ratio  = rv,
            arc_tension   = at,
            collapse_error = collapse,
        )
