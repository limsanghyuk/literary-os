"""
Literary OS V459 -- BillingEngine

ADR-012: PG 다중화 -- Stripe + TossPayments 어댑터 패턴

설계 원칙:
  - LLM-0: pg_fn(charge_fn) 주입으로 실 결제 API 격리
  - 어댑터 패턴: StripeAdapter / TossPaymentsAdapter 공통 인터페이스
  - PaymentGatewayRouter: 리전별 PG 선택 (KR -> Toss, 그 외 -> Stripe)
  - BillingRecord: 불변 결제 레코드 (감사 추적)
  - InvoiceGenerator: 월별 청구서 자동 생성
"""
from __future__ import annotations

import hashlib
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Dict, List, Optional

# ---------------------------------------------------------------------------
# 예외
# ---------------------------------------------------------------------------

class PaymentGatewayError(RuntimeError):
    """PG 결제 처리 실패."""
    def __init__(self, gateway: str, reason: str, tenant_id: str = ""):
        self.gateway   = gateway
        self.reason    = reason
        self.tenant_id = tenant_id
        super().__init__(f"[{gateway}] 결제 실패 tenant={tenant_id}: {reason}")


class InvoiceNotFoundError(KeyError):
    """청구서 없음."""


# ---------------------------------------------------------------------------
# 열거형
# ---------------------------------------------------------------------------

class PaymentStatus(str, Enum):
    PENDING   = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED    = "FAILED"
    REFUNDED  = "REFUNDED"


class PaymentGatewayType(str, Enum):
    STRIPE = "STRIPE"
    TOSS   = "TOSS"


# ---------------------------------------------------------------------------
# 결제 레코드 (불변)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BillingRecord:
    """단건 결제 불변 레코드."""
    record_id:    str
    tenant_id:    str
    amount_krw:   int            # 원화 기준 (Toss), Stripe는 환산
    amount_usd:   float          # USD 기준
    gateway:      PaymentGatewayType
    status:       PaymentStatus
    gateway_txid: str            # PG 트랜잭션 ID
    description:  str
    created_at:   datetime
    metadata:     dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "record_id":    self.record_id,
            "tenant_id":    self.tenant_id,
            "amount_krw":   self.amount_krw,
            "amount_usd":   self.amount_usd,
            "gateway":      self.gateway.value,
            "status":       self.status.value,
            "gateway_txid": self.gateway_txid,
            "description":  self.description,
            "created_at":   self.created_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# 청구서
# ---------------------------------------------------------------------------

@dataclass
class InvoiceLineItem:
    description: str
    quantity:    float
    unit_price_usd: float

    @property
    def total_usd(self) -> float:
        return round(self.quantity * self.unit_price_usd, 4)


@dataclass
class Invoice:
    """월별 청구서."""
    invoice_id:  str
    tenant_id:   str
    year_month:  str           # "YYYY-MM"
    line_items:  List[InvoiceLineItem] = field(default_factory=list)
    status:      PaymentStatus = PaymentStatus.PENDING
    paid_at:     Optional[datetime] = None
    record_id:   Optional[str] = None   # 연결된 BillingRecord

    @property
    def total_usd(self) -> float:
        return round(sum(li.total_usd for li in self.line_items), 4)

    @property
    def total_krw(self) -> int:
        """KRW 환산 (1 USD = 1350 KRW 고정 환율 - 실제는 FX API 사용)."""
        return int(self.total_usd * 1350)

    def to_dict(self) -> dict:
        return {
            "invoice_id": self.invoice_id,
            "tenant_id":  self.tenant_id,
            "year_month": self.year_month,
            "line_items": [
                {"description": li.description, "total_usd": li.total_usd}
                for li in self.line_items
            ],
            "total_usd":  self.total_usd,
            "total_krw":  self.total_krw,
            "status":     self.status.value,
        }


# ---------------------------------------------------------------------------
# PG 어댑터 인터페이스
# ---------------------------------------------------------------------------

