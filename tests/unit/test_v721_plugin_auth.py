"""
V721 — test_v721_plugin_auth.py
================================
PluginAuthAdapter 테스트 33 TC (TC01~TC33)
ADR-182: plugins/ → security/ 단방향 연결 검증

ZeroTrustTokenService API 특성:
  - verify()는 jti 일회성 소비 (replay 방지)
  - 각 TC는 독립 토큰을 발급하여 사용
"""
from __future__ import annotations
import pytest
from literary_system.plugins.plugin_auth import (
    PluginAuthAdapter,
    PluginAuthResult,
    PluginAuthError,
    PluginTokenInvalid,
    PluginTokenExpired,
    PluginAccessDenied,
    PluginTenantNotFound,
    PERMISSION_ROLE_MAP,
)
from literary_system.plugins.plugin_manifest import PluginPermission
from literary_system.security.zero_trust_token import ZeroTrustTokenService
from literary_system.security.tenant_authority import TenantAuthority


# ── 공용 픽스처 ───────────────────────────────────────────────────────────────

SECRET = b"test-secret-32bytes-padding-here"

@pytest.fixture
def svc():
    return ZeroTrustTokenService(secret_key=SECRET)

@pytest.fixture
def auth():
    a = TenantAuthority()
    a.register("t1", display_name="Tenant One",
                allowed_roles={"corpus_reader", "output_writer", "llm_caller"})
    a.register("t2", display_name="Tenant Two", allowed_roles={"nkg_reader"})
    return a

@pytest.fixture
def adapter(svc, auth):
    return PluginAuthAdapter(svc, auth)

@pytest.fixture
def adapter_lenient(svc, auth):
    return PluginAuthAdapter(svc, auth, strict=False)


# ── TC01~TC05: 기본 인증 ──────────────────────────────────────────────────────

def test_tc01_authenticate_valid_token(adapter, svc):
    """정상 Bearer 토큰 → 인증 성공."""
    token = svc.issue("plugin-1", tenant_id="t1", roles=["corpus_reader"])
    result = adapter.authenticate("Bearer " + token, "t1", [PluginPermission.READ_CORPUS])
    assert result.authenticated is True
    assert result.fully_authorized is True

def test_tc02_authenticate_without_bearer_prefix(adapter, svc):
    """Bearer 접두사 없는 raw 토큰도 허용."""
    token = svc.issue("plugin-2", tenant_id="t1")
    result = adapter.authenticate(token, "t1", [])
    assert result.authenticated is True

def test_tc03_authenticate_no_permissions_required(adapter, svc):
    """required_permissions=[] → 인증만 수행, 항상 fully_authorized."""
    token = svc.issue("plugin-3", tenant_id="t1")
    result = adapter.authenticate("Bearer " + token, "t1", [])
    assert result.fully_authorized is True
    assert result.granted_permissions == []
    assert result.denied_permissions == []

def test_tc04_authenticate_none_permissions(adapter, svc):
    """required_permissions=None → 인증만 수행."""
    token = svc.issue("plugin-4", tenant_id="t1")
    result = adapter.authenticate("Bearer " + token, "t1", None)
    assert result.authenticated is True

def test_tc05_result_claims_populated(adapter, svc):
    """인증 성공 시 result.claims에 TokenClaims 채워짐."""
    token = svc.issue("plugin-5", tenant_id="t1")
    result = adapter.authenticate("Bearer " + token, "t1", [])
    assert result.claims is not None
    assert result.claims.subject == "plugin-5"
    assert result.claims.tenant_id == "t1"


# ── TC06~TC10: 권한 인가 ──────────────────────────────────────────────────────

def test_tc06_permission_granted(adapter, svc):
    """허용된 권한 → granted_permissions에 포함."""
    token = svc.issue("plugin-6", tenant_id="t1", roles=["corpus_reader"])
    result = adapter.authenticate("Bearer " + token, "t1", [PluginPermission.READ_CORPUS])
    assert PluginPermission.READ_CORPUS in result.granted_permissions

def test_tc07_permission_denied(adapter_lenient, svc):
    """미허용 권한 → denied_permissions에 포함 (strict=False)."""
    token = svc.issue("plugin-7", tenant_id="t1")
    result = adapter_lenient.authenticate("Bearer " + token, "t1",
                                          [PluginPermission.WRITE_NKG])
    assert PluginPermission.WRITE_NKG in result.denied_permissions
    assert result.fully_authorized is False

