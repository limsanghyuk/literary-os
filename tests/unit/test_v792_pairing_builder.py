"""V792 — P0 선호쌍 빌더 불변식 I1~I5 + E4 스모크 (DESIGN-P0-PAIRING-BUILDER-v1)."""
import json
import pytest

from literary_system.learning.pairing.builder import build
from literary_system.learning.pairing.strategies.base import (
    RawPair, process_candidate, allocate, MIX)
from literary_system.learning.pairing.scoring import assert_no_sum, winner_pertoken
from literary_system.learning.pairing.length_match import length_match_decision
from literary_system.learning.pairing.splits import work_level_split, LeakError, MIN_HELD
from literary_system.learning.pairing.emit import (
    assert_no_verbatim, input_set_hash, ledger_rows)
from literary_system.learning.pairing.tokenizer import WhitespaceTokenizer, tokenizer_sha
from literary_system.learning.pertoken_winrate import SideScore


def _tok_text(n):  # n 토큰짜리 결정론 텍스트
    return " ".join(f"w{i}" for i in range(n))


def _mk_pairs(n_works=30, per_work=10, chosen_tok=40, rejected_tok=40):
    out = []
    for w in range(n_works):
        for k in range(per_work):
            out.append(RawPair(
                pair_id=f"p{w:03d}_{k}", work_id=f"work{w:03d}", strategy="p3",
                chosen_text=_tok_text(chosen_tok), rejected_text=_tok_text(rejected_tok)))
    return out


# ---- I1: per-token only, sum 3중 차단(가드 1/3) ----
def test_i1_assert_no_sum_raises():
    with pytest.raises(ValueError):
        assert_no_sum("sum")
    assert_no_sum("pertoken")  # 통과

def test_i1_build_refuses_sum():
    with pytest.raises(ValueError):
        build(_mk_pairs(), scheme="sum")

def test_i1_winner_pertoken_maps():
    # per-token이 덜 음수인 쪽이 승. chosen이 더 높음.
    c = SideScore(sumlogp=-10.0, n_tokens=10)   # -1.0/tok
    r = SideScore(sumlogp=-30.0, n_tokens=10)   # -3.0/tok
    assert winner_pertoken(c, r) == "chosen"


# ---- I2: length neutrality ----
def test_i2_token_hard_drop():
    lm = length_match_decision(100, 110, 100, 100)   # 10/110=9% > 5%
    assert lm.accept is False

def test_i2_token_hard_accept_soft_flag():
    lm = length_match_decision(100, 104, 100, 120)   # tok 4% ok, char 17% soft 위반
    assert lm.accept is True and lm.char_soft_ok is False

def test_i2_long_pair_dropped_in_pipeline():
    p = RawPair("x", "w0", "p3", chosen_text=_tok_text(40), rejected_text=_tok_text(50))
    v = process_candidate(p, WhitespaceTokenizer())
    assert v.accept is False and v.drop_reason == "length"


# ---- I3: no verbatim ----
def test_i3_assert_no_verbatim_raises():
    bad = [{"pair_id": "x", "leak": "가" * 25}]
    with pytest.raises(ValueError):
        assert_no_verbatim(bad)

def test_i3_ledger_has_no_text_fields():
    res = build(_mk_pairs())
    for row in res.ledger:
        for v in row.values():
            if isinstance(v, str):
                assert "w0 w1" not in v  # 본문 텍스트 미포함
        assert "chosen_text" not in row and "ref_text" not in row


# ---- I4: work-level split, held>=250, no leak ----
def test_i4_no_leak_and_held():
    res = build(_mk_pairs(n_works=30, per_work=10))  # 300쌍
    assert len(res.split.held) >= MIN_HELD
    assert not (set(res.split.train_works) & set(res.split.held_works))

def test_i4_held_shortfall_failfast():
    with pytest.raises(RuntimeError):
        work_level_split([{"pair_id": "a", "work_id": "w0"}], min_held=250)

def test_i4_leak_detected():
    from literary_system.learning.pairing.splits import PairSplitResult
    sr = PairSplitResult(train=[], held=[], held_works=["w1"], train_works=["w1"])
    with pytest.raises(LeakError):
        sr.assert_no_leak()


# ---- I5: tokenizer lock ----
def test_i5_tokenizer_sha_deterministic_and_recorded():
    tok = WhitespaceTokenizer()
    assert tokenizer_sha(tok) == tokenizer_sha(WhitespaceTokenizer())
    res = build(_mk_pairs())
    assert all(r["tokenizer_sha"] == res.tokenizer_sha for r in res.ledger)


# ---- E4: 암기쌍 폐기 ----
def test_e4_memorized_pair_dropped():
    # chosen이 ref(명작)를 그대로 복제 → e4 reject
    masterwork = "그날 밤 그는 강가에 서서 오래도록 흐르는 물을 바라보았다 그리고 천천히 돌아섰다"
    p = RawPair("m", "w0", "p3",
                chosen_text=masterwork, rejected_text=masterwork[:len(masterwork)],
                ref_text=masterwork)
    v = process_candidate(p, WhitespaceTokenizer())
    assert v.drop_reason == "e4_reject"


# ---- mix allocate ----
def test_allocate_overgen_sum():
    q = allocate(1000)
    assert sum(q.values()) >= 1000 * 1.3 * 0.99
    assert set(q) == set(MIX)


