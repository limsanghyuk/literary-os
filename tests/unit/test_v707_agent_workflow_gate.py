"""V707 — Gate G85 AgentWorkflow Gate 테스트 (33 TC)."""
import pytest
from literary_system.gates.agent_workflow_gate import (
    AgentWorkflowGate, GateCheckResult, ADR_169,
)


def make_gate() -> AgentWorkflowGate:
    return AgentWorkflowGate()


# ══════════════════════════════════════════════════════════════════════
class TestAgentWorkflowGate:
    def test_tc01_gate_id(self):
        assert AgentWorkflowGate.GATE_ID == "G85"

    def test_tc02_run_returns_tuple(self):
        g = make_gate()
        result = g.run()
        assert isinstance(result, tuple) and len(result) == 2

    def test_tc03_run_6_checks(self):
        g = make_gate()
        _, results = g.run()
        assert len(results) == 6

    def test_tc04_all_checks_pass(self):
        g = make_gate()
        passed, results = g.run()
        assert passed, [r.to_dict() for r in results if not r.passed]

    def test_tc05_e1_workflow_dag(self):
        g = make_gate()
        assert g._check_e1().passed

    def test_tc06_e2_load_balancer(self):
        g = make_gate()
        assert g._check_e2().passed

    def test_tc07_e3_circuit_breaker(self):
        g = make_gate()
        assert g._check_e3().passed

    def test_tc08_e4_supervisor(self):
        g = make_gate()
        assert g._check_e4().passed

    def test_tc09_e5_health_monitor(self):
        g = make_gate()
        assert g._check_e5().passed

    def test_tc10_e6_downstream_skip(self):
        g = make_gate()
        assert g._check_e6().passed

    def test_tc11_check_ids_unique(self):
        g = make_gate()
        _, results = g.run()
        ids = [r.check_id for r in results]
        assert len(ids) == len(set(ids))

    def test_tc12_check_ids_e1_to_e6(self):
        g = make_gate()
        _, results = g.run()
        ids = {r.check_id for r in results}
        for eid in ("E1", "E2", "E3", "E4", "E5", "E6"):
            assert eid in ids

    def test_tc13_score_6_of_6(self):
        g = make_gate()
        _, results = g.run()
        assert sum(r.passed for r in results) == 6

    def test_tc14_to_dict(self):
        r = GateCheckResult("E1", "test", True, "ok")
        d = r.to_dict()
        assert d["passed"] is True and d["check_id"] == "E1"

    def test_tc15_gate_rerunnable(self):
        g = make_gate()
        p1, r1 = g.run(); p2, r2 = g.run()
        assert p1 == p2

    # ── 개별 모듈 상세 검증 ───────────────────────────────────────────────

    def test_tc16_workflow_diamond_dag(self):
        from literary_system.agents.agent_workflow import AgentWorkflow
        order = []
        wf = AgentWorkflow()
        wf.add_step("A", lambda ctx: order.append("A"), step_id="A")
        wf.add_step("B", lambda ctx: order.append("B"), step_id="B", depends_on=["A"])
        wf.add_step("C", lambda ctx: order.append("C"), step_id="C", depends_on=["A"])
        wf.add_step("D", lambda ctx: order.append("D"), step_id="D", depends_on=["B", "C"])
        assert wf.run()
        assert order[0] == "A" and order[-1] == "D"

    def test_tc17_lb_round_robin(self):
        from literary_system.agents.load_balancer import AgentLoadBalancer, BalancingStrategy
        lb = AgentLoadBalancer(BalancingStrategy.ROUND_ROBIN)
        lb.register("a"); lb.register("b")
        seen = {lb.select().agent_id for _ in range(4)}
        assert seen == {"a", "b"}

    def test_tc18_cb_half_open_recovery(self):
        import time
        from literary_system.agents.circuit_breaker import (
            AgentCircuitBreaker, CircuitBreakerConfig, CircuitState,
        )
        cfg = CircuitBreakerConfig(failure_threshold=1, success_threshold=1, timeout_seconds=0.01)
        cb = AgentCircuitBreaker(config=cfg)
        try: cb.call(lambda: (_ for _ in ()).throw(ValueError()))
        except ValueError: pass
        time.sleep(0.02)
        cb.call(lambda: "ok")
        assert cb.is_closed()

    def test_tc19_supervisor_max_restarts(self):
        from literary_system.agents.agent_supervisor import AgentSupervisor
        sup = AgentSupervisor()
        sup.register("a", start_fn=lambda: True, max_restarts=2)
        sup.start("a")
        sup.restart("a"); sup.restart("a")
        assert not sup.restart("a")  # exceeded

    def test_tc20_health_monitor_recovery(self):
        from literary_system.agents.agent_supervisor import AgentHealthMonitor, HealthStatus
        flag = [False]
        m = AgentHealthMonitor(failure_threshold=2)
        m.register("a", checker=lambda: flag[0])
        m.check("a"); m.check("a")
        assert m.get_record("a").status == HealthStatus.UNHEALTHY
        flag[0] = True
        m.check("a")
        assert m.get_record("a").status == HealthStatus.HEALTHY

    def test_tc21_workflow_context_shared(self):
        from literary_system.agents.agent_workflow import AgentWorkflow
        wf = AgentWorkflow()
        wf.add_step("write", lambda ctx: ctx.data.update({"v": 99}), step_id="w")
        wf.add_step("read", lambda ctx: ctx.data["v"], step_id="r", depends_on=["w"])
        wf.run()
        assert wf.context.step_results["r"] == 99

    def test_tc22_lb_offline_excluded(self):
        from literary_system.agents.load_balancer import AgentLoadBalancer, BalancingStrategy
        lb = AgentLoadBalancer(BalancingStrategy.ROUND_ROBIN)
        lb.register("a"); lb.register("b")
        lb.set_online("a", False)
        for _ in range(5):
            assert lb.select().agent_id == "b"

    def test_tc23_cb_stats(self):
        from literary_system.agents.circuit_breaker import AgentCircuitBreaker, CircuitBreakerConfig
        cb = AgentCircuitBreaker(config=CircuitBreakerConfig(failure_threshold=10))
        cb.call(lambda: "ok"); cb.call(lambda: "ok")
        st = cb.stats()
        assert st["success_calls"] == 2

    def test_tc24_supervisor_hook(self):
        from literary_system.agents.agent_supervisor import AgentSupervisor
        sup = AgentSupervisor()
        fired = []
        sup.on("started", lambda sa: fired.append(sa.agent_id))
        sup.register("a", start_fn=lambda: True)
        sup.start("a")
        assert "a" in fired

    def test_tc25_health_stats(self):
        from literary_system.agents.agent_supervisor import AgentHealthMonitor
        m = AgentHealthMonitor()
        m.register("a"); m.register("b")
        m.check("a"); m.check("b")
        st = m.stats()
        assert st["total"] == 2

    def test_tc26_workflow_step_error_message(self):
        from literary_system.agents.agent_workflow import AgentWorkflow, StepStatus
        wf = AgentWorkflow()
        wf.add_step("bad", lambda ctx: (_ for _ in ()).throw(ValueError("boom")), step_id="bad")
        wf.run()
        assert "boom" in wf._steps["bad"].error

    def test_tc27_lb_assign_release(self):
        from literary_system.agents.load_balancer import AgentLoadBalancer, BalancingStrategy
        lb = AgentLoadBalancer(BalancingStrategy.LEAST_LOADED)
        lb.register("a")
        aid = lb.assign()
        assert lb.get_node("a").active_tasks == 1
        lb.release(aid)
        assert lb.get_node("a").active_tasks == 0

    def test_tc28_circuit_breaker_manual_trip_reset(self):
        from literary_system.agents.circuit_breaker import AgentCircuitBreaker
        cb = AgentCircuitBreaker()
        cb.trip()
        assert cb.is_open()
        cb.reset()
        assert cb.is_closed()

    def test_tc29_supervisor_auto_restart(self):
        from literary_system.agents.agent_supervisor import AgentSupervisor, AgentHealthMonitor
        fail_flag = [True]
        hm = AgentHealthMonitor(failure_threshold=1)
        sup = AgentSupervisor(health_monitor=hm)
        sup.register("a", start_fn=lambda: True,
                     health_checker=lambda: not fail_flag[0],
                     max_restarts=2)
        sup.start("a")
        hm.check("a")
        restarted = sup.supervise()
        assert "a" in restarted

    def test_tc30_workflow_cancel(self):
        from literary_system.agents.agent_workflow import AgentWorkflow, WorkflowStatus
        wf = AgentWorkflow()
        ok = wf.cancel()
        assert ok and wf.status == WorkflowStatus.CANCELLED

    def test_tc31_health_monitor_degraded_threshold(self):
        from literary_system.agents.agent_supervisor import AgentHealthMonitor, HealthStatus
        m = AgentHealthMonitor(failure_threshold=5, degraded_threshold=2)
        m.register("a", checker=lambda: False)
        m.check("a"); m.check("a")
        assert m.get_record("a").status == HealthStatus.DEGRADED
        for _ in range(3):
            m.check("a")
        assert m.get_record("a").status == HealthStatus.UNHEALTHY

    def test_tc32_adr_169(self):
        assert ADR_169["id"] == "ADR-169"
        assert ADR_169["status"] == "accepted"
        assert "G85" in ADR_169["title"]

    def test_tc33_gate_descriptions_coverage(self):
        g = make_gate()
        _, results = g.run()
        descs = " ".join(r.description for r in results)
        for kw in ("DAG", "LoadBalancer", "CircuitBreaker", "Supervisor", "HealthMonitor", "스킵"):
            assert kw in descs, f"Missing: {kw}"
