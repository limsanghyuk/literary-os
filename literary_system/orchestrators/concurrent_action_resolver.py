"""
V326 - ConcurrentActionResolver  (동시성 서사 엔진 — Phase 2)

【설계 원리】
  인물들의 IntentPacket을 수집하여 '충돌(Collision)'을 로컬에서 탐지한다.
  LLM 0회 — 순수 로컬 연산 (시간 겹침, 장소 겹침, 목표 상충 판정).

  충돌 유형 3가지:
    ① LOCATION_CLASH  — 같은 장소, 같은 시간대에 두 인물이 동시에 존재
    ② GOAL_CONFLICT   — 한 인물의 행동이 다른 인물의 목표를 직접 방해
    ③ RESOURCE_RACE   — 같은 target(인물·물건)에 두 이상의 인물이 동시 접근

  충돌 결과 → CollisionEvent:
    - tension_boost: SceneFocusInjector emotional_pressure에 가산
    - 서사 압력을 폭발적으로 높이는 원동력

  핵심 설계: resolve()는 모든 충돌 유형을 독립적으로 검사 (short-circuit 금지)
  → LOCATION_CLASH와 GOAL_CONFLICT가 동시에 탐지될 수 있다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from literary_system.orchestrators.character_intent_agent import (
    ActionType,
    IntentPacket,
)

# ────────────────────────────────────────────────────────────────
# CollisionType — 충돌의 성격
# ────────────────────────────────────────────────────────────────

class CollisionType(str, Enum):
    LOCATION_CLASH = "location_clash"  # 같은 장소·시간 → 물리적 조우
    GOAL_CONFLICT  = "goal_conflict"   # 목표 상충 → 의지의 충돌
    RESOURCE_RACE  = "resource_race"   # 같은 대상 경쟁 → 쟁탈전


# 충돌 유형별 기본 tension_boost
_BASE_TENSION_BOOST: dict[CollisionType, float] = {
    CollisionType.LOCATION_CLASH: 0.35,
    CollisionType.GOAL_CONFLICT:  0.25,
    CollisionType.RESOURCE_RACE:  0.30,
}

# CONFRONT 행동이 포함된 충돌은 추가 가산
_CONFRONT_BONUS = 0.15


# ────────────────────────────────────────────────────────────────
# CollisionEvent — 충돌 탐지 결과
# ────────────────────────────────────────────────────────────────

@dataclass
class CollisionEvent:
    """
    두 (이상) 인물 간 충돌 이벤트.

    SceneFocusInjector / CollisionFocusInjector가 이 이벤트를 받아
    씬 컨텍스트의 emotional_pressure와 hidden_intent를 조정한다.
    """
    collision_type:  CollisionType
    participants:    list[str]          # 충돌 당사자 character_id 목록
    location:        str                # 충돌 발생 장소
    time_overlap:    tuple[float, float]# 겹치는 시간 구간
    tension_boost:   float              # emotional_pressure에 가산할 값
    description:     str = ""           # 서사 힌트 (CollisionFocusInjector용)
    intents:         list[IntentPacket] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "collision_type": self.collision_type.value,
            "participants":   self.participants,
            "location":       self.location,
            "time_overlap":   list(self.time_overlap),
            "tension_boost":  round(self.tension_boost, 4),
            "description":    self.description,
        }


# ────────────────────────────────────────────────────────────────
# 충돌 목표 판정 헬퍼
# ────────────────────────────────────────────────────────────────

# 서로 상충하는 행동 쌍 (순서 무관)
_OPPOSING_ACTIONS: set[frozenset[ActionType]] = {
    frozenset({ActionType.CONFRONT, ActionType.ESCAPE}),
    frozenset({ActionType.ACQUIRE,  ActionType.CONCEAL}),
    frozenset({ActionType.CONFRONT, ActionType.CONCEAL}),
    frozenset({ActionType.ACQUIRE,  ActionType.ESCAPE}),
}

# 같은 target을 두고 경쟁하는 행동
_RACE_ACTIONS: set[ActionType] = {
    ActionType.ACQUIRE,
    ActionType.CONFRONT,
    ActionType.COMMUNICATE,
}


def _time_overlap(a: IntentPacket, b: IntentPacket) -> tuple[float, float] | None:
    """두 패킷의 시간 구간이 겹치면 겹침 구간, 아니면 None."""
    lo = max(a.time_start, b.time_start)
    hi = min(a.time_end,   b.time_end)
    return (lo, hi) if lo < hi else None


def _same_location(a: IntentPacket, b: IntentPacket) -> bool:
    """장소 문자열이 실질적으로 같은지 판정 (공백·조사 정규화)."""
    def norm(s: str) -> str:
        return s.strip().replace(" ", "").replace("의", "").replace("에서", "")
    return norm(a.location) == norm(b.location) and a.location != ""


# ────────────────────────────────────────────────────────────────
# ConcurrentActionResolver — 핵심 충돌 탐지 엔진
# ────────────────────────────────────────────────────────────────

class ConcurrentActionResolver:
    """
    N명의 IntentPacket을 받아 충돌을 탐지하고 CollisionEvent 목록을 반환.
    완전 로컬 연산 — LLM 0회.

    사용 예:
        resolver = ConcurrentActionResolver()
        events   = resolver.resolve(packets)
        # → [CollisionEvent(LOCATION_CLASH, ...), CollisionEvent(GOAL_CONFLICT, ...)]

        summary  = resolver.summary(events)
        # → {"total_collisions": 2, "max_tension_boost": 0.50, ...}
    """

    def __init__(
        self,
        location_match_required: bool = True,  # LOCATION_CLASH: 장소 일치 필수
        min_time_overlap:        float = 0.05,  # 최소 시간 겹침 비율
    ) -> None:
        self.location_match_required = location_match_required
        self.min_time_overlap        = min_time_overlap

    # ── 공개 API ─────────────────────────────────────────────

    def resolve(self, packets: list[IntentPacket]) -> list[CollisionEvent]:
        """
        IntentPacket 목록 전체를 분석하여 모든 CollisionEvent를 반환.
        충돌이 없으면 빈 리스트.

        핵심: 세 가지 충돌 유형을 독립적으로 모두 검사 (short-circuit 없음).
        같은 인물 쌍에서 LOCATION_CLASH와 GOAL_CONFLICT가 동시에 탐지될 수 있다.
        """
        if len(packets) < 2:
            return []

        events: list[CollisionEvent] = []

        for i in range(len(packets)):
            for j in range(i + 1, len(packets)):
                a, b = packets[i], packets[j]
                # 세 가지 충돌 유형을 독립적으로 모두 검사
                for check_fn in (
                    self._check_location_clash,
                    self._check_goal_conflict,
                    self._check_resource_race,
                ):
                    ev = check_fn(a, b)
                    if ev is not None:
                        events.append(ev)

        # (참가자 쌍, 충돌 유형) 기준으로 중복만 제거
        return self._deduplicate(events)

    def max_tension_boost(self, events: list[CollisionEvent]) -> float:
        """충돌 목록에서 가장 높은 tension_boost를 반환. 없으면 0.0."""
        return max((e.tension_boost for e in events), default=0.0)

    def total_tension_boost(self, events: list[CollisionEvent]) -> float:
        """모든 충돌의 tension_boost 합산 (최대 0.6으로 clamp)."""
        return min(0.6, sum(e.tension_boost for e in events))

    def summary(self, events: list[CollisionEvent]) -> dict[str, Any]:
        """충돌 요약 dict."""
        by_type: dict[str, int] = {}
        for e in events:
            key = e.collision_type.value
            by_type[key] = by_type.get(key, 0) + 1
        return {
            "total_collisions":  len(events),
            "max_tension_boost": round(self.max_tension_boost(events), 4),
            "total_tension_boost": round(self.total_tension_boost(events), 4),
            "by_type":           by_type,
            "locations":         list({e.location for e in events}),
        }

    # ── 충돌 유형별 탐지 ──────────────────────────────────────

    def _check_location_clash(
        self, a: IntentPacket, b: IntentPacket
    ) -> CollisionEvent | None:
        """
        LOCATION_CLASH:
          같은 장소 + 시간 겹침 + 최소한 한 명이 MOVE 이외 행동
        """
        overlap = _time_overlap(a, b)
        if overlap is None:
            return None
        if overlap[1] - overlap[0] < self.min_time_overlap:
            return None
        if self.location_match_required and not _same_location(a, b):
            return None

        # 두 명이 같은 장소에 있는 것만으로는 충돌 아님 — 최소 한 명이 능동 행동
        active = {ActionType.CONFRONT, ActionType.ACQUIRE,
                  ActionType.CONCEAL, ActionType.COMMUNICATE}
        if a.action_type not in active and b.action_type not in active:
            return None

        boost = _BASE_TENSION_BOOST[CollisionType.LOCATION_CLASH]
        if ActionType.CONFRONT in (a.action_type, b.action_type):
            boost += _CONFRONT_BONUS

        desc = (
            f"{a.character_id}({a.action_type.value})와 "
            f"{b.character_id}({b.action_type.value})가 "
            f"[{a.location}]에서 조우. "
            f"시간 겹침: {overlap[0]:.2f}~{overlap[1]:.2f}"
        )
        return CollisionEvent(
            collision_type = CollisionType.LOCATION_CLASH,
            participants   = [a.character_id, b.character_id],
            location       = a.location,
            time_overlap   = overlap,
            tension_boost  = round(min(boost, 0.6), 4),
            description    = desc,
            intents        = [a, b],
        )

    def _check_goal_conflict(
        self, a: IntentPacket, b: IntentPacket
    ) -> CollisionEvent | None:
        """
        GOAL_CONFLICT:
          행동 유형이 서로 상충하는 쌍 (CONFRONT vs ESCAPE 등)
        """
        overlap = _time_overlap(a, b)
        if overlap is None:
            return None

        pair = frozenset({a.action_type, b.action_type})
        if pair not in _OPPOSING_ACTIONS:
            return None

        boost = _BASE_TENSION_BOOST[CollisionType.GOAL_CONFLICT]
        if ActionType.CONFRONT in (a.action_type, b.action_type):
            boost += _CONFRONT_BONUS

        desc = (
            f"{a.character_id}의 [{a.action_type.value}] ↔ "
            f"{b.character_id}의 [{b.action_type.value}] — 목표 상충"
        )
        loc = a.location if _same_location(a, b) else f"{a.location}↔{b.location}"
        return CollisionEvent(
            collision_type = CollisionType.GOAL_CONFLICT,
            participants   = [a.character_id, b.character_id],
            location       = loc,
            time_overlap   = overlap,
            tension_boost  = round(min(boost, 0.6), 4),
            description    = desc,
            intents        = [a, b],
        )

    def _check_resource_race(
        self, a: IntentPacket, b: IntentPacket
    ) -> CollisionEvent | None:
        """
        RESOURCE_RACE:
          같은 target을 두 인물 이상이 동시에 노린다
        """
        overlap = _time_overlap(a, b)
        if overlap is None:
            return None

        if not a.target or not b.target:
            return None
        if a.target.strip() != b.target.strip():
            return None
        if a.action_type not in _RACE_ACTIONS or b.action_type not in _RACE_ACTIONS:
            return None

        boost = _BASE_TENSION_BOOST[CollisionType.RESOURCE_RACE]
        if ActionType.CONFRONT in (a.action_type, b.action_type):
            boost += _CONFRONT_BONUS

        desc = (
            f"{a.character_id}와 {b.character_id}가 "
            f"동일 대상 [{a.target}]을 동시에 노린다"
        )
        loc = a.location if _same_location(a, b) else f"{a.location}↔{b.location}"
        return CollisionEvent(
            collision_type = CollisionType.RESOURCE_RACE,
            participants   = [a.character_id, b.character_id],
            location       = loc,
            time_overlap   = overlap,
            tension_boost  = round(min(boost, 0.6), 4),
            description    = desc,
            intents        = [a, b],
        )

    # ── 내부 유틸 ─────────────────────────────────────────────

    def _deduplicate(self, events: list[CollisionEvent]) -> list[CollisionEvent]:
        """
        (participants 쌍, 충돌 유형) 기준으로 중복 제거.
        같은 인물 쌍이라도 충돌 유형이 다르면 모두 보존한다.
        같은 유형이 중복 탐지된 경우만 tension_boost가 가장 높은 것을 남긴다.
        """
        seen: dict[tuple, CollisionEvent] = {}
        for ev in events:
            key = (frozenset(ev.participants), ev.collision_type)
            if key not in seen or ev.tension_boost > seen[key].tension_boost:
                seen[key] = ev
        return list(seen.values())
