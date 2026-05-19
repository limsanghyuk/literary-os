"""
V326 - CharacterIntentAgent  (동시성 서사 엔진 — Phase 1)

【설계 원리】
  이야기 안의 인물들은 서로의 다음 행동을 모른 채 동시에 의사결정을 내린다.
  바둑의 '동시 착수'와 같은 원리 — 각자의 정보(known_world)만으로 IntentPacket을 제출.

  핵심 특성:
    - 인물 A는 인물 B의 IntentPacket을 볼 수 없다 (비공개 의사결정)
    - asyncio.gather()로 모든 인물을 병렬 실행 → 진정한 동시성 구현
    - LLM 1회/인물 (MockBridge 대응 포함)
    - ConcurrentActionResolver가 이 패킷들을 받아 충돌을 탐지한다

  출력 단위: IntentPacket — 인물의 다음 행동 계획서
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ────────────────────────────────────────────────────────────────
# ActionType — 인물이 취할 수 있는 행동 유형
# ────────────────────────────────────────────────────────────────

class IntentActionType(str, Enum):
    MOVE        = "move"         # 이동 — 장소를 바꾼다
    CONFRONT    = "confront"     # 대립 — 특정 대상에게 다가가 맞선다
    ACQUIRE     = "acquire"      # 획득 — 물건·정보·사람을 얻으려 한다
    CONCEAL     = "conceal"      # 은폐 — 정보·증거·자신을 숨긴다
    WAIT        = "wait"         # 대기 — 그 자리에서 관찰한다
    COMMUNICATE = "communicate"  # 소통 — 누군가에게 메시지를 전달한다
    ESCAPE      = "escape"       # 도주 — 현재 장소·상황에서 벗어난다
    PLAN        = "plan"         # 계획 — 다음 행동을 내부적으로 준비한다


# ────────────────────────────────────────────────────────────────
# IntentPacket — 인물의 의사결정 결과물
# ────────────────────────────────────────────────────────────────

@dataclass
class IntentPacket:
    """
    인물 한 명의 '다음 행동 계획서'.

    비공개 의사결정: 생성 시점에 다른 인물의 패킷을 모른다.
    ConcurrentActionResolver가 여러 IntentPacket을 모아 충돌을 탐지한다.
    """
    character_id:  str            # 인물 ID (예: "고애신", "유진")
    action_type:   ActionType     # 행동 유형
    location:      str            # 행동 장소 (예: "정동 교회", "한성 거리")
    time_start:    float          # 씬 내 상대 시간 시작 (0.0 ~ 1.0)
    time_end:      float          # 씬 내 상대 시간 종료 (0.0 ~ 1.0)
    target:        str  = ""      # 행동 대상 (인물ID / 물건명 / "")
    goal_fragment: str  = ""      # 이 행동이 달성하려는 목표 조각
    known_world:   dict = field(default_factory=dict)   # 인물이 아는 세계 상태
    confidence:    float= 1.0     # 행동 실행 확신도 (0~1)
    raw_response:  str  = ""      # LLM 원본 응답 (디버그용)

    # ── 직렬화 ─────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "character_id":  self.character_id,
            "action_type":   self.action_type.value,
            "location":      self.location,
            "time_start":    round(self.time_start, 4),
            "time_end":      round(self.time_end,   4),
            "target":        self.target,
            "goal_fragment": self.goal_fragment,
            "confidence":    round(self.confidence, 4),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "IntentPacket":
        return cls(
            character_id  = d["character_id"],
            action_type   = ActionType(d.get("action_type", "wait")),
            location      = d.get("location", ""),
            time_start    = float(d.get("time_start", 0.0)),
            time_end      = float(d.get("time_end",   1.0)),
            target        = d.get("target", ""),
            goal_fragment = d.get("goal_fragment", ""),
            confidence    = float(d.get("confidence", 1.0)),
        )


# ────────────────────────────────────────────────────────────────
# CharacterIntentAgent — 인물 1명의 의사결정 에이전트
# ────────────────────────────────────────────────────────────────

# LLM에게 전달할 의도 결정 프롬프트 템플릿
_INTENT_PROMPT_TEMPLATE = """당신은 드라마 인물 '{character_id}'입니다.

[현재 상황]
- 당신이 알고 있는 세계: {known_world_str}
- 당신의 현재 목표: {personal_goal}
- 현재 장소: {current_location}
- 씬 긴장도: {tension:.2f}

[규칙]
- 다른 인물의 행동 계획은 알 수 없습니다
- 당신의 목표에 가장 합리적인 다음 행동 하나를 선택하십시오

