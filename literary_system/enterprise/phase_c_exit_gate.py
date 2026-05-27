"""
literary_system/enterprise/phase_c_exit_gate.py
================================================
V680: SP-C.4 Phase C Exit Gate G79

G73~G78 6개 Enterprise Gate를 종합하여 Phase C (SP-C.4) 완료 여부를 판정한다.
모든 Enterprise Gate가 PASS이고 총 TC 수가 8500 이상이면 G79 PASS.

ADR-142 참조.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PhaseCExitStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass
class EnterprisePhaseCGateResult:
    """단일 Enterprise Gate 실행 결과."""
    gate_id: str
    description: str
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)
    error: str = ""

    @property
    def status_str(self) -> str:
        return "PASS" if self.passed else "FAIL"


@dataclass
class EnterprisePhaseCExitReport:
    """G79 Phase C Exit 종합 보고서."""
    gate_results: list[EnterprisePhaseCGateResult]
    total_tc: int
    min_tc_required: int
    overall_status: PhaseCExitStatus
    version: str = "12.0.1"

    @property
    def all_gates_passed(self) -> bool:
        return all(r.passed for r in self.gate_results)

    @property
    def tc_satisfied(self) -> bool:
        return self.total_tc >= self.min_tc_required

    @property
    def gate_passed(self) -> bool:
        return self.overall_status == PhaseCExitStatus.PASS

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.gate_results if r.passed)

    @property
    def total_count(self) -> int:
        return len(self.gate_results)

    def summary(self) -> str:
        lines = [
            f"=== G79 Phase C Exit Report (v{self.version}) ===",
            f"Enterprise Gates: {self.passed_count}/{self.total_count} PASS",
            f"Total TC: {self.total_tc} (required ≥ {self.min_tc_required})",
            f"Overall: {self.overall_status.value}",
            "",
        ]
        for r in self.gate_results:
            lines.append(f"  [{r.status_str}] {r.gate_id} — {r.description}")
            if r.error:
                lines.append(f"         ERROR: {r.error}")
        return "\n".join(lines)


class EnterprisePhaseCExitGate:
    """
    G79: SP-C.4 Phase C Exit Gate.

    체크리스트:
      C1. G73 Enterprise SLO Gate PASS
      C2. G74 Revenue Gate PASS
      C3. G75-BM Benchmark Gate PASS
      C4. G76 Tenant Isolation Gate PASS
      C5. G77 Cost Control Gate PASS
      C6. G78 Compliance Audit Gate PASS
      C7. Total TC ≥ 8500
    """

    GATE_ID = "G79"
    MIN_TC = 8500
    VERSION = "12.0.1"

    # (gate_id, description, import_path, class_name)
    ENTERPRISE_GATES: list[tuple[str, str, str, str]] = [
        ("G73", "Enterprise SLO 계약·모니터링",
         "literary_system.enterprise.slo", "EnterpriseSLOGate"),
        ("G74", "Revenue Share 계약·인보이스 검증",
         "literary_system.enterprise.revenue", "RevenueGate"),
        ("G75-BM", "Enterprise 성능 벤치마크",
         "literary_system.enterprise.benchmark", "BenchmarkGate"),
        ("G76", "Enterprise 테넌트 격리 감사",
         "literary_system.enterprise.tenant_isolation", "TenantIsolationGate"),
        ("G77", "Enterprise 비용 예산 제어",
         "literary_system.enterprise.cost_control", "EnterpriseCostControlGate"),
        ("G78", "Enterprise 컴플라이언스 감사",
         "literary_system.enterprise.compliance_audit", "EnterpriseComplianceAuditGate"),
    ]

    def _run_single_gate(
        self, gate_id: str, description: str, module_path: str, class_name: str
    ) -> EnterprisePhaseCGateResult:
        """단일 Enterprise Gate를 demo_run()으로 실행."""
        try:
            import importlib
            mod = importlib.import_module(module_path)
            cls = getattr(mod, class_name)
            instance = cls()
            report = instance.demo_run()
            passed = bool(getattr(report, "gate_passed", getattr(report, "all_passed", False)))
            details: dict[str, Any] = {}
            for attr in ("tenants", "total_events", "total_suite_usd",
                         "slo_contracts", "invoices", "benchmarks"):
                val = getattr(report, attr, None)
                if val is not None:
                    details[attr] = val
            return EnterprisePhaseCGateResult(
                gate_id=gate_id,
                description=description,
                passed=passed,
                details=details,
            )
        except Exception as exc:
            return EnterprisePhaseCGateResult(
                gate_id=gate_id,
                description=description,
                passed=False,
                error=str(exc),
            )

    def _get_total_tc(self) -> int:
        """test_inventory.json에서 TC 수를 읽는다."""
        import json
        import os

        candidates = [
            "tools/test_inventory.json",
            os.path.join(os.path.dirname(__file__), "../../tools/test_inventory.json"),
        ]
        for path in candidates:
            try:
                with open(path) as f:
                    data = json.load(f)
                return int(data.get("test_count", data.get("total", 0)))
            except Exception:
                pass
        return 0

    def run(self, total_tc: int | None = None) -> EnterprisePhaseCExitReport:
        """G79 전체 실행."""
        results: list[EnterprisePhaseCGateResult] = []
        for gate_id, desc, module_path, cls_name in self.ENTERPRISE_GATES:
            results.append(self._run_single_gate(gate_id, desc, module_path, cls_name))

        if total_tc is None:
            total_tc = self._get_total_tc()

        all_pass = all(r.passed for r in results)
        tc_ok = total_tc >= self.MIN_TC

        status = PhaseCExitStatus.PASS if (all_pass and tc_ok) else PhaseCExitStatus.FAIL
        return EnterprisePhaseCExitReport(
            gate_results=results,
            total_tc=total_tc,
            min_tc_required=self.MIN_TC,
            overall_status=status,
            version=self.VERSION,
        )

    def demo_run(self) -> EnterprisePhaseCExitReport:
        """릴리즈 Gate용 demo_run — 실제 run()과 동일."""
        return self.run()
