"""test_v761_spe2_exit.py — SP-E.2 Exit (V761, ADR-221). TC01~TC10."""
from literary_system.critic import run_spe2_exit

def test_tc01_gate_name(): assert run_spe2_exit()["gate"] == "SP-E2-EXIT"
def test_tc02_phase(): assert "E.2" in run_spe2_exit()["phase"]
def test_tc03_passed(): assert run_spe2_exit()["passed"] is True
def test_tc04_seven_checkpoints(): assert run_spe2_exit()["n_total"] == 7
def test_tc05_all_pass(): r = run_spe2_exit(); assert r["n_pass"] == r["n_total"] == 7
def test_tc06_boundary_cp(): assert any("BOUNDARY" in c["name"] and c["passed"] for c in run_spe2_exit()["checkpoints"])
def test_tc07_alignment_cp(): assert any("ALIGNMENT" in c["name"] and c["passed"] for c in run_spe2_exit()["checkpoints"])
def test_tc08_modules_cp(): assert any("7모듈" in c["name"] and c["passed"] for c in run_spe2_exit()["checkpoints"])
def test_tc09_adr_cp(): assert any("ADR" in c["name"] and c["passed"] for c in run_spe2_exit()["checkpoints"])
def test_tc10_all_five_gates():
    names = " ".join(c["name"] for c in run_spe2_exit()["checkpoints"])
    assert all(g in names for g in ["BOUNDARY","RAG","ALIGNMENT","SAFETY","COST"])