def test_tc08_multiple_permissions_partial(adapter_lenient, svc):
    """일부 허용, 일부 거부 → granted/denied 분리."""
    token = svc.issue("plugin-8", tenant_id="t1", roles=["corpus_reader"])
    result = adapter_lenient.authenticate("Bearer " + token, "t1",
                                          [PluginPermission.READ_CORPUS,
                                           PluginPermission.NETWORK_OUT])
    assert PluginPermission.READ_CORPUS in result.granted_permissions
    assert PluginPermission.NETWORK_OUT in result.denied_permissions

def test_tc09_all_permissions_granted(adapter, svc):
    """허용 역할 내 모든 권한 → fully_authorized=True."""
    token = svc.issue("plugin-9", tenant_id="t1", roles=["corpus_reader","output_writer","llm_caller"])
    result = adapter.authenticate("Bearer " + token, "t1",
                                  [PluginPermission.READ_CORPUS,
                                   PluginPermission.WRITE_OUTPUT,
                                   PluginPermission.CALL_LLM])
    assert result.fully_authorized is True
    assert len(result.denied_permissions) == 0

def test_tc10_different_tenant_permission(adapter, svc):
    """t1 토큰으로 t2 테넌트 리소스 → 거부 (strict 발생)."""
    token = svc.issue("plugin-10", tenant_id="t1")
    with pytest.raises(PluginAccessDenied):
        adapter.authenticate("Bearer " + token, "t2", [PluginPermission.READ_CORPUS])


# ── TC11~TC15: 토큰 오류 처리 ────────────────────────────────────────────────

def test_tc11_invalid_token_format():
    """잘못된 토큰 형식 → PluginTokenInvalid."""
    svc = ZeroTrustTokenService(secret_key=SECRET)
    auth = TenantAuthority()
    adapter = PluginAuthAdapter(svc, auth)
    with pytest.raises(PluginTokenInvalid):
        adapter.authenticate("Bearer not.a.valid.token", "t1", [])

def test_tc12_tampered_signature():
    """서명 변조 → PluginTokenInvalid."""
    svc = ZeroTrustTokenService(secret_key=SECRET)
    auth = TenantAuthority()
    adapter = PluginAuthAdapter(svc, auth)
    token = svc.issue("u", tenant_id="t1")
    parts = token.split(".")
    parts[-1] = "invalidsig"
    with pytest.raises(PluginTokenInvalid):
        adapter.authenticate("Bearer " + ".".join(parts), "t1", [])

def test_tc13_empty_token():
    """빈 토큰 → PluginTokenInvalid."""
    svc = ZeroTrustTokenService(secret_key=SECRET)
    auth = TenantAuthority()
    adapter = PluginAuthAdapter(svc, auth)
    with pytest.raises(PluginTokenInvalid):
        adapter.authenticate("Bearer ", "t1", [])

def test_tc14_expired_token():
    """만료 토큰 → PluginTokenExpired."""
    import time
    svc = ZeroTrustTokenService(secret_key=SECRET, default_ttl=-1)
    auth = TenantAuthority()
    adapter = PluginAuthAdapter(svc, auth)
    token = svc.issue("u", tenant_id="t1")
    with pytest.raises(PluginTokenExpired):
        adapter.authenticate("Bearer " + token, "t1", [])

def test_tc15_wrong_secret():
    """다른 키로 서명된 토큰 → PluginTokenInvalid."""
    svc_a = ZeroTrustTokenService(secret_key=b"secret-aaaaaaaaaaaaaaaaaaaaaaaaaaa")
    svc_b = ZeroTrustTokenService(secret_key=b"secret-bbbbbbbbbbbbbbbbbbbbbbbbbbb")
    auth = TenantAuthority()
    adapter = PluginAuthAdapter(svc_b, auth)
    token = svc_a.issue("u", tenant_id="t1")
    with pytest.raises(PluginTokenInvalid):
        adapter.authenticate("Bearer " + token, "t1", [])


# ── TC16~TC20: 테넌트 오류 처리 ──────────────────────────────────────────────

def test_tc16_unregistered_tenant():
    """미등록 테넌트 + strict=True → PluginAccessDenied (authorize 내부 흡수)."""
    svc = ZeroTrustTokenService(secret_key=SECRET)
    auth = TenantAuthority()
    adapter = PluginAuthAdapter(svc, auth, strict=True)
    token = svc.issue("u", tenant_id="ghost")
    with pytest.raises(PluginAccessDenied):
        adapter.authenticate("Bearer " + token, "ghost", [PluginPermission.READ_CORPUS])

