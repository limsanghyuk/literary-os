"""test_v774_loopc_closure — loop-C 폐회로 + G_LOOPC_WINRATE (V774, ADR-234). TC01~15."""
import tempfile
from literary_system.learning.winrate_gate import g_loopc_winrate, WinrateGateResult, MIN_PAIRS_RELIABLE
from literary_system.learning.loopc_closure import LoopCClosure, LoopCRoundReport
from literary_system.learning.first_training_kit import make_smoke_dataset
from literary_system.learning.pareto_router import TrainingMode

def _pairs(n=8):
    import os; fd,p=tempfile.mkstemp(suffix=".jsonl"); os.close(fd); make_smoke_dataset(p,n); return p

# --- 게이트 ---
def test_tc01_gate_adopt():
    g=g_loopc_winrate(0.5,0.7,kl=0.05,r_before=0.7,r_after=0.71,n_pairs=80)
    assert g.passed and g.decision=="adopt"
def test_tc02_gate_c1_fail_no_winrate():
    g=g_loopc_winrate(0.6,0.55,n_pairs=80); assert not g.c1_winrate and g.decision=="rollback"
def test_tc03_gate_c2_fail_kl():
    # τ_KL 표준 0.50(DESIGN-SGATE-v1)로 상향됨에 따라 경계 초과값 0.6 사용
    g=g_loopc_winrate(0.5,0.7,kl=0.6,n_pairs=80); assert not g.c2_kl and not g.passed
def test_tc04_gate_c3_fail_structure():
    g=g_loopc_winrate(0.5,0.7,r_before=0.8,r_after=0.6,n_pairs=80); assert not g.c3_structure and not g.passed
def test_tc05_gate_delta():
    assert g_loopc_winrate(0.5,0.65,n_pairs=80).delta_w==0.15
def test_tc06_gate_reliable_flag():
    assert g_loopc_winrate(0.5,0.7,n_pairs=10).reliable is False
    assert g_loopc_winrate(0.5,0.7,n_pairs=MIN_PAIRS_RELIABLE).reliable is True
def test_tc07_gate_low_sample_conditional():
    g=g_loopc_winrate(0.5,0.7,n_pairs=6); assert g.passed and "신뢰 약함" in g.detail
def test_tc08_gate_structure_optional():
    g=g_loopc_winrate(0.5,0.7,n_pairs=80); assert g.c3_structure is True  # R 미제공시 통과
# --- 폐회로 ---
def test_tc09_plan_only_await():
    r=LoopCClosure().run_round(_pairs(8))
    assert r.w1 is None and "await_training" in r.next_action
def test_tc10_evaluate_adopt_continue():
    r=LoopCClosure(target_w=0.9).evaluate_round(1,0.5,0.72,80,kl=0.05,r_before=0.7,r_after=0.71)
    assert r.gate.passed and "adopt_continue" in r.next_action
def test_tc11_evaluate_adopt_done():
    r=LoopCClosure(target_w=0.6).evaluate_round(1,0.5,0.7,200,kl=0.03,r_before=0.7,r_after=0.72)
    assert "adopt_done" in r.next_action
def test_tc12_evaluate_rollback():
    r=LoopCClosure().evaluate_round(1,0.6,0.55,80); assert r.gate.decision=="rollback" and "rollback_feedback" in r.next_action
def test_tc13_run_round_with_w1():
    r=LoopCClosure(target_w=0.9).run_round(_pairs(8),measured_w1=0.8,kl=0.05)
    assert isinstance(r,LoopCRoundReport) and r.gate is not None
def test_tc14_report_to_dict():
    d=LoopCClosure().evaluate_round(1,0.5,0.7,80).to_dict()
    assert "gate" in d and "next_action" in d and d["gate"]["decision"]=="adopt"
def test_tc15_export():
    import literary_system.learning as L
    assert hasattr(L,"LoopCClosure") and hasattr(L,"g_loopc_winrate")
