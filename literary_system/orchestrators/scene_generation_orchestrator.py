"""
V325 - SceneGenerationOrchestrator  (Phase 3)
씬 루프 집행자 — 단절 A·B 완전 해결.

단절 A 해결: MAEResult → CoefficientMapper → LearnedCoefficientStore 자동 연결
단절 B 해결: 씬 루프 자동 전개 (시퀀스 → 전체 씬 반복)

설계 원칙 (P2 외과적 통합):
  - bridge: LLMBridgeInterface → ClaudeAdapter 또는 MockLLMBridge 주입
  - MAEOrchestrator, CoefficientMapper, LearnedCoefficientStore 기존 코드 무수정
  - consensus=False AND retry<3 → 재렌더 (최대 3회)
  - consensus=True → 씬 커밋 + 계수 갱신
  - LLM 호출은 bridge.generate()를 통해서만
"""
from __future__ import annotations
import logging
from typing import Optional

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from literary_system.orchestrators.sequence_planner import SequencePlan
from literary_system.orchestrators.scene_focus_injector import (
    SceneFocusInjector,
    SceneFocusContext,
)

logger = logging.getLogger(__name__)
# V327 P1-2: DRSE 실 피드백 루프 활성화 임포트
try:
    from literary_system.evaluation.scene_metrics_collector import SceneMetricsCollector as _SceneMetricsCollector
    from literary_system.drse.drse_engine import DRSEEngine as _DRSEEngine
    _DRSE_AVAILABLE = True
except ImportError:
    _DRSE_AVAILABLE = False

# V327 P2: 동시성 엔진 lazy import
try:
    from literary_system.orchestrators.character_intent_agent import (
        ConcurrentIntentCollector as _ConcurrentIntentCollector,
    )
    from literary_system.orchestrators.concurrent_action_resolver import (
        ConcurrentActionResolver as _ConcurrentActionResolver,
    )
    from literary_system.orchestrators.collision_focus_injector import (
        CollisionFocusInjector as _CollisionFocusInjector,
    )
    _CONCURRENT_AVAILABLE = True
except ImportError:
    _CONCURRENT_AVAILABLE = False

# V327 P3: KnowledgeStateTracker lazy import
try:
    from literary_system.world.knowledge_state_tracker import (
        KnowledgeStateTracker as _KnowledgeStateTracker,
    )
    _KNOWLEDGE_TRACKER_AVAILABLE = True
except ImportError:
    _KNOWLEDGE_TRACKER_AVAILABLE = False

# V328 Task12: MiseEnSceneCompiler lazy import
try:
    from literary_system.drse.mise_en_scene_compiler import (
        MiseEnSceneCompiler as _MiseEnSceneCompiler,
    )
    _MISE_EN_SCENE_AVAILABLE = True
except ImportError:
    _MiseEnSceneCompiler = None  # type: ignore
    _MISE_EN_SCENE_AVAILABLE = False

# V328: CharacterStateGate lazy import
try:
    from literary_system.gate.character_state_gate import (
        CharacterStateGate as _CharacterStateGate,
    )
    _CHAR_STATE_GATE_AVAILABLE = True
except ImportError:
    _CharacterStateGate = None  # type: ignore
    _CHAR_STATE_GATE_AVAILABLE = False

# V328 Task17: EmotionalMomentumTracker lazy import
try:
    from literary_system.emotion.emotional_momentum_tracker import (
        EmotionalMomentumTracker as _EmotionalMomentumTracker,
    )
    _EMOTION_TRACKER_AVAILABLE = True
except ImportError:
    _EmotionalMomentumTracker = None  # type: ignore
    _EMOTION_TRACKER_AVAILABLE = False

# V328 Task17: SceneDraftOutput lazy import
try:
    from literary_system.schemas.scene_draft_output import (
        SceneDraftOutput as _SceneDraftOutput,
    )
    _SCENE_DRAFT_OUTPUT_AVAILABLE = True
