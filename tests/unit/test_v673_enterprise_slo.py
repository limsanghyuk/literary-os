"""
tests/unit/test_v673_enterprise_slo.py
V673 Enterprise SLO Gate G73 테스트 (SP-C.4, ADR-135)
TC01~TC30
"""
import pytest
from literary_system.enterprise.slo import (
    EnterpriseSLOContract, EnterpriseSLOTier, SLOMetricSnapshot,
    SLOMonitor, SLOViolationAlert, ViolationSeverity,
    EnterpriseSLOGate, EnterpriseSLOReport,
)


@pytest.fixture
def premium_contract():
    return EnterpriseSLOContract(
        contract_id="ENT-001", partner_id="partner_a",
        tier=EnterpriseSLOTier.PREMIUM, availability_target=0.999,
        latency_p99_ms=500, throughput_rps=100,
    )

@pytest.fixture
def enterprise_contract():
    return EnterpriseSLOContract(
        contract_id="ENT-002", partner_id="partner_b",
        tier=EnterpriseSLOTier.ENTERPRISE, availability_target=0.9999,
        latency_p99_ms=300, throughput_rps=200,
    )

@pytest.fixture
def good_snapshot():
    return SLOMetricSnapshot(
        contract_id="ENT-001",
        measured_availability=0.9992,
        measured_latency_p99_ms=480,
        measured_throughput_rps=110,
    )

@pytest.fixture
def bad_snapshot():
    return SLOMetricSnapshot(
        contract_id="ENT-001",
        measured_availability=0.975,  # BREACH
        measured_latency_p99_ms=1200,
        measured_throughput_rps=50,
    )

@pytest.fixture
def monitor():
    return SLOMonitor()

@pytest.fixture
def gate():
    return EnterpriseSLOGate()


# ── TC01~TC06: Contract 구조 ──────────────────────────────────────────────
def test_tc01_contract_availability_pct(premium_contract):
    assert abs(premium_contract.availability_pct - 99.9) < 0.001

def test_tc02_tier_enum_values():
    assert EnterpriseSLOTier.ENTERPRISE.value == "enterprise"
    assert EnterpriseSLOTier.PREMIUM.value == "premium"

def test_tc03_contract_fields(premium_contract):
    assert premium_contract.contract_id == "ENT-001"
    assert premium_contract.latency_p99_ms == 500
    assert premium_contract.throughput_rps == 100

def test_tc04_contract_custom_clauses():
    c = EnterpriseSLOContract(
        contract_id="C1", partner_id="P1", tier=EnterpriseSLOTier.BASIC,
        availability_target=0.99, latency_p99_ms=1000, throughput_rps=10,
        custom_clauses=["GDPR 준수", "데이터 한국 보관"],
    )
    assert len(c.custom_clauses) == 2

def test_tc05_snapshot_availability_gap(premium_contract, good_snapshot):
    gap = good_snapshot.availability_gap(premium_contract)
    assert gap < 0  # 측정값이 목표 초과

def test_tc06_snapshot_latency_ok(premium_contract, good_snapshot):
    assert good_snapshot.is_latency_ok(premium_contract) is True


# ── TC07~TC12: SLOMonitor 정상 케이스 ───────────────────────────────────
def test_tc07_no_alerts_good_snapshot(monitor, premium_contract, good_snapshot):
    alerts = monitor.check(premium_contract, good_snapshot)
    assert len(alerts) == 0

def test_tc08_warning_on_small_gap(monitor, premium_contract):
    snap = SLOMetricSnapshot("ENT-001", 0.9985, 480, 110)  # gap=0.0005
    alerts = monitor.check(premium_contract, snap)
    avail_alerts = [a for a in alerts if a.dimension == "availability"]
    assert len(avail_alerts) == 1
    assert avail_alerts[0].severity == ViolationSeverity.WARNING

def test_tc09_critical_on_medium_gap(monitor, premium_contract):
    snap = SLOMetricSnapshot("ENT-001", 0.9885, 480, 110)  # gap=0.0105
    alerts = monitor.check(premium_contract, snap)
    avail_alerts = [a for a in alerts if a.dimension == "availability"]
    assert avail_alerts[0].severity == ViolationSeverity.CRITICAL

def test_tc10_breach_on_large_gap(monitor, premium_contract, bad_snapshot):
    alerts = monitor.check(premium_contract, bad_snapshot)
    avail_alerts = [a for a in alerts if a.dimension == "availability"]
    assert avail_alerts[0].severity == ViolationSeverity.BREACH
    assert avail_alerts[0].is_breach() is True

def test_tc11_latency_violation(monitor, premium_contract):
    snap = SLOMetricSnapshot("ENT-001", 0.9992, 1200, 110)
    alerts = monitor.check(premium_contract, snap)
    lat_alerts = [a for a in alerts if a.dimension == "latency"]
    assert len(lat_alerts) == 1
    assert lat_alerts[0].severity == ViolationSeverity.BREACH

