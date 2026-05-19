"""
V433 -- ModelSelectionPolicy + ModelRegistry (ADR-006)

ModelRegistry:
  - register / promote / deprecate / rollback (30-day)
  - drift alarm
  - model metadata (tier, context_limit, cost_per_1k, capabilities)

ModelSelectionPolicy:
  - 6-axis weighted fitness: task / format / context / latency / cost / tier
  - select(task_context) -> model_id
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Model Metadata
# ---------------------------------------------------------------------------

@dataclass
class ModelCapabilities:
    supports_tools:      bool = False
    supports_streaming:  bool = True
    supports_vision:     bool = False
    max_context_tokens:  int  = 8_192
    typical_latency_ms:  float = 2000.0


@dataclass
class ModelEntry:
    model_id:        str
    provider:        str                       # claude / openai / ollama
    tier:            str                       # local / speed / quality
    cost_per_1k:     float = 0.0              # USD per 1K tokens (blended)
    capabilities:    ModelCapabilities = field(default_factory=ModelCapabilities)
    status:          str = "active"           # active / deprecated / experimental
    registered_at:   float = field(default_factory=time.time)
    deprecated_at:   Optional[float] = None
    previous_model:  Optional[str] = None     # for rollback


# ---------------------------------------------------------------------------
# ModelRegistry (ADR-006)
# ---------------------------------------------------------------------------

class ModelRegistryError(Exception):
    pass


class ModelRegistry:
    """
    ADR-006 ModelRegistry.

    Supports:
      - register(entry) -> None
      - promote(model_id, new_tier) -> None
      - deprecate(model_id, successor_id) -> None
      - rollback(model_id) -> str  (returns rolled-back model_id)
      - get(model_id) -> ModelEntry
      - list_active(tier=None) -> List[ModelEntry]
      - check_drift(model_id, latency_ms) -> bool  (True = drift alarm)
    """

    DRIFT_LATENCY_MULTIPLIER = 2.0   # 2x typical = drift alarm

    def __init__(self) -> None:
        self._models: Dict[str, ModelEntry] = {}
        self._deprecation_history: List[dict] = []

    def register(self, entry: ModelEntry) -> None:
        if entry.model_id in self._models:
            raise ModelRegistryError(f"Already registered: {entry.model_id}")
        self._models[entry.model_id] = entry

    def get(self, model_id: str) -> ModelEntry:
        if model_id not in self._models:
            raise ModelRegistryError(f"Unknown model: {model_id}")
        return self._models[model_id]

    def promote(self, model_id: str, new_tier: str) -> None:
        entry = self.get(model_id)
        entry.tier = new_tier

    def deprecate(self, model_id: str, successor_id: str) -> None:
        entry = self.get(model_id)
        successor = self.get(successor_id)  # validate successor exists
        entry.status = "deprecated"
        entry.deprecated_at = time.time()
        # Link successor's previous for rollback
        successor.previous_model = model_id
        self._deprecation_history.append({
            "deprecated":  model_id,
            "successor":   successor_id,
            "at":          entry.deprecated_at,
        })

    def rollback(self, model_id: str) -> str:
        """
        Rollback to previous model (within 30-day window).
        Returns restored model_id.
        """
        entry = self.get(model_id)
        if entry.previous_model is None:
            raise ModelRegistryError(f"No rollback target for: {model_id}")
        prev_id = entry.previous_model
        prev = self.get(prev_id)

        # 30-day window check
        if prev.deprecated_at is not None:
            elapsed_days = (time.time() - prev.deprecated_at) / 86_400
            if elapsed_days > 30:
                raise ModelRegistryError(
                    f"Rollback window expired ({elapsed_days:.1f}d > 30d)"
                )

        prev.status = "active"
        prev.deprecated_at = None
        return prev_id

    def list_active(self, tier: Optional[str] = None) -> List[ModelEntry]:
        entries = [e for e in self._models.values() if e.status == "active"]
        if tier:
            entries = [e for e in entries if e.tier == tier]
        return entries

    def check_drift(self, model_id: str, observed_latency_ms: float) -> bool:
        """
        Return True if observed latency is >= 2x typical (drift alarm).
        """
        entry = self.get(model_id)
        threshold = entry.capabilities.typical_latency_ms * self.DRIFT_LATENCY_MULTIPLIER
        return observed_latency_ms >= threshold


# ---------------------------------------------------------------------------
# ModelSelectionPolicy (6-axis fitness)
# ---------------------------------------------------------------------------

@dataclass
class SelectionWeights:
    """
    6-axis fitness weights. Must sum to 1.0 (enforced on construction).
    """
    task:     float = 0.25   # how well model handles task type
    format:   float = 0.20   # structured / prose / code output format fit
    context:  float = 0.20   # context window adequacy
    latency:  float = 0.15   # latency requirements
    cost:     float = 0.10   # cost efficiency
    tier:     float = 0.10   # requested tier match

    def __post_init__(self) -> None:
        total = self.task + self.format + self.context + self.latency + self.cost + self.tier
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total:.3f}")


@dataclass
class TaskContext:
    """
    Input context for model selection.
    """
    task_type:       str   = "generation"    # generation / analysis / coding / qa
    output_format:   str   = "prose"         # prose / structured / code
    input_tokens:    int   = 1000
    max_latency_ms:  float = 5000.0
    max_cost_usd:    float = 0.01
    preferred_tier:  str   = "speed"


class ModelSelectionPolicy:
    """
    6-axis weighted fitness model selection.

    Usage:
        policy = ModelSelectionPolicy(registry, weights)
        model_id = policy.select(task_context)
    """

    # Task type -> tier affinity scores
    _TASK_TIER_AFFINITY: Dict[str, Dict[str, float]] = {
        "generation": {"quality": 0.9, "speed": 0.7, "local": 0.4},
        "analysis":   {"quality": 0.8, "speed": 0.6, "local": 0.3},
        "coding":     {"quality": 0.7, "speed": 0.6, "local": 0.5},
        "qa":         {"quality": 0.6, "speed": 0.8, "local": 0.6},
    }

    # Output format -> tier affinity scores
    _FORMAT_TIER_AFFINITY: Dict[str, Dict[str, float]] = {
        "prose":      {"quality": 0.9, "speed": 0.7, "local": 0.5},
        "structured": {"quality": 0.7, "speed": 0.8, "local": 0.6},
        "code":       {"quality": 0.6, "speed": 0.7, "local": 0.7},
    }

    def __init__(
        self,
        registry: ModelRegistry,
        weights: Optional[SelectionWeights] = None,
    ) -> None:
        self._registry = registry
        self._weights  = weights or SelectionWeights()

    def score(self, entry: ModelEntry, ctx: TaskContext) -> float:
        """
        Compute weighted fitness score [0.0, 1.0] for a model entry.
        """
        w = self._weights

        # 1. Task axis
        affinity = self._TASK_TIER_AFFINITY.get(ctx.task_type, {})
        task_score = affinity.get(entry.tier, 0.5)

        # 2. Format axis
        fmt_affinity = self._FORMAT_TIER_AFFINITY.get(ctx.output_format, {})
        format_score = fmt_affinity.get(entry.tier, 0.5)

        # 3. Context axis: does model context window fit input?
        ctx_limit = entry.capabilities.max_context_tokens
        context_score = 1.0 if ctx.input_tokens <= ctx_limit * 0.8 else max(
            0.0, 1.0 - (ctx.input_tokens - ctx_limit * 0.8) / ctx_limit
        )

        # 4. Latency axis: typical latency vs requirement
        lat = entry.capabilities.typical_latency_ms
        latency_score = 1.0 if lat <= ctx.max_latency_ms else max(
            0.0, 1.0 - (lat - ctx.max_latency_ms) / ctx.max_latency_ms
        )

        # 5. Cost axis: per-1k cost vs budget (normalize to 0.05 USD/1K ceiling)
        # Bug-Fix: comment said "10 USD/1K ceiling" but code used 0.05 — comment corrected
        cost_norm = min(entry.cost_per_1k / 0.05, 1.0)  # 0.05 USD/1K = ceiling
        cost_score = 1.0 - cost_norm  # lower cost = higher score

        # 6. Tier axis: preferred tier match
        tier_score = 1.0 if entry.tier == ctx.preferred_tier else 0.3

        return (
            w.task    * task_score    +
            w.format  * format_score  +
            w.context * context_score +
            w.latency * latency_score +
            w.cost    * cost_score    +
            w.tier    * tier_score
        )

    def select(self, ctx: TaskContext) -> str:
        """
        Return model_id of highest-fitness active model.
        Raises ModelRegistryError if no active models.
        """
        candidates = self._registry.list_active()
        if not candidates:
            raise ModelRegistryError("No active models in registry")

        best = max(candidates, key=lambda e: self.score(e, ctx))
        return best.model_id

    def ranked(self, ctx: TaskContext) -> List[tuple]:
        """
        Return [(model_id, score), ...] sorted descending by score.
        """
        candidates = self._registry.list_active()
        scored = [(e.model_id, self.score(e, ctx)) for e in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
