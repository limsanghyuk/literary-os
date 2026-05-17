"""
V324 - test_v324_character_state_gate.py
CharacterStateGate (FSM) 테스트 (25개)
위반 케이스 10개 포함 (P7 테스트 우선 원칙)
"""
import pytest
from literary_system.gate.character_state_gate import (
    CharacterStateGate, CharacterState, StateViolation, StateCheckResult,
)


@pytest.fixture
def gate():
    return CharacterStateGate()

def make_state(alive=True, hidden=False):
    return CharacterState(is_alive=alive, is_hidden=hidden, inventory=set())


# ════════════════════════════════════════════════════════════════════
# 1. CharacterState DTO
# ════════════════════════════════════════════════════════════════════

class TestCharacterState:
    def test_defaults(self):
        s = CharacterState()
        assert s.is_alive is True
        assert s.is_hidden is False
        assert s.inventory == set()

    def test_custom_values(self):
        s = CharacterState(is_alive=False, is_hidden=True, inventory={"sword", "shield"})
        assert s.is_alive is False
        assert s.is_hidden is True
        assert "sword" in s.inventory

    def test_to_dict(self):
        s = CharacterState(is_alive=True, is_hidden=False, inventory={"key"})
        d = s.to_dict()
        assert d["is_alive"] is True
        assert d["is_hidden"] is False
        assert "key" in d["inventory"]

    def test_from_dict(self):
        d = {"is_alive": False, "is_hidden": True, "inventory": ["potion"]}
        s = CharacterState.from_dict(d)
        assert s.is_alive is False
        assert s.is_hidden is True
        assert "potion" in s.inventory


# ════════════════════════════════════════════════════════════════════
# 2. 정상 전이 (합법 케이스 15개)
# ════════════════════════════════════════════════════════════════════

class TestLegalTransitions:
    def test_alive_can_hide(self, gate):
        state = make_state(alive=True, hidden=False)
        result = gate.check_transition("char_a", "HIDE", state)
        assert result.passed is True

    def test_alive_can_reveal(self, gate):
        state = make_state(alive=True, hidden=True)
        result = gate.check_transition("char_a", "REVEAL", state)
        assert result.passed is True

    def test_alive_can_move(self, gate):
        state = make_state(alive=True, hidden=False)
        result = gate.check_transition("char_a", "MOVE", state)
        assert result.passed is True

    def test_alive_hidden_can_move(self, gate):
        state = make_state(alive=True, hidden=True)
        result = gate.check_transition("char_a", "MOVE", state)
        assert result.passed is True

    def test_alive_can_interact(self, gate):
        state = make_state(alive=True, hidden=False)
        result = gate.check_transition("char_a", "INTERACT", state)
        assert result.passed is True

    def test_alive_can_acquire(self, gate):
        state = make_state(alive=True, hidden=False)
        result = gate.check_transition("char_a", "ACQUIRE", state)
        assert result.passed is True

    def test_alive_can_kill(self, gate):
        """alive→dead 전이는 합법."""
        state = make_state(alive=True, hidden=False)
        result = gate.check_transition("char_a", "KILL", state)
        assert result.passed is True

    def test_check_returns_state_check_result(self, gate):
        state = make_state()
        result = gate.check_transition("char_a", "MOVE", state)
        assert isinstance(result, StateCheckResult)

    def test_no_violations_on_legal_transition(self, gate):
        state = make_state()
        result = gate.check_transition("char_a", "MOVE", state)
        assert len(result.violations) == 0

    def test_apply_hide_updates_state(self, gate):
        state = make_state(alive=True, hidden=False)
        new_state = gate.apply_transition("char_a", "HIDE", state)
        assert new_state.is_hidden is True
        assert new_state.is_alive is True

    def test_apply_reveal_updates_state(self, gate):
        state = make_state(alive=True, hidden=True)
        new_state = gate.apply_transition("char_a", "REVEAL", state)
        assert new_state.is_hidden is False

    def test_apply_kill_updates_state(self, gate):
        state = make_state(alive=True)
        new_state = gate.apply_transition("char_a", "KILL", state)
        assert new_state.is_alive is False

    def test_apply_move_preserves_state(self, gate):
        state = make_state(alive=True, hidden=False)
        new_state = gate.apply_transition("char_a", "MOVE", state)
        assert new_state.is_alive is True
        assert new_state.is_hidden is False

    def test_inventory_add_on_acquire(self, gate):
        state = make_state(alive=True, hidden=False)
        new_state = gate.apply_transition("char_a", "ACQUIRE", state, item_id="sword")
        assert "sword" in new_state.inventory

    def test_check_does_not_mutate_state(self, gate):
        state = make_state(alive=True, hidden=False)
        gate.check_transition("char_a", "KILL", state)
        assert state.is_alive is True  # 원본 불변


# ════════════════════════════════════════════════════════════════════
# 3. 위반 케이스 (10개)
# ════════════════════════════════════════════════════════════════════

class TestViolations:
    def test_dead_cannot_move(self, gate):
        state = make_state(alive=False)
        result = gate.check_transition("char_a", "MOVE", state)
        assert result.passed is False
        assert len(result.violations) > 0

    def test_dead_cannot_hide(self, gate):
        state = make_state(alive=False)
        result = gate.check_transition("char_a", "HIDE", state)
        assert result.passed is False

    def test_dead_cannot_interact(self, gate):
        state = make_state(alive=False)
        result = gate.check_transition("char_a", "INTERACT", state)
        assert result.passed is False

    def test_dead_cannot_acquire(self, gate):
        state = make_state(alive=False)
        result = gate.check_transition("char_a", "ACQUIRE", state)
        assert result.passed is False

    def test_dead_cannot_be_killed_again(self, gate):
        state = make_state(alive=False)
        result = gate.check_transition("char_a", "KILL", state)
        assert result.passed is False

    def test_hidden_cannot_acquire(self, gate):
        """은신 중 아이템 획득 금지."""
        state = make_state(alive=True, hidden=True)
        result = gate.check_transition("char_a", "ACQUIRE", state)
        assert result.passed is False

    def test_violation_has_reason(self, gate):
        state = make_state(alive=False)
        result = gate.check_transition("char_a", "MOVE", state)
        assert len(result.violations[0].reason) > 0

    def test_violation_has_char_id(self, gate):
        state = make_state(alive=False)
        result = gate.check_transition("char_x", "MOVE", state)
        assert result.violations[0].char_id == "char_x"

    def test_get_violations_tracks_history(self, gate):
        state = make_state(alive=False)
        gate.check_transition("char_a", "MOVE", state)
        gate.check_transition("char_b", "MOVE", state)
        assert len(gate.get_violations()) == 2

    def test_clear_violations(self, gate):
        state = make_state(alive=False)
        gate.check_transition("char_a", "MOVE", state)
        gate.clear_violations()
        assert len(gate.get_violations()) == 0
