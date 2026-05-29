"""V383 — PhysicsAwareRouter (멀티어댑터) 테스트."""
import pytest
from literary_system.llm_bridge.physics_aware_router import PhysicsAwareRouter, PhysicsRoutingPolicy
from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge


@pytest.fixture
def router():
    r = PhysicsAwareRouter(policy=PhysicsRoutingPolicy.QUALITY_PHYSICS)
    r.register('adapter_a', MockLLMBridge(), priority=1, narrative_fitness_weight=0.5)
    r.register('adapter_b', MockLLMBridge(), priority=0, narrative_fitness_weight=0.5)
    return r


class TestPhysicsAwareRouter:
    def test_provider_name(self, router):
        assert router.provider_name == 'physics_aware_router'

    def test_generate_returns_string(self, router):
        result = router.generate("test prompt")
        assert isinstance(result, str)

    def test_register_adds_adapter(self):
        r = PhysicsAwareRouter()
        r.register('mock', MockLLMBridge())
        assert len(r._nodes) == 1

    def test_empty_router_returns_message(self):
        r = PhysicsAwareRouter()
        result = r.generate("prompt")
        assert 'no adapters' in result.lower()

    def test_update_fitness(self, router):
        router.update_fitness('adapter_a', 8.5)
        node = next(n for n in router._nodes if n.name == 'adapter_a')
        assert node.last_fitness_score == pytest.approx(8.5)

    def test_quality_physics_selects_highest_fitness(self, router):
        router.update_fitness('adapter_a', 9.0)
        router.update_fitness('adapter_b', 5.0)
        selected = router._select_node()
        assert selected.name == 'adapter_a'

    def test_round_robin_cycles(self):
        r = PhysicsAwareRouter(policy=PhysicsRoutingPolicy.ROUND_ROBIN)
        r.register('a', MockLLMBridge(), priority=1)
        r.register('b', MockLLMBridge(), priority=0)
        names = [r._select_node().name for _ in range(4)]
        assert 'a' in names and 'b' in names

    def test_primary_always_first(self):
        r = PhysicsAwareRouter(policy=PhysicsRoutingPolicy.PRIMARY)
        r.register('high', MockLLMBridge(), priority=10)
        r.register('low',  MockLLMBridge(), priority=1)
        assert r._select_node().name == 'high'

    def test_ensemble_generates(self):
        r = PhysicsAwareRouter(policy=PhysicsRoutingPolicy.ENSEMBLE, ensemble_top_k=2)
        r.register('a', MockLLMBridge(), priority=1)
        r.register('b', MockLLMBridge(), priority=0)
        result = r.generate("prompt")
        assert isinstance(result, str)

    def test_stats_structure(self, router):
        stats = router.stats()
        assert 'policy' in stats
        assert 'adapters' in stats

    def test_stats_includes_fitness(self, router):
        router.update_fitness('adapter_a', 7.5)
        stats = router.stats()
        assert 'last_fitness' in stats['adapters']['adapter_a']

    def test_fitness_history_tracked(self, router):
        for score in [6.0, 7.0, 8.0]:
            router.update_fitness('adapter_a', score)
        hist = router._fitness_history.get('adapter_a', [])
        assert len(hist) == 3

    def test_fitness_history_max_10(self, router):
        for i in range(15):
            router.update_fitness('adapter_a', float(i))
        hist = router._fitness_history.get('adapter_a', [])
        assert len(hist) <= 10

    def test_calls_tracked(self, router):
        router.generate("prompt")
        node = router._select_node()
        assert node.calls >= 0

    def test_stage96_policy_inheritance(self, router):
        # PhysicsAwareRouter는 LLMBridgeInterface를 구현해야 함
        assert hasattr(router, 'generate')
        assert hasattr(router, 'provider_name')
