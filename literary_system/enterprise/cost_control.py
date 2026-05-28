"""
literary_system/enterprise/cost_control.py
V683 — Enterprise 비용 제어 레이어 (ADR-140, SP-C.4)
TD-3 수정: is_blocking → gate_passed 연결 (ADR-145)

Enterprise 테넌트별 LLM 호출 비용을 추적·예산 집행·경보 발령한다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime, timezone


# ─── Enums ───────────────────────────────────────────────────────────────────

class CostAlertLevel(str, Enum):
    OK = "ok"
    WARNING = "warning"   # 80% 이상
    CRITICAL = "critical"  # 95% 이상
    EXCEEDED = "exceeded"  # 100% 초과


class CostCategory(str, Enum):
    LLM_INFERENCE = "llm_inference"
    EMBEDDING = "embedding"
    FINETUNE = "finetune"
    STORAGE = "storage"
    OTHER = "other"


# ─── Dataclasses ─────────────────────────────────────────────────────────────

@dataclass
class EnterpriseCostBudget:
    """테넌트의 월간 비용 예산 (USD)."""
    tenant_id: str
    monthly_limit_usd: float
    warning_threshold: float = 0.80   # 80%
    critical_threshold: float = 0.95  # 95%

    @property
    def warning_usd(self) -> float:
        return self.monthly_limit_usd * self.warning_threshold

    @property
    def critical_usd(self) -> float:
        return self.monthly_limit_usd * self.critical_threshold


@dataclass
class CostEntry:
    """단일 비용 항목."""
    tenant_id: str
    category: CostCategory
    amount_usd: float
    description: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class EnterpriseCostAlert:
    """비용 초과 경보."""
    tenant_id: str
    level: CostAlertLevel
    current_usd: float
    limit_usd: float
    usage_pct: float
    message: str

    @property
    def is_blocking(self) -> bool:
        return self.level == CostAlertLevel.EXCEEDED


@dataclass
class EnterpriseCostReport:
    """테넌트 비용 리포트."""
    tenant_id: str
    total_usd: float
    budget: Optional[EnterpriseCostBudget]
    entries: List[CostEntry] = field(default_factory=list)
    alert: Optional[EnterpriseCostAlert] = None
    breakdown: Dict[str, float] = field(default_factory=dict)

    @property
    def usage_pct(self) -> float:
        if self.budget is None or self.budget.monthly_limit_usd <= 0:
            return 0.0
        return self.total_usd / self.budget.monthly_limit_usd

    @property
    def alert_level(self) -> CostAlertLevel:
        if self.alert:
            return self.alert.level
        return CostAlertLevel.OK

    @property
    def is_blocking(self) -> bool:
        """alert.is_blocking 을 위임한다 (TD-3: 기존 누락 수정)."""
        return self.alert.is_blocking if self.alert is not None else False


@dataclass
class CostAlertSummary:
    """전체 테넌트 경보 집계 (TD-3 신규)."""
    blocking: int
    exceeded: int
    critical: int
    gate_passed: bool


@dataclass
class EnterpriseCostSuiteReport:
    """전체 테넌트 비용 집계."""
    reports: List[EnterpriseCostReport] = field(default_factory=list)
    total_suite_usd: float = 0.0
    tenants_exceeded: int = 0
    gate_passed: bool = True

    @property
    def all_within_budget(self) -> bool:
        return self.tenants_exceeded == 0


# ─── Registry & Tracker ──────────────────────────────────────────────────────

class EnterpriseCostTracker:
    """테넌트별 비용 기록 및 조회."""

    def __init__(self) -> None:
        self._entries: Dict[str, List[CostEntry]] = {}
        self._budgets: Dict[str, EnterpriseCostBudget] = {}

    def set_budget(self, budget: EnterpriseCostBudget) -> None:
        self._budgets[budget.tenant_id] = budget

    def record(self, entry: CostEntry) -> None:
        self._entries.setdefault(entry.tenant_id, []).append(entry)

    def total_for(self, tenant_id: str) -> float:
        return sum(e.amount_usd for e in self._entries.get(tenant_id, []))

    def breakdown_for(self, tenant_id: str) -> Dict[str, float]:
        result: Dict[str, float] = {}
        for entry in self._entries.get(tenant_id, []):
            result[entry.category.value] = result.get(entry.category.value, 0.0) + entry.amount_usd
        return result

    def build_alert(self, tenant_id: str) -> Optional[EnterpriseCostAlert]:
        budget = self._budgets.get(tenant_id)
        if budget is None:
            return None
        total = self.total_for(tenant_id)
        pct = total / budget.monthly_limit_usd if budget.monthly_limit_usd > 0 else 0.0
        if pct >= 1.0:
            level = CostAlertLevel.EXCEEDED
            msg = f"테넌트 {tenant_id}: 예산 {budget.monthly_limit_usd:.2f} USD 초과 (현재 {total:.2f} USD, {pct*100:.1f}%)"
        elif pct >= budget.critical_threshold:
            level = CostAlertLevel.CRITICAL
            msg = f"테넌트 {tenant_id}: 예산 {pct*100:.1f}% 소진 (임계: {budget.critical_threshold*100:.0f}%)"
        elif pct >= budget.warning_threshold:
            level = CostAlertLevel.WARNING
            msg = f"테넌트 {tenant_id}: 예산 {pct*100:.1f}% 소진 (경고: {budget.warning_threshold*100:.0f}%)"
        else:
            return None
        return EnterpriseCostAlert(
            tenant_id=tenant_id,
            level=level,
            current_usd=total,
            limit_usd=budget.monthly_limit_usd,
            usage_pct=pct,
            message=msg,
        )

    def report_for(self, tenant_id: str) -> EnterpriseCostReport:
        total = self.total_for(tenant_id)
        entries = list(self._entries.get(tenant_id, []))
        breakdown = self.breakdown_for(tenant_id)
        budget = self._budgets.get(tenant_id)
        alert = self.build_alert(tenant_id)
        return EnterpriseCostReport(
            tenant_id=tenant_id,
            total_usd=total,
            budget=budget,
            entries=entries,
            alert=alert,
            breakdown=breakdown,
        )

    def all_tenant_ids(self) -> List[str]:
        ids = set(self._entries.keys()) | set(self._budgets.keys())
        return sorted(ids)


# ─── Gate ────────────────────────────────────────────────────────────────────

class EnterpriseCostControlGate:
    """G77: Enterprise 비용 제어 게이트."""

    GATE_ID = "G77"

    @staticmethod
    def _evaluate_alerts(reports: List[EnterpriseCostReport]) -> CostAlertSummary:
        """경보 집계 — is_blocking 프로퍼티를 사용하여 gate_passed 를 결정한다 (TD-3).

        blocking 1건이라도 있으면 gate 실패.
        """
        blocking_count = sum(1 for r in reports if r.is_blocking)
        exceeded_count = sum(1 for r in reports if r.alert_level == CostAlertLevel.EXCEEDED)
        critical_count = sum(1 for r in reports if r.alert_level == CostAlertLevel.CRITICAL)
        return CostAlertSummary(
            blocking=blocking_count,
            exceeded=exceeded_count,
            critical=critical_count,
            gate_passed=(blocking_count == 0),
        )

    def demo_run(self) -> EnterpriseCostSuiteReport:
        """4-테넌트 비용 시나리오 데모 실행."""
        tracker = EnterpriseCostTracker()

        # 예산 설정
        tracker.set_budget(EnterpriseCostBudget("T1-NovelAI", 500.0))
        tracker.set_budget(EnterpriseCostBudget("T2-Sudowrite", 800.0))
        tracker.set_budget(EnterpriseCostBudget("T3-NolanAI", 1200.0))
        tracker.set_budget(EnterpriseCostBudget("T4-Jenova", 300.0))

        # T1: 정상 (60%)
        for i in range(6):
            tracker.record(CostEntry("T1-NovelAI", CostCategory.LLM_INFERENCE, 50.0, f"inference-{i}"))

        # T2: WARNING (82%)
        for i in range(8):
            tracker.record(CostEntry("T2-Sudowrite", CostCategory.LLM_INFERENCE, 82.0, f"inference-{i}"))

        # T3: 정상 (50%)
        for i in range(5):
            tracker.record(CostEntry("T3-NolanAI", CostCategory.EMBEDDING, 120.0, f"embed-{i}"))

        # T4: EXCEEDED (110%)
        for i in range(11):
            tracker.record(CostEntry("T4-Jenova", CostCategory.LLM_INFERENCE, 30.0, f"inference-{i}"))

        reports = [tracker.report_for(tid) for tid in tracker.all_tenant_ids()]
        total_suite = sum(r.total_usd for r in reports)

        # TD-3: _evaluate_alerts() 로 gate_passed 결정
        summary = self._evaluate_alerts(reports)

        return EnterpriseCostSuiteReport(
            reports=reports,
            total_suite_usd=total_suite,
            tenants_exceeded=summary.exceeded,
            gate_passed=summary.gate_passed,
        )
