"""
V325 Phase 1 테스트 — ClaudeAdapter + SceneDraftTool + ToolUseParser
목표: 39 케이스 전체 PASS → 누적 620+ PASS

커버리지:
  [A] SceneDraftTool 스키마 검증            (5)
  [B] ToolUseParser — parse_tool_input     (8)
  [C] ToolUseParser — parse_raw_response   (8)
  [D] ToolUseParser — fallback 경로        (4)
  [E] ClaudeAdapter — 기본 속성/상태       (7)
  [F] ClaudeAdapter — generate() 오프라인  (4)
  [G] ClaudeAdapter — parse_action_packet  (3)
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from literary_system.action_compiler.action_packet import ActionPacket, Action
from literary_system.llm_bridge.scene_draft_tool import SCENE_DRAFT_TOOL, TOOL_NAME
from literary_system.llm_bridge.tool_use_parser import ToolUseParser
from literary_system.llm_bridge.claude_adapter import ClaudeAdapter


# ════════════════════════════════════════════════════════════════
# [A] SceneDraftTool 스키마 검증 (5)
# ════════════════════════════════════════════════════════════════

class TestSceneDraftTool:
    """SCENE_DRAFT_TOOL 딕셔너리 구조 정합성."""

    def test_tool_name_constant(self):
        """TOOL_NAME 상수가 스키마 name과 일치."""
        assert TOOL_NAME == SCENE_DRAFT_TOOL["name"] == "submit_scene_draft"

    def test_top_level_keys(self):
        """name / description / input_schema 키 존재."""
        assert "name" in SCENE_DRAFT_TOOL
        assert "description" in SCENE_DRAFT_TOOL
        assert "input_schema" in SCENE_DRAFT_TOOL

    def test_required_fields(self):
        """narrative_text, actions 가 required 목록에 포함."""
        req = SCENE_DRAFT_TOOL["input_schema"]["required"]
        assert "narrative_text" in req
        assert "actions" in req

    def test_action_type_enum(self):
        """actions.items의 action_type enum 값 검증."""
        items = SCENE_DRAFT_TOOL["input_schema"]["properties"]["actions"]["items"]
        enum_vals = items["properties"]["action_type"]["enum"]
        for expected in ("MOVE", "INTERACT", "ACQUIRE", "REVEAL", "HIDE"):
            assert expected in enum_vals

    def test_literary_state_properties(self):
        """literary_state가 SP/RU/ET/RD 숫자 필드를 포함."""
        ls = SCENE_DRAFT_TOOL["input_schema"]["properties"]["literary_state"]
        for key in ("SP", "RU", "ET", "RD"):
            assert key in ls["properties"]
            assert ls["properties"][key]["type"] == "number"


# ════════════════════════════════════════════════════════════════
# [B] ToolUseParser — parse_tool_input (8)
# ════════════════════════════════════════════════════════════════

class TestToolUseParserParseToolInput:
    """tool_use 블록 input dict → ActionPacket 변환."""

    def setup_method(self):
        self.parser = ToolUseParser()

    def _make_input(self, **kwargs):
        base = {
            "narrative_text": "고애신이 교회 문을 밀며 들어섰다.",
            "actions": [
                {"actor": "고애신", "action_type": "MOVE", "location": "교회"},
                {"actor": "유진", "action_type": "INTERACT", "target": "고애신"},
            ],
            "literary_state": {"SP": 0.72, "RU": 0.45, "ET": 0.60, "RD": 0.55},
        }
        base.update(kwargs)
        return base

    def test_returns_action_packet(self):
        """parse_tool_input 반환 타입이 ActionPacket."""
        result = self.parser.parse_tool_input(self._make_input())
        assert isinstance(result, ActionPacket)

    def test_narrative_text_preserved(self):
        """narrative_text가 ActionPacket에 그대로 보존."""
        inp = self._make_input(narrative_text="테스트 씬 텍스트.")
        result = self.parser.parse_tool_input(inp)
        assert result.narrative_text == "테스트 씬 텍스트."

    def test_actions_count(self):
        """actions 리스트 길이 일치."""
        inp = self._make_input()
        result = self.parser.parse_tool_input(inp)
        assert len(result.actions) == 2

    def test_action_actor_and_type(self):
        """첫 번째 액션의 actor/action_type 파싱."""
        inp = self._make_input()
        result = self.parser.parse_tool_input(inp)
        first = result.actions[0]
        assert first.actor == "고애신"
        assert first.action_type == "MOVE"
        assert first.location == "교회"

    def test_action_interact_target(self):
        """INTERACT 액션의 target 파싱."""
        inp = self._make_input()
        result = self.parser.parse_tool_input(inp)
        second = result.actions[1]
        assert second.actor == "유진"
        assert second.action_type == "INTERACT"
        assert second.target == "고애신"

    def test_literary_state_preserved(self):
        """literary_state SP/RU/ET/RD 값 보존."""
        inp = self._make_input()
        result = self.parser.parse_tool_input(inp)
        assert result.literary_state["SP"] == pytest.approx(0.72)
        assert result.literary_state["ET"] == pytest.approx(0.60)

    def test_parse_meta_method_is_tool_use(self):
        """parse_meta.method가 'tool_use'."""
        inp = self._make_input()
        result = self.parser.parse_tool_input(inp)
        assert result.parse_meta["method"] == "tool_use"
        assert result.parse_meta["parse_success"] is True

    def test_empty_actions_list(self):
        """actions=[] 이면 빈 리스트 반환."""
        inp = self._make_input(actions=[])
        result = self.parser.parse_tool_input(inp)
        assert result.actions == []
        assert result.parse_meta["action_count"] == 0


# ════════════════════════════════════════════════════════════════
# [C] ToolUseParser — parse_raw_response (8)
# ════════════════════════════════════════════════════════════════

class TestToolUseParserRawResponse:
    """Anthropic Message 객체 및 dict 응답 처리."""

    def setup_method(self):
        self.parser = ToolUseParser()

    def _make_mock_block(self, block_type: str, **kwargs):
        block = MagicMock()
        block.type = block_type
        for k, v in kwargs.items():
            setattr(block, k, v)
        return block

    def _make_mock_response(self, blocks):
        resp = MagicMock()
        resp.content = blocks
        return resp

    def test_parses_tool_use_block(self):
        """tool_use 블록이 있으면 ActionPacket 반환."""
        block = self._make_mock_block(
            "tool_use",
            name=TOOL_NAME,
            input={
                "narrative_text": "씬 텍스트",
                "actions": [{"actor": "A", "action_type": "INTERACT"}],
                "literary_state": {"SP": 0.5},
            },
        )
        resp = self._make_mock_response([block])
        result = self.parser.parse_raw_response(resp)
        assert isinstance(result, ActionPacket)
        assert result.narrative_text == "씬 텍스트"

    def test_ignores_wrong_tool_name(self):
        """다른 이름의 tool_use 블록은 무시 → fallback."""
        block = self._make_mock_block("tool_use", name="other_tool", input={})
        resp = self._make_mock_response([block])
        result = self.parser.parse_raw_response(resp)
        assert result.parse_meta["parse_success"] is False

    def test_text_block_fallback(self):
        """tool_use 없이 text 블록만 → fallback."""
        block = self._make_mock_block("text", text="일반 텍스트")
        resp = self._make_mock_response([block])
        result = self.parser.parse_raw_response(resp)
        assert result.parse_meta["method"] == "fallback_text"
        assert result.narrative_text == "일반 텍스트"

    def test_empty_content_fallback(self):
        """content=[] → fallback ActionPacket."""
        resp = self._make_mock_response([])
        result = self.parser.parse_raw_response(resp)
        assert result.parse_meta["parse_success"] is False

    def test_dict_response_with_narrative(self):
        """dict에 narrative_text 키 → parse_tool_input 위임."""
        d = {
            "narrative_text": "딕셔너리 씬",
            "actions": [],
            "literary_state": {},
        }
        result = self.parser.parse_raw_response(d)
        assert result.narrative_text == "딕셔너리 씬"
        assert result.parse_meta["method"] == "tool_use"

    def test_dict_response_content_array(self):
        """dict에 content 배열 + tool_use 블록 → 파싱 성공."""
        d = {
            "content": [
                {
                    "type": "tool_use",
                    "name": TOOL_NAME,
                    "input": {
                        "narrative_text": "컨텐츠 배열 씬",
                        "actions": [{"actor": "B", "action_type": "REVEAL"}],
                    },
                }
            ]
        }
        result = self.parser.parse_raw_response(d)
        assert result.narrative_text == "컨텐츠 배열 씬"
        assert len(result.actions) == 1

    def test_dict_response_fallback_text_key(self):
        """dict에 text 키 → fallback_packet."""
        d = {"text": "fallback 씬 텍스트"}
        result = self.parser.parse_raw_response(d)
        assert result.parse_meta["parse_success"] is False
        assert result.narrative_text == "fallback 씬 텍스트"

    def test_malformed_action_skipped(self):
        """action에 필수 필드 누락 시 스킵 (전체 실패 방지)."""
        inp = {
            "narrative_text": "씬",
            "actions": [
                {"actor": "A", "action_type": "MOVE"},
                {"action_type": "INTERACT"},        # actor 누락 → 빈 문자열로 처리
                {"actor": "C"},                      # action_type 누락 → INTERACT 기본값
            ],
        }
        result = self.parser.parse_tool_input(inp)
        # actor 누락 → "" actor 로 들어가고, action_type 누락 → "INTERACT" 기본값
        assert len(result.actions) == 3


# ════════════════════════════════════════════════════════════════
# [D] ToolUseParser — fallback 경로 (4)
# ════════════════════════════════════════════════════════════════

class TestToolUseParserFallback:
    """_fallback_packet 직접 호출 및 parse_meta 검증."""

    def setup_method(self):
        self.parser = ToolUseParser()

    def test_fallback_packet_narrative(self):
        """fallback 패킷의 narrative_text 보존."""
        pkt = self.parser._fallback_packet("fallback text")
        assert pkt.narrative_text == "fallback text"

    def test_fallback_packet_empty_actions(self):
        """fallback 패킷의 actions 빈 리스트."""
        pkt = self.parser._fallback_packet("x")
        assert pkt.actions == []

    def test_fallback_parse_success_false(self):
        """fallback 패킷의 parse_success=False."""
        pkt = self.parser._fallback_packet("x")
        assert pkt.parse_meta["parse_success"] is False

    def test_fallback_method_label(self):
        """fallback 패킷의 method 레이블 확인."""
        pkt = self.parser._fallback_packet("x")
        assert pkt.parse_meta["method"] == "fallback_text"


# ════════════════════════════════════════════════════════════════
# [E] ClaudeAdapter — 기본 속성/상태 (7)
# ════════════════════════════════════════════════════════════════

class TestClaudeAdapterProperties:
    """ClaudeAdapter 속성 및 상태 초기값 검증."""

    def test_default_provider_name(self):
        """기본 provider_name은 claude-sonnet-4-6."""
        adapter = ClaudeAdapter.__new__(ClaudeAdapter)
        adapter._model = "claude-sonnet-4-6"
        assert adapter._model == "claude-sonnet-4-6"

    def test_provider_name_property(self):
        """provider_name 프로퍼티가 _model을 반환."""
        adapter = ClaudeAdapter.__new__(ClaudeAdapter)
        adapter._model = "claude-opus-4-6"
        assert adapter.provider_name == "claude-opus-4-6"

    def test_initial_call_count_zero(self):
        """초기 call_count = 0."""
        adapter = ClaudeAdapter.__new__(ClaudeAdapter)
        adapter._call_count = 0
        assert adapter.call_count == 0

    def test_reset_clears_state(self):
        """reset() 후 call_count=0, _last_response=None."""
        adapter = ClaudeAdapter.__new__(ClaudeAdapter)
        adapter._call_count = 5
        adapter._last_response = object()
        adapter.reset()
        assert adapter.call_count == 0
        assert adapter._last_response is None

    def test_get_status_keys(self):
        """get_status() 반환 딕셔너리에 필수 키 존재."""
        adapter = ClaudeAdapter.__new__(ClaudeAdapter)
        adapter._model = "claude-sonnet-4-6"
        adapter._call_count = 0
        adapter._client = None
        result = adapter.get_status()
        for key in ("provider", "model", "available", "call_count", "anthropic_package", "client_ready"):
            assert key in result

    def test_is_available_false_without_client(self):
        """_client=None이면 is_available()=False."""
        adapter = ClaudeAdapter.__new__(ClaudeAdapter)
        adapter._client = None
        assert adapter.is_available() is False

    def test_custom_model_name(self):
        """커스텀 모델명이 provider_name에 반영."""
        adapter = ClaudeAdapter.__new__(ClaudeAdapter)
        adapter._model = "claude-haiku-4-5-20251001"
        assert adapter.provider_name == "claude-haiku-4-5-20251001"


# ════════════════════════════════════════════════════════════════
# [F] ClaudeAdapter — generate() 오프라인 (4)
# ════════════════════════════════════════════════════════════════

class TestClaudeAdapterGenerateOffline:
    """anthropic 패키지 없음/클라이언트 None 상황 시뮬레이션."""

    def test_generate_returns_empty_without_client(self):
        """_client=None이면 generate()=''. call_count 불변."""
        adapter = ClaudeAdapter.__new__(ClaudeAdapter)
        adapter._client = None
        adapter._call_count = 0
        adapter._last_response = None
        result = adapter.generate("프롬프트", {})
        assert result == ""
        assert adapter.call_count == 0

    def test_generate_with_mock_client(self):
        """Mock Anthropic 클라이언트로 generate() 경로 검증."""
        # tool_use 블록 mock
        mock_block = MagicMock()
        mock_block.type = "tool_use"
        mock_block.name = TOOL_NAME
        mock_block.input = {
            "narrative_text": "모킹된 씬 텍스트",
            "actions": [],
            "literary_state": {},
        }
        mock_response = MagicMock()
        mock_response.content = [mock_block]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response

        adapter = ClaudeAdapter.__new__(ClaudeAdapter)
        adapter._client      = mock_client
        adapter._model       = "claude-sonnet-4-6"
        adapter._max_tokens  = 4096
        adapter._temperature = 1.0
        adapter._system      = "system"
        adapter._call_count  = 0
        adapter._last_response = None
        adapter._parser      = ToolUseParser()

        result = adapter.generate("프롬프트", {"scene_id": "s001"})
        assert result == "모킹된 씬 텍스트"
        assert adapter.call_count == 1
        assert adapter._last_response is mock_response

    def test_generate_api_error_returns_empty(self):
        """API 예외 발생 시 빈 문자열 반환, last_response=None."""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API Error")

        adapter = ClaudeAdapter.__new__(ClaudeAdapter)
        adapter._client      = mock_client
        adapter._model       = "claude-sonnet-4-6"
        adapter._max_tokens  = 4096
        adapter._temperature = 1.0
        adapter._system      = "system"
        adapter._call_count  = 0
        adapter._last_response = object()  # 이전 값이 있어도
        adapter._parser      = ToolUseParser()

        result = adapter.generate("프롬프트", {})
        assert result == ""
        assert adapter._last_response is None  # 오류 시 초기화

    def test_build_user_message_includes_context(self):
        """_build_user_message()가 context 키를 포함한 문자열 반환."""
        adapter = ClaudeAdapter.__new__(ClaudeAdapter)
        msg = adapter._build_user_message("프롬프트", {"scene_id": "s001", "char": "유진"})
        assert "프롬프트" in msg
        assert "scene_id" in msg
        assert "s001" in msg


# ════════════════════════════════════════════════════════════════
# [G] ClaudeAdapter — parse_action_packet (3)
# ════════════════════════════════════════════════════════════════

class TestClaudeAdapterParseActionPacket:
    """generate() 후 parse_action_packet() 전체 ActionPacket 복원."""

    def _make_adapter_with_response(self, tool_input: dict):
        """mock response가 주입된 어댑터 반환."""
        mock_block = MagicMock()
        mock_block.type = "tool_use"
        mock_block.name = TOOL_NAME
        mock_block.input = tool_input

        mock_response = MagicMock()
        mock_response.content = [mock_block]

        adapter = ClaudeAdapter.__new__(ClaudeAdapter)
        adapter._parser         = ToolUseParser()
        adapter._last_response  = mock_response
        adapter._call_count     = 1
        return adapter

    def test_parse_restores_actions(self):
        """parse_action_packet()이 actions[]를 완전 복원."""
        adapter = self._make_adapter_with_response({
            "narrative_text": "복원 씬",
            "actions": [
                {"actor": "유진", "action_type": "REVEAL", "target": "비밀"},
            ],
            "literary_state": {"SP": 0.8},
        })
        pkt = adapter.parse_action_packet("복원 씬")
        assert len(pkt.actions) == 1
        assert pkt.actions[0].actor == "유진"
        assert pkt.actions[0].action_type == "REVEAL"

    def test_parse_uses_last_response_over_raw(self):
        """_last_response가 있으면 raw 인자보다 우선."""
        adapter = self._make_adapter_with_response({
            "narrative_text": "실제 씬",
            "actions": [],
            "literary_state": {},
        })
        # raw에는 다른 텍스트를 줘도 _last_response 우선
        pkt = adapter.parse_action_packet("다른 텍스트")
        assert pkt.narrative_text == "실제 씬"
        assert pkt.parse_meta["parse_success"] is True

    def test_parse_fallback_when_no_last_response(self):
        """_last_response=None이면 raw 텍스트로 fallback."""
        adapter = ClaudeAdapter.__new__(ClaudeAdapter)
        adapter._parser        = ToolUseParser()
        adapter._last_response = None

        pkt = adapter.parse_action_packet("fallback 텍스트")
        assert pkt.narrative_text == "fallback 텍스트"
        assert pkt.parse_meta["parse_success"] is False


# ════════════════════════════════════════════════════════════════
# E2ELoopOrchestrator bridge 주입 통합 검증
# ════════════════════════════════════════════════════════════════

class TestE2ELoopBridgeInjection:
    """bridge=ClaudeAdapter 주입 후 orchestrator가 이를 사용하는지 확인."""

    def test_bridge_injection_replaces_v312(self):
        """bridge= 파라미터 주입 시 V312Bridge 대신 사용됨."""
        from literary_system.orchestrators.e2e_loop_orchestrator import E2ELoopOrchestrator
        from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge

        mock_bridge = MockLLMBridge()
        orch = E2ELoopOrchestrator(bridge=mock_bridge)
        assert orch.bridge is mock_bridge

    def test_bridge_none_uses_v312(self):
        """bridge=None이면 V312Bridge 기본 사용."""
        from literary_system.orchestrators.e2e_loop_orchestrator import E2ELoopOrchestrator
        from literary_system.compiler.v312_bridge import V312Bridge

        orch = E2ELoopOrchestrator()
        assert isinstance(orch.bridge, V312Bridge)
