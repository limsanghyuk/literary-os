"""
gates/competitor_absorption_gate.py — 경쟁 흡수 Gate G72 (SP-C.4, ADR-129)

G72-1 ~ G72-5: 각 경쟁사별 서브 게이트
G72: 5개 경쟁사 전체 통합 게이트
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any

# absorption 패키지 연결 (G_CONNECTIVITY — ADR-128)
from literary_system.absorption.base import AbsorptionReport, IPAdvisoryCommit  # noqa: F401


@dataclass
class G72SubResult:
    competitor: str
    gate_id: str
    passed: bool
    ip_cleared: bool
    absorbed_count: int
    rejected_count: int
    summary: str = ""


@dataclass
class G72Report:
    sub_results: List[G72SubResult] = field(default_factory=list)
    all_passed: bool = False
    total_absorbed: int = 0
    total_rejected: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate": "G72",
            "all_passed": self.all_passed,
            "sub_results": [
                {
                    "gate_id": r.gate_id,
                    "competitor": r.competitor,
                    "passed": r.passed,
                    "ip_cleared": r.ip_cleared,
                    "absorbed": r.absorbed_count,
                    "rejected": r.rejected_count,
                }
                for r in self.sub_results
            ],
            "total_absorbed": self.total_absorbed,
            "total_rejected": self.total_rejected,
        }


def run_g72_subgate(
    competitor: str,
    gate_id: str,
    report_passed: bool,
    ip_cleared: bool,
    absorbed_count: int,
    rejected_count: int,
    summary: str = "",
) -> G72SubResult:
    """단일 경쟁사 서브 게이트 실행."""
    passed = report_passed and ip_cleared
    return G72SubResult(
        competitor=competitor,
        gate_id=gate_id,
        passed=passed,
        ip_cleared=ip_cleared,
        absorbed_count=absorbed_count,
        rejected_count=rejected_count,
        summary=summary,
    )


def run_g72_gate(sub_results: List[G72SubResult]) -> G72Report:
    """G72 통합 게이트 — 5개 서브 게이트 전부 PASS여야 통과."""
    all_passed = all(r.passed for r in sub_results)
    total_absorbed = sum(r.absorbed_count for r in sub_results)
    total_rejected = sum(r.rejected_count for r in sub_results)
    return G72Report(
        sub_results=sub_results,
        all_passed=all_passed,
        total_absorbed=total_absorbed,
        total_rejected=total_rejected,
    )
