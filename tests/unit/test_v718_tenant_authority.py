"""
tests/unit/test_v718_tenant_authority.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
V718 TenantAuthority — 33 TC (ADR-179)

구성:
  TestTenantRegistration    TC01~08  — 등록·조회·목록
  TestTenantLifecycle       TC09~14  — 활성화·비활성화
  TestRoleManagement        TC15~20  — 역할 추가·제거
  TestAccessAuthorization   TC21~29  — 접근 판정 (정상·거부)
  TestEdgeCases             TC30~33  — 경계 조건
"""
import pytest
from unittest.mock import MagicMock

from literary_system.security.tenant_authority import (
    TenantAuthority,
    TenantRecord,
    AccessDecision,
    TenantNotFoundError,
    TenantDisabledError,
    AccessDeniedError,
)


# ──────────────────────────────────────────────
# 공용 픽스처
# ──────────────────────────────────────────────
@pytest.fixture
def auth():
    a = TenantAuthority()
    a.register("tenant_A", "Tenant Alpha", allowed_roles=["writer", "editor"])
    a.register("tenant_B", "Tenant Beta",  allowed_roles=["reader"])
    return a


def _mock_claims(subject="alice", tenant_id="tenant_A", roles=None):
    claims = MagicMock()
    claims.subject = subject
    claims.tenant_id = tenant_id
    claims.roles = roles if roles is not None else ["writer"]
    return claims


# ──────────────────────────────────────────────
# TestTenantRegistration  TC01~08
# ──────────────────────────────────────────────
class TestTenantRegistration:
    def test_tc01_register_returns_record(self):
        auth = TenantAuthority()
        rec = auth.register("t1", "Test", allowed_roles=["writer"])
        assert isinstance(rec, TenantRecord)

    def test_tc02_tenant_id_stored(self, auth):
        rec = auth.get("tenant_A")
        assert rec.tenant_id == "tenant_A"

    def test_tc03_display_name_stored(self, auth):
        rec = auth.get("tenant_A")
        assert rec.display_name == "Tenant Alpha"

    def test_tc04_allowed_roles_stored(self, auth):
        rec = auth.get("tenant_A")
        assert "writer" in rec.allowed_roles
        assert "editor" in rec.allowed_roles

    def test_tc05_get_unknown_tenant_raises(self, auth):
        with pytest.raises(TenantNotFoundError):
            auth.get("unknown_tenant")

    def test_tc06_list_all_returns_all(self, auth):
        tenants = auth.list_all()
        ids = [t.tenant_id for t in tenants]
        assert "tenant_A" in ids
        assert "tenant_B" in ids

    def test_tc07_tenant_count(self, auth):
        assert auth.tenant_count == 2

    def test_tc08_empty_tenant_id_raises(self):
        auth = TenantAuthority()
        with pytest.raises(ValueError):
            auth.register("", "Empty")


# ──────────────────────────────────────────────
# TestTenantLifecycle  TC09~14
# ──────────────────────────────────────────────
class TestTenantLifecycle:
    def test_tc09_new_tenant_active_by_default(self, auth):
        rec = auth.get("tenant_A")
        assert rec.active is True

    def test_tc10_disable_makes_inactive(self, auth):
        auth.disable("tenant_A")
        rec = auth.get("tenant_A")
        assert rec.active is False

    def test_tc11_enable_reactivates(self, auth):
        auth.disable("tenant_A")
        auth.enable("tenant_A")
        rec = auth.get("tenant_A")
        assert rec.active is True

    def test_tc12_disable_unknown_raises(self, auth):
        with pytest.raises(TenantNotFoundError):
            auth.disable("no_such_tenant")

    def test_tc13_enable_unknown_raises(self, auth):
        with pytest.raises(TenantNotFoundError):
            auth.enable("no_such_tenant")

    def test_tc14_disabled_tenant_blocks_authorize(self, auth):
        auth.disable("tenant_A")
        claims = _mock_claims(tenant_id="tenant_A", roles=["writer"])
        decision = auth.authorize(claims, required_role="writer")
        assert decision.granted is False
        assert "disabled" in decision.reason.lower()


