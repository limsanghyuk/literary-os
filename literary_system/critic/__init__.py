"""literary_system.critic — LLM-1 Critic 레이어 (Phase E.2, V753~).

외부 LLM은 이 패키지에서만 평가 보조로 허용된다(G_LLM1_BOUNDARY).
corpus/·constitution/·finetune/ 은 LLM-0 유지(외부 LLM 절대 금지).
"""
from literary_system.critic.base import (
    CriticAxis, AXIS_DESC, CriticContext, CriticVerdict, CriticInterface, MockCritic, aggregate_verdicts,
)
__all__ = ["CriticAxis", "AXIS_DESC", "CriticContext", "CriticVerdict",
           "CriticInterface", "MockCritic", "aggregate_verdicts"]

from literary_system.critic.llm_critics import (
    LLMCritic, StructureCritic, CharacterCritic, DialogueCritic,
    EmotionCritic, GenreCritic, ALL_CRITICS, make_ensemble, evaluate_all_axes,
)
__all__ += ["LLMCritic", "StructureCritic", "CharacterCritic", "DialogueCritic",
            "EmotionCritic", "GenreCritic", "ALL_CRITICS", "make_ensemble", "evaluate_all_axes"]

from literary_system.critic.ensemble import CriticEnsemble, EnsembleResult
__all__ += ["CriticEnsemble", "EnsembleResult"]
