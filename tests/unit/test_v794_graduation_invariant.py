"""SP-E.10.2 — L1→L2 졸업 불변식 게이트 (V794). fail-closed 감사 함수.

실제 4070 rounds_ledger(클린 5런: pt_W1 0.68~0.72, held 250)를 모사한 레코드로 검증.
"""
import pytest
from literary_system.learning.loopc_closure import (
    graduation_invariant, GRAD_CONSEC_REQUIRED, GRAD_MIN_PAIRS)


def _round(decision="adopt", n_pairs=250, ci=0.64, lrate=0.40, c3=True):
    return {"decision": decision, "n_pairs": n_pairs,
            "w1_ci_lower": ci, "length_rule_rate": lrate, "c3_passed": c3}


def _five_clean():
    # 4070 클린 5런 모사: CI하한 0.62~0.66, length-rule 0.3~0.5, c3 PASS
    return [_round(ci=c, lrate=l) for c, l in
            [(0.62, 0.45), (0.66, 0.30), (0.63, 0.40), (0.64, 0.35), (0.65, 0.42)]]


def test_graduates_on_five_clean_rounds():
    out = graduation_invariant(_five_clean())
    assert out["graduated"] is True
    assert out["exit_version"] == "v14.0.0"
    assert out["consecutive_adopt"] == 5
    assert out["sum_pairs"] >= GRAD_MIN_PAIRS
    assert all(out["checks"].values())
    assert out["violations"] == []


def test_four_rounds_blocked_on_consec():
    out = graduation_invariant(_five_clean()[:4])
    assert out["graduated"] is False
    assert out["checks"]["consecutive_adopt_ge_required"] is False
    assert out["exit_version"] is None


def test_ci_lower_below_floor_blocks():
    rounds = _five_clean()
    rounds[2] = _round(ci=0.48)   # CI하한 0.48 ≤ 0.5
    out = graduation_invariant(rounds)
    assert out["graduated"] is False
    assert out["checks"]["all_ci_lower_gt_min"] is False


def test_length_rule_violation_blocks():
    rounds = _five_clean()
    rounds[1] = _round(lrate=0.75)   # 0.75 > 0.60
    out = graduation_invariant(rounds)
    assert out["graduated"] is False
    assert out["checks"]["all_length_rule_le_max"] is False


def test_c3_fail_blocks():
    rounds = _five_clean()
    rounds[0] = _round(c3=False)
    out = graduation_invariant(rounds)
    assert out["graduated"] is False
    assert out["checks"]["all_c3_passed"] is False


def test_rollback_breaks_streak():
    # 앞 2개 adopt, 그 다음 rollback, 마지막 5개 adopt → 말미 스트릭 5
    rounds = [_round(), _round(), _round(decision="rollback")] + _five_clean()
    out = graduation_invariant(rounds)
    assert out["consecutive_adopt"] == 5
    assert out["graduated"] is True   # 말미 5연속 클린


def test_rollback_in_window_blocks():
    # 말미 4 adopt만 (직전 rollback) → consec 4 차단
    rounds = _five_clean()[:1] + [_round(decision="rollback")] + _five_clean()[:4]
    out = graduation_invariant(rounds)
    assert out["consecutive_adopt"] == 4
    assert out["graduated"] is False


def test_sum_pairs_below_min_blocks():
    rounds = [_round(n_pairs=40) for _ in range(5)]  # 5×40=200 < 250
    out = graduation_invariant(rounds)
    assert out["graduated"] is False
    assert out["checks"]["sum_pairs_ge_min"] is False


def test_missing_field_fail_closed():
    rounds = _five_clean()
    del rounds[2]["w1_ci_lower"]   # 필드 누락 → 통과 아님
    out = graduation_invariant(rounds)
    assert out["graduated"] is False
    assert out["checks"]["all_ci_lower_gt_min"] is False
    assert any("누락" in v for v in out["violations"])


def test_empty_ledger_fail_closed():
    out = graduation_invariant([])
    assert out["graduated"] is False
    assert out["consecutive_adopt"] == 0
