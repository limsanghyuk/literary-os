"""
constraint_guard.py — ConstraintGuard: KL 발산 클램프 + 보상 안전성 제한 (V603)

ADR-063 참조. LLM-0 원칙 준수 (외부 API 호출 없음).

책임:
  - PPO 학습 중 KL 발산이 임계값 초과 시 조기 종료 신호 발생
  - 보상 값 범위 클램프 (음수 폭발, 양수 폭발 방지)
  - 정책 업데이트 크기(delta) 상한 제한
  - 제약 위반 이력 추적
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional

# ---------------------------------------------------------------------------
# 기본 제약 임계값
# ---------------------------------------------------------------------------
DEFAULT_KL_HARD_LIMIT: float = 0.15      # KL 이 이 값 초과 시 강제 중단
DEFAULT_REWARD_MIN: float = -10.0        # 보상 하한 클램프
DEFAULT_REWARD_MAX: float = 10.0         # 보상 상한 클램프
DEFAULT_DELTA_MAX: float = 0.50          # 정책 파라미터 단계 상한
DEFAULT_ENTROPY_MIN: float = 0.001       # 엔트로피 붕괴(collapse) 감지 하한


# ---------------------------------------------------------------------------
# 데이터클래스
# ---------------------------------------------------------------------------
@dataclass
class GuardConfig:
    """ConstraintGuard 설정."""

    kl_hard_limit: float = DEFAULT_KL_HARD_LIMIT
    reward_min: float = DEFAULT_REWARD_MIN
    reward_max: float = DEFAULT_REWARD_MAX
    delta_max: float = DEFAULT_DELTA_MAX
    entropy_min: float = DEFAULT_ENTROPY_MIN
    # 연속 위반 허용 횟수 (이 횟수 초과 시 학습 중단)
    max_consecutive_violations: int = 3

    def __post_init__(self) -> None:
        if self.kl_hard_limit <= 0.0:
            raise ValueError(f"kl_hard_limit must be > 0, got {self.kl_hard_limit}")
        if self.reward_min >= self.reward_max:
            raise ValueError(
                f"reward_min({self.reward_min}) must be < reward_max({self.reward_max})"
            )
        if self.delta_max <= 0.0:
            raise ValueError(f"delta_max must be > 0, got {self.delta_max}")
        if self.entropy_min < 0.0:
            raise ValueError(f"entropy_min must be >= 0, got {self.entropy_min}")


@dataclass
class ConstraintViolationRecord:
    """단일 제약 위반 기록."""

    step: int
    violation_type: str   # "kl_exceeded" | "reward_clamp" | "delta_exceeded" | "entropy_collapse"
    value: float          # 위반 당시 측정값
    threshold: float      # 적용된 임계값
    clamped_to: Optional[float] = None  # 클램프 적용 시 조정된 값


@dataclass
class GuardState:
    """ConstraintGuard 런타임 상태."""

    violations: List[ConstraintViolationRecord] = field(default_factory=list)
    consecutive_kl_violations: int = 0
    total_reward_clamps: int = 0
    total_delta_clamps: int = 0
    total_entropy_collapses: int = 0
    should_stop: bool = False
    stop_reason: str = ""

    # 통계
    @property
    def total_violations(self) -> int:
        return len(self.violations)

    def summary(self) -> dict:
        return {
            "total_violations": self.total_violations,
            "consecutive_kl_violations": self.consecutive_kl_violations,
            "total_reward_clamps": self.total_reward_clamps,
            "total_delta_clamps": self.total_delta_clamps,
            "total_entropy_collapses": self.total_entropy_collapses,
            "should_stop": self.should_stop,
            "stop_reason": self.stop_reason,
        }


# ---------------------------------------------------------------------------
# ConstraintGuard
# ---------------------------------------------------------------------------
class ConstraintGuard:
    """
    PPO 학습 루프의 안전성 가드.

    사용법::

        guard = ConstraintGuard()
        for step_idx, batch in enumerate(batches):
            result = trainer.step(batch)
            kl = guard.check_kl(step_idx, result.kl_divergence)
            reward = guard.clamp_reward(result.mean_reward)
            if guard.state.should_stop:
                break
    """

    def __init__(self, config: Optional[GuardConfig] = None) -> None:
        self.config: GuardConfig = config or GuardConfig()
        self.state: GuardState = GuardState()

    # ------------------------------------------------------------------
    # 공개 메서드
    # ------------------------------------------------------------------

    def check_kl(self, step: int, kl: float) -> float:
        """
        KL 발산 확인. 하드 리밋 초과 시 should_stop = True.

        Returns:
            kl (변경 없음 — 클램프 없이 기록만)
        """
        if not math.isfinite(kl):
            kl = self.config.kl_hard_limit * 2.0  # NaN/Inf → 강제 위반 처리

        if kl > self.config.kl_hard_limit:
            self.state.consecutive_kl_violations += 1
            self.state.violations.append(
                ConstraintViolationRecord(
                    step=step,
                    violation_type="kl_exceeded",
                    value=kl,
                    threshold=self.config.kl_hard_limit,
                )
            )
            if (
                self.state.consecutive_kl_violations
                >= self.config.max_consecutive_violations
            ):
                self.state.should_stop = True
                self.state.stop_reason = (
                    f"KL {kl:.4f} > hard_limit {self.config.kl_hard_limit} "
                    f"for {self.state.consecutive_kl_violations} consecutive steps"
                )
        else:
            # 위반 없으면 연속 카운터 리셋
            self.state.consecutive_kl_violations = 0

        return kl

    def clamp_reward(self, step: int, reward: float) -> float:
        """
        보상 값을 [reward_min, reward_max] 범위로 클램프.

        Returns:
            클램프된 보상 값
        """
        if not math.isfinite(reward):
            clamped = 0.0
            self.state.violations.append(
                ConstraintViolationRecord(
                    step=step,
                    violation_type="reward_clamp",
                    value=reward,
                    threshold=self.config.reward_max,
                    clamped_to=clamped,
                )
            )
            self.state.total_reward_clamps += 1
            return clamped

        clamped = max(self.config.reward_min, min(self.config.reward_max, reward))
        if clamped != reward:
            self.state.violations.append(
                ConstraintViolationRecord(
                    step=step,
                    violation_type="reward_clamp",
                    value=reward,
                    threshold=self.config.reward_max
                    if reward > self.config.reward_max
                    else self.config.reward_min,
                    clamped_to=clamped,
                )
            )
            self.state.total_reward_clamps += 1

        return clamped

    def clamp_delta(self, step: int, delta: float) -> float:
        """
        정책 파라미터 업데이트 크기(delta)를 [-delta_max, +delta_max] 클램프.

        Returns:
            클램프된 delta 값
        """
        if not math.isfinite(delta):
            self.state.total_delta_clamps += 1
            return 0.0

        sign = 1.0 if delta >= 0.0 else -1.0
        abs_delta = abs(delta)
        if abs_delta > self.config.delta_max:
            clamped = sign * self.config.delta_max
            self.state.violations.append(
                ConstraintViolationRecord(
                    step=step,
                    violation_type="delta_exceeded",
                    value=delta,
                    threshold=self.config.delta_max,
                    clamped_to=clamped,
                )
            )
            self.state.total_delta_clamps += 1
            return clamped

        return delta

    def check_entropy(self, step: int, entropy: float) -> bool:
        """
        엔트로피 붕괴(collapse) 감지.

        Returns:
            True if entropy collapsed (below entropy_min)
        """
        if not math.isfinite(entropy) or entropy < self.config.entropy_min:
            self.state.violations.append(
                ConstraintViolationRecord(
                    step=step,
                    violation_type="entropy_collapse",
                    value=entropy if math.isfinite(entropy) else -1.0,
                    threshold=self.config.entropy_min,
                )
            )
            self.state.total_entropy_collapses += 1
            return True
        return False

    def reset(self) -> None:
        """상태 초기화 (새 학습 세션 시작 시)."""
        self.state = GuardState()

    def is_safe(self) -> bool:
        """현재 학습이 안전하게 계속될 수 있는지 반환."""
        return not self.state.should_stop
