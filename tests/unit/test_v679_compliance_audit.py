"""
tests/unit/test_v679_compliance_audit.py
V679 — Enterprise 컴플라이언스 감사 단위 테스트 (30 TC)
"""
import pytest
from literary_system.enterprise.compliance_audit import (
    EnterpriseAuditEventType, ComplianceStatus, EnterpriseAuditSeverity,
    EnterpriseAuditEvent, TenantComplianceRecord,
    EnterpriseAuditReport, EnterpriseAuditEventStore,
    EnterpriseComplianceAuditor, EnterpriseAuditExporter,
    EnterpriseComplianceAuditGate,
)


# ─── Enums ───────────────────────────────────────────────────────────────────

def test_audit_event_types():
    assert EnterpriseAuditEventType.SLO_VIOLATION == "slo_violation"
    assert EnterpriseAuditEventType.COST_EXCEEDED == "cost_exceeded"
    assert EnterpriseAuditEventType.ISOLATION_BREACH == "isolation_breach"

def test_compliance_status_values():
    assert ComplianceStatus.COMPLIANT == "compliant"
    assert ComplianceStatus.NON_COMPLIANT == "non_compliant"
    assert ComplianceStatus.UNDER_REVIEW == "under_review"

def test_audit_severity_values():
    assert EnterpriseAuditSeverity.CRITICAL == "critical"
    assert EnterpriseAuditSeverity.WARNING == "warning"
    assert EnterpriseAuditSeverity.INFO == "info"


# ─── EnterpriseAuditEvent ─────────────────────────────────────────────────────

def test_audit_event_is_critical():
    e = EnterpriseAuditEvent("E1", "T1", EnterpriseAuditEventType.SLO_VIOLATION, EnterpriseAuditSeverity.CRITICAL, "test")
    assert e.is_critical is True

def test_audit_event_not_critical():
    e = EnterpriseAuditEvent("E1", "T1", EnterpriseAuditEventType.SLO_VIOLATION, EnterpriseAuditSeverity.INFO, "test")
    assert e.is_critical is False


# ─── TenantComplianceRecord ───────────────────────────────────────────────────

def test_record_is_compliant():
    r = TenantComplianceRecord("T1", ComplianceStatus.COMPLIANT, 0, 0, 1)
    assert r.is_compliant is True

def test_record_non_compliant():
    r = TenantComplianceRecord("T1", ComplianceStatus.NON_COMPLIANT, 3, 0, 0)
    assert r.is_compliant is False

def test_record_total_events():
    events = [
        EnterpriseAuditEvent("E1", "T1", EnterpriseAuditEventType.COST_EXCEEDED, EnterpriseAuditSeverity.INFO, "x"),
        EnterpriseAuditEvent("E2", "T1", EnterpriseAuditEventType.ACCESS_DENIED, EnterpriseAuditSeverity.WARNING, "y"),
    ]
    r = TenantComplianceRecord("T1", events=events)
    assert r.total_events == 2


# ─── EnterpriseAuditEventStore ────────────────────────────────────────────────

def test_store_record_and_retrieve():
    store = EnterpriseAuditEventStore()
    store.new_event("T1", EnterpriseAuditEventType.SLO_VIOLATION, EnterpriseAuditSeverity.INFO, "test")
    assert len(store.events_for("T1")) == 1

def test_store_empty_tenant():
    store = EnterpriseAuditEventStore()
    assert store.events_for("T_MISSING") == []

def test_store_multiple_tenants():
    store = EnterpriseAuditEventStore()
    store.new_event("T1", EnterpriseAuditEventType.SLO_VIOLATION, EnterpriseAuditSeverity.INFO, "a")
    store.new_event("T2", EnterpriseAuditEventType.COST_EXCEEDED, EnterpriseAuditSeverity.WARNING, "b")
    assert "T1" in store.all_tenant_ids()
    assert "T2" in store.all_tenant_ids()

def test_store_event_id_sequential():
    store = EnterpriseAuditEventStore()
    e1 = store.new_event("T1", EnterpriseAuditEventType.SLO_VIOLATION, EnterpriseAuditSeverity.INFO, "a")
    e2 = store.new_event("T1", EnterpriseAuditEventType.COST_EXCEEDED, EnterpriseAuditSeverity.WARNING, "b")
    assert e1.event_id != e2.event_id


# ─── EnterpriseComplianceAuditor ─────────────────────────────────────────────

