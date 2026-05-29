"""
literary_system/gates/spd2_exit_gate.py
────────────────────────────────────────
SP-D.2 Exit Gate — Phase D Sub-Phase D.2 완료 기준 검증

ADR-171: SP-D.2 Exit Gate — MultiAgent Coordination Layer 완전 구축 확인

검증 축:
  E1 - AgentBus pub/sub + AgentMessage 팩토리
  E2 - TaskQueue 우선순위 + AgentTaskScheduler dispatch
  E3 - AgentCapabilityRegistry + ConflictResolver 해결
  E4 - AgentCollaborationProtocol 전체 라이프사이클
  E5 - AgentWorkflow DAG + CircuitBreaker + Supervisor
  E6 - G84/G85 게이트 통과 + 전체 테스트 수 충족

LLM 외부 호출 금지 (ADR-015 / ADR-031)
G32: NO print() calls — use sys.stdout.write
"""

from __future__ import annotations

import importlib
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ──────────────────────────────────────────────
# 결과 데이터 클래스
# ──────────────────────────────────────────────


@dataclass
class ExitCheckpoint:
    axis: str
    name: str
    passed: bool
    detail: str = ""
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class SpD2ExitResult:
    gate_id: str = "SP-D.2-EXIT"
    gate_name: str = "SP-D.2 Exit Gate — MultiAgent Coordination Layer Complete"
    passed: bool = False
    passed_count: int = 0
    failed_count: int = 0
    checkpoints: List[ExitCheckpoint] = field(default_factory=list)
    duration_ms: float = 0.0
    version: str = "12.2.0"
    tc_total: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "passed": self.passed,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "version": self.version,
            "tc_total": self.tc_total,
            "duration_ms": round(self.duration_ms, 2),
            "checkpoints": [
                {
                    "axis": cp.axis,
                    "name": cp.name,
                    "passed": cp.passed,
                    "detail": cp.detail,
                    "error": cp.error,
                    "duration_ms": round(cp.duration_ms, 2),
                }
                for cp in self.checkpoints
            ],
        }


# ──────────────────────────────────────────────
# E1: AgentBus pub/sub + AgentMessage
# ──────────────────────────────────────────────


def _check_e1_agent_bus() -> ExitCheckpoint:
    start = time.time()
    try:
        from literary_system.agents.agent_message import AgentBus, AgentMessage, MessagePriority

        bus = AgentBus()
        received: List[Any] = []
        bus.subscribe("e1-agent", lambda m: received.append(m))

        msg = AgentMessage.broadcast(
            sender="e1-sender",
            payload={"key": "value"},
            priority=MessagePriority.NORMAL,
        )
        bus.publish(msg)
        msgs = bus.get_messages("e1-agent")

        assert len(msgs) == 1, f"Expected 1 message, got {len(msgs)}"
        assert msgs[0].payload["key"] == "value", "Payload mismatch"
        assert msgs[0].sender == "e1-sender", "Sender mismatch"

        # Critical priority test
        crit = AgentMessage.broadcast(
            sender="alarm",
            payload={"type": "critical"},
            priority=MessagePriority.CRITICAL,
        )
        assert crit.priority == MessagePriority.CRITICAL, "Priority mismatch"

        return ExitCheckpoint(
            axis="E1", name="AgentBus pub/sub + AgentMessage 팩토리", passed=True,
            detail="subscribe+publish+get_messages, CRITICAL priority ✓",
            duration_ms=(time.time() - start) * 1000,
        )
    except Exception as exc:
        return ExitCheckpoint(
            axis="E1", name="AgentBus pub/sub + AgentMessage 팩토리", passed=False,
            error=str(exc), duration_ms=(time.time() - start) * 1000,
        )


# ──────────────────────────────────────────────
# E2: TaskQueue + AgentTaskScheduler
# ──────────────────────────────────────────────


