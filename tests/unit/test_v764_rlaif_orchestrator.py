"""test_v764_rlaif_orchestrator.py — RLAIF 오케스트레이션 (V764, ADR-224). TC01~TC13."""
import tempfile, os
from literary_system.learning.rlaif_orchestrator import RLAIFTrainingSpec, RLAIFOrchestrator
from literary_system.learning.loop_c import PreferencePair

def _pairs(n, draft_wins=0):
    out = []
    for i in range(n):
        w = "draft" if i < draft_wins else "ref"
        out.append(PreferencePair.from_pass7("setup", "thriller", f"생성{i} 긴텍스트", f"명작{i}", w, f"ref::{i}"))
    return out

def _tmp(): fd, p = tempfile.mkstemp(suffix=".jsonl"); os.close(fd); return p

def test_tc01_default_base_model():
    assert "Llama" in RLAIFOrchestrator().base_model
def test_tc02_default_rank():
    assert RLAIFOrchestrator().lora_rank == 16
def test_tc03_prepare_enough():
    spec = RLAIFOrchestrator().prepare(_pairs(12), _tmp())
    assert spec.status == "prepared" and spec.n_pairs == 12
def test_tc04_prepare_writes_dpo():
    out = _tmp(); RLAIFOrchestrator().prepare(_pairs(10), out)
    assert sum(1 for _ in open(out, encoding="utf-8")) == 10
def test_tc05_too_few_blocked():
    spec = RLAIFOrchestrator().prepare(_pairs(5), _tmp())
    assert spec.status == "blocked"
def test_tc06_baseline_win_rate():
    spec = RLAIFOrchestrator().prepare(_pairs(10, draft_wins=4), _tmp())
    assert spec.baseline_win_rate == 0.4
def test_tc07_objective_dpo():
    assert RLAIFOrchestrator().prepare(_pairs(10), _tmp()).objective == "dpo"
def test_tc08_spec_summary():
    assert "RLAIF" in RLAIFOrchestrator().prepare(_pairs(10), _tmp()).summary
def test_tc09_job_request_ready():
    o = RLAIFOrchestrator(); spec = o.prepare(_pairs(10), _tmp())
    assert o.job_request(spec)["ready"] is True
def test_tc10_job_request_blocked():
    o = RLAIFOrchestrator(); spec = o.prepare(_pairs(3), _tmp())
    assert o.job_request(spec)["ready"] is False
def test_tc11_custom_model():
    o = RLAIFOrchestrator(base_model="LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct", lora_rank=32)
    assert o.base_model.startswith("LGAI") and o.lora_rank == 32
def test_tc12_spec_fields():
    spec = RLAIFOrchestrator().prepare(_pairs(10), _tmp())
    assert isinstance(spec, RLAIFTrainingSpec) and spec.dpo_dataset_path
def test_tc13_gpu_slo_note():
    spec = RLAIFOrchestrator().prepare(_pairs(10), _tmp())
    assert "GPU SLO" in RLAIFOrchestrator().job_request(spec)["note"]
