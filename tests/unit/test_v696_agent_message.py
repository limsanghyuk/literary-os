"""
test_v696_agent_message.py — V696 AgentMessage + AgentBus 단위 테스트 (ADR-158)
TC01~TC33: 33개 테스트
"""
from __future__ import annotations

import time
import pytest

from literary_system.agents.agent_message import (
    AgentMessage, AgentBus,
    MessageType, MessagePriority, DeliveryStatus,
)


# ── TC01~TC08: AgentMessage 기본 생성 ─────────────────────────────────────────

class TestAgentMessageCreation:
    def test_tc01_basic_creation(self):
        msg = AgentMessage(
            sender="agent_a",
            msg_type=MessageType.REQUEST,
            payload={"action": "generate"},
        )
        assert msg.sender == "agent_a"
        assert msg.msg_type == MessageType.REQUEST
        assert msg.payload == {"action": "generate"}

    def test_tc02_auto_message_id(self):
        m1 = AgentMessage(sender="a", msg_type=MessageType.EVENT, payload={})
        m2 = AgentMessage(sender="a", msg_type=MessageType.EVENT, payload={})
        assert m1.message_id != m2.message_id

    def test_tc03_auto_timestamp(self):
        before = time.time()
        msg = AgentMessage(sender="a", msg_type=MessageType.EVENT, payload={})
        after = time.time()
        assert before <= msg.timestamp <= after

    def test_tc04_default_priority(self):
        msg = AgentMessage(sender="a", msg_type=MessageType.REQUEST, payload={})
        assert msg.priority == MessagePriority.NORMAL

    def test_tc05_default_status(self):
        msg = AgentMessage(sender="a", msg_type=MessageType.REQUEST, payload={})
        assert msg.status == DeliveryStatus.PENDING

    def test_tc06_request_factory(self):
        msg = AgentMessage.request("agent_a", "agent_b", {"task": "write"})
        assert msg.msg_type == MessageType.REQUEST
        assert msg.sender == "agent_a"
        assert msg.receiver == "agent_b"
        assert msg.correlation_id is not None

    def test_tc07_response_factory(self):
        req = AgentMessage.request("agent_a", "agent_b", {"task": "write"})
        resp = AgentMessage.response("agent_b", "agent_a", {"result": "ok"}, req.correlation_id)
        assert resp.msg_type == MessageType.RESPONSE
        assert resp.correlation_id == req.correlation_id

    def test_tc08_broadcast_factory(self):
        msg = AgentMessage.broadcast("agent_a", {"event": "started"})
        assert msg.msg_type == MessageType.BROADCAST
        assert msg.receiver is None
        assert msg.is_broadcast() is True


# ── TC09~TC14: AgentMessage 직렬화 ───────────────────────────────────────────

class TestAgentMessageSerialization:
    def test_tc09_to_dict(self):
        msg = AgentMessage.request("a", "b", {"x": 1})
        d = msg.to_dict()
        assert d["sender"] == "a"
        assert d["receiver"] == "b"
        assert d["msg_type"] == "request"
        assert d["payload"] == {"x": 1}

    def test_tc10_from_dict_roundtrip(self):
        msg = AgentMessage.request("a", "b", {"x": 1}, MessagePriority.HIGH)
        d = msg.to_dict()
        msg2 = AgentMessage.from_dict(d)
        assert msg2.message_id == msg.message_id
        assert msg2.sender == msg.sender
        assert msg2.msg_type == msg.msg_type
        assert msg2.priority == MessagePriority.HIGH

    def test_tc11_heartbeat_factory(self):
        msg = AgentMessage.heartbeat("agent_x")
        assert msg.msg_type == MessageType.HEARTBEAT
        assert msg.priority == MessagePriority.LOW
        assert "ts" in msg.payload

    def test_tc12_ttl_expired(self):
        msg = AgentMessage(
            sender="a",
            msg_type=MessageType.REQUEST,
            payload={},
            ttl_seconds=0.001,
        )
        time.sleep(0.01)
        assert msg.is_expired() is True

    def test_tc13_ttl_not_expired(self):
        msg = AgentMessage(
            sender="a",
            msg_type=MessageType.REQUEST,
            payload={},
            ttl_seconds=60.0,
        )
        assert msg.is_expired() is False

    def test_tc14_no_ttl_never_expires(self):
        msg = AgentMessage(sender="a", msg_type=MessageType.EVENT, payload={}, ttl_seconds=None)
        assert msg.is_expired() is False


# ── TC15~TC25: AgentBus 발행/구독 ────────────────────────────────────────────