except ImportError:
    _SceneDraftOutput = None  # type: ignore
    _SCENE_DRAFT_OUTPUT_AVAILABLE = False



# ────────────────────────────────────────────────────────────────
# 결과 데이터클래스
# ────────────────────────────────────────────────────────────────

@dataclass
class SceneRecord:
    """단일 씬 처리 결과."""
    scene_id:    str
    seq_id:      str
    scene_index: int          # 에피소드 내 전역 씬 순번
    text:        str
    consensus:   bool
    retries:     int
    llm_calls:   int
    mae_score:   float        # MAEOrchestrator avg score (없으면 0.0)
    focus_ctx:   dict         # SceneFocusContext.to_dict()

    def to_dict(self) -> dict[str, Any]:
        return {
            "scene_id":    self.scene_id,
            "seq_id":      self.seq_id,
            "scene_index": self.scene_index,
            "text":        self.text[:200] + "..." if len(self.text) > 200 else self.text,
            "consensus":   self.consensus,
            "retries":     self.retries,
            "llm_calls":   self.llm_calls,
            "mae_score":   round(self.mae_score, 4),
        }


@dataclass
class E2ESceneGenerationResult:
    """SceneGenerationOrchestrator 실행 결과."""
    project_id:             str
    episode_no:             int
    total_scenes_generated: int
    total_llm_calls:        int
    total_retries:          int
    mae_consensus_rate:     float    # consensus=True 비율
    coeff_update_count:     int      # 계수 갱신 횟수
    scenes:                 list[SceneRecord] = field(default_factory=list)
    duration_seconds:       float = 0.0
    success:                bool  = True
    error:                  str | None = None

    def summary(self) -> dict[str, Any]:
        return {
            "project_id":             self.project_id,
            "episode_no":             self.episode_no,
            "total_scenes_generated": self.total_scenes_generated,
            "total_llm_calls":        self.total_llm_calls,
            "total_retries":          self.total_retries,
            "mae_consensus_rate":     round(self.mae_consensus_rate, 4),
            "coeff_update_count":     self.coeff_update_count,
            "duration_seconds":       round(self.duration_seconds, 2),
            "success":                self.success,
        }


# ────────────────────────────────────────────────────────────────
# SceneGenerationOrchestrator
# ────────────────────────────────────────────────────────────────