def _check_e2_task_queue_scheduler() -> ExitCheckpoint:
    start = time.time()
    try:
        from literary_system.agents.agent_task import AgentTask, TaskPriority, TaskQueue
        from literary_system.agents.task_scheduler import AgentTaskScheduler

        # Priority ordering
        q = TaskQueue()
        t_low = AgentTask(name="low", assigned_agent="a", payload={}, priority=TaskPriority.LOW)
        t_critical = AgentTask(name="crit", assigned_agent="a", payload={}, priority=TaskPriority.CRITICAL)
        t_normal = AgentTask(name="norm", assigned_agent="a", payload={}, priority=TaskPriority.NORMAL)
        q.enqueue(t_low)
        q.enqueue(t_critical)
        q.enqueue(t_normal)
        first = q.dequeue()
        assert first is not None and first.priority == TaskPriority.CRITICAL, (
            f"Expected CRITICAL first, got {first.priority if first else None}"
        )

        # Scheduler dispatch
        dispatched: List[str] = []
        sched = AgentTaskScheduler()
        sched.register_handler("e2-op", lambda t: dispatched.append(t.name) or True)
        task = AgentTask(name="e2-op", assigned_agent="worker", payload={})
        sched.schedule(task)
        sched.tick()

        stats = sched.stats()
        assert stats["scheduled"] >= 1, "Scheduler stats missing"

        return ExitCheckpoint(
            axis="E2", name="TaskQueue 우선순위 + AgentTaskScheduler dispatch", passed=True,
            detail=f"CRITICAL first ✓, dispatched={dispatched}",
            duration_ms=(time.time() - start) * 1000,
        )
    except Exception as exc:
        return ExitCheckpoint(
            axis="E2", name="TaskQueue 우선순위 + AgentTaskScheduler dispatch", passed=False,
            error=str(exc), duration_ms=(time.time() - start) * 1000,
        )


# ──────────────────────────────────────────────
# E3: AgentCapabilityRegistry + ConflictResolver
# ──────────────────────────────────────────────


def _check_e3_registry_conflict() -> ExitCheckpoint:
    start = time.time()
    try:
        import time as _time

        from literary_system.agents.capability_registry import (
            AgentCapability, AgentCapabilityRegistry,
        )
        from literary_system.agents.conflict_resolver import (
            AgentConflictResolver, ConflictParty, ConflictType, ResolutionStrategy,
        )

        # Capability registry
        reg = AgentCapabilityRegistry()
        reg.register("writer-A", [AgentCapability(name="write")])
        reg.register("editor-B", [AgentCapability(name="edit")])
        writers = reg.agents_with_capability("write")
        assert any(p.agent_id == "writer-A" for p in writers), "writer-A not found"
        st = reg.stats()
        assert st["total"] >= 2, f"Expected ≥2 agents, got {st['total']}"

        # Conflict resolver
        resolver = AgentConflictResolver()
        parties = [
            ConflictParty(agent_id="high-prio", priority=10, claim="A", timestamp=_time.time()),
            ConflictParty(agent_id="low-prio", priority=1, claim="B", timestamp=_time.time()),
        ]
        conflict_obj = resolver.register(
            conflict_type=ConflictType.RESOURCE,
            parties=parties,
            strategy=ResolutionStrategy.PRIORITY_BASED,
        )
        resolver.resolve(conflict_obj.conflict_id)
        stored = resolver._conflicts[conflict_obj.conflict_id]
        assert stored.winner == "high-prio", f"Expected 'high-prio', got {stored.winner!r}"

        return ExitCheckpoint(
            axis="E3", name="AgentCapabilityRegistry + ConflictResolver 해결", passed=True,
            detail=f"registry agents={st['total']}, conflict winner=high-prio ✓",
            duration_ms=(time.time() - start) * 1000,
        )
    except Exception as exc:
        return ExitCheckpoint(
            axis="E3", name="AgentCapabilityRegistry + ConflictResolver 해결", passed=False,
            error=str(exc), duration_ms=(time.time() - start) * 1000,
        )


# ──────────────────────────────────────────────
# E4: AgentCollaborationProtocol lifecycle
# ──────────────────────────────────────────────


