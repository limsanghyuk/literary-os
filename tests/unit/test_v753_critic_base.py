"""test_v753_critic_base.py — CriticInterface 5축 + G_LLM1_BOUNDARY (V753, ADR-214). TC01~TC25."""
import re
import pytest
from literary_system.critic import (
    CriticAxis, AXIS_DESC, CriticContext, CriticVerdict, CriticInterface, MockCritic,
    aggregate_verdicts,
)
import importlib.util
from pathlib import Path
_g = importlib.util.spec_from_file_location(
    "llm1b", Path(__file__).resolve().parents[2] / "tools/run_llm1_boundary_gate.py")
BG = importlib.util.module_from_spec(_g); _g.loader.exec_module(BG)

# ── 5축 ──
def test_tc01_five_axes(): assert {a.value for a in CriticAxis} == {"structure","character","dialogue","emotion","genre"}
def test_tc02_axis_count(): assert len(list(CriticAxis)) == 5
def test_tc03_axis_desc_all(): assert all(a in AXIS_DESC for a in CriticAxis)
def test_tc04_axis_structure(): assert CriticAxis.STRUCTURE == "structure"

# ── CriticContext (RAG 필수) ──
def test_tc05_ctx_valid(): assert CriticContext(rag_refs=["r1"]).rag_refs == ["r1"]
def test_tc06_ctx_empty_rag_raises():
    with pytest.raises(ValueError): CriticContext(rag_refs=[])
def test_tc07_ctx_genre(): assert CriticContext(rag_refs=["r"], genre="thriller").genre == "thriller"

# ── CriticVerdict ──
def test_tc08_verdict_valid(): assert CriticVerdict("structure","a","r","C").winner == "a"
def test_tc09_verdict_tie(): assert CriticVerdict("emotion","tie","r","C").winner == "tie"
def test_tc10_verdict_bad_winner():
    with pytest.raises(ValueError): CriticVerdict("genre","best","r","C")
def test_tc11_verdict_no_absolute_score():
    # winner만 — 점수 필드 없음 (G_NO_ABSOLUTE_REWARD)
    assert set(CriticVerdict("structure","a","r","C").__dataclass_fields__) == {"axis","winner","rationale","critic_id"}

# ── CriticInterface / MockCritic ──
def test_tc12_interface_abstract():
    with pytest.raises(TypeError): CriticInterface()  # 추상
def test_tc13_mock_eval_a():
    v = MockCritic().evaluate("더 긴 텍스트", "짧", CriticContext(rag_refs=["r"]))
    assert v.winner == "a"
def test_tc14_mock_eval_b():
    v = MockCritic(CriticAxis.DIALOGUE).evaluate("짧", "더 긴 텍스트입니다", CriticContext(rag_refs=["r"]))
    assert v.winner == "b" and v.axis == "dialogue"
def test_tc15_mock_eval_tie():
    v = MockCritic().evaluate("abc", "xyz", CriticContext(rag_refs=["r"]))
    assert v.winner == "tie"
def test_tc16_eval_requires_rag():
    class Bad: rag_refs = []  # CriticContext 아님
    with pytest.raises(ValueError): MockCritic().evaluate("a","b", Bad())
def test_tc17_eval_axis_propagates():
    for ax in CriticAxis:
        v = MockCritic(ax).evaluate("길다길다", "짧", CriticContext(rag_refs=["r"]))
        assert v.axis == ax.value
def test_tc18_critic_id():
    assert MockCritic().evaluate("길다","짧",CriticContext(rag_refs=["r"])).critic_id == "MockCritic"

# ── G_LLM1_BOUNDARY ──
def test_tc19_boundary_passes_current():
    assert BG.run_g_llm1_boundary()["passed"] is True
def test_tc20_boundary_checks_three_dirs():
    assert BG.run_g_llm1_boundary()["checked_dirs"] == ["corpus","constitution","finetune"]
def test_tc21_boundary_pattern_openai():
    assert any(rx.search("import openai") for rx in BG._RX)
def test_tc22_boundary_pattern_anthropic():
    assert any(rx.search("from anthropic import X") for rx in BG._RX)
def test_tc23_boundary_pattern_call():
    assert any(rx.search("client.chat.completions.create(") for rx in BG._RX)
def test_tc24_boundary_ignores_comment():
    # 주석 라인은 위반 아님
    assert BG._strip_noncode("# import openai 예시").strip() == ""
def test_tc25_boundary_gate_dict():
    r = BG.run_g_llm1_boundary()
    assert r["gate"] == "G_LLM1_BOUNDARY" and "violations" in r

def test_tc26_aggregate_verdicts_bt():
    vs = [CriticVerdict("structure","a","r","C"), CriticVerdict("emotion","a","r","C"),
          CriticVerdict("genre","b","r","C")]
    sc = aggregate_verdicts(vs, "draft", "ref")
    assert sc.get("draft", 0) > sc.get("ref", 0)  # a(draft) 다수 → 우세
def test_tc27_aggregate_ties_excluded():
    assert aggregate_verdicts([CriticVerdict("structure","tie","r","C")], "x", "y") == {}
