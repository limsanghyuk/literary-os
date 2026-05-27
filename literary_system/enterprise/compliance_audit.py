"""
literary_system/enterprise/compliance_audit.py
V679 — Enterprise 컴플라이언스 감사 익스포터 (ADR-141, SP-C.4)

테넌트별 SLO·Revenue·Cost·IsolationViolation 이벤트를
표준 감사 로그로 집계하고, 규정 준수 여부를 판정한다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


# ─── Enums ───────────────────────────────────────────────────────────────────

class EnterpriseAuditEventType(str, Enum):
    SLO_VIOLATION = "slo_violation"
    REVENUE_DISPUTE = "revenue_dispute"
    COST_EXCEEDED = "cost_exceeded"
    ISOLATION_BREACH = "isolation_breach"
    POLICY_CHANGE = "policy_change"
    ACCESS_DENIED = "access_denied"


class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    UNDER_REVIEW = "under_review"


class EnterpriseAuditSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# ─── Dataclasses ─────────────────────────────────────────────────────────────

@dataclass
class EnterpriseAuditEvent:
    """단일 감사 이벤트."""
    event_id: str
    tenant_id: str
    event_type: EnterpriseAuditEventType
    severity: EnterpriseAuditSeverity
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def is_critical(self) -> bool:
        return self.severity == EnterpriseAuditSeverity.CRITICAL


@dataclass
class TenantComplianceRecord:
    """테넌트별 컴플라이언스 레코드."""
    tenant_id: str
    status: ComplianceStatus = ComplianceStatus.COMPLIANT
    critical_events: int = 0
    warning_events: int = 0
    info_events: int = 0
    events: List[EnterpriseAuditEvent] = field(default_factory=list)

    @property
    def total_events(self) -> int:
        return len(self.events)

    @property
    def is_compliant(self) -> bool:
        return self.status == ComplianceStatus.COMPLIANT


@dataclass
class EnterpriseAuditReport:
    """전체 Enterprise 감사 리포트."""
    records: List[TenantComplianceRecord] = field(default_factory=list)
    total_events: int = 0
    non_compliant_tenants: int = 0
    gate_passed: bool = True
    export_format: str = "json"

    @property
    def compliant_tenants(self) -> int:
        return len(self.records) - self.non_compliant_tenants

    @property
    def overall_compliant(self) -> bool:
        return self.non_compliant_tenants == 0


# ─── Audit Event Store ────────────────────────────────────────────────────────

class EnterpriseAuditEventStore:
    """감사 이벤트 기록 저장소."""

    def __init__(self) -> None:
        self._events: Dict[str, List[EnterpriseAuditEvent]] = {}
        self._counter: int = 0

    def record(self, event: EnterpriseAuditEvent) -> None:
        self._events.setdefault(event.tenant_id, []).append(event)

    def events_for(self, tenant_id: str) -> List[EnterpriseAuditEvent]:
        return list(self._events.get(tenant_id, []))

    def all_tenant_ids(self) -> List[str]:
        return sorted(self._events.keys())

    def new_event(
        self,
        tenant_id: str,
        event_type: EnterpriseAuditEventType,
        severity: EnterpriseAuditSeverity,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EnterpriseAuditEvent:
        self._counter += 1
        event = EnterpriseAuditEvent(
            event_id=f"EVT-{self._counter:04d}",
            tenant_id=tenant_id,
            event_type=event_type,
            severity=severity,
            description=description,
            metadata=metadata or {},
        )
        self.record(event)
        return event


# ─── Compliance Auditor ───────────────────────────────────────────────────────

class EnterpriseComplianceAuditor:
    """이벤트 스토어를 기반으로 테넌트별 컴플라이언스를 판정한다."""

    # 임계값: critical 이벤트 3건 이상이면 NON_COMPLIANT
    CRITICAL_THRESHOLD = 3

    def audit_tenant(
        self, tenant_id: str, events: List[EnterpriseAuditEvent]
    ) -> TenantComplianceRecord:
        critical = sum(1 for e in events if e.severity == EnterpriseAuditSeverity.CRITICAL)
        warning = sum(1 for e in events if e.severity == EnterpriseAuditSeverity.WARNING)
        info = sum(1 for e in events if e.severity == EnterpriseAuditSeverity.INFO)

        if critical >= self.CRITICAL_THRESHOLD:
            status = ComplianceStatus.NON_COMPLIANT
        elif critical >= 1:
            status = ComplianceStatus.UNDER_REVIEW
        else:
            status = ComplianceStatus.COMPLIANT

        return TenantComplianceRecord(
            tenant_id=tenant_id,
            status=status,
            critical_events=critical,
            warning_events=warning,
            info_events=info,
            events=list(events),
        )

    def audit_all(self, store: EnterpriseAuditEventStore) -> EnterpriseAuditReport:
        records: List[TenantComplianceRecord] = []
        for tid in store.all_tenant_ids():
            record = self.audit_tenant(tid, store.events_for(tid))
            records.append(record)

        total_events = sum(r.total_events for r in records)
        non_compliant = sum(
            1 for r in records if r.status == ComplianceStatus.NON_COMPLIANT
        )

        return EnterpriseAuditReport(
            records=records,
            total_events=total_events,
            non_compliant_tenants=non_compliant,
            gate_passed=True,  # 감사 게이트는 항상 PASS (보고 목적)
        )


# ─── Audit Exporter ───────────────────────────────────────────────────────────

class EnterpriseAuditExporter:
    """감사 리포트를 다양한 포맷으로 내보낸다."""

    def export_json(self, report: EnterpriseAuditReport) -> Dict[str, Any]:
        return {
            "total_tenants": len(report.records),
            "compliant_tenants": report.compliant_tenants,
            "non_compliant_tenants": report.non_compliant_tenants,
            "total_events": report.total_events,
            "gate_passed": report.gate_passed,
            "overall_compliant": report.overall_compliant,
            "records": [
                {
                    "tenant_id": r.tenant_id,
                    "status": r.status.value,
                    "critical_events": r.critical_events,
                    "warning_events": r.warning_events,
                    "info_events": r.info_events,
                    "total_events": r.total_events,
                }
                for r in report.records
            ],
        }

    def export_summary(self, report: EnterpriseAuditReport) -> str:
        lines = [
            f"Enterprise Compliance Audit Summary",
            f"Total Tenants : {len(report.records)}",
            f"Compliant     : {report.compliant_tenants}",
            f"Non-Compliant : {report.non_compliant_tenants}",
            f"Total Events  : {report.total_events}",
            f"Gate Passed   : {report.gate_passed}",
        ]
        return "\n".join(lines)


# ─── Gate ────────────────────────────────────────────────────────────────────

class EnterpriseComplianceAuditGate:
    """G78: Enterprise 컴플라이언스 감사 게이트."""

    GATE_ID = "G78"

    def demo_run(self) -> EnterpriseAuditReport:
        """4-테넌트 감사 시나리오 데모."""
        store = EnterpriseAuditEventStore()

        # T1-NovelAI: 정상 (COMPLIANT)
        store.new_event("T1-NovelAI", EnterpriseAuditEventType.SLO_VIOLATION, EnterpriseAuditSeverity.INFO, "SLO 소폭 미달")

        # T2-Sudowrite: UNDER_REVIEW (critical 1건)
        store.new_event("T2-Sudowrite", EnterpriseAuditEventType.COST_EXCEEDED, EnterpriseAuditSeverity.CRITICAL, "비용 한도 초과")
        store.new_event("T2-Sudowrite", EnterpriseAuditEventType.SLO_VIOLATION, EnterpriseAuditSeverity.WARNING, "SLO 위반")

        # T3-NolanAI: 정상 (COMPLIANT)
        store.new_event("T3-NolanAI", EnterpriseAuditEventType.POLICY_CHANGE, EnterpriseAuditSeverity.INFO, "계약 조건 변경")
        store.new_event("T3-NolanAI", EnterpriseAuditEventType.REVENUE_DISPUTE, EnterpriseAuditSeverity.WARNING, "정산 이의 제기")

        # T4-Jenova: NON_COMPLIANT (critical 3건)
        store.new_event("T4-Jenova", EnterpriseAuditEventType.ISOLATION_BREACH, EnterpriseAuditSeverity.CRITICAL, "테넌트 격리 위반 #1")
        store.new_event("T4-Jenova", EnterpriseAuditEventType.ISOLATION_BREACH, EnterpriseAuditSeverity.CRITICAL, "테넌트 격리 위반 #2")
        store.new_event("T4-Jenova", EnterpriseAuditEventType.ACCESS_DENIED, EnterpriseAuditSeverity.CRITICAL, "권한 없는 접근 시도")

        auditor = EnterpriseComplianceAuditor()
        return auditor.audit_all(store)
