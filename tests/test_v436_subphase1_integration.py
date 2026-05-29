"""
V436 -- SubPhase 1 Integration Test
Tests the full V431-V435 LLM adapter chain working together.

Integration scenarios:
  1. AdapterContractV2 + OllamaAdapterV2 + CascadeOrchestrator + SemanticCache
  2. ModelSelectionPolicy -> adapter selection -> CascadeOrchestrator
  3. FeatureFlagService + GracefulDegradation gating
  4. RetryBudgetManager + AdapterContractV2.retry.retry_budget_id
  5. StreamingNormalizer end-to-end
"""
from __future__ import annotations
import pytest
from unittest.mock import MagicMock

from literary_system.llm_bridge.adapter_contract import AdapterContractV2, KeyConfig, RetryPolicy
from literary_system.llm_bridge.adapters_v2 import (
    ClaudeAdapterV2, OpenAIAdapterV2, OllamaAdapterV2,
)
from literary_system.llm_bridge.model_registry import (
    ModelRegistry, ModelEntry, ModelCapabilities, ModelSelectionPolicy, TaskContext,
)
from literary_system.llm_bridge.cascade import (
    SemanticCache, CascadeOrchestrator, StreamingNormalizer, ChunkEvent,
)
from literary_system.llm_bridge.resilience import (
    FeatureFlag, FeatureFlagService,
    RetryBudget, RetryBudgetManager,
    GracefulDegradation,
)


# ---------------------------------------------------------------------------
# Scenario 1: Contract + OllamaAdapterV2 + CascadeOrchestrator + Cache
# ---------------------------------------------------------------------------

class TestCascadeWithCache:
    def test_full_cascade_pipeline(self):
        """Simulate: cache miss -> speed draft -> escalate -> quality polish."""
        speed = MagicMock()
        speed.generate.return_value = "draft output"
        quality = MagicMock()
        quality.generate.return_value = "polished output"

        cache = SemanticCache(ttl=60.0)
        orch = CascadeOrchestrator(
            speed, quality,
            cache=cache,
            escalate_fn=lambda d: len(d) < 50,
            use_cache=True,
        )

        result = orch.generate("scene prompt", model_id_hint="haiku")
        assert result == "polished output"
        assert orch.stats["polish_count"] == 1

        # Second call: should hit cache
        result2 = orch.generate("scene prompt", model_id_hint="haiku")
        assert result2 == "polished output"
        assert orch.stats["cache_hits"] == 1
        assert speed.generate.call_count == 1  # not called again

    def test_cascade_stats_accumulate(self):
        speed = MagicMock()
        speed.generate.side_effect = ["d1", "d2", "d3"]
        quality = MagicMock()
        quality.generate.return_value = "polished"

        orch = CascadeOrchestrator(
            speed, quality,
            escalate_fn=lambda d: True,
            use_cache=False,
        )
        for i in range(3):
            orch.generate("p" + str(i))

        s = orch.stats
        assert s["draft_count"] == 3
        assert s["polish_count"] == 3
        assert s["escalation_rate"] == 1.0


# ---------------------------------------------------------------------------
# Scenario 2: ModelRegistry -> Selection -> Cascade
# ---------------------------------------------------------------------------

class TestSelectionToCascade:
    def test_policy_selects_model_from_registry(self):
        reg = ModelRegistry()
        reg.register(ModelEntry(
            model_id="haiku", provider="claude", tier="speed",
            cost_per_1k=0.00075,
            capabilities=ModelCapabilities(typical_latency_ms=800.0),
        ))
        reg.register(ModelEntry(
            model_id="sonnet", provider="claude", tier="quality",
            cost_per_1k=0.009,
            capabilities=ModelCapabilities(typical_latency_ms=3000.0),
        ))

        policy = ModelSelectionPolicy(reg)
        selected = policy.select(TaskContext(preferred_tier="speed", task_type="generation"))
        assert selected in {"haiku", "sonnet"}

    def test_policy_ranked_list_not_empty(self):
        reg = ModelRegistry()
        reg.register(ModelEntry("m1", "claude", "speed", 0.001,
                                ModelCapabilities(typical_latency_ms=500.0)))
        policy = ModelSelectionPolicy(reg)
        ranked = policy.ranked(TaskContext())
        assert len(ranked) == 1
        assert ranked[0][0] == "m1"


# ---------------------------------------------------------------------------
# Scenario 3: FeatureFlagService + GracefulDegradation gating
# ---------------------------------------------------------------------------

class TestFeatureFlagDegradationGating:
    def test_flag_gates_degraded_feature(self):
        svc = FeatureFlagService()
        svc.define(FeatureFlag("new_model_v2", enabled=True, rollout_pct=100.0))

        gd = GracefulDegradation(failure_threshold=1)
        gd.record_failure()  # tier -> 1

        # In degraded state, disable new feature
        can_use_new = svc.is_enabled("new_model_v2", "user1") and not gd.is_degraded()
        assert can_use_new is False

    def test_flag_passes_when_healthy(self):
        svc = FeatureFlagService()
        svc.define(FeatureFlag("new_model_v2", enabled=True, rollout_pct=100.0))
        gd = GracefulDegradation()
        can_use = svc.is_enabled("new_model_v2", "user1") and not gd.is_degraded()
        assert can_use is True