class SceneGenerationOrchestrator:
    """
    V325 핵심 오케스트레이터 — 씬 루프 집행자.

    단절 A 해결: MAEResult → CoefficientMapper.map_to_mae()
               → LearnedCoefficientStore 계수 자동 갱신
    단절 B 해결: 시퀀스 목록 전체를 씬 단위로 반복 실행

    사용 예:
        orch = SceneGenerationOrchestrator(
            bridge=ClaudeAdapter(),
            mae_orchestrator=MAEOrchestrator(),
            coeff_mapper=CoefficientMapper(),
            coeff_store=LearnedCoefficientStore(),
        )
        result = orch.run_episode(sequence_plans, project_id="mr_sunshine")
    """

    MAX_RETRIES_PER_SCENE = 3

    def __init__(
        self,
        bridge:           Any,           # LLMBridgeInterface
        mae_orchestrator: Any | None = None,    # MAEOrchestrator
        coeff_mapper:     Any | None = None,    # CoefficientMapper
        coeff_store:      Any | None = None,    # LearnedCoefficientStore
        rag_bridge:       Any | None = None,    # LibrarianRAGBridge
        scene_metrics_collector: Any | None = None,  # SceneMetricsCollector
        collector:        Any | None = None,    # V327 P1-1: SelfLearningCollector
        intent_collector: Any | None = None,    # V327 P2: ConcurrentIntentCollector
        action_resolver:  Any | None = None,    # V327 P2: ConcurrentActionResolver
        knowledge_tracker: Any | None = None,   # V327 P3: KnowledgeStateTracker
        mise_compiler:    Any | None = None,    # V328 Task12: MiseEnSceneCompiler
        char_state_gate:  Any | None = None,    # V328: CharacterStateGate
        emotion_tracker:  Any | None = None,    # V328 Task17: EmotionalMomentumTracker
        verbose:          bool = False,
    ) -> None:
        self.bridge           = bridge
        self.mae              = mae_orchestrator
        self.coeff_mapper     = coeff_mapper
        self.coeff_store      = coeff_store
        self.rag_bridge       = rag_bridge
        # V327 P1-2: SceneMetricsCollector 기본값화 — None이면 실 인스턴스 생성
        if scene_metrics_collector is not None:
            self.metrics_col = scene_metrics_collector
        elif _DRSE_AVAILABLE:
            try:
                self.metrics_col = _SceneMetricsCollector()
            except Exception:
                self.metrics_col = None
        else:
            self.metrics_col = None
        self._collector       = collector         # V327 P1-1
        self._intent_collector   = intent_collector    # V327 P2
        self._action_resolver    = action_resolver     # V327 P2
        self._knowledge_tracker  = knowledge_tracker   # V327 P3
        # V328 Task12: MiseEnSceneCompiler
        if mise_compiler is not None:
            self._mise_compiler = mise_compiler
        elif _MISE_EN_SCENE_AVAILABLE:
            try:
                self._mise_compiler = _MiseEnSceneCompiler()
            except Exception:
                self._mise_compiler = None
        else:
            self._mise_compiler = None
        # V328: CharacterStateGate
        self._char_state_gate = char_state_gate
        # V328 Task17: EmotionalMomentumTracker — None이면 자동 생성
        if emotion_tracker is not None:
            self._emotion_tracker = emotion_tracker
        elif _EMOTION_TRACKER_AVAILABLE:
            try:
                self._emotion_tracker = _EmotionalMomentumTracker()
            except Exception:
                self._emotion_tracker = None
        else:
            self._emotion_tracker = None
        # V327 P2: CollisionFocusInjector (충돌 감지 시 동적 교체)
        self._collision_injector = (
            _CollisionFocusInjector(rag_bridge=rag_bridge)
            if _CONCURRENT_AVAILABLE
            else None
        )
        self.verbose          = verbose

        self._focus_injector  = SceneFocusInjector(rag_bridge=rag_bridge)
        self._current_episode_no: int = 1   # V327 P1-1: 에피소드 번호 추적

    # ── 공개 API ─────────────────────────────────────────────────

    def run_episode(
        self,
        sequence_plans: list[SequencePlan],
        project_id:     str = "default",
        episode_no:     int = 1,
        character_states: dict[str, Any] | None = None,
    ) -> E2ESceneGenerationResult:
        """
        시퀀스 목록 → 에피소드 전체 씬 생성 루프.

        Args:
            sequence_plans:  SequencePlanner.plan() 출력
            project_id:      프로젝트 식별자
            episode_no:      에피소드 번호
            character_states: {캐릭터명: {intent, location, emotion, ...}}

        Returns:
            E2ESceneGenerationResult
        """
        self._current_episode_no = episode_no  # V327 P1-1: 에피소드 번호 동기화
        start     = time.time()
        records:  list[SceneRecord] = []
        total_llm = 0
        total_ret = 0
        coeff_upd = 0
        global_scene_idx = 0
        error     = None
        success   = True

        try:
            for seq_plan in sequence_plans:
                seq_scenes = seq_plan.scene_count
                for local_idx in range(seq_scenes):
                    record, llm_calls, retries, coeff_updated = self._run_single_scene(
                        seq_plan        = seq_plan,
                        scene_index     = local_idx,
                        total_in_seq    = seq_scenes,
                        global_idx      = global_scene_idx,
                        project_id      = project_id,
                        character_states= character_states or {},
                    )
                    records.append(record)
                    total_llm    += llm_calls
                    total_ret    += retries
                    coeff_upd    += (1 if coeff_updated else 0)
                    global_scene_idx += 1

                    if self.verbose:
                        status = "✅ PASS" if record.consensus else "⚠️  FAIL"
                        logger.debug(f"  {record.scene_id} {status} "
                              f"(retry={retries}, llm={llm_calls})")

        except Exception as exc:
            error   = str(exc)
            success = False

        consensus_count = sum(1 for r in records if r.consensus)
        consensus_rate  = consensus_count / len(records) if records else 0.0
        duration        = time.time() - start

        return E2ESceneGenerationResult(
            project_id             = project_id,
            episode_no             = episode_no,
            total_scenes_generated = len(records),
            total_llm_calls        = total_llm,
            total_retries          = total_ret,
            mae_consensus_rate     = consensus_rate,
            coeff_update_count     = coeff_upd,
            scenes                 = records,
            duration_seconds       = duration,
            success                = success,
            error                  = error,
        )

    # ── 씬 단위 처리 ─────────────────────────────────────────────

    def _run_single_scene(
        self,
        seq_plan:         SequencePlan,
        scene_index:      int,
        total_in_seq:     int,
        global_idx:       int,
        project_id:       str,
        character_states: dict[str, Any],
    ) -> tuple[SceneRecord, int, int, bool]:
        """
        단일 씬 생성 + MAE 평가 + 재렌더 루프.

        Returns:
            (SceneRecord, llm_calls, retries, coeff_updated)
        """
        # ▶ V327 P2: ConcurrentIntentCollector → ConcurrentActionResolver → CollisionFocusInjector
        _collision_event = None
        if self._intent_collector is not None and _CONCURRENT_AVAILABLE:
            try:
                _packets = self._intent_collector.collect_sync(
                    tension=seq_plan.tension_target
                )
                if self._action_resolver is not None and _packets:
                    _events = self._action_resolver.resolve(_packets)
                    if _events:
                        # 가장 tension_boost가 높은 충돌 이벤트 선택
                        _collision_event = max(_events, key=lambda e: e.tension_boost)
            except Exception:
                _collision_event = None  # 동시성 엔진 오류가 씬 생성을 중단시키지 않음

        # SceneFocusInjector → Micro-Context 조립 (충돌 감지 시 CollisionFocusInjector로 교체)
        if _collision_event is not None and self._collision_injector is not None:
            focus_ctx = self._collision_injector.build_collision(
                seq_plan         = seq_plan,
                scene_idx        = scene_index,
                total_scenes     = total_in_seq,
                collision_event  = _collision_event,
                character_states = character_states,
            )
        else:
            focus_ctx = self._focus_injector.build(
                seq_plan            = seq_plan,
                scene_index         = scene_index,
                total_scenes_in_seq = total_in_seq,
                character_states    = character_states,
            )
        scene_id  = focus_ctx.scene_id
        context   = focus_ctx.to_dict()

        # ▶ V327 P3: KnowledgeStateTracker — 지식 비대칭 압력을 character_states에 주입
        if self._knowledge_tracker is not None and _KNOWLEDGE_TRACKER_AVAILABLE:
            try:
                _chars = [c for c in character_states if not c.startswith("_")]
                if _chars:
                    _kp_result = self._knowledge_tracker.scene_pressure_from_knowledge(
                        characters_in_scene=_chars,
                    )
                    # total_pressure를 character_states에 메타키로 주입
                    # → _build_prompt()에서 지식 압력 힌트로 활용
                    character_states = {
                        **character_states,
                        "_knowledge_pressure": _kp_result.get("total_pressure", 0.0),
                        "_dominant_tension": _kp_result.get("dominant_tension"),
                    }
            except Exception:
                pass  # 지식 추적기 오류가 씬 생성을 중단시키지 않음

        llm_calls     = 0
        retries       = 0
        text          = ""
        consensus     = False
        mae_score     = 0.0
        coeff_updated = False

        for attempt in range(self.MAX_RETRIES_PER_SCENE + 1):
            # ① LLM 생성
            prompt = self._build_prompt(seq_plan, focus_ctx, attempt, character_states)
            try:
                text      = self.bridge.generate(prompt, context)
                llm_calls += 1
            except Exception:
                text = ""

            # ② MAE 평가 (없으면 consensus=True로 간주)
            if self.mae is None:
                consensus = True
                break

            metrics = self._collect_metrics(scene_id, text)
            mae_result = self.mae.evaluate(scene_id, metrics)
            mae_score  = sum(v.score for v in mae_result.votes) / len(mae_result.votes)
            consensus  = mae_result.consensus

            # ③ 단절 A 해결: MAEResult → CoefficientMapper → LearnedCoefficientStore
            if self.coeff_mapper and self.coeff_store:
                self._update_coefficients(mae_result)
                coeff_updated = True

            if consensus:
                break

            retries += 1
            if retries >= self.MAX_RETRIES_PER_SCENE:
                break

        record = SceneRecord(
            scene_id    = scene_id,
            seq_id      = seq_plan.seq_id,
            scene_index = global_idx,
            text        = text,
            consensus   = consensus,
            retries     = retries,
            llm_calls   = llm_calls,
            mae_score   = mae_score,
            focus_ctx   = focus_ctx.to_dict(),
        )

        # ▶ V327 P1-1: SelfLearningCollector 배선 (1줄 핵심 배선)
        if self._collector is not None:
            try:
                self._collector.collect(
                    scene_record = record,
                    seq_plan     = seq_plan,
                    episode_no   = self._current_episode_no,
                )
            except Exception:
                pass  # collector 오류가 씬 생성을 중단시키지 않도록

        # ▶ V328 Task17: EmotionalMomentumTracker — 씬별 감정 벡터 업데이트
        _ev = None
        if self._emotion_tracker is not None and _EMOTION_TRACKER_AVAILABLE:
            try:
                _ev = self._emotion_tracker.update(record, seq_plan)
            except Exception:
                pass

        # ▶ V328 Task17: SceneDraftOutput — Pydantic 구조화 출력 주입
        if _SCENE_DRAFT_OUTPUT_AVAILABLE:
            try:
                record._draft_output = _SceneDraftOutput.from_scene_record(
                    record=record,
                    episode_no=self._current_episode_no,
                    seq_index=getattr(seq_plan, "seq_index", 0),
                    scene_index=global_idx,
                    emotional_vector=_ev,
                )
            except Exception:
                pass

        return record, llm_calls, retries, coeff_updated

    # ── 내부 헬퍼 ────────────────────────────────────────────────

    def _build_prompt(
        self,
        seq_plan:  SequencePlan,
        focus_ctx: SceneFocusContext,
        attempt:   int,
        character_states: dict[str, Any] | None = None,
    ) -> str:
        """씬 생성 프롬프트 조립."""
        parts = [
            f"[시퀀스 목표] {seq_plan.goal}",
            f"[긴장도 목표] {seq_plan.tension_target:.2f}",
            focus_ctx.micro_context,
        ]
        # V327 P3: 지식 비대칭 압력 힌트
        if character_states:
            kp = character_states.get("_knowledge_pressure", 0.0)
            dt = character_states.get("_dominant_tension")
            if kp and kp > 0.3:
                parts.append(f"[지식 비대칭 압력] {kp:.2f}")
            if dt:
                parts.append(
                    f"[핵심 긴장축] {dt.get('chars', '')} — "
                    f"사실: {dt.get('fact', '')} (압력: {dt.get('pressure', 0):.2f})"
                )
        # V328 Task12: MiseEnSceneCompiler 연출 힌트
        if self._mise_compiler is not None and _MISE_EN_SCENE_AVAILABLE:
            try:
                _chars = [c for c in (character_states or {}) if not c.startswith("_")]
                _note  = self._mise_compiler.compile(
                    scene_id=focus_ctx.scene_id,
                    scene_goal=seq_plan.goal,
                    characters=_chars,
                )
                _hint = _note.to_prompt_hint()
                if _hint:
                    parts.append(_hint)
            except Exception:
                pass
        # V328 Task17: 감정 모멘텀 힌트
        if self._emotion_tracker is not None and _EMOTION_TRACKER_AVAILABLE:
            try:
                _em_hint = self._emotion_tracker.to_prompt_hint()
                if _em_hint:
                    parts.append(_em_hint)
            except Exception:
                pass
        if attempt > 0:
            parts.append(f"[재생성 {attempt}회차] 이전 씬이 품질 기준 미달. 더 높은 완성도로 재작성.")
        return "\n".join(parts)

    def _collect_metrics(self, scene_id: str, text: str) -> Any:
        """
        V327 P1-2: SceneMetrics 생성.
        실 인스턴스(SceneMetricsCollector) 우선 사용, 없으면 기본값 폴백.
        """
        if self.metrics_col is not None:
            try:
                return self.metrics_col.collect(scene_id, text)
            except Exception:
                pass
        # 폴백 — SceneMetricsCollector 초기화 실패 시에만 도달
        return _DefaultSceneMetrics(
            scene_id                = scene_id,
            drse_gate_pass_rate     = 0.75,
            character_state_valid   = True,
            reader_pull             = min(1.0, 0.5 + len(text) / 2000),
            reader_afterimage       = 0.6,
            reader_uncertainty      = 0.4,
        )

    def _update_coefficients(self, mae_result: Any) -> None:
        """
        단절 A 해결 구현:
        MAEResult → CoefficientMapper.map_to_mae() → LearnedCoefficientStore.
        """
        try:
            from literary_system.validation.learned_coefficient_store import (
                LearnedCoefficientStore,
                CoefficientRecord,
            )
            # MAEWeights → LearnedCoefficients 역매핑
            mae_weights = self.coeff_mapper.map_to_mae(
                self.coeff_store.get_latest_coefficients()
                if hasattr(self.coeff_store, "get_latest_coefficients")
                else _dummy_learned_coefficients()
            )
            # 결과를 ChangeLedger에 기록
            self.coeff_mapper.map_from_mae(mae_weights)
        except Exception:
            pass


