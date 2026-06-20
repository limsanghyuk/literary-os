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
    from literary_system.learning.pairing.splits import SplitResult
    sr = SplitResult(train=[], held=[], held_works=["w1"], train_works=["w1"])
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
