"""
literary_system/constitution — SP-A.7 (V594) LOSConstitution v1.0
                              + SP-C.1 (V631) LOSConstitution v2.0 Bayesian Weight Optimiser

Han-dramaturgy 5-축 장면 품질 헌법.
ADR-054 (v1.0) / ADR-098 (v2.0) 참조.
LLM-0 준수: 외부 LLM 호출 없음.
"""
from literary_system.constitution.los_constitution import (
    ConstitutionSceneScore,
    ConstitutionWeights,
    ConstitutionWorkScore,
    LOSConstitution,
)
from literary_system.constitution.los_constitution_v2 import (
    LOSConstitutionV2,
    OptimisationResult,
    entropy_constraint_pass,
)

__all__ = [
    # v1.0
    "ConstitutionWeights",
    "LOSConstitution",
    "ConstitutionSceneScore",
    "ConstitutionWorkScore",
    # v2.0 (SP-C.1, ADR-098)
    "LOSConstitutionV2",
    "OptimisationResult",
    "entropy_constraint_pass",
]
