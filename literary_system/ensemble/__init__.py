"""
literary_system.ensemble — V389 ProviderEnsemble + V646~V655 agents/ re-export.
Step-2 facade migration: 기존 legacy alias 유지 + 신규 agents/* lazy re-export.
순환 임포트 방지: agents/* 및 coordinator/cache 는 __getattr__ 지연 로드 사용.
"""
# ---- legacy alias (즉시 로드, 순환 임포트 없음) ----------------------
from literary_system.ensemble.gate8_ensemble import EnsembleGate, EnsembleGateFailure
from literary_system.ensemble.narrative_fitness_arbiter import (
    CandidateScore,
    EnsembleDecision,
    EnsembleDecisionType,
    NarrativeFitnessArbiter,
)

# ---- 지연 로드 매핑 (agents/* + coordinator + cache) ------------------
_AGENT_EXPORTS = {
    # V646~V649 agents
    "DirectorAgent":         ("literary_system.agents.director_agent",      "DirectorAgent"),
    "SceneBlueprint":        ("literary_system.agents.director_agent",      "SceneBlueprint"),
    "ScriptAgent":           ("literary_system.agents.script_agent",        "ScriptAgent"),
    "ScriptDraft":           ("literary_system.agents.script_agent",        "ScriptDraft"),
    "CriticAgent":           ("literary_system.agents.critic_agent",        "CriticAgent"),
    "CriticReport":          ("literary_system.agents.critic_agent",        "CriticReport"),
    "EditorAgent":           ("literary_system.agents.editor_agent",        "EditorAgent"),
    "EditedScene":           ("literary_system.agents.editor_agent",        "EditedScene"),
    # V650 coordinator
    "AgentCoordinator":      ("literary_system.ensemble.agent_coordinator", "AgentCoordinator"),
    "CoordinatorResult":     ("literary_system.ensemble.agent_coordinator", "CoordinatorResult"),
    # V651 cache
    "EnsembleMemoryCache":   ("literary_system.ensemble.memory_cache",      "EnsembleMemoryCache"),
    "EnsembleCacheEntry":     ("literary_system.ensemble.memory_cache",  "EnsembleCacheEntry"),
    "EnsembleCacheStats":     ("literary_system.ensemble.memory_cache",  "EnsembleCacheStats"),
    # V652 evaluator
    "AgentEnsembleEvaluator": ("literary_system.ensemble.ensemble_evaluator", "AgentEnsembleEvaluator"),
    "EnsembleEvalResult":     ("literary_system.ensemble.ensemble_evaluator", "EnsembleEvalResult"),
    # V653 safety guard
    "AgentSafetyGuard":      ("literary_system.ensemble.safety_guard",     "AgentSafetyGuard"),
    "AgentSafetyCheckResult": ("literary_system.ensemble.safety_guard",    "AgentSafetyCheckResult"),
    # V654 MAE-MultiWork G66
    "MAEMultiWorkGate":       ("literary_system.ensemble.mae_multiwork_gate", "MAEMultiWorkGate"),
    "ProjectRunSpec":         ("literary_system.ensemble.mae_multiwork_gate", "ProjectRunSpec"),
    "ProjectRunResult":       ("literary_system.ensemble.mae_multiwork_gate", "ProjectRunResult"),
    "MultiWorkGateResult":    ("literary_system.ensemble.mae_multiwork_gate", "MultiWorkGateResult"),
    # V655 Suite Registration G67
    "SuiteRegistrationGate":   ("literary_system.ensemble.suite_registration_gate", "SuiteRegistrationGate"),
    "SuiteRegistrationResult": ("literary_system.ensemble.suite_registration_gate", "SuiteRegistrationResult"),
    "ModelCardMetadata":       ("literary_system.ensemble.suite_registration_gate", "ModelCardMetadata"),
}


def __getattr__(name: str):
    if name in _AGENT_EXPORTS:
        module_path, attr = _AGENT_EXPORTS[name]
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f"module 'literary_system.ensemble' has no attribute {name!r}")


__all__ = [
    # legacy
    "EnsembleGate", "EnsembleGateFailure",
    "CandidateScore", "EnsembleDecision", "EnsembleDecisionType", "NarrativeFitnessArbiter",
    # agents V646~V649 (lazy)
    "DirectorAgent", "SceneBlueprint",
    "ScriptAgent",   "ScriptDraft",
    "CriticAgent",   "CriticReport",
    "EditorAgent",   "EditedScene",
    # coordinator V650 (lazy)
    "AgentCoordinator", "CoordinatorResult",
    # cache V651 (lazy)
    "EnsembleMemoryCache", "EnsembleCacheEntry", "EnsembleCacheStats",
    # evaluator V652 (lazy)
    "AgentEnsembleEvaluator", "EnsembleEvalResult",
    # safety guard V653 (lazy)
    "AgentSafetyGuard", "AgentSafetyCheckResult",
    # MAE-MultiWork G66 V654 (lazy)
    "MAEMultiWorkGate", "ProjectRunSpec", "ProjectRunResult", "MultiWorkGateResult",
    # Suite Registration G67 V655 (lazy)
    "SuiteRegistrationGate", "SuiteRegistrationResult", "ModelCardMetadata",
]
