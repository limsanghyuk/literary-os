"""test_v757_alignment.py — AlignmentMonitor + G_LLM1_ALIGNMENT (V757, ADR-217). TC01~TC14."""
import importlib.util
from pathlib import Path
from literary_system.critic import CriticEnsemble, CriticContext, AlignmentReport, measure_alignment, ALIGNMENT_MIN
from literary_system.critic.alignment_monitor import _human_majority_ab
from literary_system.validation.human_gt_fixtures import GT_FIXTURE_PAIRS, GT_FIXTURE_RECORDS, FIXTURE_DB

_g = importlib.util.spec_from_file_location("al", Path(__file__).resolve().parents[2] / "tools/run_llm1_alignment_gate.py")
AL = importlib.util.module_from_spec(_g); _g.loader.exec_module(AL)

def _pairs():
    return [(p.pair_id, p.left_id, p.right_id, FIXTURE_DB[p.left_id], FIXTURE_DB[p.right_id]) for p in GT_FIXTURE_PAIRS]
def _ctx(_): return CriticContext(rag_refs=["r"])

def test_tc01_min_080(): assert ALIGNMENT_MIN == 0.80
def test_tc02_human_majority_ab():
    m = _human_majority_ab(GT_FIXTURE_RECORDS)
    assert m["hgt_p01"] == "a" and m["hgt_p03"] == "b"  # canon 위치
def test_tc03_perfect_alignment():
    ens = CriticEnsemble(llm=AL._canon_judge, seed=1)
    r = measure_alignment(_pairs(), ens, _ctx, GT_FIXTURE_RECORDS)
    assert isinstance(r, AlignmentReport) and r.agreement_rate == 1.0 and r.passed
def test_tc04_n_pairs():
    r = measure_alignment(_pairs(), CriticEnsemble(llm=AL._canon_judge, seed=1), _ctx, GT_FIXTURE_RECORDS)
    assert r.n_pairs == 6
def test_tc05_per_pair_rows():
    r = measure_alignment(_pairs(), CriticEnsemble(llm=AL._canon_judge, seed=1), _ctx, GT_FIXTURE_RECORDS)
    assert len(r.per_pair) == 6 and all("match" in x for x in r.per_pair)
def test_tc06_disagreement_lowers():
    # 항상 A만 찍는 critic → 인간(canon이 좌/우 섞임)과 일부만 일치 → 1.0 미만
    ens = CriticEnsemble(llm=lambda p: "WINNER: A", seed=1)
    r = measure_alignment(_pairs(), ens, _ctx, GT_FIXTURE_RECORDS)
    assert r.agreement_rate < 1.0
def test_tc07_below_threshold_fails():
    ens = CriticEnsemble(llm=lambda p: "WINNER: B", seed=1)  # 항상 B
    r = measure_alignment(_pairs(), ens, _ctx, GT_FIXTURE_RECORDS)
    assert (r.agreement_rate < ALIGNMENT_MIN) == (not r.passed)
def test_tc08_summary(): 
    r = measure_alignment(_pairs(), CriticEnsemble(llm=AL._canon_judge, seed=1), _ctx, GT_FIXTURE_RECORDS)
    assert "일치율" in r.summary
def test_tc09_empty_pairs():
    r = measure_alignment([], CriticEnsemble(llm=AL._canon_judge), _ctx, GT_FIXTURE_RECORDS)
    assert r.n_pairs == 0 and r.agreement_rate == 0.0 and not r.passed
# ── 게이트 ──
def test_tc10_gate_passes(): assert AL.run_g_llm1_alignment()["passed"] is True
def test_tc11_gate_rate(): assert AL.run_g_llm1_alignment()["agreement_rate"] == 1.0
def test_tc12_gate_min(): assert AL.run_g_llm1_alignment()["min"] == 0.80
def test_tc13_gate_name(): assert AL.run_g_llm1_alignment()["gate"] == "G_LLM1_ALIGNMENT"
def test_tc14_gate_n(): assert AL.run_g_llm1_alignment()["n_pairs"] == 6