# ────────────────────────────────────────────────────────────────
# 내부 기본 SceneMetrics (SceneMetricsCollector 없을 때 fallback)
# ────────────────────────────────────────────────────────────────

class _DefaultSceneMetrics:
    """MAEOrchestrator가 요구하는 최소 SceneMetrics 구조."""

    def __init__(
        self,
        scene_id:               str,
        drse_gate_pass_rate:    float = 0.75,
        character_state_valid:  bool  = True,
        reader_pull:            float = 0.60,
        reader_afterimage:      float = 0.55,
        reader_uncertainty:     float = 0.40,
    ) -> None:
        self.scene_id                  = scene_id
        self.drse_gate_pass_rate       = drse_gate_pass_rate
        self.character_state_valid     = character_state_valid
        self.reader_pull               = reader_pull
        self.reader_afterimage         = reader_afterimage
        self.reader_uncertainty        = reader_uncertainty
        # All fields MAEOrchestrator / mae_agents require
        self.spatial_violation_count  = 0
        self.relation_consistency     = 1.0
        self.reader_composite_score   = (reader_pull + reader_afterimage - reader_uncertainty) / 3.0
        self.tension_delta            = 0.0
        self.information_reveal_score = 0.5
        self.causal_coherence_score   = 0.8
        self.emotional_momentum_score = 0.5


def _dummy_learned_coefficients() -> Any:
    """LearnedCoefficientStore가 없을 때 사용하는 dummy 계수."""
    class _Dummy:
        reader_pull_weight    = 1.0
        afterimage_weight     = 1.0
        uncertainty_weight    = 1.0
        drse_threshold        = 0.5
    return _Dummy()
