"""
enterprise/slo.py — Enterprise SLO 계약·모니터링·위반 경보 (SP-C.4, ADR-135)

EnterpriseSLOContract: SLA 계약 명세
SLOMonitor: 실시간 SLO 측정
SLOViolationAlert: 위반 감지 및 경보
EnterpriseSLOGate: G73 게이트 실행기
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional


class EnterpriseSLOTier(str, Enum):
    BASIC      = "basic"       # 99.0% 가용성
    STANDARD   = "standard"   # 99.5% 가용성
    PREMIUM    = "premium"    # 99.9% 가용성
    ENTERPRISE = "enterprise" # 99.99% 가용성


class ViolationSeverity(str, Enum):
    WARNING  = "warning"   # SLO < target - 0.5%
    CRITICAL = "critical"  # SLO < target - 1.0%
    BREACH   = "breach"    # SLO < target - 2.0%


@dataclass
class EnterpriseSLOContract:
    """SLA 계약 명세."""
    contract_id: str
    partner_id: str
    tier: EnterpriseSLOTier
    availability_target: float      # 예: 0.999
    latency_p99_ms: int             # P99 지연 목표 (ms)
    throughput_rps: int             # 초당 요청 목표
    data_residency_region: str = "kr"
    custom_clauses: List[str] = field(default_factory=list)

    @property
    def availability_pct(self) -> float:
        return self.availability_target * 100


@dataclass
class SLOMetricSnapshot:
    """단일 시점 SLO 측정값."""
    contract_id: str
    measured_availability: float
    measured_latency_p99_ms: int
    measured_throughput_rps: int
    timestamp: str = ""

    def availability_gap(self, contract: EnterpriseSLOContract) -> float:
        return contract.availability_target - self.measured_availability

    def is_latency_ok(self, contract: EnterpriseSLOContract) -> bool:
        return self.measured_latency_p99_ms <= contract.latency_p99_ms

    def is_throughput_ok(self, contract: EnterpriseSLOContract) -> bool:
        return self.measured_throughput_rps >= contract.throughput_rps


@dataclass
class SLOViolationAlert:
    """SLO 위반 경보."""
    contract_id: str
    severity: ViolationSeverity
    dimension: str          # "availability" | "latency" | "throughput"
    expected: float
    actual: float
    message: str = ""

    def is_breach(self) -> bool:
        return self.severity == ViolationSeverity.BREACH


class SLOMonitor:
    """SLO 모니터 — 측정값 대조 및 위반 감지."""

    def check(
        self,
        contract: EnterpriseSLOContract,
        snapshot: SLOMetricSnapshot,
    ) -> List[SLOViolationAlert]:
        alerts: List[SLOViolationAlert] = []

        # 가용성 체크
        gap = snapshot.availability_gap(contract)
        if gap > 0:
            if gap >= 0.02:
                sev = ViolationSeverity.BREACH
            elif gap >= 0.01:
                sev = ViolationSeverity.CRITICAL
            else:
                sev = ViolationSeverity.WARNING
            alerts.append(SLOViolationAlert(
                contract_id=contract.contract_id,
                severity=sev,
                dimension="availability",
                expected=contract.availability_target,
                actual=snapshot.measured_availability,
                message=f"가용성 {snapshot.measured_availability*100:.3f}% < 목표 {contract.availability_pct:.3f}%",
            ))

        # 지연 체크
        if not snapshot.is_latency_ok(contract):
            delta = snapshot.measured_latency_p99_ms - contract.latency_p99_ms
            sev = ViolationSeverity.BREACH if delta > 500 else (
                ViolationSeverity.CRITICAL if delta > 200 else ViolationSeverity.WARNING
            )
            alerts.append(SLOViolationAlert(
                contract_id=contract.contract_id,
                severity=sev,
                dimension="latency",
                expected=float(contract.latency_p99_ms),
                actual=float(snapshot.measured_latency_p99_ms),
                message=f"P99 지연 {snapshot.measured_latency_p99_ms}ms > 목표 {contract.latency_p99_ms}ms",
            ))

        # 처리량 체크
        if not snapshot.is_throughput_ok(contract):
            sev = ViolationSeverity.CRITICAL
            alerts.append(SLOViolationAlert(
                contract_id=contract.contract_id,
                severity=sev,
                dimension="throughput",
                expected=float(contract.throughput_rps),
                actual=float(snapshot.measured_throughput_rps),
                message=f"처리량 {snapshot.measured_throughput_rps}rps < 목표 {contract.throughput_rps}rps",
            ))

        return alerts


@dataclass
class EnterpriseSLOReport:
    """G73 SLO 게이트 보고서."""
    contracts_checked: int = 0
    violations_found: int = 0
    breaches: int = 0
    gate_passed: bool = False
    alerts: List[SLOViolationAlert] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict:
        return {
            "contracts_checked": self.contracts_checked,
            "violations_found": self.violations_found,
            "breaches": self.breaches,
            "gate_passed": self.gate_passed,
            "summary": self.summary,
        }


class EnterpriseSLOGate:
    """G73 Enterprise SLO 게이트."""

    GATE_ID = "G73"

    def __init__(self):
        self._monitor = SLOMonitor()

    def run(
        self,
        contracts: List[EnterpriseSLOContract],
        snapshots: List[SLOMetricSnapshot],
    ) -> EnterpriseSLOReport:
        """SLO 계약 목록 × 측정값 대조 → 보고서 생성."""
        snap_map = {s.contract_id: s for s in snapshots}
        all_alerts: List[SLOViolationAlert] = []

        for contract in contracts:
            snap = snap_map.get(contract.contract_id)
            if snap is None:
                continue
            alerts = self._monitor.check(contract, snap)
            all_alerts.extend(alerts)

        breaches = [a for a in all_alerts if a.is_breach()]
        gate_passed = len(breaches) == 0

        return EnterpriseSLOReport(
            contracts_checked=len(contracts),
            violations_found=len(all_alerts),
            breaches=len(breaches),
            gate_passed=gate_passed,
            alerts=all_alerts,
            summary=(
                f"SLO 검사 {len(contracts)}건: 위반 {len(all_alerts)}건, "
                f"breach {len(breaches)}건 → {'PASS' if gate_passed else 'FAIL'}"
            ),
        )

    def demo_run(self) -> EnterpriseSLOReport:
        """데모 실행 — 기본 계약 세트로 검증."""
        contracts = [
            EnterpriseSLOContract(
                contract_id="ENT-001",
                partner_id="partner_kakao",
                tier=EnterpriseSLOTier.PREMIUM,
                availability_target=0.999,
                latency_p99_ms=500,
                throughput_rps=100,
            ),
            EnterpriseSLOContract(
                contract_id="ENT-002",
                partner_id="partner_naver",
                tier=EnterpriseSLOTier.ENTERPRISE,
                availability_target=0.9999,
                latency_p99_ms=300,
                throughput_rps=200,
            ),
        ]
        snapshots = [
            SLOMetricSnapshot(
                contract_id="ENT-001",
                measured_availability=0.9992,
                measured_latency_p99_ms=480,
                measured_throughput_rps=110,
            ),
            SLOMetricSnapshot(
                contract_id="ENT-002",
                measured_availability=0.99995,
                measured_latency_p99_ms=290,
                measured_throughput_rps=210,
            ),
        ]
        return self.run(contracts, snapshots)