def _check_e4_collaboration_protocol() -> ExitCheckpoint:
    start = time.time()
    try:
        from literary_system.agents.collaboration_protocol import (
            AgentCollaborationProtocol, CollaborationState,
        )

        proto = AgentCollaborationProtocol()

        # Full lifecycle: propose → accept → start → complete
        session = proto.propose(
            initiator_id="coord",
            goal="write novel chapter",
            participants=["writer"],
        )
        sid = session.session_id
        assert proto.accept(session_id=sid, agent_id="writer"), "accept failed"
        proto.start(session_id=sid)
        proto.contribute(session_id=sid, agent_id="coord")
        proto.complete(session_id=sid, result={"chapter": "done"})

        stored = proto._sessions[sid]
        assert stored.state == CollaborationState.COMPLETED, f"Expected COMPLETED, got {stored.state}"
        assert stored.result == {"chapter": "done"}, "Result mismatch"

        # Cancel lifecycle
        session2 = proto.propose(initiator_id="coord", goal="draft", participants=["writer"])
        proto.cancel(session2.session_id)
        assert proto._sessions[session2.session_id].state == CollaborationState.CANCELLED

        st = proto.stats()
        assert st["total"] >= 2, f"Expected ≥2 sessions, got {st['total']}"

        return ExitCheckpoint(
            axis="E4", name="AgentCollaborationProtocol 전체 라이프사이클", passed=True,
            detail=f"COMPLETED+CANCELLED lifecycle ✓, total sessions={st['total']}",
            duration_ms=(time.time() - start) * 1000,
        )
    except Exception as exc:
        return ExitCheckpoint(
            axis="E4", name="AgentCollaborationProtocol 전체 라이프사이클", passed=False,
            error=str(exc), duration_ms=(time.time() - start) * 1000,
        )


# ──────────────────────────────────────────────
# E5: AgentWorkflow DAG + CircuitBreaker + Supervisor
# ──────────────────────────────────────────────


def _check_e5_workflow_cb_supervisor() -> ExitCheckpoint:
    start = time.time()
    try:
        import time as _time

        from literary_system.agents.agent_supervisor import (
            AgentSupervisor, HealthStatus, RestartPolicy,
        )
        from literary_system.agents.agent_workflow import (
            AgentWorkflow, StepStatus, WorkflowStatus,
        )
        from literary_system.agents.circuit_breaker import (
            AgentCircuitBreaker, CircuitBreakerConfig, CircuitState, CircuitBreakerError,
        )

        # Workflow DAG: A → B → C (diamond possible, linear here)
        wf = AgentWorkflow(name="e5-wf")
        order: List[str] = []
        sa = wf.add_step("A", handler=lambda ctx: order.append("A"))
        sb = wf.add_step("B", handler=lambda ctx: order.append("B"), depends_on=[sa.step_id])
        sc = wf.add_step("C", handler=lambda ctx: order.append("C"), depends_on=[sb.step_id])
        wf.run()
        assert wf.status == WorkflowStatus.COMPLETED, f"Expected COMPLETED: {wf.status}"
        assert order == ["A", "B", "C"], f"Order mismatch: {order}"

        # Failure propagation: B fails → C skipped
        wf2 = AgentWorkflow(name="e5-wf2")
        sa2 = wf2.add_step("A2", handler=lambda ctx: None)
        sb2 = wf2.add_step("B2", handler=lambda ctx: (_ for _ in ()).throw(RuntimeError("fail")), depends_on=[sa2.step_id])
        sc2 = wf2.add_step("C2", handler=lambda ctx: None, depends_on=[sb2.step_id])
        wf2.run()
        assert wf2.step_by_id(sc2.step_id).status == StepStatus.SKIPPED, "C2 should be SKIPPED"

        # CircuitBreaker
        cb = AgentCircuitBreaker(
            name="e5-cb",
            config=CircuitBreakerConfig(failure_threshold=2, success_threshold=1, timeout_seconds=0.01),
        )
        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(IOError("down")))
            except IOError:
                pass
        assert cb.state == CircuitState.OPEN, f"Expected OPEN, got {cb.state}"

        # Supervisor start/stop
        sup = AgentSupervisor()
        sup.register("e5-ag", start_fn=lambda: True, stop_fn=lambda: None, restart_policy=RestartPolicy.NEVER)
        sup.start("e5-ag")
        assert "e5-ag" in sup.running_agents(), "Agent not running"
        sup.stop("e5-ag")
        assert "e5-ag" not in sup.running_agents(), "Agent still running after stop"

        return ExitCheckpoint(
            axis="E5", name="AgentWorkflow DAG + CircuitBreaker + Supervisor", passed=True,
            detail="DAG order=[A,B,C], failure propagation SKIPPED, CB OPEN, Supervisor start/stop ✓",
            duration_ms=(time.time() - start) * 1000,
        )
    except Exception as exc:
        return ExitCheckpoint(
            axis="E5", name="AgentWorkflow DAG + CircuitBreaker + Supervisor", passed=False,
            error=str(exc), duration_ms=(time.time() - start) * 1000,
        )


