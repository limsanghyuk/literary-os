"""V385 ManuscriptLearning Layer."""
from literary_system.learning.manuscript_learner import ManuscriptLearner
from literary_system.learning.physics_coefficient_updater import PhysicsCoefficientUpdater
from literary_system.learning.privacy_guard import PrivacyGuard, PrivacyViolationError
from literary_system.learning.scene_corpus_builder import SceneCorpusBuilder

from literary_system.learning.loop_c import (
    PreferencePair, load_preference_pairs, to_dpo_dataset, write_dpo_jsonl,
    generation_win_rate, reference_strength, LoopCReport, summarize,
)
from literary_system.learning.reward_model import (
    RewardScore, PairwiseRewardModel, reward_from_pairs, ensemble_reward_model,
)
from literary_system.learning.rlaif_orchestrator import (
    RLAIFTrainingSpec, RLAIFOrchestrator,
)
from literary_system.learning.rlaif_trigger import TriggerResult, RLAIFTrigger

from .phase_e_exit import run_phase_e_exit  # V766

from .provider_router import ProviderRouter, RoutingSignals, RoutingDecision, validate_routing  # V768

from .split_pipeline import SplitPipeline, SplitReport, StagePlan, run_split_poc  # V769

from .pareto_router import (ParetoRouter, ParetoCandidate, pareto_frontier, TrainingMode, dispatch_training)  # V770

from .first_training_kit import (build_training_plan, prepare_dpo, make_smoke_dataset, baseline_winrate, winrate_delta)  # V771

from .winrate_gate import g_loopc_winrate, WinrateGateResult  # V774
from .loopc_closure import LoopCClosure, LoopCRoundReport  # V774
