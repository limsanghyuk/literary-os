"""V700 — AgentCollaborationProtocol 테스트 (33 TC)."""
import pytest
from literary_system.agents.collaboration_protocol import (
    AgentCollaborationProtocol, CollaborationState, CollaborationRole,
    CollaborationSession, ADR_162,
)
from literary_system.agents.agent_message import AgentBus, MessagePriority


# ── 헬퍼 ──────────────────────────────────────────────────────────────
def make_proto() -> AgentCollaborationProtocol:
    return AgentCollaborationProtocol(bus=AgentBus())


# ══════════════════════════════════════════════════════════════════════
class TestCollaborationSession:
    def test_tc01_propose_creates_session(self):
        p = make_proto()
        s = p.propose("agent-A", "write chapter 1")
        assert s.session_id
        assert s.initiator_id == "agent-A"
        assert s.goal == "write chapter 1"
        assert s.state == CollaborationState.PROPOSED

    def test_tc02_initiator_added_as_member(self):
        p = make_proto()
        s = p.propose("agent-A", "goal")
        assert "agent-A" in s.members
        assert s.members["agent-A"].role == CollaborationRole.INITIATOR

    def test_tc03_participants_added(self):
        p = make_proto()
        s = p.propose("agent-A", "goal", participants=["agent-B", "agent-C"])
        assert "agent-B" in s.members
        assert "agent-C" in s.members
        assert s.members["agent-B"].role == CollaborationRole.PARTICIPANT

    def test_tc04_accept_state_transition(self):
        p = make_proto()
        s = p.propose("A", "goal", participants=["B"])
        ok = p.accept(s.session_id, "B")
        assert ok
        assert s.state == CollaborationState.ACCEPTED

    def test_tc05_start_state_transition(self):
        p = make_proto()
        s = p.propose("A", "goal", participants=["B"])
        p.accept(s.session_id, "B")
        ok = p.start(s.session_id)
        assert ok
        assert s.state == CollaborationState.ACTIVE

    def test_tc06_complete_state_transition(self):
        p = make_proto()
        s = p.propose("A", "goal", participants=["B"])
        p.accept(s.session_id, "B")
        p.start(s.session_id)
        ok = p.complete(s.session_id, result={"chapters": 1})
        assert ok
        assert s.state == CollaborationState.COMPLETED
        assert s.result == {"chapters": 1}

    def test_tc07_fail_state_transition(self):
        p = make_proto()
        s = p.propose("A", "goal", participants=["B"])
        p.accept(s.session_id, "B")
        p.start(s.session_id)
        ok = p.fail(s.session_id, reason="timeout")
        assert ok
        assert s.state == CollaborationState.FAILED
        assert s.metadata.get("failure_reason") == "timeout"

    def test_tc08_cancel_proposed(self):
        p = make_proto()
        s = p.propose("A", "goal")
        ok = p.cancel(s.session_id)
        assert ok
        assert s.state == CollaborationState.CANCELLED

    def test_tc09_is_terminal(self):
        p = make_proto()
        s = p.propose("A", "goal")
        assert not s.is_terminal()
        p.cancel(s.session_id)
        assert s.is_terminal()

    def test_tc10_cannot_accept_cancelled(self):
        p = make_proto()
        s = p.propose("A", "goal")
        p.cancel(s.session_id)
        ok = p.accept(s.session_id, "B")
        assert not ok

    def test_tc11_cannot_start_without_accept(self):
        p = make_proto()
        s = p.propose("A", "goal")
        ok = p.start(s.session_id)
        assert not ok

    def test_tc12_cannot_complete_non_active(self):
        p = make_proto()
        s = p.propose("A", "goal")
        ok = p.complete(s.session_id)
        assert not ok

    def test_tc13_member_count(self):
        p = make_proto()
        s = p.propose("A", "goal", participants=["B", "C"])
        assert s.member_count() == 3

    def test_tc14_remove_member(self):
        p = make_proto()
        s = p.propose("A", "goal", participants=["B"])
        ok = s.remove_member("B")
        assert ok
        assert s.member_count() == 1  # only A remains active

    def test_tc15_to_dict(self):
        p = make_proto()
        s = p.propose("A", "goal")
        d = s.to_dict()
        assert d["initiator_id"] == "A"
        assert d["goal"] == "goal"
        assert d["state"] == "proposed"

    def test_tc16_send_message_in_active_session(self):
        p = make_proto()
        s = p.propose("A", "goal", participants=["B"])
        p.accept(s.session_id, "B")
        p.start(s.session_id)
        mid = p.send(s.session_id, "A", "hello")
        assert mid is not None
        assert mid in s.messages

    def test_tc17_send_fails_non_active(self):
        p = make_proto()
        s = p.propose("A", "goal")
        mid = p.send(s.session_id, "A", "hello")
        assert mid is None

    def test_tc18_send_increments_contributions(self):
        p = make_proto()
        s = p.propose("A", "goal", participants=["B"])
        p.accept(s.session_id, "B")
        p.start(s.session_id)
        p.send(s.session_id, "A", "msg1")
        p.send(s.session_id, "A", "msg2")
        assert s.members["A"].contributions == 2

    def test_tc19_contribute_manual(self):
        p = make_proto()
        s = p.propose("A", "goal", participants=["B"])
        ok = p.contribute(s.session_id, "B")
        assert ok
        assert s.members["B"].contributions == 1

    def test_tc20_get_session(self):
        p = make_proto()
        s = p.propose("A", "goal")
        retrieved = p.get_session(s.session_id)
        assert retrieved is s

    def test_tc21_get_nonexistent_session(self):
        p = make_proto()
        assert p.get_session("nonexistent") is None

    def test_tc22_active_sessions(self):
        p = make_proto()
        s1 = p.propose("A", "g1", participants=["B"])
        p.accept(s1.session_id, "B"); p.start(s1.session_id)
        s2 = p.propose("A", "g2")
        active = p.active_sessions()
        assert s1 in active
        assert s2 not in active

    def test_tc23_all_sessions(self):
        p = make_proto()
        p.propose("A", "g1")
        p.propose("A", "g2")
        assert len(p.all_sessions()) == 2

    def test_tc24_stats(self):
        p = make_proto()
        p.propose("A", "g1")
        p.propose("A", "g2")
        st = p.stats()
        assert st["total"] == 2
        assert st["by_state"].get("proposed", 0) == 2

    def test_tc25_proposed_hook_fires(self):
        p = make_proto()
        fired = []
        p.on("proposed", lambda s: fired.append(s.session_id))
        s = p.propose("A", "goal")
        assert s.session_id in fired

    def test_tc26_completed_hook_fires(self):
        p = make_proto()
        fired = []
        p.on("completed", lambda s: fired.append(True))
        s = p.propose("A", "goal", participants=["B"])
        p.accept(s.session_id, "B"); p.start(s.session_id)
        p.complete(s.session_id)
        assert fired == [True]

    def test_tc27_failed_hook_fires(self):
        p = make_proto()
        reasons = []
        p.on("failed", lambda s: reasons.append(s.metadata.get("failure_reason")))
        s = p.propose("A", "goal", participants=["B"])
        p.accept(s.session_id, "B"); p.start(s.session_id)
        p.fail(s.session_id, "network error")
        assert reasons == ["network error"]

    def test_tc28_accept_new_member(self):
        """accept() 시 기존 멤버가 아닌 에이전트도 참여 가능."""
        p = make_proto()
        s = p.propose("A", "goal")
        ok = p.accept(s.session_id, "latejoiner")
        assert ok
        assert "latejoiner" in s.members

    def test_tc29_metadata_preserved(self):
        p = make_proto()
        s = p.propose("A", "goal", metadata={"priority": "high", "deadline": "2026-06-01"})
        assert s.metadata["priority"] == "high"

    def test_tc30_multiple_complete_fails(self):
        p = make_proto()
        s = p.propose("A", "goal", participants=["B"])
        p.accept(s.session_id, "B"); p.start(s.session_id)
        p.complete(s.session_id)
        ok2 = p.complete(s.session_id)
        assert not ok2

    def test_tc31_send_non_member_fails(self):
        p = make_proto()
        s = p.propose("A", "goal", participants=["B"])
        p.accept(s.session_id, "B"); p.start(s.session_id)
        mid = p.send(s.session_id, "unknown_agent", "hi")
        assert mid is None

    def test_tc32_full_lifecycle(self):
        p = make_proto()
        events = []
        for ev in ("proposed", "accepted", "started", "completed"):
            p.on(ev, lambda s, e=ev: events.append(e))
        s = p.propose("A", "write novel", participants=["B"])
        p.accept(s.session_id, "B")
        p.start(s.session_id)
        p.send(s.session_id, "A", "draft ready")
        p.complete(s.session_id, result="novel complete")
        assert events == ["proposed", "accepted", "started", "completed"]
        assert s.state == CollaborationState.COMPLETED

    def test_tc33_adr_162(self):
        assert ADR_162["id"] == "ADR-162"
        assert ADR_162["status"] == "accepted"
        assert "CollaborationProtocol" in ADR_162["title"]
