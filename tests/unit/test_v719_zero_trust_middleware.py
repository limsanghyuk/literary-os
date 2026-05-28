"""
tests/unit/test_v719_zero_trust_middleware.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
V719 ZeroTrustMiddleware — 33 TC (ADR-180)

구성:
  TestRequestParsing          TC01~05  — Bearer 토큰 추출
  TestPassFlow                TC06~12  — 정상 통과 시나리오
  TestDenyFlow                TC13~22  — 거부 시나리오
  TestAuditLog                TC23~28  — 감사 로그
  TestHooks                   TC29~33  — 이벤트 훅
"""
import pytest
from literary_system.security import (
    ZeroTrustTokenService, TenantAuthority,
    ZeroTrustMiddleware, ZTRequest, ZTResponse, ZeroTrustAuditEntry,
)


# ──────────────────────────────────────────────
# 픽스처
# ──────────────────────────────────────────────
SECRET = b"test-secret-32bytes-padded-12345"

@pytest.fixture
def svc():
    return ZeroTrustTokenService(secret_key=SECRET)

@pytest.fixture
def authority():
    a = TenantAuthority()
    a.register("tenant_A", "Alpha", allowed_roles=["writer", "editor"])
    return a

@pytest.fixture
def mw(svc, authority):
    return ZeroTrustMiddleware(svc, authority, required_role="writer")

def make_request(token=None, path="/api/scene", rid="req-001"):
    auth_header = f"Bearer {token}" if token else None
    return ZTRequest(request_id=rid, authorization=auth_header, path=path)


# ──────────────────────────────────────────────
# TestRequestParsing  TC01~05
# ──────────────────────────────────────────────
class TestRequestParsing:
    def test_tc01_bearer_extracted_from_authorization(self, svc):
        tok = svc.issue("alice", "tenant_A")
        req = ZTRequest(request_id="r1", authorization=f"Bearer {tok}")
        assert req.bearer_token() == tok

    def test_tc02_no_authorization_returns_none(self):
        req = ZTRequest(request_id="r2")
        assert req.bearer_token() is None

    def test_tc03_bearer_in_headers_dict(self, svc):
        tok = svc.issue("alice", "tenant_A")
        req = ZTRequest(request_id="r3", headers={"Authorization": f"Bearer {tok}"})
        assert req.bearer_token() == tok

    def test_tc04_non_bearer_scheme_returns_none(self):
        req = ZTRequest(request_id="r4", authorization="Basic dXNlcjpwYXNz")
        assert req.bearer_token() is None

    def test_tc05_path_stored(self):
        req = ZTRequest(request_id="r5", path="/api/episode")
        assert req.path == "/api/episode"


# ──────────────────────────────────────────────
# TestPassFlow  TC06~12
# ──────────────────────────────────────────────
class TestPassFlow:
    def test_tc06_valid_token_passes(self, mw, svc):
        tok = svc.issue("alice", "tenant_A", roles=["writer"])
        resp = mw.process(make_request(tok))
        assert resp.allowed is True

    def test_tc07_status_200_on_pass(self, mw, svc):
        tok = svc.issue("alice", "tenant_A", roles=["writer"])
        resp = mw.process(make_request(tok))
        assert resp.status_code == 200

    def test_tc08_claims_attached_on_pass(self, mw, svc):
        tok = svc.issue("bob", "tenant_A", roles=["writer"])
        resp = mw.process(make_request(tok))
        assert resp.claims is not None
        assert resp.claims.subject == "bob"

    def test_tc09_decision_attached_on_pass(self, mw, svc):
        tok = svc.issue("alice", "tenant_A", roles=["writer"])
        resp = mw.process(make_request(tok))
        assert resp.decision is not None
        assert resp.decision.granted is True

    def test_tc10_no_role_check_when_required_role_none(self, svc, authority):
        mw_no_role = ZeroTrustMiddleware(svc, authority, required_role=None)
        tok = svc.issue("alice", "tenant_A", roles=[])
        resp = mw_no_role.process(make_request(tok))
        assert resp.allowed is True

    def test_tc11_editor_role_passes_when_required_editor(self, svc, authority):
        mw_ed = ZeroTrustMiddleware(svc, authority, required_role="editor")
        tok = svc.issue("alice", "tenant_A", roles=["editor"])
        resp = mw_ed.process(make_request(tok))
        assert resp.allowed is True

    def test_tc12_response_reason_ok_on_pass(self, mw, svc):
        tok = svc.issue("alice", "tenant_A", roles=["writer"])
        resp = mw.process(make_request(tok))
        assert resp.reason == "OK"


