"""
TIdealLearner — V518
ADR-022: T_ideal Fourier 계수 적응

T_ideal(t) = base + a1·sin(2πt − 0.50) + a2·sin(6πt)
의 계수 {base, a1, a2} 를 작품/장르별로 SGD 로 학습.

- 매 작품 완료 후 실제 tension 시계열과 비교
- 장르별 독립 계수 관리 (장르 미지정 시 "default" 사용)
- NarrativeTensionCurve.update_fourier_coefficients() 를 통해 반영
"""

from __future__ import annotations

import math
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# ─── 상수 ─────────────────────────────────────────────────────────────────────
T_LR: float = 0.005                    # Fourier 계수 SGD 학습률
GENRE_WINDOW: int = 5                  # 장르별 rolling history 크기
CLIP_GRAD: float = 0.50               # gradient clipping

# 계수 범위 (ADR-022)
BASE_MIN: float = 0.40;  BASE_MAX: float = 0.80
A1_MIN: float = 0.10;    A1_MAX: float = 0.60
A2_MIN: float = 0.05;    A2_MAX: float = 0.40

# 장르별 초기값 (V500 AMW 장르 초기화와 매핑)
GENRE_FOURIER_INIT: Dict[str, Tuple[float, float, float]] = {
    "melodrama": (0.60, 0.45, 0.20),
    "thriller":  (0.65, 0.50, 0.25),
    "romcom":    (0.55, 0.35, 0.15),
    "family":    (0.58, 0.38, 0.18),
    "default":   (0.60, 0.40, 0.20),
}


# ─── 데이터 클래스 ─────────────────────────────────────────────────────────────
@dataclass
class FourierCoeffs:
    base: float = 0.60
    a1: float = 0.40
    a2: float = 0.20

    def t_ideal(self, t: float) -> float:
        return (
            self.base
            + self.a1 * math.sin(2 * math.pi * t - 0.50)
            + self.a2 * math.sin(6 * math.pi * t)
        )

    def as_tuple(self) -> Tuple[float, float, float]:
        return (self.base, self.a1, self.a2)


@dataclass
class FourierUpdate:
    genre: str
    base: float
    a1: float
    a2: float
    grad_base: float
    grad_a1: float
    grad_a2: float
    l_tension_before: float = 0.0

    @property
    def coeffs(self) -> FourierCoeffs:
        return FourierCoeffs(self.base, self.a1, self.a2)


# ─── TIdealLearner ────────────────────────────────────────────────────────────
class TIdealLearner:
    """
    T_ideal Fourier 계수 자동 적응 학습기 (V518, ADR-022).

    update() 를 작품 완료 시 호출. tension_curve.update_fourier_coefficients() 를 통해
    NarrativeTensionCurve 에 즉시 반영된다.
    """

    def __init__(self) -> None:
        self._coeffs: Dict[str, FourierCoeffs] = {}
        self._history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=GENRE_WINDOW))
        self._update_count: int = 0
        self._update_log: List[FourierUpdate] = []

    # ── 공개 API ─────────────────────────────────────────────────────────────
    def update(
        self,
        tension_curve,                    # NarrativeTensionCurve 인스턴스
        actual_tensions: List[float],     # 씬별 실제 tension 시계열
        genre: str = "default",
    ) -> Optional[FourierUpdate]:
        """
        실제 tension 과 T_ideal 의 MSE 기울기로 Fourier 계수를 한 스텝 갱신.
        tension_curve 에 직접 반영한다.
        """
        if not actual_tensions:
            return None

        coeffs = self._get_coeffs(genre)
        n = len(actual_tensions)

        # 갱신 전 L_tension 계산
        l_before = self._compute_l_tension(coeffs, actual_tensions)

        # Gradient 계산 (MSE wrt T_ideal 계수)
        grad_base, grad_a1, grad_a2 = 0.0, 0.0, 0.0
        for i, actual_t in enumerate(actual_tensions):
            t = i / max(n - 1, 1)
            ideal = coeffs.t_ideal(t)
            err = (ideal - actual_t) * 2.0 / n       # d/dT_ideal of (T_ideal-T_actual)²
            grad_base += err                          # dT_ideal/dbase = 1
            grad_a1 += err * math.sin(2 * math.pi * t - 0.50)
            grad_a2 += err * math.sin(6 * math.pi * t)

        # Gradient clipping
        grad_base = _clip(grad_base, CLIP_GRAD)
        grad_a1 = _clip(grad_a1, CLIP_GRAD)
        grad_a2 = _clip(grad_a2, CLIP_GRAD)

        # SGD 갱신 (손실 최소화 → 그래디언트 반대 방향)
        new_base = _clamp(coeffs.base - T_LR * grad_base, BASE_MIN, BASE_MAX)
        new_a1 = _clamp(coeffs.a1 - T_LR * grad_a1, A1_MIN, A1_MAX)
        new_a2 = _clamp(coeffs.a2 - T_LR * grad_a2, A2_MIN, A2_MAX)

        new_coeffs = FourierCoeffs(new_base, new_a1, new_a2)
        self._coeffs[genre] = new_coeffs
        self._history[genre].append(new_coeffs.as_tuple())
        self._update_count += 1

        # NarrativeTensionCurve 에 반영
        tension_curve.update_fourier_coefficients(new_base, new_a1, new_a2)

        result = FourierUpdate(
            genre=genre,
            base=new_base,
            a1=new_a1,
            a2=new_a2,
            grad_base=grad_base,
            grad_a1=grad_a1,
            grad_a2=grad_a2,
            l_tension_before=l_before,
        )
        self._update_log.append(result)
        return result

    def get_coeffs(self, genre: str = "default") -> FourierCoeffs:
        """현재 장르별 계수 반환."""
        return self._get_coeffs(genre)

    def get_history(self, genre: str = "default") -> List[Tuple[float, float, float]]:
        return list(self._history[genre])

    def reset_genre(self, genre: str) -> None:
        """특정 장르 계수 초기화."""
        if genre in self._coeffs:
            del self._coeffs[genre]
        self._history[genre].clear()

    @property
    def update_count(self) -> int:
        return self._update_count

    @property
    def update_log(self) -> List[FourierUpdate]:
        return list(self._update_log)

    # ── 내부 헬퍼 ────────────────────────────────────────────────────────────
    def _get_coeffs(self, genre: str) -> FourierCoeffs:
        if genre not in self._coeffs:
            init = GENRE_FOURIER_INIT.get(genre, GENRE_FOURIER_INIT["default"])
            self._coeffs[genre] = FourierCoeffs(*init)
        return self._coeffs[genre]

    @staticmethod
    def _compute_l_tension(coeffs: FourierCoeffs, actuals: List[float]) -> float:
        n = len(actuals)
        if n == 0:
            return 0.0
        return sum(
            (coeffs.t_ideal(i / max(n - 1, 1)) - a) ** 2
            for i, a in enumerate(actuals)
        ) / n


# ─── 유틸 ─────────────────────────────────────────────────────────────────────
def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _clip(v: float, threshold: float) -> float:
    return max(-threshold, min(threshold, v))
