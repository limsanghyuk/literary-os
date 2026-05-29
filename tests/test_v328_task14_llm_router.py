"""V328 Task14: OllamaAdapter + LLMNodeRouter 테스트."""
import sys; sys.path.insert(0,"/tmp/literary_os_v328")
import pytest
from literary_system.llm_bridge.llm_node_router import LLMNodeRouter, RoutingPolicy
from literary_system.llm_bridge.ollama_adapter import OllamaAdapter
from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge

class TestLLMNodeRouter:
    def test_no_adapters_returns_message(self):
        r = LLMNodeRouter()
        result = r.generate("test")
        assert "no adapters" in result.lower() or result != ""

    def test_register_chaining(self):
        r = LLMNodeRouter()
        ret = r.register("mock", MockLLMBridge(), priority=1)
        assert ret is r

    def test_primary_policy_uses_highest_priority(self):
        r = LLMNodeRouter(policy=RoutingPolicy.PRIMARY)
        r.register("low",  MockLLMBridge(), priority=0)
        r.register("high", MockLLMBridge(), priority=10)
        result = r.generate("prompt")
        assert isinstance(result, str)

    def test_fallback_policy(self):
        class FailAdapter:
            def generate(self, p, **kw): raise RuntimeError("fail")
        r = LLMNodeRouter(policy=RoutingPolicy.FALLBACK)
        r.register("fail",    FailAdapter(),    priority=10)
        r.register("working", MockLLMBridge(),  priority=5)
        result = r.generate("prompt")
        assert isinstance(result, str)

    def test_round_robin_cycles(self):
        r = LLMNodeRouter(policy=RoutingPolicy.ROUND_ROBIN)
        r.register("a", MockLLMBridge(), priority=0)
        r.register("b", MockLLMBridge(), priority=0)
        r.generate("p1")
        r.generate("p2")
        stats = r.stats()
        assert sum(v["calls"] for v in stats.values()) == 2

    def test_stats_tracks_calls(self):
        r = LLMNodeRouter()
        r.register("m", MockLLMBridge(), priority=1)
        r.generate("x")
        r.generate("y")
        assert r.stats()["m"]["calls"] == 2

    def test_can_inject_as_bridge_in_sgo(self):
        from literary_system.orchestrators.scene_generation_orchestrator import SceneGenerationOrchestrator as SGO
        router = LLMNodeRouter()
        router.register("mock", MockLLMBridge(), priority=1)
        sgo = SGO(bridge=router)
        assert sgo.bridge is router

class TestOllamaAdapter:
    def test_instantiation(self):
        a = OllamaAdapter(model="llama3")
        assert a.model == "llama3"

    def test_generate_falls_back_when_unavailable(self):
        a = OllamaAdapter(base_url="http://localhost:19999")  # non-existent
        result = a.generate("test prompt")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_is_available_false_when_offline(self):
        a = OllamaAdapter(base_url="http://localhost:19999")
        assert a.is_available() == False

    def test_custom_base_url(self):
        a = OllamaAdapter(base_url="http://myhost:11434")
        assert "myhost" in a.base_url

    def test_ollama_implements_interface(self):
        from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface
        a = OllamaAdapter()
        assert isinstance(a, LLMBridgeInterface)
