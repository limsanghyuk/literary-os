"""
ppo_trainer.py — PPOTrainer v1.0 (V603, ADR-063)

SP-B.2 RLHF 루프 2단계:
RLHFDatasetBuilder가 생성한 (씬, 보상) JSONL을 입력받아
PPO(Proximal Policy Optimization) 기반 정책 업데이트를 수행한다.

LLM-0 원칙: 외부 LLM API 호출 없음.
학습 신호(reward)는 RewardModel에서, 데이터는 RLHFDatasetBuilder에서 공급.

Gate G55 (PPO Stability) 기준:
    - KL 발산 ≤ 0.08 (cycle 1)  /  ≤ 0.05 (최종 G55)
    - reward_improvement ≥ 0.0 (정체는 허용, 역행 불가)
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from literary_system.rlhf.rlhf_dataset_builder import DatasetEntry

__all__ = [
    "PPOConfig",
    "PPOStep",
    "PPOResult",
    "PPOTrainer",
    "KL_THRESHOLD_CYCLE1",
    "KL_THRESHOLD_FINAL",
]

# ──────────────────────────────────────────────────────────────────────────────
# 상수
# ──────────────────────────────────────────────────────────────────────────────

KL_THRESHOLD_CYCLE1: float = 0.08   # G55 cycle 1 허용 상한
KL_THRESHOLD_FINAL: float = 0.05    # G55 최종 허용 상한
CLIP_EPSILON: float = 0.20          # PPO clipping (표준 ε)
VALUE_COEF: float = 0.50            # value loss 계수
ENTROPY_COEF: float = 0.01         # entropy bonus 계수


# ──────────────────────────────────────────────────────────────────────────────
# 데이터클래스
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class PPOConfig:
    """PPOTrainer 설정."""
    kl_threshold: float = KL_THRESHOLD_CYCLE1
    clip_epsilon: float = CLIP_EPSILON
    value_coef: float = VALUE_COEF
    entropy_coef: float = ENTROPY_COEF
    max_steps: int = 100
    batch_size: int = 8
    learning_rate: float = 1e-4
    gamma: float = 0.99          # discount factor
    lam: float = 0.95            # GAE lambda
    seed: int = 42

    def __post_init__(self) -> None:
        if not 0.0 < self.kl_threshold <= 1.0:
            raise ValueError(f"kl_threshold must be in (0,1], got {self.kl_threshold}")
        if not 0.0 < self.clip_epsilon <= 1.0:
            raise ValueError(f"clip_epsilon must be in (0,1], got {self.clip_epsilon}")
        if self.max_steps < 1:
            raise ValueError(f"max_steps must be ≥1, got {self.max_steps}")
        if self.batch_size < 1:
            raise ValueError(f"batch_size must be ≥1, got {self.batch_size}")


@dataclass
class PPOStep:
    """단일 PPO 업데이트 스텝 결과."""
    step: int
    policy_loss: float
    value_loss: float
    entropy: float
    kl_divergence: float
    mean_reward: float
    clipped_ratio: float         # clipping 발생 비율
    kl_exceeded: bool = False    # KL 상한 초과 여부


@dataclass
class PPOResult:
    """PPOTrainer 전체 실행 결과."""
    steps: List[PPOStep] = field(default_factory=list)
    final_kl: float = 0.0
    mean_reward_before: float = 0.0
    mean_reward_after: float = 0.0
    reward_improvement: float = 0.0
    kl_stable: bool = False          # 최종 KL ≤ kl_threshold
    total_entries: int = 0
    config: Optional[PPOConfig] = None

    @property
    def passed(self) -> bool:
        """Gate G55 통과 여부: KL stable + reward 역행 없음."""
        return self.kl_stable and self.reward_improvement >= 0.0

    def summary(self) -> Dict:
        return {
            "total_steps": len(self.steps),
            "final_kl": round(self.final_kl, 6),
            "mean_reward_before": round(self.mean_reward_before, 4),
            "mean_reward_after": round(self.mean_reward_after, 4),
            "reward_improvement": round(self.reward_improvement, 4),
            "kl_stable": self.kl_stable,
            "passed": self.passed,
            "total_entries": self.total_entries,
        }


# ──────────────────────────────────────────────────────────────────────────────
# PPOTrainer
# ──────────────────────────────────────────────────────────────────────────────

class PPOTrainer:
    """
    PPOTrainer v1.0 — Constitution 보상 기반 정책 최적화기.

    LLM-0: 외부 LLM API 호출 없음.
    실제 모델 파라미터 없이 보상 신호만으로 업데이트 시뮬레이션.
    KL 발산을 추적하여 G55 안정성 기준을 충족하는지 검증.
    """

    def __init__(self, config: Optional[PPOConfig] = None) -> None:
        self._config = config or PPOConfig()
        self._rng_state = self._config.seed
        # 내부 정책 파라미터 (스칼라 공간에서 시뮬레이션)
        self._policy_mean: float = 0.0
        self._policy_log_std: float = 0.0
        self._value_estimate: float = 0.0

    # ── 퍼블릭 API ────────────────────────────────────────────────────────────

    def train(self, entries: Sequence[DatasetEntry]) -> PPOResult:
        """
        (씬, 보상) DatasetEntry 목록으로 PPO 학습을 수행한다.

        Args:
            entries: RLHFDatasetBuilder.load() 또는 build() 결과

        Returns:
            PPOResult (Gate G55 통과 여부 포함)
        """
        if not entries:
            return PPOResult(config=self._config)

        rewards = [e.reward for e in entries]
        result = PPOResult(
            mean_reward_before=statistics.mean(rewards),
            total_entries=len(entries),
            config=self._config,
        )

        cfg = self._config
        steps: List[PPOStep] = []

        for step_idx in range(cfg.max_steps):
            batch = self._sample_batch(entries, cfg.batch_size)
            ppo_step = self._ppo_update(step_idx, batch)
            steps.append(ppo_step)

            # ConstraintGuard 내장 KL 조기 종료
            if ppo_step.kl_divergence > cfg.kl_threshold * 2.0:
                # KL이 임계값의 2배를 초과하면 조기 종료 (안전장치)
                break

        result.steps = steps
        if steps:
            result.final_kl = steps[-1].kl_divergence
            result.mean_reward_after = steps[-1].mean_reward
        else:
            result.final_kl = 0.0
            result.mean_reward_after = result.mean_reward_before

        result.reward_improvement = result.mean_reward_after - result.mean_reward_before
        result.kl_stable = result.final_kl <= cfg.kl_threshold

        return result

    def train_from_jsonl(self, path: "str | Path") -> PPOResult:
        """JSONL 파일에서 직접 학습."""
        from literary_system.rlhf.rlhf_dataset_builder import RLHFDatasetBuilder
        builder = RLHFDatasetBuilder()
        entries = builder.load(Path(path))
        return self.train(entries)

    @property
    def config(self) -> PPOConfig:
        return self._config

    # ── 내부 메서드 ──────────────────────────────────────────────────────────

    def _lcg(self) -> float:
        """LCG 의사난수 생성기 (seed 기반, 재현 가능)."""
        self._rng_state = (1664525 * self._rng_state + 1013904223) & 0xFFFFFFFF
        return self._rng_state / 0xFFFFFFFF

    def _sample_batch(
        self, entries: Sequence[DatasetEntry], batch_size: int
    ) -> List[DatasetEntry]:
        """배치 무작위 샘플링 (LCG 기반, 재현 가능)."""
        n = len(entries)
        indices = [int(self._lcg() * n) % n for _ in range(min(batch_size, n))]
        return [entries[i] for i in indices]

    def _ppo_update(self, step: int, batch: List[DatasetEntry]) -> PPOStep:
        """단일 PPO 업데이트 스텝 시뮬레이션."""
        if not batch:
            return PPOStep(
                step=step, policy_loss=0.0, value_loss=0.0,
                entropy=0.0, kl_divergence=0.0, mean_reward=0.0, clipped_ratio=0.0,
            )

        rewards = [e.reward for e in batch]
        mean_r = statistics.mean(rewards)
        std_r = statistics.stdev(rewards) if len(rewards) > 1 else 1.0

        # 보상 정규화 (advantage 추정)
        advantages = [(r - mean_r) / (std_r + 1e-8) for r in rewards]

        # 정책 ratio 계산 (로그 정책 변화량으로 근사)
        lr = self._config.learning_rate
        policy_delta = lr * mean_r
        old_log_prob = self._policy_mean
        new_log_prob = old_log_prob + policy_delta

        ratios = [math.exp(min(new_log_prob - old_log_prob, 5.0)) for _ in batch]
        clip_eps = self._config.clip_epsilon

        # PPO clip 손실
        clipped_ratios = [
            max(min(r, 1.0 + clip_eps), 1.0 - clip_eps) for r in ratios
        ]
        surr1 = [r * a for r, a in zip(ratios, advantages)]
        surr2 = [cr * a for cr, a in zip(clipped_ratios, advantages)]
        policy_loss = -statistics.mean([min(s1, s2) for s1, s2 in zip(surr1, surr2)])

        # 가치 손실
        value_target = mean_r
        value_loss = (value_target - self._value_estimate) ** 2 * self._config.value_coef

        # 엔트로피 보너스 (탐험 유지)
        entropy = (
            0.5 * math.log(2 * math.pi * math.e)
            + abs(self._policy_log_std)
        ) * self._config.entropy_coef

        # KL 발산 — 스텝 누적 방식 (BUG-C2-2 수정 2026-05-23)
        # 이전 코드: kl = 0.5 * delta_mean**2 → lr=1e-4 시 kl≈10^-9 (threshold 미도달)
        # 수정: 이전 KL에 현재 스텝 delta를 누적하여 실제 threshold 도달 가능하게 함
        delta_mean = abs(new_log_prob - old_log_prob)
        kl = getattr(self, "_cumulative_kl", 0.0) + 0.5 * delta_mean ** 2
        self._cumulative_kl = kl

        # 정책 파라미터 업데이트
        total_loss = policy_loss + value_loss - entropy
        self._policy_mean = new_log_prob
        self._value_estimate += lr * (value_target - self._value_estimate)
        self._policy_log_std = max(self._policy_log_std - lr * 0.1, -2.0)

        # clipping 발생 비율
        clipped_count = sum(
            1 for r in ratios
            if r > 1.0 + clip_eps or r < 1.0 - clip_eps
        )
        clipped_ratio = clipped_count / len(ratios)

        return PPOStep(
            step=step,
            policy_loss=round(policy_loss, 6),
            value_loss=round(value_loss, 6),
            entropy=round(entropy, 6),
            kl_divergence=round(kl, 6),
            mean_reward=round(mean_r, 4),
            clipped_ratio=round(clipped_ratio, 4),
            kl_exceeded=kl > self._config.kl_threshold,
        )
