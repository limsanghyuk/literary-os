"""
V323 — ActionPacket & ActionPacketParser
Layer 1.5: LLM 출력 -> 구조화된 ActionPacket 변환

설계 원칙 (CSA/CSC/CPE 합의):
  - LLM 호출 0회. 정규식 + JSON 파싱만 사용.
  - Gemini CompilerPayload 개념 재해석:
      CompilerPayload(narrative_text, actions[]) ->
      ActionPacket(narrative_text, actions[], literary_state, parse_meta)
  - 액션 타입 5종: MOVE / INTERACT / ACQUIRE / REVEAL / HIDE
  - 파싱 실패 시 raw_text fallback (서비스 중단 방지)
  - V322 RelationGraphStore.StoryNode와 완전 호환

출처: Gemini 진영 ShadowRunSimulator / CompilerPayload 재해석
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ─────────────────────────────────────────────────────────────────
# 액션 타입
# ─────────────────────────────────────────────────────────────────

class ActionType(str, Enum):
    MOVE     = "MOVE"      # 인물 이동
    INTERACT = "INTERACT"  # 인물 간 상호작용 (공간 제약 적용)
    ACQUIRE  = "ACQUIRE"   # 오브젝트 획득
    REVEAL   = "REVEAL"    # 정보 공개 (ForbiddenRevealScanner 연동)
    HIDE     = "HIDE"      # 정보 은폐


# ─────────────────────────────────────────────────────────────────
# 데이터 클래스
# ─────────────────────────────────────────────────────────────────

@dataclass
class Action:
    """
    LLM 생성 텍스트에서 추출된 단일 인물 행동.
    V322 RelationGraphStore의 StoryNode/StoryEdge와 연계.
    """
    actor: str                        # 행동 주체 인물명
    action_type: str                  # ActionType 값
    target: str | None = None         # 대상 인물 또는 오브젝트명
    location: str | None = None       # 목적지 (MOVE 전용)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "actor": self.actor,
            "action_type": self.action_type,
            "target": self.target,
            "location": self.location,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Action":
        return cls(
            actor=d.get("actor", ""),
            action_type=d.get("action_type", "INTERACT"),
            target=d.get("target"),
            location=d.get("location"),
            metadata=d.get("metadata", {}),
        )


@dataclass
class ActionPacket:
    """
    V323 Layer 1.5 핵심 데이터 구조.
    LLM render_output을 구조화된 패킷으로 변환한 결과.

    Gemini CompilerPayload 재해석:
      - narrative_text: 실제 서사 텍스트
      - actions: 추출된 인물 행동 목록 (SpatialConstraintGate 입력)
      - literary_state: V312 LiteraryStateVector (있으면 그대로 전달)
      - parse_meta: 파싱 품질 정보
    """
    narrative_text: str
    actions: list[Action] = field(default_factory=list)
    literary_state: dict[str, Any] = field(default_factory=dict)
    parse_meta: dict[str, Any] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        """파싱 성공 여부."""
        return self.parse_meta.get("parse_success", False)

    @property
    def action_count(self) -> int:
        return len(self.actions)

    def to_dict(self) -> dict[str, Any]:
        return {
            "narrative_text": self.narrative_text,
            "actions": [a.to_dict() for a in self.actions],
            "literary_state": self.literary_state,
            "parse_meta": self.parse_meta,
        }


# ─────────────────────────────────────────────────────────────────
# ActionPacketParser
# ─────────────────────────────────────────────────────────────────

class ActionPacketParser:
    """
    V323 Layer 1.5 — LLM 출력 -> ActionPacket 변환기.

    지원하는 LLM 출력 형식:
      1. JSON 블록 포함: ```json {"narrative_text":..., "actions":[...]} ```
      2. YAML-like 태그: <action type="MOVE" actor="김민준" location="서울역"/>
      3. 괄호 표기:  [MOVE: 김민준 -> 서울역], [INTERACT: 김민준 & 이서연]
      4. fallback: 액션 없이 전체 텍스트를 narrative_text로 처리

    LLM 호출 0회. 완전 로컬.
    """

    # 정규식 패턴
    _JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
    _XML_ACTION = re.compile(
        r'<action\s+([^>]+)/>', re.IGNORECASE
    )
    _BRACKET_ACTION = re.compile(
        r'\[(?P<type>MOVE|INTERACT|ACQUIRE|REVEAL|HIDE)\s*:\s*(?P<body>[^\]]+)\]',
        re.IGNORECASE,
    )
    _MOVE_ARROW = re.compile(r'(?P<actor>.+?)\s*->\s*(?P<location>.+)')
    _INTERACT_AMP = re.compile(r'(?P<a1>.+?)\s*[&와과]\s*(?P<a2>.+)')
    _ATTR = re.compile(r'(\w+)=["\']([^"\']*)["\']')

    def __init__(self, strict: bool = False):
        """
        Args:
            strict: True이면 파싱 실패 시 ValueError 발생. False이면 fallback.
        """
        self.strict = strict

    def parse(
        self,
        render_output: str | dict[str, Any],
        literary_state: dict[str, Any] | None = None,
    ) -> ActionPacket:
        """
        V312Bridge render_output -> ActionPacket.

        Args:
            render_output: V312 렌더링 결과 (str 또는 dict)
            literary_state: V312 LiteraryStateVector (선택)

        Returns:
            ActionPacket
        """
        lit_state = literary_state or {}

        # dict 입력 처리
        if isinstance(render_output, dict):
            text = render_output.get("text", render_output.get("output", ""))
            if not lit_state:
                lit_state = render_output.get("literary_state", {})
        else:
            text = str(render_output)

        # 파싱 시도 (우선순위 순)
        actions, method = self._try_json_block(text)
        if not actions:
            actions, method = self._try_xml_tags(text)
        if not actions:
            actions, method = self._try_bracket_notation(text)

        parse_success = len(actions) > 0
        if not parse_success and self.strict:
            raise ValueError(
                f"ActionPacketParser: 액션 추출 실패. 텍스트 길이={len(text)}"
            )

        # narrative_text: JSON 파싱 성공 시 narrative_text 필드, 아니면 전체 텍스트
        narrative = self._extract_narrative(text, method)

        return ActionPacket(
            narrative_text=narrative,
            actions=actions,
            literary_state=lit_state,
            parse_meta={
                "parse_success": parse_success,
                "parse_method": method,
                "action_count": len(actions),
                "raw_length": len(text),
            },
        )

    # ── 파싱 방법 1: JSON 블록 ────────────────────────────────────

    def _try_json_block(self, text: str) -> tuple[list[Action], str]:
        m = self._JSON_BLOCK.search(text)
        if not m:
            # JSON 블록 없이 전체가 JSON인 경우
            stripped = text.strip()
            if stripped.startswith("{") and stripped.endswith("}"):
                m_obj = stripped
            else:
                return [], ""
        else:
            m_obj = m.group(1)

        try:
            data = json.loads(m_obj if isinstance(m_obj, str) else m_obj)
            raw_actions = data.get("actions", [])
            actions = [Action.from_dict(a) for a in raw_actions if isinstance(a, dict)]
            return actions, "json_block"
        except (json.JSONDecodeError, Exception):
            return [], ""

    # ── 파싱 방법 2: XML 태그 ────────────────────────────────────

    def _try_xml_tags(self, text: str) -> tuple[list[Action], str]:
        actions = []
        for m in self._XML_ACTION.finditer(text):
            attrs = dict(self._ATTR.findall(m.group(1)))
            action_type = attrs.get("type", "INTERACT").upper()
            actor = attrs.get("actor", "")
            if not actor:
                continue
            actions.append(Action(
                actor=actor,
                action_type=action_type,
                target=attrs.get("target"),
                location=attrs.get("location"),
                metadata={k: v for k, v in attrs.items()
                          if k not in ("type", "actor", "target", "location")},
            ))
        return actions, "xml_tags" if actions else ""

    # ── 파싱 방법 3: 괄호 표기 ────────────────────────────────────

    def _try_bracket_notation(self, text: str) -> tuple[list[Action], str]:
        actions = []
        for m in self._BRACKET_ACTION.finditer(text):
            action_type = m.group("type").upper()
            body = m.group("body").strip()

            if action_type == "MOVE":
                mv = self._MOVE_ARROW.match(body)
                if mv:
                    actions.append(Action(
                        actor=mv.group("actor").strip(),
                        action_type=action_type,
                        location=mv.group("location").strip(),
                    ))
                else:
                    parts = body.split()
                    if parts:
                        actions.append(Action(actor=parts[0], action_type=action_type))

            elif action_type == "INTERACT":
                ia = self._INTERACT_AMP.match(body)
                if ia:
                    actions.append(Action(
                        actor=ia.group("a1").strip(),
                        action_type=action_type,
                        target=ia.group("a2").strip(),
                    ))
                else:
                    parts = [p.strip() for p in re.split(r"[,\s]+", body) if p.strip()]
                    if parts:
                        actions.append(Action(
                            actor=parts[0],
                            action_type=action_type,
                            target=parts[1] if len(parts) > 1 else None,
                        ))

            else:  # ACQUIRE, REVEAL, HIDE
                parts = [p.strip() for p in re.split(r"[,\s]+", body) if p.strip()]
                if parts:
                    actions.append(Action(
                        actor=parts[0],
                        action_type=action_type,
                        target=parts[1] if len(parts) > 1 else None,
                    ))

        return actions, "bracket_notation" if actions else ""

    def _extract_narrative(self, text: str, method: str) -> str:
        """서사 텍스트 추출."""
        if method == "json_block":
            # JSON 블록에서 narrative_text 필드 추출 시도
            m = self._JSON_BLOCK.search(text)
            if m:
                try:
                    data = json.loads(m.group(1))
                    if "narrative_text" in data:
                        return data["narrative_text"]
                except Exception:
                    pass
            # JSON 블록 제거 후 나머지를 narrative로
            return self._JSON_BLOCK.sub("", text).strip()

        if method == "xml_tags":
            return self._XML_ACTION.sub("", text).strip()

        if method == "bracket_notation":
            return self._BRACKET_ACTION.sub("", text).strip()

        # fallback: 전체 텍스트
        return text.strip()
