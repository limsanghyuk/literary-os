"""
SP-B.2 (V604) — RLHFMonitor: RLHF 보상 추세 모니터링 + 자동 롤백

설계 원칙 (ADR-064, Phase B 본안 v2.0):
  - 슬라이딩 윈도우 이동 평균으로 보상 추세 감지
  - 연속 감소 횟수 >= degradation_steps 시 자동 롤백 트리거
  - rollback_threshold 이하 보상 + 감소 추세 → 즉시 롤백
  - 최소 min_samples 이상 수집 후 추세 판단 (cold-start 보호)
  - LLM-0 원칙: 외부 LLM API 직접 호출 없음

ADR-064 참조.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------
TREND_IMPROVING: str = "improving"
TREND_DEGRADING: str = "degrading"
TREND_STABLE: str = "stable"
TREND_UNKNOWN: str = "unknown"   # cold-start (min_samples 미달)

IMPROVE_DELTA: float = 0.01     # 이동 평균 증가 임계 (improving 판정)
DEGRADE_DELTA: float = -0.01    # 이동 평균 감소 임계 (degrading 판정)


# ---------------------------------------------------------------------------
# 설정 및 데이터 클래스
# ---------------------------------------------------------------------------
@dataclass
class MonitorConfig:
    """RLHFMonitor 동작 설정."""

    window_size: int = 10
    """이동 평균 윈도우 크기."""

    rollback_threshold: float = 0.60
    """보상이 이 값 미만이고 degrading 추세면 롤백 트리거."""

    degradation_steps: int = 3
    """연속 감소 스텝 수 >= 이 값 → 자동 롤백."""

    min_samples: int = 5
    """추세 판단 최소 누적 스텝 수 (cold-start 보호)."""

    reward_floor: float = 0.0
    """보상 하한 클램프 (음수 보상 방지)."""

    def __post_init__(self) -> None:
        if self.window_size < 1:
            raise ValueError(f"window_size must be >= 1, got {self.window_size}")
        if not (0.0 <= self.rollback_threshold <= 1.0):
            raise ValueError(
                f"rollback_threshold must be in [0,1], got {self.rollback_threshold}"
            )
        if self.degradation_steps < 1:
            raise ValueError(
                f"degradation_steps must be >= 1, got {self.degradation_steps}"
            )
        if self.min_samples < 1:
            raise ValueError(f"min_samples must be >= 1, got {self.min_samples}")


@dataclass
class RewardSnapshot:
    """단일 스텝의 보상 스냅샷."""

    step: int
    mean_reward: float
    moving_avg: float
    trend: str
    n_samples: int


@dataclass
class RollbackRecord:
    """자동 롤백 트리거 이력."""

    step: int
    trigger_reason: str
    reward_at_trigger: float
    moving_avg_at_trigger: float
    consecutive_degradations: int


@dataclass
class MonitorState:
    """RLHFMonitor 전체 상태."""

    snapshots: List[RewardSnapshot] = field(default_factory=list)
    rollback_records: List[RollbackRecord] = field(default_factory=list)
    consecutive_degradations: int = 0
    should_rollback: bool = False
    rollback_reason: str = ""
    total_rollbacks: int = 0


# ---------------------------------------------------------------------------
# 핵심 클래스
# ---------------------------------------------------------------------------
class RLHFMonitor:
    """
    RLHF 훈련 중 보상 추세를 모니터링하고 자동 롤백을 트리거한다.

    사용 예:
        monitor = RLHFMonitor()
        snap = monitor.record(step=1, rewards=[0.72, 0.68, 0.75])
        if monitor.check_rollback(step=1):
            pass  # handle rollback: monitor.state.rollback_reason
    """

    def __init__(self, config: Optional[MonitorConfig] = None) -> None:
        self.config: MonitorConfig = config or MonitorConfig()
        self.state: MonitorState = MonitorState()
        self._reward_history: List[float] = []   # 전체 스텝 평균 보상 이력

    # ------------------------------------------------------------------
    # 기록
    # ------------------------------------------------------------------
    def record(self, step: int, rewards: Sequence[float]) -> RewardSnapshot:
        """
        한 스텝의 보상 배치를 기록하고 스냅샷을 반환한다.

        Args:
            step:    현재 훈련 스텝 번호
            rewards: 해당 스텝에서 얻은 보상 값 목록

        Returns:
            RewardSnapshot — 이동 평균·추세 포함
        """
        if not rewards:
            raise ValueError("rewards must not be empty")

        # 배치 평균 (floor 클램프)
        mean_r = max(
            self.config.reward_floor,
            sum(rewards) / len(rewards),
        )
        self._reward_history.append(mean_r)

        mvg = self._moving_average_value()
        tr = self._compute_trend()

        snap = RewardSnapshot(
            step=step,
            mean_reward=mean_r,
            moving_avg=mvg,
            trend=tr,
            n_samples=len(self._reward_history),
        )
        self.state.snapshots.append(snap)

        # 연속 감소 카운터 업데이트
        self._update_degradation_counter(mean_r)

        return snap

    # ------------------------------------------------------------------
    # 이동 평균
    # ------------------------------------------------------------------
    def moving_average(self, n: Optional[int] = None) -> float:
        """
        최근 n 스텝의 이동 평균을 반환한다.

        Args:
            n: 윈도우 크기 (None이면 config.window_size 사용)

        Returns:
            이동 평균 값. 기록이 없으면 0.0.
        """
        return self._moving_average_value(n)

    def _moving_average_value(self, n: Optional[int] = None) -> float:
        win = n if n is not None else self.config.window_size
        if not self._reward_history:
            return 0.0
        window = self._reward_history[-win:]
        return sum(window) / len(window)

    # ------------------------------------------------------------------
    # 추세
    # ------------------------------------------------------------------
    def trend(self) -> str:
        """현재 보상 추세를 반환한다."""
        return self._compute_trend()

    def _compute_trend(self) -> str:
        n = len(self._reward_history)
        if n < self.config.min_samples:
            return TREND_UNKNOWN

        # 윈도우 반 나눠 전반 평균 vs 후반 평균 비교
        win = min(self.config.window_size, n)
        recent = self._reward_history[-win:]
        half = max(1, win // 2)
        first_half_avg = sum(recent[:half]) / half
        second_half_avg = sum(recent[half:]) / max(1, len(recent) - half)

        delta = second_half_avg - first_half_avg
        if delta >= IMPROVE_DELTA:
            return TREND_IMPROVING
        if delta <= DEGRADE_DELTA:
            return TREND_DEGRADING
        return TREND_STABLE

    # ------------------------------------------------------------------
    # 롤백
    # ------------------------------------------------------------------
    def _update_degradation_counter(self, mean_r: float) -> None:
        """연속 감소 카운터를 갱신한다."""
        n = len(self._reward_history)
        if n < 2:
            self.state.consecutive_degradations = 0
            return

        prev = self._reward_history[-2]
        if mean_r < prev:
            self.state.consecutive_degradations += 1
        else:
            self.state.consecutive_degradations = 0

    def check_rollback(self, step: int) -> bool:
        """
        현재 상태에서 롤백이 필요한지 판단하고,
        필요하면 state.should_rollback = True로 설정한다.

        트리거 조건 (OR):
          1. 연속 감소 횟수 >= config.degradation_steps
          2. 이동 평균 < config.rollback_threshold AND 추세 == degrading

        Returns:
            True이면 롤백 트리거됨.
        """
        mvg = self._moving_average_value()
        tr = self._compute_trend()
        reason: str = ""

        # 조건 1: 연속 감소
        if self.state.consecutive_degradations >= self.config.degradation_steps:
            reason = (
                f"consecutive_degradations={self.state.consecutive_degradations} "
                f">= {self.config.degradation_steps}"
            )

        # 조건 2: 낮은 이동 평균 + degrading
        if not reason and (
            mvg < self.config.rollback_threshold
            and tr == TREND_DEGRADING
        ):
            reason = (
                f"moving_avg={mvg:.4f} < threshold={self.config.rollback_threshold} "
                f"AND trend=degrading"
            )

        if reason:
            self.state.should_rollback = True
            self.state.rollback_reason = reason
            self.state.total_rollbacks += 1
            self.state.rollback_records.append(
                RollbackRecord(
                    step=step,
                    trigger_reason=reason,
                    reward_at_trigger=self._reward_history[-1] if self._reward_history else 0.0,
                    moving_avg_at_trigger=mvg,
                    consecutive_degradations=self.state.consecutive_degradations,
                )
            )
            return True

        return False

    def reset_rollback_flag(self) -> None:
        """롤백 플래그와 연속 감소 카운터를 초기화한다 (롤백 수행 후 호출)."""
        self.state.should_rollback = False
        self.state.rollback_reason = ""
        self.state.consecutive_degradations = 0

    # ------------------------------------------------------------------
    # 요약
    # ------------------------------------------------------------------
    def summary(self) -> Dict:
        """
        현재 모니터 상태 요약 딕셔너리를 반환한다.

        Required keys:
            total_steps, current_moving_avg, current_trend,
            total_rollbacks, consecutive_degradations,
            should_rollback, last_mean_reward
        """
        last_r = self._reward_history[-1] if self._reward_history else 0.0
        return {
            "total_steps": len(self._reward_history),
            "current_moving_avg": round(self._moving_average_value(), 6),
            "current_trend": self._compute_trend(),
            "total_rollbacks": self.state.total_rollbacks,
            "consecutive_degradations": self.state.consecutive_degradations,
            "should_rollback": self.state.should_rollback,
            "last_mean_reward": round(last_r, 6),
        }
