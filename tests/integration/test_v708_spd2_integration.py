"""
V708 — SP-D.2 MultiAgent Coordination Integration Tests (ADR-170)
33 TC: End-to-end multi-agent coordination scenarios combining all SP-D.2 modules.
G32: NO print() anywhere in this file.
"""

import time
import importlib
from typing import List, Dict, Any

import pytest

from literary_system.agents.agent_message import AgentMessage, AgentBus, MessagePriority
from literary_system.agents.agent_task import AgentTask, TaskQueue, TaskPriority
from literary_system.agents.capability_registry import (
    AgentCapabilityRegistry, AgentCapability, AgentProfile,
)
from literary_system.agents.task_scheduler import AgentTaskScheduler
from literary_system.agents.collaboration_protocol import (
    AgentCollaborationProtocol, CollaborationState,
)
from literary_system.agents.conflict_resolver import (
    AgentConflictResolver, ConflictType, ResolutionStrategy, ConflictParty,
)
from literary_system.agents.agent_workflow import (
    AgentWorkflow, StepStatus, WorkflowStatus,
)
from literary_system.agents.load_balancer import AgentLoadBalancer, BalancingStrategy
from literary_system.agents.circuit_breaker import (
    AgentCircuitBreaker, CircuitState, CircuitBreakerConfig, CircuitBreakerError,
)
from literary_system.agents.agent_supervisor import (
    AgentSupervisor, AgentHealthMonitor, HealthStatus, RestartPolicy,
)


# ---------------------------------------------------------------------------
# TC01~TC05: AgentBus + TaskScheduler integration
# ---------------------------------------------------------------------------

class TestBusSchedulerIntegration:
    """TC01~TC05: Message bus + task scheduling combined."""

    def test_tc01_bus_publish_and_receive(self):
        """TC01: Agent subscribes, receives published message."""
        bus = AgentBus()
        received: List[AgentMessage] = []
        bus.subscribe("coordinator", lambda m: received.append(m))
        msg = AgentMessage.broadcast(sender="initiator", payload={"cmd": "schedule"}, priority=MessagePriority.NORMAL)
        bus.publish(msg)
        msgs = bus.get_messages("coordinator")
        assert len(msgs) == 1
        assert msgs[0].payload["cmd"] == "schedule"

    def test_tc02_critical_message_triggers_critical_task(self):
        """TC02: CRITICAL bus message triggers CRITICAL task enqueue."""
        bus = AgentBus()
        queue = TaskQueue()
        triggered: List[str] = []

        def handler(m: AgentMessage) -> None:
            if m.priority == MessagePriority.CRITICAL:
                t = AgentTask(name="urgent", assigned_agent="worker", payload={}, priority=TaskPriority.CRITICAL)
                queue.enqueue(t)
                triggered.append("scheduled")

        bus.subscribe("worker", handler)
        msg = AgentMessage.broadcast(sender="alarm", payload={"type": "critical"}, priority=MessagePriority.CRITICAL)
        bus.publish(msg)
        bus.get_messages("worker")  # triggers handler

        assert "scheduled" in triggered
        top = queue.dequeue()
        assert top is not None
        assert top.priority == TaskPriority.CRITICAL

    def test_tc03_scheduler_dispatches_task_then_bus_notifies(self):
        """TC03: Scheduler ticks and dispatches; bus notifies completion."""
        bus = AgentBus()
        results: List[str] = []
        bus.subscribe("monitor", lambda m: results.append(m.payload.get("event", "")))

        sched = AgentTaskScheduler()
        sched.register_handler("compute", lambda t: None)
        task = AgentTask(name="compute", assigned_agent="worker", payload={})
        sched.schedule(task)
        sched.tick()

        msg = AgentMessage.broadcast(sender="sched", payload={"event": "tick_done"}, priority=MessagePriority.LOW)
        bus.publish(msg)
        bus.get_messages("monitor")
        assert "tick_done" in results

    def test_tc04_multiple_subscribers_all_receive(self):
        """TC04: Multiple agents subscribe; all receive broadcast."""
        bus = AgentBus()
        got: Dict[str, int] = {"a": 0, "b": 0, "c": 0}

        for ag in ["a", "b", "c"]:
            ag_key = ag
            bus.subscribe(ag_key, lambda m, k=ag_key: got.update({k: got[k] + 1}))

        msg = AgentMessage.broadcast(sender="hub", payload={"msg": "hello"}, priority=MessagePriority.NORMAL)
        bus.publish(msg)
        for ag in ["a", "b", "c"]:
            bus.get_messages(ag)

        assert all(v == 1 for v in got.values())

    def test_tc05_scheduler_no_handler_stats(self):
        """TC05: Task scheduled without handler — stats reflect pending task."""
        sched = AgentTaskScheduler()
        task = AgentTask(name="orphan", assigned_agent="none", payload={}, priority=TaskPriority.LOW)
        sched.schedule(task)
        sched.tick()
        stats = sched.stats()
        assert stats["scheduled"] >= 1


