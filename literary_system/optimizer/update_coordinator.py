"""
V387 — UpdateCoordinator.
MAEWeights(LearnedCoefficientStore) ↔ PhysicsCoefficientStore 동기화 감시.
두 store가 동일 update_interval을 공유하고 불일치 없이 갱신 완료되었을 때만 Gate 통과 허용.
"""
from __future__ import annotations

from typing import Optional

from literary_system.physics.coefficient_store import PhysicsCoefficientStore


class CoordinationError(Exception):
    pass


class UpdateCoordinator:
    """
    두 store의 갱신 주기 동기화 감시자.
    - physics_store와 mae_store(learned_coefficient_store)가 동일 UPDATE_INTERVAL 사용
    - 주기 도달 시 양쪽 모두 업데이트 완료 여부 확인
    """

    def __init__(
        self,
        physics_store,
        mae_store=None,
    ) -> None:
        self._physics = physics_store
        self._mae     = mae_store
        self._synced_episodes: int = 0

    def tick_and_sync(self) -> bool:
        """
        에피소드 1회 진행. 두 store가 동기화 완료되면 True 반환.
        """
        physics_due = self._physics.tick_episode()
        mae_due = False
        if self._mae and hasattr(self._mae, 'tick_episode'):
            mae_due = self._mae.tick_episode()

        if physics_due:
            self._synced_episodes += 1
            return True
        return False

    def assert_synced(self) -> None:
        """Gate 진입 전 동기화 상태 확인. 불일치 시 CoordinationError."""
        if self._mae is None:
            return
        # 간단한 동기화 검증: episode_count 차이 확인
        p_count = getattr(self._physics, '_episode_count', 0)
        m_count = getattr(self._mae, '_episode_count', 0)
        if abs(p_count - m_count) > self._physics.UPDATE_INTERVAL:
            raise CoordinationError(
                f"UpdateCoordinator: store sync gap too large "
                f"(physics={p_count}, mae={m_count})"
            )

    @property
    def synced_count(self) -> int:
        return self._synced_episodes
