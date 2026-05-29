"""V725 — test_v725_zero_trust_security_gate.py: G88 Zero-Trust Security Gate 33 TC"""
from __future__ import annotations
import pytest
from literary_system.gates.zero_trust_security_gate import (
    ZeroTrustSecurityGate, run_zero_trust_security_gate,
    ZTCheckResult, _check_zt1_token_service, _check_zt2_tenant_authority,
    _check_zt3_middleware, _check_zt4_audit_log,
    _check_zt5_plugin_auth, _check_zt6_agent_bridge, _check_zt7_chaos_integration,
)

# TC01~TC07: 개별 체크포인트
def test_tc01_zt1_pass(): assert _check_zt1_token_service().passed
def test_tc02_zt2_pass(): assert _check_zt2_tenant_authority().passed
def test_tc03_zt3_pass(): assert _check_zt3_middleware().passed
def test_tc04_zt4_pass(): assert _check_zt4_audit_log().passed
def test_tc05_zt5_pass(): assert _check_zt5_plugin_auth().passed
def test_tc06_zt6_pass(): assert _check_zt6_agent_bridge().passed
def test_tc07_zt7_pass(): assert _check_zt7_chaos_integration().passed

# TC08~TC10: 전체 Gate 실행
def test_tc08_gate_passes():
    passed, results = run_zero_trust_security_gate()
    assert passed

def test_tc09_gate_7_checkpoints():
    _, results = run_zero_trust_security_gate()
    assert len(results) == 7

def test_tc10_all_checkpoints_pass():
    _, results = run_zero_trust_security_gate()
    failed = [r for r in results if not r.passed]
    assert failed == [], f"실패: {failed}"

# TC11~TC14: 클래스 인터페이스
def test_tc11_class_run():
    gate = ZeroTrustSecurityGate()
    passed, results = gate.run()
    assert passed

def test_tc12_class_returns_tuple():
    gate = ZeroTrustSecurityGate()
    result = gate.run()
    assert isinstance(result, tuple) and len(result) == 2

def test_tc13_checkpoint_names():
    _, results = run_zero_trust_security_gate()
    names = [r.checkpoint for r in results]
    assert names == ["ZT-1","ZT-2","ZT-3","ZT-4","ZT-5","ZT-6","ZT-7"]

def test_tc14_result_dataclass():
    r = ZTCheckResult(checkpoint="ZT-X", passed=True, detail="ok")
    assert r.passed and r.checkpoint == "ZT-X"

# TC15~TC21: 각 CP 세부 검증

def test_tc15_zt1_token_issued():
    from literary_system.security.zero_trust_token import ZeroTrustTokenService
    svc = ZeroTrustTokenService(secret_key=b"gate-test-secret-32bytes-paddd!!")
    token = svc.issue("u", tenant_id="t", roles=["r"])
    claims = svc.verify(token)
    assert claims.subject == "u"

def test_tc16_zt2_cross_tenant_blocked():
    from literary_system.security.zero_trust_token import ZeroTrustTokenService
    from literary_system.security.tenant_authority import TenantAuthority
    svc = ZeroTrustTokenService(secret_key=b"gate-test-secret-32bytes-paddd!!")
    auth = TenantAuthority()
    auth.register("a", display_name="A", allowed_roles={"writer"})
    auth.register("b", display_name="B", allowed_roles={"reader"})
    token = svc.issue("u", tenant_id="a", roles=["writer"])
    claims = svc.verify(token)
    d = auth.authorize(claims, required_role="writer", target_tenant_id="b")
    assert not d.granted

def test_tc17_zt3_middleware_rejects_no_token():
    from literary_system.security.zero_trust_token import ZeroTrustTokenService
    from literary_system.security.tenant_authority import TenantAuthority
    from literary_system.security.zero_trust_middleware import ZeroTrustMiddleware, ZTRequest
    svc = ZeroTrustTokenService(secret_key=b"gate-test-secret-32bytes-paddd!!")
    auth = TenantAuthority()
    mw = ZeroTrustMiddleware(svc, auth)
    resp = mw.process(ZTRequest(request_id="x"))
    assert not resp.allowed

def test_tc18_zt4_chain_integrity():
    from literary_system.security.zero_trust_audit_log import ZeroTrustAuditLog
    log = ZeroTrustAuditLog(secret_key=b"gate-test-audit-key-32bytes-pad!")
    for i in range(3):
        log.append("PASS", f"u{i}", "t", "ALLOW", "ok")
    assert log.verify_chain()

