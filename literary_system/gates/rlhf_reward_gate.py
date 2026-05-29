"""Gate G56 — RLHF 보상 게이트: mean_reward ≥ 0.75 AND delta ≥ 0.05 (V606, ADR-066)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

REWARD_THRESHOLD: float = 0.75
DELTA_THRESHOLD: float = 0.05

GATE_ID = "G56"
GATE_NAME = "RLHF Reward Gate"


@dataclass
class RLHFRewardGateResult:
    """G56 게이트 결과."""

    passed: bool
    mean_reward: float
    delta: float
    reward_threshold: float
    delta_threshold: float
    n_samples: int
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def run_rlhf_reward_gate(
    rewards: List[float],
    baseline: float,
    reward_threshold: float = REWARD_THRESHOLD,
    delta_threshold: float = DELTA_THRESHOLD,
) -> RLHFRewardGateResult:
    """G56 게이트 실행.

    Args:
        rewards: RLHF 학습 후 보상 목록 (씬 단위).
        baseline: 베이스라인 평균 보상 (사전 학습 또는 이전 체크포인트).
        reward_threshold: mean_reward 임계값 (기본 0.75).
        delta_threshold: 향상도 임계값 (기본 0.05).

    Returns:
        RLHFRewardGateResult with passed, mean_reward, delta, reason.
    """
    if not rewards:
        return RLHFRewardGateResult(
            passed=False,
            mean_reward=0.0,
            delta=0.0,
            reward_threshold=reward_threshold,
            delta_threshold=delta_threshold,
            n_samples=0,
            reason="rewards 목록이 비어 있습니다.",
        )

    mean_reward = sum(rewards) / len(rewards)
    delta = mean_reward - baseline

    reward_ok = mean_reward >= reward_threshold
    delta_ok = delta >= delta_threshold
    passed = reward_ok and delta_ok

    fail_reasons: List[str] = []
    if not reward_ok:
        fail_reasons.append(
            f"mean_reward={mean_reward:.4f} < threshold={reward_threshold}"
        )
    if not delta_ok:
        fail_reasons.append(
            f"delta={delta:.4f} < threshold={delta_threshold}"
        )

    reason = "PASS" if passed else "; ".join(fail_reasons)

    return RLHFRewardGateResult(
        passed=passed,
        mean_reward=round(mean_reward, 6),
        delta=round(delta, 6),
        reward_threshold=reward_threshold,
        delta_threshold=delta_threshold,
        n_samples=len(rewards),
        reason=reason,
    )
