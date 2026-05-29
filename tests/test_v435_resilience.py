"""
V435 -- ExperimentRegistry + FeatureFlagService + RetryBudgetManager + GracefulDegradation tests
"""
from __future__ import annotations
import time
import pytest

from literary_system.llm_bridge.resilience import (
    Variant, Experiment, ExperimentRegistry,
    FeatureFlag, FeatureFlagService,
    RetryBudget, RetryBudgetManager,
    GracefulDegradation, DEGRADATION_TIERS,
)


# ---------------------------------------------------------------------------
# Experiment + ExperimentRegistry
# ---------------------------------------------------------------------------

class TestExperiment:
    def _make_exp(self):
        return Experiment(
            experiment_id="exp-001",
            variants=[
                Variant("control", weight=0.5),
                Variant("treatment", weight=0.5),
            ],
        )

    def test_invalid_weights_raise(self):
        with pytest.raises(ValueError, match="sum to 1.0"):
            Experiment(
                experiment_id="bad",
                variants=[Variant("a", 0.3), Variant("b", 0.3)],
            )

    def test_assign_deterministic(self):
        exp = self._make_exp()
        v1 = exp.assign("user123")
        v2 = exp.assign("user123")
        assert v1 == v2

    def test_assign_returns_valid_variant(self):
        exp = self._make_exp()
        v = exp.assign("user_abc")
        assert v in {"control", "treatment"}

    def test_assign_distributes(self):
        exp = self._make_exp()
        variants = {exp.assign("user" + str(i)) for i in range(200)}
        assert "control" in variants
        assert "treatment" in variants

    def test_record_outcome(self):
        exp = self._make_exp()
        exp.assign("u1")
        exp.record_outcome("u1", success=True)
        variant = exp._assignments["u1"]
        assert 1 in exp._outcomes[variant]

    def test_not_significant_with_few_samples(self):
        exp = self._make_exp()
        # Only 5 samples -- not significant
        for i in range(5):
            exp.assign("u" + str(i))
            exp.record_outcome("u" + str(i), success=(i % 2 == 0))
        assert exp.is_significant(min_samples=30) is False

    def test_significant_with_clear_winner(self):
        exp = self._make_exp()
        # Force many assignments to control
        control_users = []
        treatment_users = []
        for i in range(500):
            uid = "u" + str(i)
            v = exp.assign(uid)
            if v == "control":
                control_users.append(uid)
            else:
                treatment_users.append(uid)
        # Control 90% success, treatment 10% success
        for uid in control_users:
            exp.record_outcome(uid, success=True)
        for i, uid in enumerate(treatment_users):
            exp.record_outcome(uid, success=(i % 10 == 0))
        assert exp.is_significant(min_samples=30, confidence=0.90) is True


class TestExperimentRegistry:
    def test_create_and_get(self):
        reg = ExperimentRegistry()
        exp = reg.create("e1", [Variant("a", 0.5), Variant("b", 0.5)])
        assert reg.get("e1") is exp

    def test_duplicate_raises(self):
        reg = ExperimentRegistry()
        reg.create("e1", [Variant("a", 1.0)])
        with pytest.raises(ValueError, match="already exists"):
            reg.create("e1", [Variant("a", 1.0)])

    def test_assign_delegates(self):
        reg = ExperimentRegistry()
        reg.create("e1", [Variant("control", 0.5), Variant("treatment", 0.5)])
        v = reg.assign("e1", "user1")
        assert v in {"control", "treatment"}

    def test_stop_returns_first_variant(self):
        reg = ExperimentRegistry()
        reg.create("e1", [Variant("control", 0.5), Variant("treatment", 0.5)])
        reg.stop("e1")
        v = reg.assign("e1", "new_user")
        assert v == "control"


# ---------------------------------------------------------------------------
# FeatureFlagService
# ---------------------------------------------------------------------------

class TestFeatureFlagService:
    def test_disabled_flag(self):
        svc = FeatureFlagService()
        svc.define(FeatureFlag("flag1", enabled=False))
        assert svc.is_enabled("flag1", "user1") is False

    def test_enabled_100pct(self):
        svc = FeatureFlagService()
        svc.define(FeatureFlag("flag1", enabled=True, rollout_pct=100.0))
        assert svc.is_enabled("flag1", "user1") is True
        assert svc.is_enabled("flag1", "user999") is True

    def test_enabled_0pct(self):
        svc = FeatureFlagService()
        svc.define(FeatureFlag("flag1", enabled=True, rollout_pct=0.0))
        assert svc.is_enabled("flag1", "user1") is False

    def test_allow_list(self):
        svc = FeatureFlagService()
        svc.define(FeatureFlag("f", enabled=True, rollout_pct=0.0, allow_list=["admin"]))
        assert svc.is_enabled("f", "admin") is True
        assert svc.is_enabled("f", "regular") is False

    def test_deny_list(self):
        svc = FeatureFlagService()
        svc.define(FeatureFlag("f", enabled=True, rollout_pct=100.0, deny_list=["blocked"]))
        assert svc.is_enabled("f", "blocked") is False
        assert svc.is_enabled("f", "normal") is True

    def test_deterministic_rollout(self):
        svc = FeatureFlagService()
        svc.define(FeatureFlag("f", enabled=True, rollout_pct=50.0))
        results = {svc.is_enabled("f", "u" + str(i)) for i in range(100)}
        assert True in results and False in results

    def test_set_rollout(self):
        svc = FeatureFlagService()
        svc.define(FeatureFlag("f", enabled=True, rollout_pct=5.0))
        svc.set_rollout("f", 100.0)
        assert svc._flags["f"].rollout_pct == 100.0

    def test_set_rollout_unknown_raises(self):
        svc = FeatureFlagService()
        with pytest.raises(KeyError):
            svc.set_rollout("nonexistent", 50.0)

    def test_undefined_flag_returns_false(self):
        svc = FeatureFlagService()
        assert svc.is_enabled("unknown_flag", "user") is False