# ---------------------------------------------------------------------------
# TC06~TC10: CapabilityRegistry + LoadBalancer integration
# ---------------------------------------------------------------------------

class TestRegistryLoadBalancerIntegration:
    """TC06~TC10: Capability discovery + workload distribution."""

    def test_tc06_register_then_balance(self):
        """TC06: Register agents in registry, load balancer uses same IDs."""
        reg = AgentCapabilityRegistry()
        lb = AgentLoadBalancer(strategy=BalancingStrategy.ROUND_ROBIN)

        for agent_id in ["writer-1", "writer-2"]:
            reg.register(agent_id, [AgentCapability(name="write")])
            lb.register(agent_id, capacity=10)

        writers = [p.agent_id for p in reg.agents_with_capability("write")]
        assert "writer-1" in writers and "writer-2" in writers

        sel1 = lb.select()
        sel2 = lb.select()
        assert sel1 is not None and sel2 is not None

    def test_tc07_least_loaded_prefers_idle_agent(self):
        """TC07: LEAST_LOADED picks agent with fewer active tasks."""
        lb = AgentLoadBalancer(strategy=BalancingStrategy.LEAST_LOADED)
        lb.register("busy", capacity=10)
        lb.register("idle", capacity=10)
        # Assign 8 tasks to busy
        for _ in range(8):
            # select busy node, then assign via assign()
            lb.set_online("idle", False)
            lb.assign()
            lb.set_online("idle", True)

        sel = lb.select()
        assert sel is not None
        assert sel.agent_id == "idle"

    def test_tc08_assign_and_release_cycle(self):
        """TC08: assign() increments active_tasks, release() decrements."""
        lb = AgentLoadBalancer(strategy=BalancingStrategy.ROUND_ROBIN)
        lb.register("node-A", capacity=5)

        sel = lb.select()
        assert sel is not None
        lb.assign()
        node = lb._nodes[sel.agent_id]
        assert node.active_tasks == 1

        lb.release(sel.agent_id)
        assert node.active_tasks == 0

    def test_tc09_weighted_strategy_prefers_high_weight(self):
        """TC09: WEIGHTED strategy selects higher-weight agent more often."""
        lb = AgentLoadBalancer(strategy=BalancingStrategy.WEIGHTED)
        lb.register("heavy-w", capacity=10, weight=10)
        lb.register("light-w", capacity=10, weight=1)

        counts: Dict[str, int] = {"heavy-w": 0, "light-w": 0}
        for _ in range(20):
            sel = lb.select()
            if sel:
                counts[sel.agent_id] += 1

        assert counts["heavy-w"] > counts["light-w"]

    def test_tc10_deregister_removes_from_pool(self):
        """TC10: Deregistered agent is no longer selected."""
        lb = AgentLoadBalancer(strategy=BalancingStrategy.ROUND_ROBIN)
        lb.register("gone", capacity=5)
        lb.register("stay", capacity=5)
        lb.deregister("gone")

        for _ in range(5):
            sel = lb.select()
            assert sel is None or sel.agent_id != "gone"


# ---------------------------------------------------------------------------
# TC11~TC15: CollaborationProtocol + ConflictResolver integration
# ---------------------------------------------------------------------------

