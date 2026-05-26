"""
literary_system/constitution — SP-A.7 (V594) LOSConstitution v1.0
                              + SP-C.1 (V631) LOSConstitution v2.0 Bayesian Weight Optimiser
                              + SP-C.1 (V632) ConstitutionWeightTracker LOSDB 영속화 + 롤백
                              + SP-C.1 (V633) PatternLibraryV2 압축+랭킹
                              + SP-C.1 (V634) RetrainingScheduler F1 drift 기반 재학습
                              + SP-C.1 (V635) AutoPromotionGate G62 자동 승격
                              + SP-C.1 (V636) SelfLearningMonitor 파이프라인 모니터

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