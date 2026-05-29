"""
V722 — test_v722_agent_auth_bridge.py
========================================
AgentAuthBridge 테스트 33 TC (TC01~TC33)
ADR-183: agents/ → security/ 단방향 연결 검증
"""
from __future__ import annotations
import pytest
from literary_system.agents.agent_auth_bridge import (
    AgentAuthBridge, AgentAuthRecord, BridgeResult, AuthDecision,
)
from literary_system.security.zero_trust_token import ZeroTrustTokenService
from literary_system.security.tenant_authority import TenantAuthority

SECRET = b"bridge-secret-32bytes-padding-xxx"

@pytest.fixture
def svc():
    return ZeroTrustTokenService(secret_key=SECRET)

@pytest.fixture
def auth():
    a = TenantAuthority()
    a.register("t1", display_name="T1", allowed_roles={"writer", "reader"})
    a.register("t2", display_name="T2", allowed_roles={"reader"})
    return a

@pytest.fixture
def bridge(svc, auth):
    b = AgentAuthBridge(svc, auth)
    b.register_agent("writer-A", tenant_id="t1", required_role="writer")
    b.register_agent("reader-B", tenant_id="t1", required_role="reader")
    b.register_agent("no-role-C", tenant_id="t1")  # 역할 미지정
    return b

# ── TC01~TC06: 기본 인증 ──────────────────────────────────────────────────────

def test_tc01_allow_with_correct_role(bridge, svc):
    token = svc.issue("agent", tenant_id="t1", roles=["writer"])
    r = bridge.check("writer-A", "Bearer " + token)
    assert r.allowed and r.decision == AuthDecision.ALLOW

def test_tc02_deny_wrong_role(bridge, svc):
    token = svc.issue("agent", tenant_id="t1", roles=["reader"])
    r = bridge.check("writer-A", "Bearer " + token)
    assert not r.allowed and r.decision == AuthDecision.DENY

def test_tc03_allow_no_role_required(bridge, svc):
    """required_role=None → 테넌트 일치만 확인."""
    token = svc.issue("agent", tenant_id="t1")
    r = bridge.check("no-role-C", "Bearer " + token)
    assert r.allowed

def test_tc04_deny_tenant_mismatch_no_role(bridge, svc):
    token = svc.issue("agent", tenant_id="t2")
    r = bridge.check("no-role-C", "Bearer " + token)
    assert not r.allowed

def test_tc05_claims_in_allow_result(bridge, svc):
    token = svc.issue("agent-x", tenant_id="t1", roles=["writer"])
    r = bridge.check("writer-A", "Bearer " + token)
    assert r.claims is not None
    assert r.claims.subject == "agent-x"

def test_tc06_allow_raw_token_no_bearer(bridge, svc):
    token = svc.issue("agent", tenant_id="t1", roles=["reader"])
    r = bridge.check("reader-B", token)
    assert r.allowed

# ── TC07~TC10: 미등록·비활성 에이전트 ────────────────────────────────────────

def test_tc07_unregistered_fail_closed():
    svc = ZeroTrustTokenService(secret_key=SECRET)
    auth = TenantAuthority()
    bridge = AgentAuthBridge(svc, auth, fail_closed=True)
    token = svc.issue("u", tenant_id="t")
    r = bridge.check("ghost", "Bearer " + token)
    assert not r.allowed

def test_tc08_unregistered_fail_open():
    svc = ZeroTrustTokenService(secret_key=SECRET)
    auth = TenantAuthority()
    bridge = AgentAuthBridge(svc, auth, fail_closed=False)
    token = svc.issue("u", tenant_id="t")
    r = bridge.check("ghost", "Bearer " + token)
    assert r.allowed

def test_tc09_deactivated_agent(bridge, svc):
    bridge._agents["writer-A"].active = False
    token = svc.issue("agent", tenant_id="t1", roles=["writer"])
    r = bridge.check("writer-A", "Bearer " + token)
    assert not r.allowed

def test_tc10_register_and_check(svc, auth):
    bridge = AgentAuthBridge(svc, auth)
    bridge.register_agent("new-agent", tenant_id="t1", required_role="writer")
    token = svc.issue("u", tenant_id="t1", roles=["writer"])
    r = bridge.check("new-agent", "Bearer " + token)
    assert r.allowed

# ── TC11~TC14: 토큰 오류 ──────────────────────────────────────────────────────

def test_tc11_invalid_token(bridge):
    r = bridge.check("writer-A", "Bearer bad.token.x")
    assert r.decision == AuthDecision.INVALID

def test_tc12_expired_token(auth):
    svc_exp = ZeroTrustTokenService(secret_key=SECRET, default_ttl=-1)
    bridge = AgentAuthBridge(svc_exp, auth)
    bridge.register_agent("ag", tenant_id="t1", required_role="writer")
    token = svc_exp.issue("u", tenant_id="t1", roles=["writer"])
    r = bridge.check("ag", "Bearer " + token)
    assert r.decision == AuthDecision.EXPIRED

def test_tc13_empty_token(bridge):
    r = bridge.check("writer-A", "Bearer ")
    assert r.decision == AuthDecision.INVALID

def test_tc14_wrong_secret(auth):
    svc_a = ZeroTrustTokenService(secret_key=b"secret-a-32bytes-paddddddddddddd")
    svc_b = ZeroTrustTokenService(secret_key=b"secret-b-32bytes-paddddddddddddd")
    bridge = AgentAuthBridge(svc_b, auth)
    bridge.register_agent("ag", tenant_id="t1")
    token = svc_a.issue("u", tenant_id="t1")
    r = bridge.check("ag", "Bearer " + token)
    assert r.decision == AuthDecision.INVALID