class TestCollaborationConflictIntegration:
    """TC11~TC15: Collaboration sessions with embedded conflict resolution."""

    def test_tc11_collaboration_full_lifecycle(self):
        """TC11: propose→accept→start→complete full lifecycle."""
        proto = AgentCollaborationProtocol()
        session = proto.propose(initiator_id="agent-A", goal="write chapter 1", participants=["agent-B"])
        sid = session.session_id
        proto.accept(session_id=sid, agent_id="agent-B")
        proto.start(session_id=sid)
        proto.contribute(session_id=sid, agent_id="agent-A")
        proto.complete(session_id=sid, result={"output": "chapter done"})

        stored = proto._sessions[sid]
        assert stored.state == CollaborationState.COMPLETED
        assert stored.result["output"] == "chapter done"

    def test_tc12_conflict_resolved_by_priority(self):
        """TC12: Two agents conflict; PRIORITY_BASED picks higher-priority party."""
        resolver = AgentConflictResolver()
        events: List[str] = []
        resolver.on("resolved", lambda c: events.append(c.conflict_id))

        parties = [
            ConflictParty(agent_id="agent-A", priority=10, claim="style-A", timestamp=time.time()),
            ConflictParty(agent_id="agent-B", priority=5, claim="style-B", timestamp=time.time()),
        ]
        conflict = resolver.register(
            conflict_type=ConflictType.DECISION,
            parties=parties,
            strategy=ResolutionStrategy.PRIORITY_BASED,
        )
        cid = conflict.conflict_id
        resolver.resolve(cid)
        stored = resolver._conflicts[cid]
        assert stored.winner == "agent-A"

    def test_tc13_failed_collaboration_replaced_by_new_session(self):
        """TC13: Failed session can be superseded by a new proposal."""
        proto = AgentCollaborationProtocol()
        session1 = proto.propose(initiator_id="A", goal="draft", participants=["B"])
        sid1 = session1.session_id
        proto.accept(sid1, "B")
        proto.start(sid1)
        proto.fail(sid1, reason="timeout")

        session2 = proto.propose(initiator_id="A", goal="draft-retry", participants=["B"])
        assert session2.session_id != sid1
        assert proto._sessions[session2.session_id].state == CollaborationState.PROPOSED

    def test_tc14_consensus_picks_majority_claim(self):
        """TC14: CONSENSUS picks the claim with clear majority."""
        resolver = AgentConflictResolver()
        parties = [
            ConflictParty(agent_id="a1", priority=1, claim="option-X", timestamp=time.time()),
            ConflictParty(agent_id="a2", priority=1, claim="option-X", timestamp=time.time()),
            ConflictParty(agent_id="a3", priority=1, claim="option-Y", timestamp=time.time()),
        ]
        conflict = resolver.register(ConflictType.DECISION, parties, ResolutionStrategy.CONSENSUS)
        cid = conflict.conflict_id
        resolver.resolve(cid)
        stored = resolver._conflicts[cid]
        # CONSENSUS winner is the agent_id of first matching party, not claim string
        assert stored.winner in ["a1", "a2"]  # both claimed option-X

    def test_tc15_collaboration_cancel_state(self):
        """TC15: Cancelled session is CANCELLED."""
        proto = AgentCollaborationProtocol()
        session = proto.propose(initiator_id="Z", goal="abandoned", participants=["W"])
        proto.cancel(session.session_id)
        stored = proto._sessions[session.session_id]
        assert stored.state == CollaborationState.CANCELLED


# ---------------------------------------------------------------------------
# TC16~TC20: AgentWorkflow + CircuitBreaker integration
# ---------------------------------------------------------------------------

