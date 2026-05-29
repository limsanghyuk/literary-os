"""
literary_system.gates.safety_regression_gate — SafetyRegressionV2 Release Gate.

V11.39.0 ADR-128: safety/ 패키지를 gates 레이어에 연결.
"""
from __future__ import annotations
from literary_system.safety.safety_regression_v2 import SafetyRegressionV2, SafetyRegressionReport


class SafetyRegressionGate:
    """SP-C.4 진입 전 안전성 회귀 검증 게이트."""

    def __init__(self) -> None:
        self._checker = SafetyRegressionV2()

    def run(self, text_samples: list[str]) -> dict:
        """text_samples에 대해 SafetyRegressionV2를 실행하고 결과 반환."""
        report: SafetyRegressionReport = self._checker.run(text_samples)
        passed = len(report.violations) == 0
        return {
            "gate": "G_SAFETY_REGRESSION",
            "passed": passed,
            "violations": len(report.violations),
            "details": [v.__dict__ for v in report.violations],
        }