[출력 형식 — JSON 한 줄]
{{"action_type":"move|confront|acquire|conceal|wait|communicate|escape|plan",
  "location":"행동 장소",
  "time_start":0.0,"time_end":0.3,
  "target":"대상(없으면 빈 문자열)",
  "goal_fragment":"이 행동으로 달성하려는 것",
  "confidence":0.0~1.0}}"""


class CharacterIntentAgent:
    """
    인물 1명의 의사결정 에이전트.

    bridge.generate()를 통해 LLM에게 의도를 물어보고,
    응답을 IntentPacket으로 파싱하여 반환한다.
    """

    def __init__(
        self,
        character_id:    str,
        personal_goal:   str,
        current_location: str,
        known_world:     dict[str, Any] | None = None,
        bridge=None,       # LLMBridgeInterface (None이면 로컬 휴리스틱)
    ) -> None:
        self.character_id     = character_id
        self.personal_goal    = personal_goal
        self.current_location = current_location
        self.known_world      = known_world or {}
        self.bridge           = bridge

    # ── 동기 결정 (테스트·간단 호출용) ────────────────────────

    def decide_sync(self, tension: float = 0.5) -> IntentPacket:
        """동기 버전 — bridge가 None이거나 Mock일 때도 동작."""
        if self.bridge is None:
            return self._heuristic_intent(tension)

        prompt = _INTENT_PROMPT_TEMPLATE.format(
            character_id    = self.character_id,
            known_world_str = json.dumps(self.known_world, ensure_ascii=False),
            personal_goal   = self.personal_goal,
            current_location= self.current_location,
            tension         = tension,
        )
        try:
            raw = self.bridge.generate(prompt)
            return self._parse_response(raw)
        except Exception:
            return self._heuristic_intent(tension)

    # ── 비동기 결정 (asyncio.gather() 병렬 실행용) ────────────

    async def decide(self, tension: float = 0.5) -> IntentPacket:
        """
        비동기 버전 — ConcurrentIntentCollector.gather_all()에서 호출.
        실제 비동기 LLM이 없을 경우 동기 버전을 await로 래핑.
        """
        loop = asyncio.get_event_loop()
        # run_in_executor로 동기 bridge 호출을 비동기화 (CPU 차단 방지)
        return await loop.run_in_executor(None, self.decide_sync, tension)

    # ── 내부 파싱 ──────────────────────────────────────────────

    def _parse_response(self, raw: str) -> IntentPacket:
        """LLM 응답 JSON → IntentPacket."""
        raw = raw.strip()
        # 응답 안의 JSON 추출 시도
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                d = json.loads(raw[start:end])
                d["character_id"] = self.character_id
                d.setdefault("location", self.current_location)
                packet = IntentPacket.from_dict(d)
                packet.known_world  = self.known_world
                packet.raw_response = raw
                return packet
            except (json.JSONDecodeError, KeyError, ValueError):
                pass
        return self._heuristic_intent(0.5)

    def _heuristic_intent(self, tension: float) -> IntentPacket:
        """
        LLM 없이 목표 문자열 기반 로컬 휴리스틱.
        테스트 환경 / MockBridge / 파싱 실패 시 폴백.
        """
        goal_lower = self.personal_goal.lower()

        # 목표 키워드 → 행동 유형 매핑
        if any(k in goal_lower for k in ("도주", "탈출", "피하", "도망")):
            action = ActionType.ESCAPE
        elif any(k in goal_lower for k in ("공격", "저격", "대립", "맞서")):
            action = ActionType.CONFRONT
        elif any(k in goal_lower for k in ("숨기", "은폐", "감추")):
            action = ActionType.CONCEAL
        elif any(k in goal_lower for k in ("얻", "획득", "찾", "가져")):
            action = ActionType.ACQUIRE
        elif any(k in goal_lower for k in ("전달", "알리", "연락", "소통")):
            action = ActionType.COMMUNICATE
        elif tension > 0.7:
            action = ActionType.CONFRONT
        else:
            action = ActionType.WAIT

        return IntentPacket(
            character_id  = self.character_id,
            action_type   = action,
            location      = self.current_location,
            time_start    = 0.0,
            time_end      = 0.4 + 0.4 * tension,
            target        = "",
            goal_fragment = self.personal_goal,
            known_world   = self.known_world,
            confidence    = 0.75,
        )


# ────────────────────────────────────────────────────────────────
# ConcurrentIntentCollector — N명 에이전트 병렬 실행기
# ────────────────────────────────────────────────────────────────

class ConcurrentIntentCollector:
    """
    여러 CharacterIntentAgent를 asyncio.gather()로 동시에 실행해
    IntentPacket 목록을 수집한다.

    사용 예:
        agents = [
            CharacterIntentAgent("고애신", "일본군 저격", "정동 교회"),
            CharacterIntentAgent("유진",   "고애신 보호", "한성 거리"),
        ]
        collector = ConcurrentIntentCollector(agents)
        packets   = collector.collect_sync(tension=0.7)
        # → [IntentPacket(고애신, CONFRONT, ...), IntentPacket(유진, MOVE, ...)]
    """

    def __init__(self, agents: list[CharacterIntentAgent]) -> None:
        self.agents = agents

    # ── 동기 래퍼 (테스트·단일 스레드 환경) ──────────────────

    def collect_sync(self, tension: float = 0.5) -> list[IntentPacket]:
        """이벤트 루프 없이도 동작하는 동기 래퍼."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Jupyter / 중첩 이벤트 루프 환경
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    futures = [
                        pool.submit(a.decide_sync, tension) for a in self.agents
                    ]
                    return [f.result() for f in futures]
            else:
                return loop.run_until_complete(self._gather(tension))
        except RuntimeError:
            # 루프 없음 — 새로 생성
            return asyncio.run(self._gather(tension))

    # ── 비동기 버전 ────────────────────────────────────────────

    async def collect(self, tension: float = 0.5) -> list[IntentPacket]:
        """async 환경에서 직접 await 가능."""
        return await self._gather(tension)

    async def _gather(self, tension: float) -> list[IntentPacket]:
        return list(await asyncio.gather(
            *[agent.decide(tension) for agent in self.agents]
        ))

    # ── 유틸 ──────────────────────────────────────────────────

    def agent_count(self) -> int:
        return len(self.agents)

    def character_ids(self) -> list[str]:
        return [a.character_id for a in self.agents]

ActionType = IntentActionType  # V579 backward-compat alias
