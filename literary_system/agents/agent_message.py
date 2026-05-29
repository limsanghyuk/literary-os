"""
V696 — AgentMessage + AgentBus (SP-D.2 MultiAgent Coordination Layer)
ADR-158: 에이전트 간 메시지 포맷 표준화 및 버스 구조.

LLM-0 원칙: 외부 LLM API 직접 호출 없음.
DEV_MODE: False (기본값).
"""
from __future__ import annotations

import uuid
import time
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ── 열거형 ────────────────────────────────────────────────────────────────────

class MessageType(Enum):
    """에이전트 메시지 유형."""
    REQUEST    = "request"     # 작업 요청
    RESPONSE   = "response"    # 요청 응답
    EVENT      = "event"       # 이벤트 알림
    BROADCAST  = "broadcast"   # 전체 브로드캐스트
    HEARTBEAT  = "heartbeat"   # 생존 신호
    ERROR      = "error"       # 에러 보고
    ACK        = "ack"         # 수신 확인


class MessagePriority(Enum):
    """메시지 우선순위."""
    LOW      = 0
    NORMAL   = 1
    HIGH     = 2
    CRITICAL = 3


class DeliveryStatus(Enum):
    """메시지 전달 상태."""
    PENDING    = "pending"
    DELIVERED  = "delivered"
    FAILED     = "failed"
    EXPIRED    = "expired"


# ── 핵심 데이터 클래스 ─────────────────────────────────────────────────────────