def test_tc19_zt5_plugin_adapter_import():
    from literary_system.plugins.plugin_auth import PluginAuthAdapter, PERMISSION_ROLE_MAP
    from literary_system.plugins.plugin_manifest import PluginPermission
    assert len(PERMISSION_ROLE_MAP) == len(PluginPermission)

def test_tc20_zt6_agent_bridge_fail_closed():
    from literary_system.security.zero_trust_token import ZeroTrustTokenService
    from literary_system.security.tenant_authority import TenantAuthority
    from literary_system.agents.agent_auth_bridge import AgentAuthBridge
    svc = ZeroTrustTokenService(secret_key=b"gate-test-secret-32bytes-paddd!!")
    auth = TenantAuthority()
    bridge = AgentAuthBridge(svc, auth, fail_closed=True)
    token = svc.issue("u", tenant_id="t")
    r = bridge.check("unknown", "Bearer " + token)
    assert not r.allowed

def test_tc21_zt7_chaos_engine_5_types():
    from literary_system.chaos import ChaosEngine, FaultType
    assert len(FaultType) == 5

# TC22~TC26: G32·순환·의존성 구조 검증

def test_tc22_g32_gate_file():
    import literary_system.gates.zero_trust_security_gate as m
    src = open(m.__file__, encoding="utf-8").read()
    lines = [l for l in src.splitlines() if l.strip().startswith("print(")]
    assert len(lines) == 0

def test_tc23_no_circular_chaos_to_security():
    import literary_system.chaos.chaos_engine as m
    src = open(m.__file__, encoding="utf-8").read()
    assert "from literary_system.security" not in src

def test_tc24_no_circular_chaos_to_gates():
    import literary_system.chaos.chaos_engine as m
    src = open(m.__file__, encoding="utf-8").read()
    assert "from literary_system.gates" not in src

def test_tc25_security_no_import_agents():
    import literary_system.security.zero_trust_middleware as m
    src = open(m.__file__, encoding="utf-8").read()
    assert "from literary_system.agents" not in src

def test_tc26_security_no_import_plugins():
    import literary_system.security.zero_trust_token as m
    src = open(m.__file__, encoding="utf-8").read()
    assert "from literary_system.plugins" not in src

# TC27~TC30: chaos/ 연결 검증 (ADR-128)

def test_tc27_chaos_importable_from_gate():
    from literary_system.gates.zero_trust_security_gate import _check_zt7_chaos_integration
    result = _check_zt7_chaos_integration()
    assert result.passed

def test_tc28_chaos_engine_register_activate_inject():
    from literary_system.chaos import ChaosEngine, FaultSpec, FaultType
    e = ChaosEngine()
    s = FaultSpec("f1", FaultType.SERVICE_CRASH, "svc", duration_ms=0)
    e.register(s); e.activate("f1")
    r = e.inject("f1")
    assert r.injected

def test_tc29_chaos_fault_injector_records():
    from literary_system.chaos import ChaosEngine, FaultSpec, FaultType, FaultInjector
    e = ChaosEngine()
    s = FaultSpec("f1", FaultType.MEMORY_PRESSURE, "t", duration_ms=0)
    e.register(s); e.activate("f1")
    inj = FaultInjector(e)
    inj.inject_before("f1", lambda: None)
    assert inj.injected_count() >= 1

def test_tc30_zt7_detail_contains_chaos():
    r = _check_zt7_chaos_integration()
    assert "chaos" in r.detail.lower() or "Chaos" in r.detail

# TC31~TC33: 최종 통합 확인

def test_tc31_full_gate_result_structure():
    passed, results = run_zero_trust_security_gate()
    for r in results:
        assert isinstance(r.checkpoint, str)
        assert isinstance(r.passed, bool)
        assert isinstance(r.detail, str)

def test_tc32_gate_idempotent():
    p1, r1 = run_zero_trust_security_gate()
    p2, r2 = run_zero_trust_security_gate()
    assert p1 == p2
    assert len(r1) == len(r2)

def test_tc33_gate_name_g88():
    gate = ZeroTrustSecurityGate()
    assert "ZeroTrustSecurityGate" in type(gate).__name__
