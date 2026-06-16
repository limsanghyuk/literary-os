"""run_gpu_routing_gate.py — G_GPU_ROUTING (V768). 라우팅 5규칙×안전성 검증."""
import sys
from literary_system.finetune.gpu_adapter import GPUProvider
from literary_system.learning.provider_router import ProviderRouter, RoutingSignals, validate_routing
from literary_system.learning.rlaif_orchestrator import RLAIFTrainingSpec

def _spec(model):
    return RLAIFTrainingSpec("/x/dpo.jsonl", 12, 0.58, model, 16, "dpo", "prepared")

def run_g_gpu_routing():
    r = ProviderRouter(); rows = []
    scen = [
        ("민감+3B", _spec("llama-3.2-3b"), RoutingSignals(sensitive_corpus=True)),
        ("민감+70B", _spec("llama-70b"), RoutingSignals(sensitive_corpus=True)),
        ("비민감+70B", _spec("llama-70b"), RoutingSignals()),
        ("biweekly+3B", _spec("llama-3.2-3b"), RoutingSignals(biweekly_scheduled=True)),
        ("기본+3B", _spec("llama-3.2-3b"), RoutingSignals()),
        ("force=Lambda", _spec("llama-3.2-3b"), RoutingSignals(force_provider=GPUProvider.LAMBDA_LABS)),
    ]
    allok = True
    for name, sp, sig in scen:
        dec = r.select(sp, sig); v = validate_routing(dec, sig)
        allok &= v["passed"]
        rows.append((name, dec.rule, dec.provider.value, v["passed"]))
    return allok, rows

if __name__ == "__main__":
    ok, rows = run_g_gpu_routing()
    print(f"[{'PASS' if ok else 'FAIL'}] G_GPU_ROUTING")
    for n, rule, prov, p in rows:
        print(f"  {'OK' if p else 'XX'} {n}: {rule}→{prov}")
    sys.exit(0 if ok else 1)
