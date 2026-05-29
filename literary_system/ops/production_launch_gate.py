"""
literary_system/ops/production_launch_gate.py
V479 — ProductionLaunchGate (SLA 4축 최종 검증)

SLA 4축 (ADR-015):
  1. p95 응답 시간 < 3s (베타)
  2. 가용성 ≥ 99.0% (베타)
  3. DR RPO ≤ 1h / RTO ≤ 4h
  4. 허상 탐지율 ≤ 5%

인터페이스:
  run_full_check() → LaunchReport
  approve_launch() → bool
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SLAAxis:
    name:    str
    metric:  float
    target:  float
    pass_if: str   # "lt" | "lte" | "gt" | "gte"
    unit:    str   = ""

    @property
    def passed(self) -> bool:
        if self.pass_if == "lt":
            return self.metric < self.target
        elif self.pass_if == "lte":
            return self.metric <= self.target
        elif self.pass_if == "gt":
            return self.metric > self.target
        elif self.pass_if == "gte":
            return self.metric >= self.target
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name":    self.name,
            "metric":  self.metric,
            "target":  self.target,
            "unit":    self.unit,
            "passed":  self.passed,
        }


@dataclass
class LaunchReport:
    axes:         List[SLAAxis]
    all_passed:   bool
    gate_checks:  Dict[str, bool]
    notes:        List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.all_passed

    def summary(self) -> str:
        passed = sum(1 for a in self.axes if a.passed)
        total  = len(self.axes)
        status = "PASS" if self.all_passed else "FAIL"
        return f"ProductionLaunchGate: {status} — SLA {passed}/{total} 통과"


class ProductionLaunchGate:
    """
    프로덕션 출시 최종 게이트.

    metric_fn: () → Dict[str, float]  (지표 주입)
      키: p95_ms, availability_pct, rpo_s, rto_s, hallucination_rate
    """

    SLA_TARGETS = {
        "p95_ms":            (3000.0, "lt",  "ms",  "API 응답 시간 p95"),
        "availability_pct":  (99.0,   "gte", "%",   "시스템 가용성"),
        "rpo_s":             (3600.0, "lte", "s",   "DR RPO"),
        "rto_s":             (14400.0,"lte", "s",   "DR RTO"),
        "hallucination_rate":(0.05,   "lte", "rate","허상 탐지율"),
    }

    def __init__(
        self,
        metric_fn=None,
        gate_check_fns: Optional[Dict[str, Any]] = None,
    ) -> None:
        # 기본 mock: 모든 SLA 통과하는 값
        self._metric_fn = metric_fn or (lambda: {
            "p95_ms":            1200.0,
            "availability_pct":  99.5,
            "rpo_s":             900.0,
            "rto_s":             7200.0,
            "hallucination_rate":0.02,
        })
        self._gate_fns = gate_check_fns or {}

    def run_full_check(self) -> LaunchReport:
        """SLA 4축 + 게이트 체크 전체 실행."""
        metrics = self._metric_fn()

        axes: List[SLAAxis] = []
        for key, (target, pass_if, unit, name) in self.SLA_TARGETS.items():
            val = metrics.get(key, 0.0)
            axes.append(SLAAxis(
                name=name,
                metric=float(val),
                target=float(target),
                pass_if=pass_if,
                unit=unit,
            ))

        # 외부 게이트 체크
        gate_checks: Dict[str, bool] = {}
        for gate_name, fn in self._gate_fns.items():
            try:
                gate_checks[gate_name] = bool(fn())
            except Exception:
                gate_checks[gate_name] = False

        all_passed = all(a.passed for a in axes) and all(gate_checks.values())

        notes = []
        for a in axes:
            if not a.passed:
                notes.append(
                    f"SLA 미달: {a.name} = {a.metric}{a.unit} "
                    f"(목표 {a.pass_if} {a.target}{a.unit})"
                )

        return LaunchReport(
            axes=axes,
            all_passed=all_passed,
            gate_checks=gate_checks,
            notes=notes,
        )

    def approve_launch(self) -> bool:
        """출시 승인 여부 반환."""
        report = self.run_full_check()
        return report.all_passed
