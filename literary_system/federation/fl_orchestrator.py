"""fl_orchestrator.py — FLOrchestrator E2E 파이프라인 (V736, SP-D.4)

FLCoordinator + FedAvgAggregator + FLClient[] + FLPrivacyNoise를
단일 run_federation() 호출로 묶는 최상위 오케스트레이터.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from literary_system.federation.fl_coordinator import FLCoordinator, InsufficientClientsError
from literary_system.federation.fl_client import FLClient
from literary_system.federation.fedavg import FedAvgAggregator
from literary_system.federation.fl_privacy import FLPrivacyNoise
from literary_system.federation.fl_types import FLGlobalModel


@dataclass
class FLRunResult:
    """run_federation() 최종 결과 요약."""
    total_rounds: int
    converged: bool
    final_global_loss: float
    loss_trend: List[float]
    privacy_budget: Dict
    round_summaries: List[Dict] = field(default_factory=list)
    elapsed_seconds: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "total_rounds": self.total_rounds,
            "converged": self.converged,
            "final_global_loss": self.final_global_loss,
            "loss_trend": self.loss_trend,
            "privacy_budget": self.privacy_budget,
            "round_count": len(self.round_summaries),
            "elapsed_seconds": self.elapsed_seconds,
        }


class FLOrchestrator:
    """Federated Learning E2E 오케스트레이터.

    사용법::
        orch = FLOrchestrator(clients=clients, max_rounds=5)
        result = orch.run_federation()
    """

    def __init__(
        self,
        clients: List[FLClient],
        max_rounds: int = 10,
        convergence_threshold: float = 1e-4,
        dp_epsilon: float = 1.0,
        dp_delta: float = 1e-5,
        dp_clip_norm: float = 1.0,
        use_privacy: bool = True,
        min_clients: int = 2,
    ) -> None:
        if len(clients) < min_clients:
            raise ValueError(
                f"FLOrchestrator requires at least {min_clients} clients, "
                f"got {len(clients)}"
            )
        if max_rounds < 1:
            raise ValueError("max_rounds must be >= 1")
        if dp_epsilon <= 0:
            raise ValueError("dp_epsilon must be > 0")

        self._clients = list(clients)
        self._max_rounds = max_rounds
        self._use_privacy = use_privacy

        # 내부 컴포넌트 초기화
        self._coordinator = FLCoordinator(
            min_clients=min_clients,
            max_rounds=max_rounds,
            convergence_threshold=convergence_threshold,
        )
        self._aggregator = FedAvgAggregator()
        self._privacy = FLPrivacyNoise(
            epsilon=dp_epsilon,
            delta=dp_delta,
            clip_norm=dp_clip_norm,
        )

        # 클라이언트 등록
        for c in self._clients:
            self._coordinator.register_client(c.client_id)

        self._result: Optional[FLRunResult] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_federation(self) -> FLRunResult:
        """전체 FL 루프 실행.

        1. start_round() → 2. 각 클라이언트 train() → 3. (선택) privatize()
        4. FedAvg aggregate() → 5. 전역 모델을 각 클라이언트에 broadcast
        6. finalize_round() → 7. should_continue() 반복
        """
        t0 = time.time()
        round_summaries: List[Dict] = []

        while self._coordinator.should_continue():
            fl_round = self._coordinator.start_round()
            round_num = fl_round.round_num

            # 현재 전역 모델 가중치 broadcast
            global_weights: Dict = {}
            gm = self._coordinator.global_model
            if gm is not None:
                global_weights = gm.global_weights
            for c in self._clients:
                if c.client_id in fl_round.participants:
                    c.receive_global_model(global_weights)

            # 로컬 훈련
            client_states = []
            for c in self._clients:
                if c.client_id in fl_round.participants:
                    state = c.train(round_num)
                    client_states.append(state)

            # (선택) DP 노이즈 적용
            if self._use_privacy:
                for state in client_states:
                    state.weights = self._privacy.privatize(state.weights)

            # FedAvg 집계
            new_global = self._aggregator.aggregate(
                client_states,
                round_num=round_num,
                current_global=self._coordinator.global_model,
            )

            # 라운드 마감
            self._coordinator.finalize_round(new_global)

            round_summaries.append({
                "round": round_num,
                "participants": len(client_states),
                "global_loss": new_global.global_loss,
                "converged": new_global.converged,
            })

        final_gm = self._coordinator.global_model
        final_loss = final_gm.global_loss if final_gm else 0.0

        self._result = FLRunResult(
            total_rounds=len(self._coordinator.rounds),
            converged=self._coordinator.is_converged(),
            final_global_loss=final_loss,
            loss_trend=self._aggregator.loss_trend(),
            privacy_budget=self._privacy.privacy_budget,
            round_summaries=round_summaries,
            elapsed_seconds=time.time() - t0,
        )
        return self._result

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def result(self) -> Optional[FLRunResult]:
        """마지막 run_federation() 결과 (실행 전: None)."""
        return self._result

    @property
    def coordinator(self) -> FLCoordinator:
        return self._coordinator

    @property
    def aggregator(self) -> FedAvgAggregator:
        return self._aggregator

    @property
    def privacy(self) -> FLPrivacyNoise:
        return self._privacy

    @property
    def clients(self) -> List[FLClient]:
        return list(self._clients)

    def summary(self) -> Dict:
        """오케스트레이터 상태 요약."""
        base = {
            "num_clients": len(self._clients),
            "max_rounds": self._max_rounds,
            "use_privacy": self._use_privacy,
            "privacy_epsilon": self._privacy.privacy_budget["epsilon"],
        }
        if self._result:
            base.update(self._result.to_dict())
        return base
