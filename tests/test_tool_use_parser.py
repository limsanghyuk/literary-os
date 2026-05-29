"""
V573-S3: ToolUseParser 단위 테스트
BUG-3 회귀 방지 — ActionPacketParser → ToolUseParser 수정 후 실제 기능 검증

TC-01: ToolUseParser 임포트 가능 (BUG-3 회귀 방지)
TC-02: parse_tool_input — 정상 입력 파싱
TC-03: parse_raw_response — dict 형태 응답 파싱
TC-04: parse_raw_response — tool_use 블록 없을 때 fallback 패킷 반환
"""

from __future__ import annotations

import pytest


# ─── TC-01: 임포트 성공 (BUG-3 회귀 방지) ─────────────────────────────────
def test_tool_use_parser_tc01_import():
    """TC-01: tool_use_parser 모듈에서 ToolUseParser를 정상 임포트."""
    # BUG-3: ActionPacketParser → ToolUseParser 수정 후 임포트 가능해야 함
    from literary_system.llm_bridge.tool_use_parser import ToolUseParser
    parser = ToolUseParser()
    assert parser is not None

    # 3개 어댑터 파일의 임포트 패턴도 직접 검증
    from literary_system.llm_bridge.openai_compatible_adapter import OpenAICompatibleAdapter
    from literary_system.llm_bridge.llm_node_router import LLMNodeRouter
    from literary_system.llm_bridge.physics_aware_router import PhysicsAwareRouter
    assert OpenAICompatibleAdapter is not None
    assert LLMNodeRouter is not None
    assert PhysicsAwareRouter is not None


# ─── TC-02: parse_tool_input 정상 파싱 ────────────────────────────────────
def test_tool_use_parser_tc02_parse_tool_input():
    """TC-02: 정상 tool_input dict → ActionPacket 반환."""
    from literary_system.llm_bridge.tool_use_parser import ToolUseParser

    parser = ToolUseParser()
    tool_input = {
        "narrative_text": "고애신이 교회로 이동한다.",
        "actions": [
            {"actor": "고애신", "action_type": "MOVE", "location": "교회"},
            {"actor": "유진", "action_type": "INTERACT", "target": "고애신"},
        ],
        "literary_state": {"SP": 0.72, "RU": 0.45, "ET": 0.60, "RD": 0.55},
    }
    packet = parser.parse_tool_input(tool_input)

    assert packet.narrative_text == "고애신이 교회로 이동한다."
    assert len(packet.actions) == 2
    assert packet.actions[0].actor == "고애신"
    assert packet.actions[0].action_type == "MOVE"
    assert packet.actions[1].actor == "유진"
    assert packet.literary_state == {"SP": 0.72, "RU": 0.45, "ET": 0.60, "RD": 0.55}
    assert packet.parse_meta["parse_success"] is True
    assert packet.parse_meta["method"] == "tool_use"


# ─── TC-03: parse_raw_response — dict 형태 ─────────────────────────────────
def test_tool_use_parser_tc03_parse_raw_response_dict():
    """TC-03: dict 형태 response → ActionPacket 반환."""
    from literary_system.llm_bridge.tool_use_parser import ToolUseParser, TOOL_NAME  # type: ignore[attr-defined]
    # TOOL_NAME이 export 안 될 수도 있으므로 직접 임포트 시도
    try:
        from literary_system.llm_bridge.scene_draft_tool import TOOL_NAME as _TOOL_NAME
    except ImportError:
        _TOOL_NAME = "literary_scene_draft"

    parser = ToolUseParser()
    response_dict = {
        "content": [
            {
                "type": "tool_use",
                "name": _TOOL_NAME,
                "input": {
                    "narrative_text": "유진이 미국으로 간다.",
                    "actions": [{"actor": "유진", "action_type": "MOVE", "location": "미국"}],
                    "literary_state": {},
                },
            }
        ]
    }
    packet = parser.parse_raw_response(response_dict)

    assert packet.narrative_text == "유진이 미국으로 간다."
    assert len(packet.actions) >= 1


# ─── TC-04: parse_raw_response — tool_use 없을 때 fallback ───────────────
def test_tool_use_parser_tc04_fallback_on_no_tool_use():
    """TC-04: tool_use 블록 없는 응답 → fallback ActionPacket (parse_success=False)."""
    from literary_system.llm_bridge.tool_use_parser import ToolUseParser

    parser = ToolUseParser()
    response_dict = {"text": "일반 텍스트 응답", "content": []}
    packet = parser.parse_raw_response(response_dict)

    # fallback 패킷 — parse_success=False, actions=[]
    assert packet.actions == []
    assert packet.parse_meta["parse_success"] is False
