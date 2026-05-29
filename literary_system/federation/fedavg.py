"""FedAvg 집계 알고리즘 스텁 — V733 (ADR-195)

V734~V735에서 완전 구현된다. 현재는 가중 평균 골격만 제공.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

from literary_system.federation.fl_types import FLClientState, FLGlobalModel


class FedAvgAggregator:
    """Federated Averaging (McMahan et al., 2017) 집계기.

    FedAvg 공식:
        w_global = Σ (n_k / N) * w_k
    where n_k = 클라이언트 k의 샘플 수, N = 전체 샘플 수 합계.

    V733: 스텁 — aggregate() 시그니처 + 기본 계산 골격
    V734: FLPrivacyNoise DP 노이즈 추가 완전 구현
    """

    def __init__(self, dp_noise_scale: float = 0.0) -> None:
        """
        Args:
            dp_noise_scale: 차분 프라이버시 노이즈 크기 (0 = 비활성, V734에서 완전 구현).
        """
        self.dp_noise_scale = dp_noise_scale
        self._history: List[FLGlobalModel] = []

    def aggregate(
        self,
        client_states: List[FLClientState],
        round_num: int,
        current_global: Optional[Dict[str, List[float]]] = None,
    ) -> FLGlobalModel:
        """FedAvg 가중 평균으로 글로벌 모델 갱신.

        Args:
            client_states: 참여 클라이언트 로컬 훈련 결과 목록.
            round_num: 현재 라운드 번호.
            current_global: 이전 글로벌 가중치 (없으면 0으로 초기화).

        Returns:
            새 FLGlobalModel.

        Raises:
            ValueError: 클라이언트 목록이 비어있거나 유효하지 않을 때.
        """
        valid = [s for s in client_states if s.is_valid()]
        if not valid:
            raise ValueError("No valid client states for aggregation")

        total_samples = sum(s.num_samples for s in valid)
        if total_samples == 0:
            raise ValueError("Total samples must be > 0")

        # 가중치가 있는 클라이언트만 FedAvg 수행
        states_with_weights = [s for s in valid if s.weights]

        global_weights: Dict[str, List[float]] = {}
        if states_with_weights:
            # 모든 레이어 키 수집
            all_keys = set()
            for s in states_with_weights:
                all_keys.update(s.weights.keys())

            for key in all_keys:
                # FedAvg 가중 평균
                agg = None
                for s in states_with_weights:
                    if key not in s.weights:
                        continue
                    w_k = s.weights[key]
                    n_k = s.num_samples
                    scaled = [v * n_k / total_samples for v in w_k]
                    if agg is None:
                        agg = scaled
                    else:
                        agg = [a + b for a, b in zip(agg, scaled)]
                if agg is not None:
                    global_weights[key] = agg

        # 글로벌 손실: 샘플 수 가중 평균
        global_loss = sum(s.local_loss * s.num_samples / total_samples for s in valid)

        gm = FLGlobalModel(
            round_num=round_num,
            global_weights=global_weights,
            aggregated_from=len(valid),
            global_loss=global_loss,
        )
        self._history.append(gm)
        return gm

    @property
    def history(self) -> List[FLGlobalModel]:
        return list(self._history)

    def loss_trend(self) -> List[float]:
        """히스토리에서 글로벌 손실 추이를 반환."""
        return [m.global_loss for m in self._history]

    def is_improving(self) -> bool:
        """최근 두 라운드 손실이 감소 중인지 확인."""
        if len(self._history) < 2:
            return True
        return self._history[-1].global_loss < self._history[-2].global_loss
