"""
V323 Phase 1 — SpatialConstraintGate 테스트 (25개)
[CSC] G2 복합 게이트 검증.
"""
import pytest
from literary_system.action_compiler.action_packet import Action, ActionPacket, ActionType
from literary_system.action_compiler.spatial_constraint_gate import (
    SpatialConstraintGate, SpatialPositionIndex, SpatialViolation
)


@pytest.fixture
def index():
    idx = SpatialPositionIndex()
    idx.set_position("김민준", "카페")
    idx.set_position("이서연", "카페")
    idx.set_position("박준혁", "병원")
    idx.set_position("열쇠", "창고")
    return idx


@pytest.fixture
def gate(index):
    return SpatialConstraintGate(position_index=index, strict_mode=False)


@pytest.fixture
def strict_gate(index):
    return SpatialConstraintGate(position_index=index, strict_mode=True)


# ── 1. SpatialPositionIndex ─────────────────────────────────────

class TestPositionIndex:
    def test_set_and_get(self):
        idx = SpatialPositionIndex()
        idx.set_position("A", "서울역")
        assert idx.get_position("A") == "서울역"

    def test_unknown_entity_returns_none(self):
        idx = SpatialPositionIndex()
        assert idx.get_position("없는인물") is None

    def test_move_updates_position(self):
        idx = SpatialPositionIndex()
        idx.set_position("A", "집")
        idx.move("A", "학교")
        assert idx.get_position("A") == "학교"

    def test_to_dict_roundtrip(self):
        idx = SpatialPositionIndex()
        idx.set_position("A", "X")
        idx.set_position("B", "Y")
        d = idx.to_dict()
        idx2 = SpatialPositionIndex()
        idx2.from_dict(d)
        assert idx2.get_position("A") == "X"


# ── 2. INTERACT 검증 ────────────────────────────────────────────

class TestInteractCheck:
    def test_same_location_passes(self, gate):
        action = Action(actor="김민준", action_type="INTERACT", target="이서연")
        result = gate.check_action(action)
        assert result.passed
        assert result.gate_weight == 1.0

    def test_different_location_fails(self, gate):
        action = Action(actor="김민준", action_type="INTERACT", target="박준혁")
        result = gate.check_action(action)
        assert not result.passed
        assert result.gate_weight == 0.0
        assert result.violation is not None
        assert "카페" in result.violation.reason
        assert "병원" in result.violation.reason

    def test_no_target_passes(self, gate):
        action = Action(actor="김민준", action_type="INTERACT", target=None)
        result = gate.check_action(action)
        assert result.passed

    def test_unknown_location_passes_non_strict(self, gate):
        action = Action(actor="미지인물", action_type="INTERACT", target="이서연")
        result = gate.check_action(action)
        assert result.passed  # strict=False이면 미지정 위치는 통과

    def test_unknown_location_fails_strict(self, strict_gate):
        action = Action(actor="미지인물", action_type="INTERACT", target="이서연")
        result = strict_gate.check_action(action)
        assert not result.passed


# ── 3. MOVE 검증 ────────────────────────────────────────────────

class TestMoveCheck:
    def test_move_with_location_passes(self, gate):
        action = Action(actor="김민준", action_type="MOVE", location="병원")
        result = gate.check_action(action)
        assert result.passed

    def test_move_without_location_passes_non_strict(self, gate):
        action = Action(actor="김민준", action_type="MOVE", location=None)
        result = gate.check_action(action)
        assert result.passed

    def test_move_without_location_fails_strict(self, strict_gate):
        action = Action(actor="김민준", action_type="MOVE", location=None)
        result = strict_gate.check_action(action)
        assert not result.passed

    def test_move_updates_position_via_gate(self, gate):
        action = Action(actor="김민준", action_type="MOVE", location="병원")
        gate.update_from_action(action)
        assert gate._index.get_position("김민준") == "병원"


# ── 4. ACQUIRE 검증 ─────────────────────────────────────────────

class TestAcquireCheck:
    def test_different_location_fails(self, gate):
        action = Action(actor="김민준", action_type="ACQUIRE", target="열쇠")
        # 김민준=카페, 열쇠=창고 -> 실패
        result = gate.check_action(action)
        assert not result.passed

    def test_same_location_passes(self, gate):
        gate._index.set_position("보물", "카페")
        action = Action(actor="김민준", action_type="ACQUIRE", target="보물")
        result = gate.check_action(action)
        assert result.passed


# ── 5. REVEAL / HIDE — 공간 제약 없음 ────────────────────────────

class TestRevealHideCheck:
    def test_reveal_always_passes(self, gate):
        action = Action(actor="김민준", action_type="REVEAL", target="비밀")
        result = gate.check_action(action)
        assert result.passed
        assert result.gate_weight == 1.0

    def test_hide_always_passes(self, gate):
        action = Action(actor="이서연", action_type="HIDE", target="편지")
        result = gate.check_action(action)
        assert result.passed


# ── 6. ActionPacket 전체 검증 ────────────────────────────────────

class TestPacketCheck:
    def test_all_pass_packet(self, gate):
        actions = [
            Action(actor="김민준", action_type="INTERACT", target="이서연"),
            Action(actor="김민준", action_type="MOVE", location="병원"),
        ]
        pkt = ActionPacket(narrative_text="test", actions=actions)
        results = gate.check_packet(pkt)
        assert all(r.passed for r in results)
        assert gate.packet_gate_weight(pkt) == 1.0

    def test_one_fail_zeros_whole_packet(self, gate):
        actions = [
            Action(actor="김민준", action_type="INTERACT", target="이서연"),  # pass
            Action(actor="김민준", action_type="INTERACT", target="박준혁"),  # fail (다른 위치)
        ]
        pkt = ActionPacket(narrative_text="test", actions=actions)
        assert gate.packet_gate_weight(pkt) == 0.0

    def test_empty_packet_passes(self, gate):
        pkt = ActionPacket(narrative_text="text", actions=[])
        assert gate.packet_gate_weight(pkt) == 1.0

    def test_violations_accumulated(self, gate):
        gate.clear_violations()
        action = Action(actor="김민준", action_type="INTERACT", target="박준혁")
        gate.check_action(action)
        assert len(gate.violations) == 1

    def test_stats(self, gate):
        s = gate.stats()
        assert "total_violations" in s
        assert "strict_mode" in s
        assert "tracked_entities" in s
