"""
krippendorff_alpha.py — Krippendorff α 평가자 간 신뢰도 계산기 (V641, ADR-101)

SP-C.1 MetaLearner 사이클 검증을 위한 평가자 간 신뢰도(inter-rater reliability) 측정.
Constitution v2.0 요구사항: α ≥ 0.70 달성 시 MetaLearner 가중치 확정.

알고리즘: Krippendorff (2011) 표준 coincidence matrix 방식
  1. Coincidence matrix c_vw = Σ_u 2/(m_u-1) for each rater-pair (k,l) in unit u
  2. D_o = Σ_{v,w} c_vw * d(v,w) / (2n)
  3. n_v = marginal count, D_e = Σ_{v≠w} n_v * n_w * d(v,w) / (n*(n-1))
  4. α = 1 - D_o/D_e

임계값: α ≥ 0.80 우수, α ≥ 0.70 허용 가능 (Krippendorff 2004)
LLM-0 준수: 외부 API 없음, 순수 Python 표준 라이브러리
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Dict, List, Optional

# ─── 척도 상수 ─────────────────────────────────────────────────────────────────
METRIC_INTERVAL = "interval"
METRIC_NOMINAL  = "nominal"
METRIC_ORDINAL  = "ordinal"

SUPPORTED_METRICS = (METRIC_INTERVAL, METRIC_NOMINAL, METRIC_ORDINAL)

# Constitution v2.0 §A1 임계값
ALPHA_MIN_THRESHOLD:  float = 0.70
ALPHA_GOOD_THRESHOLD: float = 0.80


# ─── 불일치 함수 ───────────────────────────────────────────────────────────────
def _delta_interval(v1: float, v2: float, **_) -> float:
    return (v1 - v2) ** 2


def _delta_nominal(v1: float, v2: float, **_) -> float:
    return 0.0 if math.isclose(v1, v2, abs_tol=1e-9) else 1.0


def _delta_ordinal(
    v1: float, v2: float,
    ordered_values: Optional[List[float]] = None,
    marginal: Optional[Dict[float, float]] = None,
    **_,
) -> float:
    """
    순위 척도 불일치 (Krippendorff 2004, p. 231).
    g-CDF 기반: d(v_k, v_l) = (Σ_{g=k}^{l} n_g - (n_k + n_l)/2)²
    fallback → interval if ordered_values/marginal 없음.
    """
    if ordered_values is None or marginal is None:
        return _delta_interval(v1, v2)
    try:
        idx1 = ordered_values.index(v1)
        idx2 = ordered_values.index(v2)
    except ValueError:
        return _delta_interval(v1, v2)
    if idx1 == idx2:
        return 0.0
    lo, hi = (idx1, idx2) if idx1 < idx2 else (idx2, idx1)
    cum = sum(marginal.get(ordered_values[g], 0.0) for g in range(lo, hi + 1))
    n_lo = marginal.get(ordered_values[lo], 0.0)
    n_hi = marginal.get(ordered_values[hi], 0.0)
    return (cum - (n_lo + n_hi) / 2.0) ** 2


# ─── 결과 데이터 클래스 ─────────────────────────────────────────────────────────
@dataclass
class AlphaResult:
    alpha: float
    d_observed: float
    d_expected: float
    n_units: int
    n_raters_avg: float
    metric: str

    @property
    def passed(self) -> bool:
        return self.alpha >= ALPHA_MIN_THRESHOLD

    @property
    def quality(self) -> str:
        if self.alpha >= ALPHA_GOOD_THRESHOLD:
            return "우수"
        if self.alpha >= ALPHA_MIN_THRESHOLD:
            return "허용"
        return "부족"

    @property
    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return (
            f"Krippendorff α={self.alpha:.4f} [{status}] "
            f"품질={self.quality} | "
            f"D_o={self.d_observed:.6f} D_e={self.d_expected:.6f} | "
            f"units={self.n_units} metric={self.metric}"
        )


# ─── KrippendorffAlpha ─────────────────────────────────────────────────────────
class KrippendorffAlpha:
    """
    Krippendorff α 평가자 간 신뢰도 계산기 (V641, LLM-0 준수).

    표준 coincidence matrix 방식 (Krippendorff 2011).

    rater_data = {
        "rater_A": {"unit_1": 0.8, "unit_2": 0.6, ...},
        "rater_B": {"unit_1": 0.7, "unit_2": None, ...},  # None = 미평가
    }
    result = KrippendorffAlpha("interval").compute(rater_data)
    """

    def __init__(self, metric: str = METRIC_INTERVAL) -> None:
        if metric not in SUPPORTED_METRICS:
            raise ValueError(f"metric must be one of {SUPPORTED_METRICS}")
        self._metric = metric

    @property
    def metric(self) -> str:
        return self._metric

    def compute(
        self,
        rater_data: Dict[str, Dict[str, Optional[float]]],
    ) -> AlphaResult:
        """Krippendorff α 계산."""
        # 1. 유닛별 유효 평가 수집 (2인 이상만)
        unit_ids = sorted(
            {uid for ratings in rater_data.values() for uid in ratings}
        )
        units: Dict[str, List[float]] = {}
        for uid in unit_ids:
            vals = [
                float(rater_data[rid][uid])
                for rid in rater_data
                if uid in rater_data[rid] and rater_data[rid][uid] is not None
            ]
            if len(vals) >= 2:
                units[uid] = vals

        if not units:
            return AlphaResult(
                alpha=0.0, d_observed=0.0, d_expected=0.0,
                n_units=0, n_raters_avg=0.0, metric=self._metric
            )

        # 2. Coincidence matrix 구성
        coincidence: DefaultDict[tuple, float] = defaultdict(float)
        for vals in units.values():
            m = len(vals)
            weight = 2.0 / (m - 1)
            for i in range(m):
                for j in range(m):
                    if i != j:
                        coincidence[(vals[i], vals[j])] += weight / 2.0

        # 3. n_total = Σ coincidence 행렬 상삼각 합계
        n_total = sum(coincidence[(v1, v2)] for v1, v2 in coincidence if v1 <= v2)
        if n_total < 1e-12:
            return AlphaResult(
                alpha=1.0, d_observed=0.0, d_expected=0.0,
                n_units=len(units), n_raters_avg=0.0, metric=self._metric
            )

        # 4. Marginal counts n_v
        marginal: Dict[float, float] = defaultdict(float)
        for (v1, v2), c in coincidence.items():
            marginal[v1] += c

        ordered_values = sorted(marginal.keys())

        # 5. D_o 계산
        d_o = 0.0
        for (v1, v2), c in coincidence.items():
            if not math.isclose(v1, v2, abs_tol=1e-9):
                d_o += c * self._delta(v1, v2, ordered_values, marginal)
        d_o /= (2.0 * n_total)

        # 6. D_e 계산
        d_e = 0.0
        for v1 in ordered_values:
            for v2 in ordered_values:
                if not math.isclose(v1, v2, abs_tol=1e-9):
                    d_e += marginal[v1] * marginal[v2] * self._delta(
                        v1, v2, ordered_values, marginal
                    )
        # C-1 수정: Krippendorff n = Σ marginal[v] (full matrix sum = 2*n_total for symmetric)
        # 기존 n_total (upper triangle only) 대신 실제 Krippendorff n 사용
        n_full = sum(marginal.values())
        d_e /= (n_full * (n_full - 1))

        # 7. α 계산
        if d_e < 1e-12:
            alpha = 1.0 if d_o < 1e-12 else 0.0
        else:
            alpha = 1.0 - (d_o / d_e)

        n_raters_avg = (
            sum(len(v) for v in units.values()) / len(units)
        )

        return AlphaResult(
            alpha=alpha,
            d_observed=d_o,
            d_expected=d_e,
            n_units=len(units),
            n_raters_avg=n_raters_avg,
            metric=self._metric,
        )

    def _delta(
        self,
        v1: float, v2: float,
        ordered_values: List[float],
        marginal: Dict[float, float],
    ) -> float:
        if self._metric == METRIC_INTERVAL:
            return _delta_interval(v1, v2)
        if self._metric == METRIC_NOMINAL:
            return _delta_nominal(v1, v2)
        return _delta_ordinal(v1, v2, ordered_values=ordered_values, marginal=marginal)