@dataclass
class AgentMessage:
    """에이전트 간 통신 메시지 표준 포맷 (ADR-158).

    Attributes:
        message_id: 메시지 고유 ID (UUID v4)
        sender: 송신 에이전트 ID
        receiver: 수신 에이전트 ID (None = 브로드캐스트)
        msg_type: 메시지 유형
        payload: 메시지 본문 (임의 dict)
        timestamp: 생성 시각 (Unix epoch, float)
        priority: 우선순위
        correlation_id: 요청-응답 연결 ID
        ttl_seconds: 메시지 유효 기간 (초, None = 무한)
        status: 전달 상태
    """
    sender: str
    msg_type: MessageType
    payload: Dict[str, Any]
    receiver: Optional[str] = None
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    priority: MessagePriority = MessagePriority.NORMAL
    correlation_id: Optional[str] = None
    ttl_seconds: Optional[float] = None
    status: DeliveryStatus = DeliveryStatus.PENDING

    # ── 팩토리 메서드 ────────────────────────────────────────────────────

    @classmethod
    def request(
        cls,
        sender: str,
        receiver: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> "AgentMessage":
        """REQUEST 메시지 생성."""
        return cls(
            sender=sender,
            receiver=receiver,
            msg_type=MessageType.REQUEST,
            payload=payload,
            priority=priority,
            correlation_id=str(uuid.uuid4()),
        )

    @classmethod
    def response(
        cls,
        sender: str,
        receiver: str,
        payload: Dict[str, Any],
        correlation_id: str,
    ) -> "AgentMessage":
        """RESPONSE 메시지 생성 (correlation_id 연결)."""
        return cls(
            sender=sender,
            receiver=receiver,
            msg_type=MessageType.RESPONSE,
            payload=payload,
            correlation_id=correlation_id,
        )

    @classmethod
    def broadcast(
        cls,
        sender: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> "AgentMessage":
        """BROADCAST 메시지 생성."""
        return cls(
            sender=sender,
            receiver=None,
            msg_type=MessageType.BROADCAST,
            payload=payload,
            priority=priority,
        )

    @classmethod
    def heartbeat(cls, sender: str) -> "AgentMessage":
        """HEARTBEAT 메시지 생성."""
        return cls(
            sender=sender,
            msg_type=MessageType.HEARTBEAT,
            payload={"ts": time.time()},
            priority=MessagePriority.LOW,
        )

    # ── 직렬화 ──────────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id":    self.message_id,
            "sender":        self.sender,
            "receiver":      self.receiver,
            "msg_type":      self.msg_type.value,
            "payload":       self.payload,
            "timestamp":     self.timestamp,
            "priority":      self.priority.value,
            "correlation_id": self.correlation_id,
            "ttl_seconds":   self.ttl_seconds,
            "status":        self.status.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        return cls(
            message_id=data.get("message_id", str(uuid.uuid4())),
            sender=data["sender"],
            receiver=data.get("receiver"),
            msg_type=MessageType(data["msg_type"]),
            payload=data.get("payload", {}),
            timestamp=data.get("timestamp", time.time()),
            priority=MessagePriority(data.get("priority", MessagePriority.NORMAL.value)),
            correlation_id=data.get("correlation_id"),
            ttl_seconds=data.get("ttl_seconds"),
            status=DeliveryStatus(data.get("status", DeliveryStatus.PENDING.value)),
        )

    def is_expired(self) -> bool:
        """TTL 초과 여부 확인."""
        if self.ttl_seconds is None:
            return False
        return (time.time() - self.timestamp) > self.ttl_seconds

    def is_broadcast(self) -> bool:
        return self.receiver is None or self.msg_type == MessageType.BROADCAST


# ── AgentBus ──────────────────────────────────────────────────────────────────

class AgentBus:
    """멀티에이전트 메시지 버스 (Pub/Sub 브로커).

    에이전트 간 비동기 메시지 라우팅을 담당한다.
    - publish(): 특정 수신자 또는 브로드캐스트 발행
    - subscribe(): 에이전트별 핸들러 등록
    - subscribe_type(): 메시지 유형별 핸들러 등록
    - get_messages(): 수신함 조회
    """

    def __init__(self, name: str = "default-bus") -> None:
        self.name = name
        self._subscribers: Dict[str, List[Callable[[AgentMessage], None]]] = defaultdict(list)
        self._type_subscribers: Dict[MessageType, List[Callable[[AgentMessage], None]]] = defaultdict(list)
        self._inbox: Dict[str, List[AgentMessage]] = defaultdict(list)
        self._published: List[AgentMessage] = []
        self._stats: Dict[str, int] = {
            "published": 0,
            "delivered": 0,
            "expired": 0,
            "failed": 0,
        }

    # ── 구독 ──────────────────────────────────────────────────────────

    def subscribe(
        self,
        agent_id: str,
        handler: Callable[[AgentMessage], None],
    ) -> None:
        """특정 에이전트 ID를 대상으로 하는 메시지를 구독한다."""
        self._subscribers[agent_id].append(handler)
        logger.debug("[AgentBus] %s subscribed agent=%s", self.name, agent_id)

    def unsubscribe(self, agent_id: str) -> None:
        """에이전트 구독 해제."""
        self._subscribers.pop(agent_id, None)
        logger.debug("[AgentBus] %s unsubscribed agent=%s", self.name, agent_id)

    def subscribe_type(
        self,
        msg_type: MessageType,
        handler: Callable[[AgentMessage], None],
    ) -> None:
        """메시지 유형별 구독."""
        self._type_subscribers[msg_type].append(handler)

    # ── 발행 ──────────────────────────────────────────────────────────

    def publish(self, message: AgentMessage) -> bool:
        """메시지를 버스에 발행한다.

        Returns:
            True: 하나 이상의 핸들러 또는 수신함에 전달됨.
            False: 메시지 만료 또는 수신자 없음.
        """
        if message.is_expired():
            message.status = DeliveryStatus.EXPIRED
            self._stats["expired"] += 1
            logger.warning("[AgentBus] Message %s expired before delivery", message.message_id)
            return False

        self._published.append(message)
        self._stats["published"] += 1
        delivered = False

        # 1. 유형별 핸들러 호출
        for handler in self._type_subscribers.get(message.msg_type, []):
            try:
                handler(message)
                delivered = True
            except Exception as exc:
                logger.error("[AgentBus] type-handler error: %s", exc)

        # 2. 브로드캐스트: 모든 구독 에이전트에 전달
        if message.is_broadcast():
            for agent_id, handlers in self._subscribers.items():
                if agent_id == message.sender:
                    continue
                self._inbox[agent_id].append(message)
                for handler in handlers:
                    try:
                        handler(message)
                        delivered = True
                    except Exception as exc:
                        logger.error("[AgentBus] broadcast-handler error: %s", exc)
        else:
            # 3. 특정 수신자
            receiver = message.receiver
            if receiver:
                self._inbox[receiver].append(message)
                for handler in self._subscribers.get(receiver, []):
                    try:
                        handler(message)
                        delivered = True
                    except Exception as exc:
                        logger.error("[AgentBus] receiver-handler error: %s", exc)

        if delivered:
            message.status = DeliveryStatus.DELIVERED
            self._stats["delivered"] += 1
        else:
            # 수신함에는 쌓였으므로 PENDING 유지 (polling 방식 지원)
            if not message.is_broadcast() and message.receiver:
                delivered = True  # 수신함에 저장됨

        return delivered

    def get_messages(
        self,
        agent_id: str,
        msg_type: Optional[MessageType] = None,
        clear: bool = False,
    ) -> List[AgentMessage]:
        """에이전트 수신함 조회.

        Args:
            agent_id: 에이전트 ID
            msg_type: 특정 유형만 필터 (None = 전체)
            clear: True면 조회 후 수신함 비우기
        """
        msgs = self._inbox.get(agent_id, [])
        # 만료 메시지 제거
        msgs = [m for m in msgs if not m.is_expired()]
        if msg_type is not None:
            msgs = [m for m in msgs if m.msg_type == msg_type]
        if clear:
            self._inbox[agent_id] = []
        return msgs

    def stats(self) -> Dict[str, int]:
        """버스 통계."""
        return dict(self._stats)

    def agent_count(self) -> int:
        """구독 에이전트 수."""
        return len(self._subscribers)

    def pending_count(self, agent_id: str) -> int:
        """에이전트 수신함 대기 메시지 수."""
        return len(self._inbox.get(agent_id, []))

    def all_published(self) -> List[AgentMessage]:
        """발행된 전체 메시지 목록."""
        return list(self._published)

    def clear_inbox(self, agent_id: str) -> None:
        """에이전트 수신함 초기화."""
        self._inbox[agent_id] = []


# ── ADR-158 문서 상수 ─────────────────────────────────────────────────────────

ADR_158 = {
    "id": "ADR-158",
    "title": "AgentMessage + AgentBus — MultiAgent 통신 표준",
    "status": "accepted",
    "context": "SP-D.2 MultiAgent Coordination Layer — 에이전트 간 메시지 포맷 표준화 필요",
    "decision": (
        "AgentMessage dataclass로 통신 포맷 표준화. "
        "AgentBus로 Pub/Sub 브로커 구현 (LLM-0: 외부 API 없음). "
        "MessageType 7종, MessagePriority 4단계, TTL 지원."
    ),
    "consequences": [
        "에이전트 간 직접 의존 제거 (버스를 통한 간접 통신)",
        "메시지 유형별 핸들러로 관심사 분리",
        "TTL로 만료 메시지 자동 처리",
    ],
    "version": "V696",
}
