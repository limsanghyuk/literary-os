"""
V674 Revenue Gate G74 테스트 (SP-C.4, ADR-136)
30 TC — RevenueModel/InvoiceStatus/RevenueTier/Contract/Invoice/Calculator/Generator/Gate
"""
import pytest
from literary_system.enterprise.revenue import (
    RevenueModel, InvoiceStatus, RevenueTier,
    PartnerRevenueContract, RevenueInvoice, RevenueReport,
    RevenueCalculator, RevenueInvoiceGenerator, RevenueGate,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def flat_contract():
    return PartnerRevenueContract(
        contract_id="RC-F1", partner_id="P-A", partner_name="PartnerA",
        model=RevenueModel.FLAT, flat_rate=0.20,
    )

@pytest.fixture
def tiered_contract():
    return PartnerRevenueContract(
        contract_id="RC-T1", partner_id="P-B", partner_name="PartnerB",
        model=RevenueModel.TIERED,
        tiers=[
            RevenueTier(0, 1000, 0.25),
            RevenueTier(1000, -1, 0.15),
        ],
    )

@pytest.fixture
def usage_contract():
    return PartnerRevenueContract(
        contract_id="RC-U1", partner_id="P-C", partner_name="PartnerC",
        model=RevenueModel.USAGE_BASED, usage_rate=0.05,
    )

@pytest.fixture
def generator():
    return RevenueInvoiceGenerator()

@pytest.fixture
def gate():
    return RevenueGate()


# ── TC01~TC05: RevenueModel & InvoiceStatus 열거형 ───────────────────────────

def test_revenue_model_values():
    assert RevenueModel.FLAT.value == "flat"
    assert RevenueModel.TIERED.value == "tiered"
    assert RevenueModel.USAGE_BASED.value == "usage_based"

def test_invoice_status_values():
    assert InvoiceStatus.DRAFT.value == "draft"
    assert InvoiceStatus.ISSUED.value == "issued"
    assert InvoiceStatus.PAID.value == "paid"
    assert InvoiceStatus.OVERDUE.value == "overdue"

def test_revenue_model_count():
    assert len(RevenueModel) == 3

def test_invoice_status_count():
    assert len(InvoiceStatus) == 4

def test_revenue_tier_fields():
    t = RevenueTier(min_amount=0, max_amount=500, rate=0.20)
    assert t.min_amount == 0
    assert t.max_amount == 500
    assert t.rate == 0.20


# ── TC06~TC10: PartnerRevenueContract ────────────────────────────────────────

def test_flat_contract_fields(flat_contract):
    assert flat_contract.contract_id == "RC-F1"
    assert flat_contract.model == RevenueModel.FLAT
    assert flat_contract.flat_rate == 0.20
    assert flat_contract.active is True

def test_tiered_contract_tiers(tiered_contract):
    assert len(tiered_contract.tiers) == 2
    assert tiered_contract.tiers[0].rate == 0.25
    assert tiered_contract.tiers[1].rate == 0.15

def test_usage_contract_rate(usage_contract):
    assert usage_contract.usage_rate == 0.05
    assert usage_contract.model == RevenueModel.USAGE_BASED

def test_contract_default_currency(flat_contract):
    assert flat_contract.currency == "USD"

def test_inactive_contract():
    c = PartnerRevenueContract(
        contract_id="RC-X", partner_id="P-X", partner_name="X",
        model=RevenueModel.FLAT, flat_rate=0.30, active=False,
    )
    assert c.active is False


# ── TC11~TC17: RevenueCalculator ─────────────────────────────────────────────

def test_flat_calculation(flat_contract):
    share = RevenueCalculator.calculate_partner_share(flat_contract, 1000.0)
    assert share == pytest.approx(200.0)

def test_flat_calculation_zero(flat_contract):
    share = RevenueCalculator.calculate_partner_share(flat_contract, 0.0)
    assert share == pytest.approx(0.0)

def test_tiered_below_first_threshold(tiered_contract):
    # 500 USD: 전량 25%
    share = RevenueCalculator.calculate_partner_share(tiered_contract, 500.0)
    assert share == pytest.approx(125.0)

def test_tiered_above_first_threshold(tiered_contract):
    # 2500 USD: 1000*0.25 + 1500*0.15 = 250 + 225 = 475
    share = RevenueCalculator.calculate_partner_share(tiered_contract, 2500.0)
    assert share == pytest.approx(475.0)

def test_usage_based_calculation(usage_contract):
    share = RevenueCalculator.calculate_partner_share(usage_contract, 0.0, usage_units=1000.0)
    assert share == pytest.approx(50.0)

def test_inactive_contract_returns_zero():
    c = PartnerRevenueContract(
        contract_id="RC-X", partner_id="P-X", partner_name="X",
        model=RevenueModel.FLAT, flat_rate=0.50, active=False,
    )
    share = RevenueCalculator.calculate_partner_share(c, 1000.0)
    assert share == pytest.approx(0.0)

def test_tiered_empty_tiers_returns_zero():
    c = PartnerRevenueContract(
        contract_id="RC-T0", partner_id="P-T0", partner_name="T0",
        model=RevenueModel.TIERED, tiers=[],
    )
    share = RevenueCalculator.calculate_partner_share(c, 1000.0)
    assert share == pytest.approx(0.0)


# ── TC18~TC22: RevenueInvoiceGenerator ───────────────────────────────────────

def test_invoice_generated(generator, flat_contract):
    inv = generator.generate(flat_contract, 1000.0, "2026-05-01", "2026-05-31")
    assert inv.invoice_id.startswith("INV-")
    assert inv.gross_revenue == 1000.0
    assert inv.partner_share == pytest.approx(200.0)
    assert inv.platform_share == pytest.approx(800.0)

def test_invoice_balance(generator, tiered_contract):
    inv = generator.generate(tiered_contract, 2000.0, "2026-05-01", "2026-05-31")
    total = inv.partner_share + inv.platform_share
    assert abs(total - inv.gross_revenue) < 0.01

def test_invoice_status(generator, flat_contract):
    inv = generator.generate(flat_contract, 500.0, "2026-05-01", "2026-05-31")
    assert inv.status == InvoiceStatus.ISSUED

def test_invoice_line_items(generator, flat_contract):
    inv = generator.generate(flat_contract, 1000.0, "2026-05-01", "2026-05-31")
    types = {item["type"] for item in inv.line_items}
    assert "gross" in types
    assert "partner" in types
    assert "platform" in types

def test_invoice_id_sequential(generator, flat_contract):
    inv1 = generator.generate(flat_contract, 100.0, "2026-05-01", "2026-05-31")
    inv2 = generator.generate(flat_contract, 200.0, "2026-05-01", "2026-05-31")
    assert inv1.invoice_id != inv2.invoice_id


# ── TC23~TC27: RevenueGate.run() ─────────────────────────────────────────────

def test_gate_run_pass(gate, flat_contract, generator):
    inv = generator.generate(flat_contract, 1000.0, "2026-05-01", "2026-05-31")
    report = gate.run([flat_contract], [inv])
    assert report.gate_passed is True
    assert report.gate_id == "G74"
    assert report.total_contracts == 1
    assert report.total_invoices == 1

def test_gate_run_gross_sum(gate, flat_contract, tiered_contract, generator):
    inv1 = generator.generate(flat_contract, 1000.0, "2026-05-01", "2026-05-31")
    inv2 = generator.generate(tiered_contract, 2000.0, "2026-05-01", "2026-05-31")
    report = gate.run([flat_contract, tiered_contract], [inv1, inv2])
    assert report.total_gross == pytest.approx(3000.0)

def test_gate_orphan_invoice_error(gate, generator):
    orphan_contract = PartnerRevenueContract(
        contract_id="RC-ORPHAN", partner_id="P-O", partner_name="O",
        model=RevenueModel.FLAT, flat_rate=0.10,
    )
    inv = generator.generate(orphan_contract, 500.0, "2026-05-01", "2026-05-31")
    report = gate.run([], [inv])  # 계약 없음
    assert report.gate_passed is False
    assert len(report.errors) > 0

def test_gate_empty_invoices_fail(gate, flat_contract):
    report = gate.run([flat_contract], [])
    assert report.gate_passed is False

def test_gate_tiered_no_tiers_error(gate, generator):
    bad_contract = PartnerRevenueContract(
        contract_id="RC-BAD", partner_id="P-BAD", partner_name="BAD",
        model=RevenueModel.TIERED, tiers=[],
    )
    inv = generator.generate(bad_contract, 1000.0, "2026-05-01", "2026-05-31")
    report = gate.run([bad_contract], [inv])
    assert report.gate_passed is False


# ── TC28~TC30: demo_run + 모듈 임포트 검증 ───────────────────────────────────

def test_demo_run_pass(gate):
    report = gate.demo_run()
    assert report.gate_passed is True
    assert report.total_contracts == 3
    assert report.total_invoices == 3

def test_demo_run_partner_pay(gate):
    report = gate.demo_run()
    # FLAT 5000*0.20=1000, TIERED 2500(1000*0.25+1500*0.15)=475, USAGE 20000*0.05=1000 → 2475
    assert report.total_partner_pay == pytest.approx(2475.0)

def test_module_import():
    from literary_system.enterprise import RevenueGate as G
    assert G.GATE_ID == "G74"
