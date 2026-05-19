"""
NILOrchestrator — V519~V521
NIL 6-step 루프 통합 최상위 오케스트레이터

NIL Step 1 : CIM.update() + TemporalCIM.set_episode()  → 캐릭터 관계망 갱신
NIL Step 2 : CIM.top_k_triangles()                     → Triangle Tension
NIL Step 3 : AMW.update()                              → EmotionalVector
NIL Step 4 : MAEOrchestratorV2.evaluate()              → MAEResult (LLM 호출)
NIL Step 5 : PhysicsRewardBridge.process()             → BridgeResult (LLM-0)
NIL Step 6 : NarrativeTensionCurve.record()            → L_final 기여
+ QueryIntentClassifier (enable_rag_classifier 시)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from literary_system.nie.adaptive_momentum_weights import AdaptiveMomentumWeights
from literary_system.nie.agent_calibrator import AgentCalibrator, CalibrationResult
from literary_system.nie.character_influence_matrix import CharacterInfluenceMatrix
from literary_system.nie.mae_agents_v2 import MAEOrchestratorV2, MAEResultV2
from literary_system.nie.meta_learner import MetaLearner, MetaUpdateResult
from literary_system.nie.narrative_tension_curve import LossResult, NarrativeTensionCurve
from literary_system.nie.nie_l7_container import NIEConfig
from literary_system.nie.nil_stability_module import NILStabilityModule
from literary_system.nie.physics_reward_bridge import BridgeResult
from literary_system.nie.query_intent_classifier import QueryIntentClassifier
from literary_system.nie.temporal_cim import TemporalCIM
from literary_system.nie.tideal_learner import TIdealLearner

# ─── 입력/출력 스키마 ──────────────────────────────────────────────────────────

@dataclass
class SceneInput:
    """NIL 루프에 투입되는 씬 단위 입력."""
    scene_id: str
    episode_idx: int           # 에피소드 내 씬 순서 (0-based)
    total_scenes: int          # 에피소드 전체 씬 수
    metrics: Dict[str, float]  # {tension, sympathy, dread, catharsis, ...}
    char_updates: List[Tuple[str, str, float]] = field(default_factory=list)
    # char_updates: [(char_i, char_j, delta), ...] — CIM 갱신용
    feature: Optional[List[float]] = None   # PhysicsRewardBridge 피처 벡터
    query: Optional[str] = None             # RAG 쿼리 (enable_rag_classifier 시)


@dataclass
class NILResult:
    """NIL 루프 1회 실행 결과."""
    scene_id: str
    bridge_result: BridgeResult
    mae_result: MAEResultV2
    actual_tension: float
    step1_edges_updated: int
    step2_top_triangles: int
    step3_amw_vector: Dict[str, float]
    step6_rag_intent: Optional[str] = None
    stability_event: Optional[Any] = None  # StabilityEvent


@dataclass
class WorkCompletionResult:
    """작품 1편 완료 후 메타 레이어 실행 결과."""
    l_final: LossResult
    calibration: Optional[CalibrationResult] = None
    meta_update: Optional[MetaUpdateResult] = None
    fourier_update: Optional[Any] = None   # FourierUpdate


# ─── NILOrchestrator ──────────────────────────────────────────────────────────

class NILOrchestrator:
    """
    NIL 6-step 루프를 실행하는 통합 오케스트레이터 (V519~V521).

    NIEConfig 의 enable_* 플래그에 따라 모듈을 선택적으로 활성화한다.
    """

    def __init__(self, config: Optional[NIEConfig] = None) -> None:
        self._config = config or NIEConfig()

        # ── 핵심 모듈 (항상 활성) ───────────────────────────────────────────
        self._cim = CharacterInfluenceMatrix()
        self._mae = MAEOrchestratorV2()
        self._amw = AdaptiveMomentumWeights()
        self._tension_curve = NarrativeTensionCurve()
        self._calibrator = AgentCalibrator()

        # ── 선택적 모듈 ──────────────────────────────────────────────────────
        self._stability: Optional[NILStabilityModule] = (
            NILStabilityModule() if self._config.enable_stability else None
        )
        self._temporal_cim: Optional[TemporalCIM] = (
            TemporalCIM() if self._config.enable_temporal_cim else None
        )
        self._meta_learner: Optional[MetaLearner] = (
            MetaLearner() if self._config.enable_meta_learner else None
        )
        self._tideal: Optional[TIdealLearner] = (
            TIdealLearner() if self._config.enable_meta_learner else None
        )
        self._classifier: Optional[QueryIntentClassifier] = (
            QueryIntentClassifier() if self._config.enable_rag_classifier else None
        )

        # PhysicsRewardBridge — stability 모듈 주입
        # NIL 내장 reward bridge 상태 (V430 레거시 의존 없이 MAEOrchestratorV2 활용)
        self._reward_baseline: float = 0.50
        self._reward_baseline_decay: float = 0.95

        # 상태
        self._episode_idx: int = 0
        self._work_tension_history: List[float] = []
        self._scene_count: int = 0

    # ── 공개 API ─────────────────────────────────────────────────────────────

    def process_scene(self, scene: SceneInput) -> NILResult:
        """
        NIL 6-step 루프 1회 실행.
        씬 단위로 호출한다.
        """
        self._scene_count += 1

        # ── Step 1: CIM 갱신 ────────────────────────────────────────────────
        for char_i, char_j, delta in scene.char_updates:
            self._cim.update(char_i, char_j, delta)
        edges_updated = len(scene.char_updates)

        if self._temporal_cim is not None:
            for char_i, char_j, delta in scene.char_updates:
                self._temporal_cim.update(self._episode_idx, char_i, char_j, delta)

        # ── Step 2: Triangle Tension ─────────────────────────────────────────
        triangles = self._cim.top_k_triangles()

        # ── Step 3: AMW 갱신 ────────────────────────────────────────────────
        _amw_ev = self._amw.update(
            scene_record=scene.metrics,
            advantage=0.0,              # advantage 는 Step 5 이후 다음 씬에 반영
            episode_idx=scene.episode_idx,
        )
        amw_vector = {"tension": _amw_ev.tension, "sympathy": _amw_ev.sympathy,
                      "dread": _amw_ev.dread, "catharsis": _amw_ev.catharsis}

        # ── Step 4: MAE 평가 ─────────────────────────────────────────────────
        mae_result = self._mae.evaluate(scene.scene_id, scene.metrics)

        # 캘리브레이터 기록
        for agent_name in ["reader", "writer", "editor", "cultural"]:
            self._calibrator.record_result(
                agent=agent_name,
                passed=mae_result.passed,
                sigma=mae_result.sigma,
            )

        # ── Step 5: NIL Inline Reward Bridge (LLM-0, MAEOrchestratorV2 기반) ───
        _total = max(len(mae_result.verdicts), 1)
        _pass_n = sum(1 for v in mae_result.verdicts if v.score >= 0.55)
        _bonus = 0.10 if mae_result.sigma < 0.05 else 0.0
        _reward = min(_pass_n / _total + _bonus, 1.0)
        _advantage = _reward - self._reward_baseline
        self._reward_baseline = (
            self._reward_baseline_decay * self._reward_baseline
            + (1 - self._reward_baseline_decay) * _reward
        )
        bridge_result = BridgeResult(
            scene_id=scene.scene_id,
            reward=_reward,
            advantage=_advantage,
            baseline=self._reward_baseline,
            coefficients_updated=False,
            delta=_advantage * (self._stability.get_effective_lr("physics", 0.01) if self._stability else 0.01),
        )

        # advantage 를 AMW 에 소급 반영
        if abs(_advantage) > 1e-6:
            _amw_ev2 = self._amw.update(
                scene_record=scene.metrics,
                advantage=_advantage,
                episode_idx=scene.episode_idx,
            )
            amw_vector = {"tension": _amw_ev2.tension, "sympathy": _amw_ev2.sympathy,
                          "dread": _amw_ev2.dread, "catharsis": _amw_ev2.catharsis}

        # ── Step 6: NarrativeTensionCurve + RAG ──────────────────────────────
        actual_tension = scene.metrics.get("tension", 0.5)
        self._tension_curve.record(
            scene_idx=scene.episode_idx,
            total_scenes=scene.total_scenes,
            actual_tension=actual_tension,
        )
        self._work_tension_history.append(actual_tension)

        rag_intent = None
        if self._classifier is not None and scene.query:
            clf_result = self._classifier.classify(scene.query)
            rag_intent = clf_result.intent.value

        # 안정성 이벤트 캡처
        stability_event = None
        if self._stability is not None:
            for dim in ("tension", "sympathy", "dread", "catharsis"):
                evt = self._stability.check_boundary(dim, amw_vector.get(dim, 0.5))
                if evt and evt.is_alarm:
                    stability_event = evt
                    break

        return NILResult(
            scene_id=scene.scene_id,
            bridge_result=bridge_result,
            mae_result=mae_result,
            actual_tension=actual_tension,
            step1_edges_updated=edges_updated,
            step2_top_triangles=len(triangles),
            step3_amw_vector=amw_vector,
            step6_rag_intent=rag_intent,
            stability_event=stability_event,
        )

    def complete_episode(self) -> None:
        """에피소드 1화 완료 시 호출. TemporalCIM 에포크 진행."""
        if self._temporal_cim is not None:
            self._episode_idx += 1
            self._temporal_cim.set_episode(self._episode_idx)

    def complete_work(self, genre: Optional[str] = None) -> WorkCompletionResult:
        """
        작품 1편 완료 시 호출.
        L_final 계산 → TIdealLearner → AgentCalibrator → MetaLearner 순으로 실행.
        """
        # L_final
        l_result = self._tension_curve.compute_l_final()

        # TIdealLearner (enable_meta_learner 시)
        fourier_update = None
        if self._tideal is not None and self._work_tension_history:
            fourier_update = self._tideal.update(
                tension_curve=self._tension_curve,
                actual_tensions=self._work_tension_history,
                genre=genre or "default",
            )

        # AgentCalibrator
        self._calibrator.complete_work()
        calibration = self._calibrator.maybe_calibrate(self._mae)

        # MetaLearner
        meta_update = None
        if self._meta_learner is not None:
            self._meta_learner.record_work_loss(l_result.l_final, genre=genre)
            meta_update = self._meta_learner.maybe_meta_update(
                amw=self._amw,
                tension_curve=self._tension_curve,
                orchestrator=self._mae,
                stability=self._stability,
            )

        # 히스토리 초기화 (다음 작품 준비)
        self._work_tension_history.clear()
        self._tension_curve.reset() if hasattr(self._tension_curve, "reset") else None

        return WorkCompletionResult(
            l_final=l_result,
            calibration=calibration,
            meta_update=meta_update,
            fourier_update=fourier_update,
        )

    # ── 상태 조회 ──────────────────────────────────────────────────────────
    @property
    def config(self) -> NIEConfig:
        return self._config

    @property
    def scene_count(self) -> int:
        return self._scene_count

    @property
    def tension_curve(self) -> NarrativeTensionCurve:
        return self._tension_curve

    @property
    def cim(self) -> CharacterInfluenceMatrix:
        return self._cim

    @property
    def stability(self) -> Optional[NILStabilityModule]:
        return self._stability

    @property
    def meta_learner(self) -> Optional[MetaLearner]:
        return self._meta_learner

    def get_l_final(self) -> LossResult:
        return self._tension_curve.compute_l_final()

    def get_mae_sigma(self) -> float:
        """최근 MAE 결과의 σ 반환 (Gate25 점검용)."""
        history = getattr(self._mae, "_history", [])
        if history:
            return history[-1].sigma
        return 0.0
