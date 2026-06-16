"""test_v770_pareto_router — 파레토 라우팅 + 모드 디스패처 (V770, ADR-230). TC01~15."""
import pytest
from literary_system.finetune.gpu_adapter import GPUProvider, LocalGPUAdapter, LocalPreflight, LocalPreflightResult
from literary_system.learning.provider_router import ProviderRouter, RoutingSignals
from literary_system.learning.pareto_router import (
    ParetoRouter, ParetoCandidate, pareto_frontier, TrainingMode, dispatch_training)
from literary_system.learning.rlaif_orchestrator import RLAIFTrainingSpec

class _OK(LocalPreflight):
    def run(self): return LocalPreflightResult(True, True, 12.0, [], "PASS(sim 4070)")
def _base(): return ProviderRouter(local_adapter=LocalGPUAdapter(preflight=_OK()))
def _pareto(pref): return ParetoRouter(base_router=_base(), preference=pref)
def _spec(m="llama-3.1-8b"): return RLAIFTrainingSpec("/x/dpo.jsonl", 12, 0.58, m, 16, "dpo", "prepared")

def test_tc01_dominance():
    a = ParetoCandidate("local","qlora",0.0,0.75,True); b = ParetoCandidate("runpod","qlora",0.78,0.75,True)
    assert a.dominates(b) and not b.dominates(a)
def test_tc02_frontier_drops_dominated():
    cs = [ParetoCandidate("local","qlora",0.05,0.75,True),
          ParetoCandidate("runpod","qlora",0.78,0.75,True),
          ParetoCandidate("lambda_labs","full_ft",2.98,0.79,True)]
    f = pareto_frontier(cs)
    assert any(c.provider=="local" for c in f) and not any(c.provider=="runpod" for c in f)
def test_tc03_invalid_pref():
    with pytest.raises(ValueError): ParetoRouter(preference="x")
def test_tc04_cost_pref_local():
    assert _pareto("cost").select(_spec(), RoutingSignals()).provider == GPUProvider.LOCAL
def test_tc05_quality_pref_lambda():
    assert _pareto("quality").select(_spec(), RoutingSignals()).provider == GPUProvider.LAMBDA_LABS
def test_tc06_pareto_rule_tag():
    assert _pareto("cost").select(_spec(), RoutingSignals()).rule == "P*"
def test_tc07_quality_estimate_warning():
    d = _pareto("balanced").select(_spec(), RoutingSignals())
    assert any("추정치" in w for w in d.warnings)
def test_tc08_hard_constraint_privacy_wins():
    # 민감 → R2 LOCAL 강제, 파레토 스킵
    d = _pareto("quality").select(_spec(), RoutingSignals(sensitive_corpus=True))
    assert d.provider == GPUProvider.LOCAL and "skip" in d.reason
def test_tc09_candidates_13b_no_local():
    cs = ParetoRouter(base_router=_base()).candidates(_spec("llama-13b"))
    assert not any(c.provider=="local" for c in cs)  # 13B 로컬 불가
def test_tc10_dispatch_cloud():
    r = dispatch_training(_spec(), TrainingMode.CLOUD, RoutingSignals())
    assert r["provider"] == "runpod" and r["status"] == "dry_run"
def test_tc11_dispatch_local():
    r = dispatch_training(_spec(), TrainingMode.LOCAL, RoutingSignals())
    assert r["provider"] == "local" and r["status"] == "dry_run"
def test_tc12_dispatch_hybrid():
    r = dispatch_training(_spec("llama-13b"), TrainingMode.HYBRID, RoutingSignals())
    assert r["mode"] == "hybrid" and len(r["stages"]) == 2
def test_tc13_dispatch_auto():
    r = dispatch_training(_spec(), TrainingMode.AUTO, RoutingSignals())
    assert r["status"] == "dry_run" and r["mode"] == "auto"
def test_tc14_mode_enum():
    assert {m.value for m in TrainingMode} == {"cloud","local","hybrid","auto"}
def test_tc15_export():
    import literary_system.learning as L
    assert hasattr(L,"ParetoRouter") and hasattr(L,"dispatch_training") and hasattr(L,"TrainingMode")
