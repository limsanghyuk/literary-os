"""
enterprise/revenue.py — 파트너 Revenue Share 모델 및 인보이스 생성 (SP-C.4, ADR-136)

RevenueModel: 수익 배분 정책 (FLAT / TIERED / USAGE_BASED)
PartnerRevenueContract: 파트너별 수익 계약
RevenueInvoice: 월별 인보이스 생성
RevenueGate: G74 게이트 실행기
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional
import datetime


class RevenueModel(str, Enum):
    FLAT        = "flat"          # 고정 수수료
    TIERED      = "tiered"        # 구간별 요율
    USAGE_BASED = "usage_based"   # 사용량 기반


class InvoiceStatus(str, Enum):
    DRAFT   = "draft"
    ISSUED  = "issued"
    PAID    = "paid"
    OVERDUE = "overdue"


@dataclass
class RevenueTier:
    """구간별 수익 요율"""
    min_amount: float   # 구간 하한 (USD)
    max_amount: float   # 구간 상한 (USD, -1 = unlimited)
    rate: float         # 요율 (0.0 ~ 1.0)


@dataclass
class PartnerRevenueContract:
    """파트너 수익 배분 계약"""
    contract_id:   str
    partner_id:    str
    partner_name:  str
    model:         RevenueModel
    flat_rate:     float = 0.0          # FLAT 모드: 고정 요율
    tiers:         List[RevenueTier] = field(default_factory=list)  # TIERED 모드
    usage_rate:    float = 0.0          # USAGE_BASED 모드: 단위당 요율
    currency:      str = "USD"
    active:        bool = True


@dataclass
class RevenueInvoice:
    """월별 수익 인보이스"""
    invoice_id:       str
    contract_id:      str
    partner_id:       str
    period_start:     str   # YYYY-MM-DD
    period_end:       str   # YYYY-MM-DD
    gross_revenue:    float
    partner_share:    float
    platform_share:   float
    currency:         str
    status:           InvoiceStatus
    line_items:       List[Dict] = field(default_factory=list)


@dataclass
class RevenueReport:
    """G74 게이트 결과 보고서"""
    gate_id:           str = "G74"
    gate_passed:       bool = False
    total_contracts:   int = 0
    total_invoices:    int = 0
    total_gross:       float = 0.0
    total_partner_pay: float = 0.0
    details:           List[Dict] = field(default_factory=list)
    errors:            List[str] = field(default_factory=list)


class RevenueCalculator:
    """수익 배분 계산기"""

    @staticmethod
    def calculate_partner_share(
        contract: PartnerRevenueContract,
        gross_revenue: float,
        usage_units: float = 0.0,
    ) -> float:
        """파트너 수익 분배금 계산"""
        if not contract.active:
            return 0.0

        if contract.model == RevenueModel.FLAT:
            return gross_revenue * contract.flat_rate

        elif contract.model == RevenueModel.TIERED:
            if not contract.tiers:
                return 0.0
            total = 0.0
            remaining = gross_revenue
            # 구간 정렬 (min_amount 오름차순)
            sorted_tiers = sorted(contract.tiers, key=lambda t: t.min_amount)
            for tier in sorted_tiers:
                tier_max = tier.max_amount if tier.max_amount >= 0 else float("inf")
                tier_width = tier_max - tier.min_amount
                applicable = min(remaining, tier_width)
                if applicable <= 0:
                    break
                total += applicable * tier.rate
                remaining -= applicable
                if remaining <= 0:
                    break
            return total

        elif contract.model == RevenueModel.USAGE_BASED:
            return usage_units * contract.usage_rate

        return 0.0


class RevenueInvoiceGenerator:
    """인보이스 생성기"""

    def __init__(self) -> None:
        self._invoice_counter = 0

    def generate(
        self,
        contract: PartnerRevenueContract,
        gross_revenue: float,
        period_start: str,
        period_end: str,
        usage_units: float = 0.0,
    ) -> RevenueInvoice:
        self._invoice_counter += 1
        partner_share = RevenueCalculator.calculate_partner_share(
            contract, gross_revenue, usage_units
        )
        platform_share = gross_revenue - partner_share
        return RevenueInvoice(
            invoice_id    = f"INV-{self._invoice_counter:04d}",
            contract_id   = contract.contract_id,
            partner_id    = contract.partner_id,
            period_start  = period_start,
            period_end    = period_end,
            gross_revenue = gross_revenue,
            partner_share = round(partner_share, 2),
            platform_share= round(platform_share, 2),
            currency      = contract.currency,
            status        = InvoiceStatus.ISSUED,
            line_items    = [
                {"type": "gross",    "amount": gross_revenue},
                {"type": "partner",  "amount": round(partner_share, 2)},
                {"type": "platform", "amount": round(platform_share, 2)},
            ],
        )


class RevenueGate:
    """G74: Revenue Share 계약 및 인보이스 검증 게이트"""

    GATE_ID = "G74"

    def run(
        self,
        contracts: List[PartnerRevenueContract],
        invoices:  List[RevenueInvoice],
    ) -> RevenueReport:
        report = RevenueReport(
            gate_id         = self.GATE_ID,
            total_contracts = len(contracts),
            total_invoices  = len(invoices),
        )

        # 계약 검증
        for c in contracts:
            if not c.contract_id or not c.partner_id:
                report.errors.append(f"계약 ID/파트너 ID 누락: {c}")
                continue
            if c.model == RevenueModel.TIERED and not c.tiers:
                report.errors.append(f"TIERED 계약에 tiers 없음: {c.contract_id}")
                continue

        # 인보이스 검증
        contract_map = {c.contract_id: c for c in contracts}
        total_gross = 0.0
        total_partner = 0.0
        for inv in invoices:
            if inv.contract_id not in contract_map:
                report.errors.append(f"인보이스 {inv.invoice_id}: 계약 없음 ({inv.contract_id})")
                continue
            if inv.gross_revenue < 0:
                report.errors.append(f"인보이스 {inv.invoice_id}: 음수 매출")
                continue
            if abs(inv.partner_share + inv.platform_share - inv.gross_revenue) > 0.01:
                report.errors.append(
                    f"인보이스 {inv.invoice_id}: 배분 합계 불일치 "
                    f"({inv.partner_share}+{inv.platform_share} ≠ {inv.gross_revenue})"
                )
                continue
            total_gross   += inv.gross_revenue
            total_partner += inv.partner_share
            report.details.append({
                "invoice_id":    inv.invoice_id,
                "partner_id":    inv.partner_id,
                "gross":         inv.gross_revenue,
                "partner_share": inv.partner_share,
                "status":        inv.status.value,
            })

        report.total_gross       = round(total_gross, 2)
        report.total_partner_pay = round(total_partner, 2)
        report.gate_passed       = len(report.errors) == 0 and len(invoices) > 0
        return report

    def demo_run(self) -> RevenueReport:
        """데모: FLAT + TIERED 계약 각 1건, 인보이스 2건 생성"""
        gen = RevenueInvoiceGenerator()

        # 계약 1: FLAT 20%
        c1 = PartnerRevenueContract(
            contract_id="RC-001", partner_id="P-NOVEL", partner_name="NovelAI Partner",
            model=RevenueModel.FLAT, flat_rate=0.20,
        )
        # 계약 2: TIERED (0~1000: 25%, 1000+: 15%)
        c2 = PartnerRevenueContract(
            contract_id="RC-002", partner_id="P-SUDO", partner_name="Sudowrite Partner",
            model=RevenueModel.TIERED,
            tiers=[
                RevenueTier(0, 1000, 0.25),
                RevenueTier(1000, -1, 0.15),
            ],
        )
        # 계약 3: USAGE_BASED ($0.05/unit)
        c3 = PartnerRevenueContract(
            contract_id="RC-003", partner_id="P-NOLAN", partner_name="NolanAI Partner",
            model=RevenueModel.USAGE_BASED, usage_rate=0.05,
        )

        inv1 = gen.generate(c1, gross_revenue=5000.0,
                            period_start="2026-05-01", period_end="2026-05-31")
        inv2 = gen.generate(c2, gross_revenue=2500.0,
                            period_start="2026-05-01", period_end="2026-05-31")
        inv3 = gen.generate(c3, gross_revenue=1000.0,
                            period_start="2026-05-01", period_end="2026-05-31",
                            usage_units=20000.0)

        return self.run([c1, c2, c3], [inv1, inv2, inv3])
