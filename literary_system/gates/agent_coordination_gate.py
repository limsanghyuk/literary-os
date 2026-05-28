"""V706 — Gate G84 AgentCoordination Gate (SP-D.2) ADR-168.

SP-D.2 핵심 에이전트 조율 모듈 6종이 올바르게 구현되었는지 검증한다.
"""
from __future__ import annotations
import importlib, sys, logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


@dataclass
class GateCheckResult:
    check_id: str
    description: str
    passed: bool
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "description": self.description,
            "passed": self.passed,
            "message": self.message,
        }


class AgentCoordinationGate:
    """G84: SP-D.2 에이전트 조율 레이어 6축 게이트.

    E1 — AgentMessage / AgentBus 임포트 및 기본 기능
    E2 — AgentTask / TaskQueue 우선순위 큐
    E3 — AgentCapabilityRegistry 능력 등록 및 하트비트
    E4 — AgentTaskScheduler 틱 기반 dispatch
    E5 — AgentCollaborationProtocol 세션 수명주기
    E6 — AgentConflictResolver 전략 실행
    """

    GATE_ID = "G84"

    def run(self) -> Tuple[bool, List[GateCheckResult]]:
        results: List[GateCheckResult] = []
        results.append(self._check_e1())
        results.append(self._check_e2())
        results.append(self._check_e3())
        results.append(self._check_e4())
        results.append(self._check_e5())
        results.append(self._check_e6())
        passed = all(r.passed for r in results)
        return passed, results

    # ── E1: AgentMessage / AgentBus ─────────────────────────────────────

    def _check_e1(self) -> GateCheckResult:
        cid = "E1"
        desc = "AgentMessage/AgentBus 임포트 및 publish/subscribe 동작"
        try:
            from literary_system.agents.agent_message import (
                AgentBus, AgentMessage, MessageType, MessagePriority,
            )
            bus = AgentBus()
            received = []
            bus.subscribe("agent-A", handler=lambda m: received.append(m))
            msg = AgentMessage.broadcast(
                sender="agent-B",
                payload={"test": True},
                priority=MessagePriority.HIGH,
            )
            bus.publish(msg)
            inbox = bus.get_messages("agent-A")
            assert len(inbox) > 0, "broadcast not received"
            assert bus.stats()["published"] >= 1
            return GateCheckResult(cid, desc, True, f"published={bus.stats()['published']}")
        except Exception as exc:
            return GateCheckResult(cid, desc, False, str(exc))

    # ── E2: AgentTask / TaskQueue ────────────────────────────────────────

    def _check_e2(self) -> GateCheckResult:
        cid = "E2"
        desc = "AgentTask/TaskQueue 우선순위 큐 enqueue/dequeue"
        try:
            from literary_system.agents.agent_task import (
                AgentTask, TaskQueue, TaskPriority, TaskStatus,
            )
            q = TaskQueue("gate-q")
            t_low = AgentTask(name="low", assigned_agent="a", payload={},
                              priority=TaskPriority.LOW)
            t_high = AgentTask(name="high", assigned_agent="a", payload={},
                               priority=TaskPriority.CRITICAL)
            q.enqueue(t_low); q.enqueue(t_high)
            first = q.dequeue()
            assert first.name == "high", f"expected high, got {first.name}"
            assert first.priority == TaskPriority.CRITICAL
            return GateCheckResult(cid, desc, True, "CRITICAL dequeued first ✓")
        except Exception as exc:
            return GateCheckResult(cid, desc, False, str(exc))

    # ── E3: AgentCapabilityRegistry ─────────────────────────────────────

    def _check_e3(self) -> GateCheckResult:
        cid = "E3"
        desc = "AgentCapabilityRegistry 능력 등록 + agents_with_capability"
        try:
            from literary_system.agents.capability_registry import (
                AgentCapabilityRegistry, AgentCapability,
            )
            reg = AgentCapabilityRegistry()
            cap = AgentCapability(name="write", description="write prose",
                                  version="1.0", tags=["nlp"])
            reg.register("writer-A", [cap])
            agent_profiles = reg.agents_with_capability("write")
            agents = [p.agent_id for p in agent_profiles]
            assert "writer-A" in agents, "writer-A not found"
            st = reg.stats()
            assert st["total"] >= 1
            return GateCheckResult(cid, desc, True, f"agents={agents}")
        except Exception as exc:
            return GateCheckResult(cid, desc, False, str(exc))

    # ── E4: AgentTaskScheduler ───────────────────────────────────────────

    def _check_e4(self) -> GateCheckResult:
        cid = "E4"
        desc = "AgentTaskScheduler schedule + tick dispatch"
        try:
            from literary_system.agents.task_scheduler import AgentTaskScheduler
            from literary_system.agents.agent_task import AgentTask, TaskPriority, TaskStatus
            sched = AgentTaskScheduler()
            results: list = []
            sched.register_handler("gate_test", lambda t: (results.append(t.name), True)[1])
            t = AgentTask(name="gate_task", assigned_agent="x", payload={},
                          tags=["gate_test"])
            ok = sched.schedule(t)
            assert ok, "schedule returned False"
            dispatched = sched.tick()
            assert dispatched == 1, f"expected 1 dispatch, got {dispatched}"
            assert t.status == TaskStatus.DONE
            return GateCheckResult(cid, desc, True, "task dispatched and DONE ✓")
        except Exception as exc:
            return GateCheckResult(cid, desc, False, str(exc))

    # ── E5: AgentCollaborationProtocol ──────────────────────────────────

    def _check_e5(self) -> GateCheckResult:
        cid = "E5"
        desc = "AgentCollaborationProtocol propose→accept→start→complete"
        try:
            from literary_system.agents.collaboration_protocol import (
                AgentCollaborationProtocol, CollaborationState,
            )
            proto = AgentCollaborationProtocol()
            s = proto.propose("orchestrator", "gate_e5_task",
                              participants=["worker"])
            assert s.state == CollaborationState.PROPOSED
            proto.accept(s.session_id, "worker")
            proto.start(s.session_id)
            proto.complete(s.session_id, result="done")
            assert s.state == CollaborationState.COMPLETED
            st = proto.stats()
            assert st["total"] == 1
            return GateCheckResult(cid, desc, True, "full lifecycle ✓")
        except Exception as exc:
            return GateCheckResult(cid, desc, False, str(exc))

    # ── E6: AgentConflictResolver ────────────────────────────────────────

    def _check_e6(self) -> GateCheckResult:
        cid = "E6"
        desc = "AgentConflictResolver PRIORITY_BASED resolution"
        try:
            from literary_system.agents.conflict_resolver import (
                AgentConflictResolver, ConflictType, ConflictParty,
                ResolutionStrategy, ConflictState,
            )
            resolver = AgentConflictResolver()
            parties = [
                ConflictParty(agent_id="low", priority=1, claim="claimA"),
                ConflictParty(agent_id="high", priority=9, claim="claimB"),
            ]
            c = resolver.register(ConflictType.RESOURCE, parties,
                                  ResolutionStrategy.PRIORITY_BASED)
            ok = resolver.resolve(c.conflict_id)
            assert ok, "resolve returned False"
            assert c.winner == "high", f"expected 'high', got {c.winner}"
            assert c.state == ConflictState.RESOLVED
            return GateCheckResult(cid, desc, True, f"winner={c.winner} ✓")
        except Exception as exc:
            return GateCheckResult(cid, desc, False, str(exc))


ADR_168 = {
    "id": "ADR-168",
    "title": "Gate G84 AgentCoordination Gate",
    "status": "accepted",
    "decision": "SP-D.2 에이전트 조율 6축(E1~E6) 통합 게이트. 6/6 PASS 필수.",
    "version": "V706",
}


def main() -> None:
    import json
    gate = AgentCoordinationGate()
    passed, results = gate.run()
    summary = {
        "gate": gate.GATE_ID,
        "passed": passed,
        "checks": [r.to_dict() for r in results],
        "score": f"{sum(r.passed for r in results)}/{len(results)}",
    }
    sys.stdout.write(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
