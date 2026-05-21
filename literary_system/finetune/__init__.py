"""
literary_system.finetune — SP4 FineTune LoRA POC 패키지 (V474)

ADR-006/008/009/010/014/017
"""
from literary_system.finetune.canary_kpi_monitor import (
    KPI_THRESHOLDS,
    CanaryKPIMonitor,
    KPIRecord,
    KPIWindow,
    RollbackEvent,
)
from literary_system.finetune.finetune_job_manager import (
    FineTuneJob,
    FineTuneJobManager,
    FineTuneMethod,
    JobStatus,
)
from literary_system.finetune.model_eval_harness import (
    EvalReport,
    EvalSample,
    ModelEvalHarness,
)
from literary_system.finetune.model_version_manager import (
    CANARY_STEPS,
    ModelArtifact,
    ModelStage,
    ModelVersion,
    ModelVersionManager,
)
from literary_system.finetune.prose_specializer_api import (
    ABComparisonResult,
    ABGroup,
    ProseSpecializerAPI,
    ServeRequest,
    ServeResponse,
    ServingTier,
)
from literary_system.finetune.prose_style_dataset import (
    ALLOWED_LICENSES,
    DatasetCard,
    DatasetSplit,
    DataSource,
    LicenseType,
    ProseEntry,
    ProseStyle,
    ProseStyleDataset,
    make_entry,
)
from literary_system.finetune.safety_regression_suite import (
    SafetyCategory,
    SafetyRegressionSuite,
    SafetyReport,
    SafetyViolation,
)

__all__ = [
    "FineTuneJobManager", "FineTuneJob", "FineTuneMethod", "JobStatus",
    "ProseStyleDataset", "ProseEntry", "ProseStyle", "DataSource", "LicenseType",
    "DatasetSplit", "LoRADatasetSplit", "DatasetCard", "make_entry", "ALLOWED_LICENSES",
    "ModelEvalHarness", "EvalSample", "EvalReport",
    "SafetyRegressionSuite", "SafetyViolation", "SafetyReport", "SafetyCategory",
    "ModelVersionManager", "ModelVersion", "ModelArtifact", "ModelStage", "CANARY_STEPS",
    "CanaryKPIMonitor", "KPIRecord", "KPIWindow", "RollbackEvent", "KPI_THRESHOLDS",
    "ProseSpecializerAPI", "ServeRequest", "ServeResponse", "ABComparisonResult",
    "ServingTier", "ABGroup",
]
from literary_system.finetune.equivalence_tester import (
    DRIFT_PASS_RATE_MIN,
    THRESHOLD_BERTSCORE_F1_MIN,
    THRESHOLD_KL_DIVERGENCE_MAX,
    EquivalenceAxis,
    EquivalenceDriftReport,
    EquivalenceReport,
    EquivalenceTester,
)
from literary_system.finetune.gpu_adapter import (
    DEFAULT_COST_SLO,
    CostSLO,
    GPUAdapterContract,
    GPUJobRequest,
    GPUJobResult,
    GPUJobStatus,
    GPUProvider,
    HFAutoTrainAdapter,
    LambdaLabsAdapter,
    RunPodAdapter,
    get_adapter,
    list_providers,
)
from literary_system.finetune.lora_dataset_builder import (
    ALPACA_INSTRUCTION,
    ALPACA_INPUT_TEMPLATE,
    LoRASample,
    LoRADatasetBuilder,
)
from literary_system.finetune.dataset_splitter import (
    DEFAULT_TRAIN_RATIO,
    DEFAULT_VAL_RATIO,
    DEFAULT_TEST_RATIO,
    DEFAULT_SEED,
    LoRADatasetSplit,
    DatasetSplitter,
)
from literary_system.finetune.dataset_registry import (
    LoRADatasetVersion,
    DatasetRegistry,
)
from literary_system.finetune.lora_training_config import (
    DEFAULT_BASE_MODEL,
    DEFAULT_LORA_RANK,
    DEFAULT_TARGET_MODULES,
    MONTHLY_SLO_USD,
    LoRAQuantizationType,
    LoRAScheduleType,
    LoRATrainingConfig,
)
from literary_system.finetune.lora_job_runner import (
    BIWEEKLY_INTERVAL_DAYS,
    WEEKLY_INTERVAL_DAYS,
    BiweeklyScheduler,
    JobRunRecord,
    LoRAJobRunner,
)

# V598 — LoRAArtifact + LoRAModelRegistry + LoRAInferenceGateway (SP-B.1, ADR-058)
from literary_system.finetune.lora_artifact import (
    ArtifactStage,
    LoRAArtifact,
    LoRAArtifactContract,
    compute_sha256,
    make_artifact,
)
from literary_system.finetune.lora_model_registry import (
    ArtifactNotFoundError,
    LoRAModelRegistry,
    RegisterConflictError,
    StageTransitionError,
)
from literary_system.finetune.lora_inference_gateway import (
    G53_LATENCY_LIMIT_MS,
    G53_MIN_LENGTH,
    InferenceResult,
    LORA_PROVIDER_NAME,
    LoRAInferenceGateway,
    StubInferenceBackend,
)
from literary_system.finetune.pre_train_safety import (
    PreTrainSafety,
    SafetyAxis,
    SafetyResult,
    AxisResult,
)
from literary_system.finetune.finetune_eval_pipeline import (
    FineTuneEvalPipeline,
    EvalResult,
    EvalAxisResult,
    compute_bertscore_f1,
    compute_bleu4,
    compute_krippendorff_alpha,
    THRESHOLD_BERTSCORE_F1,
    THRESHOLD_LLM_JUDGE,
    THRESHOLD_STYLE,
    THRESHOLD_BLEU,
    THRESHOLD_KRIPPENDORFF_ALPHA,
)
from literary_system.finetune.long_context_strategy import (
    LongContextStrategy,
    TextChunk,
    ChunkingResult,
    CHUNK_SIZE_TOKENS,
    OVERLAP_TOKENS,
)