def test_tc17_strict_access_denied():
    """strict=True + 권한 거부 → PluginAccessDenied."""
    svc = ZeroTrustTokenService(secret_key=SECRET)
    auth = TenantAuthority()
    auth.register("t", display_name="T", allowed_roles=set())
    adapter = PluginAuthAdapter(svc, auth, strict=True)
    token = svc.issue("u", tenant_id="t")
    with pytest.raises(PluginAccessDenied):
        adapter.authenticate("Bearer " + token, "t", [PluginPermission.READ_CORPUS])

def test_tc18_lenient_no_raise():
    """strict=False + 권한 거부 → 예외 없이 PluginAuthResult 반환."""
    svc = ZeroTrustTokenService(secret_key=SECRET)
    auth = TenantAuthority()
    auth.register("t", display_name="T", allowed_roles=set())
    adapter = PluginAuthAdapter(svc, auth, strict=False)
    token = svc.issue("u", tenant_id="t")
    result = adapter.authenticate("Bearer " + token, "t", [PluginPermission.CALL_LLM])
    assert isinstance(result, PluginAuthResult)
    assert not result.fully_authorized

def test_tc19_disabled_tenant():
    """비활성 테넌트 → 접근 거부 (테넌트 비활성 시 TenantDisabledError or deny)."""
    svc = ZeroTrustTokenService(secret_key=SECRET)
    auth = TenantAuthority()
    auth.register("t", display_name="T", allowed_roles={"corpus_reader"})
    auth.disable("t")
    adapter = PluginAuthAdapter(svc, auth, strict=False)
    token = svc.issue("u", tenant_id="t")
    # disabled 테넌트 → denied or PluginTenantNotFound/PluginAccessDenied
    try:
        result = adapter.authenticate("Bearer " + token, "t", [PluginPermission.READ_CORPUS])
        assert not result.fully_authorized
    except (PluginTenantNotFound, PluginAccessDenied):
        pass  # 예외 발생도 허용

def test_tc20_cross_tenant_isolation():
    """t1 토큰 + t2 리소스 → lenient 모드에서도 denied."""
    svc = ZeroTrustTokenService(secret_key=SECRET)
    auth = TenantAuthority()
    auth.register("t1", display_name="T1", allowed_roles={"corpus_reader"})
    auth.register("t2", display_name="T2", allowed_roles={"corpus_reader"})
    adapter = PluginAuthAdapter(svc, auth, strict=False)
    token = svc.issue("u", tenant_id="t1")
    # t2 리소스에 대한 t1 토큰 → deny
    try:
        result = adapter.authenticate("Bearer " + token, "t2", [PluginPermission.READ_CORPUS])
        assert not result.fully_authorized or result.denied_permissions
    except (PluginAccessDenied, PluginTenantNotFound):
        pass  # 예외도 허용


# ── TC21~TC25: verify_token_only ─────────────────────────────────────────────

def test_tc21_verify_token_only_returns_claims():
    """verify_token_only → TokenClaims 반환."""
    svc = ZeroTrustTokenService(secret_key=SECRET)
    auth = TenantAuthority()
    adapter = PluginAuthAdapter(svc, auth)
    token = svc.issue("agent-1", tenant_id="t1")
    claims = adapter.verify_token_only("Bearer " + token)
    assert claims.subject == "agent-1"

def test_tc22_verify_token_only_no_bearer():
    """Bearer 접두사 없이도 동작."""
    svc = ZeroTrustTokenService(secret_key=SECRET)
    auth = TenantAuthority()
    adapter = PluginAuthAdapter(svc, auth)
    token = svc.issue("agent-2", tenant_id="t1")
    claims = adapter.verify_token_only(token)
    assert claims.subject == "agent-2"

def test_tc23_verify_token_only_invalid():
    """잘못된 토큰 → PluginTokenInvalid."""
    svc = ZeroTrustTokenService(secret_key=SECRET)
    auth = TenantAuthority()
    adapter = PluginAuthAdapter(svc, auth)
    with pytest.raises(PluginTokenInvalid):
        adapter.verify_token_only("Bearer bad.token.here")

def test_tc24_verify_token_only_expired():
    """만료 → PluginTokenExpired."""
    svc = ZeroTrustTokenService(secret_key=SECRET, default_ttl=-1)
    auth = TenantAuthority()
    adapter = PluginAuthAdapter(svc, auth)
    token = svc.issue("u", tenant_id="t")
    with pytest.raises(PluginTokenExpired):
        adapter.verify_token_only("Bearer " + token)

