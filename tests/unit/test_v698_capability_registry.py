"""test_v698_capability_registry.py — V698 AgentCapabilityRegistry 단위 테스트 TC01~TC33"""
from __future__ import annotations
import time, pytest
from literary_system.agents.capability_registry import (
    AgentCapability, AgentProfile, AgentCapabilityRegistry, ADR_160
)

def cap(name, tags=None):
    return AgentCapability(name=name, description=f"{name} desc", tags=tags or [])

def make_registry():
    return AgentCapabilityRegistry(heartbeat_timeout_seconds=0.5)

class TestAgentCapability:
    def test_tc01_creation(self):
        c = cap("scene_write")
        assert c.name == "scene_write"
        assert c.max_concurrent == 1

    def test_tc02_to_dict(self):
        c = cap("critique", tags=["sp-d2"])
        d = c.to_dict()
        assert d["name"] == "critique"
        assert "sp-d2" in d["tags"]

    def test_tc03_version(self):
        c = AgentCapability(name="x", version="2.0")
        assert c.version == "2.0"

class TestAgentProfile:
    def test_tc04_has_capability(self):
        p = AgentProfile(agent_id="a", capabilities=[cap("write"), cap("critique")])
        assert p.has_capability("write") is True
        assert p.has_capability("missing") is False

    def test_tc05_capability_names(self):
        p = AgentProfile(agent_id="a", capabilities=[cap("write"), cap("edit")])
        assert p.capability_names() == {"write", "edit"}

    def test_tc06_get_capability(self):
        c = cap("write")
        p = AgentProfile(agent_id="a", capabilities=[c])
        assert p.get_capability("write") is c
        assert p.get_capability("missing") is None

    def test_tc07_heartbeat_update(self):
        p = AgentProfile(agent_id="a")
        before = p.last_heartbeat
        time.sleep(0.01)
        p.update_heartbeat()
        assert p.last_heartbeat > before

    def test_tc08_to_dict(self):
        p = AgentProfile(agent_id="a", capabilities=[cap("write")])
        d = p.to_dict()
        assert d["agent_id"] == "a"
        assert len(d["capabilities"]) == 1

class TestAgentCapabilityRegistry:
    def setup_method(self):
        self.reg = make_registry()

    def test_tc09_register(self):
        self.reg.register("agent_a", [cap("write")])
        assert self.reg.agent_count() == 1

    def test_tc10_get_agent(self):
        self.reg.register("agent_a", [cap("write")])
        p = self.reg.get_agent("agent_a")
        assert p is not None
        assert p.agent_id == "agent_a"

    def test_tc11_deregister(self):
        self.reg.register("agent_a", [cap("write")])
        assert self.reg.deregister("agent_a") is True
        assert self.reg.get_agent("agent_a") is None

    def test_tc12_deregister_missing(self):
        assert self.reg.deregister("ghost") is False

    def test_tc13_agents_with_capability(self):
        self.reg.register("a1", [cap("write"), cap("critique")])
        self.reg.register("a2", [cap("critique")])
        self.reg.register("a3", [cap("edit")])
        critics = self.reg.agents_with_capability("critique")
        assert len(critics) == 2

    def test_tc14_active_agents(self):
        self.reg.register("a1", [cap("write")])
        self.reg.register("a2", [cap("edit")])
        assert self.reg.active_count() == 2

    def test_tc15_all_capabilities(self):
        self.reg.register("a1", [cap("write"), cap("critique")])
        self.reg.register("a2", [cap("edit")])
        caps = self.reg.all_capabilities()
        assert caps == {"write", "critique", "edit"}

    def test_tc16_heartbeat(self):
        self.reg.register("a1", [cap("write")])
        assert self.reg.heartbeat("a1") is True

    def test_tc17_heartbeat_missing_agent(self):
        assert self.reg.heartbeat("ghost") is False

    def test_tc18_health_check_alive(self):
        self.reg.register("a1", [cap("write")])
        health = self.reg.check_health()
        assert health["a1"] is True

    def test_tc19_health_check_timeout(self):
        self.reg.register("a1", [cap("write")])
        time.sleep(0.6)  # heartbeat_timeout=0.5
        health = self.reg.check_health()
        assert health["a1"] is False

    def test_tc20_register_updates_existing(self):
        self.reg.register("a1", [cap("write")])
        self.reg.register("a1", [cap("write"), cap("edit")])
        assert len(self.reg.get_agent("a1").capabilities) == 2

    def test_tc21_stats(self):
        self.reg.register("a1", [cap("write")])
        self.reg.register("a2", [cap("critique")])
        s = self.reg.stats()
        assert s["total"] == 2
        assert s["active"] == 2
        assert s["capabilities"] == 2

    def test_tc22_agents_with_inactive_excluded(self):
        self.reg.register("a1", [cap("write")])
        self.reg.register("a2", [cap("write")])
        time.sleep(0.6)  # a1 timeout
        self.reg.heartbeat("a2")  # a2 갱신
        self.reg.check_health()
        writers = self.reg.agents_with_capability("write")
        ids = [p.agent_id for p in writers]
        assert "a2" in ids
        assert "a1" not in ids

    def test_tc23_metadata(self):
        self.reg.register("a1", [cap("write")], metadata={"region": "us-east"})
        p = self.reg.get_agent("a1")
        assert p.metadata["region"] == "us-east"

    def test_tc24_all_agents(self):
        self.reg.register("a1", [cap("write")])
        self.reg.register("a2", [cap("edit")])
        assert len(self.reg.all_agents()) == 2

    def test_tc25_capability_max_concurrent(self):
        c = AgentCapability(name="heavy", max_concurrent=5)
        assert c.max_concurrent == 5

    def test_tc26_capability_avg_latency(self):
        c = AgentCapability(name="slow", avg_latency_ms=250.0)
        assert c.avg_latency_ms == 250.0

    def test_tc27_no_agents_for_capability(self):
        result = self.reg.agents_with_capability("nonexistent")
        assert result == []

    def test_tc28_multiple_capabilities_same_agent(self):
        caps = [cap(f"skill_{i}") for i in range(5)]
        self.reg.register("multi", caps)
        assert len(self.reg.get_agent("multi").capabilities) == 5

    def test_tc29_active_count_after_deregister(self):
        self.reg.register("a1", [cap("w")])
        self.reg.register("a2", [cap("w")])
        self.reg.deregister("a1")
        assert self.reg.active_count() == 1

    def test_tc30_heartbeat_reactivates(self):
        self.reg.register("a1", [cap("w")])
        # 수동으로 비활성화
        self.reg.get_agent("a1").active = False
        self.reg.heartbeat("a1")
        assert self.reg.get_agent("a1").active is True

    def test_tc31_registered_at_set(self):
        before = time.time()
        self.reg.register("a1", [cap("w")])
        after = time.time()
        p = self.reg.get_agent("a1")
        assert before <= p.registered_at <= after

    def test_tc32_empty_registry(self):
        assert self.reg.agent_count() == 0
        assert self.reg.all_capabilities() == set()
        assert self.reg.active_agents() == []

    def test_tc33_adr_160(self):
        assert ADR_160["id"] == "ADR-160"
        assert "AgentCapabilityRegistry" in ADR_160["decision"]
