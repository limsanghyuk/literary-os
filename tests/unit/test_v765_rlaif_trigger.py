"""test_v765_rlaif_trigger.py — RLAIFTrigger (V765, ADR-225). TC01~TC12."""
import tempfile, os
from literary_system.learning.rlaif_trigger import TriggerResult, RLAIFTrigger
from literary_system.learning.rlaif_orchestrator import RLAIFOrchestrator
from literary_system.learning.loop_c import PreferencePair

def _pairs(n, dw=0):
    return [PreferencePair.from_pass7("setup", "thriller", f"생성{i} 긴텍스트", f"명작{i}",
            "draft" if i < dw else "ref", f"ref::{i}") for i in range(n)]
def _spec(n=12, dw=4):
    fd, out = tempfile.mkstemp(suffix=".jsonl"); os.close(fd)
    return RLAIFOrchestrator().prepare(_pairs(n, dw), out)

def test_tc01_provider_default():
    from literary_system.finetune.gpu_adapter import GPUProvider
    assert RLAIFTrigger()._provider == GPUProvider.RUNPOD
def test_tc02_dry_run_status():
    r = RLAIFTrigger(dry_run=True).trigger(_spec())
    assert r.status == "dry_run"
def test_tc03_job_has_cost():
    r = RLAIFTrigger(dry_run=True).trigger(_spec())
    assert "cost_usd" in r.job
def test_tc04_job_id():
    r = RLAIFTrigger(dry_run=True).trigger(_spec())
    assert r.job.get("job_id")
def test_tc05_not_ready_blocked_spec():
    spec = _spec(n=3)  # <8 → blocked
    r = RLAIFTrigger(dry_run=True).trigger(spec)
    assert r.status == "not_ready"
def test_tc06_result_type():
    assert isinstance(RLAIFTrigger(dry_run=True).trigger(_spec()), TriggerResult)
def test_tc07_summary():
    assert "RLAIF-Trigger" in RLAIFTrigger(dry_run=True).trigger(_spec()).summary
def test_tc08_note_cloud():
    r = RLAIFTrigger(dry_run=True).trigger(_spec())
    assert "클라우드" in r.note and "GPU SLO" in r.note
def test_tc09_config_builds():
    t = RLAIFTrigger(dry_run=True); cfg = t._config(_spec())
    assert "Llama" in cfg.base_model and cfg.lora_rank == 16
def test_tc10_config_objective_extra():
    cfg = RLAIFTrigger(dry_run=True)._config(_spec())
    assert cfg.extra.get("objective") == "dpo" and cfg.extra.get("rlaif") is True
def test_tc11_baseline_in_note():
    r = RLAIFTrigger(dry_run=True).trigger(_spec(n=10, dw=4))
    assert "0.4" in r.note  # baseline 승률
def test_tc12_dry_run_no_gpu():
    # 이 환경(GPU 없음) dry_run — 실 GPU 미기동, 비용 추정만
    r = RLAIFTrigger(dry_run=True).trigger(_spec())
    assert r.job.get("dry_run") in (True, None) and r.status == "dry_run"
