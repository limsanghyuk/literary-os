"""
V498 - NIE-L7 Container
ADR-016: NIE는 L7 Narrative Physics Engine의 자가 학습 운영 레이어.

NIL 6단계 루프의 진입점 컨테이너.
L7 텐서(physics_coefficients + alpha_dim + W[i][j])를 자가 학습한다.

V498 범위: 컨테이너 골격 + PhysicsRewardBridge 배선.
V502+: CIM 통합, V509+: RAG 통합, V512+: Stability 연동.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import logging

from literary_system.nie.physics_reward_bridge import PhysicsRewardBridge, BridgeResult
from literary_system.evaluation.mae_orchestrator import MAEOrchestrator
from literary_system.evaluation.scene_metrics_collector import SceneMetrics
from literary_system.learning.physics_coefficient_updater import PhysicsCoefficientUpdater
from literary_system.physics.coefficient_store import PhysicsCoefficientStore
from literary_system.physics.scene_feature_extractor import SceneFeature

logger = logging.getLogger(__name__)


@dataclass
class NIEConfig:
    """NIE-L7 컨테이너 설정."""
    enable_stability: bool = False    # V512+ NILStabilityModule
    enable_temporal_cim: bool = False # V505+ TemporalCIM
    enable_meta_learner: bool = False # V515+ MetaLearner (작품 30+ 필요)
    enable_rag_classifier: bool = False  # V509+ QueryIntentClassifier
    sample_rate: float = 0.27         # MAE 샘플링 비율 (27% 기본)
    version: str = "NIE-v2.0-V498"


class NIEContainer:
    """
    NIL 루프 진입점 컨테이너.
    ADR-016: L7 Narrative Physics Engine과의 통합 계약.

    V498 구현:
      - PhysicsRewardBridge 배선
      - run_scene(): 단일 씬 NIL Step 4+5 실행
      - get_status(): 현재 계수 + 기준선 조회
    """

    def __init__(
        self,
        mae_orchestrator: MAEOrchestrator,
        coefficient_store: PhysicsCoefficientStore,
        config: Optional[NIEConfig] = None,
        stability_module=None,
    ) -> None:
        self._config = config or NIEConfig()
        self._store = coefficient_store
        self._updater = PhysicsCoefficientUpdater(coefficient_store)
        self._bridge = PhysicsRewardBridge(
            mae_orchestrator=mae_orchestrator,
            coefficient_updater=self._updater,
            coefficient_store=coefficient_store,
            stability_module=stability_module,
        )
        logger.info("NIEContainer initialized: %s", self._config.version)

    def run_scene(
        self,
        scene_id: str,
        metrics: SceneMetrics,
        feature: Optional[SceneFeature] = None,
    ) -> BridgeResult:
        """
        NIL Step 4+5: MAE 평가 -> R(scene) -> 계수 업데이트.

        Args:
            scene_id: 씬 식별자
            metrics:  SceneMetrics (MAE 입력)
            feature:  SceneFeature (계수 업데이트 입력, None이면 업데이트 생략)
        """
        return self._bridge.process(scene_id, metrics, feature)

    def get_status(self) -> Dict[str, Any]:
        """현재 물리 계수 + NIL 기준선 조회."""
        return {
            "version": self._config.version,
            "physics_coefficients": self._store.as_dict(),
            "reward_baseline": self._bridge.get_baseline(),
            "processed_scenes": len(self._bridge.get_history()),
            "config": {
                "stability": self._config.enable_stability,
                "temporal_cim": self._config.enable_temporal_cim,
                "meta_learner": self._config.enable_meta_learner,
                "sample_rate": self._config.sample_rate,
            },
        }

    def reset(self) -> None:
        """새 작품 시작 시 기준선 + 히스토리 리셋."""
        self._bridge.reset_baseline()
        logger.info("NIEContainer reset: new work session")

    @property
    def bridge(self) -> PhysicsRewardBridge:
        return self._bridge

    @property
    def store(self) -> PhysicsCoefficientStore:
        return self._store

# [B3-FIX] 외부 참조 호환 별칭 (manifest / NILOrchestrator 등)
NIE_L7_Container = NIEContainer
