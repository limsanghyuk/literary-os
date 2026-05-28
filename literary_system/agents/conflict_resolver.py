"""V701 — AgentConflictResolver (SP-D.2) ADR-163: 에이전트 간 충돌 해소."""
from __future__ import annotations
import time, uuid, logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    RESOURCE = "resource"         # 자원 경합
    TASK = "task"                 # 작업 중복 할당
    DECISION = "decision"         # 의사결정 불일치
    DATA = "data"                 # 데이터 불일치
    PRIORITY = "priority"         # 우선순위 충돌


class ResolutionStrategy(Enum):
    PRIORITY_BASED = "priority_based"   # 우선순위 높은 에이전트 우선
    CONSENSUS = "consensus"             # 다수결
    MEDIATOR = "mediator"               # 중재자 결정
    TIMESTAMP = "timestamp"             # 먼저 요청한 쪽 우선
    RANDOM = "random"                   # 랜덤 (fallback)


class ConflictState(Enum):
    OPEN = "open"
    RESOLVING = "resolving"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


@dataclass
class ConflictParty:
    agent_id: str
    priority: int = 0         # 높을수록 우선
    claim: Any = None         # 에이전트의 주장/요청
    timestamp: float = field(default_factory=time.time)


@dataclass
class Conflict:
    conflict_id: str
    conflict_type: ConflictType
    parties: List[ConflictParty]
    state: ConflictState = ConflictState.OPEN
    strategy: ResolutionStrategy = ResolutionStrategy.PRIORITY_BASED
    winner: Optional[str] = None       # winning agent_id
    resolution: Optional[Any] = None
    reason: str = ""
    created_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_resolved(self) -> bool:
        return self.state in (ConflictState.RESOLVED, ConflictState.ESCALATED)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "type": self.conflict_type.value,
            "state": self.state.value,
            "strategy": self.strategy.value,
            "winner": self.winner,
            "party_count": len(self.parties),
            "resolved_at": self.resolved_at,
        }


