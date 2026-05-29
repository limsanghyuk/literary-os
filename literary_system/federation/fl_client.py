"""FLClient — 연합 학습 로컬 훈련 시뮬레이터 (V734, ADR-196)

역할:
  - 로컬 데이터셋 시뮬레이션 (ProseDataShard)
  - 로컬 SGD 훈련 (N 에폭)
  - 훈련 후 FLClientState 반환
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from literary_system.federation.fl_types import FLClientState


@dataclass
class ProseDataShard:
    """단일 클라이언트 로컬 데이터 샤드.

    실제 텍스트 대신 손실 시뮬레이션 파라미터를 보유.
    """
    shard_id: str
    num_samples: int
    base_loss: float = 1.0          # 훈련 전 기본 손실
    noise_std: float = 0.05         # 배치 손실 노이즈

    def __post_init__(self):
        if self.num_samples <= 0:
            raise ValueError("num_samples must be > 0")
        if self.base_loss < 0:
            raise ValueError("base_loss must be >= 0")


class FLClient:
    """연합 학습 클라이언트 — 로컬 SGD 훈련 시뮬레이터.

    Args:
        client_id: 고유 클라이언트 식별자.
        shard: 로컬 데이터 샤드.
        learning_rate: SGD 학습률 (로컬 업데이트 크기 결정).
        local_epochs: 로컬 에폭 수.
        weight_dim: 시뮬레이션 가중치 차원 (벡터 길이).
        seed: 재현성 난수 시드.
    """

    def __init__(
        self,
        client_id: str,
        shard: ProseDataShard,
        learning_rate: float = 0.01,
        local_epochs: int = 3,
        weight_dim: int = 8,
        seed: Optional[int] = None,
    ) -> None:
        if not client_id:
            raise ValueError("client_id must not be empty")
        if learning_rate <= 0:
            raise ValueError("learning_rate must be > 0")
        if local_epochs < 1:
            raise ValueError("local_epochs must be >= 1")

        self.client_id = client_id
        self.shard = shard
        self.learning_rate = learning_rate
        self.local_epochs = local_epochs
        self.weight_dim = weight_dim
        self._rng = random.Random(seed)

        # 로컬 가중치 (글로벌 모델 초기화 후 덮어씌워짐)
        self._local_weights: Dict[str, List[float]] = {
            "layer_0": [self._rng.gauss(0, 0.1) for _ in range(weight_dim)],
        }

    def receive_global_model(self, global_weights: Dict[str, List[float]]) -> None:
        """서버로부터 글로벌 가중치를 수신하여 로컬 가중치를 덮어씀."""
        self._local_weights = {k: list(v) for k, v in global_weights.items()}
        if not self._local_weights:
            # 글로벌 모델이 비어있으면 기존 로컬 가중치 유지
            self._local_weights = {
                "layer_0": [self._rng.gauss(0, 0.1) for _ in range(self.weight_dim)],
            }

    def train(self, round_num: int) -> FLClientState:
        """로컬 SGD 훈련 수행 후 FLClientState 반환.

        손실 시뮬레이션:
            loss_t = base_loss * exp(-lr * epoch) + noise
        가중치 시뮬레이션:
            w_t = w_{t-1} - lr * gradient_noise
        """
        current_loss = self.shard.base_loss
        weights = {k: list(v) for k, v in self._local_weights.items()}

        for epoch in range(self.local_epochs):
            # 손실 감소 시뮬레이션 (지수 감쇠)
            current_loss = self.shard.base_loss * math.exp(
                -self.learning_rate * (epoch + 1)
            ) + self._rng.gauss(0, self.shard.noise_std)
            current_loss = max(0.0, current_loss)

            # 가중치 업데이트 시뮬레이션 (SGD 방향 근사)
            for key in weights:
                gradient = [self._rng.gauss(0, 0.1) for _ in weights[key]]
                weights[key] = [
                    w - self.learning_rate * g
                    for w, g in zip(weights[key], gradient)
                ]

        # 훈련 결과 저장
        self._local_weights = weights

        return FLClientState(
            client_id=self.client_id,
            round_num=round_num,
            num_samples=self.shard.num_samples,
            local_loss=current_loss,
            weights=weights,
        )

    @property
    def local_weights(self) -> Dict[str, List[float]]:
        return {k: list(v) for k, v in self._local_weights.items()}
