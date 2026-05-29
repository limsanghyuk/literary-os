"""V383 — PhysicsCoefficientStore. NarrativePhysics 전용 계수 저장소."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


def _clamp(v: float, lo: float = 0.05, hi: float = 0.45) -> float:
    return max(lo, min(hi, v))


@dataclass
class PhysicsChangeLedger:
    entries: List[Dict] = field(default_factory=list)
    def record(self, name: str, old: float, new: float) -> None:
        self.entries.append({"coeff": name, "old": old, "new": new})


class PhysicsCoefficientStore:
    """
    6개 초기 계수. V385 ManuscriptLearning 이후 학습 기반 값으로 대체.
    update_interval=100 (LearnedCoefficientStore와 동일 주기 공유).
    """
    UPDATE_INTERVAL = 100

    def __init__(self) -> None:
        self.conflict_weight:       float = 0.20
        self.scene_energy_weight:   float = 0.15
        self.motif_weight:          float = 0.15
        self.curiosity_weight:      float = 0.20
        self.arc_pressure_coupling: float = 0.12
        self.prose_physics_bridge:  float = 0.18
        self._ledger   = PhysicsChangeLedger()
        self._episode_count = 0

    # ── 계수 접근 ─────────────────────────────────────────────
    def as_dict(self) -> Dict[str, float]:
        return {
            "conflict_weight":       self.conflict_weight,
            "scene_energy_weight":   self.scene_energy_weight,
            "motif_weight":          self.motif_weight,
            "curiosity_weight":      self.curiosity_weight,
            "arc_pressure_coupling": self.arc_pressure_coupling,
            "prose_physics_bridge":  self.prose_physics_bridge,
        }

    def weight_sum(self) -> float:
        return sum(self.as_dict().values())

    # ── 업데이트 ──────────────────────────────────────────────
    def update(self, **kwargs: float) -> None:
        """계수 업데이트. clamp [0.05, 0.45] 적용."""
        for name, value in kwargs.items():
            if hasattr(self, name):
                old = getattr(self, name)
                new = _clamp(value)
                setattr(self, name, new)
                self._ledger.record(name, old, new)

    def tick_episode(self) -> bool:
        """에피소드 1회 진행. update_interval 도달 시 True 반환."""
        self._episode_count += 1
        return (self._episode_count % self.UPDATE_INTERVAL) == 0

    @property
    def ledger(self) -> PhysicsChangeLedger:
        return self._ledger
