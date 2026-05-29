"""
V677 단위 테스트 — Enterprise Tenant Isolation Layer (ADR-139, SP-C.4 안정화 3)
30 TC
"""
import pytest
from literary_system.enterprise.tenant_isolation import (
    EnterpriseTenantStatus, IsolationLevel, EnterpriseTenant,
    EnterpriseIsolationViolation, TenantIsolationReport,
    EnterpriseTenantRegistry, TenantIsolationAuditor, TenantIsolationGate,
)
from literary_system.enterprise.slo import EnterpriseSLOContract, EnterpriseSLOTier
from literary_system.enterprise.revenue import PartnerRevenueContract, RevenueModel


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def registry():
    return EnterpriseTenantRegistry()

@pytest.fixture
def auditor():
    return TenantIsolationAuditor()

@pytest.fixture
def gate():
    return TenantIsolationGate()

def _make_tenant(tenant_id, status=EnterpriseTenantStatus.ACTIVE, level=IsolationLevel.DEDICATED,
                 slo=None, revenue=None):
    return EnterpriseTenant(
        tenant_id=tenant_id, tenant_name=f"Tenant-{tenant_id}",
        status=status, isolation_level=level,
        slo_contract=slo, revenue_contract=revenue,
    )

def _premium_slo(tid):
    return EnterpriseSLOContract(
        contract_id=f"SLO-{tid}", partner_id=tid,
        tier=EnterpriseSLOTier.PREMIUM,
        availability_target=0.999, latency_p99_ms=200, throughput_rps=500,
    )

def _enterprise_slo(tid):
    return EnterpriseSLOContract(
        contract_id=f"SLO-{tid}", partner_id=tid,
        tier=EnterpriseSLOTier.ENTERPRISE,
        availability_target=0.9999, latency_p99_ms=150, throughput_rps=1000,
    )

def _flat_revenue(tid):
    return PartnerRevenueContract(
        contract_id=f"RC-{tid}", partner_id=tid, partner_name=f"P-{tid}",
        model=RevenueModel.FLAT, flat_rate=0.20,
    )


# ── TC01~TC05: 열거형 ──────────────────────────────────────────────────────────

def test_tenant_status_values():
    assert EnterpriseTenantStatus.ACTIVE == "active"
    assert EnterpriseTenantStatus.SUSPENDED == "suspended"
    assert EnterpriseTenantStatus.OFFBOARDED == "offboarded"

def test_isolation_level_values():
    assert IsolationLevel.SHARED == "shared"
    assert IsolationLevel.DEDICATED == "dedicated"
    assert IsolationLevel.STRICT == "strict"

def test_enterprise_tenant_defaults():
    t = _make_tenant("T0")
    assert t.is_active is True
    assert t.has_slo is False
    assert t.has_revenue is False

def test_enterprise_tenant_suspended():
    t = _make_tenant("T9", status=EnterpriseTenantStatus.SUSPENDED)
    assert t.is_active is False

def test_enterprise_tenant_with_slo():
    t = _make_tenant("TX", slo=_premium_slo("TX"))
    assert t.has_slo is True


# ── TC06~TC10: EnterpriseTenantRegistry ───────────────────────────────────────

def test_registry_register_and_get(registry):
    t = _make_tenant("A")
    registry.register(t)
    assert registry.get("A") is t

def test_registry_len(registry):
    registry.register(_make_tenant("B1"))
    registry.register(_make_tenant("B2"))
    assert len(registry) == 2

def test_registry_all_tenants(registry):
    registry.register(_make_tenant("C1"))
    registry.register(_make_tenant("C2", status=EnterpriseTenantStatus.SUSPENDED))
    assert len(registry.all_tenants()) == 2

def test_registry_active_tenants(registry):
    registry.register(_make_tenant("D1"))
    registry.register(_make_tenant("D2", status=EnterpriseTenantStatus.SUSPENDED))
    assert len(registry.active_tenants()) == 1

def test_registry_unregister(registry):
    registry.register(_make_tenant("E"))
    result = registry.unregister("E")
    assert result is True
    assert registry.get("E") is None


# ── TC11~TC18: TenantIsolationAuditor 규칙 검증 ───────────────────────────────

def test_audit_clean_passes(registry, auditor):
    registry.register(_make_tenant("F1", level=IsolationLevel.DEDICATED, slo=_premium_slo("F1")))
    report = auditor.audit(registry)
    assert report.gate_passed is True
    assert report.violation_count == 0

def test_audit_strict_missing_slo_is_error(registry, auditor):
    # STRICT 격리지만 SLO 없음
    registry.register(_make_tenant("G1", level=IsolationLevel.STRICT, revenue=_flat_revenue("G1")))
    report = auditor.audit(registry)
    assert any(v.violation_type == "missing_slo" for v in report.violations)
    assert report.gate_passed is False

