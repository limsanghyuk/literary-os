"""test_v773_cloud_wiring — dispatch→RealRunPod 실 배선 (V773, ADR-233). TC01~13."""
from literary_system.finetune.gpu_adapter import GPUProvider, GPUJobStatus, GPUJobRequest
from literary_system.finetune.runpod_real_adapter import RealRunPodAdapter
from literary_system.finetune.lora_job_runner import LoRAJobRunner
from literary_system.learning.rlaif_trigger import RLAIFTrigger
from literary_system.learning.pareto_router import dispatch_training, TrainingMode
from literary_system.learning.provider_router import RoutingSignals
from literary_system.learning.rlaif_orchestrator import RLAIFOrchestrator, RLAIFTrainingSpec
from literary_system.learning.loop_c import PreferencePair
import tempfile, os

def _spec(model="llama-3.1-8b", prepared=True):
    if not prepared: return RLAIFTrainingSpec("/x/dpo.jsonl",3,0.5,model,16,"dpo","blocked")
    fd,o=tempfile.mkstemp(suffix=".jsonl");os.close(fd)
    pairs=[PreferencePair.from_pass7("s","t",f"d{i} 긴텍스트",f"r{i}","draft" if i<4 else "ref",f"r::{i}") for i in range(12)]
    return RLAIFOrchestrator().prepare(pairs,o)
def _fake(rec):
    def t(m,u,h,b):
        rec.append(m)
        return (200,[]) if m=="GET" else (201,{"id":"pod_x"})
    return t

# 주입 경로
def test_tc01_runner_accepts_adapter():
    rec=[]; a=RealRunPodAdapter(api_key="k",transport=_fake(rec))
    r=LoRAJobRunner(provider=GPUProvider.RUNPOD,dry_run=False,adapter=a)
    assert r._adapter is a
def test_tc02_runner_default_mock():
    from literary_system.finetune.gpu_adapter import RunPodAdapter
    assert isinstance(LoRAJobRunner(provider=GPUProvider.RUNPOD)._adapter, RunPodAdapter)
def test_tc03_trigger_injects_adapter():
    rec=[]; a=RealRunPodAdapter(api_key="k",transport=_fake(rec))
    RLAIFTrigger(provider=GPUProvider.RUNPOD,dry_run=False,adapter=a).trigger(_spec())
    assert "POST" in rec
def test_tc04_trigger_dry_run_no_network():
    rec=[]; a=RealRunPodAdapter(api_key="k",transport=_fake(rec))
    RLAIFTrigger(provider=GPUProvider.RUNPOD,dry_run=True,adapter=a).trigger(_spec())
    assert rec == []   # dry_run → 네트워크 미호출

# dispatch 3모드 유지
def test_tc05_dispatch_local():
    assert dispatch_training(_spec("llama-3.2-3b"),TrainingMode.LOCAL,RoutingSignals())["provider"]=="local"
def test_tc06_dispatch_cloud_nokey_mock():
    r=dispatch_training(_spec(),TrainingMode.CLOUD,RoutingSignals())
    assert r["provider"]=="runpod" and r["real_adapter"] is False
def test_tc07_dispatch_cloud_real_key():
    r=dispatch_training(_spec(),TrainingMode.CLOUD,RoutingSignals(),real=True,api_key="rpa_K")
    assert r["provider"]=="runpod" and r["real_adapter"] is True
def test_tc08_dispatch_hybrid_maintained():
    r=dispatch_training(_spec("llama-13b"),TrainingMode.HYBRID,RoutingSignals())
    assert r["mode"]=="hybrid" and len(r["stages"])==2
def test_tc09_dispatch_hybrid_cloud_real():
    r=dispatch_training(_spec("llama-13b"),TrainingMode.HYBRID,RoutingSignals(),real=True,api_key="rpa_K")
    assert r["cloud_stage"]["real_adapter"] is True
def test_tc10_env_key_auto_real(monkeypatch):
    monkeypatch.setenv("RUNPOD_API_KEY","rpa_ENV")
    r=dispatch_training(_spec(),TrainingMode.CLOUD,RoutingSignals())
    assert r["real_adapter"] is True   # 키 있으면 자동 실 어댑터
def test_tc11_dispatch_auto_still_works():
    r=dispatch_training(_spec("llama-3.1-8b"),TrainingMode.AUTO,RoutingSignals())
    assert r["status"] in ("dry_run","submitted","not_ready")
def test_tc12_local_never_real_adapter():
    r=dispatch_training(_spec("llama-3.2-3b"),TrainingMode.LOCAL,RoutingSignals(),real=True,api_key="rpa_K")
    assert r["real_adapter"] is False   # 로컬은 실 RunPod 어댑터 미사용
def test_tc13_key_not_leaked():
    import json
    r=dispatch_training(_spec(),TrainingMode.CLOUD,RoutingSignals(),real=True,api_key="rpa_SECRET")
    assert "rpa_SECRET" not in json.dumps(r)
