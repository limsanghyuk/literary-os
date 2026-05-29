"""
V326 - CollisionFocusInjector  (동시성 서사 엔진 — Phase 3)

【설계 원리】
  CollisionEvent를 받아 씬 컨텍스트(SceneFocusContext)를 확장한다.
  기존 SceneFocusInjector를 완전히 교체하는 것이 아니라,
  '충돌이 있는 씬'에서만 추가로 작동하는 레이어다.

  두 가지 Injector:
    ① CollisionFocusInjector — 충돌이 감지된 씬용
       hidden_intent: 각 인물의 비공개 목표 + 상대 모름을 명시
       emotional_pressure: 기존값 + tension_boost (max 1.0 clamp)
       micro_context: 교차 서술 힌트 (독자는 알지만 인물은 모름)

    ② UnawareFocusInjector — 순수 동시성(미인지) 씬용
       인물들이 서로를 모르는 채 같은 방향으로 움직이는 씬.
       서스펜스 빌드업 (충돌 직전 단계) 에 사용.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from literary_system.orchestrators.character_intent_agent import (
    ActionType,
    IntentPacket,
)
from literary_system.orchestrators.concurrent_action_resolver import (
    CollisionEvent,
    CollisionType,
)
from literary_system.orchestrators.scene_focus_injector import (
    SceneFocusContext,
    SceneFocusInjector,
)
from literary_system.orchestrators.sequence_planner import SequencePlan

# ────────────────────────────────────────────────────────────────
# CollisionSceneFocusContext — 충돌 씬 전용 컨텍스트
# ────────────────────────────────────────────────────────────────

@dataclass
class CollisionSceneFocusContext(SceneFocusContext):
    """
    SceneFocusContext 확장 — 충돌 씬에만 추가되는 필드.
    기존 SceneGenerationOrchestrator의 build() 호출과 완전 호환.
    """
    collision_event:   CollisionEvent | None = None
    collision_type:    str   = ""      # CollisionType 문자열
    unaware_chars:     list  = None    # 상대의 행동을 모르는 인물 목록
    cross_cut_hint:    str   = ""      # 교차편집 힌트 (LLM에게 전달)

    def __post_init__(self):
        if self.unaware_chars is None:
            self.unaware_chars = []


# ────────────────────────────────────────────────────────────────
# CollisionFocusInjector
# ────────────────────────────────────────────────────────────────

class CollisionFocusInjector(SceneFocusInjector):
    """
    충돌이 감지된 씬의 컨텍스트를 구성한다.
    SceneFocusInjector를 상속하여 기존 필드를 그대로 활용하고,
    충돌 특화 필드를 추가로 채운다.
    """

    def build_collision(
        self,
        seq_plan:        SequencePlan,
        scene_idx:       int,
        total_scenes:    int,
        collision_event: CollisionEvent,
        character_states: dict[str, Any] | None = None,
        scene_id:        str | None = None,
    ) -> CollisionSceneFocusContext:
        """
        충돌 씬 전용 컨텍스트 빌드.

        Args:
            seq_plan:         현재 시퀀스 플랜
            scene_idx:        씬 인덱스 (0-based)
            total_scenes:     시퀀스 내 총 씬 수
            collision_event:  ConcurrentActionResolver가 탐지한 충돌
            character_states: 인물 상태 dict
            scene_id:         직접 지정 (None이면 자동 생성)

        Returns:
            CollisionSceneFocusContext — emotional_pressure·hidden_intent 확장됨
        """
        # 기존 SceneFocusContext 빌드 (base)
        base: SceneFocusContext = self.build(
            seq_plan        = seq_plan,
            scene_index          = scene_idx,
            total_scenes_in_seq  = total_scenes,
            character_states= character_states,
            scene_id        = scene_id,
        )

        # ── emotional_pressure 상승 ──────────────────────────
        boosted_pressure = min(
            1.0,
            base.emotional_pressure + collision_event.tension_boost,
        )

        # ── hidden_intent 확장 — 각자가 모르는 상대의 목표 ──
        hidden = self._build_collision_hidden_intent(
            collision_event, character_states or {}
        )

        # ── micro_context 교차 편집 힌트 ─────────────────────
        micro  = self._build_cross_cut_context(base.micro_context, collision_event)

        # ── cross_cut_hint ────────────────────────────────────
        hint   = self._build_cross_cut_hint(collision_event)

        return CollisionSceneFocusContext(
            # SceneFocusContext 기존 필드
            scene_id          = base.scene_id,
            temporal_delta    = base.temporal_delta,
            emotional_pressure= boosted_pressure,
            hidden_intent     = hidden,
            retrieved_docs    = base.retrieved_docs,
            micro_context     = micro,
            # 충돌 확장 필드
            collision_event   = collision_event,
            collision_type    = collision_event.collision_type.value,
            unaware_chars     = list(collision_event.participants),
            cross_cut_hint    = hint,
        )

    # ── hidden_intent 구성 ────────────────────────────────────

    def _build_collision_hidden_intent(
        self,
        event:            CollisionEvent,
        character_states: dict[str, Any],
    ) -> str:
        """
        각 인물이 상대의 행동을 모른 채 자신의 목표만 추구한다는 것을 명시.
        독자(LLM)는 두 의도를 모두 알지만, 인물들은 모른다.
        """
        lines = []
        for intent in event.intents:
            cid    = intent.character_id
            goal   = intent.goal_fragment or character_states.get(
                cid, {}
            ).get("intent", "미정")
            action = intent.action_type.value
            loc    = intent.location

            lines.append(
                f"[{cid}] → 목표: {goal} / 행동: {action} / 장소: {loc}"
                f" ← 상대의 이 계획을 모름"
            )

        collision_label = {
            CollisionType.LOCATION_CLASH: "물리적 조우 예정",
            CollisionType.GOAL_CONFLICT:  "목표 충돌 예정",
            CollisionType.RESOURCE_RACE:  "동일 대상 쟁탈 예정",
        }.get(event.collision_type, "충돌 예정")

        return "\n".join(lines) + f"\n※ 상황: {collision_label}"

    # ── micro_context 교차편집 힌트 ──────────────────────────

    def _build_cross_cut_context(
        self,
        base_micro:  str,
        event:       CollisionEvent,
    ) -> str:
        """기존 micro_context에 교차편집 서사 힌트를 추가한다."""
        participants = "·".join(event.participants)
        hint = (
            f"\n[교차편집] {participants}의 행동이 [{event.location}]에서 "
            f"교차된다. 시간 겹침: "
            f"{event.time_overlap[0]:.2f}~{event.time_overlap[1]:.2f}"
        )
        return base_micro + hint

    def _build_cross_cut_hint(self, event: CollisionEvent) -> str:
        """ClaudeAdapter에 전달할 짧은 교차편집 지시문."""
        type_hint = {
            CollisionType.LOCATION_CLASH:
                "두 인물이 같은 장소에서 마주치는 순간을 클라이맥스로 서술하라",
            CollisionType.GOAL_CONFLICT:
                "한 인물의 행동이 다른 인물의 목표를 방해하는 긴장을 서술하라",
            CollisionType.RESOURCE_RACE:
                "같은 대상을 향해 두 인물이 동시에 접근하는 경쟁을 서술하라",
        }.get(event.collision_type, "충돌의 긴장을 서술하라")
        return f"[{event.collision_type.value.upper()}] {type_hint}. 충돌 설명: {event.description}"


# ────────────────────────────────────────────────────────────────
# UnawareFocusInjector — 서스펜스 빌드업 씬
# ────────────────────────────────────────────────────────────────

class UnawareFocusInjector(SceneFocusInjector):
    """
    인물들이 서로의 행동을 전혀 모르는 채 각자 움직이는 씬을 위한 Injector.
    충돌이 아직 발생하지 않았지만, 독자는 충돌이 임박함을 안다.
    → 영화·드라마의 '서스펜스 빌드업' 씬에 사용.

    예: 형사와 범인이 서로를 모른 채 같은 골목으로 걸어오는 씬.
    """

    def build_unaware(
        self,
        seq_plan:         SequencePlan,
        scene_idx:        int,
        total_scenes:     int,
        intents:          list[IntentPacket],   # 아직 충돌 미발생 인물들의 의도
        approaching_event: CollisionEvent | None = None,  # 예상 충돌 (선택)
        character_states:  dict[str, Any] | None = None,
        scene_id:          str | None = None,
    ) -> CollisionSceneFocusContext:
        """
        서스펜스 씬 컨텍스트 빌드.
        독자는 알지만 인물들은 모르는 상황을 micro_context에 주입.
        """
        base = self.build(
            seq_plan         = seq_plan,
            scene_index          = scene_idx,
            total_scenes_in_seq  = total_scenes,
            character_states = character_states,
            scene_id         = scene_id,
        )

        # hidden_intent: 각자의 계획을 나열 (상대 모름 명시)
        hidden_lines = []
        for intent in intents:
            hidden_lines.append(
                f"[{intent.character_id}] {intent.action_type.value} → "
                f"{intent.location} (상대 모름)"
            )

        # micro_context: 독자용 서스펜스 힌트
        approaching = ""
        if approaching_event:
            approaching = (
                f"\n[독자 인지 — 인물 미인지] "
                f"{' 와 '.join(approaching_event.participants)}가 "
                f"곧 [{approaching_event.location}]에서 마주친다."
            )

        # 서스펜스는 pressure를 살짝만 올림 (충돌 전 단계)
        suspense_boost = 0.15
        if approaching_event:
            suspense_boost += approaching_event.tension_boost * 0.4

        return CollisionSceneFocusContext(
            scene_id          = base.scene_id,
            temporal_delta    = base.temporal_delta,
            emotional_pressure= min(1.0, base.emotional_pressure + suspense_boost),
            hidden_intent     = "\n".join(hidden_lines),
            retrieved_docs    = base.retrieved_docs,
            micro_context     = base.micro_context + approaching,
            collision_event   = approaching_event,
            collision_type    = "unaware_buildup",
            unaware_chars     = [i.character_id for i in intents],
            cross_cut_hint    = (
                "[서스펜스] 인물들은 서로의 존재를 모른다. "
                "독자만 아는 아이러니를 서술에 반영하라."
            ),
        )
