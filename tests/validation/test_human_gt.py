"""test_human_gt.py — 인간 GT 인프라 테스트 (V750, ADR-213). TC01~TC42."""
from __future__ import annotations
import pytest
from literary_system.validation.human_gt import (
    GTMode, GTPair, GTRecord, HUMAN_GT_ALPHA_MIN, GT_CHOICES, GT_QUESTIONS,
    validate_anchor, build_blind_sheet, record_from_sheet,
    aggregate_winrate, majority_by_pair, inter_rater_alpha,
    panel_alignment, run_g_human_gt_alignment,
)
from literary_system.validation.human_gt_fixtures import (
    FIXTURE_DB, GT_FIXTURE_PAIRS, GT_FIXTURE_RECORDS, PANEL_FIXTURE_JUDGMENTS,
)

DB = FIXTURE_DB

# ── GTMode ──
def test_tc01_mode_values(): assert {m.value for m in GTMode} == {"A", "B", "C"}
def test_tc02_mode_a(): assert GTMode.A_GEN_VS_REAL.value == "A"
def test_tc03_mode_str(): assert GTMode.B_PRESTIGE_CALIB == "B"

# ── GTPair ──
def test_tc04_pair_valid():
    p = GTPair("p", "hgt_canon_01", "hgt_deg_01", "B", True, True)
    assert p.pair_id == "p" and p.left_is_real
def test_tc05_pair_bad_mode():
    with pytest.raises(ValueError): GTPair("p", "a", "b", "Z", True, False)
def test_tc06_pair_bad_question():
    with pytest.raises(ValueError): GTPair("p", "a", "b", "B", True, False, question="bad")
def test_tc07_pair_no_anchor():
    with pytest.raises(ValueError): GTPair("p", "a", "b", "B", False, False)
def test_tc08_pair_one_anchor_ok():
    assert GTPair("p", "a", "b", "A", False, True).right_is_real

# ── GTRecord ──
def test_tc09_record_valid():
    r = GTRecord("p", "a", "b", "left", "preference", "w1", "B")
    assert r.winner == "left" and r.ts > 0
def test_tc10_record_bad_winner():
    with pytest.raises(ValueError): GTRecord("p", "a", "b", "X", "preference", "w1", "B")
def test_tc11_record_tie_ok():
    assert GTRecord("p", "a", "b", "tie", "trait", "w1", "B").winner == "tie"

# ── validate_anchor (DB 앵커 강제) ──
def test_tc12_anchor_present_ok():
    validate_anchor(GTPair("p", "hgt_canon_01", "hgt_deg_01", "B", True, True), DB)
def test_tc13_anchor_missing_raises():
    with pytest.raises(ValueError):
        validate_anchor(GTPair("p", "not_in_db", "hgt_deg_01", "B", True, True), DB)
def test_tc14_nonreal_not_checked():
    # 생성물(비실제)은 DB 없어도 통과 (한 쪽만 실제면 OK)
    validate_anchor(GTPair("p", "generated_xyz", "hgt_canon_01", "A", False, True), DB)
def test_tc15_recalled_reference_blocked():
    # LLM 회상 레퍼런스(=DB 없는 real) 차단 — WP-4 핵심 규칙
    with pytest.raises(ValueError):
        validate_anchor(GTPair("p", "hgt_canon_01", "llm_recalled_ref", "A", True, True), DB)

# ── build_blind_sheet ──
def test_tc16_sheet_len():
    assert len(build_blind_sheet(GT_FIXTURE_PAIRS, DB, seed=1)) == 6
def test_tc17_sheet_has_AB_swapped():
    row = build_blind_sheet(GT_FIXTURE_PAIRS, DB, seed=1)[0]
    assert {"A", "B", "swapped", "pair_id", "question"} <= set(row)
def test_tc18_sheet_no_source_leak():
    row = build_blind_sheet(GT_FIXTURE_PAIRS, DB, seed=1)[0]
    assert "left_is_real" not in row and "is_real" not in row
def test_tc19_sheet_deterministic():
    s1 = build_blind_sheet(GT_FIXTURE_PAIRS, DB, seed=7)
    s2 = build_blind_sheet(GT_FIXTURE_PAIRS, DB, seed=7)
    assert [r["swapped"] for r in s1] == [r["swapped"] for r in s2]
def test_tc20_sheet_validates_anchor():
    bad = [GTPair("p", "not_in_db", "also_missing", "B", True, True)]
    with pytest.raises(ValueError): build_blind_sheet(bad, DB)
def test_tc21_sheet_swap_randomizes():
    # 서로 다른 seed면 swap 패턴이 달라질 수 있음(통계적); 같은 seed면 동일
    assert build_blind_sheet(GT_FIXTURE_PAIRS, DB, seed=1) is not None

# ── record_from_sheet (좌우 역변환) ──
def _row(swapped, A="hgt_canon_01", B="hgt_deg_01"):
    return {"pair_id": "p", "A": A, "B": B, "swapped": swapped, "question": "preference", "mode": "B"}
def test_tc22_noswap_A_left():
    r = record_from_sheet(_row(False), "A", "w1"); assert r.winner == "left"
