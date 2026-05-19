"""
V324 - CharacterStateGate  (Phase 3)
캐릭터 상태 전이 FSM — is_alive / is_hidden / inventory 3-상태 일관성 강제.

설계 원칙 (P2 외과적 통합, P6 State 감사, P3 LLM 0회):
  - RelationGraphStore와 어댑터 패턴으로 결합 (내부 변경 없음)
  - FSM 규칙:
      alive=True, hidden=False  → MOVE/INTERACT/ACQUIRE/HIDE/KILL/REVEAL 허용
      alive=True, hidden=True   → MOVE/INTERACT/HIDE/REVEAL/KILL 허용
                                   ACQUIRE 금지 (은신 중 획득 불가)
      alive=False               → 모든 전이 금지 (최종 상태)
  - check_transition() → StateCheckResult (원본 state 불변)
  - apply_transition() → 새 CharacterState 반환 (불변성)
  - get_violations() / clear_violations() → 감사 이력 관리
  - LLM 0회. 완전 로컬.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import List, Optional, Set


# ════════════════════════════════════════════════════════════════════
# CharacterState DTO
# ════════════════════════════════════════════════════════════════════

@dataclass
class CharacterStateSnapshot:
    """단일 캐릭터의 현재 상태."""
    is_alive: bool = True
    is_hidden: bool = False
    inventory: Set[str] = field(default_factory=set)

    def to_dict(self) -> dict:
        return {
            "is_alive": self.is_alive,
            "is_hidden": self.is_hidden,
            "inventory": list(self.inventory),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CharacterState":
        return cls(
            is_alive=d.get("is_alive", True),
            is_hidden=d.get("is_hidden", False),
            inventory=set(d.get("inventory", [])),
        )

    def copy(self) -> "CharacterState":
        return CharacterState(
            is_alive=self.is_alive,
            is_hidden=self.is_hidden,
            inventory=set(self.inventory),
        )


# ════════════════════════════════════════════════════════════════════
# StateViolation / StateCheckResult
# ════════════════════════════════════════════════════════════════════

@dataclass
class StateViolation:
    """상태 전이 위반 레코드."""
    char_id: str
    action_type: str
    reason: str
    current_state: dict = field(default_factory=dict)


@dataclass
class StateCheckResult:
    """check_transition() 결과."""
    passed: bool
    violations: List[StateViolation] = field(default_factory=list)


# ════════════════════════════════════════════════════════════════════
# FSM 규칙 정의
# ════════════════════════════════════════════════════════════════════

# 모든 살아있는 캐릭터에 허용되는 액션
_ALIVE_ALLOWED = {"MOVE", "INTERACT", "HIDE", "REVEAL", "KILL"}
# 은신 중 금지 액션
_HIDDEN_FORBIDDEN = {"ACQUIRE"}
# 사망 시 허용 액션 (없음)
_DEAD_ALLOWED: set = set()


def _is_allowed(action_type: str, state: CharacterState) -> tuple[bool, str]:
    """
    (allowed, reason) 반환.
    """
    act = action_type.upper()

    if not state.is_alive:
        return False, f"캐릭터가 사망 상태(alive=False)이므로 {act} 불가"

    if act == "ACQUIRE" and state.is_hidden:
        return False, f"은신 중(hidden=True)에는 ACQUIRE 불가"

    # 살아있으면 ACQUIRE 포함 모든 기본 액션 허용
    return True, ""


# ════════════════════════════════════════════════════════════════════
# CharacterStateGate
# ════════════════════════════════════════════════════════════════════

class CharacterStateGate:
    """
    캐릭터 상태 전이 검증 + 적용.

    - check_transition(): 원본 state를 변경하지 않고 합법성만 검사
    - apply_transition(): 새 CharacterState 반환 (불변성)
    - get_violations() / clear_violations(): 감사 이력
    """

    def __init__(self) -> None:
        self._violations: List[StateViolation] = []

    # ── 핵심 API ────────────────────────────────────────────────────

    def check_transition(
        self,
        char_id: str,
        action_type: str,
        state: CharacterState,
    ) -> StateCheckResult:
        """
        전이 합법성 검사. 원본 state 불변.
        위반 시 내부 이력에도 기록.
        """
        allowed, reason = _is_allowed(action_type, state)
        violations = []
        if not allowed:
            v = StateViolation(
                char_id=char_id,
                action_type=action_type.upper(),
                reason=reason,
                current_state=state.to_dict(),
            )
            violations.append(v)
            self._violations.append(v)
        return StateCheckResult(passed=allowed, violations=violations)

    def apply_transition(
        self,
        char_id: str,
        action_type: str,
        state: CharacterState,
        item_id: str | None = None,
    ) -> CharacterState:
        """
        합법 전이를 적용하여 새 CharacterState 반환.
        불법 전이면 원본 상태 복사본 반환 (부작용 없음).
        """
        new_state = state.copy()
        act = action_type.upper()

        allowed, _ = _is_allowed(act, state)
        if not allowed:
            return new_state  # 원본 불변 복사본만 반환

        if act == "HIDE":
            new_state.is_hidden = True
        elif act == "REVEAL":
            new_state.is_hidden = False
        elif act == "KILL":
            new_state.is_alive = False
            new_state.is_hidden = False
        elif act == "ACQUIRE" and item_id:
            new_state.inventory.add(item_id)

        return new_state

    # ── 감사 이력 ────────────────────────────────────────────────────

    def get_violations(self) -> List[StateViolation]:
        """누적 위반 이력 복사본 반환."""
        return list(self._violations)

    def clear_violations(self) -> None:
        """위반 이력 초기화."""
        self._violations.clear()

CharacterState = CharacterStateSnapshot  # V579 backward-compat alias
