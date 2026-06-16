"""test_v769_split_pipeline — 하이브리드 분업 PoC (V769, ADR-229). TC01~13."""
from literary_system.finetune.gpu_adapter import LocalGPUAdapter, LocalPreflight, LocalPreflightResult, GPUProvider
from literary_system.learning.provider_router import ProviderRouter, RoutingSignals
from literary_system.learning.split_pipeline import SplitPipeline, SplitReport, StagePlan, run_split_poc

class _OK(LocalPreflight):
    def run(self): return LocalPreflightResult(True, True, 12.0, [], "PASS(sim 4070)")
def _router(): return ProviderRouter(local_adapter=LocalGPUAdapter(preflight=_OK()))
_JUDGE = lambda d, r: "draft" if len(d) >= len(r) else "ref"
_CANDS = [("c1","짧음"),("c2","조금 더 긴 후보"),("c3","가장 길고 풍부한 후보 본문 텍스트")]
_REFS = ["레퍼런스 명작", "또 다른 레퍼런스"]

def test_tc01_plan_type():
    assert isinstance(SplitPipeline(router=_router()).plan(RoutingSignals()), SplitReport)
def test_tc02_stagea_local():
    rep = SplitPipeline(router=_router()).plan(RoutingSignals())
    assert rep.stages[0].provider == "local" and rep.stages[0].cost_usd == 0.0
def test_tc03_stageb_cloud_for_13b():
    rep = SplitPipeline(router=_router()).plan(RoutingSignals())  # large=13b
    assert rep.stages[1].provider == "runpod" and rep.stages[1].rule == "R3"
def test_tc04_savings_positive_13b():
    rep = SplitPipeline(router=_router()).plan(RoutingSignals())
    assert rep.savings_usd > 0 and 0 < rep.savings_pct < 100
def test_tc05_8b_full_local_max_savings():
    rep = SplitPipeline(router=_router(), large_model="llama-3.1-8b").plan(RoutingSignals())
    assert rep.stages[1].provider == "local" and rep.savings_pct == 100.0
def test_tc06_electricity_recorded():
    rep = SplitPipeline(router=_router()).plan(RoutingSignals())
    assert rep.stages[0].electricity_usd > 0
def test_tc07_select_candidates_topk():
    top = SplitPipeline(router=_router()).select_candidates(_CANDS, _REFS, _JUDGE, top_k=1)
    alls = SplitPipeline(router=_router()).select_candidates(_CANDS, _REFS, _JUDGE, top_k=3)
    assert len(top) == 1 and top[0].reward == max(s.reward for s in alls)  # 최고 보상 선별
def test_tc08_select_sorted_desc():
    top = SplitPipeline(router=_router()).select_candidates(_CANDS, _REFS, _JUDGE, top_k=3)
    assert top[0].reward >= top[-1].reward
def test_tc09_run_poc_end2end():
    rep = run_split_poc(_CANDS, _REFS, _JUDGE, RoutingSignals(), SplitPipeline(router=_router()))
    assert rep.selected and rep.hybrid_cost_usd <= rep.all_cloud_cost_usd
def test_tc10_report_to_dict():
    d = SplitPipeline(router=_router()).plan(RoutingSignals()).to_dict()
    assert "stages" in d and "savings_pct" in d
def test_tc11_summary_str():
    assert "Split-PoC" in SplitPipeline(router=_router()).plan(RoutingSignals()).summary
def test_tc12_sensitive_forces_both_local():
    # 민감 코퍼스: StageB 13B도 LOCAL 강제(클라우드 금지) — 경고 동반
    rep = SplitPipeline(router=_router()).plan(RoutingSignals(sensitive_corpus=True))
    assert all(s.provider == "local" for s in rep.stages)
def test_tc13_export():
    import literary_system.learning as L
    assert hasattr(L, "SplitPipeline") and hasattr(L, "run_split_poc")