class TestAgentBus:
    def setup_method(self):
        self.bus = AgentBus(name="test-bus")

    def test_tc15_bus_creation(self):
        assert self.bus.name == "test-bus"
        assert self.bus.agent_count() == 0

    def test_tc16_subscribe(self):
        received = []
        self.bus.subscribe("agent_b", received.append)
        assert self.bus.agent_count() == 1

    def test_tc17_publish_to_subscriber(self):
        received = []
        self.bus.subscribe("agent_b", received.append)
        msg = AgentMessage.request("agent_a", "agent_b", {"task": "write"})
        result = self.bus.publish(msg)
        assert result is True
        assert len(received) == 1
        assert received[0].sender == "agent_a"

    def test_tc18_message_inbox(self):
        msg = AgentMessage.request("agent_a", "agent_b", {"x": 1})
        self.bus.publish(msg)
        inbox = self.bus.get_messages("agent_b")
        assert len(inbox) == 1

    def test_tc19_broadcast_to_all(self):
        r1, r2, r3 = [], [], []
        self.bus.subscribe("b1", r1.append)
        self.bus.subscribe("b2", r2.append)
        self.bus.subscribe("b3", r3.append)
        msg = AgentMessage.broadcast("agent_a", {"event": "ready"})
        self.bus.publish(msg)
        assert len(r1) == 1 and len(r2) == 1 and len(r3) == 1

    def test_tc20_broadcast_excludes_sender(self):
        received = []
        self.bus.subscribe("agent_a", received.append)
        msg = AgentMessage.broadcast("agent_a", {"event": "self"})
        self.bus.publish(msg)
        assert len(received) == 0  # 자신에게는 전달 안 됨

    def test_tc21_unsubscribe(self):
        received = []
        self.bus.subscribe("agent_b", received.append)
        self.bus.unsubscribe("agent_b")
        msg = AgentMessage.request("a", "agent_b", {})
        self.bus.publish(msg)
        assert len(received) == 0

    def test_tc22_type_subscriber(self):
        received = []
        self.bus.subscribe_type(MessageType.EVENT, received.append)
        msg = AgentMessage(sender="a", msg_type=MessageType.EVENT, payload={})
        self.bus.publish(msg)
        assert len(received) == 1

    def test_tc23_type_subscriber_filter(self):
        received = []
        self.bus.subscribe_type(MessageType.EVENT, received.append)
        req = AgentMessage.request("a", "b", {})
        self.bus.publish(req)
        assert len(received) == 0  # REQUEST는 EVENT 구독자에게 안 감

    def test_tc24_expired_message_not_delivered(self):
        received = []
        self.bus.subscribe("agent_b", received.append)
        msg = AgentMessage(
            sender="a",
            receiver="agent_b",
            msg_type=MessageType.REQUEST,
            payload={},
            ttl_seconds=0.001,
        )
        time.sleep(0.01)
        result = self.bus.publish(msg)
        assert result is False
        assert len(received) == 0
        assert self.bus.stats()["expired"] == 1

    def test_tc25_stats(self):
        self.bus.subscribe("b", lambda m: None)
        for i in range(5):
            self.bus.publish(AgentMessage.request("a", "b", {"i": i}))
        s = self.bus.stats()
        assert s["published"] == 5
        assert s["delivered"] == 5


# ── TC26~TC33: 복합 시나리오 ─────────────────────────────────────────────────

class TestAgentBusScenarios:
    def setup_method(self):
        self.bus = AgentBus()

    def test_tc26_request_response_pattern(self):
        """요청-응답 패턴: correlation_id로 연결."""
        responses = []
        self.bus.subscribe("agent_a", responses.append)

        # A→B 요청
        req = AgentMessage.request("agent_a", "agent_b", {"q": "write scene"})
        self.bus.publish(req)

        # B→A 응답 (correlation_id 연결)
        resp = AgentMessage.response("agent_b", "agent_a", {"r": "done"}, req.correlation_id)
        self.bus.publish(resp)

        assert len(responses) == 1
        assert responses[0].correlation_id == req.correlation_id

    def test_tc27_multiple_messages_ordering(self):
        msgs = []
        self.bus.subscribe("b", msgs.append)
        for i in range(10):
            self.bus.publish(AgentMessage.request("a", "b", {"seq": i}))
        assert len(msgs) == 10
        seqs = [m.payload["seq"] for m in msgs]
        assert seqs == list(range(10))

    def test_tc28_priority_high_creation(self):
        msg = AgentMessage.request("a", "b", {}, priority=MessagePriority.HIGH)
        assert msg.priority == MessagePriority.HIGH

    def test_tc29_get_messages_by_type(self):
        self.bus.publish(AgentMessage.request("a", "b", {"t": "req"}))
        self.bus.publish(AgentMessage(sender="c", receiver="b", msg_type=MessageType.EVENT, payload={"t": "evt"}))
        reqs = self.bus.get_messages("b", msg_type=MessageType.REQUEST)
        assert len(reqs) == 1
        assert reqs[0].payload["t"] == "req"

    def test_tc30_get_messages_clear(self):
        self.bus.publish(AgentMessage.request("a", "b", {}))
        self.bus.get_messages("b", clear=True)
        assert self.bus.pending_count("b") == 0

    def test_tc31_pending_count(self):
        for i in range(3):
            self.bus.publish(AgentMessage.request("a", "b", {"i": i}))
        assert self.bus.pending_count("b") == 3

    def test_tc32_all_published(self):
        self.bus.publish(AgentMessage.broadcast("a", {}))
        self.bus.publish(AgentMessage.request("a", "b", {}))
        assert len(self.bus.all_published()) == 2

    def test_tc33_adr_158_constants(self):
        from literary_system.agents.agent_message import ADR_158
        assert ADR_158["id"] == "ADR-158"
        assert ADR_158["status"] == "accepted"
        assert "AgentMessage" in ADR_158["decision"]
