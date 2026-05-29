"""V705 — AgentSupervisor + AgentHealthMonitor 테스트 (33 TC)."""
import pytest
from literary_system.agents.agent_supervisor import (
    AgentHealthMonitor, AgentSupervisor, HealthStatus, HealthRecord,
    RestartPolicy, SupervisedAgent, ADR_167,
)


# ══════════════════════════════════════════════════════════════════════
class TestAgentHealthMonitor:
    def test_tc01_register_no_checker(self):
        m = AgentHealthMonitor()
        r = m.register("agent-A")
        assert r.agent_id == "agent-A"
        assert r.status == HealthStatus.UNKNOWN

    def test_tc02_check_no_checker_healthy(self):
        m = AgentHealthMonitor()
        m.register("a")
        r = m.check("a")
        assert r.status == HealthStatus.HEALTHY

    def test_tc03_check_passing_checker(self):
        m = AgentHealthMonitor()
        m.register("a", checker=lambda: True)
        r = m.check("a")
        assert r.status == HealthStatus.HEALTHY

    def test_tc04_check_failing_checker_degraded(self):
        m = AgentHealthMonitor(degraded_threshold=1, failure_threshold=3)
        m.register("a", checker=lambda: False)
        r = m.check("a")
        assert r.status == HealthStatus.DEGRADED

    def test_tc05_consecutive_failures_unhealthy(self):
        m = AgentHealthMonitor(failure_threshold=2)
        m.register("a", checker=lambda: False)
        m.check("a"); m.check("a")
        r = m.get_record("a")
        assert r.status == HealthStatus.UNHEALTHY

    def test_tc06_recovery_resets_failures(self):
        m = AgentHealthMonitor(failure_threshold=3)
        flag = [False]
        m.register("a", checker=lambda: flag[0])
        m.check("a"); m.check("a")
        assert m.get_record("a").consecutive_failures == 2
        flag[0] = True
        m.check("a")
        assert m.get_record("a").consecutive_failures == 0
        assert m.get_record("a").status == HealthStatus.HEALTHY

    def test_tc07_check_all(self):
        m = AgentHealthMonitor()
        m.register("a"); m.register("b")
        records = m.check_all()
        assert "a" in records and "b" in records

    def test_tc08_healthy_agents_list(self):
        m = AgentHealthMonitor()
        m.register("a", checker=lambda: True)
        m.register("b", checker=lambda: False)
        m.check("a"); m.check("b")
        assert "a" in m.healthy_agents()
        assert "b" not in m.healthy_agents()

    def test_tc09_unhealthy_agents_list(self):
        m = AgentHealthMonitor(failure_threshold=1)
        m.register("a", checker=lambda: False)
        m.check("a")
        assert "a" in m.unhealthy_agents()

    def test_tc10_failure_rate(self):
        m = AgentHealthMonitor(failure_threshold=10)
        m.register("a", checker=lambda: False)
        m.check("a"); m.check("a")
        r = m.get_record("a")
        assert r.failure_rate() == 1.0

    def test_tc11_checker_exception_counted_as_failure(self):
        m = AgentHealthMonitor(failure_threshold=10)
        def bad_checker():
            raise RuntimeError("check error")
        m.register("a", checker=bad_checker)
        r = m.check("a")
        assert r.total_failures == 1
        assert "check error" in r.message

    def test_tc12_unknown_agent_check(self):
        m = AgentHealthMonitor()
        r = m.check("ghost")
        assert r.status == HealthStatus.UNKNOWN

    def test_tc13_status_changed_hook(self):
        m = AgentHealthMonitor(failure_threshold=1)
        changes = []
        m.on("status_changed", lambda r: changes.append(r.status))
        m.register("a", checker=lambda: False)
        m.check("a")
        assert HealthStatus.UNHEALTHY in changes

    def test_tc14_checked_hook(self):
        m = AgentHealthMonitor()
        fired = []
        m.on("checked", lambda r: fired.append(r.agent_id))
        m.register("a", checker=lambda: True)
        m.check("a")
        assert "a" in fired

    def test_tc15_stats(self):
        m = AgentHealthMonitor()
        m.register("a"); m.register("b")
        m.check("a"); m.check("b")
        st = m.stats()
        assert st["total"] == 2

    def test_tc16_to_dict(self):
        m = AgentHealthMonitor()
        m.register("a", checker=lambda: True)
        m.check("a")
        d = m.get_record("a").to_dict()
        assert d["agent_id"] == "a"
        assert d["status"] == "healthy"