class AgentConflictResolver:
    """멀티에이전트 충돌 해소기.

    ADR-163: 우선순위/합의/중재 전략으로 에이전트 간 충돌을 자동 해소한다.
    해소 불가 시 ESCALATED 상태로 전환하여 상위 레벨에 위임한다.
    """

    def __init__(self) -> None:
        self._conflicts: Dict[str, Conflict] = {}
        self._mediator: Optional[Callable[[Conflict], Any]] = None
        self._hooks: Dict[str, List[Callable]] = {}

    # ── 충돌 등록 ───────────────────────────────────────────────────────

    def register(
        self,
        conflict_type: ConflictType,
        parties: List[ConflictParty],
        strategy: ResolutionStrategy = ResolutionStrategy.PRIORITY_BASED,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Conflict:
        """새 충돌 등록."""
        cid = str(uuid.uuid4())
        conflict = Conflict(
            conflict_id=cid,
            conflict_type=conflict_type,
            parties=list(parties),
            strategy=strategy,
            metadata=metadata or {},
        )
        self._conflicts[cid] = conflict
        self._fire("registered", conflict)
        logger.debug("[Resolver] registered conflict=%s type=%s strategy=%s",
                     cid[:8], conflict_type.value, strategy.value)
        return conflict

    # ── 해소 전략 실행 ──────────────────────────────────────────────────

    def resolve(self, conflict_id: str) -> bool:
        """충돌 해소 시도. 성공 시 True."""
        conflict = self._conflicts.get(conflict_id)
        if not conflict or conflict.is_resolved():
            return False

        conflict.state = ConflictState.RESOLVING
        try:
            ok = self._apply_strategy(conflict)
        except Exception as exc:
            logger.warning("[Resolver] strategy error: %s", exc)
            ok = False

        if ok:
            conflict.state = ConflictState.RESOLVED
            conflict.resolved_at = time.time()
            self._fire("resolved", conflict)
        else:
            conflict.state = ConflictState.ESCALATED
            self._fire("escalated", conflict)

        return ok

    def _apply_strategy(self, conflict: Conflict) -> bool:
        s = conflict.strategy
        parties = conflict.parties

        if not parties:
            return False

        if s == ResolutionStrategy.PRIORITY_BASED:
            winner = max(parties, key=lambda p: p.priority)
            conflict.winner = winner.agent_id
            conflict.resolution = winner.claim
            conflict.reason = f"priority_based: agent {winner.agent_id} priority={winner.priority}"
            return True

        elif s == ResolutionStrategy.TIMESTAMP:
            winner = min(parties, key=lambda p: p.timestamp)
            conflict.winner = winner.agent_id
            conflict.resolution = winner.claim
            conflict.reason = f"timestamp: agent {winner.agent_id} was first"
            return True

        elif s == ResolutionStrategy.CONSENSUS:
            # 단순 다수결: claims 중 가장 많은 값
            from collections import Counter
            claims = [str(p.claim) for p in parties]
            most_common, count = Counter(claims).most_common(1)[0]
            if count > len(parties) // 2:
                # 명확한 다수
                conflict.winner = next(
                    p.agent_id for p in parties if str(p.claim) == most_common
                )
                conflict.resolution = most_common
                conflict.reason = f"consensus: {count}/{len(parties)} agreed"
                return True
            return False  # 합의 불가 → escalate

        elif s == ResolutionStrategy.MEDIATOR:
            if self._mediator is None:
                return False
            result = self._mediator(conflict)
            if result is not None:
                conflict.resolution = result
                conflict.reason = "mediator decision"
                # winner는 mediator가 resolution 안에 포함할 수 있음
                return True
            return False

        elif s == ResolutionStrategy.RANDOM:
            import random
            winner = random.choice(parties)
            conflict.winner = winner.agent_id
            conflict.resolution = winner.claim
            conflict.reason = "random selection"
            return True

        return False

    # ── 중재자·훅 ────────────────────────────────────────────────────────

    def set_mediator(self, fn: Callable[[Conflict], Any]) -> None:
        """중재자 함수 등록 (MEDIATOR 전략에서 사용)."""
        self._mediator = fn

    def on(self, event: str, cb: Callable) -> None:
        self._hooks.setdefault(event, []).append(cb)

    def _fire(self, event: str, conflict: Conflict) -> None:
        for cb in self._hooks.get(event, []):
            try:
                cb(conflict)
            except Exception as exc:
                logger.warning("[Resolver] hook error: %s", exc)

    # ── 조회 ────────────────────────────────────────────────────────────

    def get_conflict(self, conflict_id: str) -> Optional[Conflict]:
        return self._conflicts.get(conflict_id)

    def open_conflicts(self) -> List[Conflict]:
        return [c for c in self._conflicts.values()
                if c.state in (ConflictState.OPEN, ConflictState.RESOLVING)]

    def resolved_conflicts(self) -> List[Conflict]:
        return [c for c in self._conflicts.values()
                if c.state == ConflictState.RESOLVED]

    def escalated_conflicts(self) -> List[Conflict]:
        return [c for c in self._conflicts.values()
                if c.state == ConflictState.ESCALATED]

    def stats(self) -> Dict[str, Any]:
        total = len(self._conflicts)
        return {
            "total": total,
            "open": len(self.open_conflicts()),
            "resolved": len(self.resolved_conflicts()),
            "escalated": len(self.escalated_conflicts()),
        }


ADR_163 = {
    "id": "ADR-163",
    "title": "AgentConflictResolver",
    "status": "accepted",
    "decision": (
        "우선순위/합의/중재/타임스탬프/랜덤 5가지 전략으로 에이전트 충돌 해소. "
        "해소 불가 시 ESCALATED 전환."
    ),
    "version": "V701",
}
