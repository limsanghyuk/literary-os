"""FLPrivacyNoise — 차분 프라이버시 노이즈 (V734, ADR-196)

Gaussian Mechanism 기반 ε-δ 차분 프라이버시 노이즈를 FedAvg 가중치에 주입.

참조: Abadi et al., "Deep Learning with Differential Privacy", CCS 2016.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List, Optional


class FLPrivacyNoise:
    """Gaussian Mechanism 차분 프라이버시 노이즈 주입기.

    노이즈 크기:
        σ = clip_norm * sqrt(2 * ln(1.25/δ)) / ε

    Args:
        epsilon: 프라이버시 예산 ε (작을수록 강한 보호, 기본 1.0).
        delta: 실패 확률 δ (기본 1e-5).
        clip_norm: 그래디언트 클리핑 노름 C (기본 1.0).
        seed: 재현성 난수 시드.
    """

    def __init__(
        self,
        epsilon: float = 1.0,
        delta: float = 1e-5,
        clip_norm: float = 1.0,
        seed: Optional[int] = None,
    ) -> None:
        if epsilon <= 0:
            raise ValueError("epsilon must be > 0")
        if not (0 < delta < 1):
            raise ValueError("delta must be in (0, 1)")
        if clip_norm <= 0:
            raise ValueError("clip_norm must be > 0")

        self.epsilon = epsilon
        self.delta = delta
        self.clip_norm = clip_norm
        self._rng = random.Random(seed)

        # Gaussian Mechanism 노이즈 표준편차
        self.sigma = self._compute_sigma()

    def _compute_sigma(self) -> float:
        """σ = C * sqrt(2 * ln(1.25/δ)) / ε"""
        return self.clip_norm * math.sqrt(2 * math.log(1.25 / self.delta)) / self.epsilon

    def add_noise(
        self, weights: Dict[str, List[float]]
    ) -> Dict[str, List[float]]:
        """가중치 딕셔너리에 Gaussian 노이즈를 추가하여 새 딕셔너리 반환.

        원본은 변경하지 않음.
        """
        noisy = {}
        for key, vals in weights.items():
            noisy[key] = [
                v + self._rng.gauss(0, self.sigma) for v in vals
            ]
        return noisy

    def clip_weights(
        self, weights: Dict[str, List[float]]
    ) -> Dict[str, List[float]]:
        """L2 norm을 clip_norm으로 클리핑.

        각 레이어 벡터를 개별적으로 클리핑.
        """
        clipped = {}
        for key, vals in weights.items():
            norm = math.sqrt(sum(v**2 for v in vals))
            if norm > self.clip_norm and norm > 0:
                scale = self.clip_norm / norm
                clipped[key] = [v * scale for v in vals]
            else:
                clipped[key] = list(vals)
        return clipped

    def privatize(
        self, weights: Dict[str, List[float]]
    ) -> Dict[str, List[float]]:
        """클리핑 후 노이즈 추가 — DP 파이프라인 전체."""
        clipped = self.clip_weights(weights)
        return self.add_noise(clipped)

    @property
    def privacy_budget(self) -> Dict[str, float]:
        return {"epsilon": self.epsilon, "delta": self.delta, "sigma": self.sigma}
