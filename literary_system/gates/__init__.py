from .endurance_gate import EnduranceGate, GateResult

__all__ = ["EnduranceGate", "GateResult"]

# SelfLearningGate (V645, ADR-105)
from literary_system.gates.self_learning_gate import (  # noqa: E402
    SelfLearningGate,
    SelfLearningGateReport,
    SLGAxisResult,
    _kl_divergence_from_uniform,
    run_g63_gate,
    KL_MAX,
    ALPHA_MIN,
    CONTAMINATION_MAX,
    N_CONSTITUTION_AXES,
)
