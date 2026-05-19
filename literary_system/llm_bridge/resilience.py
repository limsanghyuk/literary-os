"""
V435 -- ExperimentRegistry + FeatureFlagService + RetryBudgetManager + GracefulDegradation

ExperimentRegistry:   A/B test variant assignment + statistical significance check
FeatureFlagService:   Progressive rollout (5%->100%) + flag evaluation
RetryBudgetManager:   Per-user/global daily+monthly retry limits (CostLedger companion)
GracefulDegradation:  5-tier quality degradation (ADR-010)
"""
from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# ExperimentRegistry -- A/B test
# ---------------------------------------------------------------------------

@dataclass
class Variant:
    name:       str
    weight:     float = 0.5   # traffic fraction [0.0, 1.0]
    metadata:   dict  = field(default_factory=dict)


@dataclass
class Experiment:
    experiment_id: str
    variants:      List[Variant]
    active:        bool  = True
    created_at:    float = field(default_factory=time.time)
    # Assignments: user_id -> variant_name
    _assignments:  Dict[str, str] = field(default_factory=dict, repr=False)
    # Outcomes: variant_name -> list of 1/0 (success/failure)
    _outcomes:     Dict[str, List[int]] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        total = sum(v.weight for v in self.variants)
        if abs(total - 1.0) > 0.01:
            raise ValueError("Variant weights must sum to 1.0, got " + str(total))
        for v in self.variants:
            self._outcomes[v.name] = []

    def assign(self, user_id: str) -> str:
        """Deterministic variant assignment via hash."""
        if user_id in self._assignments:
            return self._assignments[user_id]
        raw = (self.experiment_id + ":" + user_id).encode("utf-8")
        bucket = int(hashlib.md5(raw).hexdigest(), 16) % 1000 / 1000.0
        cumulative = 0.0
        for v in self.variants:
            cumulative += v.weight
            if bucket < cumulative:
                self._assignments[user_id] = v.name
                return v.name
        # Fallback to last variant
        self._assignments[user_id] = self.variants[-1].name
        return self.variants[-1].name

    def record_outcome(self, user_id: str, success: bool) -> None:
        variant = self._assignments.get(user_id)
        if variant and variant in self._outcomes:
            self._outcomes[variant].append(1 if success else 0)

    def is_significant(self, min_samples: int = 30, confidence: float = 0.90) -> bool:
        """
        Simple two-proportion z-test for statistical significance.
        Returns True if difference between variants meets confidence threshold.
        Requires >= 2 variants and min_samples per variant.
        """
        if len(self.variants) < 2:
            return False
        names = [v.name for v in self.variants[:2]]
        outcomes = [self._outcomes.get(n, []) for n in names]
        for o in outcomes:
            if len(o) < min_samples:
                return False
        n1, n2 = len(outcomes[0]), len(outcomes[1])
        p1 = sum(outcomes[0]) / n1
        p2 = sum(outcomes[1]) / n2
        p_pool = (sum(outcomes[0]) + sum(outcomes[1])) / (n1 + n2)
        if p_pool <= 0 or p_pool >= 1:
            return False
        se = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
        if se == 0:
            return False
        z = abs(p1 - p2) / se
        # Bug-Fix: added 99% confidence level (z=2.576); was binary with no 99% support
        if confidence <= 0.90:
            z_threshold = 1.645   # ~90%
        elif confidence <= 0.95:
            z_threshold = 1.96    # ~95%
        else:
            z_threshold = 2.576   # ~99%
        return z >= z_threshold


class ExperimentRegistry:
    """A/B experiment lifecycle management."""

    def __init__(self) -> None:
        self._experiments: Dict[str, Experiment] = {}

    def create(self, experiment_id: str, variants: List[Variant]) -> Experiment:
        if experiment_id in self._experiments:
            raise ValueError("Experiment already exists: " + experiment_id)
        exp = Experiment(experiment_id=experiment_id, variants=variants)
        self._experiments[experiment_id] = exp
        return exp

    def get(self, experiment_id: str) -> Experiment:
        if experiment_id not in self._experiments:
            raise KeyError("Experiment not found: " + experiment_id)
        return self._experiments[experiment_id]

    def assign(self, experiment_id: str, user_id: str) -> str:
        exp = self.get(experiment_id)
        if not exp.active:
            return self._experiments[experiment_id].variants[0].name
        return exp.assign(user_id)

    def stop(self, experiment_id: str) -> None:
        self.get(experiment_id).active = False


# ---------------------------------------------------------------------------
# FeatureFlagService -- progressive rollout
# ---------------------------------------------------------------------------

@dataclass
class FeatureFlag:
    flag_id:        str
    enabled:        bool  = False
    rollout_pct:    float = 0.0    # 0.0 - 100.0
    allow_list:     List[str] = field(default_factory=list)
    deny_list:      List[str] = field(default_factory=list)


