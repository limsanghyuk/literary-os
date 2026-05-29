"""V394 Payoff Debt Ledger Tests"""
import pytest
from literary_system.longform.payoff_debt import (
    DebtType, DebtPriority, DebtStatus, PayoffDebt, PayoffDebtLedger
)

class TestDebtEnums:
    def test_debt_status_values(self):
        for s in [DebtStatus.OPEN, DebtStatus.ESCALATING, DebtStatus.DUE,
                  DebtStatus.PAID, DebtStatus.DEFAULTED, DebtStatus.CANCELLED]:
            assert s is not None

    def test_debt_priority_values(self):
        for p in [DebtPriority.CRITICAL, DebtPriority.NORMAL, DebtPriority.OPTIONAL]:
            assert p is not None

    def test_debt_type_values(self):
        for t in [DebtType.FORESHADOW, DebtType.MYSTERY, DebtType.EMOTIONAL,
                  DebtType.RELATIONSHIP, DebtType.MOTIF]:
            assert t is not None

    def test_all_enums_are_strings(self):
        assert isinstance(DebtStatus.OPEN, str)
        assert isinstance(DebtPriority.CRITICAL, str)

class TestPayoffDebt:
    def _make(self, **kw):
        defaults = dict(
            debt_id="D001", debt_type=DebtType.FORESHADOW,
            priority=DebtPriority.CRITICAL, created_episode=2, created_scene="ep2_sc3",
            promise_type="secret_reveal", expected_payoff_min=6, expected_payoff_max=10
        )
        defaults.update(kw)
        return PayoffDebt(**defaults)

    def test_default_status_is_open(self):
        d = self._make()
        assert d.status == DebtStatus.OPEN

    def test_is_critical_default_false_when_open(self):
        d = self._make()
        assert d.is_critical_default is False

    def test_is_critical_default_true_when_defaulted(self):
        d = self._make()
        d.status = DebtStatus.DEFAULTED
        assert d.is_critical_default is True

    def test_is_overdue(self):
        d = self._make()
        d.status = DebtStatus.DUE
        assert d.is_overdue is True

    def test_normal_debt_not_critical_default(self):
        d = self._make(priority=DebtPriority.NORMAL)
        d.status = DebtStatus.DEFAULTED
        assert d.is_critical_default is False

class TestPayoffDebtLedger:
    def setup_method(self):
        self.ledger = PayoffDebtLedger()

    def _make_debt(self, debt_id, priority=DebtPriority.NORMAL, created=1, min_ep=4, max_ep=8):
        return PayoffDebt(
            debt_id=debt_id, debt_type=DebtType.FORESHADOW,
            priority=priority, created_episode=created, created_scene=f"sc{created}",
            promise_type="reveal", expected_payoff_min=min_ep, expected_payoff_max=max_ep
        )

    def test_window_half_constant(self):
        assert PayoffDebtLedger.WINDOW_HALF == 5

    def test_add_debt(self):
        d = self._make_debt("D001")
        self.ledger.add_debt(d)
        assert self.ledger.summary()["total"] == 1

    def test_mark_paid(self):
        d = self._make_debt("D001")
        self.ledger.add_debt(d)
        result = self.ledger.mark_paid("D001", episode=5, scene="ep5_sc2", strength=0.9)
        assert result is True
        assert self.ledger.summary()["paid"] == 1

    def test_mark_paid_wrong_id(self):
        d = self._make_debt("D001")
        self.ledger.add_debt(d)
        result = self.ledger.mark_paid("D999", episode=5, scene="ep5_sc2", strength=0.9)
        assert result is False

    def test_tick_episode_transitions_to_due(self):
        d = self._make_debt("D001", min_ep=4, max_ep=8)
        self.ledger.add_debt(d)
        self.ledger.tick_episode(4)
        assert d.status == DebtStatus.DUE

    def test_tick_episode_defaults_overdue(self):
        d = self._make_debt("D001", min_ep=2, max_ep=4)
        self.ledger.add_debt(d)
        self.ledger.tick_episode(9)
        assert d.status == DebtStatus.DEFAULTED

    def test_summary_keys(self):
        s = self.ledger.summary()
        for key in ["total", "paid", "defaulted", "critical_defaults", "open"]:
            assert key in s

    def test_finale_critical_check_empty(self):
        result = self.ledger.finale_critical_check()
        assert result is True

    def test_finale_critical_check_all_paid(self):
        d = self._make_debt("D001", priority=DebtPriority.CRITICAL, min_ep=12, max_ep=15)
        self.ledger.add_debt(d)
        self.ledger.mark_paid("D001", episode=14, scene="ep14_sc1", strength=1.0)
        assert self.ledger.finale_critical_check() is True

    def test_finale_critical_check_unpaid_critical_fails(self):
        d = self._make_debt("D001", priority=DebtPriority.CRITICAL, min_ep=2, max_ep=6)
        self.ledger.add_debt(d)
        self.ledger.tick_episode(10)  # Force default
        assert self.ledger.finale_critical_check() is False

    def test_multiple_debts_summary(self):
        for i in range(5):
            self.ledger.add_debt(self._make_debt(f"D{i:03d}"))
        assert self.ledger.summary()["total"] == 5

    def test_open_debts(self):
        d1 = self._make_debt("D001")
        d2 = self._make_debt("D002")
        self.ledger.add_debt(d1)
        self.ledger.add_debt(d2)
        self.ledger.mark_paid("D001", episode=5, scene="sc", strength=1.0)
        assert len(self.ledger.open_debts()) == 1

    def test_critical_open_debts(self):
        d1 = self._make_debt("D001", priority=DebtPriority.CRITICAL)
        d2 = self._make_debt("D002", priority=DebtPriority.NORMAL)
        self.ledger.add_debt(d1)
        self.ledger.add_debt(d2)
        assert len(self.ledger.critical_open_debts()) == 1

    def test_window_debts(self):
        d = self._make_debt("D001", created=3)
        self.ledger.add_debt(d)
        # Window at ep 5: [0, 10] → includes created_ep 3
        result = self.ledger.window_debts(5)
        assert len(result) == 1

    def test_window_debts_excludes_far(self):
        d = self._make_debt("D001", created=15)
        self.ledger.add_debt(d)
        # Window at ep 0: [0, 5] → created_ep 15 outside
        result = self.ledger.window_debts(0)
        assert len(result) == 0

