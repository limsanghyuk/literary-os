"""
test_v603_ppo_trainer.py — V603 PPOTrainer + ConstraintGuard 단위 테스트 (9 TC)

ADR-063 체크포인트 기반.
"""
from __future__ import annotations

import math
import pytest

from literary_system.rlhf.ppo_trainer import (
    CLIP_EPSILON,
    KL_THRESHOLD_CYCLE1,
    KL_THRESHOLD_FINAL,
    PPOConfig,
    PPOResult,
    PPOStep,
    PPOTrainer,
)
from literary_system.rlhf.constraint_guard import (
    ConstraintGuard,
    GuardConfig,
    ConstraintViolationRecord,
)
from literary_system.rlhf.rlhf_dataset_builder import DatasetEntry


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------
def _make_entries(n: int = 12, reward: float = 0.70) -> list[DatasetEntry]:
    return [
        DatasetEntry(
            entry_id=f"e{i}",
            scene=f"씬 텍스트 {i} " * 5,
            reward=reward + i * 0.005,
            passed=True,
            axis_rewards={
                "coherence": 0.80,
                "style": 0.75,
                "ethics": 0.90,
                "engagement": 0.70,
                "originality": 0.75,
            },
            model_target="8B",
            split="train",
        )
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# TC-1: PPOConfig 기본값 유효성
# ---------------------------------------------------------------------------
def test_tc1_ppo_config_defaults():
    cfg = PPOConfig()
    assert 0 < cfg.kl_threshold <= 0.10, "kl_threshold 범위 초과"
    assert 0 < cfg.clip_epsilon < 1.0, "clip_epsilon 범위 초과"
    assert cfg.kl_threshold == KL_THRESHOLD_CYCLE1
    assert cfg.clip_epsilon == CLIP_EPSILON
    assert cfg.max_steps > 0
    assert cfg.batch_size > 0


# ---------------------------------------------------------------------------
# TC-2: PPOConfig 검증 — 잘못된 값 예외
# ---------------------------------------------------------------------------
def test_tc2_ppo_config_validation():
    with pytest.raises(ValueError):
        PPOConfig(kl_threshold=-0.01)
    with pytest.raises(ValueError):
        PPOConfig(clip_epsilon=0.0)
    with pytest.raises(ValueError):
        PPOConfig(clip_epsilon=1.5)
    with pytest.raises(ValueError):
        PPOConfig(batch_size=0)


# ---------------------------------------------------------------------------
# TC-3: PPOTrainer.train() 반환 타입 및 기본 구조
# ---------------------------------------------------------------------------
def test_tc3_ppo_train_returns_ppo_result():
    entries = _make_entries(12)
    trainer = PPOTrainer()
    result = trainer.train(entries)
    assert isinstance(result, PPOResult)
    assert isinstance(result.steps, list)
    assert result.total_entries == 12
    assert result.config is not None
    assert math.isfinite(result.final_kl)
    assert math.isfinite(result.mean_reward_before)
    assert math.isfinite(result.mean_reward_after)


# ---------------------------------------------------------------------------
# TC-4: PPOResult.passed 의미론
# ---------------------------------------------------------------------------
def test_tc4_ppo_result_passed_semantics():
    step = PPOStep(
        step=0, policy_loss=0.1, value_loss=0.05,
        entropy=0.5, kl_divergence=0.03,
        mean_reward=0.75, clipped_ratio=0.02,
    )
    # PASS 케이스
    r_pass = PPOResult(
        steps=[step], final_kl=0.03,
        mean_reward_before=0.60, mean_reward_after=0.75,
        reward_improvement=0.15, kl_stable=True,
        total_entries=10, config=None,
    )
    assert r_pass.passed is True

    # kl_stable=False
    r_kl = PPOResult(
        steps=[step], final_kl=0.20,
        mean_reward_before=0.60, mean_reward_after=0.75,
        reward_improvement=0.15, kl_stable=False,
        total_entries=10, config=None,
    )
    assert r_kl.passed is False

    # reward_improvement < 0
    r_neg = PPOResult(
        steps=[step], final_kl=0.03,
        mean_reward_before=0.60, mean_reward_after=0.55,
        reward_improvement=-0.05, kl_stable=True,
        total_entries=10, config=None,
    )
    assert r_neg.passed is False


# ---------------------------------------------------------------------------
# TC-5: PPOResult.summary() 필수 7키
# ---------------------------------------------------------------------------
def test_tc5_ppo_result_summary_keys():
    step = PPOStep(
        step=0, policy_loss=0.1, value_loss=0.05,
        entropy=0.5, kl_divergence=0.03,
        mean_reward=0.75, clipped_ratio=0.02,
    )
    r = PPOResult(
        steps=[step], final_kl=0.03,
        mean_reward_before=0.60, mean_reward_after=0.75,
        reward_improvement=0.15, kl_stable=True,
        total_entries=10, config=None,
    )
    summary = r.summary()
    required = {"final_kl", "mean_reward_before", "mean_reward_after",
                "reward_improvement", "kl_stable", "total_entries", "passed"}
    assert required <= set(summary.keys()), f"누락 키: {required - set(summary.keys())}"


# ---------------------------------------------------------------------------
# TC-6: ConstraintGuard — KL 하드 리밋 3연속 → should_stop
# ---------------------------------------------------------------------------
def test_tc6_constraint_guard_kl_hard_limit():
    guard = ConstraintGuard(GuardConfig(kl_hard_limit=0.10, max_consecutive_violations=3))
    for i in range(3):
        guard.check_kl(i, 0.20)  # 초과값
    assert guard.state.should_stop is True
    assert guard.state.consecutive_kl_violations >= 3
    assert guard.is_safe() is False


# ---------------------------------------------------------------------------
# TC-7: ConstraintGuard — KL 리셋 (안전한 값 후 카운터 초기화)
# ---------------------------------------------------------------------------
def test_tc7_constraint_guard_kl_reset():
    guard = ConstraintGuard(GuardConfig(kl_hard_limit=0.10, max_consecutive_violations=3))
    guard.check_kl(0, 0.20)  # 초과 1
    guard.check_kl(1, 0.05)  # 정상 → 리셋
    guard.check_kl(2, 0.20)  # 초과 1 (카운터 재시작)
    assert guard.state.should_stop is False  # 아직 연속 3회 미달
    assert guard.state.consecutive_kl_violations == 1


# ---------------------------------------------------------------------------
# TC-8: ConstraintGuard.clamp_reward() 범위 정확성
# ---------------------------------------------------------------------------
def test_tc8_constraint_guard_clamp_reward():
    guard = ConstraintGuard(GuardConfig(reward_min=-5.0, reward_max=5.0))
    assert guard.clamp_reward(0, 15.0) == 5.0
    assert guard.clamp_reward(1, -20.0) == -5.0
    assert guard.clamp_reward(2, 3.0) == 3.0    # 클램프 없음
    assert guard.state.total_reward_clamps == 2


# ---------------------------------------------------------------------------
# TC-9: PPOTrainer.train_from_jsonl() — 빈 JSONL 경로 예외 처리
# ---------------------------------------------------------------------------
def test_tc9_ppo_train_from_jsonl_missing_file():
    trainer = PPOTrainer()
    with pytest.raises((FileNotFoundError, OSError)):
        trainer.train_from_jsonl("/nonexistent/path/data.jsonl")
