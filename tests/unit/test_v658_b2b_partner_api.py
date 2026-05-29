"""V658 B2B Partner API 테스트 (ADR-118) — 33 TC."""
from __future__ import annotations

import pytest

from literary_system.sdk.b2b import (
    B2BPartnerAPI,
    ExpiredTokenError,
    InvalidClientError,
    InvalidTokenError,
    OAuth21Manager,
    OAuthError,
    PartnerAPIConfig,
    PartnerQuotaError,
    WebhookEvent,
    WebhookEventType,
    WebhookManager,
    sign_payload,
    verify_signature,
)


@pytest.fixture
def api():
    return B2BPartnerAPI(PartnerAPIConfig(offline_mode=True, default_rpm=0))

@pytest.fixture
def partner(api):
    cid, secret = api.register_partner("TestCo")
    return cid, secret

@pytest.fixture
def token(api, partner):
    cid, secret = partner
    return api.issue_token(cid, secret)


# ── TC-01~07: OAuth 2.1 등록/발급 ─────────────────────────────────────────

class TestOAuth:
    def test_register_returns_credentials(self, api):                      # TC-01
        cid, secret = api.register_partner("Partner A")
        assert cid.startswith("cid_")
        assert len(secret) > 20

    def test_issue_token_returns_access_token(self, api, partner):         # TC-02
        cid, secret = partner
        tok = api.issue_token(cid, secret)
        assert tok.token.startswith("los_")
        assert tok.client_id == cid

    def test_wrong_secret_raises(self, api, partner):                      # TC-03
        cid, _ = partner
        with pytest.raises(InvalidClientError):
            api.issue_token(cid, "wrong_secret")

    def test_unknown_client_raises(self, api):                             # TC-04
        with pytest.raises(InvalidClientError):
            api.issue_token("cid_unknown", "any")

    def test_wrong_grant_type_raises(self, api, partner):                  # TC-05
        cid, secret = partner
        with pytest.raises(OAuthError, match="unsupported_grant_type|Unsupported"):
            api.issue_token(cid, secret, grant_type="password")

    def test_validate_token_ok(self, api, token):                          # TC-06
        at = api.validate_token(token.token)
        assert at.client_id == token.client_id

    def test_invalid_token_raises(self, api):                              # TC-07
        with pytest.raises(InvalidTokenError):
            api.validate_token("los_invalid")

    def test_revoke_token(self, api, token):                               # TC-08
        api.revoke_token(token.token)
        with pytest.raises(InvalidTokenError):
            api.validate_token(token.token)

    def test_deactivate_partner(self, api):                                # TC-09
        cid, secret = api.register_partner("ToDeactivate")
        api.deactivate_partner(cid)
        with pytest.raises(InvalidClientError):
            api.issue_token(cid, secret)


# ── TC-10~16: RPM 제한 ────────────────────────────────────────────────────

class TestRPM:
    def test_no_limit_passes(self, api, token):                            # TC-10
        # rpm=0 → 무제한
        result = api.call_analyze(token.token, "영수는 창문을 바라보았다. 눈물이 고였다.")
        assert "quality" in result

    def test_rpm_exceeded_raises(self):                                    # TC-11
        limited_api = B2BPartnerAPI(PartnerAPIConfig(offline_mode=True, default_rpm=2))
        cid, secret = limited_api.register_partner("LimitedCo", rpm_limit=2)
        tok = limited_api.issue_token(cid, secret)
        text = "영수는 창문을 바라보았다. 눈물이 고였다."
        limited_api.call_analyze(tok.token, text)
        limited_api.call_analyze(tok.token, text)
        with pytest.raises(PartnerQuotaError):
            limited_api.call_analyze(tok.token, text)

    def test_rpm_current_increments(self, api, token):                     # TC-12
        before = api.rpm_current(token.client_id)
        api.call_analyze(token.token, "영수는 창문을 바라보았다. 눈물이 고였다.")
        assert api.rpm_current(token.client_id) >= before


# ── TC-13~20: API 호출 ────────────────────────────────────────────────────

