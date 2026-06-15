"""test_v756_critic_ensemble.py — CriticEnsemble + G_LLM1_RAG (V756, ADR-216). TC01~TC18."""
import importlib.util
from pathlib import Path
import pytest
from literary_system.critic import CriticEnsemble, EnsembleResult, CriticContext, CriticVerdict

_g = importlib.util.spec_from_file_location("rag", Path(__file__).resolve().parents[2] / "tools/run_llm1_rag_gate.py")
RAG = importlib.util.module_from_spec(_g); _g.loader.exec_module(RAG)

CTX = CriticContext(rag_refs=["real::s1"], genre="thriller")
def _longer(p):
    a = p.split("씬 A ===")[1].split("씬 B ===")[0]; b = p.split("씬 B ===")[1]
    return f"WINNER: {'A' if len(a) > len(b) else 'B'}"
def _const(w): return lambda p: f"WINNER: {w}"

def test_tc01_returns_ensemble_result():
    r = CriticEnsemble(llm=_const("A"), seed=1).evaluate("긴 텍스트", "짧", CTX)
    assert isinstance(r, EnsembleResult)
def test_tc02_five_axes():
    r = CriticEnsemble(llm=_const("A"), seed=1).evaluate("긴 텍스트", "짧", CTX)
    assert r.n_axes == 5 and len(r.per_axis) == 5
def test_tc03_winner_a_when_longer():
    r = CriticEnsemble(llm=_longer, seed=3).evaluate("아주 긴 생성 씬 " * 4, "짧", CTX, "draft", "ref")
    assert r.winner == "a" and r.consensus.get("draft", 0) > r.consensus.get("ref", 0)
def test_tc04_winner_b():
    r = CriticEnsemble(llm=_longer, seed=3).evaluate("짧", "아주 긴 레퍼런스 " * 4, CTX)
    assert r.winner == "b"
def test_tc05_axis_winners_dict():
    r = CriticEnsemble(llm=_longer, seed=1).evaluate("긴 " * 5, "짧", CTX)
    assert set(r.axis_winners) == {"structure","character","dialogue","emotion","genre"}
def test_tc06_per_axis_verdicts():
    r = CriticEnsemble(llm=_const("A"), seed=1).evaluate("긴 텍스트", "짧", CTX)
    assert all(isinstance(v, CriticVerdict) for v in r.per_axis)
def test_tc07_rag_required():
    class Bad: rag_refs = []
    with pytest.raises(ValueError): CriticEnsemble(llm=_const("A")).evaluate("a","b", Bad())
def test_tc08_as_judge_draft():
    j = CriticEnsemble(llm=_longer, seed=2).as_judge(CTX)
    assert j("아주 긴 생성 씬 " * 4, "짧") == "draft"
def test_tc09_as_judge_ref():
    j = CriticEnsemble(llm=_longer, seed=2).as_judge(CTX)
    assert j("짧", "아주 긴 레퍼런스 " * 4) == "ref"
def test_tc10_no_absolute_in_consensus():
    # consensus는 BT 상대점수(합=1 근사), 절대 채점 아님
    r = CriticEnsemble(llm=_longer, seed=1).evaluate("긴 " * 5, "짧", CTX, "x", "y")
    assert abs(sum(r.consensus.values()) - 1.0) < 0.01 or r.consensus == {}

# ── G_LLM1_RAG ──
def test_tc11_rag_gate_passes(): assert RAG.run_g_llm1_rag()["passed"] is True
def test_tc12_rag_gate_ctx_rejects(): assert RAG.run_g_llm1_rag()["checks"]["ctx_rejects_empty"]
def test_tc13_rag_gate_ensemble_requires(): assert RAG.run_g_llm1_rag()["checks"]["ensemble_requires_rag"]
def test_tc14_rag_gate_valid_works(): assert RAG.run_g_llm1_rag()["checks"]["valid_rag_works"]
def test_tc15_rag_gate_name(): assert RAG.run_g_llm1_rag()["gate"] == "G_LLM1_RAG"

# ── 프롬프트 형식강제 + _parse 폴백 (V754 보강) ──
def test_tc16_parse_winner(): from literary_system.critic.llm_critics import LLMCritic; assert LLMCritic._parse("...\nWINNER: A") == "a"
def test_tc17_parse_fallback():
    from literary_system.critic.llm_critics import LLMCritic
    assert LLMCritic._parse("A가 더 우수: A") == "a"
def test_tc18_parse_default_tie():
    from literary_system.critic.llm_critics import LLMCritic
    assert LLMCritic._parse("애매한 분석만") == "tie"
