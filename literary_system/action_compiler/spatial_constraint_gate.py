"""
V323 — SpatialConstraintGate  (Layer 2, DRSE G2 강화)
Gemini StateEngine INTERACT 공간 제약 재해석.
LLM 0회. 완전 로컬.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SpatialViolation:
    action_type: str
    actor: str
    target: str | None
    actor_location: str | None
    target_location: str | None
    reason: str


@dataclass
class SpatialCheckResult:
    action_index: int
    action_type: str
    actor: str
    passed: bool
    gate_weight: float
    violation: SpatialViolation | None = None


class SpatialPositionIndex:
    """인물/오브젝트 위치 인덱스."""
    def __init__(self):
        self._positions: dict[str, str | None] = {}

    def set_position(self, entity: str, location: str | None) -> None:
        self._positions[entity] = location

    def get_position(self, entity: str) -> str | None:
        return self._positions.get(entity)

    def move(self, actor: str, new_location: str) -> None:
        self._positions[actor] = new_location

    def to_dict(self) -> dict[str, Any]:
        return dict(self._positions)

    def from_dict(self, d: dict[str, Any]) -> None:
        self._positions = {k: v for k, v in d.items()}


class SpatialConstraintGate:
    """
    V323 공간 제약 게이트.
    G2_v323 = KnowledgeBoundaryGate.weight * SpatialConstraintGate.weight
    strict_mode=False: 위치 미지정시 통과 (V322 호환)
    strict_mode=True:  위치 미지정시 실패
    """

    def __init__(
        self,
        position_index: SpatialPositionIndex | None = None,
        relation_graph=None,
        strict_mode: bool = False,
    ):
        self._index = position_index or SpatialPositionIndex()
        self._rgs = relation_graph
        self.strict_mode = strict_mode
        self._violations: list[SpatialViolation] = []

    def _get_location(self, entity_name: str) -> str | None:
        if self._rgs is not None:
            for node in self._rgs.all_nodes():
                if node.content == entity_name or node.node_id == entity_name:
                    for tag in node.tags:
                        if tag.startswith("location:"):
                            return tag.split(":", 1)[1]
        return self._index.get_position(entity_name)

    def set_position(self, entity: str, location: str | None) -> None:
        self._index.set_position(entity, location)

    def update_from_action(self, action) -> None:
        from literary_system.action_compiler.action_packet import ActionType
        if action.action_type == ActionType.MOVE and action.location:
            self._index.move(action.actor, action.location)

    def check_action(self, action) -> SpatialCheckResult:
        from literary_system.action_compiler.action_packet import ActionType
        act_type = action.action_type.upper()

        if act_type == ActionType.MOVE:
            result = self._check_move(action)
        elif act_type == ActionType.INTERACT:
            result = self._check_interact(action)
        elif act_type == ActionType.ACQUIRE:
            result = self._check_acquire(action)
        else:
            # REVEAL, HIDE: 공간 제약 없음
            return SpatialCheckResult(
                action_index=0, action_type=act_type,
                actor=action.actor, passed=True, gate_weight=1.0,
            )

        if result.violation:
            self._violations.append(result.violation)
        return result

    def check_packet(self, packet) -> list[SpatialCheckResult]:
        results = []
        for i, action in enumerate(packet.actions):
            result = self.check_action(action)
            result.action_index = i
            results.append(result)
        return results

    def packet_gate_weight(self, packet) -> float:
        """AbsoluteGate: 하나라도 실패하면 0.0."""
        results = self.check_packet(packet)
        for r in results:
            if not r.passed:
                return 0.0
        return 1.0

    def _check_move(self, action) -> SpatialCheckResult:
        if not action.location and self.strict_mode:
            v = SpatialViolation(
                action_type="MOVE", actor=action.actor, target=None,
                actor_location=self._get_location(action.actor),
                target_location=None,
                reason="MOVE 액션에 목적지(location)가 없습니다.",
            )
            return SpatialCheckResult(0, "MOVE", action.actor, False, 0.0, v)
        return SpatialCheckResult(0, "MOVE", action.actor, True, 1.0)

    def _check_interact(self, action) -> SpatialCheckResult:
        if not action.target:
            return SpatialCheckResult(0, "INTERACT", action.actor, True, 1.0)
        actor_loc = self._get_location(action.actor)
        target_loc = self._get_location(action.target)
        if actor_loc is None or target_loc is None:
            if self.strict_mode:
                v = SpatialViolation(
                    action_type="INTERACT", actor=action.actor, target=action.target,
                    actor_location=actor_loc, target_location=target_loc,
                    reason=f"위치 미지정: {action.actor}={actor_loc}, {action.target}={target_loc}",
                )
                return SpatialCheckResult(0, "INTERACT", action.actor, False, 0.0, v)
            return SpatialCheckResult(0, "INTERACT", action.actor, True, 1.0)
        if actor_loc != target_loc:
            v = SpatialViolation(
                action_type="INTERACT", actor=action.actor, target=action.target,
                actor_location=actor_loc, target_location=target_loc,
                reason=(
                    f"공간 제약 위반: {action.actor}(위치:{actor_loc})와 "
                    f"{action.target}(위치:{target_loc})은 다른 장소."
                ),
            )
            return SpatialCheckResult(0, "INTERACT", action.actor, False, 0.0, v)
        return SpatialCheckResult(0, "INTERACT", action.actor, True, 1.0)

    def _check_acquire(self, action) -> SpatialCheckResult:
        if not action.target:
            return SpatialCheckResult(0, "ACQUIRE", action.actor, True, 1.0)
        actor_loc = self._get_location(action.actor)
        obj_loc = self._get_location(action.target)
        if actor_loc is None or obj_loc is None:
            if self.strict_mode:
                v = SpatialViolation(
                    action_type="ACQUIRE", actor=action.actor, target=action.target,
                    actor_location=actor_loc, target_location=obj_loc,
                    reason="위치 미지정으로 ACQUIRE 검증 불가.",
                )
                return SpatialCheckResult(0, "ACQUIRE", action.actor, False, 0.0, v)
            return SpatialCheckResult(0, "ACQUIRE", action.actor, True, 1.0)
        if actor_loc != obj_loc:
            v = SpatialViolation(
                action_type="ACQUIRE", actor=action.actor, target=action.target,
                actor_location=actor_loc, target_location=obj_loc,
                reason=f"{action.actor}({actor_loc})는 {action.target}({obj_loc})와 다른 위치.",
            )
            return SpatialCheckResult(0, "ACQUIRE", action.actor, False, 0.0, v)
        return SpatialCheckResult(0, "ACQUIRE", action.actor, True, 1.0)

    @property
    def violations(self) -> list[SpatialViolation]:
        return list(self._violations)

    def clear_violations(self) -> None:
        self._violations.clear()

    def stats(self) -> dict[str, Any]:
        return {
            "total_violations": len(self._violations),
            "strict_mode": self.strict_mode,
            "tracked_entities": len(self._index.to_dict()),
        }
