"""test_v768_provider_router — ProviderRouter 3-모드 라우팅 (V768, ADR-228). TC01~14."""
from literary_system.finetune.gpu_adapter import GPUProvider, LocalGPUAdapter, LocalPreflight
from literary_system.learning.provider_router import (
    ProviderRouter, RoutingSignals, RoutingDecision, validate_routing)
from literary_system.learning.rlaif_orchestrator import RLAIFTrainingSpec

def _spec(model="llama-3.2-3b"):
    return RLAIFTrainingSpec("/x/dpo.jsonl", 12, 0.58, model, 16, "dpo", "prepared")

class _OKPre(LocalPreflight):           # Preflight 강제 PASS (4070 시뮬)
    def run(self):
        from literary_system.finetune.gpu_adapter import LocalPreflightResult
        return LocalPreflightResult(True, True, 12.0, [], "PASS(sim)")

def _router_local_ok():
    return ProviderRouter(local_adapter=LocalGPUAdapter(preflight=_OKPre()))

def test_tc01_r1_force():
    d = _router_local_ok().select(_spec(), RoutingSignals(force_provider=GPUProvider.LAMBDA_LABS))
    assert d.rule == "R1" and d.provider == GPUProvider.LAMBDA_LABS
def test_tc02_r2_privacy_local():
    d = _router_local_ok().select(_spec(), RoutingSignals(sensitive_corpus=True))
    assert d.rule == "R2" and d.provider == GPUProvider.LOCAL
def test_tc03_r2_privacy_oversize_still_local():
    d = _router_local_ok().select(_spec("llama-70b"), RoutingSignals(sensitive_corpus=True))
    assert d.provider == GPUProvider.LOCAL and d.warnings  # 경고는 있되 클라우드 금지
def test_tc04_r3_capacity_cloud():
    d = _router_local_ok().select(_spec("llama-70b"), RoutingSignals())
    assert d.rule == "R3" and d.provider == GPUProvider.RUNPOD
def test_tc05_r4_biweekly_cloud():
    d = _router_local_ok().select(_spec(), RoutingSignals(biweekly_scheduled=True))
    assert d.rule == "R4" and d.provider == GPUProvider.RUNPOD
def test_tc06_r5_default_local():
    d = _router_local_ok().select(_spec(), RoutingSignals())
    assert d.rule == "R5" and d.provider == GPUProvider.LOCAL
def test_tc07_r6_fallback_when_preflight_fail():
    # 기본 LocalGPUAdapter(이 샌드박스 GPU 없음) → R6 폴백
    d = ProviderRouter().select(_spec(), RoutingSignals())
    assert d.rule == "R6" and d.provider == GPUProvider.RUNPOD and d.fallback_from == "local"
def test_tc08_decision_to_dict():
    assert "provider" in _router_local_ok().select(_spec()).to_dict()
def test_tc09_gate_sensitive_never_cloud():
    sig = RoutingSignals(sensitive_corpus=True)
    d = _router_local_ok().select(_spec(), sig)
    assert validate_routing(d, sig)["passed"]
def test_tc10_gate_detects_violation():
    # 인위적 위반: 민감인데 cloud
    bad = RoutingDecision(GPUProvider.RUNPOD, "x", True, "R?")
    assert not validate_routing(bad, RoutingSignals(sensitive_corpus=True))["passed"]
def test_tc11_route_trigger_end2end():
    import tempfile, os
    from literary_system.learning.rlaif_orchestrator import RLAIFOrchestrator
    from literary_system.learning.loop_c import PreferencePair
    fd, out = tempfile.mkstemp(suffix=".jsonl"); os.close(fd)
    pairs = [PreferencePair.from_pass7("s","thriller",f"d{i} 긴글",f"r{i}","draft" if i<4 else "ref",f"r::{i}") for i in range(12)]
    spec = RLAIFOrchestrator().prepare(pairs, out)
    dec, res = _router_local_ok().route_trigger(spec, RoutingSignals())
    assert dec.provider == GPUProvider.LOCAL and res.status == "dry_run"
def test_tc12_cloud_provider_configurable():
    r = ProviderRouter(cloud_provider=GPUProvider.LAMBDA_LABS, local_adapter=LocalGPUAdapter(preflight=_OKPre()))
    assert r.select(_spec("llama-70b"), RoutingSignals()).provider == GPUProvider.LAMBDA_LABS
def test_tc13_export():
    import literary_system.learning as L
    assert hasattr(L, "ProviderRouter") and hasattr(L, "validate_routing")
def test_tc14_gate_cli():
    from tools.run_gpu_routing_gate import run_g_gpu_routing
    ok, rows = run_g_gpu_routing()
    assert ok and len(rows) == 6
