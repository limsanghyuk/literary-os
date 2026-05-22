"""
literary_system/rlhf — RLHF (Reinforcement Learning from Human Feedback) 패키지

SP-B.2 (V601~V610):
- V601: RewardModel (Constitution 5축 → 스칼라 보상)
- V602: RLHFDatasetBuilder ((씬, 보상) 쌍 JSONL)
- V603: PPOTrainer + ConstraintGuard (KL 안정화 + Gate G55)
- V604: RLHFMonitor (보상 추세 + 자동 롤백)
- V605: CanaryController + ModelServingEndpoint (A/B 테스트)
- V610: RLHFGate (G56) + ConstitutionGate (G57)

LLM-0 원칙: 외부 LLM API 직접 호출 없음.
LLM-1 원칙: PROMOTED 아티팩트만 추론에 사용.
ADR-061~064 참조.
"""
from __future__ import annotations

__all__ = [
    # V601
    "RewardModel",
    "RewardResult",
    "ConstitutionAxisReward",
    "AdversarialSeed",
    # V602
    "RLHFDatasetBuilder",
    "DatasetEntry",
    "RLHFDatasetStats",
    "BuildResult",
    # V603
    "PPOTrainer",
    "PPOConfig",
    "PPOResult",
    "PPOStep",
    "ConstraintGuard",
    "GuardConfig",
    "GuardState",
    "ConstraintViolationRecord",
    # V604
    "RLHFMonitor",
    "MonitorConfig",
    "MonitorState",
    "RewardSnapshot",
    "RollbackRecord",
]

from literary_system.rlhf.constraint_guard import (
    ConstraintGuard,
    ConstraintViolationRecord,
    GuardConfig,
    GuardState,
)
from literary_system.rlhf.ppo_trainer import (
    PPOConfig,
    PPOResult,
    PPOStep,
    PPOTrainer,
)
from literary_system.rlhf.reward_model import (
    AdversarialSeed,
    ConstitutionAxisReward,
    RewardModel,
    RewardResult,
)
from literary_system.rlhf.rlhf_dataset_builder import (  # noqa: E402
    BuildResult,
    DatasetEntry,
    RLHFDatasetBuilder,
    RLHFDatasetStats,
)
from literary_system.rlhf.rlhf_monitor import (
    MonitorConfig,
    MonitorState,
    RewardSnapshot,
    RLHFMonitor,
    RollbackRecord,
)
