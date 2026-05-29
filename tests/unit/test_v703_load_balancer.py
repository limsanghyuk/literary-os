"""V703 — AgentLoadBalancer 테스트 (33 TC)."""
import pytest
from literary_system.agents.load_balancer import (
    AgentLoadBalancer, AgentNode, BalancingStrategy, ADR_165,
)


def make_lb(strategy=BalancingStrategy.ROUND_ROBIN) -> AgentLoadBalancer:
    return AgentLoadBalancer(strategy=strategy)


# ══════════════════════════════════════════════════════════════════════
class TestAgentNode:
    def test_tc01_node_creation(self):
        n = AgentNode(agent_id="a", capacity=5)
        assert n.agent_id == "a"
        assert n.capacity == 5
        assert n.active_tasks == 0
        assert n.online is True

    def test_tc02_load_ratio(self):
        n = AgentNode(agent_id="a", capacity=10)
        n.active_tasks = 5
        assert n.load_ratio() == 0.5

    def test_tc03_is_available(self):
        n = AgentNode(agent_id="a", capacity=2)
        n.active_tasks = 1
        assert n.is_available()
        n.active_tasks = 2
        assert not n.is_available()

    def test_tc04_is_unavailable_when_offline(self):
        n = AgentNode(agent_id="a", capacity=10, online=False)
        assert not n.is_available()

    def test_tc05_assign_increments(self):
        n = AgentNode(agent_id="a", capacity=10)
        n.assign()
        assert n.active_tasks == 1
        assert n.total_handled == 1

    def test_tc06_release_decrements(self):
        n = AgentNode(agent_id="a", capacity=10)
        n.assign()
        n.release()
        assert n.active_tasks == 0

    def test_tc07_release_failed(self):
        n = AgentNode(agent_id="a", capacity=10)
        n.assign()
        n.release(failed=True)
        assert n.failed_tasks == 1

    def test_tc08_release_no_underflow(self):
        n = AgentNode(agent_id="a", capacity=10)
        n.release()  # already 0
        assert n.active_tasks == 0

    def test_tc09_to_dict(self):
        n = AgentNode(agent_id="a", capacity=5)
        d = n.to_dict()
        assert d["agent_id"] == "a"
        assert d["capacity"] == 5


class TestLoadBalancer:
    def test_tc10_register_node(self):
        lb = make_lb()
        node = lb.register("agent-1", capacity=5)
        assert node.agent_id == "agent-1"
        assert lb.get_node("agent-1") is node

    def test_tc11_deregister_node(self):
        lb = make_lb()
        lb.register("agent-1")
        ok = lb.deregister("agent-1")
        assert ok
        assert lb.get_node("agent-1") is None

    def test_tc12_deregister_nonexistent(self):
        lb = make_lb()
        assert not lb.deregister("ghost")

    def test_tc13_set_offline(self):
        lb = make_lb()
        lb.register("a")
        lb.set_online("a", False)
        assert not lb.get_node("a").online

    def test_tc14_round_robin_cycles(self):
        lb = make_lb(BalancingStrategy.ROUND_ROBIN)
        lb.register("a"); lb.register("b")
        seq = [lb.select().agent_id for _ in range(4)]
        assert seq[0] != seq[1]  # alternates
        assert set(seq) == {"a", "b"}

    def test_tc15_least_loaded_selects_min(self):
        lb = make_lb(BalancingStrategy.LEAST_LOADED)
        lb.register("a", capacity=10)
        lb.register("b", capacity=10)
        lb.get_node("a").active_tasks = 5
        lb.get_node("b").active_tasks = 2
        selected = lb.select()
        assert selected.agent_id == "b"

    def test_tc16_weighted_returns_available(self):
        lb = make_lb(BalancingStrategy.WEIGHTED)
        lb.register("a", weight=1)
        lb.register("b", weight=99)
        # Run many times — b should dominate (but not guaranteed exact %)
        for _ in range(20):
            n = lb.select()
            assert n is not None

    def test_tc17_random_returns_available(self):
        lb = make_lb(BalancingStrategy.RANDOM)
        lb.register("a")
        lb.register("b")
        for _ in range(10):
            n = lb.select()
            assert n is not None
            assert n.agent_id in ("a", "b")

    def test_tc18_select_none_when_empty(self):
        lb = make_lb()
        assert lb.select() is None

    def test_tc19_select_none_when_all_offline(self):
        lb = make_lb()
        lb.register("a")
        lb.set_online("a", False)
        assert lb.select() is None

    def test_tc20_select_none_when_all_full(self):
        lb = make_lb()
        lb.register("a", capacity=1)
        lb.get_node("a").active_tasks = 1
        assert lb.select() is None

    def test_tc21_assign_returns_agent_id(self):
        lb = make_lb()
        lb.register("a")
        aid = lb.assign()
        assert aid == "a"
        assert lb.get_node("a").active_tasks == 1

    def test_tc22_assign_none_when_unavailable(self):
        lb = make_lb()
        assert lb.assign() is None

    def test_tc23_release_ok(self):
        lb = make_lb()
        lb.register("a")
        lb.assign()
        ok = lb.release("a")
        assert ok
        assert lb.get_node("a").active_tasks == 0

    def test_tc24_release_nonexistent(self):
        lb = make_lb()
        assert not lb.release("ghost")

    def test_tc25_available_nodes(self):
        lb = make_lb()
        lb.register("a", capacity=1)
        lb.register("b", capacity=1)
        lb.get_node("a").active_tasks = 1  # full
        avail = lb.available_nodes()
        assert len(avail) == 1
        assert avail[0].agent_id == "b"

    def test_tc26_all_nodes(self):
        lb = make_lb()
        lb.register("a"); lb.register("b")
        assert len(lb.all_nodes()) == 2

    def test_tc27_stats(self):
        lb = make_lb()
        lb.register("a"); lb.register("b")
        lb.set_online("b", False)
        st = lb.stats()
        assert st["total_nodes"] == 2
        assert st["online_nodes"] == 1

    def test_tc28_stats_total_handled(self):
        lb = make_lb()
        lb.register("a")
        lb.assign(); lb.assign()
        st = lb.stats()
        assert st["total_handled"] == 2

    def test_tc29_capacity_zero_unavailable(self):
        n = AgentNode(agent_id="a", capacity=0)
        assert not n.is_available()
        assert n.load_ratio() == 1.0

    def test_tc30_round_robin_skips_full(self):
        lb = make_lb(BalancingStrategy.ROUND_ROBIN)
        lb.register("a", capacity=1)
        lb.register("b", capacity=10)
        lb.get_node("a").active_tasks = 1  # a is full
        for _ in range(3):
            n = lb.select()
            assert n.agent_id == "b"

    def test_tc31_weighted_single_node(self):
        lb = make_lb(BalancingStrategy.WEIGHTED)
        lb.register("only", weight=5)
        n = lb.select()
        assert n.agent_id == "only"

    def test_tc32_metadata_preserved(self):
        lb = make_lb()
        lb.register("a", metadata={"region": "us-east"})
        assert lb.get_node("a").metadata["region"] == "us-east"

    def test_tc33_adr_165(self):
        assert ADR_165["id"] == "ADR-165"
        assert ADR_165["status"] == "accepted"
        assert "LoadBalancer" in ADR_165["title"]