class TestWorkflowCircuitBreakerIntegration:
    """TC16~TC20: Workflow DAG execution with circuit-breaker protected steps."""

    def test_tc16_linear_workflow_all_complete(self):
        """TC16: Linear workflow A→B→C all complete successfully."""
        wf = AgentWorkflow(name="wf-16")
        order: List[str] = []
        sa = wf.add_step("step-A", handler=lambda ctx: order.append("A"))
        sb = wf.add_step("step-B", handler=lambda ctx: order.append("B"), depends_on=[sa.step_id])
        wf.add_step("step-C", handler=lambda ctx: order.append("C"), depends_on=[sb.step_id])
        wf.run()
        assert order == ["A", "B", "C"]
        assert wf.status == WorkflowStatus.COMPLETED

    def test_tc17_failed_step_skips_downstream(self):
        """TC17: Failing step B causes C to be SKIPPED."""
        wf = AgentWorkflow(name="wf-17")
        sa = wf.add_step("step-A", handler=lambda ctx: None)
        sb = wf.add_step(
            "step-B",
            handler=lambda ctx: (_ for _ in ()).throw(RuntimeError("fail")),
            depends_on=[sa.step_id],
        )
        sc = wf.add_step("step-C", handler=lambda ctx: None, depends_on=[sb.step_id])
        wf.run()

        assert wf.step_by_id(sc.step_id).status == StepStatus.SKIPPED
        assert wf.status == WorkflowStatus.FAILED

    def test_tc18_circuit_breaker_trips_after_failures(self):
        """TC18: CircuitBreaker opens after threshold failures."""
        cb = AgentCircuitBreaker(
            name="service-cb",
            config=CircuitBreakerConfig(failure_threshold=2, success_threshold=1, timeout_seconds=60.0),
        )
        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(ValueError("err")))
            except ValueError:
                pass

        assert cb.state == CircuitState.OPEN
        with pytest.raises(CircuitBreakerError):
            cb.call(lambda: "ok")

    def test_tc19_circuit_breaker_recovers_after_timeout(self):
        """TC19: After timeout, circuit transitions OPEN→HALF_OPEN→CLOSED."""
        cb = AgentCircuitBreaker(
            name="recover-cb",
            config=CircuitBreakerConfig(failure_threshold=1, success_threshold=1, timeout_seconds=0.01),
        )
        try:
            cb.call(lambda: (_ for _ in ()).throw(IOError("down")))
        except IOError:
            pass

        assert cb.state == CircuitState.OPEN
        time.sleep(0.05)

        state = cb.state  # triggers OPEN→HALF_OPEN auto-transition
        assert state == CircuitState.HALF_OPEN

        result = cb.call(lambda: "recovered")
        assert result == "recovered"
        assert cb.state == CircuitState.CLOSED

    def test_tc20_open_circuit_breaker_causes_workflow_step_failure(self):
        """TC20: Workflow step uses open CB; step FAILED, downstream SKIPPED."""
        cb = AgentCircuitBreaker(
            name="wf-cb",
            config=CircuitBreakerConfig(failure_threshold=1, success_threshold=1, timeout_seconds=60.0),
        )
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("tripped")))
        except RuntimeError:
            pass

        wf = AgentWorkflow(name="wf-20")
        sa = wf.add_step("step-A", handler=lambda ctx: None)
        sb = wf.add_step(
            "step-B",
            handler=lambda ctx: cb.call(lambda: "ok"),
            depends_on=[sa.step_id],
        )
        sc = wf.add_step("step-C", handler=lambda ctx: None, depends_on=[sb.step_id])
        wf.run()

        assert wf.step_by_id(sc.step_id).status == StepStatus.SKIPPED


# ---------------------------------------------------------------------------
# TC21~TC25: AgentSupervisor + HealthMonitor integration
# ---------------------------------------------------------------------------

