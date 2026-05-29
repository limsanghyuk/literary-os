"""
literary_system/constitution — SP-A.7 (V594) LOSConstitution v1.0
                              + SP-C.1 (V631) LOSConstitution v2.0 Bayesian Weight Optimiser
                              + SP-C.1 (V632) ConstitutionWeightTracker LOSDB 영속화 + 롤백
                              + SP-C.1 (V633) PatternLibraryV2 압축+랭킹
                              + SP-C.1 (V634) RetrainingScheduler F1 drift 기반 재학습
                              + SP-C.1 (V635) AutoPromotionGate G62 자동 승격
                              + SP-C.1 (V636) SelfLearningMonitor 파이프라인 모니터
                              + SP-C.1 (V638) ContaminationDetector 훈련 데이터 오염 탐지

Han-dramaturgy 5-축 장면 품질 헌법.
ADR-054 (v1.0) / ADR-098 (v2.0) / ADR-099 (WeightTracker) / ADR-075 (PatternLibraryV2)
ADR-076 (RetrainingScheduler) 참조.
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
from literary_system.constitution.constitution_weight_tracker import (
    ConstitutionWeightTracker,
    WeightRecord,
)
from literary_system.constitution.pattern_library_v2 import (
    PatternEntry,
    PatternLibraryV2,
)
from literary_system.constitution.retraining_scheduler import (
    RetrainingScheduler,
    ScheduleRecord,
    DRIFT_THRESHOLD,
    MIN_INTERVAL_DAYS,
)

__all__ = [
    # v1.0 (ADR-054)
    "ConstitutionWeights",
    "LOSConstitution",
    "ConstitutionSceneScore",
    "ConstitutionWorkScore",
    # v2.0 (SP-C.1, ADR-098)
    "LOSConstitutionV2",
    "OptimisationResult",
    "entropy_constraint_pass",
    # WeightTracker (SP-C.1, ADR-099)
    "ConstitutionWeightTracker",
    "WeightRecord",
    # PatternLibraryV2 (SP-C.1, ADR-075)
    "PatternEntry",
    "PatternLibraryV2",
    # RetrainingScheduler (SP-C.1, ADR-076)
    "RetrainingScheduler",
    "ScheduleRecord",
    "DRIFT_THRESHOLD",
    "MIN_INTERVAL_DAYS",
]

# AutoPromotionGate (SP-C.1, ADR-077) — gates/ 모듈이지만 constitution API로 공개
from literary_system.gates.auto_promotion_gate import (
    AutoPromotionGate,
    GateResult,
    R_THRESHOLD,
    MAX_ROLLBACKS,
)
from literary_system.constitution.self_learning_monitor import (
    SelfLearningMonitor,
    MonitorSnapshot,
    ComponentStatus,
    ROLLBACK_SURGE_THRESHOLD,
    F1_DROP_THRESHOLD,
    GATE_FAIL_STREAK_THRESHOLD,
    COMPONENT_NAMES,
)

# ConstitutionEvalV2 (SP-C.1, ADR-079)
from literary_system.constitution.constitution_eval_v2 import (  # noqa: E402
    ConstitutionEvalV2,
    EvalDimension,
    ConstitutionEvalResult,
    EvalScore,
    EVAL_THRESHOLD,
    DEFAULT_DIMENSION_NAMES,
)

# ContaminationDetector (SP-C.1, ADR-080)
from literary_system.constitution.contamination_detector import (  # noqa: E402
    ContaminationDetector,
    ContaminationFlag,
    ContaminationReport,
    LABEL_NOISE_THRESHOLD,
    NEAR_DUPLICATE_THRESHOLD,
    DISTRIBUTION_SHIFT_THRESHOLD,
    POISON_THRESHOLD,
)

# DataAugmentationController (SP-C.1, ADR-081)
from literary_system.constitution.data_augmentation_controller import (  # noqa: E402
    DataAugmentationController,
    AugmentedSample,
    AugmentationBatch,
    AUGMENTATION_STRATEGIES,
    DEFAULT_AUGMENT_RATIO,
    DEFAULT_AUGMENT_COUNT,
    MAX_AUGMENT_COUNT,
)

# FeedbackIntegrator (SP-C.1, ADR-082)
from literary_system.constitution.feedback_integrator import (  # noqa: E402
    FeedbackIntegrator,
    FeedbackRecord,
    IntegrationResult,
    FEEDBACK_TYPES,
    MIN_FEEDBACK_FOR_SIGNAL,
    CORRECTION_WEIGHT,
    REJECTION_PENALTY,
)

# MetaLearnerCycle (SP-C.1, ADR-101~104)
from literary_system.constitution.meta_learner_cycle import (  # noqa: E402
    MetaLearnerCycle,
    CycleReport,
    WeightConvergenceReport,
    MetaUpdateResult,
    FeedbackSignalSummary,
    WEIGHT_SUM_TOLERANCE,
    WEIGHT_ENTROPY_MIN,
    WEIGHT_CONVERGENCE_MIN_CYCLES,
    FEEDBACK_SIGNAL_MIN_STRENGTH,
    FEEDBACK_ADJUSTED_LOSS_SCALE,
)
