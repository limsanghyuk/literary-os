"""V700 — AgentCollaborationProtocol (SP-D.2) ADR-162: 에이전트 간 협업 프로토콜."""
from __future__ import annotations
import time, uuid, logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from literary_system.agents.agent_message import AgentBus, AgentMessage, MessagePriority
from literary_system.agents.agent_task import AgentTask, TaskStatus

logger = logging.getLogger(__name__)


class CollaborationState(Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CollaborationRole(Enum):
    INITIATOR = "initiator"
    PARTICIPANT = "participant"
    OBSERVER = "observer"
    COORDINATOR = "coordinator"


@dataclass
class CollaborationMember:
    agent_id: str
    role: CollaborationRole
    joined_at: float = field(default_factory=time.time)
    contributions: int = 0
    active: bool = True


@dataclass
class CollaborationSession:
    """에이전트 간 협업 세션."""
    session_id: str
    initiator_id: str
    goal: str
    state: CollaborationState = CollaborationState.PROPOSED
    members: Dict[str, CollaborationMember] = field(default_factory=dict)
    messages: List[str] = field(default_factory=list)  # message_ids
    result: Optional[Any] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_member(self, agent_id: str, role: CollaborationRole) -> CollaborationMember:
        member = CollaborationMember(agent_id=agent_id, role=role)
        self.members[agent_id] = member
        self.updated_at = time.time()
        return member

    def remove_member(self, agent_id: str) -> bool:
        if agent_id in self.members:
            self.members[agent_id].active = False
            self.updated_at = time.time()
            return True
        return False

    def active_members(self) -> List[CollaborationMember]:
        return [m for m in self.members.values() if m.active]

    def member_count(self) -> int:
        return len(self.active_members())

    def is_terminal(self) -> bool:
        return self.state in (
            CollaborationState.COMPLETED,
            CollaborationState.FAILED,
            CollaborationState.CANCELLED,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "initiator_id": self.initiator_id,
            "goal": self.goal,
            "state": self.state.value,
            "member_count": self.member_count(),
            "message_count": len(self.messages),
            "result": self.result,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class AgentCollaborationProtocol:
    """멀티에이전트 협업 프로토콜 관리자.

    AgentBus 기반 메시지 교환으로 협업 세션 수명주기를 관리한다.
    ADR-162: 제안→수락→활성→완료/실패 상태 전이.
    """

    def __init__(self, bus: Optional[AgentBus] = None) -> None:
        self._bus = bus or AgentBus()
        self._sessions: Dict[str, CollaborationSession] = {}
        self._hooks: Dict[str, List[Callable]] = {}  # event → callbacks

    # ── 세션 생명주기 ──────────────────────────────────────────────────

    def propose(self, initiator_id: str, goal: str,
                participants: Optional[List[str]] = None,
                metadata: Optional[Dict[str, Any]] = None) -> CollaborationSession:
        """새 협업 세션 제안."""
        session_id = str(uuid.uuid4())
        session = CollaborationSession(
            session_id=session_id,
            initiator_id=initiator_id,
            goal=goal,
            metadata=metadata or {},
        )
        session.add_member(initiator_id, CollaborationRole.INITIATOR)
        for pid in (participants or []):
            session.add_member(pid, CollaborationRole.PARTICIPANT)
        self._sessions[session_id] = session

        # 버스로 제안 브로드캐스트
        msg = AgentMessage.broadcast(
            sender=initiator_id,
            payload={"event": "collaboration_proposed", "session_id": session_id, "goal": goal},
            priority=MessagePriority.NORMAL,
        )
        self._bus.publish(msg)
        self._fire("proposed", session)
        logger.debug("[Collab] proposed session=%s goal=%s", session_id[:8], goal)
        return session

    def accept(self, session_id: str, agent_id: str) -> bool:
        """에이전트가 협업 참여를 수락."""
        session = self._sessions.get(session_id)
        if not session or session.state != CollaborationState.PROPOSED:
            return False
        if agent_id not in session.members:
            session.add_member(agent_id, CollaborationRole.PARTICIPANT)
        session.state = CollaborationState.ACCEPTED
        session.updated_at = time.time()
        self._fire("accepted", session)
        return True

    def start(self, session_id: str) -> bool:
        """협업 세션 시작 (ACCEPTED → ACTIVE)."""
        session = self._sessions.get(session_id)
        if not session or session.state != CollaborationState.ACCEPTED:
            return False
        session.state = CollaborationState.ACTIVE
        session.updated_at = time.time()
        self._fire("started", session)
        return True

    def complete(self, session_id: str, result: Any = None) -> bool:
        """협업 세션 완료."""
        session = self._sessions.get(session_id)
        if not session or session.state != CollaborationState.ACTIVE:
            return False
        session.state = CollaborationState.COMPLETED
        session.result = result
        session.updated_at = time.time()
        self._fire("completed", session)
        return True

    def fail(self, session_id: str, reason: str = "") -> bool:
        """협업 세션 실패."""
        session = self._sessions.get(session_id)
        if not session or session.is_terminal():
            return False
        session.state = CollaborationState.FAILED
        session.metadata["failure_reason"] = reason
        session.updated_at = time.time()
        self._fire("failed", session)
        return True

    def cancel(self, session_id: str) -> bool:
        """협업 세션 취소."""
        session = self._sessions.get(session_id)
        if not session or session.is_terminal():
            return False
        session.state = CollaborationState.CANCELLED
        session.updated_at = time.time()
        self._fire("cancelled", session)
        return True

    # ── 메시지 교환 ────────────────────────────────────────────────────

    def send(self, session_id: str, sender_id: str,
             content: Any, priority: MessagePriority = MessagePriority.NORMAL) -> Optional[str]:
        """협업 세션 내 메시지 전송."""
        session = self._sessions.get(session_id)
        if not session or session.state != CollaborationState.ACTIVE:
            return None
        if sender_id not in session.members:
            return None
        msg = AgentMessage.broadcast(
            sender=sender_id,
            payload={"session_id": session_id, "data": content},
            priority=priority,
        )
        self._bus.publish(msg)
        session.messages.append(msg.message_id)
        if sender_id in session.members:
            session.members[sender_id].contributions += 1
        session.updated_at = time.time()
        return msg.message_id

    def contribute(self, session_id: str, agent_id: str) -> bool:
        """에이전트 기여 카운트 증가."""
        session = self._sessions.get(session_id)
        if not session or agent_id not in session.members:
            return False
        session.members[agent_id].contributions += 1
        return True

    # ── 훅·조회 ────────────────────────────────────────────────────────

    def on(self, event: str, callback: Callable) -> None:
        """이벤트 훅 등록 (proposed/accepted/started/completed/failed/cancelled)."""
        self._hooks.setdefault(event, []).append(callback)

    def _fire(self, event: str, session: CollaborationSession) -> None:
        for cb in self._hooks.get(event, []):
            try:
                cb(session)
            except Exception as exc:
                logger.warning("[Collab] hook error event=%s: %s", event, exc)

    def get_session(self, session_id: str) -> Optional[CollaborationSession]:
        return self._sessions.get(session_id)

    def active_sessions(self) -> List[CollaborationSession]:
        return [s for s in self._sessions.values()
                if s.state == CollaborationState.ACTIVE]

    def all_sessions(self) -> List[CollaborationSession]:
        return list(self._sessions.values())

    def stats(self) -> Dict[str, Any]:
        states = {}
        for s in self._sessions.values():
            states[s.state.value] = states.get(s.state.value, 0) + 1
        return {"total": len(self._sessions), "by_state": states,
                "active": len(self.active_sessions())}


ADR_162 = {
    "id": "ADR-162",
    "title": "AgentCollaborationProtocol",
    "status": "accepted",
    "decision": "제안→수락→활성→완료/실패 협업 세션 수명주기. AgentBus 기반 메시지 교환.",
    "version": "V700",
}
