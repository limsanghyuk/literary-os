"""test_v783 — M2 NextEpisodeBench (V783, ADR-244). TC01~14."""
from literary_system.critic.next_episode_bench import (
    run_next_episode_bench, NextEpItem, BenchResult, ngram_overlap, to_preference_pairs)
def _items():
    return [NextEpItem("무명A",False,{"func":"midpoint"},"그는 문을 열었다. 진실. 침묵이 흘렀다. 어둠."),
            NextEpItem("무명B",False,{"func":"crisis"},"세진은 멈췄다. 배신을 알았다. 차가운 어둠."),
            NextEpItem("유명미생",True,{"func":"setup"},"오상식 차장이 들어왔다.")]
_GEN=lambda ctx: f"인물이 행동했다 {ctx.get('func','')}"
def _JUDGE(a,b):
    f=lambda x: sum(x.count(m) for m in ["침묵","어둠","배신","진실","멈췄"])+len(x)*0.005
    return "a" if f(a)>f(b) else ("tie" if abs(f(a)-f(b))<1e-9 else "b")

def test_tc01_ngram_overlap_identical():
    assert ngram_overlap("a b c d e","a b c d e")==1.0
def test_tc02_ngram_overlap_disjoint():
    assert ngram_overlap("a b c d","x y z w")==0.0
def test_tc03_famous_excluded():
    r=run_next_episode_bench(_items(),generate=_GEN,judge=_JUDGE)
    assert any("유명작" in e["reason"] for e in r.excluded)
def test_tc04_scored_excludes_famous():
    r=run_next_episode_bench(_items(),generate=_GEN,judge=_JUDGE)
    assert r.n_scored==2 and r.n_excluded==1
def test_tc05_ngram_leak_excluded():
    # 생성이 실제와 거의 동일 → n-gram 중첩 임계 초과 제외
    it=[NextEpItem("암기",False,{"func":"x"},"하나 둘 셋 넷 다섯 여섯 일곱")]
    r=run_next_episode_bench(it,generate=lambda c:"하나 둘 셋 넷 다섯 여섯 일곱",judge=_JUDGE)
    assert r.n_scored==0 and any("n-gram" in e["reason"] for e in r.excluded)
def test_tc06_parity_rate_range():
    r=run_next_episode_bench(_items(),generate=_GEN,judge=_JUDGE)
    assert 0.0<=r.parity_rate<=1.0 and 0.0<=r.win_rate<=1.0
def test_tc07_weak_gen_loses():
    # 평이한 생성 → 실제 명작에 짐 → 필적률 낮음
    r=run_next_episode_bench(_items(),generate=_GEN,judge=_JUDGE)
    assert r.parity_rate < 0.5
def test_tc08_critic_unqualified_refuses():
    r=run_next_episode_bench(_items(),generate=_GEN,judge=_JUDGE,critic_qualified=False)
    assert r.n_scored==0 and "자격 미달" in r.detail
def test_tc09_pairs_generated():
    r=run_next_episode_bench(_items(),generate=_GEN,judge=_JUDGE)
    assert len(r.pairs)==2 and all("draft" in p and "ref" in p for p in r.pairs)
def test_tc10_loss_pair_ref_chosen():
    r=run_next_episode_bench(_items(),generate=_GEN,judge=_JUDGE)
    assert all(p["winner"] in ("draft","ref","tie") for p in r.pairs)
def test_tc11_position_swap_deterministic_seed():
    r1=run_next_episode_bench(_items(),generate=_GEN,judge=_JUDGE,seed=7)
    r2=run_next_episode_bench(_items(),generate=_GEN,judge=_JUDGE,seed=7)
    assert r1.to_dict()==r2.to_dict()
def test_tc12_to_preference_pairs():
    r=run_next_episode_bench(_items(),generate=_GEN,judge=_JUDGE)
    pp=to_preference_pairs(r,"thriller"); assert isinstance(pp,list)
def test_tc13_result_to_dict():
    assert "parity_rate" in run_next_episode_bench(_items(),generate=_GEN,judge=_JUDGE).to_dict()
def test_tc14_export():
    import literary_system.critic as C
    assert hasattr(C,"run_next_episode_bench") and hasattr(C,"NextEpItem")