# ---- input_set_hash 동결(G2) ----
def test_input_set_hash_stable():
    a = build(_mk_pairs()); b = build(_mk_pairs())
    assert a.input_set_hash == b.input_set_hash


# ====================================================================
# V792 보강 케이스 (§3 최소 33 TC 충족) — I1~I5 경계·스텁·리포트
# ====================================================================

def test_i1_winner_pertoken_tie():
    c = SideScore(sumlogp=-10.0, n_tokens=10); r = SideScore(sumlogp=-10.0, n_tokens=10)
    assert winner_pertoken(c, r) == "tie"

def test_i1_winner_pertoken_rejected():
    c = SideScore(sumlogp=-30.0, n_tokens=10); r = SideScore(sumlogp=-10.0, n_tokens=10)
    assert winner_pertoken(c, r) == "rejected"

def test_i1_assert_no_sum_uppercase_blocked():
    with pytest.raises(ValueError):
        assert_no_sum("SUM")

def test_i1_assert_no_sum_empty_blocked():
    with pytest.raises(ValueError):
        assert_no_sum("")

def test_i2_token_boundary_exactly_5pct_accept():
    assert length_match_decision(100, 95, 100, 100).accept is True

def test_i2_token_just_over_5pct_reject():
    assert length_match_decision(100, 94, 100, 100).accept is False

def test_i2_char_boundary_exactly_8pct_ok():
    assert length_match_decision(100, 100, 100, 92).char_soft_ok is True

def test_i2_char_just_over_8pct_softflag():
    assert length_match_decision(100, 100, 100, 91).char_soft_ok is False

def test_i2_zero_length_no_div_error():
    lm = length_match_decision(0, 0, 0, 0)
    assert lm.token_delta_ratio == 0.0 and lm.accept is True

def test_i3_input_set_hash_16hex():
    h = input_set_hash([])
    assert len(h) == 16 and all(ch in "0123456789abcdef" for ch in h)

def test_i3_ledger_rows_only_accepted():
    res = build(_mk_pairs())
    assert len(res.ledger) == len(res.accepted)

def test_i3_ledger_sumlogp_is_none_and_pertoken():
    r0 = build(_mk_pairs()).ledger[0]
    assert r0["chosen_sumlogp"] is None and r0["scheme"] == "pertoken"

def test_i3_assert_no_verbatim_passes_clean():
    assert_no_verbatim(build(_mk_pairs()).ledger)

def test_i3_write_ledger_roundtrip(tmp_path):
    res = build(_mk_pairs()); p = tmp_path / "ledger.jsonl"
    from literary_system.learning.pairing.emit import write_ledger
    n = write_ledger(res.ledger, str(p))
    assert n == len(res.ledger) and sum(1 for _ in open(p)) == n

def _wpairs(n_works, per_work):
    return [{"pair_id": f"p{w}_{k}", "work_id": f"w{w:03d}"}
            for w in range(n_works) for k in range(per_work)]

def test_i4_split_reaches_min_held_exact():
    res = work_level_split(_wpairs(10, 2), min_held=4)
    assert len(res.held) >= 4; res.assert_no_leak()

def test_i4_split_deterministic():
    a = work_level_split(_wpairs(10, 2), min_held=4); b = work_level_split(_wpairs(10, 2), min_held=4)
    assert a.held_works == b.held_works and a.train_works == b.train_works

def test_i4_no_overlap_train_held():
    res = work_level_split(_wpairs(40, 10), min_held=250)
    assert not (set(res.train_works) & set(res.held_works))

def test_i5_tokenizer_sha_len16():
    assert len(tokenizer_sha(WhitespaceTokenizer())) == 16

def test_i5_whitespace_tokenize():
    assert WhitespaceTokenizer().tokenize("a b c") == ["a", "b", "c"]

def test_i5_report_records_tokenizer_sha():
    assert build(_mk_pairs()).tokenizer_sha == tokenizer_sha(WhitespaceTokenizer())

def test_mix_sums_to_one():
    assert abs(sum(MIX.values()) - 1.0) < 1e-9

def test_overgen_is_1_3():
    from literary_system.learning.pairing.strategies.base import OVERGEN
    assert OVERGEN == 1.3

def test_process_candidate_no_ref_passes():
    p = RawPair("n", "w0", "p3", chosen_text=_tok_text(40), rejected_text=_tok_text(40))
    v = process_candidate(p, WhitespaceTokenizer())
    assert v.accept is True and v.e4_decision == "pass"

def test_report_mix_target_equals_mix():
    assert build(_mk_pairs()).report.mix_target == dict(MIX)

def test_report_counts_consistent():
    res = build(_mk_pairs())
    assert res.report.total_in == len(res.verdicts)
    assert res.report.accepted == len(res.accepted)
    assert res.report.held_count == len(res.split.held)

def test_credit_uniform_shares():
    from literary_system.learning.pairing.credit import UniformCreditAssigner
    out = UniformCreditAssigner().assign(["s1", "s2", "s3", "s4"], 1.0)
    assert all(abs(v - 0.25) < 1e-9 for v in out.values())

def test_credit_empty_returns_empty():
    from literary_system.learning.pairing.credit import UniformCreditAssigner
    assert UniformCreditAssigner().assign([], 1.0) == {}
