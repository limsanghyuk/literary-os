"""test_v788_pertoken_winrate — per-token 길이정규화 승률 코어 (V788, DESIGN-SGATE-v1 ③). TC01~12."""
import math
from literary_system.learning.pertoken_winrate import (
    SideScore, per_token_logp, pairwise_winner, win_rate,
    char_len, ws_token_len, length_diagnostic, EPS_TIE)


def test_tc01_per_token_basic():
    assert per_token_logp(-120.0, 60) == -2.0
def test_tc02_per_token_zero_tokens_safe():
    assert per_token_logp(-5.0, 0) == -5.0          # max(n,1) 보호
def test_tc03_sidescore_per_token():
    assert SideScore(-90.0, 60).per_token == -1.5
def test_tc04_sum_scheme_prefers_shorter():
    # draft 더 길어 누적 logp 더 음수 → sum 스킴은 ref 승(길이 편향 재현)
    d, f = SideScore(-120.0, 100), SideScore(-90.0, 60)
    assert pairwise_winner(d, f, "sum") == "ref"
def test_tc05_pertoken_flips_to_draft():
    # 동일 쌍이 per-token(-1.2 > -1.5)에서는 draft 승 → 편향 분리 입증
    d, f = SideScore(-120.0, 100), SideScore(-90.0, 60)
    assert pairwise_winner(d, f, "pertoken") == "draft"
def test_tc06_tie_within_eps():
    d, f = SideScore(-1.0, 1), SideScore(-1.0 - EPS_TIE / 2, 1)
    assert pairwise_winner(d, f, "pertoken") == "tie"
def test_tc07_unknown_scheme_raises():
    try:
        pairwise_winner(SideScore(-1, 1), SideScore(-1, 1), "bogus"); assert False
    except ValueError:
        pass
def test_tc08_winrate_sum_vs_pertoken_differ():
    rows = [{"draft": {"sumlogp": -120, "n_tokens": 100}, "ref": {"sumlogp": -90, "n_tokens": 60}}]
    assert win_rate(rows, "sum") == 0.0 and win_rate(rows, "pertoken") == 1.0
def test_tc09_winrate_empty():
    assert win_rate([], "pertoken") == 0.0
def test_tc10_winrate_tie_half():
    rows = [{"draft": {"sumlogp": -2.0, "n_tokens": 2}, "ref": {"sumlogp": -1.0, "n_tokens": 1}}]
    assert win_rate(rows, "pertoken") == 0.5     # 둘다 -1.0 → tie → 0.5
def test_tc11_length_diag_detects_asymmetry():
    pairs = [{"draft": "x" * 600, "ref": "y" * 400} for _ in range(10)]
    d = length_diagnostic(pairs, char_len)
    assert d.draft_minus_ref == 200.0 and d.null_winrate_shorter == 1.0  # ref 항상 짧음
def test_tc12_ws_token_len_and_empty_diag():
    assert ws_token_len("a b c") == 3 and char_len("") == 0
    assert length_diagnostic([], char_len).n == 0