# ══════════════════════════════════════════════════════════════════════
class TestAgentSupervisor:
    def test_tc17_register_agent(self):
        sup = AgentSupervisor()
        sa = sup.register("agent-A")
        assert sa.agent_id == "agent-A"
        assert not sa.running

    def test_tc18_start_agent(self):
        sup = AgentSupervisor()
        sup.register("a", start_fn=lambda: True)
        ok = sup.start("a")
        assert ok
        assert sup.get_agent("a").running

    def test_tc19_start_fail(self):
        sup = AgentSupervisor()
        sup.register("a", start_fn=lambda: False)
        ok = sup.start("a")
        assert not ok

    def test_tc20_stop_agent(self):
        sup = AgentSupervisor()
        sup.register("a", start_fn=lambda: True)
        sup.start("a")
        ok = sup.stop("a")
        assert ok
        assert not sup.get_agent("a").running

    def test_tc21_restart_increments_count(self):
        sup = AgentSupervisor()
        sup.register("a", start_fn=lambda: True)
        sup.start("a")
        sup.restart("a")
        assert sup.get_agent("a").restart_count == 1

    def test_tc22_max_restarts_limit(self):
        sup = AgentSupervisor()
        sup.register("a", start_fn=lambda: True, max_restarts=2)
        sup.start("a")
        sup.restart("a"); sup.restart("a")
        ok = sup.restart("a")  # 3rd — exceeds max
        assert not ok

    def test_tc23_restart_policy_never(self):
        sup = AgentSupervisor()
        sup.register("a", start_fn=lambda: True,
                     restart_policy=RestartPolicy.NEVER)
        sup.start("a")
        ok = sup.restart("a")
        assert not ok

    def test_tc24_supervise_restarts_unhealthy(self):
        fail_flag = [True]
        sup = AgentSupervisor()
        sup.register("a", start_fn=lambda: True,
                     health_checker=lambda: not fail_flag[0],
                     restart_policy=RestartPolicy.ON_FAILURE,
                     max_restarts=3)
        sup.start("a")
        # force 3 failures → unhealthy
        for _ in range(3):
            sup._health.check("a")
        restarted = sup.supervise()
        assert "a" in restarted

    def test_tc25_supervise_no_restart_when_healthy(self):
        sup = AgentSupervisor()
        sup.register("a", start_fn=lambda: True,
                     health_checker=lambda: True)
        sup.start("a")
        restarted = sup.supervise()
        assert "a" not in restarted

    def test_tc26_running_agents(self):
        sup = AgentSupervisor()
        sup.register("a", start_fn=lambda: True)
        sup.register("b", start_fn=lambda: True)
        sup.start("a")
        running = sup.running_agents()
        assert "a" in running
        assert "b" not in running

    def test_tc27_started_hook(self):
        sup = AgentSupervisor()
        fired = []
        sup.on("started", lambda sa: fired.append(sa.agent_id))
        sup.register("a", start_fn=lambda: True)
        sup.start("a")
        assert "a" in fired

    def test_tc28_stopped_hook(self):
        sup = AgentSupervisor()
        fired = []
        sup.on("stopped", lambda sa: fired.append(sa.agent_id))
        sup.register("a", start_fn=lambda: True)
        sup.start("a"); sup.stop("a")
        assert "a" in fired

    def test_tc29_restarted_hook(self):
        sup = AgentSupervisor()
        fired = []
        sup.on("restarted", lambda sa: fired.append(sa.agent_id))
        sup.register("a", start_fn=lambda: True)
        sup.start("a"); sup.restart("a")
        assert "a" in fired

    def test_tc30_stats(self):
        sup = AgentSupervisor()
        sup.register("a", start_fn=lambda: True)
        sup.register("b", start_fn=lambda: True)
        sup.start("a")
        st = sup.stats()
        assert st["total"] == 2
        assert st["running"] == 1

    def test_tc31_cannot_start_already_running(self):
        sup = AgentSupervisor()
        sup.register("a", start_fn=lambda: True)
        sup.start("a")
        ok2 = sup.start("a")
        assert not ok2

    def test_tc32_cannot_stop_not_running(self):
        sup = AgentSupervisor()
        sup.register("a")
        ok = sup.stop("a")
        assert not ok

    def test_tc33_adr_167(self):
        assert ADR_167["id"] == "ADR-167"
        assert ADR_167["status"] == "accepted"
        assert "Supervisor" in ADR_167["title"]
