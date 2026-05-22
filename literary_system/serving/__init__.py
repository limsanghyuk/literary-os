"""literary_system/serving — 모델 서빙 레이어 (V605)."""

from __future__ import annotations

from literary_system.serving.canary_controller import (
    STAGE_WEIGHTS,
    CanaryConfig,
    CanaryController,
    CanaryStage,
    CanaryState,
    CanaryStatus,
    PromotionRecord,
    StageMetrics,
)
from literary_system.serving.model_serving_endpoint import (
    EndpointConfig,
    ModelCard,
    ModelServingEndpoint,
)

__all__ = [
    # canary_controller
    "CanaryConfig",
    "CanaryController",
    "CanaryStage",
    "CanaryState",
    "CanaryStatus",
    "PromotionRecord",
    "STAGE_WEIGHTS",
    "StageMetrics",
    # model_serving_endpoint
    "EndpointConfig",
    "ModelCard",
    "ModelServingEndpoint",
]