def test_audit_strict_missing_revenue_is_warning(registry, auditor):
    # STRICT 격리 + SLO 있지만 Revenue 없음 → warning만
    registry.register(_make_tenant("H1", level=IsolationLevel.STRICT, slo=_enterprise_slo("H1")))
    report = auditor.audit(registry)
    warn = [v for v in report.violations if v.severity == "warning"]
    assert len(warn) >= 1
    # gate는 error 없으므로 PASS
    assert report.gate_passed is True

def test_audit_enterprise_slo_shared_is_error(registry, auditor):
    # ENTERPRISE SLO + SHARED 격리 → error
    registry.register(_make_tenant("I1", level=IsolationLevel.SHARED, slo=_enterprise_slo("I1")))
    report = auditor.audit(registry)
    assert any(v.violation_type == "isolation_mismatch" for v in report.violations)
    assert report.gate_passed is False

def test_audit_suspended_tenant_skipped(registry, auditor):
    # SUSPENDED 테넌트는 감사 제외 (STRICT 격리지만 SUSPENDED이므로 위반 없음)
    registry.register(_make_tenant("J1", status=EnterpriseTenantStatus.SUSPENDED,
                                   level=IsolationLevel.STRICT))
    report = auditor.audit(registry)
    assert report.gate_passed is True
    assert report.violation_count == 0

def test_audit_counts(registry, auditor):
    registry.register(_make_tenant("K1", slo=_premium_slo("K1")))
    registry.register(_make_tenant("K2", revenue=_flat_revenue("K2")))
    registry.register(_make_tenant("K3", status=EnterpriseTenantStatus.SUSPENDED))
    report = auditor.audit(registry)
    assert report.tenants_total == 3
    assert report.tenants_active == 2
    assert report.tenants_with_slo == 1
    assert report.tenants_with_revenue == 1

def test_isolation_violation_fields():
    v = EnterpriseIsolationViolation(tenant_id="T1", violation_type="missing_slo",
                           description="test", severity="error")
    assert v.severity == "error"
    assert v.tenant_id == "T1"

def test_audit_no_tenants(registry, auditor):
    report = auditor.audit(registry)
    assert report.tenants_total == 0
    assert report.gate_passed is True


# ── TC19~TC24: TenantIsolationGate demo_run ───────────────────────────────────

def test_gate_demo_run_returns_report(gate):
    report = gate.demo_run()
    assert isinstance(report, TenantIsolationReport)

def test_gate_demo_run_4_tenants(gate):
    report = gate.demo_run()
    assert report.tenants_total == 4

def test_gate_demo_run_3_active(gate):
    report = gate.demo_run()
    assert report.tenants_active == 3

def test_gate_demo_run_gate_passed(gate):
    report = gate.demo_run()
    assert report.gate_passed is True, [v.description for v in report.violations]

def test_gate_demo_run_no_error_violations(gate):
    report = gate.demo_run()
    assert len(report.error_violations) == 0

def test_gate_demo_run_slo_revenue_counts(gate):
    report = gate.demo_run()
    # T1~T3 모두 SLO 있음 (4번은 SUSPENDED)
    assert report.tenants_with_slo == 3
    assert report.tenants_with_revenue == 3


# ── TC25~TC30: GATE_ID + 패키지 노출 ─────────────────────────────────────────

def test_tenant_isolation_gate_id():
    assert TenantIsolationGate.GATE_ID == "G76"

def test_report_error_violations_property():
    violations = [
        EnterpriseIsolationViolation("T1", "t1", "d1", severity="error"),
        EnterpriseIsolationViolation("T2", "t2", "d2", severity="warning"),
    ]
    report = TenantIsolationReport(
        tenants_total=2, tenants_active=2,
        tenants_with_slo=0, tenants_with_revenue=0,
        violations=violations, gate_passed=False,
    )
    assert len(report.error_violations) == 1

def test_enterprise_package_exports_tenant():
    from literary_system.enterprise import TenantIsolationGate as TIG
    assert TIG is not None

def test_release_gate_g76():
    from literary_system.gates.release_gate import GATES
    gate_ids = [g[0] for g in GATES]
    assert "tenant_isolation_g76" in gate_ids

def test_registry_get_missing_returns_none(registry):
    assert registry.get("NOT_EXIST") is None

def test_registry_overwrite(registry):
    t1 = _make_tenant("Z")
    t2 = _make_tenant("Z", status=EnterpriseTenantStatus.SUSPENDED)
    registry.register(t1)
    registry.register(t2)
    assert registry.get("Z").is_active is False
