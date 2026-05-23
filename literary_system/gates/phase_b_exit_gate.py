"""
phase_b_exit_gate.py — Gate G61: Phase B Exit Gate (V620)

SP-B.1~SP-B.4 전체 완료를 6축으로 판정하는 Phase B 최종 Exit Gate.

체크포인트
-----------
C1 (SP-B.1): Gate G54 PASS — LoRA Fine-tuning Pipeline 완성
C2 (SP-B.2): Gate G56 + G57 PASS — RLHF 루프 (RewardModel R≥0.75)
C3 (SP-B.3): Gate G59 PASS — MultiWork 협업 (7모듈 통합)
C4 (SP-B.4): Gate G60 PASS — PerformanceSLOGate (P95≤1.5초)
C5 (게이트 수): 전체 Gates ≥ 60 ALL PASS
C6 (테스트 수): 총 테스트 ≥ 6,700 PASS
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 임계값 상수
# ---------------------------------------------------------------------------
MIN_GATES: int = 60       # SP-B 완료 기준 Gate 수
MIN_TESTS: int = 6700     # SP-B 완료 기준 테스트 수


# ---------------------------------------------------------------------------
# 체크포인트 결과
# ---------------------------------------------------------------------------

@dataclass
class PhaseBCheckpoint:
    """단일 체크포인트 평가 결과."""

    name: str
    passed: bool
    detail: str = ""

    def to_dict(self) -> dict:
        return {"name": self.name, "passed": self.passed, "detail": self.detail}


# ---------------------------------------------------------------------------
# Phase B Exit Gate 보고서
# ---------------------------------------------------------------------------

@dataclass
class PhaseBExitReport:
    """Gate G61 전체 평가 보고서."""

    checkpoints: List[PhaseBCheckpoint] = field(default_factory=list)
    gates_total: int = 0
    tests_total: int = 0

    @property
    def all_pass(self) -> bool:
        return all(cp.passed for cp in self.checkpoints)

    @property
    def passed_count(self) -> int:
        return sum(1 for cp in self.checkpoints if cp.passed)

    @property
    def total_count(self) -> int:
        return len(self.checkpoints)

    @property
    def failed_checkpoints(self) -> List[str]:
        return [cp.name for cp in self.checkpoints if not cp.passed]

    def summary(self) -> str:
        status = "PASS" if self.all_pass else "FAIL"
        return (
            f"Phase B Exit Gate G61 {status} | "
            f"체크포인트 {self.passed_count}/{self.total_count} | "
            f"Gates={self.gates_total} Tests={self.tests_total}"
        )

    def to_dict(self) -> dict:
        return {
            "gate": "G61",
            "all_pass": self.all_pass,
            "passed_count": self.passed_count,
            "total_count": self.total_count,
            "failed_checkpoints": self.failed_checkpoints,
            "gates_total": self.gates_total,
            "tests_total": self.tests_total,
            "checkpoints": [cp.to_dict() for cp in self.checkpoints],
            "summary": self.summary(),
        }


# ---------------------------------------------------------------------------
# Gate 실행 함수
# ---------------------------------------------------------------------------

def run_phase_b_exit_gate(
    gates_passed: Optional[int] = None,
    tests_passed: Optional[int] = None,
    _rg_results_override: Optional[dict] = None,
) -> PhaseBExitReport:
    """
    Phase B Exit Gate G61 을 실행하고 PhaseBExitReport 를 반환한다.

    Parameters
    ----------
    gates_passed:
        현재 통과된 Gate 수. None 이면 release_gate 를 직접 호출해 측정한다.
    tests_passed:
        현재 통과된 테스트 수. None 이면 test_inventory.json 에서 읽는다.
    _rg_results_override:
        테스트 전용. release_gate 결과를 직접 주입할 때 사용한다.
        None 이면 run_release_gate() 를 실제로 호출한다.
    """
    _log.info("Phase B Exit Gate G61 실행 시작")

    # ── release_gate 결과 수집 ──────────────────────────────────────────
    if _rg_results_override is not None:
        rg = _rg_results_override
    else:
        from literary_system.gates.release_gate import run_release_gate
        rg = run_release_gate()

    results = rg.get("results", {})

    if gates_passed is None:
        gates_passed = rg.get("gates_passed", 0)

    # ── 테스트 수 수집 ────────────────────────────────────────────────
    if tests_passed is None:
        tests_passed = _count_tests()

    report = PhaseBExitReport(
        gates_total=gates_passed,
        tests_total=tests_passed,
    )

    # ── C1: G54 LoRA Fine-tuning Pipeline ────────────────────────────
    g54 = results.get("lora_finetuning_g54", {})
    report.checkpoints.append(PhaseBCheckpoint(
        name="C1-G54-LoRA",
        passed=bool(g54.get("pass")),
        detail=f"G54 pass={g54.get('pass')} (SP-B.1 LoRA Pipeline)",
    ))

    # ── C2: G56 + G57 RLHF ───────────────────────────────────────────
    g56 = results.get("rlhf_reward_g56", {})
    g57 = results.get("constitution_axis_g57", {})
    c2_pass = bool(g56.get("pass")) and bool(g57.get("pass"))
    report.checkpoints.append(PhaseBCheckpoint(
        name="C2-G56+G57-RLHF",
        passed=c2_pass,
        detail=(
            f"G56 pass={g56.get('pass')} G57 pass={g57.get('pass')} "
            f"(SP-B.2 RLHF)"
        ),
    ))

    # ── C3: G59 MultiWork ────────────────────────────────────────────
    g59 = results.get("sp_b3_exit_g59", {})
    report.checkpoints.append(PhaseBCheckpoint(
        name="C3-G59-MultiWork",
        passed=bool(g59.get("pass")),
        detail=f"G59 pass={g59.get('pass')} (SP-B.3 MultiWork 7모듈)",
    ))

    # ── C4: G60 PerformanceSLO ───────────────────────────────────────
    g60 = results.get("performance_slo_g60", {})
    report.checkpoints.append(PhaseBCheckpoint(
        name="C4-G60-PerfSLO",
        passed=bool(g60.get("pass")),
        detail=f"G60 pass={g60.get('pass')} (SP-B.4 P95≤1.5초)",
    ))

    # ── C5: 총 Gates ≥ MIN_GATES ─────────────────────────────────────
    c5_pass = gates_passed >= MIN_GATES
    report.checkpoints.append(PhaseBCheckpoint(
        name="C5-TotalGates",
        passed=c5_pass,
        detail=f"gates={gates_passed} (기준≥{MIN_GATES})",
    ))

    # ── C6: 총 Tests ≥ MIN_TESTS ─────────────────────────────────────
    c6_pass = tests_passed >= MIN_TESTS
    report.checkpoints.append(PhaseBCheckpoint(
        name="C6-TotalTests",
        passed=c6_pass,
        detail=f"tests={tests_passed} (기준≥{MIN_TESTS})",
    ))

    status = "PASS" if report.all_pass else "FAIL"
    _log.info("Phase B Exit Gate G61 %s — %s", status, report.summary())
    return report


# ---------------------------------------------------------------------------
# 테스트 수 보조 함수
# ---------------------------------------------------------------------------

def _count_tests() -> int:
    """tools/test_inventory.json 에서 총 테스트 수를 읽는다."""
    import json
    from pathlib import Path

    inventory_path = Path(__file__).parents[2] / "tools" / "test_inventory.json"
    try:
        data = json.loads(inventory_path.read_text())
        return data.get("total_tests", 0)
    except Exception as exc:  # noqa: BLE001
        _log.warning("test_inventory.json 읽기 실패: %s", exc)
        return 0


# ---------------------------------------------------------------------------
# release_gate.py 연동 래퍼
# ---------------------------------------------------------------------------

def run_g61_gate() -> dict:
    """release_gate.py 에서 호출되는 표준 인터페이스."""
    report = run_phase_b_exit_gate()
    return {
        "gate": "G61",
        "gate_name": "Phase B Exit Gate G61 — SP-B 6축 완료 판정",
        "pass": report.all_pass,
        "passed_count": report.passed_count,
        "total_count": report.total_count,
        "failed_checkpoints": report.failed_checkpoints,
        "gates_total": report.gates_total,
        "tests_total": report.tests_total,
        "checkpoints": {cp.name: cp.to_dict() for cp in report.checkpoints},
        "summary": report.summary(),
    }
