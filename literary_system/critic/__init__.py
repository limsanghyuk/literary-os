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

from literary_system.critic.alignment_monitor import (
    AlignmentReport, measure_alignment, ALIGNMENT_MIN,
)
__all__ += ["AlignmentReport", "measure_alignment", "ALIGNMENT_MIN"]

from literary_system.critic.corpus_gate import CorpusGate, MIN_CORPUS_WORKS
from literary_system.critic.llm1_metrics import LLM1Metrics, COST_HARD_USD, COST_SOFT_USD
__all__ += ["CorpusGate", "MIN_CORPUS_WORKS", "LLM1Metrics", "COST_HARD_USD", "COST_SOFT_USD"]

from literary_system.critic.arbitration import (
    DisagreementRecord, classify, formula_winner, arbitrate,
)
__all__ += ["DisagreementRecord", "classify", "formula_winner", "arbitrate"]

from literary_system.critic.spe2_exit import run_spe2_exit
__all__ += ["run_spe2_exit"]

from literary_system.critic.critic_qualification import (qualify_critic, QualificationResult, degrade, build_ladder, DegradeAxis, WIN_MIN)  # V782 M1

from literary_system.critic.next_episode_bench import (run_next_episode_bench, NextEpItem, BenchResult, ngram_overlap, to_preference_pairs as nextep_pairs)  # V783 M2

from literary_system.critic.distribution_guard import (distribution_guard, GuardResult, compute_stats, apply_guard_to_reward, NORMAL_BANDS)  # V784 M3

from literary_system.critic.self_eval_pipeline import (SelfEvalPipeline, SelfEvalReport)  # V785

from literary_system.critic.distribution_guard import (distribution_guard_features, CORPUS_FEATURE_BANDS)  # V787