def test_tc23_noswap_B_right():
    r = record_from_sheet(_row(False), "B", "w1"); assert r.winner == "right"
def test_tc24_swap_A_right():
    r = record_from_sheet(_row(True), "A", "w1"); assert r.winner == "right"
def test_tc25_swap_B_left():
    r = record_from_sheet(_row(True), "B", "w1"); assert r.winner == "left"
def test_tc26_tie():
    assert record_from_sheet(_row(False), "tie", "w1").winner == "tie"
def test_tc27_bad_choice():
    with pytest.raises(ValueError): record_from_sheet(_row(False), "C", "w1")
def test_tc27b_roundtrip_left_id_restored():
    # 불변식: swap 여부와 무관하게 left_id/right_id는 항상 원본 좌표로 복원
    pair = GTPair("rt", "hgt_canon_01", "hgt_deg_01", "B", True, True)
    for seed in range(10):
        row = build_blind_sheet([pair], DB, seed=seed)[0]
        r = record_from_sheet(row, "A", "w1")
        assert r.left_id == "hgt_canon_01" and r.right_id == "hgt_deg_01"

# ── aggregate_winrate ──
def test_tc28_winrate_canon_top():
    sc = aggregate_winrate(GT_FIXTURE_RECORDS)
    # canon 씬들이 deg 씬들보다 BT 점수 높아야
    canon = [sc.get(f"hgt_canon_{i:02d}", 0) for i in range(1, 7)]
    deg = [sc.get(f"hgt_deg_{i:02d}", 0) for i in range(1, 7)]
    assert sum(canon) > sum(deg)
def test_tc29_winrate_tie_excluded():
    recs = [GTRecord("p", "a", "b", "tie", "preference", "w1", "B")]
    assert aggregate_winrate(recs) == {}
def test_tc30_winrate_empty():
    assert aggregate_winrate([]) == {}

# ── majority_by_pair ──
def test_tc31_majority():
    maj = majority_by_pair(GT_FIXTURE_RECORDS)
    assert maj["hgt_p01"] == "left" and maj["hgt_p03"] == "right"

# ── inter_rater_alpha ──
def test_tc32_alpha_high_agreement():
    ar = inter_rater_alpha(GT_FIXTURE_RECORDS)
    assert ar.alpha >= HUMAN_GT_ALPHA_MIN
def test_tc33_alpha_result_fields():
    ar = inter_rater_alpha(GT_FIXTURE_RECORDS)
    assert ar.n_units >= 1 and "α=" in ar.summary
def test_tc34_alpha_low_on_random():
    # 평가자들이 완전 엇갈리면 α 낮음
    recs = [
        GTRecord("q1", "a", "b", "left", "preference", "w1", "B"),
        GTRecord("q1", "a", "b", "right", "preference", "w2", "B"),
        GTRecord("q2", "c", "d", "right", "preference", "w1", "B"),
        GTRecord("q2", "c", "d", "left", "preference", "w2", "B"),
    ]
    assert inter_rater_alpha(recs).alpha < HUMAN_GT_ALPHA_MIN

# ── panel_alignment ──
def test_tc35_panel_full_align():
    a = panel_alignment(GT_FIXTURE_RECORDS, PANEL_FIXTURE_JUDGMENTS)
    assert a["alignment"] == 1.0 and a["n"] >= 1
def test_tc36_panel_empty():
    assert panel_alignment(GT_FIXTURE_RECORDS, [])["n"] == 0
def test_tc37_panel_partial():
    bad_panel = [{"pair_id": "hgt_p01", "winner": "right"}]  # 인간(left)과 불일치
    a = panel_alignment(GT_FIXTURE_RECORDS, bad_panel)
    assert a["alignment"] == 0.0

# ── run_g_human_gt_alignment ──
def test_tc38_gate_pass():
    res = run_g_human_gt_alignment(GT_FIXTURE_RECORDS, PANEL_FIXTURE_JUDGMENTS)
    assert res["gate"] == "G_HUMAN_GT_ALIGNMENT" and res["passed"] is True
def test_tc39_gate_reports_alpha():
    res = run_g_human_gt_alignment(GT_FIXTURE_RECORDS, PANEL_FIXTURE_JUDGMENTS)
    assert res["alpha"] >= HUMAN_GT_ALPHA_MIN and res["alpha_min"] == HUMAN_GT_ALPHA_MIN
def test_tc40_gate_empty_fails():
    res = run_g_human_gt_alignment([], [])
    assert res["passed"] is False
def test_tc41_gate_panel_alignment_reported():
    res = run_g_human_gt_alignment(GT_FIXTURE_RECORDS, PANEL_FIXTURE_JUDGMENTS)
    assert res["panel_alignment"]["alignment"] == 1.0

# ── 픽스처 정합 ──
def test_tc42_fixtures_sane():
    assert len(GT_FIXTURE_PAIRS) == 6 and len(GT_FIXTURE_RECORDS) == 18
    assert all(p.left_is_real or p.right_is_real for p in GT_FIXTURE_PAIRS)
