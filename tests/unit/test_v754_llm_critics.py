"""test_v754_llm_critics.py — 실 LLM 축별 Critic 5종 (V754, ADR-215). TC01~TC24."""
import pytest
from literary_system.critic import (
    CriticAxis, CriticContext, CriticVerdict,
    LLMCritic, StructureCritic, CharacterCritic, DialogueCritic, EmotionCritic, GenreCritic,
    ALL_CRITICS, make_ensemble, evaluate_all_axes,
)

CTX = CriticContext(rag_refs=["real::s1", "real::s2"], genre="thriller")

def _fake_longer(prompt):
    a = prompt.split("=== 씬 A ===")[1].split("=== 씬 B ===")[0]
    b = prompt.split("=== 씬 B ===")[1]
    return f"근거... WINNER: {'A' if len(a) > len(b) else 'B'}"

def _fake_const(w):
    return lambda p: f"WINNER: {w}"

# ── 5종 축 ──
def test_tc01_structure_axis(): assert StructureCritic().axis == CriticAxis.STRUCTURE
def test_tc02_character_axis(): assert CharacterCritic().axis == CriticAxis.CHARACTER
def test_tc03_dialogue_axis(): assert DialogueCritic().axis == CriticAxis.DIALOGUE
def test_tc04_emotion_axis(): assert EmotionCritic().axis == CriticAxis.EMOTION
def test_tc05_genre_axis(): assert GenreCritic().axis == CriticAxis.GENRE
def test_tc06_all_critics_five(): assert len(ALL_CRITICS) == 5
def test_tc07_ensemble_five(): assert len(make_ensemble()) == 5
def test_tc08_ensemble_axes_unique():
    assert len({c.axis for c in make_ensemble()}) == 5

# ── _parse ──
def test_tc09_parse_a(): assert LLMCritic._parse("...\nWINNER: A") == "a"
def test_tc10_parse_b(): assert LLMCritic._parse("WINNER: B") == "b"
def test_tc11_parse_tie(): assert LLMCritic._parse("WINNER: TIE") == "tie"
def test_tc12_parse_missing_defaults_tie(): assert LLMCritic._parse("애매함") == "tie"
def test_tc13_parse_korean_colon(): assert LLMCritic._parse("WINNER： a") == "a"

# ── _judge / evaluate ──
def test_tc14_judge_requires_llm():
    with pytest.raises(RuntimeError): StructureCritic(llm=None).evaluate("a", "b", CTX)
def test_tc15_evaluate_returns_verdict():
    v = StructureCritic(llm=_fake_const("A"), seed=1).evaluate("긴 씬 텍스트", "짧", CTX)
    assert isinstance(v, CriticVerdict) and v.winner in ("a", "b", "tie")
def test_tc16_content_aware_a_wins():
    # a_text가 더 길면 swap 무관하게 winner=a (내용 인지 fake)
    for seed in range(8):
        v = DialogueCritic(llm=_fake_longer, seed=seed).evaluate("아주 긴 생성 씬 텍스트입니다 " * 3, "짧음", CTX)
        assert v.winner == "a"
def test_tc17_content_aware_b_wins():
    for seed in range(8):
        v = EmotionCritic(llm=_fake_longer, seed=seed).evaluate("짧", "아주 긴 레퍼런스 텍스트 " * 3, CTX)
        assert v.winner == "b"
def test_tc18_rag_required():
    class Bad: rag_refs = []
    with pytest.raises(ValueError): StructureCritic(llm=_fake_const("A")).evaluate("a", "b", Bad())
def test_tc19_verdict_axis():
    v = GenreCritic(llm=_fake_const("A"), seed=0).evaluate("긴 텍스트", "짧", CTX)
    assert v.axis == "genre"
def test_tc20_prompt_contains_criteria():
    p = StructureCritic(llm=_fake_const("A"))._build_prompt("A텍스트", "B텍스트", CTX)
    assert "구조" in p and "WINNER" in p and "thriller" in p

# ── evaluate_all_axes ──
def test_tc21_all_axes_five_verdicts():
    vs, con = evaluate_all_axes("긴 생성 " * 5, "짧은 레퍼런스", CTX, _fake_longer)
    assert len(vs) == 5
def test_tc22_all_axes_consensus_a():
    vs, con = evaluate_all_axes("아주 긴 생성 씬 " * 5, "짧", CTX, _fake_longer, "draft", "ref")
    assert con.get("draft", 0) > con.get("ref", 0)
def test_tc23_all_axes_verdict_types():
    vs, _ = evaluate_all_axes("긴 " * 5, "짧", CTX, _fake_longer)
    assert all(isinstance(v, CriticVerdict) for v in vs)
def test_tc24_no_absolute_score():
    v = StructureCritic(llm=_fake_const("A"), seed=0).evaluate("긴텍스트", "짧", CTX)
    assert "score" not in v.__dataclass_fields__ and v.winner in ("a", "b", "tie")
