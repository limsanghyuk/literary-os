"""
V511 - NarrativeTensionCurve
Gap 2 (RAG) + NIL 목적 함수 수렴점.

T_ideal(t) = 0.60 + 0.40·sin(2πt - 0.50) + 0.20·sin(6πt)
L_tension  = (1/N)·Σ_t (T_actual(t) - T_ideal(t))²
L_coverage = Σ_act max(0, target_cnt - actual_cnt)²
L_final    = L_tension + λ·L_coverage   (λ=0.3 초기, MetaLearner V515+에서 학습)

TIdealLearner (V518+) 연동: Fourier 계수 작품·장르별 적응.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# 기본 T_ideal 계수 (하드코딩 초기값 — V518에서 학습)
T_BASE   = 0.60
T_A1     = 0.40   # sin(2πt - 0.50) 계수
T_A2     = 0.20   # sin(6πt) 계수
LAMBDA   = 0.30   # L_coverage 가중치


@dataclass
class TensionPoint:
    """단일 씬의 긴장도 측정값."""
    t: float           # 정규화된 진행도 [0.0, 1.0]
    actual: float      # 실제 긴장도
    ideal: float       # 이상 긴장도
    diff_sq: float     # (actual - ideal)²

    def to_dict(self) -> dict:
        return {
            "t": round(self.t, 3),
            "actual": round(self.actual, 3),
            "ideal": round(self.ideal, 3),
            "diff_sq": round(self.diff_sq, 6),
        }


@dataclass
class LossResult:
    """NIL 목적 함수 결과."""
    l_tension: float
    l_coverage: float
    l_final: float
    lambda_val: float
    n_points: int

    def to_dict(self) -> dict:
        return {
            "l_tension": round(self.l_tension, 6),
            "l_coverage": round(self.l_coverage, 6),
            "l_final": round(self.l_final, 6),
            "lambda": round(self.lambda_val, 3),
            "n_points": self.n_points,
        }


class NarrativeTensionCurve:
    """
    NIL 수렴점 — T_ideal 곡선 + L_final 손실 함수.

    V511 구현: 고정 Fourier 계수.
    V518+: TIdealLearner가 계수를 작품별로 학습.
    """

    def __init__(
        self,
        base: float = T_BASE,
        a1: float = T_A1,
        a2: float = T_A2,
        lam: float = LAMBDA,
    ) -> None:
        self._base = base
        self._a1 = a1
        self._a2 = a2
        self._lambda = lam
        self._points: List[TensionPoint] = []

    # ── T_ideal ───────────────────────────────────────────────────

    def t_ideal(self, t: float) -> float:
        """
        T_ideal(t) = base + a1·sin(2πt - 0.50) + a2·sin(6πt)
        t ∈ [0.0, 1.0]: 정규화된 작품 진행도.
        """
        return (
            self._base
            + self._a1 * math.sin(2 * math.pi * t - 0.50)
            + self._a2 * math.sin(6 * math.pi * t)
        )

    def ideal_curve(self, n_points: int = 100) -> List[Tuple[float, float]]:
        """T_ideal 곡선 샘플링. [(t, ideal), ...]
        [B1-FIX] Fourier 합성값을 [0.0, 1.0] 범위로 클립하여 초과값 방지.
        """
        return [
            (i / (n_points - 1), max(0.0, min(1.0, self.t_ideal(i / (n_points - 1)))))
            for i in range(n_points)
        ]

    # ── 실측 긴장도 기록 ──────────────────────────────────────────

    def record(self, scene_idx: int, total_scenes: int, actual_tension: float) -> TensionPoint:
        """
        씬의 실측 긴장도 기록.
        t = scene_idx / max(total_scenes - 1, 1)
        """
        t = scene_idx / max(total_scenes - 1, 1)
        ideal = self.t_ideal(t)
        diff_sq = (actual_tension - ideal) ** 2
        point = TensionPoint(t=t, actual=actual_tension, ideal=ideal, diff_sq=diff_sq)
        self._points.append(point)
        return point

    # ── L_tension ─────────────────────────────────────────────────

    def compute_l_tension(self) -> float:
        """L_tension = (1/N) · Σ (actual - ideal)²"""
        if not self._points:
            return 0.0
        return sum(p.diff_sq for p in self._points) / len(self._points)

    # ── L_coverage ────────────────────────────────────────────────

    @staticmethod
    def compute_l_coverage(
        target_counts: Dict[str, int],
        actual_counts: Dict[str, int],
    ) -> float:
        """
        L_coverage = Σ_act max(0, target_cnt - actual_cnt)²
        act: 감정 상태, 관계 이벤트 등의 서사 행위
        """
        return sum(
            max(0, target_counts.get(act, 0) - actual_counts.get(act, 0)) ** 2
            for act in target_counts
        )

    # ── L_final ───────────────────────────────────────────────────

    def compute_l_final(
        self,
        target_counts: Optional[Dict[str, int]] = None,
        actual_counts: Optional[Dict[str, int]] = None,
    ) -> LossResult:
        """
        L_final = L_tension + λ·L_coverage
        λ = self._lambda (초기 0.3, V515+ MetaLearner 학습)
        """
        l_tension = self.compute_l_tension()
        l_coverage = 0.0
        if target_counts and actual_counts:
            l_coverage = self.compute_l_coverage(target_counts, actual_counts)

        # [B2-FIX] ADR-020 준수: L_final = λ·L_tension + (1-λ)·L_coverage
        l_final = self._lambda * l_tension + (1 - self._lambda) * l_coverage

        return LossResult(
            l_tension=l_tension,
            l_coverage=l_coverage,
            l_final=l_final,
            lambda_val=self._lambda,
            n_points=len(self._points),
        )

    # ── TIdealLearner 연동 (V518+) ────────────────────────────────

    def update_fourier_coefficients(
        self,
        base: float,
        a1: float,
        a2: float,
    ) -> None:
        """V518+ TIdealLearner에서 학습된 계수 주입."""
        self._base = max(0.0, min(1.0, base))
        self._a1 = max(-1.0, min(1.0, a1))
        self._a2 = max(-1.0, min(1.0, a2))
        logger.debug("TensionCurve Fourier updated: base=%.3f a1=%.3f a2=%.3f",
                     self._base, self._a1, self._a2)

    def update_lambda(self, lam: float) -> None:
        """MetaLearner (V515+)에서 λ 업데이트."""
        self._lambda = max(0.0, min(2.0, lam))

    # ── 조회 ──────────────────────────────────────────────────────

    def get_points(self) -> List[TensionPoint]:
        return list(self._points)

    def reset(self) -> None:
        self._points.clear()

    def get_config(self) -> dict:
        return {
            "base": self._base,
            "a1": self._a1,
            "a2": self._a2,
            "lambda": self._lambda,
        }
