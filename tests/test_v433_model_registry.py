"""
V433 -- ModelRegistry + ModelSelectionPolicy tests (ADR-006)
"""
from __future__ import annotations
import time
import pytest

from literary_system.llm_bridge.model_registry import (
    ModelEntry, ModelCapabilities, ModelRegistry, ModelRegistryError,
    ModelSelectionPolicy, SelectionWeights, TaskContext,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_registry() -> ModelRegistry:
    reg = ModelRegistry()
    reg.register(ModelEntry(
        model_id="claude-haiku-4-5",
        provider="claude",
        tier="speed",
        cost_per_1k=0.00075,
        capabilities=ModelCapabilities(
            supports_tools=True, max_context_tokens=200_000, typical_latency_ms=800.0,
        ),
    ))
    reg.register(ModelEntry(
        model_id="claude-sonnet-4-6",
        provider="claude",
        tier="quality",
        cost_per_1k=0.009,
        capabilities=ModelCapabilities(
            supports_tools=True, max_context_tokens=200_000, typical_latency_ms=3000.0,
        ),
    ))
    reg.register(ModelEntry(
        model_id="llama3.2-local",
        provider="ollama",
        tier="local",
        cost_per_1k=0.0,
        capabilities=ModelCapabilities(
            supports_tools=False, max_context_tokens=8_192, typical_latency_ms=5000.0,
        ),
    ))
    return reg


# ---------------------------------------------------------------------------
# ModelRegistry tests
# ---------------------------------------------------------------------------

class TestModelRegistry:
    def test_register_and_get(self):
        reg = make_registry()
        entry = reg.get("claude-haiku-4-5")
        assert entry.model_id == "claude-haiku-4-5"
        assert entry.tier == "speed"

    def test_register_duplicate_raises(self):
        reg = make_registry()
        with pytest.raises(ModelRegistryError, match="Already registered"):
            reg.register(ModelEntry(model_id="claude-haiku-4-5", provider="claude", tier="speed"))

    def test_get_unknown_raises(self):
        reg = make_registry()
        with pytest.raises(ModelRegistryError, match="Unknown model"):
            reg.get("nonexistent-model")

    def test_promote_changes_tier(self):
        reg = make_registry()
        reg.promote("claude-haiku-4-5", "quality")
        assert reg.get("claude-haiku-4-5").tier == "quality"

    def test_deprecate(self):
        reg = make_registry()
        reg.deprecate("claude-haiku-4-5", "claude-sonnet-4-6")
        entry = reg.get("claude-haiku-4-5")
        assert entry.status == "deprecated"
        assert entry.deprecated_at is not None

    def test_deprecate_links_successor(self):
        reg = make_registry()
        reg.deprecate("claude-haiku-4-5", "claude-sonnet-4-6")
        successor = reg.get("claude-sonnet-4-6")
        assert successor.previous_model == "claude-haiku-4-5"

    def test_rollback_restores_model(self):
        reg = make_registry()
        reg.deprecate("claude-haiku-4-5", "claude-sonnet-4-6")
        restored = reg.rollback("claude-sonnet-4-6")
        assert restored == "claude-haiku-4-5"
        assert reg.get("claude-haiku-4-5").status == "active"

    def test_rollback_no_previous_raises(self):
        reg = make_registry()
        with pytest.raises(ModelRegistryError, match="No rollback target"):
            reg.rollback("claude-haiku-4-5")

    def test_rollback_expired_window(self):
        reg = make_registry()
        reg.deprecate("claude-haiku-4-5", "claude-sonnet-4-6")
        # Manually set deprecated_at to 31 days ago
        entry = reg.get("claude-haiku-4-5")
        entry.deprecated_at = time.time() - (31 * 86_400)
        with pytest.raises(ModelRegistryError, match="window expired"):
            reg.rollback("claude-sonnet-4-6")

    def test_list_active_all(self):
        reg = make_registry()
        active = reg.list_active()
        assert len(active) == 3
        assert all(e.status == "active" for e in active)

    def test_list_active_by_tier(self):
        reg = make_registry()
        speed = reg.list_active(tier="speed")
        assert len(speed) == 1
        assert speed[0].model_id == "claude-haiku-4-5"

    def test_list_active_excludes_deprecated(self):
        reg = make_registry()
        reg.deprecate("claude-haiku-4-5", "claude-sonnet-4-6")
        active = reg.list_active()
        ids = [e.model_id for e in active]
        assert "claude-haiku-4-5" not in ids

    def test_check_drift_false_normal(self):
        reg = make_registry()
        # typical_latency_ms=800, threshold=1600
        assert reg.check_drift("claude-haiku-4-5", 1000.0) is False

    def test_check_drift_true_alarm(self):
        reg = make_registry()
        # 800 * 2.0 = 1600 threshold
        assert reg.check_drift("claude-haiku-4-5", 1600.0) is True
        assert reg.check_drift("claude-haiku-4-5", 2000.0) is True

    def test_deprecation_history_recorded(self):
        reg = make_registry()
        reg.deprecate("claude-haiku-4-5", "claude-sonnet-4-6")
        assert len(reg._deprecation_history) == 1
        assert reg._deprecation_history[0]["deprecated"] == "claude-haiku-4-5"


# ---------------------------------------------------------------------------
# SelectionWeights tests
# ---------------------------------------------------------------------------

class TestSelectionWeights:
    def test_valid_weights(self):
        w = SelectionWeights(task=0.25, format=0.20, context=0.20,
                             latency=0.15, cost=0.10, tier=0.10)
        assert abs(w.task + w.format + w.context + w.latency + w.cost + w.tier - 1.0) < 0.001

    def test_invalid_weights_raises(self):
        with pytest.raises(ValueError, match="sum to 1.0"):
            SelectionWeights(task=0.5, format=0.5, context=0.5,
                             latency=0.0, cost=0.0, tier=0.0)


# ---------------------------------------------------------------------------
# ModelSelectionPolicy tests
# ---------------------------------------------------------------------------

class TestModelSelectionPolicy:
    def test_select_returns_model_id(self):
        reg = make_registry()
        policy = ModelSelectionPolicy(reg)
        ctx = TaskContext(task_type="generation", output_format="prose",
                          preferred_tier="speed")
        model_id = policy.select(ctx)
        assert model_id in ["claude-haiku-4-5", "claude-sonnet-4-6", "llama3.2-local"]

    def test_select_prefers_speed_tier(self):
        reg = make_registry()
        # Heavy weight on tier axis
        weights = SelectionWeights(task=0.1, format=0.1, context=0.1,
                                   latency=0.1, cost=0.1, tier=0.5)
        policy = ModelSelectionPolicy(reg, weights)
        ctx = TaskContext(preferred_tier="speed")
        model_id = policy.select(ctx)
        assert model_id == "claude-haiku-4-5"

    def test_select_prefers_quality_tier(self):
        reg = make_registry()
        weights = SelectionWeights(task=0.1, format=0.1, context=0.1,
                                   latency=0.1, cost=0.1, tier=0.5)
        policy = ModelSelectionPolicy(reg, weights)
        ctx = TaskContext(preferred_tier="quality")
        model_id = policy.select(ctx)
        assert model_id == "claude-sonnet-4-6"

    def test_select_raises_with_no_active_models(self):
        reg = ModelRegistry()
        policy = ModelSelectionPolicy(reg)
        with pytest.raises(ModelRegistryError, match="No active models"):
            policy.select(TaskContext())

    def test_ranked_returns_sorted_list(self):
        reg = make_registry()
        policy = ModelSelectionPolicy(reg)
        ctx = TaskContext(preferred_tier="speed")
        ranked = policy.ranked(ctx)
        assert len(ranked) == 3
        # Verify descending order
        scores = [s for _, s in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_score_between_0_and_1(self):
        reg = make_registry()
        policy = ModelSelectionPolicy(reg)
        ctx = TaskContext()
        for entry in reg.list_active():
            s = policy.score(entry, ctx)
            assert 0.0 <= s <= 1.0, f"{entry.model_id}: score {s} out of range"

    def test_local_favored_when_cost_weight_high(self):
        reg = make_registry()
        weights = SelectionWeights(task=0.05, format=0.05, context=0.05,
                                   latency=0.05, cost=0.75, tier=0.05)
        policy = ModelSelectionPolicy(reg, weights)
        ctx = TaskContext(preferred_tier="local")
        model_id = policy.select(ctx)
        # llama3.2-local has 0.0 cost_per_1k -> highest cost_score
        assert model_id == "llama3.2-local"

    def test_context_penalty_for_large_input(self):
        reg = ModelRegistry()
        reg.register(ModelEntry(
            model_id="small-ctx-model",
            provider="test",
            tier="speed",
            cost_per_1k=0.001,
            capabilities=ModelCapabilities(max_context_tokens=1000, typical_latency_ms=500.0),
        ))
        reg.register(ModelEntry(
            model_id="large-ctx-model",
            provider="test",
            tier="speed",
            cost_per_1k=0.002,
            capabilities=ModelCapabilities(max_context_tokens=100_000, typical_latency_ms=500.0),
        ))
        weights = SelectionWeights(task=0.1, format=0.1, context=0.6,
                                   latency=0.05, cost=0.05, tier=0.1)
        policy = ModelSelectionPolicy(reg, weights)
        ctx = TaskContext(input_tokens=50_000, preferred_tier="speed")
        model_id = policy.select(ctx)
        assert model_id == "large-ctx-model"
