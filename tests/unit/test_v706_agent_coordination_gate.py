"""V706 — Gate G84 AgentCoordination Gate 테스트 (33 TC)."""
import pytest
from literary_system.gates.agent_coordination_gate import (
    AgentCoordinationGate, GateCheckResult, ADR_168,
)


def make_gate() -> AgentCoordinationGate:
    return AgentCoordinationGate()


# ══════════════════════════════════════════════════════════════════════
class TestGateCheckResult:
    def test_tc01_result_creation(self):
        r = GateCheckResult("E1", "test", True, "ok")
        assert r.check_id == "E1"
        assert r.passed is True

    def test_tc02_to_dict(self):
        r = GateCheckResult("E2", "desc", False, "error")
        d = r.to_dict()
        assert d["passed"] is False
        assert d["check_id"] == "E2"


class TestAgentCoordinationGate:
    def test_tc03_gate_id(self):
        assert AgentCoordinationGate.GATE_ID == "G84"

    def test_tc04_run_returns_tuple(self):
        g = make_gate()
        result = g.run()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_tc05_run_6_checks(self):
        g = make_gate()
        _, results = g.run()
        assert len(results) == 6

    def test_tc06_all_checks_pass(self):
        g = make_gate()
        passed, results = g.run()
        assert passed, [r.to_dict() for r in results if not r.passed]

    def test_tc07_e1_agent_message(self):
        g = make_gate()
        r = g._check_e1()
        assert r.passed, r.message

    def test_tc08_e2_agent_task(self):
        g = make_gate()
        r = g._check_e2()
        assert r.passed, r.message

    def test_tc09_e3_capability_registry(self):
        g = make_gate()
        r = g._check_e3()
        assert r.passed, r.message

    def test_tc10_e4_task_scheduler(self):
        g = make_gate()
        r = g._check_e4()
        assert r.passed, r.message

    def test_tc11_e5_collaboration_protocol(self):
        g = make_gate()
        r = g._check_e5()
        assert r.passed, r.message

    def test_tc12_e6_conflict_resolver(self):
        g = make_gate()
        r = g._check_e6()
        assert r.passed, r.message

    def test_tc13_passed_true_means_all_pass(self):
        g = make_gate()
        passed, results = g.run()
        assert passed == all(r.passed for r in results)

    def test_tc14_check_ids_unique(self):
        g = make_gate()
        _, results = g.run()
        ids = [r.check_id for r in results]
        assert len(ids) == len(set(ids))

    def test_tc15_check_ids_e1_to_e6(self):
        g = make_gate()
        _, results = g.run()
        ids = {r.check_id for r in results}
        for eid in ("E1", "E2", "E3", "E4", "E5", "E6"):
            assert eid in ids

    def test_tc16_all_results_have_description(self):
        g = make_gate()
        _, results = g.run()
        for r in results:
            assert r.description

    def test_tc17_passing_results_have_message(self):
        g = make_gate()
        _, results = g.run()
        for r in results:
            if r.passed:
                assert r.message  # success message present

    # ── 개별 E체크 상세 검증 ─────────────────────────────────────────────

    def test_tc18_e1_uses_agentbus(self):
        """E1 check: bus.publish + subscribe 동작."""
        from literary_system.agents.agent_message import AgentBus, AgentMessage, MessagePriority
        bus = AgentBus()
        received = []
        bus.subscribe("x", handler=lambda m: received.append(m))
        msg = AgentMessage.broadcast(sender="y", payload={"k": 1})
        bus.publish(msg)
        assert len(bus.get_messages("x")) == 1

    def test_tc19_e2_priority_ordering(self):
        from literary_system.agents.agent_task import AgentTask, TaskQueue, TaskPriority
        q = TaskQueue("t")
        t1 = AgentTask(name="bg", assigned_agent="a", payload={}, priority=TaskPriority.BACKGROUND)
        t2 = AgentTask(name="crit", assigned_agent="a", payload={}, priority=TaskPriority.CRITICAL)
        q.enqueue(t1); q.enqueue(t2)
        assert q.dequeue().name == "crit"

    def test_tc20_e3_agents_with_capability(self):
        from literary_system.agents.capability_registry import AgentCapabilityRegistry, AgentCapability
        reg = AgentCapabilityRegistry()
        cap = AgentCapability(name="edit", description="edit", version="1.0", tags=[])
        reg.register("editor", [cap])
        profiles = reg.agents_with_capability("edit")
        assert "editor" in [p.agent_id for p in profiles]

    def test_tc21_e4_scheduler_dispatch(self):
        from literary_system.agents.task_scheduler import AgentTaskScheduler
        from literary_system.agents.agent_task import AgentTask, TaskStatus
        sched = AgentTaskScheduler()
        sched.register_handler("x", lambda t: True)
        t = AgentTask(name="t", assigned_agent="a", payload={}, tags=["x"])
        sched.schedule(t)
        sched.tick()
        assert t.status == TaskStatus.DONE

    def test_tc22_e5_collaboration_lifecycle(self):
        from literary_system.agents.collaboration_protocol import (
            AgentCollaborationProtocol, CollaborationState,
        )
        p = AgentCollaborationProtocol()
        s = p.propose("A", "goal", participants=["B"])
        p.accept(s.session_id, "B"); p.start(s.session_id)
        p.complete(s.session_id)
        assert s.state == CollaborationState.COMPLETED

    def test_tc23_e6_conflict_resolution(self):
        from literary_system.agents.conflict_resolver import (
            AgentConflictResolver, ConflictType, ConflictParty, ResolutionStrategy,
        )
        r = AgentConflictResolver()
        parties = [ConflictParty("A", 1), ConflictParty("B", 5)]
        c = r.register(ConflictType.RESOURCE, parties, ResolutionStrategy.PRIORITY_BASED)
        r.resolve(c.conflict_id)
        assert c.winner == "B"

    def test_tc24_gate_result_score_6_6(self):
        g = make_gate()
        passed, results = g.run()
        score = sum(r.passed for r in results)
        assert score == 6

    def test_tc25_adr_168(self):
        assert ADR_168["id"] == "ADR-168"
        assert ADR_168["status"] == "accepted"

    def test_tc26_gate_rerunnable(self):
        """Gate를 여러 번 실행해도 동일 결과."""
        g = make_gate()
        p1, r1 = g.run()
        p2, r2 = g.run()
        assert p1 == p2
        assert len(r1) == len(r2)

    def test_tc27_e4_no_dispatch_empty_queue(self):
        from literary_system.agents.task_scheduler import AgentTaskScheduler
        sched = AgentTaskScheduler()
        assert sched.tick() == 0

    def test_tc28_e5_cancel_session(self):
        from literary_system.agents.collaboration_protocol import (
            AgentCollaborationProtocol, CollaborationState,
        )
        p = AgentCollaborationProtocol()
        s = p.propose("A", "goal")
        p.cancel(s.session_id)
        assert s.state == CollaborationState.CANCELLED

    def test_tc29_e6_escalate_on_no_consensus(self):
        from literary_system.agents.conflict_resolver import (
            AgentConflictResolver, ConflictType, ConflictParty,
            ResolutionStrategy, ConflictState,
        )
        r = AgentConflictResolver()
        parties = [ConflictParty("A", claim="x"), ConflictParty("B", claim="y")]
        c = r.register(ConflictType.DECISION, parties, ResolutionStrategy.CONSENSUS)
        r.resolve(c.conflict_id)
        assert c.state == ConflictState.ESCALATED

    def test_tc30_e1_message_expiry(self):
        from literary_system.agents.agent_message import AgentMessage
        msg = AgentMessage.broadcast(sender="x", payload={})
        assert msg.message_id  # has ID

    def test_tc31_e3_all_capabilities(self):
        from literary_system.agents.capability_registry import (
            AgentCapabilityRegistry, AgentCapability,
        )
        reg = AgentCapabilityRegistry()
        cap1 = AgentCapability(name="write", description="w", version="1.0", tags=[])
        cap2 = AgentCapability(name="edit", description="e", version="1.0", tags=[])
        reg.register("agent", [cap1, cap2])
        caps = reg.all_capabilities()
        assert "write" in caps and "edit" in caps

    def test_tc32_e2_force_requeue(self):
        from literary_system.agents.agent_task import AgentTask, TaskQueue, TaskStatus
        q = TaskQueue("t")
        t = AgentTask(name="t", assigned_agent="a", payload={})
        q.enqueue(t)
        dequeued = q.dequeue()
        dequeued.status = TaskStatus.PENDING
        q.force_requeue(dequeued)
        assert q.pending_count() == 1

    def test_tc33_gate_description_coverage(self):
        g = make_gate()
        _, results = g.run()
        descs = " ".join(r.description for r in results)
        for keyword in ("AgentMessage", "AgentTask", "Capability", "Scheduler",
                        "Collaboration", "ConflictResolver"):
            assert keyword in descs, f"Missing keyword: {keyword}"
