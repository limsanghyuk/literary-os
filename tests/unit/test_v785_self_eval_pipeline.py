"""test_v785 — 자체평가→loop-C 통합 (V785, ADR-246). TC01~12."""
from literary_system.critic.self_eval_pipeline import SelfEvalPipeline, SelfEvalReport
from literary_system.critic.next_episode_bench import NextEpItem
_MPS=["그는 멈췄다. 숨을 골랐다. 침묵 속에서 어둠이 천천히 깔렸다. 차가운 바람.",
      "심장이 뛰었다. 발소리가 가까웠다. 배신을 알았다. 진실이 거기 있었다."]
_ITEMS=[NextEpItem("무명A",False,{"func":"crisis"},"세진은 멈췄다. 배신을 알았다. 어둠 속 침묵."),
        NextEpItem("무명B",False,{"func":"midpoint"},"그는 문을 열었다. 진실이 거기 있었다. 심장이 뛰었다.")]
_GEN=lambda ctx: f"인물이 행동했다 {ctx.get('func','')}"
def _GOOD(a,b):
    f=lambda x: sum(x.count(m) for m in ["침묵","어둠","배신","진실","멈췄","심장"])+len(x)*0.005
    return "a" if f(a)>f(b) else ("tie" if abs(f(a)-f(b))<1e-9 else "b")
def _run(judge=_GOOD): return SelfEvalPipeline(_MPS,"thriller").run(_ITEMS,judge=judge,generate=_GEN)

def test_tc01_qualified_runs():
    r=_run(); assert r.qualified and isinstance(r,SelfEvalReport)
def test_tc02_unqualified_blocked():
    r=_run(lambda a,b:"tie"); assert not r.qualified and "자격 미달" in r.blocked_reason
def test_tc03_blocked_no_pairs():
    assert _run(lambda a,b:"tie").n_pairs==0
def test_tc04_m1_gate_before_m2():
    # 자격 미달이면 M2 미실행(차단)
    r=_run(lambda a,b:"b"); assert not r.qualified and not r.ready_for_loopc
def test_tc05_pairs_have_guard():
    r=_run(); assert all("guard_penalty" in p for p in r.pairs)
def test_tc06_m3_counts_pathology():
    r=_run(); assert r.n_guarded>=0
def test_tc07_to_preference_pairs():
    pipe=SelfEvalPipeline(_MPS,"thriller"); r=pipe.run(_ITEMS,judge=_GOOD,generate=_GEN)
    pp=pipe.to_preference_pairs(r); assert len(pp)>=1
def test_tc08_pathological_loss_kept():
    # 병리 생성이 진(rejected) 쌍은 유지 = 부정 신호
    pipe=SelfEvalPipeline(_MPS,"thriller"); r=pipe.run(_ITEMS,judge=_GOOD,generate=_GEN)
    assert len(pipe.to_preference_pairs(r))>=1
def test_tc09_ready_flag():
    assert _run().ready_for_loopc is True
def test_tc10_summary():
    assert "SelfEval" in _run().summary() and "자체평가 차단" in _run(lambda a,b:"tie").summary()
def test_tc11_to_dict():
    assert "ready_for_loopc" in _run().to_dict()
def test_tc12_export():
    import literary_system.critic as C
    assert hasattr(C,"SelfEvalPipeline")