def test_auditor_compliant_no_critical():
    auditor = EnterpriseComplianceAuditor()
    events = [
        EnterpriseAuditEvent("E1", "T1", EnterpriseAuditEventType.SLO_VIOLATION, EnterpriseAuditSeverity.INFO, "x"),
        EnterpriseAuditEvent("E2", "T1", EnterpriseAuditEventType.SLO_VIOLATION, EnterpriseAuditSeverity.WARNING, "y"),
    ]
    rec = auditor.audit_tenant("T1", events)
    assert rec.status == ComplianceStatus.COMPLIANT

def test_auditor_under_review_one_critical():
    auditor = EnterpriseComplianceAuditor()
    events = [
        EnterpriseAuditEvent("E1", "T1", EnterpriseAuditEventType.ISOLATION_BREACH, EnterpriseAuditSeverity.CRITICAL, "breach"),
    ]
    rec = auditor.audit_tenant("T1", events)
    assert rec.status == ComplianceStatus.UNDER_REVIEW

def test_auditor_non_compliant_three_critical():
    auditor = EnterpriseComplianceAuditor()
    events = [
        EnterpriseAuditEvent(f"E{i}", "T1", EnterpriseAuditEventType.ISOLATION_BREACH, EnterpriseAuditSeverity.CRITICAL, f"b{i}")
        for i in range(3)
    ]
    rec = auditor.audit_tenant("T1", events)
    assert rec.status == ComplianceStatus.NON_COMPLIANT

def test_auditor_all_counts():
    store = EnterpriseAuditEventStore()
    store.new_event("T1", EnterpriseAuditEventType.SLO_VIOLATION, EnterpriseAuditSeverity.INFO, "a")
    store.new_event("T2", EnterpriseAuditEventType.COST_EXCEEDED, EnterpriseAuditSeverity.CRITICAL, "b")
    store.new_event("T2", EnterpriseAuditEventType.COST_EXCEEDED, EnterpriseAuditSeverity.CRITICAL, "c")
    store.new_event("T2", EnterpriseAuditEventType.COST_EXCEEDED, EnterpriseAuditSeverity.CRITICAL, "d")
    auditor = EnterpriseComplianceAuditor()
    report = auditor.audit_all(store)
    assert report.non_compliant_tenants == 1
    assert report.total_events == 4


# ─── EnterpriseAuditExporter ─────────────────────────────────────────────────

def test_exporter_json_keys():
    gate = EnterpriseComplianceAuditGate()
    report = gate.demo_run()
    exporter = EnterpriseAuditExporter()
    data = exporter.export_json(report)
    assert "total_tenants" in data
    assert "non_compliant_tenants" in data
    assert "records" in data

def test_exporter_summary_contains_tenants():
    gate = EnterpriseComplianceAuditGate()
    report = gate.demo_run()
    exporter = EnterpriseAuditExporter()
    summary = exporter.export_summary(report)
    assert "Total Tenants" in summary
    assert "Non-Compliant" in summary


# ─── EnterpriseComplianceAuditGate ───────────────────────────────────────────

def test_gate_id():
    assert EnterpriseComplianceAuditGate.GATE_ID == "G78"

def test_gate_demo_returns_report():
    gate = EnterpriseComplianceAuditGate()
    report = gate.demo_run()
    assert isinstance(report, EnterpriseAuditReport)

def test_gate_demo_4_tenants():
    report = EnterpriseComplianceAuditGate().demo_run()
    assert len(report.records) == 4

def test_gate_demo_gate_passed():
    report = EnterpriseComplianceAuditGate().demo_run()
    assert report.gate_passed is True

def test_gate_demo_one_non_compliant():
    report = EnterpriseComplianceAuditGate().demo_run()
    assert report.non_compliant_tenants == 1

def test_gate_demo_t4_non_compliant():
    report = EnterpriseComplianceAuditGate().demo_run()
    jenova = next(r for r in report.records if "Jenova" in r.tenant_id)
    assert jenova.status == ComplianceStatus.NON_COMPLIANT
    assert jenova.critical_events == 3

def test_gate_demo_t2_under_review():
    report = EnterpriseComplianceAuditGate().demo_run()
    sudo = next(r for r in report.records if "Sudowrite" in r.tenant_id)
    assert sudo.status == ComplianceStatus.UNDER_REVIEW

def test_gate_demo_t1_compliant():
    report = EnterpriseComplianceAuditGate().demo_run()
    novel = next(r for r in report.records if "NovelAI" in r.tenant_id)
    assert novel.status == ComplianceStatus.COMPLIANT

def test_enterprise_exports():
    from literary_system.enterprise import EnterpriseComplianceAuditGate as ECAG
    assert ECAG.GATE_ID == "G78"

def test_release_gate_g78():
    from literary_system.gates.release_gate import _gate_enterprise_compliance_audit_g78
    result = _gate_enterprise_compliance_audit_g78()
    assert result["passed"] is True
    assert result["gate"] == "G78"
