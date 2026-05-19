"""
V325 - SceneDraftTool  (Phase 1)
Anthropic Tool Use API용 씬 초안 제출 스키마.

설계 원칙 (P2 외과적 통합, P3 LLM 0회):
  - ClaudeAdapter가 tools=[SceneDraftTool] 형태로 Anthropic API에 전달
  - Claude가 반드시 이 도구를 호출하도록 tool_choice={"type": "tool"} 강제
  - narrative_text + actions[] + literary_state 구조를 JSON으로 100% 보장
  - 파싱 실패 원천 차단 (특수문자·중괄호 대사 안전)
  - ToolUseParser가 tool_use 블록을 ActionPacket으로 변환
"""
from __future__ import annotations

from typing import Any

# ────────────────────────────────────────────────────────────────
# SceneDraftTool 정의 (Anthropic tools 파라미터 형식)
# ────────────────────────────────────────────────────────────────

SCENE_DRAFT_TOOL: dict[str, Any] = {
    "name": "submit_scene_draft",
    "description": (
        "씬 초안을 제출합니다. "
        "narrative_text에 완성된 씬 텍스트를 작성하고, "
        "actions 배열에 각 인물의 행동을 기록하세요. "
        "이 도구를 반드시 호출해야 합니다."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "narrative_text": {
                "type": "string",
                "description": "완성된 씬 텍스트 (대사 + 지문 포함). 작가의 문체를 살려 작성하세요.",
            },
            "actions": {
                "type": "array",
                "description": "씬에서 발생하는 인물 행동 목록",
                "items": {
                    "type": "object",
                    "properties": {
                        "actor": {
                            "type": "string",
                            "description": "행동 주체 인물명",
                        },
                        "action_type": {
                            "type": "string",
                            "enum": ["MOVE", "INTERACT", "ACQUIRE", "REVEAL", "HIDE"],
                            "description": "행동 유형",
                        },
                        "target": {
                            "type": "string",
                            "description": "대상 인물 또는 오브젝트 (선택)",
                        },
                        "location": {
                            "type": "string",
                            "description": "이동 목적지 — MOVE 전용 (선택)",
                        },
                    },
                    "required": ["actor", "action_type"],
                },
            },
            "literary_state": {
                "type": "object",
                "description": "씬 종료 후 Literary State 추정값 (선택)",
                "properties": {
                    "SP": {"type": "number", "description": "Scene Pressure [0,1]"},
                    "RU": {"type": "number", "description": "Reveal Budget Used [0,1]"},
                    "ET": {"type": "number", "description": "Emotional Tension [0,1]"},
                    "RD": {"type": "number", "description": "Relational Density [0,1]"},
                },
            },
        },
        "required": ["narrative_text", "actions"],
    },
}


TOOL_NAME = "submit_scene_draft"
