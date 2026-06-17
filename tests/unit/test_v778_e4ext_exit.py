"""test_v778 — E.4 확장 Exit (V778, ADR-238). TC01~10."""
from literary_system.learning.e4ext_exit import run_e4ext_exit
R = run_e4ext_exit()
def test_tc01_gate_name(): assert R["gate"]=="E4-EXT-EXIT"
def test_tc02_passed(): assert R["passed"] is True
def test_tc03_seven_cp(): assert R["n_total"]==7
def test_tc04_all_pass(): assert R["n_pass"]==7
def test_tc05_cp1_modes(): assert "local" in R["checkpoints"][0]["detail"] and R["checkpoints"][0]["passed"]
def test_tc06_cp2_cloud(): assert R["checkpoints"][1]["passed"]
def test_tc07_cp4_loopc(): assert R["checkpoints"][3]["passed"] and "adopt" in R["checkpoints"][3]["detail"]
def test_tc08_cp5_discrimination(): assert R["checkpoints"][4]["passed"] and "AUC" in R["checkpoints"][4]["detail"]
def test_tc09_cp7_adr(): assert R["checkpoints"][6]["passed"]
def test_tc10_export():
    import literary_system.learning as L; assert hasattr(L,"run_e4ext_exit")
