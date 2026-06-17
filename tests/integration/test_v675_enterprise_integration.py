"""
V675 Enterprise 통합 테스트 (SP-C.4, ADR-137)
SLO + Revenue 레이어 통합 시나리오 20 TC
"""
import pytest
from literary_system.enterprise.slo import (
    EnterpriseSLOTier, EnterpriseSLOContract, SLOMetricSnapshot,
    EnterpriseSLOGate,
)
from literary_system.enterprise.revenue import (
    RevenueModel, RevenueTier, PartnerRevenueContract,
    RevenueCalculator, RevenueInvoiceGenerator, RevenueGate,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def premium_slo_contract():
    return EnterpriseSLOContract(
        contract_id="SLO-P1", partner_id="P-NOVEL", tier=EnterpriseSLOTier.PREMIUM,
        availability_target=0.999, latency_p99_ms=200, throughput_rps=500,
    )

@pytest.fixture
def enterprise_slo_contract():
    return EnterpriseSLOContract(
        contract_id="SLO-E1", partner_id="P-SUDO", tier=EnterpriseSLOTier.ENTERPRISE,
        availability_target=0.9999, latency_p99_ms=150, throughput_rps=1000,
    )

@pytest.fixture
def revenue_contract_novel():
    return PartnerRevenueContract(
        contract_id="RC-NOVEL", partner_id="P-NOVEL", partner_name="NovelAI Partner",
        model=RevenueModel.FLAT, flat_rate=0.20,
    )

@pytest.fixture
def revenue_contract_sudo():
    return PartnerRevenueContract(
        contract_id="RC-SUDO", partner_id="P-SUDO", partner_name="Sudowrite Partner",
        model=RevenueModel.TIERED,
        tiers=[RevenueTier(0, 2000, 0.25), RevenueTier(2000, -1, 0.18)],
    )


# ── TC01~TC05: SLO + Revenue 파트너 일치성 ───────────────────────────────────

def test_partner_id_match_slo_revenue(premium_slo_contract, revenue_contract_novel):
    """SLO 계약과 Revenue 계약의 파트너 ID 일치 확인"""
    assert premium_slo_contract.partner_id == revenue_contract_novel.partner_id

def test_enterprise_tier_highest_availability(enterprise_slo_contract):
    assert enterprise_slo_contract.tier == EnterpriseSLOTier.ENTERPRISE
    assert enterprise_slo_contract.availability_target >= 0.9999

def test_premium_tier_availability(premium_slo_contract):
    assert premium_slo_contract.tier == EnterpriseSLOTier.PREMIUM
    assert premium_slo_contract.availability_target >= 0.999

def test_revenue_flat_rate_range(revenue_contract_novel):
    assert 0.0 < revenue_contract_novel.flat_rate < 1.0

def test_revenue_tiered_sorted(revenue_contract_sudo):
    tiers = sorted(revenue_contract_sudo.tiers, key=lambda t: t.min_amount)
    assert tiers[0].min_amount < tiers[1].min_amount


# ── TC06~TC10: SLO 게이트 통합 ───────────────────────────────────────────────

def test_slo_gate_demo_run():
    gate = EnterpriseSLOGate()
    report = gate.demo_run()
    assert report.gate_passed is True

def test_slo_passing_snapshot(premium_slo_contract):
    from literary_system.enterprise.slo import SLOMonitor, SLOMetricSnapshot
    snap = SLOMetricSnapshot(
        contract_id="SLO-P1",
        measured_availability=0.9995, measured_latency_p99_ms=180, measured_throughput_rps=550,
    )
    violations = SLOMonitor().check(premium_slo_contract, snap)
    assert len(violations) == 0

def test_slo_failing_availability(premium_slo_contract):
    from literary_system.enterprise.slo import SLOMonitor, SLOMetricSnapshot, ViolationSeverity
    snap = SLOMetricSnapshot(
        contract_id="SLO-P1",
        measured_availability=0.990, measured_latency_p99_ms=180, measured_throughput_rps=550,
    )
    violations = SLOMonitor().check(premium_slo_contract, snap)
    assert len(violations) > 0

def test_slo_gate_75th():
    """G74 이후 G73 엔터프라이즈 레이어가 Release Gate 목록에 있음 검증"""
    from literary_system.gates.release_gate import GATES
    gate_names = [name for name, _, _ in GATES]
    assert "enterprise_slo_g73" in gate_names

def test_slo_and_revenue_gate_both_in_registry():
    from literary_system.gates.release_gate import GATES
    gate_names = [name for name, _, _ in GATES]
    assert "enterprise_slo_g73" in gate_names
    assert "revenue_g74" in gate_names


# ── TC11~TC15: Revenue 계산 통합 ─────────────────────────────────────────────

def test_flat_revenue_calculation(revenue_contract_novel):
    share = RevenueCalculator.calculate_partner_share(revenue_contract_novel, 10000.0)
    assert share == pytest.approx(2000.0)

def test_tiered_revenue_below_threshold(revenue_contract_sudo):
    # 1500 USD: 전량 25% 구간
    share = RevenueCalculator.calculate_partner_share(revenue_contract_sudo, 1500.0)
    assert share == pytest.approx(375.0)

def test_tiered_revenue_above_threshold(revenue_contract_sudo):
    # 5000 USD: 2000*0.25 + 3000*0.18 = 500 + 540 = 1040
    share = RevenueCalculator.calculate_partner_share(revenue_contract_sudo, 5000.0)
    assert share == pytest.approx(1040.0)

def test_invoice_partner_platform_sum(revenue_contract_novel):
    gen = RevenueInvoiceGenerator()
    inv = gen.generate(revenue_contract_novel, 3000.0, "2026-05-01", "2026-05-31")
    assert abs(inv.partner_share + inv.platform_share - inv.gross_revenue) < 0.01

def test_revenue_gate_two_contracts(revenue_contract_novel, revenue_contract_sudo):
    gen = RevenueInvoiceGenerator()
    inv1 = gen.generate(revenue_contract_novel, 5000.0, "2026-05-01", "2026-05-31")
    inv2 = gen.generate(revenue_contract_sudo, 5000.0, "2026-05-01", "2026-05-31")
    gate = RevenueGate()
    report = gate.run([revenue_contract_novel, revenue_contract_sudo], [inv1, inv2])
    assert report.gate_passed is True
    assert report.total_gross == pytest.approx(10000.0)


# ── TC16~TC20: 엔터프라이즈 패키지 전체 임포트 검증 ──────────────────────────

def test_enterprise_package_slo_exports():
    from literary_system.enterprise import (
        EnterpriseSLOTier, EnterpriseSLOContract, EnterpriseSLOGate,
        SLOMonitor, ViolationSeverity,
    )
    assert EnterpriseSLOGate.GATE_ID == "G73"

def test_enterprise_package_revenue_exports():
    from literary_system.enterprise import (
        RevenueModel, PartnerRevenueContract, RevenueGate,
        RevenueCalculator, RevenueInvoiceGenerator,
    )
    assert RevenueGate.GATE_ID == "G74"

def test_enterprise_full_pipeline():
    """SLO + Revenue 풀 파이프라인: 계약 생성 → 인보이스 → 게이트 통과"""
    # SLO
    slo_gate = EnterpriseSLOGate()
    slo_report = slo_gate.demo_run()
    assert slo_report.gate_passed

    # Revenue
    rev_gate = RevenueGate()
    rev_report = rev_gate.demo_run()
    assert rev_report.gate_passed

    # 두 게이트 모두 통과 → 엔터프라이즈 파트너 활성화 가능
    enterprise_ready = slo_report.gate_passed and rev_report.gate_passed
    assert enterprise_ready is True

def test_gate_count_80():
    from literary_system.gates.release_gate import GATES
    assert len(GATES) == 97

def test_sp_c4_gates_present():
    from literary_system.gates.release_gate import GATES
    gate_names = {name for name, _, _ in GATES}
    sp_c4_gates = {
        "novel_ai_absorption_g72_1", "sudowrite_absorption_g72_2",
        "novelcrafter_absorption_g72_3", "nolan_ai_absorption_g72_4",
        "jenova_absorption_g72_5", "competitive_absorption_g72_unified",
        "distillation_export_g72d", "enterprise_slo_g73", "revenue_g74",
    }
    assert sp_c4_gates.issubset(gate_names)
