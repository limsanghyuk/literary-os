"""
V324 - test_v324_llm_bridge.py
LLMBridgeInterface + MockLLMBridge 테스트 (20개)
"""
import pytest
from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface
from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge
from literary_system.action_compiler.action_packet import ActionPacket


# ════════════════════════════════════════════════════════════════════
# 1. MockLLMBridge — 기본 기능
# ════════════════════════════════════════════════════════════════════

class TestMockLLMBridgeBasic:
    def test_is_llm_bridge_subclass(self):
        assert issubclass(MockLLMBridge, LLMBridgeInterface)

    def test_provider_name(self):
        assert MockLLMBridge().provider_name == "mock"

    def test_generate_returns_string(self):
        bridge = MockLLMBridge(scripted_response="hello world")
        assert bridge.generate("prompt", {}) == "hello world"

    def test_generate_default_response(self):
        result = MockLLMBridge().generate("any prompt", {})
        assert isinstance(result, str) and len(result) > 0

    def test_generate_accepts_context(self):
        bridge = MockLLMBridge()
        result = bridge.generate("prompt", {"scene_id": "s1"})
        assert isinstance(result, str)

    def test_call_count_zero_initially(self):
        assert MockLLMBridge().call_count == 0


# ════════════════════════════════════════════════════════════════════
# 2. MockLLMBridge — parse_action_packet
# ════════════════════════════════════════════════════════════════════

class TestMockLLMBridgeParse:
    def test_parse_returns_action_packet(self):
        raw = '{"action": "MOVE", "source": "char_a", "target": "loc_b"}'
        packet = MockLLMBridge().parse_action_packet(raw)
        assert isinstance(packet, ActionPacket)

    def test_parse_empty_gives_action_packet(self):
        packet = MockLLMBridge().parse_action_packet("")
        assert isinstance(packet, ActionPacket)

    def test_parse_malformed_gives_action_packet(self):
        packet = MockLLMBridge().parse_action_packet("@@@invalid@@@")
        assert isinstance(packet, ActionPacket)

    def test_parse_json_block(self):
        raw = '```json\n{"action": "INTERACT", "source": "a", "target": "b"}\n```'
        packet = MockLLMBridge().parse_action_packet(raw)
        assert isinstance(packet, ActionPacket)

    def test_scripted_packet_override(self):
        scripted = ActionPacket(narrative_text="scripted scene")
        bridge = MockLLMBridge(scripted_packet=scripted)
        result = bridge.parse_action_packet("anything")
        assert result.narrative_text == "scripted scene"

    def test_scripted_packet_none_uses_parser(self):
        bridge = MockLLMBridge(scripted_packet=None)
        packet = bridge.parse_action_packet("")
        assert isinstance(packet, ActionPacket)


# ════════════════════════════════════════════════════════════════════
# 3. LLMBridgeInterface — 추상 계약
# ════════════════════════════════════════════════════════════════════

class TestLLMBridgeInterface:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            LLMBridgeInterface()

    def test_abstract_methods_required(self):
        import inspect
        abstract = {
            name for name, method in inspect.getmembers(LLMBridgeInterface)
            if getattr(method, "__isabstractmethod__", False)
        }
        assert "generate" in abstract
        assert "parse_action_packet" in abstract

    def test_provider_name_is_abstract(self):
        import inspect
        members = dict(inspect.getmembers(LLMBridgeInterface))
        prop = LLMBridgeInterface.__dict__.get("provider_name")
        assert prop is not None

    def test_concrete_subclass_works(self):
        class MinimalBridge(LLMBridgeInterface):
            def generate(self, prompt, context): return "ok"
            def parse_action_packet(self, raw):
                return ActionPacket(narrative_text=raw or "noop")
            @property
            def provider_name(self): return "minimal"
        b = MinimalBridge()
        assert b.generate("p", {}) == "ok"
        assert b.provider_name == "minimal"


# ════════════════════════════════════════════════════════════════════
# 4. MockLLMBridge — 통합 / 부가 기능
# ════════════════════════════════════════════════════════════════════

class TestMockLLMBridgeIntegration:
    def test_generate_then_parse_pipeline(self):
        raw = '{"action": "MOVE", "source": "char_a", "target": "loc_b"}'
        bridge = MockLLMBridge(scripted_response=raw)
        generated = bridge.generate("write a scene", {})
        packet = bridge.parse_action_packet(generated)
        assert isinstance(packet, ActionPacket)

    def test_call_count_tracks_generate(self):
        bridge = MockLLMBridge()
        bridge.generate("p1", {})
        bridge.generate("p2", {})
        assert bridge.call_count == 2

    def test_reset_clears_call_count(self):
        bridge = MockLLMBridge()
        bridge.generate("p", {})
        bridge.reset()
        assert bridge.call_count == 0

    def test_multiple_scripted_responses(self):
        """responses 리스트로 순서대로 반환."""
        bridge = MockLLMBridge(scripted_responses=["first", "second", "third"])
        assert bridge.generate("p", {}) == "first"
        assert bridge.generate("p", {}) == "second"
        assert bridge.generate("p", {}) == "third"

    def test_responses_loop_on_exhaustion(self):
        """responses 소진 시 마지막 응답 반복."""
        bridge = MockLLMBridge(scripted_responses=["only"])
        bridge.generate("p", {})
        assert bridge.generate("p", {}) == "only"