class TestAPICalls:
    def test_call_analyze_returns_dict(self, api, token):                  # TC-13
        r = api.call_analyze(token.token, "영수는 창문을 바라보았다. 눈물이 고였다.")
        assert "quality" in r
        assert "issues" in r
        assert "passed" in r

    def test_call_generate_returns_scene(self, api, token):                # TC-14
        r = api.call_generate(
            token.token, "운명", ["이지수"], "골목", "비밀"
        )
        assert "scene_text" in r
        assert len(r["scene_text"]) > 0

    def test_call_repair_returns_result(self, api, token):                 # TC-15
        r = api.call_repair(
            token.token,
            "짧은 씬이다. 이게 전부다.",
            ["too_few_sentences"],
        )
        assert "repaired_text" in r
        assert "improved" in r

    def test_call_predict_returns_list(self, api, token):                  # TC-16
        r = api.call_predict(token.token, "두 사람이 마주쳤다. 분위기가 이상했다.", n=2)
        assert "predictions" in r
        assert len(r["predictions"]) == 2

    def test_scope_missing_raises(self):                                   # TC-17
        restricted_api = B2BPartnerAPI(PartnerAPIConfig(offline_mode=True, default_rpm=0))
        cid, secret = restricted_api._oauth.register_client(
            "Restricted", scopes=["analyze"], rpm_limit=0
        )
        tok = restricted_api.issue_token(cid, secret)
        with pytest.raises(OAuthError):
            restricted_api.call_generate(tok.token, "T", ["A"], "S", "C")

    def test_expired_token_raises(self):                                   # TC-18
        short_api = B2BPartnerAPI(PartnerAPIConfig(offline_mode=True, default_rpm=0))
        short_api._oauth._token_ttl = 0  # 즉시 만료
        cid, secret = short_api.register_partner("ShortLived")
        tok = short_api.issue_token(cid, secret)
        import time; time.sleep(0.01)
        with pytest.raises(ExpiredTokenError):
            short_api.validate_token(tok.token)


# ── TC-19~26: Webhook ─────────────────────────────────────────────────────

class TestWebhook:
    def test_register_webhook(self, api, token):                           # TC-19
        result = api.register_webhook(token.client_id, "http://localhost/hook", "mysecret")
        assert result is True

    def test_webhook_fired_after_analyze(self, api, token):                # TC-20
        api.register_webhook(token.client_id, "http://localhost/hook", "mysecret")
        api.call_analyze(token.token, "영수는 창문을 바라보았다. 눈물이 고였다.")
        history = api.webhook_history(token.client_id)
        assert len(history) >= 1

    def test_webhook_event_success(self, api, token):                      # TC-21
        api.register_webhook(token.client_id, "http://ok/hook", "s")
        api.call_analyze(token.token, "영수는 창문을 바라보았다. 눈물이 고였다.")
        history = api.webhook_history(token.client_id)
        assert history[-1].success is True

    def test_sign_payload(self):                                           # TC-22
        sig = sign_payload(b"hello", "mysecret")
        assert len(sig) == 64  # SHA-256 hex digest

    def test_verify_signature_ok(self):                                    # TC-23
        body = b'{"event":"test"}'
        sig = sign_payload(body, "secret123")
        assert verify_signature(body, "secret123", sig) is True

    def test_verify_signature_fail(self):                                  # TC-24
        body = b'{"event":"test"}'
        sig = sign_payload(body, "secret123")
        assert verify_signature(body, "wrong_secret", sig) is False

    def test_webhook_event_types(self):                                    # TC-25
        types = list(WebhookEventType)
        assert WebhookEventType.SCENE_ANALYZED in types
        assert WebhookEventType.QUOTA_EXCEEDED in types

    def test_webhook_history_filtered_by_client(self, api, token):        # TC-26
        cid2, secret2 = api.register_partner("Other")
        tok2 = api.issue_token(cid2, secret2)
        api.register_webhook(token.client_id, "http://a/hook", "s1")
        api.register_webhook(cid2, "http://b/hook", "s2")
        api.call_analyze(token.token, "영수는 창문을 바라보았다. 눈물이 고였다.")
        api.call_analyze(tok2.token, "박민호가 그녀를 바라보았다. 설렘이 느껴졌다.")
        h1 = api.webhook_history(token.client_id)
        h2 = api.webhook_history(cid2)
        assert all(r.client_id == token.client_id for r in h1)
        assert all(r.client_id == cid2 for r in h2)


# ── TC-27~33: OAuth 저수준 ────────────────────────────────────────────────

class TestOAuthLow:
    def test_token_not_expired_initially(self, api, token):                # TC-27
        assert token.is_expired is False

    def test_token_scopes_populated(self, api, token):                     # TC-28
        assert len(token.scopes) > 0

    def test_purge_expired_tokens(self):                                   # TC-29
        mgr = OAuth21Manager(token_ttl=0)
        cid, secret = mgr.register_client("X")
        mgr.issue_token(cid, secret)
        import time; time.sleep(0.01)
        purged = mgr.purge_expired_tokens()
        assert purged >= 1

    def test_client_scopes_allowed(self, api, partner):                    # TC-30
        cid, secret = partner
        tok = api.issue_token(cid, secret, requested_scopes=["analyze"])
        assert "analyze" in tok.scopes

    def test_invalid_scope_raises(self, api, partner):                     # TC-31
        cid, secret = partner
        with pytest.raises(OAuthError, match="invalid_scope|not allowed"):
            api.issue_token(cid, secret, requested_scopes=["admin"])

    def test_active_token_count(self, api):                                # TC-32
        cid, secret = api.register_partner("CountTest")
        api.issue_token(cid, secret)
        assert api._oauth.active_token_count >= 1

    def test_partner_quota_error_attrs(self, api):                         # TC-33
        err = PartnerQuotaError("cid_test", 500)
        assert err.client_id == "cid_test"
        assert err.limit == 500