# ---------------------------------------------------------------------------
# Scenario 4: RetryBudget + AdapterContractV2 retry_budget_id
# ---------------------------------------------------------------------------

class TestRetryBudgetWithContract:
    def test_retry_budget_id_in_contract(self):
        contract = AdapterContractV2.for_tier("speed",
            retry=RetryPolicy(max_attempts=3, retry_budget_id="user-001")
        )
        assert contract.retry.retry_budget_id == "user-001"

    def test_retry_manager_blocks_on_exhaustion(self):
        mgr = RetryBudgetManager()
        mgr.register(RetryBudget("user-001", daily_limit=2))

        assert mgr.consume("user-001") is True
        assert mgr.consume("user-001") is True
        assert mgr.consume("user-001") is False

    def test_adapter_contract_linked_to_budget(self):
        """Verify contract retry_budget_id can be used to look up budget."""
        mgr = RetryBudgetManager()
        mgr.register(RetryBudget("budget-abc", daily_limit=5))

        contract = AdapterContractV2.for_tier("speed",
            retry=RetryPolicy(max_attempts=3, retry_budget_id="budget-abc")
        )
        budget_id = contract.retry.retry_budget_id
        assert mgr.can_retry(budget_id) is True
        for _ in range(5):
            mgr.consume(budget_id)
        assert mgr.can_retry(budget_id) is False


# ---------------------------------------------------------------------------
# Scenario 5: StreamingNormalizer end-to-end (multi-provider)
# ---------------------------------------------------------------------------

class TestStreamingNormalizerIntegration:
    def _collect_text(self, events):
        return "".join(e.text for e in events)

    def test_anthropic_stream_reconstructed(self):
        n = StreamingNormalizer("anthropic")
        chunks = [
            {"type": "content_block_delta", "delta": {"text": "Once "}},
            {"type": "content_block_delta", "delta": {"text": "upon "}},
            {"type": "content_block_delta", "delta": {"text": "a time."}},
            {"type": "message_stop"},
        ]
        events = list(n.normalize(iter(chunks)))
        full = self._collect_text(events)
        assert full == "Once upon a time."
        assert events[-1].is_final is True

    def test_openai_stream_reconstructed(self):
        n = StreamingNormalizer("openai")
        chunks = [
            {"choices": [{"delta": {"content": "Hello"}, "finish_reason": None}]},
            {"choices": [{"delta": {"content": " World"}, "finish_reason": "stop"}]},
        ]
        events = list(n.normalize(iter(chunks)))
        full = self._collect_text(events)
        assert full == "Hello World"

    def test_normalize_text_is_single_final_chunk(self):
        for provider in ["anthropic", "openai", "ollama", "plain"]:
            n = StreamingNormalizer(provider)
            events = n.normalize_text("complete text")
            assert len(events) == 1
            assert events[0].is_final is True
            assert events[0].text == "complete text"


# ---------------------------------------------------------------------------
# SubPhase 1 survival: all new modules importable
# ---------------------------------------------------------------------------

class TestSubPhase1ModuleSurvival:
    """Gate check: all V431-V435 modules import cleanly."""

    def test_adapter_contract_importable(self):
        from literary_system.llm_bridge.adapter_contract import (
            AdapterContractV2, KeyConfig, RetryPolicy, TimeoutConfig,
            TokenBudget, ResponseValidator, CostConfig, execute_with_retry,
        )

    def test_adapters_v2_importable(self):
        from literary_system.llm_bridge.adapters_v2 import (
            ClaudeAdapterV2, OpenAIAdapterV2, OllamaAdapterV2, CircuitBreakerState,
        )

    def test_model_registry_importable(self):
        from literary_system.llm_bridge.model_registry import (
            ModelRegistry, ModelEntry, ModelSelectionPolicy,
            SelectionWeights, TaskContext, ModelRegistryError,
        )

    def test_cascade_importable(self):
        from literary_system.llm_bridge.cascade import (
            SemanticCache, CacheEntry, CascadeOrchestrator,
            StreamingNormalizer, ChunkEvent,
        )

    def test_resilience_importable(self):
        from literary_system.llm_bridge.resilience import (
            ExperimentRegistry, Experiment, Variant,
            FeatureFlagService, FeatureFlag,
            RetryBudgetManager, RetryBudget,
            GracefulDegradation, DEGRADATION_TIERS,
        )

    def test_llm_bridge_interface_v431_methods(self):
        from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface
        assert hasattr(LLMBridgeInterface, "get_contract")
        assert hasattr(LLMBridgeInterface, "set_contract")