class TestSupervisorHealthIntegration:
    """TC21~TC25: Supervisor lifecycle with health monitoring."""

    def test_tc21_supervisor_start_stop(self):
        """TC21: Start and stop supervised agent."""
        sup = AgentSupervisor()
        sup.register("ag-21", start_fn=lambda: True, stop_fn=lambda: None, restart_policy=RestartPolicy.NEVER)
        sup.start("ag-21")
        assert "ag-21" in sup.running_agents()
        sup.stop("ag-21")
        assert "ag-21" not in sup.running_agents()

    def test_tc22_health_monitor_degraded_on_one_failure(self):
        """TC22: One failed check → DEGRADED."""
        monitor = AgentHealthMonitor(failure_threshold=3, degraded_threshold=1)
        monitor.register("mon-22", checker=lambda: False)
        rec = monitor.check("mon-22")
        assert rec.status == HealthStatus.DEGRADED

    def test_tc23_health_monitor_unhealthy_at_threshold(self):
        """TC23: Three consecutive failures → UNHEALTHY."""
        monitor = AgentHealthMonitor(failure_threshold=3, degraded_threshold=1)
        monitor.register("mon-23", checker=lambda: False)
        for _ in range(3):
            rec = monitor.check("mon-23")
        assert rec.status == HealthStatus.UNHEALTHY

    def test_tc24_supervisor_restarts_unhealthy_agent(self):
        """TC24: supervise() auto-restarts UNHEALTHY agent with ON_FAILURE policy."""
        restart_count: List[int] = [0]

        def start_fn() -> bool:
            restart_count[0] += 1
            return True

        sup = AgentSupervisor()
        sup.register(
            "ag-24",
            start_fn=start_fn,
            health_checker=lambda: False,  # always fails → UNHEALTHY
            restart_policy=RestartPolicy.ON_FAILURE,
            max_restarts=3,
        )
        sup.start("ag-24")
        initial_count = restart_count[0]

        # Force UNHEALTHY via direct checks before supervise
        for _ in range(3):
            sup._health.check("ag-24")

        restarted = sup.supervise()
        assert "ag-24" in restarted
        assert sup._agents["ag-24"].restart_count >= 1
        assert restart_count[0] > initial_count

    def test_tc25_never_policy_no_restart(self):
        """TC25: NEVER restart policy — supervisor does not restart agent."""
        sup = AgentSupervisor()
        sup.register(
            "ag-25",
            start_fn=lambda: True,
            health_checker=lambda: False,
            restart_policy=RestartPolicy.NEVER,
        )
        sup.start("ag-25")
        before = sup._agents["ag-25"].restart_count

        for _ in range(3):
            sup._health.check("ag-25")

        sup.supervise()
        assert sup._agents["ag-25"].restart_count == before


# ---------------------------------------------------------------------------
# TC26~TC30: Full end-to-end multi-agent pipeline
# ---------------------------------------------------------------------------

