"""
V323 Phase 1 — ActionPacketParser 테스트 (30개)
[CSC] Test-First 원칙: 구현 완료 후 전원 통과 확인.
"""
import json
import pytest
from literary_system.action_compiler.action_packet import (
    Action, ActionPacket, ActionPacketParser, ActionType
)


@pytest.fixture
def parser():
    return ActionPacketParser()


@pytest.fixture
def strict_parser():
    return ActionPacketParser(strict=True)


# ── 1. Action 데이터 클래스 ─────────────────────────────────────

class TestActionDataclass:
    def test_action_defaults(self):
        a = Action(actor="김민준", action_type="MOVE")
        assert a.actor == "김민준"
        assert a.target is None
        assert a.location is None
        assert a.metadata == {}

    def test_action_to_dict(self):
        a = Action(actor="이서연", action_type="INTERACT", target="박준혁")
        d = a.to_dict()
        assert d["actor"] == "이서연"
        assert d["action_type"] == "INTERACT"
        assert d["target"] == "박준혁"

    def test_action_from_dict_roundtrip(self):
        original = Action(actor="최유진", action_type="REVEAL", target="비밀편지", metadata={"ep": 3})
        restored = Action.from_dict(original.to_dict())
        assert restored.actor == original.actor
        assert restored.action_type == original.action_type
        assert restored.metadata == original.metadata

    def test_action_type_enum_values(self):
        assert ActionType.MOVE == "MOVE"
        assert ActionType.INTERACT == "INTERACT"
        assert ActionType.ACQUIRE == "ACQUIRE"
        assert ActionType.REVEAL == "REVEAL"
        assert ActionType.HIDE == "HIDE"


# ── 2. ActionPacket 데이터 클래스 ───────────────────────────────

class TestActionPacket:
    def test_packet_defaults(self):
        pkt = ActionPacket(narrative_text="어두운 골목에서 그들이 마주쳤다.")
        assert pkt.actions == []
        assert pkt.literary_state == {}
        assert pkt.action_count == 0
        assert not pkt.is_valid  # parse_meta 없음 -> False

    def test_packet_is_valid_with_meta(self):
        pkt = ActionPacket(
            narrative_text="test",
            parse_meta={"parse_success": True},
        )
        assert pkt.is_valid

    def test_packet_to_dict(self):
        actions = [Action(actor="김민준", action_type="MOVE", location="서울역")]
        pkt = ActionPacket(narrative_text="그가 서울역으로 걸어갔다.", actions=actions)
        d = pkt.to_dict()
        assert d["narrative_text"] == "그가 서울역으로 걸어갔다."
        assert len(d["actions"]) == 1
        assert d["actions"][0]["actor"] == "김민준"


# ── 3. JSON 블록 파싱 ────────────────────────────────────────────

class TestJsonBlockParsing:
    def test_json_block_basic(self, parser):
        text = '''그는 천천히 걸음을 옮겼다.
```json
{"narrative_text": "그는 서울역으로 이동했다.", "actions": [{"actor": "김민준", "action_type": "MOVE", "location": "서울역"}]}
```'''
        pkt = parser.parse(text)
        assert pkt.is_valid
        assert pkt.parse_meta["parse_method"] == "json_block"
        assert len(pkt.actions) == 1
        assert pkt.actions[0].actor == "김민준"
        assert pkt.actions[0].location == "서울역"

    def test_json_block_multiple_actions(self, parser):
        data = {
            "narrative_text": "두 사람이 마주쳤다.",
            "actions": [
                {"actor": "이서연", "action_type": "MOVE", "location": "카페"},
                {"actor": "박준혁", "action_type": "INTERACT", "target": "이서연"},
            ]
        }
        text = f"```json\n{json.dumps(data, ensure_ascii=False)}\n```"
        pkt = parser.parse(text)
        assert len(pkt.actions) == 2
        assert pkt.actions[1].target == "이서연"

    def test_json_block_with_literary_state(self, parser):
        data = {"narrative_text": "씬 텍스트", "actions": []}
        lit_state = {"pdi": 0.35, "residue_density": 0.6}
        text = f"```json\n{json.dumps(data)}\n```"
        pkt = parser.parse(text, literary_state=lit_state)
        assert pkt.literary_state["pdi"] == 0.35

    def test_bare_json_object(self, parser):
        data = {"narrative_text": "내용", "actions": [{"actor": "A", "action_type": "HIDE", "target": "B"}]}
        pkt = parser.parse(json.dumps(data))
        assert pkt.is_valid
        assert pkt.actions[0].action_type == "HIDE"

    def test_dict_input_with_literary_state(self, parser):
        render_output = {
            "text": "```json\n{\"narrative_text\": \"내용\", \"actions\": []}\n```",
            "literary_state": {"pdi": 0.4}
        }
        pkt = parser.parse(render_output)
        assert pkt.literary_state["pdi"] == 0.4


