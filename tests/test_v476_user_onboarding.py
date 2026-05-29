"""
tests/test_v476_user_onboarding.py
V476 — UserOnboarding + BillingEngine 테스트
"""
import pytest
from literary_system.ops.user_onboarding import (
    UserOnboarding, UserPlan, PaymentGateway,
    OnboardResult, Subscription, User,
)


class TestUserOnboarding:
    def test_onboard_basic(self):
        uo = UserOnboarding()
        r = uo.onboard({"email": "test@test.com", "name": "테스터"})
        assert isinstance(r, OnboardResult)
        assert r.user.email == "test@test.com"
        assert r.user is not None

    def test_onboard_generates_user_id(self):
        uo = UserOnboarding()
        r = uo.onboard({"email": "a@b.com", "name": "A"})
        assert r.user.user_id.startswith("usr_")

    def test_onboard_default_plan_free(self):
        uo = UserOnboarding()
        r = uo.onboard({"email": "a@b.com", "name": "A"})
        assert r.user.plan == UserPlan.FREE

    def test_user_count_increments(self):
        uo = UserOnboarding()
        uo.onboard({"email": "a@b.com", "name": "A"})
        uo.onboard({"email": "b@b.com", "name": "B"})
        assert uo.user_count() == 2

    def test_get_user_by_id(self):
        uo = UserOnboarding()
        r = uo.onboard({"email": "x@x.com", "name": "X"})
        found = uo.get_user(r.user.user_id)
        assert found is not None
        assert found.email == "x@x.com"

    def test_get_user_nonexistent_returns_none(self):
        uo = UserOnboarding()
        assert uo.get_user("usr_ghost") is None

    def test_create_subscription_pro(self):
        uo = UserOnboarding()
        r = uo.onboard({"email": "p@p.com", "name": "P"})
        sub = uo.create_subscription(r.user.user_id, UserPlan.PRO, PaymentGateway.STRIPE)
        assert isinstance(sub, Subscription)
        assert sub.active is True
        assert sub.plan == UserPlan.PRO

    def test_create_subscription_enterprise(self):
        uo = UserOnboarding()
        r = uo.onboard({"email": "e@e.com", "name": "E"})
        sub = uo.create_subscription(r.user.user_id, UserPlan.ENTERPRISE, PaymentGateway.TOSS)
        assert sub.active is True
        assert sub.plan == UserPlan.ENTERPRISE

    def test_subscription_price_free(self):
        assert UserOnboarding.PLAN_PRICE[UserPlan.FREE] == pytest.approx(0.0)

    def test_subscription_price_pro(self):
        assert UserOnboarding.PLAN_PRICE[UserPlan.PRO] > 0

    def test_cancel_subscription(self):
        uo = UserOnboarding()
        r = uo.onboard({"email": "c@c.com", "name": "C"})
        sub = uo.create_subscription(r.user.user_id, UserPlan.PRO, PaymentGateway.STRIPE)
        assert uo.cancel_subscription(sub.sub_id) is True
        cancelled = uo.get_subscription(sub.sub_id)
        assert cancelled.active is False

    def test_cancel_nonexistent_subscription(self):
        uo = UserOnboarding()
        assert uo.cancel_subscription("sub_ghost") is False

    def test_onboard_missing_email_raises(self):
        uo = UserOnboarding()
        with pytest.raises((ValueError, KeyError)):
            uo.onboard({"name": "no_email"})

    def test_duplicate_email_raises(self):
        uo = UserOnboarding()
        uo.onboard({"email": "dup@dup.com", "name": "Dup"})
        with pytest.raises(ValueError):
            uo.onboard({"email": "dup@dup.com", "name": "Dup2"})

    def test_payment_gateways_exist(self):
        assert PaymentGateway.STRIPE is not None
        assert PaymentGateway.TOSS is not None
