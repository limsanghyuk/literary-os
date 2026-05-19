"""
V324 - CoefficientMapper  (Phase 1)
LearnedCoefficients ↔ MAEWeights 양방향 매핑 + ChangeLedger.

설계 원칙 (P2 외과적 통합, P5 계수 추적성):
  - 정방향: LearnedCoefficients → MAEWeights
      alpha_logic   = clamp(decay_lambda * 10.0,      0.2, 0.9)
      beta_char     = clamp(residue_boost / 3.0,       0.2, 0.9)
      gamma_tension = clamp(arc_pressure_boost / 2.5,  0.2, 0.9)
  - 역방향: MAEWeights → LearnedCoefficients
      decay_lambda        = clamp(alpha_logic / 10.0,       0.001, 0.5)
      residue_boost       = clamp(beta_char * 3.0,           1.0,  3.0)
      arc_pressure_boost  = clamp(gamma_tension * 2.5,       1.0,  2.5)
  - 역방향 후 clamp_all() 강제 호출
  - ChangeLedger: 모든 계수 변경 이력 기록
  - to_json() / from_json_inplace() → SnapshotManager 연동
  - LLM 0회. 완전 로컬.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import List

from literary_system.validation.learned_coefficient_store import LearnedCoefficients

# ════════════════════════════════════════════════════════════════════
# MAEWeights DTO
# ════════════════════════════════════════════════════════════════════

_MAE_CLAMP = (0.2, 0.9)


def _clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


@dataclass
class MAEWeights:
    """
    MAEOrchestrator 3에이전트에 전달되는 가중치.

    안전 범위: [0.2, 0.9]
    """
    alpha_logic: float = 0.5
    beta_char: float = 0.5
    gamma_tension: float = 0.5

    def __post_init__(self) -> None:
        self.alpha_logic = _clamp(self.alpha_logic, *_MAE_CLAMP)
        self.beta_char = _clamp(self.beta_char, *_MAE_CLAMP)
        self.gamma_tension = _clamp(self.gamma_tension, *_MAE_CLAMP)

    def to_dict(self) -> dict:
        return {
            "alpha_logic": self.alpha_logic,
            "beta_char": self.beta_char,
            "gamma_tension": self.gamma_tension,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MAEWeights":
        return cls(
            alpha_logic=d.get("alpha_logic", 0.5),
            beta_char=d.get("beta_char", 0.5),
            gamma_tension=d.get("gamma_tension", 0.5),
        )


# ════════════════════════════════════════════════════════════════════
# ChangeLedgerEntry
# ════════════════════════════════════════════════════════════════════

@dataclass
class ChangeLedgerEntry:
    """단일 계수 변경 이력 레코드."""
    reason: str
    before_decay_lambda: float
    after_decay_lambda: float
    before_residue_boost: float
    after_residue_boost: float
    before_arc_pressure_boost: float
    after_arc_pressure_boost: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "reason": self.reason,
            "before_decay_lambda": self.before_decay_lambda,
            "after_decay_lambda": self.after_decay_lambda,
            "before_residue_boost": self.before_residue_boost,
            "after_residue_boost": self.after_residue_boost,
            "before_arc_pressure_boost": self.before_arc_pressure_boost,
            "after_arc_pressure_boost": self.after_arc_pressure_boost,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ChangeLedgerEntry":
        entry = cls.__new__(cls)
        entry.reason = d.get("reason", "")
        entry.before_decay_lambda = d.get("before_decay_lambda", 0.0)
        entry.after_decay_lambda = d.get("after_decay_lambda", 0.0)
        entry.before_residue_boost = d.get("before_residue_boost", 0.0)
        entry.after_residue_boost = d.get("after_residue_boost", 0.0)
        entry.before_arc_pressure_boost = d.get("before_arc_pressure_boost", 0.0)
        entry.after_arc_pressure_boost = d.get("after_arc_pressure_boost", 0.0)
        entry.timestamp = d.get("timestamp", time.time())
        return entry


# ════════════════════════════════════════════════════════════════════
# CoefficientMapper
# ════════════════════════════════════════════════════════════════════

class CoefficientMapper:
    """
    V323 LearnedCoefficients ↔ MAEWeights 양방향 매핑.
    모든 계수 변경을 ChangeLedger에 기록하여 추적성 확보.
    """

    def __init__(self) -> None:
        self._ledger: List[ChangeLedgerEntry] = []

    # ── 정방향 매핑 ─────────────────────────────────────────────────

    def map_to_mae(self, coeff: LearnedCoefficients) -> MAEWeights:
        """LearnedCoefficients → MAEWeights."""
        alpha = _clamp(coeff.decay_lambda * 10.0, *_MAE_CLAMP)
        beta = _clamp(coeff.residue_boost / 3.0, *_MAE_CLAMP)
        gamma = _clamp(coeff.arc_pressure_boost / 2.5, *_MAE_CLAMP)
        return MAEWeights(alpha_logic=alpha, beta_char=beta, gamma_tension=gamma)

    # ── 역방향 매핑 ─────────────────────────────────────────────────

    def map_from_mae(self, mae_weights: MAEWeights) -> LearnedCoefficients:
        """MAEWeights → LearnedCoefficients. 역방향 후 clamp_all() 강제."""
        dl_ranges = LearnedCoefficients.CLAMP_RANGES
        decay_lambda = _clamp(
            mae_weights.alpha_logic / 10.0,
            dl_ranges["decay_lambda"][0],
            dl_ranges["decay_lambda"][1],
        )
        residue_boost = _clamp(
            mae_weights.beta_char * 3.0,
            dl_ranges["residue_boost"][0],
            dl_ranges["residue_boost"][1],
        )
        arc_pressure_boost = _clamp(
            mae_weights.gamma_tension * 2.5,
            dl_ranges["arc_pressure_boost"][0],
            dl_ranges["arc_pressure_boost"][1],
        )
        c = LearnedCoefficients(
            decay_lambda=decay_lambda,
            residue_boost=residue_boost,
            arc_pressure_boost=arc_pressure_boost,
        )
        c.clamp_all()  # 안전망 이중 적용
        return c

    # ── ChangeLedger ─────────────────────────────────────────────────

    def record_change(
        self,
        before: LearnedCoefficients,
        after: LearnedCoefficients,
        reason: str,
    ) -> None:
        """계수 변경 이력 기록."""
        entry = ChangeLedgerEntry(
            reason=reason,
            before_decay_lambda=before.decay_lambda,
            after_decay_lambda=after.decay_lambda,
            before_residue_boost=before.residue_boost,
            after_residue_boost=after.residue_boost,
            before_arc_pressure_boost=before.arc_pressure_boost,
            after_arc_pressure_boost=after.arc_pressure_boost,
        )
        self._ledger.append(entry)

    def get_ledger(self) -> List[ChangeLedgerEntry]:
        """ChangeLedger 복사본 반환."""
        return list(self._ledger)

    # ── JSON 직렬화 (SnapshotManager 연동) ───────────────────────────

    def to_json(self) -> str:
        data = {"ledger": [e.to_dict() for e in self._ledger]}
        return json.dumps(data, ensure_ascii=False)

    def from_json_inplace(self, json_str: str) -> None:
        data = json.loads(json_str)
        self._ledger = [
            ChangeLedgerEntry.from_dict(d) for d in data.get("ledger", [])
        ]