def test_tc12_throughput_violation(monitor, premium_contract):
    snap = SLOMetricSnapshot("ENT-001", 0.9992, 480, 50)
    alerts = monitor.check(premium_contract, snap)
    tp_alerts = [a for a in alerts if a.dimension == "throughput"]
    assert len(tp_alerts) == 1


# ── TC13~TC18: EnterpriseSLOGate 정상 ─────────────────────────────────
def test_tc13_gate_pass_all_good(gate, premium_contract, good_snapshot):
    report = gate.run([premium_contract], [good_snapshot])
    assert report.gate_passed is True
    assert report.breaches == 0

def test_tc14_gate_fail_on_breach(gate, premium_contract, bad_snapshot):
    report = gate.run([premium_contract], [bad_snapshot])
    assert report.gate_passed is False
    assert report.breaches >= 1

def test_tc15_gate_report_contracts_checked(gate, premium_contract, good_snapshot):
    report = gate.run([premium_contract], [good_snapshot])
    assert report.contracts_checked == 1

def test_tc16_gate_report_summary_nonempty(gate, premium_contract, good_snapshot):
    report = gate.run([premium_contract], [good_snapshot])
    assert len(report.summary) > 0

def test_tc17_gate_demo_run_pass(gate):
    report = gate.demo_run()
    assert report.gate_passed is True
    assert report.contracts_checked == 2

def test_tc18_gate_report_to_dict(gate):
    report = gate.demo_run()
    d = report.to_dict()
    assert "gate_passed" in d
    assert "contracts_checked" in d


# ── TC19~TC24: 다수 계약 처리 ────────────────────────────────────────────
def test_tc19_multiple_contracts(gate, premium_contract, enterprise_contract):
    snaps = [
        SLOMetricSnapshot("ENT-001", 0.9992, 480, 110),
        SLOMetricSnapshot("ENT-002", 0.99995, 290, 210),
    ]
    report = gate.run([premium_contract, enterprise_contract], snaps)
    assert report.contracts_checked == 2
    assert report.gate_passed is True

def test_tc20_missing_snapshot_ignored(gate, premium_contract):
    report = gate.run([premium_contract], [])
    assert report.contracts_checked == 1
    assert report.violations_found == 0

def test_tc21_multiple_violations(gate, premium_contract):
    snap = SLOMetricSnapshot("ENT-001", 0.97, 1500, 30)
    report = gate.run([premium_contract], [snap])
    assert report.violations_found >= 3

def test_tc22_violation_alert_fields(gate, premium_contract, bad_snapshot):
    report = gate.run([premium_contract], [bad_snapshot])
    for alert in report.alerts:
        assert alert.contract_id
        assert alert.dimension in ("availability", "latency", "throughput")
        assert alert.expected > 0
        assert alert.actual >= 0

def test_tc23_all_tiers_creatable():
    for tier in EnterpriseSLOTier:
        c = EnterpriseSLOContract(
            contract_id=f"C-{tier.value}", partner_id="p",
            tier=tier, availability_target=0.99,
            latency_p99_ms=1000, throughput_rps=10,
        )
        assert c.tier == tier

def test_tc24_gate_partial_breach(gate, premium_contract, enterprise_contract):
    snaps = [
        SLOMetricSnapshot("ENT-001", 0.97, 480, 110),   # breach
        SLOMetricSnapshot("ENT-002", 0.99995, 290, 210), # ok
    ]
    report = gate.run([premium_contract, enterprise_contract], snaps)
    assert report.gate_passed is False
    assert report.breaches >= 1


# ── TC25~TC30: Release Gate G73 연동 ───────────────────────────────────
def test_tc25_g73_gate_in_release_gate():
    from literary_system.gates.release_gate import GATES
    ids = [g[0] for g in GATES]
    assert "enterprise_slo_g73" in ids

def test_tc26_g73_gate_result_pass():
    from literary_system.gates.release_gate import _gate_enterprise_slo_g73
    result = _gate_enterprise_slo_g73()
    assert result["pass"] is True

def test_tc27_g73_gate_result_keys():
    from literary_system.gates.release_gate import _gate_enterprise_slo_g73
    result = _gate_enterprise_slo_g73()
    assert "gate" in result and "checkpoints" in result

def test_tc28_violation_severity_ordering():
    assert ViolationSeverity.WARNING.value == "warning"
    assert ViolationSeverity.BREACH.value == "breach"

def test_tc29_slo_report_no_alerts_by_default():
    report = EnterpriseSLOReport()
    assert len(report.alerts) == 0
    assert report.gate_passed is False

def test_tc30_enterprise_slo_importable():
    from literary_system.enterprise.slo import EnterpriseSLOGate as G
    assert G is not None