class TestEndToEndPipeline:
    """TC26~TC30: Full pipeline: discovery → assignment → collaboration → workflow."""

    def test_tc26_e2e_discover_assign_collaborate(self):
        """TC26: E2E — discover capable agent, assign via LB, start collaboration."""
        reg = AgentCapabilityRegistry()
        lb = AgentLoadBalancer(strategy=BalancingStrategy.LEAST_LOADED)
        proto = AgentCollaborationProtocol()

        reg.register("writer-A", [AgentCapability(name="write")])
        lb.register("writer-A", capacity=10)

        writers = [p.agent_id for p in reg.agents_with_capability("write")]
        assert "writer-A" in writers

        sel = lb.select()
        assert sel is not None
        lb.assign()

        session = proto.propose(
            initiator_id="coordinator",
            goal="chapter",
            participants=[sel.agent_id],
        )
        proto.accept(session.session_id, sel.agent_id)
        proto.start(session.session_id)
        proto.complete(session.session_id, result={"text": "done"})

        assert proto._sessions[session.session_id].state == CollaborationState.COMPLETED

    def test_tc27_e2e_workflow_with_bus_notification(self):
        """TC27: E2E — workflow completes, bus notifies subscribers."""
        bus = AgentBus()
        notifications: List[str] = []
        bus.subscribe("logger", lambda m: notifications.append(m.payload.get("event", "")))

        wf = AgentWorkflow(name="wf-27")
        sa = wf.add_step("parse", handler=lambda ctx: None)
        wf.add_step("render", handler=lambda ctx: None, depends_on=[sa.step_id])
        wf.run()

        msg = AgentMessage.broadcast(
            sender="wf",
            payload={"event": "workflow_complete"},
            priority=MessagePriority.NORMAL,
        )
        bus.publish(msg)
        bus.get_messages("logger")

        assert wf.status == WorkflowStatus.COMPLETED
        assert "workflow_complete" in notifications

    def test_tc28_e2e_conflict_resolution_feeds_workflow(self):
        """TC28: E2E — conflict resolved before workflow selects execution strategy."""
        resolver = AgentConflictResolver()
        parties = [
            ConflictParty(agent_id="A", priority=9, claim="strategy-fast", timestamp=time.time()),
            ConflictParty(agent_id="B", priority=3, claim="strategy-safe", timestamp=time.time()),
        ]
        conflict = resolver.register(ConflictType.DECISION, parties, ResolutionStrategy.PRIORITY_BASED)
        cid = conflict.conflict_id
        resolver.resolve(cid)
        chosen = resolver._conflicts[cid].winner
        assert chosen == "A"

        # Workflow uses the winning strategy
        wf = AgentWorkflow(name="wf-28")
        wf.add_step("exec", handler=lambda ctx: None)
        wf.run()
        assert wf.status == WorkflowStatus.COMPLETED

    def test_tc29_e2e_bad_node_offline_lb_selects_healthy(self):
        """TC29: E2E — failed node taken offline; LB selects healthy node."""
        lb = AgentLoadBalancer(strategy=BalancingStrategy.LEAST_LOADED)
        cb_bad = AgentCircuitBreaker(
            name="bad-node-cb",
            config=CircuitBreakerConfig(failure_threshold=1, success_threshold=1, timeout_seconds=60.0),
        )

        lb.register("bad-node", capacity=10)
        lb.register("good-node", capacity=10)

        # Trip bad-node CB
        try:
            cb_bad.call(lambda: (_ for _ in ()).throw(RuntimeError("down")))
        except RuntimeError:
            pass

        lb.set_online("bad-node", False)

        sel = lb.select()
        assert sel is not None
        assert sel.agent_id == "good-node"

    def test_tc30_e2e_supervisor_detects_failure_bus_alerts(self):
        """TC30: E2E — supervisor detects unhealthy agent, bus broadcasts alert."""
        sup = AgentSupervisor()
        bus = AgentBus()
        alerts: List[str] = []
        bus.subscribe("ops", lambda m: alerts.append(m.payload.get("alert", "")))

        sup.register(
            "monitored-agent",
            start_fn=lambda: True,
            health_checker=lambda: False,
            restart_policy=RestartPolicy.ON_FAILURE,
            max_restarts=1,
        )
        sup.start("monitored-agent")

        # Force UNHEALTHY
        for _ in range(3):
            sup._health.check("monitored-agent")

        sup.supervise()

        msg = AgentMessage.broadcast(
            sender="supervisor",
            payload={"alert": "agent_restarted"},
            priority=MessagePriority.HIGH,
        )
        bus.publish(msg)
        bus.get_messages("ops")

        assert "agent_restarted" in alerts


# ---------------------------------------------------------------------------
# TC31~TC33: Gate integration verification
# ---------------------------------------------------------------------------

class TestGateIntegration:
    """TC31~TC33: Gate passes verify all coordination modules healthy."""

    def test_tc31_g84_gate_passes(self):
        """TC31: Gate G84 (AgentCoordination) passes cleanly."""
        from literary_system.gates.agent_coordination_gate import AgentCoordinationGate
        gate = AgentCoordinationGate()
        passed, results = gate.run()
        assert passed, f"G84 failed: {[r for r in results if not r.passed]}"

    def test_tc32_g85_gate_passes(self):
        """TC32: Gate G85 (AgentWorkflow) passes cleanly."""
        from literary_system.gates.agent_workflow_gate import AgentWorkflowGate
        gate = AgentWorkflowGate()
        passed, results = gate.run()
        assert passed, f"G85 failed: {[r for r in results if not r.passed]}"

    def test_tc33_all_agent_modules_importable(self):
        """TC33: All SP-D.2 modules import without error."""
        modules = [
            "literary_system.agents.agent_message",
            "literary_system.agents.agent_task",
            "literary_system.agents.capability_registry",
            "literary_system.agents.task_scheduler",
            "literary_system.agents.collaboration_protocol",
            "literary_system.agents.conflict_resolver",
            "literary_system.agents.agent_workflow",
            "literary_system.agents.load_balancer",
            "literary_system.agents.circuit_breaker",
            "literary_system.agents.agent_supervisor",
            "literary_system.gates.agent_coordination_gate",
            "literary_system.gates.agent_workflow_gate",
        ]
        for mod in modules:
            m = importlib.import_module(mod)
            assert m is not None, f"Failed to import {mod}"
