"""V387 — ExtendedPhysicsCoefficientStore. 14개 계수 전체 지원."""
from __future__ import annotations

from literary_system.physics.coefficient_store import PhysicsCoefficientStore


def _clamp(v: float, lo: float = 0.02, hi: float = 0.45) -> float:
    return max(lo, min(hi, v))


class ExtendedPhysicsCoefficientStore(PhysicsCoefficientStore):
    """
    V387: 6개 기본 계수 + 8개 확장 계수 = 14개 전체.
    V383/V385의 PhysicsCoefficientStore를 상속하여 하위 호환.
    """

    def __init__(self) -> None:
        super().__init__()
        # V387 추가 8개 계수
        self.leakage_penalty_weight:       float = 0.10
        self.branchpoint_survival_weight:  float = 0.08
        self.style_drift_penalty:          float = 0.05
        self.arc_escalation_bonus:         float = 0.07
        self.reveal_entropy_weight:        float = 0.06
        self.character_agency_weight:      float = 0.07
        self.temporal_coherence_weight:    float = 0.05
        self.motif_echo_weight:            float = 0.06

    def all_14_dict(self) -> dict:
        base = self.as_dict()
        ext = {
            'leakage_penalty_weight':      self.leakage_penalty_weight,
            'branchpoint_survival_weight': self.branchpoint_survival_weight,
            'style_drift_penalty':         self.style_drift_penalty,
            'arc_escalation_bonus':        self.arc_escalation_bonus,
            'reveal_entropy_weight':       self.reveal_entropy_weight,
            'character_agency_weight':     self.character_agency_weight,
            'temporal_coherence_weight':   self.temporal_coherence_weight,
            'motif_echo_weight':           self.motif_echo_weight,
        }
        return {**base, **ext}

    def update_extended(self, **kwargs: float) -> None:
        for name, value in kwargs.items():
            if hasattr(self, name):
                old = getattr(self, name)
                new = _clamp(value)
                setattr(self, name, new)
                self._ledger.record(name, old, new)
