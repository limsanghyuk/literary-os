"""PayoffDebtLedger — V394. LLM 0 calls.
Rolling Window (±5화) + Priority Queue (Critical/Normal/Optional).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class DebtType(str, Enum):
    FORESHADOW = "FORESHADOW"; MYSTERY = "MYSTERY"; EMOTIONAL = "EMOTIONAL"
    RELATIONSHIP = "RELATIONSHIP"; MOTIF = "MOTIF"; MORAL = "MORAL"
    INSTITUTIONAL = "INSTITUTIONAL"


class DebtPriority(str, Enum):
    CRITICAL = "CRITICAL"; NORMAL = "NORMAL"; OPTIONAL = "OPTIONAL"


class DebtStatus(str, Enum):
    OPEN = "OPEN"; ESCALATING = "ESCALATING"; DUE = "DUE"
    PAID = "PAID"; DEFAULTED = "DEFAULTED"; CANCELLED = "CANCELLED"


@dataclass
class PayoffDebt:
    debt_id: str
    debt_type: DebtType
    priority: DebtPriority
    created_episode: int
    created_scene: str
    promise_type: str
    expected_payoff_min: int
    expected_payoff_max: int
    status: DebtStatus = DebtStatus.OPEN
    payoff_episode: Optional[int] = None
    payoff_scene: Optional[str] = None
    payoff_strength: Optional[float] = None

    @property
    def is_overdue(self) -> bool:
        return self.status == DebtStatus.DUE

    @property
    def is_critical_default(self) -> bool:
        return (self.priority == DebtPriority.CRITICAL
                and self.status == DebtStatus.DEFAULTED)


class PayoffDebtLedger:
    """V394 — 복선 부채 원장.
    Rolling Window: 현재 에피소드 ±5 범위의 debt만 활성 관리.
    """

    WINDOW_HALF = 5

    def __init__(self) -> None:
        self._debts: List[PayoffDebt] = []

    def add_debt(self, debt: PayoffDebt) -> None:
        self._debts.append(debt)

    def mark_paid(
        self, debt_id: str, episode: int, scene: str, strength: float
    ) -> bool:
        for d in self._debts:
            if d.debt_id == debt_id and d.status in (
                DebtStatus.OPEN, DebtStatus.ESCALATING, DebtStatus.DUE
            ):
                d.status = DebtStatus.PAID
                d.payoff_episode = episode
                d.payoff_scene = scene
                d.payoff_strength = strength
                return True
        return False

    def tick_episode(self, current_episode: int) -> List[PayoffDebt]:
        """에피소드 진행 시 상태 갱신. 새로 DUE/DEFAULTED된 debt 반환."""
        changed = []
        for d in self._debts:
            if d.status not in (DebtStatus.OPEN, DebtStatus.ESCALATING):
                continue
            # DUE 전환: 예정 payoff 창에 진입
            if current_episode >= d.expected_payoff_min and d.status == DebtStatus.OPEN:
                d.status = DebtStatus.DUE
                changed.append(d)
            # ESCALATING: 예정 창 중반
            mid = (d.expected_payoff_min + d.expected_payoff_max) // 2
            if current_episode >= mid and d.status == DebtStatus.OPEN:
                d.status = DebtStatus.ESCALATING
                changed.append(d)
            # DEFAULT: 창 초과
            if current_episode > d.expected_payoff_max and d.status in (
                DebtStatus.DUE, DebtStatus.ESCALATING, DebtStatus.OPEN
            ):
                d.status = DebtStatus.DEFAULTED
                changed.append(d)
        return changed

    def window_debts(self, current_episode: int) -> List[PayoffDebt]:
        lo = max(0, current_episode - self.WINDOW_HALF)
        hi = current_episode + self.WINDOW_HALF
        return [d for d in self._debts if lo <= d.created_episode <= hi]

    def open_debts(self) -> List[PayoffDebt]:
        return [d for d in self._debts
                if d.status in (DebtStatus.OPEN, DebtStatus.ESCALATING, DebtStatus.DUE)]

    def critical_open_debts(self) -> List[PayoffDebt]:
        return [d for d in self.open_debts() if d.priority == DebtPriority.CRITICAL]

    def finale_critical_check(self) -> bool:
        """결말에 Critical Debt Default = 0이면 True."""
        return not any(d.is_critical_default for d in self._debts)

    def summary(self) -> dict:
        total = len(self._debts)
        paid = sum(1 for d in self._debts if d.status == DebtStatus.PAID)
        defaulted = sum(1 for d in self._debts if d.status == DebtStatus.DEFAULTED)
        critical_defaults = sum(1 for d in self._debts if d.is_critical_default)
        return {
            "total": total, "paid": paid, "defaulted": defaulted,
            "critical_defaults": critical_defaults,
            "open": len(self.open_debts()),
        }
