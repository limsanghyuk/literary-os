"""test_v760_judge_consensus.py — 심판 상향(3페르소나 합의) (V760, ADR-220). TC01~TC14."""
from literary_system.critic import CriticEnsemble, CriticContext
from literary_system.critic.llm_critics import StructureCritic, make_ensemble, LLMCritic

CTX = CriticContext(rag_refs=["r"])
def _longer(p):
    a = p.split("씬 A ===")[1].split("씬 B ===")[0]; b = p.split("씬 B ===")[1]
    return f"WINNER: {'A' if len(a) > len(b) else 'B'}"
def _const(w): return lambda p: f"WINNER: {w}"

def test_tc01_default_single():
    c = StructureCritic(llm=_const("A"), seed=1); assert c._n_judges == 1
def test_tc02_n_judges_set():
    assert StructureCritic(llm=_const("A"), n_judges=3)._n_judges == 3
def test_tc03_default_personas():
    assert StructureCritic()._personas == ("문학평론가", "드라마투르그", "일반시청자")
def test_tc04_consensus_rationale():
    v = StructureCritic(llm=_longer, seed=1, n_judges=3).evaluate("아주 긴 생성 " * 5, "짧", CTX)
    assert "합의(3)" in v.rationale and v.winner == "a"
def test_tc05_single_no_consensus_marker():
    v = StructureCritic(llm=_const("A"), seed=1, n_judges=1).evaluate("긴 텍스트", "짧", CTX)
    assert "합의" not in v.rationale
def test_tc06_robust_one_dissent():
    st = {"n": 0}
    def flaky(p):
        st["n"] += 1
        if st["n"] % 3 == 0: return "WINNER: B"
        a = p.split("씬 A ===")[1].split("씬 B ===")[0]; b = p.split("씬 B ===")[1]
        return f"WINNER: {'A' if len(a) > len(b) else 'B'}"
    v = StructureCritic(llm=flaky, seed=5, n_judges=3).evaluate("아주 긴 생성 " * 5, "짧", CTX)
    assert v.winner == "a"  # 2/3 다수결
def test_tc07_all_disagree_tie():
    # 3 페르소나가 a,b,tie로 갈리면 동률 → tie
    seq = iter(["WINNER: A", "WINNER: B", "WINNER: TIE"])
    v = StructureCritic(llm=lambda p: next(seq), seed=0, n_judges=3).evaluate("x", "y", CTX)
    assert v.winner == "tie"
def test_tc08_persona_in_prompt():
    p = StructureCritic(llm=_const("A"))._build_prompt("A", "B", CTX, persona="드라마투르그")
    assert "드라마투르그" in p
def test_tc09_no_persona_default():
    p = StructureCritic(llm=_const("A"))._build_prompt("A", "B", CTX)
    assert "관점의" not in p
# ── 전파 ──
def test_tc10_make_ensemble_n_judges():
    ens = make_ensemble(llm=_longer, seed=1, n_judges=3)
    assert all(c._n_judges == 3 for c in ens)
def test_tc11_critic_ensemble_n_judges():
    r = CriticEnsemble(llm=_longer, seed=2, n_judges=3).evaluate("아주 긴 " * 5, "짧", CTX, "d", "r")
    assert r.winner == "a"
def test_tc12_ensemble_default_single():
    r = CriticEnsemble(llm=_const("A"), seed=1).evaluate("긴 텍스트", "짧", CTX)
    assert r.n_axes == 5
def test_tc13_all_axes_consensus():
    ens = make_ensemble(llm=_longer, seed=1, n_judges=3)
    assert len({c.axis for c in ens}) == 5
def test_tc14_backward_compat():
    # 기존 단일판정 동작 유지 (n_judges 기본 1)
    v = StructureCritic(llm=_const("A"), seed=1).evaluate("긴 텍스트", "짧", CTX)
    assert v.winner in ("a", "b", "tie")
