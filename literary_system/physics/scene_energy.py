"""
V383 — SceneEnergyConservationAudit
씬 에너지 입출력 보존 검증. 손실률 > 30% 시 SceneEnergyViolation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class SceneEnergyViolation:
    scene_id:   str
    loss_ratio: float
    message:    str


@dataclass
class EnergyAuditResult:
    energy_input:  float
    energy_output: float
    energy_ratio:  float          # 1 - loss_ratio (보존율)
    loss_ratio:    float
    violation:     Optional[SceneEnergyViolation] = None


_LOSS_THRESHOLD = 0.30  # 30% 초과 손실 시 위반


class SceneEnergyConservationAudit:
    """씬 에너지 보존 감사. 에너지는 arc_tension + conflict + reveal로 입력, reader_pull + emotion으로 출력."""

    def __init__(self, loss_threshold: float = _LOSS_THRESHOLD):
        self._threshold = loss_threshold

    def audit(
        self,
        energy_input:  float,
        energy_output: float,
        scene_id:      str = "unknown",
    ) -> EnergyAuditResult:
        if energy_input <= 0.0:
            # 입력 0 → 에너지 없음 → 비율 0
            return EnergyAuditResult(
                energy_input  = energy_input,
                energy_output = energy_output,
                energy_ratio  = 0.0,
                loss_ratio    = 0.0,
                violation     = None,
            )

        loss_ratio  = (energy_input - energy_output) / energy_input
        energy_ratio = max(0.0, 1.0 - loss_ratio)  # 보존율

        violation = None
        if loss_ratio > self._threshold:
            violation = SceneEnergyViolation(
                scene_id   = scene_id,
                loss_ratio = loss_ratio,
                message    = (
                    f"Scene '{scene_id}' energy loss {loss_ratio:.1%} "
                    f"exceeds threshold {self._threshold:.0%}."
                ),
            )

        return EnergyAuditResult(
            energy_input  = energy_input,
            energy_output = energy_output,
            energy_ratio  = energy_ratio,
            loss_ratio    = loss_ratio,
            violation     = violation,
        )