class FeatureFlagService:
    """
    Feature flag evaluation with progressive rollout.
    Rollout: deterministic hash-based assignment.
    """

    def __init__(self) -> None:
        self._flags: Dict[str, FeatureFlag] = {}

    def define(self, flag: FeatureFlag) -> None:
        self._flags[flag.flag_id] = flag

    def is_enabled(self, flag_id: str, user_id: str = "") -> bool:
        flag = self._flags.get(flag_id)
        if flag is None or not flag.enabled:
            return False
        if user_id in flag.deny_list:
            return False
        if user_id in flag.allow_list:
            return True
        if flag.rollout_pct >= 100.0:
            return True
        if flag.rollout_pct <= 0.0:
            return False
        # Deterministic bucket assignment
        raw = (flag_id + ":" + user_id).encode("utf-8")
        bucket = int(hashlib.md5(raw).hexdigest(), 16) % 100
        return bucket < flag.rollout_pct

    def set_rollout(self, flag_id: str, pct: float) -> None:
        flag = self._flags.get(flag_id)
        if flag is None:
            raise KeyError("Unknown flag: " + flag_id)
        flag.rollout_pct = max(0.0, min(100.0, pct))


# ---------------------------------------------------------------------------
# RetryBudgetManager
# ---------------------------------------------------------------------------

@dataclass
class RetryBudget:
    budget_id:          str
    daily_limit:        int   = 10
    monthly_limit:      int   = 100
    _daily_used:        int   = field(default=0, repr=False)
    _monthly_used:      int   = field(default=0, repr=False)
    _day_reset_at:      float = field(default_factory=time.time, repr=False)
    _month_reset_at:    float = field(default_factory=time.time, repr=False)

    def _maybe_reset(self) -> None:
        now = time.time()
        if (now - self._day_reset_at) >= 86_400:
            self._daily_used = 0
            self._day_reset_at = now
        if (now - self._month_reset_at) >= (30 * 86_400):
            self._monthly_used = 0
            self._month_reset_at = now

    def can_retry(self) -> bool:
        self._maybe_reset()
        return (
            self._daily_used < self.daily_limit and
            self._monthly_used < self.monthly_limit
        )

    def consume(self) -> bool:
        if not self.can_retry():
            return False
        self._daily_used   += 1
        self._monthly_used += 1
        return True

    def remaining_daily(self) -> int:
        self._maybe_reset()
        return max(0, self.daily_limit - self._daily_used)


class RetryBudgetManager:
    """Per-budget retry limit manager. CostLedger companion (ADR V431)."""

    def __init__(self) -> None:
        self._budgets: Dict[str, RetryBudget] = {}

    def register(self, budget: RetryBudget) -> None:
        self._budgets[budget.budget_id] = budget

    def get(self, budget_id: str) -> RetryBudget:
        if budget_id not in self._budgets:
            raise KeyError("Unknown budget: " + budget_id)
        return self._budgets[budget_id]

    def can_retry(self, budget_id: str) -> bool:
        budget = self._budgets.get(budget_id)
        if budget is None:
            return True   # No budget = unlimited
        return budget.can_retry()

    def consume(self, budget_id: str) -> bool:
        budget = self._budgets.get(budget_id)
        if budget is None:
            return True
        return budget.consume()


# ---------------------------------------------------------------------------
# GracefulDegradation -- 5-tier (ADR-010)
# ---------------------------------------------------------------------------

DEGRADATION_TIERS = [
    "full",         # Tier 0: normal operation
    "cached_only",  # Tier 1: serve only cached responses
    "simplified",   # Tier 2: simplified model (speed only)
    "partial",      # Tier 3: partial functionality
    "minimal",      # Tier 4: minimal fallback only
]


class GracefulDegradation:
    """
    5-tier progressive degradation (ADR-010).

    Tier escalation: automatic on consecutive failures or explicit trigger.
    Tier recovery: automatic after recovery_window (default 300s).
    """

    def __init__(
        self,
        failure_threshold: int   = 3,
        recovery_window:   float = 300.0,
    ) -> None:
        self._tier             = 0
        self._failure_threshold = failure_threshold
        self._recovery_window  = recovery_window
        self._consecutive_failures = 0
        self._last_failure_time: float = 0.0
        self._escalation_history: List[dict] = []

    @property
    def current_tier(self) -> int:
        return self._tier

    @property
    def current_tier_name(self) -> str:
        return DEGRADATION_TIERS[self._tier]

    def record_success(self) -> None:
        """Record success; attempt recovery."""
        self._consecutive_failures = 0
        if self._tier > 0:
            elapsed = time.time() - self._last_failure_time
            if elapsed >= self._recovery_window:
                self._tier = max(0, self._tier - 1)

    def record_failure(self) -> None:
        """Record failure; escalate tier if threshold reached."""
        self._consecutive_failures += 1
        self._last_failure_time = time.time()
        if self._consecutive_failures >= self._failure_threshold:
            self._escalate()
            self._consecutive_failures = 0

    def force_tier(self, tier: int) -> None:
        """Explicit tier override (for testing / manual intervention)."""
        tier = max(0, min(len(DEGRADATION_TIERS) - 1, tier))
        self._escalation_history.append({
            "from": self._tier, "to": tier, "at": time.time(), "reason": "forced"
        })
        self._tier = tier

    def is_degraded(self) -> bool:
        return self._tier > 0

    def can_serve_full(self) -> bool:
        return self._tier == 0

    def _escalate(self) -> None:
        new_tier = min(self._tier + 1, len(DEGRADATION_TIERS) - 1)
        self._escalation_history.append({
            "from": self._tier, "to": new_tier, "at": time.time(), "reason": "auto"
        })
        self._tier = new_tier

    def status(self) -> dict:
        return {
            "tier": self._tier,
            "tier_name": self.current_tier_name,
            "is_degraded": self.is_degraded(),
            "consecutive_failures": self._consecutive_failures,
            "escalations": len(self._escalation_history),
        }
