"""
Enterprise Tenant Isolation Layer (V677, SP-C.4 안정화 3)
테넌트별 SLO 계약·Revenue 계약 격리 관리 + TenantIsolationGate

ADR-139
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from .slo import EnterpriseSLOContract, EnterpriseSLOTier
from .revenue import PartnerRevenueContract, RevenueModel


# ── Enums ──────────────────────────────────────────────────────────────────────

class EnterpriseTenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    OFFBOARDED = "offboarded"


class IsolationLevel(str, Enum):
    SHARED = "shared"      # 공유 리소스
    DEDICATED = "dedicated"  # 전용 리소스
    STRICT = "strict"       # 완전 격리


# ── Dataclasses ────────────────────────────────────────────────────────────────

@dataclass
class EnterpriseTenant:
    """단일 Enterprise 테넌트 정보."""
    tenant_id: str
    tenant_name: str
    status: EnterpriseTenantStatus = EnterpriseTenantStatus.ACTIVE
    isolation_level: IsolationLevel = IsolationLevel.DEDICATED
    slo_contract: Optional[EnterpriseSLOContract] = None
    revenue_contract: Optional[PartnerRevenueContract] = None
    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def has_slo(self) -> bool:
        return self.slo_contract is not None

    @property
    def has_revenue(self) -> bool:
        return self.revenue_contract is not None

    @property
    def is_active(self) -> bool:
        return self.status == EnterpriseTenantStatus.ACTIVE


@dataclass
class EnterpriseIsolationViolation:
    """격리 위반 사항."""
    tenant_id: str
    violation_type: str
    description: str
    severity: str = "warning"  # warning | error


@dataclass
class TenantIsolationReport:
    """테넌트 격리 감사 보고서."""
    tenants_total: int
    tenants_active: int
    tenants_with_slo: int
    tenants_with_revenue: int
    violations: List[EnterpriseIsolationViolation] = field(default_factory=list)
    gate_passed: bool = True

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    @property
    def error_violations(self) -> List[EnterpriseIsolationViolation]:
        return [v for v in self.violations if v.severity == "error"]


# ── TenantRegistry ─────────────────────────────────────────────────────────────

class EnterpriseTenantRegistry:
    """Enterprise 테넌트 등록 및 조회."""

    def __init__(self):
        self._tenants: Dict[str, EnterpriseTenant] = {}

    def register(self, tenant: EnterpriseTenant) -> None:
        self._tenants[tenant.tenant_id] = tenant

    def get(self, tenant_id: str) -> Optional[EnterpriseTenant]:
        return self._tenants.get(tenant_id)

    def all_tenants(self) -> List[EnterpriseTenant]:
        return list(self._tenants.values())

    def active_tenants(self) -> List[EnterpriseTenant]:
        return [t for t in self._tenants.values() if t.is_active]

    def unregister(self, tenant_id: str) -> bool:
        if tenant_id in self._tenants:
            del self._tenants[tenant_id]
            return True
        return False

    def __len__(self) -> int:
        return len(self._tenants)


# ── IsolationAuditor ───────────────────────────────────────────────────────────

class TenantIsolationAuditor:
    """테넌트 격리 정책 감사."""

    def audit(self, registry: EnterpriseTenantRegistry) -> TenantIsolationReport:
        tenants = registry.all_tenants()
        active = registry.active_tenants()
        with_slo = [t for t in tenants if t.has_slo]
        with_revenue = [t for t in tenants if t.has_revenue]

        violations: List[EnterpriseIsolationViolation] = []

        for tenant in active:
            # 규칙 1: STRICT 격리 테넌트는 SLO + Revenue 모두 필요
            if tenant.isolation_level == IsolationLevel.STRICT:
                if not tenant.has_slo:
                    violations.append(EnterpriseIsolationViolation(
                        tenant_id=tenant.tenant_id,
                        violation_type="missing_slo",
                        description=f"STRICT 격리 테넌트 {tenant.tenant_id}에 SLO 계약 없음",
                        severity="error",
                    ))
                if not tenant.has_revenue:
                    violations.append(EnterpriseIsolationViolation(
                        tenant_id=tenant.tenant_id,
                        violation_type="missing_revenue",
                        description=f"STRICT 격리 테넌트 {tenant.tenant_id}에 Revenue 계약 없음",
                        severity="warning",
                    ))
            # 규칙 2: ENTERPRISE SLO 티어 테넌트는 DEDICATED 이상 격리 필요
            if tenant.has_slo and tenant.slo_contract.tier == EnterpriseSLOTier.ENTERPRISE:
                if tenant.isolation_level == IsolationLevel.SHARED:
                    violations.append(EnterpriseIsolationViolation(
                        tenant_id=tenant.tenant_id,
                        violation_type="isolation_mismatch",
                        description=f"ENTERPRISE SLO 티어 테넌트 {tenant.tenant_id}가 SHARED 격리 사용 중",
                        severity="error",
                    ))

        # 에러 위반이 있으면 gate_passed = False
        gate_passed = len([v for v in violations if v.severity == "error"]) == 0

        return TenantIsolationReport(
            tenants_total=len(tenants),
            tenants_active=len(active),
            tenants_with_slo=len(with_slo),
            tenants_with_revenue=len(with_revenue),
            violations=violations,
            gate_passed=gate_passed,
        )


# ── TenantIsolationGate ────────────────────────────────────────────────────────

class TenantIsolationGate:
    """Enterprise 테넌트 격리 게이트 (SP-C.4 안정화 3)."""

    GATE_ID = "G76"

    def __init__(
        self,
        registry: Optional[EnterpriseTenantRegistry] = None,
        auditor: Optional[TenantIsolationAuditor] = None,
    ):
        self.registry = registry or EnterpriseTenantRegistry()
        self.auditor = auditor or TenantIsolationAuditor()

    def demo_run(self) -> TenantIsolationReport:
        """
        데모: 4 테넌트 등록 (모두 정책 준수)
        - T1: NovelAI (DEDICATED, PREMIUM SLO, FLAT Revenue)
        - T2: Sudowrite (DEDICATED, ENTERPRISE SLO, TIERED Revenue)
        - T3: NolanAI (STRICT, ENTERPRISE SLO, USAGE_BASED Revenue)
        - T4: Jenova (SHARED, BASIC SLO, 계약 없음) — SUSPENDED
        """
        from .slo import EnterpriseSLOContract
        from .revenue import PartnerRevenueContract, RevenueModel, RevenueTier

        # T1
        self.registry.register(EnterpriseTenant(
            tenant_id="T1", tenant_name="NovelAI",
            status=EnterpriseTenantStatus.ACTIVE,
            isolation_level=IsolationLevel.DEDICATED,
            slo_contract=EnterpriseSLOContract(
                contract_id="SLO-T1", partner_id="T1",
                tier=EnterpriseSLOTier.PREMIUM,
                availability_target=0.999, latency_p99_ms=200, throughput_rps=500,
            ),
            revenue_contract=PartnerRevenueContract(
                contract_id="RC-T1", partner_id="T1", partner_name="NovelAI",
                model=RevenueModel.FLAT, flat_rate=0.20,
            ),
        ))
        # T2
        self.registry.register(EnterpriseTenant(
            tenant_id="T2", tenant_name="Sudowrite",
            status=EnterpriseTenantStatus.ACTIVE,
            isolation_level=IsolationLevel.DEDICATED,
            slo_contract=EnterpriseSLOContract(
                contract_id="SLO-T2", partner_id="T2",
                tier=EnterpriseSLOTier.ENTERPRISE,
                availability_target=0.9999, latency_p99_ms=150, throughput_rps=1000,
            ),
            revenue_contract=PartnerRevenueContract(
                contract_id="RC-T2", partner_id="T2", partner_name="Sudowrite",
                model=RevenueModel.TIERED,
                tiers=[RevenueTier(0, 2000, 0.25), RevenueTier(2000, -1, 0.18)],
            ),
        ))
        # T3 — STRICT + ENTERPRISE: 모두 완비
        self.registry.register(EnterpriseTenant(
            tenant_id="T3", tenant_name="NolanAI",
            status=EnterpriseTenantStatus.ACTIVE,
            isolation_level=IsolationLevel.STRICT,
            slo_contract=EnterpriseSLOContract(
                contract_id="SLO-T3", partner_id="T3",
                tier=EnterpriseSLOTier.ENTERPRISE,
                availability_target=0.9999, latency_p99_ms=100, throughput_rps=2000,
            ),
            revenue_contract=PartnerRevenueContract(
                contract_id="RC-T3", partner_id="T3", partner_name="NolanAI",
                model=RevenueModel.USAGE_BASED, usage_rate=0.04,
            ),
        ))
        # T4 — SUSPENDED, 검사 제외
        self.registry.register(EnterpriseTenant(
            tenant_id="T4", tenant_name="Jenova",
            status=EnterpriseTenantStatus.SUSPENDED,
            isolation_level=IsolationLevel.SHARED,
        ))

        return self.auditor.audit(self.registry)