def test_tc25_verify_token_only_roles():
    """클레임에 roles가 올바르게 포함됨."""
    svc = ZeroTrustTokenService(secret_key=SECRET)
    auth = TenantAuthority()
    adapter = PluginAuthAdapter(svc, auth)
    token = svc.issue("u", tenant_id="t1", roles=["admin", "reader"])
    claims = adapter.verify_token_only("Bearer " + token)
    assert "admin" in claims.roles
    assert "reader" in claims.roles


# ── TC26~TC29: has_permission ────────────────────────────────────────────────

def test_tc26_has_permission_true():
    """허용된 권한 → True."""
    svc = ZeroTrustTokenService(secret_key=SECRET)
    auth = TenantAuthority()
    auth.register("t", display_name="T", allowed_roles={"corpus_reader"})
    adapter = PluginAuthAdapter(svc, auth)
    token = svc.issue("u", tenant_id="t", roles=["corpus_reader"])
    claims = adapter.verify_token_only(token)
    assert adapter.has_permission(claims, PluginPermission.READ_CORPUS, "t") is True

def test_tc27_has_permission_false():
    """미허용 권한 → False."""
    svc = ZeroTrustTokenService(secret_key=SECRET)
    auth = TenantAuthority()
    auth.register("t", display_name="T", allowed_roles=set())
    adapter = PluginAuthAdapter(svc, auth)
    token = svc.issue("u", tenant_id="t")
    claims = adapter.verify_token_only(token)
    assert adapter.has_permission(claims, PluginPermission.WRITE_NKG, "t") is False

def test_tc28_has_permission_no_exception():
    """예외 발생 시 False 반환 (내부 흡수)."""
    svc = ZeroTrustTokenService(secret_key=SECRET)
    auth = TenantAuthority()
    adapter = PluginAuthAdapter(svc, auth)
    token = svc.issue("u", tenant_id="t")
    claims = adapter.verify_token_only(token)
    # 미등록 테넌트 → False (예외 아님)
    assert adapter.has_permission(claims, PluginPermission.READ_CORPUS, "nonexistent") is False

def test_tc29_has_permission_all_permissions():
    """PERMISSION_ROLE_MAP의 모든 권한 검증."""
    svc = ZeroTrustTokenService(secret_key=SECRET)
    auth = TenantAuthority()
    roles = set(PERMISSION_ROLE_MAP.values())
    auth.register("t", display_name="T", allowed_roles=roles)
    adapter = PluginAuthAdapter(svc, auth)
    all_roles = list(PERMISSION_ROLE_MAP.values())
    token = svc.issue("u", tenant_id="t", roles=all_roles)
    claims = adapter.verify_token_only(token)
    for perm in PluginPermission:
        assert adapter.has_permission(claims, perm, "t") is True


# ── TC30~TC33: 구조·설계 검증 ────────────────────────────────────────────────

def test_tc30_permission_role_map_complete():
    """PERMISSION_ROLE_MAP이 모든 PluginPermission 커버."""
    for perm in PluginPermission:
        assert perm in PERMISSION_ROLE_MAP, f"{perm} not in PERMISSION_ROLE_MAP"

def test_tc31_plugin_auth_error_hierarchy():
    """PluginAuthError 예외 계층 정상."""
    assert issubclass(PluginTokenInvalid, PluginAuthError)
    assert issubclass(PluginTokenExpired, PluginAuthError)
    assert issubclass(PluginAccessDenied, PluginAuthError)
    assert issubclass(PluginTenantNotFound, PluginAuthError)

def test_tc32_security_dependency_direction():
    """plugins → security 단방향: security가 plugins를 import하지 않음."""
    import importlib, sys
    # security 모듈 소스에서 'from literary_system.plugins' 참조 없어야 함
    import literary_system.security.zero_trust_token as m
    src = open(m.__file__, encoding="utf-8").read()
    assert "from literary_system.plugins" not in src
    assert "import literary_system.plugins" not in src

def test_tc33_plugin_auth_result_dataclass():
    """PluginAuthResult 기본 필드 초기화 정상."""
    r = PluginAuthResult(authenticated=True, reason="OK")
    assert r.authenticated is True
    assert r.granted_permissions == []
    assert r.denied_permissions == []
    assert r.fully_authorized is True  # authenticated=True, denied=[]