# ---------------------------------------------------------------------------
# RetryBudgetManager
# ---------------------------------------------------------------------------

class TestRetryBudget:
    def test_can_retry_within_limit(self):
        b = RetryBudget("b1", daily_limit=5, monthly_limit=100)
        assert b.can_retry() is True

    def test_consume_decrements(self):
        b = RetryBudget("b1", daily_limit=3, monthly_limit=100)
        b.consume()
        b.consume()
        assert b.remaining_daily() == 1

    def test_consume_returns_false_when_exhausted(self):
        b = RetryBudget("b1", daily_limit=2, monthly_limit=100)
        b.consume()
        b.consume()
        assert b.consume() is False

    def test_can_retry_false_when_daily_exhausted(self):
        b = RetryBudget("b1", daily_limit=1, monthly_limit=100)
        b.consume()
        assert b.can_retry() is False

    def test_remaining_daily(self):
        b = RetryBudget("b1", daily_limit=10, monthly_limit=100)
        b.consume()
        b.consume()
        b.consume()
        assert b.remaining_daily() == 7


class TestRetryBudgetManager:
    def test_unknown_budget_unlimited(self):
        mgr = RetryBudgetManager()
        assert mgr.can_retry("unknown") is True
        assert mgr.consume("unknown") is True

    def test_registered_budget(self):
        mgr = RetryBudgetManager()
        b = RetryBudget("b1", daily_limit=2, monthly_limit=10)
        mgr.register(b)
        assert mgr.can_retry("b1") is True
        mgr.consume("b1")
        mgr.consume("b1")
        assert mgr.can_retry("b1") is False

    def test_get_budget(self):
        mgr = RetryBudgetManager()
        b = RetryBudget("b1")
        mgr.register(b)
        assert mgr.get("b1") is b

    def test_get_unknown_raises(self):
        mgr = RetryBudgetManager()
        with pytest.raises(KeyError):
            mgr.get("missing")


# ---------------------------------------------------------------------------
# GracefulDegradation
# ---------------------------------------------------------------------------

class TestGracefulDegradation:
    def test_initial_tier_zero(self):
        gd = GracefulDegradation()
        assert gd.current_tier == 0
        assert gd.current_tier_name == "full"
        assert gd.is_degraded() is False

    def test_escalates_after_failures(self):
        gd = GracefulDegradation(failure_threshold=3)
        gd.record_failure()
        gd.record_failure()
        assert gd.current_tier == 0  # not yet
        gd.record_failure()
        assert gd.current_tier == 1
        assert gd.is_degraded() is True

    def test_max_tier_capped_at_4(self):
        gd = GracefulDegradation(failure_threshold=1)
        for _ in range(10):
            gd.record_failure()
        assert gd.current_tier == len(DEGRADATION_TIERS) - 1

    def test_force_tier(self):
        gd = GracefulDegradation()
        gd.force_tier(3)
        assert gd.current_tier == 3
        assert gd.current_tier_name == "partial"

    def test_recovery_after_window(self):
        gd = GracefulDegradation(failure_threshold=1, recovery_window=0.01)
        gd.record_failure()
        assert gd.current_tier == 1
        time.sleep(0.02)
        gd.record_success()
        assert gd.current_tier == 0

    def test_no_recovery_before_window(self):
        gd = GracefulDegradation(failure_threshold=1, recovery_window=9999.0)
        gd.record_failure()
        assert gd.current_tier == 1
        gd.record_success()
        assert gd.current_tier == 1  # not recovered yet

    def test_status_dict(self):
        gd = GracefulDegradation()
        s = gd.status()
        assert "tier" in s
        assert "tier_name" in s
        assert "is_degraded" in s
        assert "escalations" in s

    def test_tier_names_valid(self):
        gd = GracefulDegradation(failure_threshold=1)
        names_seen = set()
        for _ in range(5):
            names_seen.add(gd.current_tier_name)
            gd.record_failure()
        assert names_seen.issubset(set(DEGRADATION_TIERS))

    def test_can_serve_full_only_at_tier0(self):
        gd = GracefulDegradation(failure_threshold=1)
        assert gd.can_serve_full() is True
        gd.record_failure()
        assert gd.can_serve_full() is False