# ──────────────────────────────────────────────
# TestRoleManagement  TC15~20
# ──────────────────────────────────────────────
class TestRoleManagement:
    def test_tc15_add_role(self, auth):
        auth.add_role("tenant_A", "admin")
        rec = auth.get("tenant_A")
        assert "admin" in rec.allowed_roles

    def test_tc16_remove_role(self, auth):
        auth.remove_role("tenant_A", "editor")
        rec = auth.get("tenant_A")
        assert "editor" not in rec.allowed_roles

    def test_tc17_remove_nonexistent_role_is_noop(self, auth):
        # removing a role that doesn't exist should not raise
        auth.remove_role("tenant_A", "nonexistent_role")
        rec = auth.get("tenant_A")
        assert "writer" in rec.allowed_roles  # other roles intact

    def test_tc18_is_role_permitted_true(self, auth):
        rec = auth.get("tenant_A")
        assert rec.is_role_permitted("writer") is True

    def test_tc19_is_role_permitted_false(self, auth):
        rec = auth.get("tenant_A")
        assert rec.is_role_permitted("super_admin") is False

    def test_tc20_add_role_unknown_tenant_raises(self, auth):
        with pytest.raises(TenantNotFoundError):
            auth.add_role("ghost_tenant", "writer")


# ──────────────────────────────────────────────
# TestAccessAuthorization  TC21~29
# ──────────────────────────────────────────────
class TestAccessAuthorization:
    def test_tc21_authorize_granted_no_role(self, auth):
        claims = _mock_claims(tenant_id="tenant_A")
        decision = auth.authorize(claims)
        assert decision.granted is True

    def test_tc22_authorize_granted_with_role(self, auth):
        claims = _mock_claims(tenant_id="tenant_A", roles=["writer"])
        decision = auth.authorize(claims, required_role="writer")
        assert decision.granted is True

    def test_tc23_authorize_denied_missing_role_in_token(self, auth):
        claims = _mock_claims(tenant_id="tenant_A", roles=["reader"])
        decision = auth.authorize(claims, required_role="writer")
        assert decision.granted is False

    def test_tc24_authorize_denied_role_not_permitted_for_tenant(self, auth):
        # tenant_B only allows "reader", token claims "reader"
        # but request requires "writer" which tenant_B doesn't allow
        claims = _mock_claims(tenant_id="tenant_B", roles=["writer"])
        decision = auth.authorize(claims, required_role="writer")
        assert decision.granted is False

    def test_tc25_cross_tenant_denied(self, auth):
        claims = _mock_claims(tenant_id="tenant_A")
        decision = auth.authorize(claims, target_tenant_id="tenant_B")
        assert decision.granted is False
        assert "Cross-tenant" in decision.reason

    def test_tc26_unknown_tenant_denied(self, auth):
        claims = _mock_claims(tenant_id="unknown_xyz")
        decision = auth.authorize(claims)
        assert decision.granted is False

    def test_tc27_decision_contains_subject(self, auth):
        claims = _mock_claims(subject="bob", tenant_id="tenant_A")
        decision = auth.authorize(claims)
        assert decision.subject == "bob"

    def test_tc28_authorize_or_raise_success(self, auth):
        claims = _mock_claims(tenant_id="tenant_A", roles=["writer"])
        decision = auth.authorize_or_raise(claims, required_role="writer")
        assert decision.granted is True

    def test_tc29_authorize_or_raise_raises_on_deny(self, auth):
        claims = _mock_claims(tenant_id="tenant_A", roles=[])
        with pytest.raises(AccessDeniedError):
            auth.authorize_or_raise(claims, required_role="writer")


# ──────────────────────────────────────────────
# TestEdgeCases  TC30~33
# ──────────────────────────────────────────────
class TestEdgeCases:
    def test_tc30_access_decision_granted_field(self, auth):
        claims = _mock_claims(tenant_id="tenant_A")
        d = auth.authorize(claims)
        assert isinstance(d, AccessDecision)
        assert d.granted is True

    def test_tc31_register_overwrites_existing(self, auth):
        auth.register("tenant_A", "New Name", allowed_roles=["admin"])
        rec = auth.get("tenant_A")
        assert rec.display_name == "New Name"
        assert "admin" in rec.allowed_roles

    def test_tc32_tags_stored_in_record(self):
        auth = TenantAuthority()
        auth.register("t1", "T1", tags={"env": "prod"})
        rec = auth.get("t1")
        assert rec.tags["env"] == "prod"

    def test_tc33_empty_roles_list_stored(self):
        auth = TenantAuthority()
        auth.register("t1", "T1", allowed_roles=[])
        rec = auth.get("t1")
        assert len(rec.allowed_roles) == 0
