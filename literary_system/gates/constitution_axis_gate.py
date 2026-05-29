"""Gate G57 — Constitution 5축 상관 게이트: mean_correlation ≥ 0.80 (V606, ADR-066)."""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

CORRELATION_THRESHOLD: float = 0.80
GATE_ID = "G57"
GATE_NAME = "Constitution 5-Axis Correlation Gate"

CONSTITUTION_AXES: List[str] = [
    "safety",
    "coherence",
    "creativity",
    "quality",
    "consistency",
]


@dataclass
class ConstitutionAxisGateResult:
    """G57 게이트 결과."""

    passed: bool
    mean_correlation: float
    axis_correlations: Dict[str, float]
    threshold: float
    n_pairs: int
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _pearson(x: List[float], y: List[float]) -> float:
    """피어슨 상관계수 계산 (순수 파이썬)."""
    n = len(x)
    if n < 2:
        return 0.0

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    denom_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
    denom_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))

    if denom_x == 0.0 or denom_y == 0.0:
        return 0.0

    return numerator / (denom_x * denom_y)


def run_constitution_axis_gate(
    scores: Dict[str, List[float]],
    threshold: float = CORRELATION_THRESHOLD,
) -> ConstitutionAxisGateResult:
    """G57 게이트 실행.

    Args:
        scores: {축이름: 씬별 점수 목록} — Constitution 5축 모두 포함 필수.
            예: {"safety": [0.9, 0.8, ...], "coherence": [...], ...}
        threshold: 평균 상관계수 임계값 (기본 0.80).

    Returns:
        ConstitutionAxisGateResult with passed, mean_correlation, axis_correlations.

    Notes:
        모든 축 쌍 (C(5,2)=10쌍) 의 피어슨 상관계수 평균 ≥ threshold 일 때 PASS.
        상관이 높다 = 보상 모델이 5축을 균형 있게 평가 중 (단일 축 편향 없음).
    """
    missing = [ax for ax in CONSTITUTION_AXES if ax not in scores]
    if missing:
        return ConstitutionAxisGateResult(
            passed=False,
            mean_correlation=0.0,
            axis_correlations={},
            threshold=threshold,
            n_pairs=0,
            reason=f"누락된 Constitution 축: {missing}",
        )

    axis_data = {ax: scores[ax] for ax in CONSTITUTION_AXES}

    # 길이 일치 검증
    lengths = {ax: len(v) for ax, v in axis_data.items()}
    if len(set(lengths.values())) != 1:
        return ConstitutionAxisGateResult(
            passed=False,
            mean_correlation=0.0,
            axis_correlations={},
            threshold=threshold,
            n_pairs=0,
            reason=f"축 데이터 길이 불일치: {lengths}",
        )

    n_axes = len(CONSTITUTION_AXES)
    axis_correlations: Dict[str, float] = {}
    correlations: List[float] = []

    for i in range(n_axes):
        for j in range(i + 1, n_axes):
            ax_i = CONSTITUTION_AXES[i]
            ax_j = CONSTITUTION_AXES[j]
            pair_key = f"{ax_i}↔{ax_j}"
            corr = _pearson(axis_data[ax_i], axis_data[ax_j])
            axis_correlations[pair_key] = round(corr, 4)
            correlations.append(corr)

    mean_correlation = sum(correlations) / len(correlations) if correlations else 0.0
    passed = mean_correlation >= threshold

    weak_pairs = [k for k, v in axis_correlations.items() if v < threshold]
    reason = "PASS" if passed else (
        f"mean_correlation={mean_correlation:.4f} < threshold={threshold}. "
        f"약한 상관 쌍: {weak_pairs}"
    )

    return ConstitutionAxisGateResult(
        passed=passed,
        mean_correlation=round(mean_correlation, 4),
        axis_correlations=axis_correlations,
        threshold=threshold,
        n_pairs=len(correlations),
        reason=reason,
    )
