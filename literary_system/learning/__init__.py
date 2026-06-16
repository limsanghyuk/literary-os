"""V385 ManuscriptLearning Layer."""
from literary_system.learning.manuscript_learner import ManuscriptLearner
from literary_system.learning.physics_coefficient_updater import PhysicsCoefficientUpdater
from literary_system.learning.privacy_guard import PrivacyGuard, PrivacyViolationError
from literary_system.learning.scene_corpus_builder import SceneCorpusBuilder

from literary_system.learning.loop_c import (
    PreferencePair, load_preference_pairs, to_dpo_dataset, write_dpo_jsonl,
    generation_win_rate, reference_strength, LoopCReport, summarize,
)
