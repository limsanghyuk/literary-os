"""test_v758_corpus_cost.py — CorpusGate(SAFETY) + LLM1Metrics(COST) (V758, ADR-218). TC01~TC16."""
import importlib.util
from pathlib import Path
from literary_system.critic import CorpusGate, MIN_CORPUS_WORKS, LLM1Metrics, COST_HARD_USD, COST_SOFT_USD
_g = importlib.util.spec_from_file_location("ops", Path(__file__).resolve().parents[2] / "tools/run_llm1_ops_gates.py")
OPS = importlib.util.module_from_spec(_g); _g.loader.exec_module(OPS)

# ── CorpusGate (SAFETY) ──
def test_tc01_min_50(): assert MIN_CORPUS_WORKS == 50
def test_tc02_allowed_at_50(): assert CorpusGate().is_critic_allowed(50)
def test_tc03_allowed_above(): assert CorpusGate().is_critic_allowed(205)
def test_tc04_blocked_below(): assert not CorpusGate().is_critic_allowed(49)
def test_tc05_check_dict():
    c = CorpusGate().check(205)
    assert c["gate"] == "G_LLM1_SAFETY" and c["passed"] and c["critic_allowed"]
def test_tc06_check_blocked():
    assert CorpusGate().check(10)["passed"] is False
def test_tc07_custom_min():
    assert CorpusGate(min_works=100).is_critic_allowed(50) is False

# ── LLM1Metrics (COST) ──
def test_tc08_record_returns_cost():
    m = LLM1Metrics(); c = m.record("gpt-4o-mini", 1000, 1000)
    assert c > 0 and m.n_calls == 1
def test_tc09_total_cost():
    m = LLM1Metrics(); m.record("gpt-4o-mini", 1000, 500); m.record("gpt-5", 1000, 500)
    assert m.total_cost > 0
def test_tc10_gpt5_pricier():
    a = LLM1Metrics(); a.record("gpt-4o-mini", 1000, 1000)
    b = LLM1Metrics(); b.record("gpt-5", 1000, 1000)
    assert b.total_cost > a.total_cost
def test_tc11_budget_within():
    m = LLM1Metrics(); m.record("gpt-4o-mini", 100, 100)
    bd = m.check_budget(); assert bd["passed"] and bd["within_soft"]
def test_tc12_hard_soft_consts():
    assert COST_HARD_USD == 50.0 and COST_SOFT_USD == 30.0
def test_tc13_budget_gate_name():
    assert LLM1Metrics().check_budget()["gate"] == "G_LLM1_COST"
def test_tc14_empty_zero_cost():
    assert LLM1Metrics().total_cost == 0.0

# ── 게이트 CLI ──
def test_tc15_ops_safety_pass(): assert OPS.run_safety(205)["passed"] is True
def test_tc16_ops_cost_pass(): assert OPS.run_cost()["passed"] is True
