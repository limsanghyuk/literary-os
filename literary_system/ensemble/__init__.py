"""V646 SP-C.2 — ensemble/ facade 재구성 (4-step 마이그레이션 Step 2).

신규 agents/* re-export + 기존 legacy alias 양립.
V680까지 하위 호환 유지 (ADR-106).
"""
# ── 신규 agents/* re-export ─────────────────────────────────────────────────
from literary_system.agents.director_agent import DirectorAgent, SceneBlueprint

# ── 기존 legacy alias 유지 (V389 이래 사용 중) ─────────────────────────────
from literary_system.ensemble.gate8_ensemble import EnsembleGate, EnsembleGateFailure
from literary_system.ensemble.narrative_fitness_arbiter import (
    CandidateScore,
    EnsembleDecision,
    EnsembleDecisionType,
    NarrativeFitnessArbiter,
)

__all__ = [
    # 신규
    "DirectorAgent",
    "SceneBlueprint",
    # legacy
    "EnsembleGate",
    "EnsembleGateFailure",
    "CandidateScore",
    "EnsembleDecision",
    "EnsembleDecisionType",
    "NarrativeFitnessArbiter",
]
