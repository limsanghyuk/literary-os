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
