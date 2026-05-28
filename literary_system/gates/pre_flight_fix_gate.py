"""
literary_system/gates/pre_flight_fix_gate.py
============================================
V684 — G81: Pre-flight Fix Gate (ADR-146)

SP-D.1 진입 전 수정한 TD-1/TD-2/TD-3 기술부채 + D-M-13 구조 변경을
통합 검증하는 Gate.

검증 항목 (5축):
  FX-1 (TD-1): benchmark.percentile() NIST R-7 구현 존재 및 정확성
  FX-2 (TD-2): RevenueCalculator.is_contiguous() + calculate_tiered() 존재 및 정확성
  FX-3 (TD-3): EnterpriseCostReport.is_blocking + _evaluate_alerts() 연결
  FX-4 (D-M-13): gates/phase_c_exit_gate.py Wrapper 존재 및 8-체크포인트 보유
  FX-5 (통합): 3 TD + 1 구조변경 ALL PASS → gate_passed True

ADR-146 참조.
LLM-0 원칙 완전 준수 (외부 LLM 호출 없음)
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import List, Optional

GATE_ID: str = "G81"


# ---------------------------------------------------------------------------
# 결과 데이터클래스
# ---------------------------------------------------------------------------

@dataclass
class FixCheckpoint:
    """개별 수정 검증 결과."""
    name: str
    passed: bool
    detail: str = ""


@dataclass
class PreFlightFixReport:
    """G81 통합 결과 리포트."""
    checkpoints: List[FixCheckpoint] = field(default_factory=list)
    gate_passed: bool = False

    def add(self, checkpoint: FixCheckpoint) -> None:
        self.checkpoints.append(checkpoint)

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checkpoints if c.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for c in self.checkpoints if not c.passed)


# ---------------------------------------------------------------------------
# FX-1: TD-1 — benchmark.percentile() NIST R-7
# ---------------------------------------------------------------------------

def _check_fx1_benchmark_percentile() -> FixCheckpoint:
    """TD-1: benchmark.percentile()가 NIST R-7 방식으로 구현되었는지 검증."""
    try:
        from literary_system.enterprise.benchmark import percentile  # noqa: PLC0415

        # n=100 → NIST R-7: rank=0.99*99=98.01 → lo=98(val=99), hi=99(val=100), frac=0.01
        # result = 99 + 0.01*(100-99) = 99.01
        data100 = list(range(1, 101))
        p99 = percentile(data100, 0.99)
        expected = 99.01
        ok = abs(p99 - expected) < 1e-6

        # n=1 edge
        ok = ok and (percentile([42.0], 0.99) == 42.0)

        # n=2 midpoint p=0.5 → rank=0.5*1=0.5, lo=0(0.0), hi=1(100.0), frac=0.5 → 50.0
        two = percentile([0.0, 100.0], 0.5)
        ok = ok and abs(two - 50.0) < 1e-6

        # n=0 → 0.0
        ok = ok and (percentile([], 0.99) == 0.0)

        detail = (
            "p99(1..100)={:.4f} expected={} n=1={} n=2_mid={:.1f}".format(
                p99, expected, percentile([42.0], 0.99), two
            )
            if ok
            else "FAIL p99={:.4f} expected={}".format(p99, expected)
        )
        return FixCheckpoint("FX-1(TD-1) benchmark.percentile NIST-R7", ok, detail)
    except Exception as exc:
        return FixCheckpoint("FX-1(TD-1) benchmark.percentile NIST-R7", False, str(exc))


# ---------------------------------------------------------------------------
# FX-2: TD-2 — RevenueCalculator.is_contiguous() + calculate_tiered()
# ---------------------------------------------------------------------------

def _check_fx2_revenue_is_contiguous() -> FixCheckpoint:
    """TD-2: is_contiguous() + calculate_tiered() 존재 및 정확성 검증."""
    try:
        from literary_system.enterprise.revenue import (  # noqa: PLC0415
            PartnerRevenueContract,
            RevenueCalculator,
            RevenueModel,
            RevenueTier,
        )

        # is_contiguous: 연속 티어 → True
        t1 = RevenueTier(min_amount=0.0, max_amount=1000.0, rate=0.15)
        t2 = RevenueTier(min_amount=1000.0, max_amount=5000.0, rate=0.12)
        t3 = RevenueTier(min_amount=5000.0, max_amount=-1, rate=0.10)
        ok_contig = RevenueCalculator.is_contiguous([t1, t2, t3])

        # 갭 있는 티어 → False
        gap_t = RevenueTier(min_amount=1500.0, max_amount=5000.0, rate=0.12)
        ok_gap = not RevenueCalculator.is_contiguous([t1, gap_t])

        # calculate_tiered: 2,000 USD → 1,000*0.15 + 1,000*0.12 = 150+120 = 270
        contract = PartnerRevenueContract(
            contract_id="TEST-TIERED",
            partner_id="P-001",
            partner_name="TestPartner",
            model=RevenueModel.TIERED,
            tiers=[t1, t2],
        )
        result = RevenueCalculator.calculate_tiered(contract, 2000.0)
        ok_calc = abs(result - 270.0) < 0.01

        # non-contiguous → ValueError
        bad_contract = PartnerRevenueContract(
            contract_id="BAD",
            partner_id="P-002",
            partner_name="Bad",
            model=RevenueModel.TIERED,
            tiers=[t1, gap_t],
        )
        ok_error = False
        try:
            RevenueCalculator.calculate_tiered(bad_contract, 1000.0)
        except ValueError:
            ok_error = True

        ok = ok_contig and ok_gap and ok_calc and ok_error
        detail = (
            "is_contig={}, gap_detect={}, tiered(2000)={:.2f}, ValueError={}".format(
                ok_contig, ok_gap, result, ok_error
            )
        )
        return FixCheckpoint("FX-2(TD-2) is_contiguous+calculate_tiered", ok, detail)
    except Exception as exc:
        return FixCheckpoint("FX-2(TD-2) is_contiguous+calculate_tiered", False, str(exc))


# ---------------------------------------------------------------------------
# FX-3: TD-3 — EnterpriseCostReport.is_blocking + _evaluate_alerts()
# ---------------------------------------------------------------------------

def _check_fx3_cost_control_is_blocking() -> FixCheckpoint:
    """TD-3: is_blocking 위임 + _evaluate_alerts() gate_passed 결정 검증."""
    try:
        from literary_system.enterprise.cost_control import (  # noqa: PLC0415
            CostAlertLevel,
            EnterpriseCostAlert,
            EnterpriseCostControlGate,
            EnterpriseCostReport,
        )

        # EnterpriseCostReport.is_blocking: EXCEEDED → True
        exceeded_alert = EnterpriseCostAlert(
            tenant_id="T-test", level=CostAlertLevel.EXCEEDED,
            current_usd=110.0, limit_usd=100.0, usage_pct=1.1, message="test",
        )
        report_exceeded = EnterpriseCostReport(
            tenant_id="T-test", total_usd=110.0, budget=None, alert=exceeded_alert,
        )
        ok_delegate = report_exceeded.is_blocking is True

        # no-alert → False
        report_ok = EnterpriseCostReport(
            tenant_id="T-ok", total_usd=50.0, budget=None, alert=None,
        )
        ok_no_alert = report_ok.is_blocking is False

        # _evaluate_alerts: blocking 1건 → gate_passed=False
        gate = EnterpriseCostControlGate()
        summary = gate._evaluate_alerts([report_exceeded, report_ok])
        ok_eval = (summary.gate_passed is False) and (summary.blocking == 1)

        # demo_run(): T4-Jenova EXCEEDED → gate_passed=False
        demo = gate.demo_run()
        ok_demo = demo.gate_passed is False

        ok = ok_delegate and ok_no_alert and ok_eval and ok_demo
        detail = (
            "delegate={}, no_alert={}, evaluate={}, demo_gate={}".format(
                ok_delegate, ok_no_alert, ok_eval, ok_demo
            )
        )
        return FixCheckpoint("FX-3(TD-3) is_blocking→gate_passed", ok, detail)
    except Exception as exc:
        return FixCheckpoint("FX-3(TD-3) is_blocking→gate_passed", False, str(exc))


# ---------------------------------------------------------------------------
# FX-4: D-M-13 — gates/phase_c_exit_gate.py Wrapper
# ---------------------------------------------------------------------------

def _check_fx4_phase_c_exit_gate_wrapper() -> FixCheckpoint:
    """D-M-13: gates/phase_c_exit_gate.py 가 8-체크포인트 Wrapper로 존재하는지 확인."""
    try:
        from literary_system.gates.phase_c_exit_gate import (  # noqa: PLC0415
            PhaseCCheckpoint,
            PhaseCExitReport,
            run_phase_c_exit_gate,
            run_g79_gate,
            MIN_GATES,
            MIN_TESTS,
            GATE_ID as G79_ID,
        )

        # 상수 검증
        ok_constants = (MIN_GATES == 80) and (MIN_TESTS == 8845) and (G79_ID == "G79")

        # run_phase_c_exit_gate() 빠른 실행 (_rg_results_override 주입)
        report = run_phase_c_exit_gate(
            gates_passed=80,
            tests_passed=8845,
            _rg_results_override={
                "pass": True,
                "gates_total": 80,
                "tests_total": 8845,
                "gate_passed": True,
            }
        )
        ok_callable = isinstance(report, PhaseCExitReport)

        # 체크포인트 8개 이상 보유
        ok_cp_count = len(report.checkpoints) >= 8

        # run_g79_gate() 딕셔너리 반환 (파라미터 없이 호출 → 빠른 경로 불가하므로 시그니처만 확인)
        import inspect  # noqa: PLC0415
        sig = inspect.signature(run_g79_gate)
        ok_g79_exists = callable(run_g79_gate)

        ok = ok_constants and ok_callable and ok_cp_count and ok_g79_exists
        detail = (
            "constants={}, callable={}, cp_count={}, g79_exists={}".format(
                ok_constants, ok_callable, len(report.checkpoints), ok_g79_exists
            )
        )
        return FixCheckpoint("FX-4(D-M-13) phase_c_exit_gate Wrapper", ok, detail)
    except Exception as exc:
        return FixCheckpoint("FX-4(D-M-13) phase_c_exit_gate Wrapper", False, str(exc))


# ---------------------------------------------------------------------------
# FX-5: 통합 — 전체 PASS 여부
# ---------------------------------------------------------------------------

def _check_fx5_all_pass(checkpoints: List[FixCheckpoint]) -> FixCheckpoint:
    """FX-5: 모든 수정 항목(FX-1~FX-4) ALL PASS → gate_passed True."""
    all_pass = all(c.passed for c in checkpoints)
    detail = "{}/{} checkpoints passed".format(
        sum(c.passed for c in checkpoints), len(checkpoints)
    )
    return FixCheckpoint("FX-5 통합 ALL-PASS", all_pass, detail)


# ---------------------------------------------------------------------------
# 메인 실행 함수
# ---------------------------------------------------------------------------

def run_pre_flight_fix_gate() -> PreFlightFixReport:
    """G81: Pre-flight Fix Gate 실행."""
    report = PreFlightFixReport()

    fx1 = _check_fx1_benchmark_percentile()
    report.add(fx1)

    fx2 = _check_fx2_revenue_is_contiguous()
    report.add(fx2)

    fx3 = _check_fx3_cost_control_is_blocking()
    report.add(fx3)

    fx4 = _check_fx4_phase_c_exit_gate_wrapper()
    report.add(fx4)

    fx5 = _check_fx5_all_pass([fx1, fx2, fx3, fx4])
    report.add(fx5)

    report.gate_passed = fx5.passed
    return report


def run_g81_gate(
    _rg_results_override: Optional[dict] = None,
) -> dict:
    """release_gate.py 통합용 딕셔너리 반환."""
    report = run_pre_flight_fix_gate()
    checkpoints_summary = [
        {"name": c.name, "passed": c.passed, "detail": c.detail}
        for c in report.checkpoints
    ]
    return {
        "pass": report.gate_passed,
        "gate_id": GATE_ID,
        "passed_count": report.passed_count,
        "failed_count": report.failed_count,
        "checkpoints": checkpoints_summary,
    }


if __name__ == "__main__":
    result = run_pre_flight_fix_gate()
    status = "PASS" if result.gate_passed else "FAIL"
    sys.stdout.write("[{}] G81 Pre-flight Fix Gate\n".format(status))
    for cp in result.checkpoints:
        icon = "OK" if cp.passed else "FAIL"
        sys.stdout.write("  [{}] {}: {}\n".format(icon, cp.name, cp.detail))
    sys.exit(0 if result.gate_passed else 1)