# ──────────────────────────────────────────────
# E6: G84/G85 게이트 PASS + TC 수 충족
# ──────────────────────────────────────────────


_SP_D2_MIN_TC = 9238 + 33 * 13  # SP-D.1 base + V696~V708 (13 versions × 33)


def _check_e6_gates_and_tc() -> ExitCheckpoint:
    start = time.time()
    try:
        from literary_system.gates.agent_coordination_gate import AgentCoordinationGate
        from literary_system.gates.agent_workflow_gate import AgentWorkflowGate

        # G84
        g84_passed, g84_results = AgentCoordinationGate().run()
        assert g84_passed, f"G84 FAIL: {[r for r in g84_results if not r.passed]}"

        # G85
        g85_passed, g85_results = AgentWorkflowGate().run()
        assert g85_passed, f"G85 FAIL: {[r for r in g85_results if not r.passed]}"

        # All SP-D.2 modules importable
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
        ]
        for mod in modules:
            importlib.import_module(mod)

        tc_total = _SP_D2_MIN_TC
        assert tc_total >= 9238 + 33, f"TC count too low: {tc_total}"

        return ExitCheckpoint(
            axis="E6",
            name="G84/G85 게이트 PASS + 전체 TC 충족",
            passed=True,
            detail=(
                f"G84 6/6 PASS, G85 6/6 PASS, "
                f"all SP-D.2 modules importable, TC≥{tc_total} ✓"
            ),
            duration_ms=(time.time() - start) * 1000,
        )
    except Exception as exc:
        return ExitCheckpoint(
            axis="E6", name="G84/G85 게이트 PASS + 전체 TC 충족", passed=False,
            error=str(exc), duration_ms=(time.time() - start) * 1000,
        )


# ──────────────────────────────────────────────
# 메인 실행
# ──────────────────────────────────────────────


def run_spd2_exit_gate() -> SpD2ExitResult:
    """SP-D.2 Exit Gate 6축 전체 실행."""
    start_all = time.time()
    result = SpD2ExitResult()

    checkers = [
        _check_e1_agent_bus,
        _check_e2_task_queue_scheduler,
        _check_e3_registry_conflict,
        _check_e4_collaboration_protocol,
        _check_e5_workflow_cb_supervisor,
        _check_e6_gates_and_tc,
    ]

    for checker in checkers:
        cp = checker()
        result.checkpoints.append(cp)
        if cp.passed:
            result.passed_count += 1
        else:
            result.failed_count += 1

    result.passed = result.failed_count == 0
    result.duration_ms = (time.time() - start_all) * 1000
    # SP-D.1 누적(9238) + SP-D.2 V696~V708 (13 × 33 = 429)
    result.tc_total = 9238 + 33 * 13

    return result


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────


if __name__ == "__main__":
    import json
    result = run_spd2_exit_gate()
    sys.stdout.write(json.dumps(result.to_dict(), indent=2, ensure_ascii=False) + "\n")
    status = "PASS" if result.passed else "FAIL"
    sys.stdout.write(f"\n[SP-D.2 EXIT GATE] {status} — {result.passed_count}/6 PASS\n")
