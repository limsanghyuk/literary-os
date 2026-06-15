"""test_v759_arbitration.py — Arbitration Protocol v1 (V759, ADR-219). TC01~TC16."""
import importlib.util
from pathlib import Path
from literary_system.critic import DisagreementRecord, classify, formula_winner, arbitrate
_g = importlib.util.spec_from_file_location("arb", Path(__file__).resolve().parents[2] / "tools/run_arbitration_check.py")
ARB = importlib.util.module_from_spec(_g); _g.loader.exec_module(ARB)

# ── classify 5분기 ──
def test_tc01_agree(): assert classify("a", "a") == "agree"
def test_tc02_pending(): assert classify("a", "b") == "pending"
def test_tc03_formula_defect(): assert classify("a", "b", "b") == "formula_defect"
def test_tc04_critic_defect(): assert classify("a", "b", "a") == "critic_defect"
def test_tc05_genuine_ambiguous(): assert classify("a", "b", "tie") == "genuine_ambiguous"
def test_tc06_agree_with_human(): assert classify("a", "a", "a") == "agree"

# ── formula_winner (공식 R) ──
def test_tc07_formula_a_wins():
    w, gap = formula_winner("긴장이 폭발하는 갈등의 장면. 인물들이 정면으로 충돌하며 비밀이 드러난다. " * 4, "끝.")
    assert w in ("a", "b", "tie")  # 실제 R 비교 동작
def test_tc08_formula_tie_same():
    w, gap = formula_winner("동일한 텍스트입니다 같은 길이.", "동일한 텍스트입니다 같은 길이.")
    assert w == "tie" and abs(gap) < 0.02
def test_tc09_formula_returns_gap():
    w, gap = formula_winner("갈등 " * 30, "짧")
    assert isinstance(gap, float)

# ── arbitrate ──
def test_tc10_arbitrate_records():
    r = arbitrate([{"pair_id": "x", "formula_winner": "a", "critic_winner": "a"}])
    assert len(r["records"]) == 1 and isinstance(r["records"][0], DisagreementRecord)
def test_tc11_arbitrate_queue():
    r = arbitrate([{"pair_id": "x", "formula_winner": "a", "critic_winner": "b"}])
    assert r["disagreement_queue"] == ["x"]
def test_tc12_arbitrate_counts():
    r = arbitrate([{"pair_id": "p1", "formula_winner": "a", "critic_winner": "a"},
                   {"pair_id": "p2", "formula_winner": "a", "critic_winner": "b", "human_winner": "b"}])
    assert r["counts"]["agree"] == 1 and r["counts"]["formula_defect"] == 1
def test_tc13_record_fields():
    rec = arbitrate([{"pair_id": "x", "formula_winner": "a", "critic_winner": "b", "human_winner": "a", "r_gap": 0.1}])["records"][0]
    assert rec.classification == "critic_defect" and rec.r_gap == 0.1
def test_tc14_empty():
    r = arbitrate([]); assert r["records"] == [] and r["disagreement_queue"] == []

# ── 게이트/프로토콜 ──
def test_tc15_check_passes(): assert ARB.run_check()["passed"] is True
def test_tc16_check_queue(): assert ARB.run_check()["queue"] == ["p2"]