# ── 4. XML 태그 파싱 ─────────────────────────────────────────────

class TestXmlTagParsing:
    def test_xml_move_action(self, parser):
        text = '그가 이동한다. <action type="MOVE" actor="김민준" location="병원"/>'
        pkt = parser.parse(text)
        assert pkt.is_valid
        assert pkt.parse_meta["parse_method"] == "xml_tags"
        assert pkt.actions[0].action_type == "MOVE"
        assert pkt.actions[0].location == "병원"

    def test_xml_interact_action(self, parser):
        text = '<action type="INTERACT" actor="이서연" target="박준혁"/> 두 사람이 만났다.'
        pkt = parser.parse(text)
        assert len(pkt.actions) == 1
        assert pkt.actions[0].target == "박준혁"

    def test_xml_multiple_actions(self, parser):
        text = '''
        <action type="MOVE" actor="A" location="X"/>
        <action type="ACQUIRE" actor="A" target="열쇠"/>
        '''
        pkt = parser.parse(text)
        assert len(pkt.actions) == 2

    def test_xml_case_insensitive(self, parser):
        text = '<ACTION type="move" actor="김민준" location="서울"/>'
        pkt = parser.parse(text)
        assert pkt.actions[0].action_type == "MOVE"


# ── 5. 괄호 표기 파싱 ────────────────────────────────────────────

class TestBracketNotation:
    def test_bracket_move(self, parser):
        text = "그가 집을 떠났다. [MOVE: 김민준 -> 공항]"
        pkt = parser.parse(text)
        assert pkt.is_valid
        assert pkt.parse_meta["parse_method"] == "bracket_notation"
        assert pkt.actions[0].actor == "김민준"
        assert pkt.actions[0].location == "공항"

    def test_bracket_interact(self, parser):
        text = "[INTERACT: 이서연 & 박준혁] 그들이 대화를 나눴다."
        pkt = parser.parse(text)
        assert pkt.actions[0].actor == "이서연"
        assert pkt.actions[0].target == "박준혁"

    def test_bracket_reveal(self, parser):
        text = "[REVEAL: 최유진, 비밀편지]"
        pkt = parser.parse(text)
        assert pkt.actions[0].action_type == "REVEAL"
        assert pkt.actions[0].actor == "최유진"

    def test_bracket_multiple(self, parser):
        text = "[MOVE: A -> 병원] 그리고 [INTERACT: A & B]"
        pkt = parser.parse(text)
        assert len(pkt.actions) == 2

    def test_narrative_stripped_from_bracket(self, parser):
        text = "그녀가 복도를 걸었다. [MOVE: 이서연 -> 회의실] 문을 열었다."
        pkt = parser.parse(text)
        assert "[MOVE:" not in pkt.narrative_text


# ── 6. Fallback 처리 ─────────────────────────────────────────────

class TestFallbackHandling:
    def test_no_actions_fallback(self, parser):
        text = "비가 내렸다. 그는 창밖을 바라보았다."
        pkt = parser.parse(text)
        assert not pkt.is_valid
        assert pkt.narrative_text == text
        assert pkt.action_count == 0

    def test_strict_mode_raises(self, strict_parser):
        text = "단순한 서사 텍스트."
        with pytest.raises(ValueError):
            strict_parser.parse(text)

    def test_empty_string_fallback(self, parser):
        pkt = parser.parse("")
        assert not pkt.is_valid
        assert pkt.narrative_text == ""

    def test_dict_with_empty_text(self, parser):
        pkt = parser.parse({"text": "", "literary_state": {}})
        assert not pkt.is_valid


# ── 7. 파싱 메타데이터 ───────────────────────────────────────────

class TestParseMeta:
    def test_meta_fields_present(self, parser):
        text = '[MOVE: A -> B]'
        pkt = parser.parse(text)
        meta = pkt.parse_meta
        assert "parse_success" in meta
        assert "parse_method" in meta
        assert "action_count" in meta
        assert "raw_length" in meta

    def test_action_count_matches(self, parser):
        text = '[MOVE: A -> B] [INTERACT: C & D] [HIDE: E, F]'
        pkt = parser.parse(text)
        assert pkt.parse_meta["action_count"] == pkt.action_count == 3