# ──────────────────────────────────────────────
# TestDenyFlow  TC13~22
# ──────────────────────────────────────────────
class TestDenyFlow:
    def test_tc13_missing_token_401(self, mw):
        resp = mw.process(ZTRequest(request_id="r-noauth", path="/"))
        assert resp.allowed is False
        assert resp.status_code == 401

    def test_tc14_expired_token_401(self, mw, svc):
        tok = svc.issue("alice", "tenant_A", ttl=-1)
        resp = mw.process(make_request(tok))
        assert resp.allowed is False
        assert resp.status_code == 401

    def test_tc15_tampered_token_401(self, mw):
        resp = mw.process(make_request("header.payload.BADSIG"))
        assert resp.allowed is False
        assert resp.status_code == 401

    def test_tc16_missing_role_403(self, mw, svc):
        tok = svc.issue("alice", "tenant_A", roles=[])  # no writer role
        resp = mw.process(make_request(tok))
        assert resp.allowed is False
        assert resp.status_code == 403

    def test_tc17_unknown_tenant_403(self, mw, svc):
        tok = svc.issue("alice", "unknown_tenant", roles=["writer"])
        resp = mw.process(make_request(tok))
        assert resp.allowed is False
        assert resp.status_code == 403

    def test_tc18_disabled_tenant_403(self, svc, authority):
        authority.disable("tenant_A")
        mw2 = ZeroTrustMiddleware(svc, authority, required_role="writer")
        tok = svc.issue("alice", "tenant_A", roles=["writer"])
        resp = mw2.process(make_request(tok))
        assert resp.allowed is False
        assert resp.status_code == 403
        authority.enable("tenant_A")  # restore

    def test_tc19_denied_claims_none(self, mw):
        resp = mw.process(ZTRequest(request_id="r-nc"))
        assert resp.claims is None

    def test_tc20_denied_decision_none(self, mw):
        resp = mw.process(ZTRequest(request_id="r-nd"))
        assert resp.decision is None

    def test_tc21_garbage_bearer_401(self, mw):
        req = ZTRequest(request_id="r-gar", authorization="Bearer garbage")
        resp = mw.process(req)
        assert resp.status_code == 401

    def test_tc22_reason_contains_info_on_deny(self, mw):
        req = ZTRequest(request_id="r-reason")
        resp = mw.process(req)
        assert len(resp.reason) > 0


# ──────────────────────────────────────────────
# TestAuditLog  TC23~28
# ──────────────────────────────────────────────
class TestAuditLog:
    def test_tc23_audit_entry_created_on_pass(self, mw, svc):
        tok = svc.issue("alice", "tenant_A", roles=["writer"])
        mw.process(make_request(tok))
        assert mw.audit_count >= 1

    def test_tc24_audit_entry_created_on_deny(self, mw):
        mw.process(ZTRequest(request_id="deny-audit"))
        assert mw.audit_count >= 1

    def test_tc25_pass_entry_outcome(self, mw, svc):
        tok = svc.issue("alice", "tenant_A", roles=["writer"])
        mw.process(make_request(tok, rid="pass-r"))
        entry = next(e for e in mw.audit_log if e.request_id == "pass-r")
        assert entry.outcome == "PASS"

    def test_tc26_deny_entry_outcome(self, mw):
        mw.process(ZTRequest(request_id="deny-r"))
        entry = next(e for e in mw.audit_log if e.request_id == "deny-r")
        assert entry.outcome == "DENY"

    def test_tc27_pass_count_increments(self, mw, svc):
        before = mw.pass_count()
        tok = svc.issue("alice", "tenant_A", roles=["writer"])
        mw.process(make_request(tok))
        assert mw.pass_count() == before + 1

    def test_tc28_deny_count_increments(self, mw):
        before = mw.deny_count()
        mw.process(ZTRequest(request_id="dc-r"))
        assert mw.deny_count() == before + 1


# ──────────────────────────────────────────────
# TestHooks  TC29~33
# ──────────────────────────────────────────────
class TestHooks:
    def test_tc29_on_pass_hook_called(self, mw, svc):
        fired = []
        mw.on_pass(lambda e: fired.append(e))
        tok = svc.issue("alice", "tenant_A", roles=["writer"])
        mw.process(make_request(tok))
        assert len(fired) == 1

    def test_tc30_on_deny_hook_called(self, mw):
        fired = []
        mw.on_deny(lambda e: fired.append(e))
        mw.process(ZTRequest(request_id="hook-deny"))
        assert len(fired) == 1

    def test_tc31_pass_hook_receives_audit_entry(self, mw, svc):
        entries = []
        mw.on_pass(lambda e: entries.append(e))
        tok = svc.issue("alice", "tenant_A", roles=["writer"])
        mw.process(make_request(tok, rid="hook-pass"))
        assert isinstance(entries[0], ZeroTrustAuditEntry)
        assert entries[0].outcome == "PASS"

    def test_tc32_deny_hook_receives_audit_entry(self, mw):
        entries = []
        mw.on_deny(lambda e: entries.append(e))
        mw.process(ZTRequest(request_id="hook-deny2"))
        assert isinstance(entries[0], ZeroTrustAuditEntry)
        assert entries[0].outcome == "DENY"

    def test_tc33_multiple_hooks_all_called(self, mw, svc):
        counts = [0, 0]
        mw.on_pass(lambda e: counts.__setitem__(0, counts[0] + 1))
        mw.on_pass(lambda e: counts.__setitem__(1, counts[1] + 1))
        tok = svc.issue("alice", "tenant_A", roles=["writer"])
        mw.process(make_request(tok))
        assert counts == [1, 1]
