"""
V326 동시성 서사 엔진 테스트 — 40 케이스 전체 PASS 목표

커버리지:
  [A] IntentPacket 데이터클래스                      (6)
  [B] CharacterIntentAgent — 의사결정 로직           (8)
  [C] ConcurrentIntentCollector — 병렬 실행          (5)
  [D] ConcurrentActionResolver — 충돌 탐지           (12)
  [E] CollisionFocusInjector — 컨텍스트 확장         (5)
  [F] UnawareFocusInjector — 서스펜스 씬             (4)

설계 검증 포인트:
  ✓ 비공개 의사결정: 각 에이전트가 독립적으로 IntentPacket 제출
  ✓ LOCATION_CLASH / GOAL_CONFLICT / RESOURCE_RACE 탐지
  ✓ tension_boost → emotional_pressure 주입
  ✓ LLM 0회 원칙 (resolver 단계는 완전 로컬)
  ✓ CollisionFocusContext가 SceneFocusContext 호환
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from literary_system.orchestrators.character_intent_agent import (
    ActionType,
    IntentPacket,
    CharacterIntentAgent,
    ConcurrentIntentCollector,
)
from literary_system.orchestrators.concurrent_action_resolver import (
    CollisionType,
    CollisionEvent,
    ConcurrentActionResolver,
)
from literary_system.orchestrators.collision_focus_injector import (
    CollisionFocusInjector,
    CollisionSceneFocusContext,
    UnawareFocusInjector,
)
from literary_system.orchestrators.scene_focus_injector import SceneFocusContext
from literary_system.orchestrators.sequence_planner import SequencePlan


# ════════════════════════════════════════════════════════════════
# 공통 픽스처
# ════════════════════════════════════════════════════════════════

def _seq_plan(**kw) -> SequencePlan:
    defaults = dict(
        seq_id="ep01_seq01", episode_no=1, seq_index=1,
        goal="갈등 고조", tension_target=0.65,
        scene_count=4, act_index=2,
        pct_start=0.2, pct_end=0.45,
    )
    defaults.update(kw)
    return SequencePlan(**defaults)


def _packet(
    cid="고애신",
    action=ActionType.CONFRONT,
    location="정동 교회",
    ts=0.1, te=0.5,
    target="",
    goal="일본군 저격",
) -> IntentPacket:
    return IntentPacket(
        character_id=cid, action_type=action,
        location=location, time_start=ts, time_end=te,
        target=target, goal_fragment=goal,
    )


# ════════════════════════════════════════════════════════════════
# [A] IntentPacket 데이터클래스 (6)
# ════════════════════════════════════════════════════════════════

class TestIntentPacket:

    def test_fields_accessible(self):
        """모든 필드가 접근 가능."""
        p = _packet()
        assert p.character_id == "고애신"
        assert p.action_type  == ActionType.CONFRONT
        assert p.location     == "정동 교회"

    def test_to_dict_keys(self):
        """to_dict() 필수 키 포함."""
        d = _packet().to_dict()
        for k in ("character_id","action_type","location",
                  "time_start","time_end","target","goal_fragment","confidence"):
            assert k in d

    def test_to_dict_action_type_is_string(self):
        """action_type이 문자열로 직렬화."""
        d = _packet(action=ActionType.ESCAPE).to_dict()
        assert d["action_type"] == "escape"

    def test_from_dict_roundtrip(self):
        """to_dict → from_dict 왕복."""
        p  = _packet(cid="유진", action=ActionType.MOVE, location="한성 거리")
        p2 = IntentPacket.from_dict(p.to_dict())
        assert p2.character_id == "유진"
        assert p2.action_type  == ActionType.MOVE
        assert p2.location     == "한성 거리"

    def test_time_range_valid(self):
        """time_start < time_end."""
        p = _packet(ts=0.1, te=0.5)
        assert p.time_start < p.time_end

    def test_action_type_enum_values(self):
        """ActionType 7가지 값 모두 유효."""
        for at in ActionType:
            p = _packet(action=at)
            assert p.action_type == at


# ════════════════════════════════════════════════════════════════
# [B] CharacterIntentAgent — 의사결정 로직 (8)
# ════════════════════════════════════════════════════════════════

class TestCharacterIntentAgent:

    def test_decide_sync_returns_intent_packet(self):
        """decide_sync()가 IntentPacket을 반환."""
        agent = CharacterIntentAgent("고애신", "일본군 저격", "정동 교회")
        pkt   = agent.decide_sync(tension=0.7)
        assert isinstance(pkt, IntentPacket)
        assert pkt.character_id == "고애신"

    def test_no_bridge_uses_heuristic(self):
        """bridge=None이면 휴리스틱 폴백."""
        agent = CharacterIntentAgent("유진", "고애신 보호", "한성 거리", bridge=None)
        pkt   = agent.decide_sync(tension=0.5)
        assert pkt.action_type is not None

    def test_heuristic_escape_goal(self):
        """'도주' 키워드 → ESCAPE 행동."""
        agent = CharacterIntentAgent("범인", "도주하여 탈출", "아지트")
        pkt   = agent.decide_sync(tension=0.5)
        assert pkt.action_type == ActionType.ESCAPE

    def test_heuristic_confront_goal(self):
        """'저격' 키워드 → CONFRONT 행동."""
        agent = CharacterIntentAgent("고애신", "일본군 저격", "교회 종탑")
        pkt   = agent.decide_sync(tension=0.5)
        assert pkt.action_type == ActionType.CONFRONT

    def test_heuristic_high_tension_confront(self):
        """긴장도 0.8 이상 + 중립 목표 → CONFRONT 또는 적극 행동."""
        agent = CharacterIntentAgent("X", "목표 달성", "거리")
        pkt   = agent.decide_sync(tension=0.9)
        assert pkt.action_type in (ActionType.CONFRONT, ActionType.WAIT,
                                   ActionType.MOVE, ActionType.COMMUNICATE)

    def test_bridge_mock_called(self):
        """bridge가 있으면 generate() 호출."""
        bridge = MagicMock()
        bridge.generate.return_value = '{"action_type":"wait","location":"교회","time_start":0.0,"time_end":0.3,"target":"","goal_fragment":"대기","confidence":0.9}'
        agent = CharacterIntentAgent("유진", "관찰", "교회", bridge=bridge)
        pkt   = agent.decide_sync()
        bridge.generate.assert_called_once()
        assert isinstance(pkt, IntentPacket)

    def test_bridge_parse_failure_falls_back(self):
        """bridge가 파싱 불가 응답 → 휴리스틱 폴백."""
        bridge = MagicMock()
        bridge.generate.return_value = "파싱 불가 응답"
        agent  = CharacterIntentAgent("A", "도주하여 탈출", "거리", bridge=bridge)
        pkt    = agent.decide_sync()
        assert isinstance(pkt, IntentPacket)

    def test_character_id_preserved_through_bridge(self):
        """bridge 파싱 후에도 character_id가 에이전트 설정값으로 고정."""
        bridge = MagicMock()
        bridge.generate.return_value = '{"action_type":"move","location":"골목","time_start":0.0,"time_end":0.2,"target":"","goal_fragment":"이동","confidence":1.0}'
        agent  = CharacterIntentAgent("고애신", "이동", "골목", bridge=bridge)
        pkt    = agent.decide_sync()
        assert pkt.character_id == "고애신"


# ════════════════════════════════════════════════════════════════
# [C] ConcurrentIntentCollector — 병렬 실행 (5)
# ════════════════════════════════════════════════════════════════

class TestConcurrentIntentCollector:

    def _make_collector(self, n=2) -> ConcurrentIntentCollector:
        goals = ["일본군 저격", "고애신 보호", "도주하여 탈출", "증거 은폐"]
        locs  = ["정동 교회", "한성 거리", "아지트", "문서 창고"]
        cids  = ["고애신", "유진", "범인", "공범"]
        agents = [
            CharacterIntentAgent(cids[i], goals[i], locs[i])
            for i in range(n)
        ]
        return ConcurrentIntentCollector(agents)

    def test_collect_returns_all_packets(self):
        """collect_sync()가 에이전트 수만큼 패킷 반환."""
        collector = self._make_collector(n=3)
        packets   = collector.collect_sync(tension=0.5)
        assert len(packets) == 3

    def test_all_packets_are_intent_packets(self):
        """반환 목록이 모두 IntentPacket 인스턴스."""
        packets = self._make_collector(n=2).collect_sync()
        assert all(isinstance(p, IntentPacket) for p in packets)

    def test_character_ids_unique(self):
        """각 패킷의 character_id가 고유."""
        packets = self._make_collector(n=4).collect_sync()
        ids = [p.character_id for p in packets]
        assert len(ids) == len(set(ids))

    def test_agent_count(self):
        """agent_count()가 에이전트 수 반환."""
        col = self._make_collector(n=3)
        assert col.agent_count() == 3

    def test_character_ids_list(self):
        """character_ids()가 등록 순서대로 반환."""
        col = self._make_collector(n=2)
        assert col.character_ids() == ["고애신", "유진"]


# ════════════════════════════════════════════════════════════════
# [D] ConcurrentActionResolver — 충돌 탐지 (12)
# ════════════════════════════════════════════════════════════════

class TestConcurrentActionResolver:

    def setup_method(self):
        self.resolver = ConcurrentActionResolver()

    # ── LOCATION_CLASH ────────────────────────────────────────

    def test_location_clash_detected(self):
        """같은 장소·시간 겹침 → LOCATION_CLASH."""
        a = _packet("고애신", ActionType.CONFRONT, "정동 교회", 0.1, 0.6)
        b = _packet("유진",   ActionType.MOVE,     "정동 교회", 0.2, 0.7)
        events = self.resolver.resolve([a, b])
        types  = [e.collision_type for e in events]
        assert CollisionType.LOCATION_CLASH in types

    def test_no_collision_different_locations(self):
        """장소 다르면 LOCATION_CLASH 없음."""
        a = _packet("A", ActionType.CONFRONT, "교회", 0.1, 0.5)
        b = _packet("B", ActionType.MOVE,     "거리", 0.1, 0.5)
        events = self.resolver.resolve([a, b])
        assert not any(e.collision_type == CollisionType.LOCATION_CLASH for e in events)

    def test_no_collision_no_time_overlap(self):
        """시간 겹침 없으면 충돌 없음."""
        a = _packet("A", ActionType.CONFRONT, "교회", 0.0, 0.3)
        b = _packet("B", ActionType.CONFRONT, "교회", 0.5, 0.9)
        events = self.resolver.resolve([a, b])
        assert CollisionType.LOCATION_CLASH not in [e.collision_type for e in events]

    def test_confront_adds_bonus_tension(self):
        """CONFRONT 포함 충돌은 tension_boost 가산."""
        a = _packet("A", ActionType.CONFRONT, "교회", 0.0, 0.8)
        b = _packet("B", ActionType.MOVE,     "교회", 0.1, 0.6)
        events = self.resolver.resolve([a, b])
        clash  = next((e for e in events if e.collision_type == CollisionType.LOCATION_CLASH), None)
        assert clash is not None
        assert clash.tension_boost > 0.35  # 기본 0.35 + CONFRONT_BONUS 0.15

    # ── GOAL_CONFLICT ─────────────────────────────────────────

    def test_goal_conflict_confront_vs_escape(self):
        """CONFRONT ↔ ESCAPE → GOAL_CONFLICT."""
        a = _packet("형사", ActionType.CONFRONT, "아지트", 0.2, 0.7)
        b = _packet("범인", ActionType.ESCAPE,   "아지트", 0.1, 0.6)
        events = self.resolver.resolve([a, b])
        types  = [e.collision_type for e in events]
        assert CollisionType.GOAL_CONFLICT in types

    def test_goal_conflict_acquire_vs_conceal(self):
        """ACQUIRE ↔ CONCEAL → GOAL_CONFLICT."""
        a = _packet("A", ActionType.ACQUIRE, "창고", 0.0, 0.5)
        b = _packet("B", ActionType.CONCEAL, "창고", 0.1, 0.4)
        events = self.resolver.resolve([a, b])
        assert any(e.collision_type == CollisionType.GOAL_CONFLICT for e in events)

    def test_same_action_no_goal_conflict(self):
        """같은 행동 유형은 GOAL_CONFLICT 아님."""
        a = _packet("A", ActionType.MOVE, "거리", 0.0, 0.5)
        b = _packet("B", ActionType.MOVE, "거리", 0.1, 0.6)
        events = self.resolver.resolve([a, b])
        assert not any(e.collision_type == CollisionType.GOAL_CONFLICT for e in events)

    # ── RESOURCE_RACE ─────────────────────────────────────────

    def test_resource_race_same_target(self):
        """같은 target → RESOURCE_RACE."""
        a = _packet("A", ActionType.ACQUIRE, "창고", 0.0, 0.5, target="비밀 문서")
        b = _packet("B", ActionType.ACQUIRE, "창고", 0.1, 0.6, target="비밀 문서")
        events = self.resolver.resolve([a, b])
        assert any(e.collision_type == CollisionType.RESOURCE_RACE for e in events)

    def test_resource_race_different_targets(self):
        """target이 다르면 RESOURCE_RACE 아님."""
        a = _packet("A", ActionType.ACQUIRE, "창고", 0.0, 0.5, target="문서")
        b = _packet("B", ActionType.ACQUIRE, "창고", 0.0, 0.5, target="열쇠")
        events = self.resolver.resolve([a, b])
        assert not any(e.collision_type == CollisionType.RESOURCE_RACE for e in events)

    # ── 공통 ─────────────────────────────────────────────────

    def test_no_collision_single_packet(self):
        """인물 1명이면 충돌 없음."""
        events = self.resolver.resolve([_packet()])
        assert events == []

    def test_max_tension_boost(self):
        """max_tension_boost()가 가장 높은 값 반환."""
        a = _packet("A", ActionType.CONFRONT, "교회", 0.0, 0.8)
        b = _packet("B", ActionType.ESCAPE,   "교회", 0.1, 0.7)
        events = self.resolver.resolve([a, b])
        assert self.resolver.max_tension_boost(events) > 0.0

    def test_summary_keys(self):
        """summary()가 필수 키 포함."""
        a = _packet("A", ActionType.CONFRONT, "교회", 0.0, 0.5)
        b = _packet("B", ActionType.ESCAPE,   "교회", 0.1, 0.4)
        events = self.resolver.resolve([a, b])
        s = self.resolver.summary(events)
        for k in ("total_collisions","max_tension_boost","total_tension_boost","by_type"):
            assert k in s


# ════════════════════════════════════════════════════════════════
# [E] CollisionFocusInjector — 컨텍스트 확장 (5)
# ════════════════════════════════════════════════════════════════

class TestCollisionFocusInjector:

    def setup_method(self):
        self.injector = CollisionFocusInjector(rag_bridge=None)
        self.plan     = _seq_plan()
        self.event    = CollisionEvent(
            collision_type = CollisionType.LOCATION_CLASH,
            participants   = ["고애신", "유진"],
            location       = "정동 교회",
            time_overlap   = (0.2, 0.5),
            tension_boost  = 0.35,
            description    = "두 인물이 교회에서 조우",
            intents = [
                _packet("고애신", ActionType.CONFRONT, "정동 교회", 0.1, 0.6, goal="저격"),
                _packet("유진",   ActionType.MOVE,     "정동 교회", 0.2, 0.7, goal="보호"),
            ],
        )

    def test_returns_collision_scene_focus_context(self):
        """build_collision()이 CollisionSceneFocusContext 반환."""
        ctx = self.injector.build_collision(self.plan, 1, 4, self.event)
        assert isinstance(ctx, CollisionSceneFocusContext)

    def test_collision_context_is_scene_focus_context(self):
        """CollisionSceneFocusContext는 SceneFocusContext 호환."""
        ctx = self.injector.build_collision(self.plan, 0, 4, self.event)
        assert isinstance(ctx, SceneFocusContext)

    def test_emotional_pressure_boosted(self):
        """충돌 씬의 emotional_pressure가 기본 씬보다 높다."""
        base_ctx  = self.injector.build(self.plan, 0, 4)
        clash_ctx = self.injector.build_collision(self.plan, 0, 4, self.event)
        assert clash_ctx.emotional_pressure >= base_ctx.emotional_pressure

    def test_hidden_intent_contains_participants(self):
        """hidden_intent에 충돌 당사자가 포함."""
        ctx = self.injector.build_collision(self.plan, 0, 4, self.event)
        assert "고애신" in ctx.hidden_intent
        assert "유진"   in ctx.hidden_intent

    def test_collision_type_field_set(self):
        """collision_type 필드가 정확히 설정."""
        ctx = self.injector.build_collision(self.plan, 0, 4, self.event)
        assert ctx.collision_type == "location_clash"


# ════════════════════════════════════════════════════════════════
# [F] UnawareFocusInjector — 서스펜스 씬 (4)
# ════════════════════════════════════════════════════════════════

class TestUnawareFocusInjector:

    def setup_method(self):
        self.injector = UnawareFocusInjector(rag_bridge=None)
        self.plan     = _seq_plan(tension_target=0.45)
        self.intents  = [
            _packet("형사",   ActionType.MOVE,   "골목", 0.0, 0.4, goal="수색"),
            _packet("용의자", ActionType.ESCAPE, "골목", 0.1, 0.5, goal="도주하여 탈출"),
        ]
        self.approaching = CollisionEvent(
            collision_type = CollisionType.LOCATION_CLASH,
            participants   = ["형사", "용의자"],
            location       = "골목",
            time_overlap   = (0.1, 0.4),
            tension_boost  = 0.30,
            description    = "곧 충돌 예정",
        )

    def test_returns_collision_scene_focus_context(self):
        """build_unaware()가 CollisionSceneFocusContext 반환."""
        ctx = self.injector.build_unaware(self.plan, 0, 4, self.intents)
        assert isinstance(ctx, CollisionSceneFocusContext)

    def test_unaware_chars_populated(self):
        """unaware_chars에 인물 목록 포함."""
        ctx = self.injector.build_unaware(self.plan, 0, 4, self.intents)
        assert "형사" in ctx.unaware_chars
        assert "용의자" in ctx.unaware_chars

    def test_pressure_lower_than_collision(self):
        """서스펜스 씬은 충돌 씬보다 pressure가 낮다."""
        clash_inj = CollisionFocusInjector(rag_bridge=None)
        event = CollisionEvent(
            collision_type=CollisionType.LOCATION_CLASH,
            participants=["형사","용의자"],
            location="골목",
            time_overlap=(0.1,0.4),
            tension_boost=0.30,
            description="충돌",
            intents=self.intents,
        )
        unaware_ctx = self.injector.build_unaware(
            self.plan, 0, 4, self.intents, self.approaching
        )
        clash_ctx   = clash_inj.build_collision(self.plan, 0, 4, event)
        assert unaware_ctx.emotional_pressure <= clash_ctx.emotional_pressure

    def test_cross_cut_hint_present(self):
        """서스펜스 씬에 cross_cut_hint가 존재."""
        ctx = self.injector.build_unaware(
            self.plan, 0, 4, self.intents, self.approaching
        )
        assert len(ctx.cross_cut_hint) > 0