# ── TC15~TC18: 에이전트 관리 ─────────────────────────────────────────────────

def test_tc15_list_agents(bridge):
    agents = bridge.list_agents()
    assert "writer-A" in agents
    assert "reader-B" in agents
    assert "no-role-C" in agents

def test_tc16_deregister_agent(bridge, svc):
    ok = bridge.deregister_agent("reader-B")
    assert ok
    assert "reader-B" not in bridge.list_agents()

def test_tc17_deregister_nonexistent(bridge):
    assert bridge.deregister_agent("ghost") is False

def test_tc18_get_agent_record(bridge):
    rec = bridge.get_agent_record("writer-A")
    assert isinstance(rec, AgentAuthRecord)
    assert rec.tenant_id == "t1"
    assert rec.required_role == "writer"

# ── TC19~TC22: 감사 로그 ─────────────────────────────────────────────────────

def test_tc19_audit_log_grows(bridge, svc):
    t1 = svc.issue("u1", tenant_id="t1", roles=["writer"])
    t2 = svc.issue("u2", tenant_id="t1", roles=["writer"])
    bridge.check("writer-A", "Bearer " + t1)
    bridge.check("writer-A", "Bearer " + t2)
    assert len(bridge.audit_log()) >= 2

def test_tc20_audit_log_records_deny(bridge):
    bridge.check("writer-A", "Bearer bad.token.x")
    log = bridge.audit_log()
    assert any(r.decision in (AuthDecision.INVALID, AuthDecision.DENY) for r in log)

def test_tc21_clear_audit(bridge, svc):
    token = svc.issue("u", tenant_id="t1", roles=["writer"])
    bridge.check("writer-A", "Bearer " + token)
    bridge.clear_audit()
    assert len(bridge.audit_log()) == 0

def test_tc22_audit_result_is_copy(bridge, svc):
    token = svc.issue("u", tenant_id="t1", roles=["writer"])
    bridge.check("writer-A", "Bearer " + token)
    log = bridge.audit_log()
    log.clear()
    assert len(bridge.audit_log()) > 0  # 내부 리스트 영향 없음

# ── TC23~TC26: 통계 ───────────────────────────────────────────────────────────

def test_tc23_stats_allow(bridge, svc):
    token = svc.issue("u", tenant_id="t1", roles=["writer"])
    bridge.check("writer-A", "Bearer " + token)
    stats = bridge.stats()
    assert stats["ALLOW"] >= 1

def test_tc24_stats_deny(bridge):
    bridge.check("writer-A", "Bearer bad.token.x")
    stats = bridge.stats()
    assert stats["INVALID"] >= 1

def test_tc25_stats_all_keys(bridge):
    stats = bridge.stats()
    for d in AuthDecision:
        assert d.value in stats

def test_tc26_stats_expired(auth):
    svc_exp = ZeroTrustTokenService(secret_key=SECRET, default_ttl=-1)
    bridge = AgentAuthBridge(svc_exp, auth)
    bridge.register_agent("ag", tenant_id="t1")
    token = svc_exp.issue("u", tenant_id="t1")
    bridge.check("ag", "Bearer " + token)
    assert bridge.stats()["EXPIRED"] >= 1

# ── TC27~TC30: check_batch ────────────────────────────────────────────────────

def test_tc27_check_batch_all_valid(bridge, svc):
    tokens = [svc.issue(f"u{i}", tenant_id="t1", roles=["writer"]) for i in range(3)]
    results = bridge.check_batch("writer-A", ["Bearer " + t for t in tokens])
    assert len(results) == 3
    assert all(r.allowed for r in results)

def test_tc28_check_batch_mixed(bridge, svc):
    t1 = svc.issue("u1", tenant_id="t1", roles=["writer"])
    results = bridge.check_batch("writer-A", ["Bearer " + t1, "Bearer bad.token.x"])
    assert results[0].allowed
    assert not results[1].allowed

def test_tc29_check_batch_empty(bridge):
    results = bridge.check_batch("writer-A", [])
    assert results == []

def test_tc30_check_batch_single(bridge, svc):
    t = svc.issue("u", tenant_id="t1", roles=["reader"])
    results = bridge.check_batch("reader-B", ["Bearer " + t])
    assert len(results) == 1
    assert results[0].allowed

# ── TC31~TC33: 설계·구조 검증 ────────────────────────────────────────────────

def test_tc31_no_circular_import():
    """security → agents 역방향 import 없음."""
    import literary_system.security.zero_trust_token as m
    src = open(m.__file__, encoding="utf-8").read()
    assert "from literary_system.agents" not in src
    assert "import literary_system.agents" not in src

def test_tc32_bridge_result_allowed():
    r = BridgeResult(decision=AuthDecision.ALLOW, reason="OK")
    assert r.allowed is True
    r2 = BridgeResult(decision=AuthDecision.DENY, reason="no")
    assert r2.allowed is False

def test_tc33_auth_decision_enum():
    assert AuthDecision.ALLOW.value == "ALLOW"
    assert AuthDecision.DENY.value == "DENY"
    assert AuthDecision.EXPIRED.value == "EXPIRED"
    assert AuthDecision.INVALID.value == "INVALID"
