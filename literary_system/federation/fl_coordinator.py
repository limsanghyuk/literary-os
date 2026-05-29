"""FLCoordinator — 연합 학습 조율자 (V732, ADR-194)

역할:
  - 클라이언트 등록 / 라운드 관리
  - FLRound 생성 및 상태 추적
  - 최소 참여 클라이언트 수 강제 (min_clients)
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from literary_system.federation.fl_types import FLClientState, FLGlobalModel, FLRound

logger = logging.getLogger(__name__)


class InsufficientClientsError(Exception):
    """최소 클라이언트 수 미충족."""


class FLCoordinator:
    """Federated Learning 중앙 조율자.

    Args:
        min_clients: 라운드 시작에 필요한 최소 클라이언트 수.
        max_rounds: 최대 라운드 수 (수렴 판단용).
        convergence_threshold: 글로벌 손실 개선 δ 미만이면 수렴 판정.
    """

    def __init__(
        self,
        min_clients: int = 2,
        max_rounds: int = 10,
        convergence_threshold: float = 1e-4,
    ) -> None:
        if min_clients < 1:
            raise ValueError("min_clients must be >= 1")
        self.min_clients = min_clients
        self.max_rounds = max_rounds
        self.convergence_threshold = convergence_threshold

        self._clients: Dict[str, bool] = {}   # client_id → available
        self._rounds: List[FLRound] = []
        self._global_model: Optional[FLGlobalModel] = None
        self._current_round: int = 0

    # ------------------------------------------------------------------
    # 클라이언트 관리
    # ------------------------------------------------------------------

    def register_client(self, client_id: str) -> None:
        """클라이언트를 조율자에 등록."""
        if client_id in self._clients:
            logger.debug("Client %s already registered", client_id)
            return
        self._clients[client_id] = True
        logger.info("Registered client: %s (total=%d)", client_id, len(self._clients))

    def unregister_client(self, client_id: str) -> None:
        """클라이언트 등록 해제."""
        self._clients.pop(client_id, None)

    @property
    def registered_clients(self) -> List[str]:
        return list(self._clients.keys())

    # ------------------------------------------------------------------
    # 라운드 관리
    # ------------------------------------------------------------------

    def start_round(self) -> FLRound:
        """새 연합 학습 라운드를 시작한다.

        Raises:
            InsufficientClientsError: 등록된 클라이언트가 min_clients 미만.
        """
        available = [cid for cid, avail in self._clients.items() if avail]
        if len(available) < self.min_clients:
            raise InsufficientClientsError(
                f"Need >= {self.min_clients} clients, got {len(available)}"
            )
        self._current_round += 1
        rnd = FLRound(
            round_num=self._current_round,
            participants=available[:],
            status="aggregating",
        )
        self._rounds.append(rnd)
        logger.info("Started FL round %d with %d clients", self._current_round, len(available))
        return rnd

    def submit_client_state(self, state: FLClientState) -> None:
        """클라이언트 로컬 훈련 결과를 현재 라운드에 제출."""
        if not self._rounds:
            raise RuntimeError("No active round. Call start_round() first.")
        if not state.is_valid():
            raise ValueError(f"Invalid FLClientState: {state}")
        current = self._rounds[-1]
        current.client_states.append(state)
        logger.debug("Client %s submitted state for round %d", state.client_id, state.round_num)

    def finalize_round(self, global_model: FLGlobalModel) -> FLRound:
        """집계 결과를 현재 라운드에 기록하고 완료 처리."""
        if not self._rounds:
            raise RuntimeError("No active round to finalize.")
        current = self._rounds[-1]
        current.global_model = global_model
        current.status = "done"
        self._global_model = global_model

        # 수렴 판정
        if len(self._rounds) >= 2:
            prev_loss = self._rounds[-2].global_model.global_loss if self._rounds[-2].global_model else float("inf")
            delta = abs(prev_loss - global_model.global_loss)
            if delta < self.convergence_threshold:
                global_model.converged = True
                logger.info("FL converged at round %d (Δloss=%.6f)", self._current_round, delta)

        return current

    # ------------------------------------------------------------------
    # 조회
    # ------------------------------------------------------------------

    @property
    def global_model(self) -> Optional[FLGlobalModel]:
        return self._global_model

    @property
    def rounds(self) -> List[FLRound]:
        return list(self._rounds)

    def is_converged(self) -> bool:
        return bool(self._global_model and self._global_model.converged)

    def should_continue(self) -> bool:
        return (
            self._current_round < self.max_rounds
            and not self.is_converged()
        )

    def summary(self) -> Dict:
        return {
            "clients": len(self._clients),
            "rounds_completed": len(self._rounds),
            "converged": self.is_converged(),
            "global_loss": self._global_model.global_loss if self._global_model else None,
        }
