"""
WP-1 (V747) — FormulaEntry 레지스트리.

FormulaEntry TypedDict + REGISTRY dict.
lifecycle: candidate → validated → recalibrate → deprecated
LLM 호출 0회 — 완전 로컬.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Literal

# 씬 특징 행 타입 별칭 (scene_feature 테이블 한 행)
SceneRow = Dict[str, Any]

# ──────────────────────────────────────────────────────────────
# TypedDict (Python 3.8+ 호환)
# ──────────────────────────────────────────────────────────────
try:
    from typing import TypedDict

    class FormulaEntry(TypedDict):
        formula_id:  str
        domain:      str
        score_fn:    Callable[[SceneRow], float]
        lifecycle:   Literal["candidate", "validated", "recalibrate", "deprecated"]

except ImportError:  # pragma: no cover
    # 구버전 폴백: 일반 dict
    FormulaEntry = dict  # type: ignore[misc,assignment]


# ──────────────────────────────────────────────────────────────
# 내장 score_fn 구현
# ──────────────────────────────────────────────────────────────

_PHYSICS_KEYS = [
    "conflict_intensity",
    "scene_energy_ratio",
    "motif_residue_score",
    "curiosity_gradient",
    "reader_surface_score",
    "arc_tension_score",
]


def _fitness_score(row: SceneRow) -> float:
    """
    NarrativeFitnessScore 래핑.
    literary_system.physics 미사용 환경(테스트 등)에서는 단순 평균 폴백.
    """
    try:
        from literary_system.physics.fitness_score import (
            NarrativeFitnessComponents,
            NarrativeFitnessScore,
        )
        from literary_system.physics.coefficient_store import PhysicsCoefficientStore

        comp = NarrativeFitnessComponents(
            conflict_intensity   = float(row.get("conflict_intensity",   0.5)),
            scene_energy_ratio   = float(row.get("scene_energy_ratio",   0.5)),
            motif_residue_score  = float(row.get("motif_residue_score",  0.5)),
            curiosity_gradient   = float(row.get("curiosity_gradient",   0.5)),
            reader_surface_score = float(row.get("reader_surface_score", 0.5)),
            arc_tension_score    = float(row.get("arc_tension_score",    0.5)),
        )
        return NarrativeFitnessScore(PhysicsCoefficientStore()).calculate(comp)
    except ImportError:
        # 로컬 폴백
        vals = [float(row.get(k, 0.5)) for k in _PHYSICS_KEYS]
        return sum(vals) / len(vals) * 10.0


# ──────────────────────────────────────────────────────────────
# REGISTRY (1차 등록: physics domain)
# ──────────────────────────────────────────────────────────────

REGISTRY: Dict[str, FormulaEntry] = {
    "F-06_fitness": FormulaEntry(  # type: ignore[call-arg]
        formula_id = "F-06_fitness",
        domain     = "physics",
        score_fn   = _fitness_score,
        lifecycle  = "candidate",
    ),
}
