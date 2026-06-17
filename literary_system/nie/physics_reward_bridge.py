"""
V498 - PhysicsRewardBridge
ADR-015: MAEOrchestrator -> R(scene) -> PhysicsCoefficientUpdater 배선.

설계 원칙 (ADR-006 격리 범위):
  - LLM 호출 금지 (LLM-0).
  - Policy Gradient Lite: advantage = R - R_baseline
  - R_baseline: EMA (decay=0.95, init=0.50)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from literary_system.evaluation.mae_orchestrator import MAEOrchestrator, MAEResult
from literary_system.evaluation.scene_metrics_collector import SceneMetrics
from literary_system.learning.physics_coefficient_updater import PhysicsCoefficientUpdater
from literary_system.physics.coefficient_store import PhysicsCoefficientStore
from literary_system.physics.scene_feature_extractor import SceneFeature

logger = logging.getLogger(__name__)


def _compute_reward(mae_result: MAEResult) -> float:
    """MAEResult -> R(scene) in [0.0, 1.0]."""
    total = max(len(mae_result.votes), 1)
    base = mae_result.pass_count / total
    bonus = 0.1 if mae_result.consensus else 0.0
    return min(base + bonus, 1.0)


@dataclass
class BridgeResult_Nie:
    scene_id: str
    reward: float
    advantage: float
    baseline: float
    coefficients_updated: bool
    delta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "scene_id": self.scene_id,
            "reward": round(self.reward, 4),
            "advantage": round(self.advantage, 4),
            "baseline": round(self.baseline, 4),
            "coefficients_updated": self.coefficients_updated,
            "delta": {k: round(v, 6) for k, v in self.delta.items()},
        }


class PhysicsRewardBridge:
    """
    NIL Step 5 - MAE 평가 결과를 물리 계수 업데이트로 변환.
    ADR-015: LLM-0 원칙 준수. R_baseline EMA.
    NILStabilityModule 연동 (V512+, optional).
    """

    LR_PHYSICS: float = 0.01
    BASELINE_DECAY: float = 0.95
    BASELINE_INIT: float = 0.50

    def __init__(
        self,
        mae_orchestrator: MAEOrchestrator,
        coefficient_updater: PhysicsCoefficientUpdater,
        coefficient_store: PhysicsCoefficientStore,
        stability_module=None,
    ) -> None:
        self._mae = mae_orchestrator
        self._updater = coefficient_updater
        self._store = coefficient_store
        self._stability = stability_module
        self._baseline: float = self.BASELINE_INIT
        self._history: List[BridgeResult] = []

    def process(
        self,
        scene_id: str,
        metrics: SceneMetrics,
        feature: Optional[SceneFeature] = None,
    ) -> BridgeResult:
        mae_result: MAEResult = self._mae.evaluate(scene_id, metrics)
        reward = _compute_reward(mae_result)
        advantage = reward - self._baseline
        self._baseline = (
            self.BASELINE_DECAY * self._baseline
            + (1.0 - self.BASELINE_DECAY) * reward
        )
        effective_lr = self.LR_PHYSICS
        if self._stability is not None:
            effective_lr = self._stability.get_effective_lr("physics", self.LR_PHYSICS)

        delta: dict = {}
        updated = False
        if feature is not None:
            old_coeff = self._store.as_dict().copy()
            self._updater.LR = effective_lr
            self._updater.update_one_epoch([feature])
            new_coeff = self._store.as_dict()
            delta = {
                k: new_coeff[k] - old_coeff[k]
                for k in new_coeff
                if abs(new_coeff[k] - old_coeff.get(k, 0.0)) > 1e-8
            }
            updated = True

        result = BridgeResult(
            scene_id=scene_id,
            reward=reward,
            advantage=advantage,
            baseline=self._baseline,
            coefficients_updated=updated,
            delta=delta,
        )
        self._history.append(result)
        return result

    def process_batch(self, scenes: List[dict]) -> List[BridgeResult]:
        return [
            self.process(
                scene_id=s["scene_id"],
                metrics=s["metrics"],
                feature=s.get("feature"),
            )
            for s in scenes
        ]

    def get_history(self) -> List[BridgeResult]:
        return list(self._history)

    def get_baseline(self) -> float:
        return self._baseline

    def reset_baseline(self) -> None:
        self._baseline = self.BASELINE_INIT
        self._history.clear()


# G37 DuplicateZero(ADR-033): 클래스명 전역 고유화 — 외부 import 하위호환 별칭
BridgeResult = BridgeResult_Nie
