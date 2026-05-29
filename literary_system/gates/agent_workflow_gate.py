"""V707 — Gate G85 AgentWorkflow Gate (SP-D.2) ADR-169.

SP-D.2 고급 에이전트 패턴 4종이 올바르게 구현되었는지 검증한다.
"""
from __future__ import annotations
import sys, logging
from dataclasses import dataclass
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


class AgentWorkflowGate:
    """G85: SP-D.2 고급 에이전트 패턴 6축 게이트.

    E1 — AgentWorkflow DAG 실행 + 의존성 순서 보장
    E2 — AgentLoadBalancer 부하 분산 (LEAST_LOADED)
    E3 — AgentCircuitBreaker CLOSED→OPEN 전이
    E4 — AgentSupervisor 수명주기 (start/stop/restart)
    E5 — AgentHealthMonitor 헬스체크 + UNHEALTHY 판정
    E6 — Workflow 실패 시 다운스트림 스킵 검증
    """

    GATE_ID = "G85"

    def run(self) -> Tuple[bool, List[GateCheckResult]]:
        results = [
            self._check_e1(),
            self._check_e2(),
            self._check_e3(),
            self._check_e4(),
            self._check_e5(),
            self._check_e6(),
        ]
        passed = all(r.passed for r in results)
        return passed, results

    # ── E1: AgentWorkflow DAG ────────────────────────────────────────────

    def _check_e1(self) -> GateCheckResult:
        cid = "E1"
        desc = "AgentWorkflow DAG 실행 + 의존성 순서 보장"
        try:
            from literary_system.agents.agent_workflow import AgentWorkflow, WorkflowContext
            order: list = []
            wf = AgentWorkflow(name="gate_e1")
            wf.add_step("A", lambda ctx: order.append("A"), step_id="A")
            wf.add_step("B", lambda ctx: order.append("B"), step_id="B", depends_on=["A"])
            wf.add_step("C", lambda ctx: order.append("C"), step_id="C", depends_on=["A"])
            wf.add_step("D", lambda ctx: order.append("D"), step_id="D", depends_on=["B", "C"])
            ok = wf.run()
            assert ok, f"workflow failed: {[(s.name, s.status) for s in wf.steps()]}"
            assert order[0] == "A", f"A must be first, got {order}"
            assert order[-1] == "D", f"D must be last, got {order}"
            return GateCheckResult(cid, desc, True, f"order={order} ✓")
        except Exception as exc:
            return GateCheckResult(cid, desc, False, str(exc))

    # ── E2: AgentLoadBalancer ────────────────────────────────────────────

    def _check_e2(self) -> GateCheckResult:
        cid = "E2"
        desc = "AgentLoadBalancer LEAST_LOADED 선택"
        try:
            from literary_system.agents.load_balancer import AgentLoadBalancer, BalancingStrategy
            lb = AgentLoadBalancer(strategy=BalancingStrategy.LEAST_LOADED)
            lb.register("heavy", capacity=10)
            lb.register("light", capacity=10)
            lb.get_node("heavy").active_tasks = 7
            lb.get_node("light").active_tasks = 1
            node = lb.select()
            assert node is not None, "select returned None"
            assert node.agent_id == "light", f"expected light, got {node.agent_id}"
            # assign/release cycle
            aid = lb.assign()
            assert aid == "light"
            lb.release(aid)
            assert lb.get_node("light").active_tasks == 1  # restored
            return GateCheckResult(cid, desc, True, f"selected={node.agent_id} ✓")
        except Exception as exc:
            return GateCheckResult(cid, desc, False, str(exc))

    # ── E3: AgentCircuitBreaker ──────────────────────────────────────────

    def _check_e3(self) -> GateCheckResult:
        cid = "E3"
        desc = "AgentCircuitBreaker CLOSED→OPEN 전이 + fast-fail"
        try:
            from literary_system.agents.circuit_breaker import (
                AgentCircuitBreaker, CircuitBreakerConfig, CircuitState, CircuitBreakerError,
            )
            cfg = CircuitBreakerConfig(failure_threshold=2, timeout_seconds=60.0)
            cb = AgentCircuitBreaker(name="gate-cb", config=cfg)
            assert cb.state == CircuitState.CLOSED
            for _ in range(2):
                try:
                    cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
                except ValueError:
                    pass
            assert cb.state == CircuitState.OPEN, f"expected OPEN, got {cb.state}"
            try:
                cb.call(lambda: "ok")
                assert False, "should have raised CircuitBreakerError"
            except CircuitBreakerError:
                pass
            return GateCheckResult(cid, desc, True, "OPEN blocks requests ✓")
        except Exception as exc:
            return GateCheckResult(cid, desc, False, str(exc))

    # ── E4: AgentSupervisor ──────────────────────────────────────────────

    def _check_e4(self) -> GateCheckResult:
        cid = "E4"
        desc = "AgentSupervisor start/stop/restart 수명주기"
        try:
            from literary_system.agents.agent_supervisor import AgentSupervisor, RestartPolicy
            sup = AgentSupervisor()
            sup.register("worker", start_fn=lambda: True, stop_fn=lambda: None,
                         restart_policy=RestartPolicy.ON_FAILURE, max_restarts=3)
            ok = sup.start("worker")
            assert ok, "start failed"
            assert "worker" in sup.running_agents()
            ok2 = sup.stop("worker")
            assert ok2, "stop failed"
            assert "worker" not in sup.running_agents()
            sup.start("worker")
            ok3 = sup.restart("worker")
            assert ok3, "restart failed"
            assert sup.get_agent("worker").restart_count == 1
            return GateCheckResult(cid, desc, True, "lifecycle ✓")
        except Exception as exc:
            return GateCheckResult(cid, desc, False, str(exc))

    # ── E5: AgentHealthMonitor ───────────────────────────────────────────

    def _check_e5(self) -> GateCheckResult:
        cid = "E5"
        desc = "AgentHealthMonitor 연속 실패 → UNHEALTHY 판정"
        try:
            from literary_system.agents.agent_supervisor import (
                AgentHealthMonitor, HealthStatus,
            )
            monitor = AgentHealthMonitor(failure_threshold=2, degraded_threshold=1)
            monitor.register("probe", checker=lambda: False)
            monitor.check("probe")  # 1 failure → DEGRADED
            r1 = monitor.get_record("probe")
            assert r1.status == HealthStatus.DEGRADED, f"expected DEGRADED, got {r1.status}"
            monitor.check("probe")  # 2 failures → UNHEALTHY
            r2 = monitor.get_record("probe")
            assert r2.status == HealthStatus.UNHEALTHY, f"expected UNHEALTHY, got {r2.status}"
            assert "probe" in monitor.unhealthy_agents()
            return GateCheckResult(cid, desc, True, "DEGRADED→UNHEALTHY ✓")
        except Exception as exc:
            return GateCheckResult(cid, desc, False, str(exc))

    # ── E6: Workflow downstream skip ──────────────────────────────────────

    def _check_e6(self) -> GateCheckResult:
        cid = "E6"
        desc = "Workflow 실패 시 다운스트림 스킵 검증"
        try:
            from literary_system.agents.agent_workflow import AgentWorkflow, StepStatus
            wf = AgentWorkflow(name="gate_e6")
            wf.add_step("root", lambda ctx: (_ for _ in ()).throw(RuntimeError("root fail")),
                        step_id="root")
            wf.add_step("child", lambda ctx: "never", step_id="child", depends_on=["root"])
            wf.add_step("grandchild", lambda ctx: "never", step_id="gc", depends_on=["child"])
            ok = wf.run()
            assert not ok, "workflow should have failed"
            assert wf._steps["root"].status == StepStatus.FAILED
            assert wf._steps["child"].status == StepStatus.SKIPPED
            assert wf._steps["gc"].status == StepStatus.SKIPPED
            return GateCheckResult(cid, desc, True, "downstream skip ✓")
        except Exception as exc:
            return GateCheckResult(cid, desc, False, str(exc))


ADR_169 = {
    "id": "ADR-169",
    "title": "Gate G85 AgentWorkflow Gate",
    "status": "accepted",
    "decision": "SP-D.2 고급 에이전트 패턴 6축(E1~E6) 게이트. 6/6 PASS 필수.",
    "version": "V707",
}


def main() -> None:
    import json
    gate = AgentWorkflowGate()
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