class _BasePaymentAdapter:
    """공통 PG 어댑터 인터페이스."""
    GATEWAY_TYPE: PaymentGatewayType = NotImplemented

    def __init__(self, charge_fn: Optional[Callable] = None):
        """
        charge_fn(amount_krw, amount_usd, description, metadata) -> {"txid": str}
        LLM-0: 실 PG 호출을 테스트에서 주입 가능하도록 격리.
        """
        self._charge_fn = charge_fn or self._default_charge_fn

    def charge(
        self,
        tenant_id: str,
        amount_krw: int,
        amount_usd: float,
        description: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        """결제 실행 -> {"txid": str}"""
        try:
            return self._charge_fn(
                amount_krw=amount_krw,
                amount_usd=amount_usd,
                description=description,
                metadata=metadata or {},
            )
        except Exception as e:
            raise PaymentGatewayError(
                self.GATEWAY_TYPE.value, str(e), tenant_id
            ) from e

    @staticmethod
    def _default_charge_fn(**kwargs) -> dict:
        """테스트용 Mock — 항상 성공."""
        return {"txid": f"mock-{uuid.uuid4().hex[:12]}"}


class StripeAdapter(_BasePaymentAdapter):
    """Stripe PG 어댑터 (KR 외 리전 기본)."""
    GATEWAY_TYPE = PaymentGatewayType.STRIPE


class TossPaymentsAdapter(_BasePaymentAdapter):
    """TossPayments PG 어댑터 (KR 리전 기본)."""
    GATEWAY_TYPE = PaymentGatewayType.TOSS


# ---------------------------------------------------------------------------
# PG 라우터
# ---------------------------------------------------------------------------

class PaymentGatewayRouter:
    """
    리전별 PG 선택 라우터.

    KR  -> TossPayments (국내 결제 최적)
    EU/US -> Stripe
    """

    def __init__(
        self,
        stripe_adapter:  Optional[StripeAdapter]       = None,
        toss_adapter:    Optional[TossPaymentsAdapter]  = None,
    ):
        self._stripe = stripe_adapter or StripeAdapter()
        self._toss   = toss_adapter   or TossPaymentsAdapter()

    def select(self, region: str) -> _BasePaymentAdapter:
        """리전 코드로 PG 선택."""
        if region.upper() == "KR":
            return self._toss
        return self._stripe

    def charge(
        self,
        tenant_id:   str,
        region:      str,
        amount_krw:  int,
        amount_usd:  float,
        description: str,
        metadata:    Optional[dict] = None,
    ) -> dict:
        """PG 자동 선택 후 결제."""
        adapter = self.select(region)
        return adapter.charge(tenant_id, amount_krw, amount_usd, description, metadata)


# ---------------------------------------------------------------------------
# InvoiceGenerator
# ---------------------------------------------------------------------------

class InvoiceGenerator:
    """월별 청구서 자동 생성."""

    def __init__(self):
        self._invoices: Dict[str, Invoice] = {}  # invoice_id -> Invoice
        self._lock = threading.Lock()

    def generate(
        self,
        tenant_id:  str,
        year_month: str,
        line_items: List[InvoiceLineItem],
    ) -> Invoice:
        """청구서 생성."""
        inv_id = f"INV-{tenant_id}-{year_month}-{uuid.uuid4().hex[:6].upper()}"
        invoice = Invoice(
            invoice_id=inv_id,
            tenant_id=tenant_id,
            year_month=year_month,
            line_items=line_items,
        )
        with self._lock:
            self._invoices[inv_id] = invoice
        return invoice

    def mark_paid(self, invoice_id: str, record_id: str) -> Invoice:
        with self._lock:
            if invoice_id not in self._invoices:
                raise InvoiceNotFoundError(invoice_id)
            inv = self._invoices[invoice_id]
            inv.status    = PaymentStatus.SUCCEEDED
            inv.paid_at   = datetime.now(timezone.utc)
            inv.record_id = record_id
            return inv

    def get_invoice(self, invoice_id: str) -> Invoice:
        with self._lock:
            if invoice_id not in self._invoices:
                raise InvoiceNotFoundError(invoice_id)
            return self._invoices[invoice_id]

    def list_invoices(self, tenant_id: str) -> List[Invoice]:
        with self._lock:
            return [v for v in self._invoices.values() if v.tenant_id == tenant_id]


# ---------------------------------------------------------------------------
# BillingEngine (통합 진입점)
# ---------------------------------------------------------------------------

class BillingEngine:
    """
    Literary OS V459 BillingEngine.

    책임:
      - 청구서 생성 (InvoiceGenerator)
      - PG 라우팅 결제 (PaymentGatewayRouter)
      - 결제 레코드 저장 (불변 BillingRecord)
      - 환불 처리
    """

    def __init__(
        self,
        pg_router:         Optional[PaymentGatewayRouter] = None,
        invoice_generator: Optional[InvoiceGenerator]     = None,
    ):
        self._router    = pg_router or PaymentGatewayRouter()
        self._invoicer  = invoice_generator or InvoiceGenerator()
        self._records:  Dict[str, BillingRecord] = {}
        self._lock = threading.Lock()

    # ── 결제 흐름 ─────────────────────────────────────────────────────────────

    def create_and_charge(
        self,
        tenant_id:  str,
        region:     str,
        year_month: str,
        line_items: List[InvoiceLineItem],
        description: str = "",
    ) -> BillingRecord:
        """
        청구서 생성 -> PG 결제 -> BillingRecord 반환.

        Raises:
            PaymentGatewayError: PG 오류 시
        """
        invoice = self._invoicer.generate(tenant_id, year_month, line_items)

        pg_result = self._router.charge(
            tenant_id=tenant_id,
            region=region,
            amount_krw=invoice.total_krw,
            amount_usd=invoice.total_usd,
            description=description or f"Literary OS {year_month}",
            metadata={"invoice_id": invoice.invoice_id},
        )

        adapter = self._router.select(region)
        record = BillingRecord(
            record_id=f"REC-{uuid.uuid4().hex[:12].upper()}",
            tenant_id=tenant_id,
            amount_krw=invoice.total_krw,
            amount_usd=invoice.total_usd,
            gateway=adapter.GATEWAY_TYPE,
            status=PaymentStatus.SUCCEEDED,
            gateway_txid=pg_result.get("txid", ""),
            description=description,
            created_at=datetime.now(timezone.utc),
        )

        with self._lock:
            self._records[record.record_id] = record

        self._invoicer.mark_paid(invoice.invoice_id, record.record_id)
        return record

    def refund(self, record_id: str) -> BillingRecord:
        """결제 환불 (레코드 상태 변경)."""
        with self._lock:
            if record_id not in self._records:
                raise KeyError(f"BillingRecord 없음: {record_id}")
            old = self._records[record_id]
            # frozen dataclass -> 새 인스턴스 생성
            refunded = BillingRecord(
                record_id=old.record_id,
                tenant_id=old.tenant_id,
                amount_krw=old.amount_krw,
                amount_usd=old.amount_usd,
                gateway=old.gateway,
                status=PaymentStatus.REFUNDED,
                gateway_txid=old.gateway_txid,
                description=old.description + " [REFUNDED]",
                created_at=old.created_at,
            )
            self._records[record_id] = refunded
            return refunded

    # ── 조회 ─────────────────────────────────────────────────────────────────

    def get_record(self, record_id: str) -> BillingRecord:
        with self._lock:
            if record_id not in self._records:
                raise KeyError(f"BillingRecord 없음: {record_id}")
            return self._records[record_id]

    def list_records(self, tenant_id: str) -> List[BillingRecord]:
        with self._lock:
            return [r for r in self._records.values() if r.tenant_id == tenant_id]

    def total_revenue_usd(self) -> float:
        with self._lock:
            return round(sum(
                r.amount_usd for r in self._records.values()
                if r.status == PaymentStatus.SUCCEEDED
            ), 4)

    def summary(self) -> dict:
        with self._lock:
            by_gw: Dict[str, int] = {}
            by_status: Dict[str, int] = {}
            for r in self._records.values():
                by_gw[r.gateway.value]     = by_gw.get(r.gateway.value, 0) + 1
                by_status[r.status.value]  = by_status.get(r.status.value, 0) + 1
        return {
            "total_records": len(self._records),
            "by_gateway": by_gw,
            "by_status": by_status,
            "total_revenue_usd": self.total_revenue_usd(),
        }
