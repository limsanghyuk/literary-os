"""test_v782 — M1 Critic 자격검정 (V782, ADR-243). TC01~14."""
from literary_system.critic.critic_qualification import (
    qualify_critic, QualificationResult, degrade, build_ladder, DegradeAxis, WIN_MIN)
_MP=["그는 멈췄다. 숨을 골랐다. 다시 한 걸음. 침묵 속에서 어둠이 천천히 깔렸다. 차가운 바람이 불었다.",
     "심장이 뛰었다. 발소리가 가까웠다. 그저 기다렸다. 긴장이 흘렀다."]
def _good(a,b):
    f=lambda x: sum(x.count(m) for m in ["멈췄","숨","침묵","어둠","천천히","심장","긴장","빛났"])+len(x)*0.01
    return "a" if f(a)>f(b) else ("tie" if abs(f(a)-f(b))<1e-9 else "b")

def test_tc01_degrade_zero_severity_identity():
    assert degrade(_MP[0], DegradeAxis.EMOTION, 0.0)==_MP[0]
def test_tc02_degrade_changes_text():
    assert degrade(_MP[0], DegradeAxis.EMOTION, 1.0)!=_MP[0]
def test_tc03_degrade_causality_shuffles():
    d=degrade(_MP[0], DegradeAxis.CAUSALITY, 1.0); assert d!=_MP[0] and len(d)>0
def test_tc04_degrade_foreshadow_removes():
    d=degrade(_MP[0], DegradeAxis.FORESHADOW, 0.5); assert len(d)<=len(_MP[0])
def test_tc05_ladder_len():
    L=build_ladder(_MP[0], DegradeAxis.EMOTION, (0.25,0.5,0.75,1.0)); assert len(L)==4
def test_tc06_ladder_severity_order():
    L=build_ladder(_MP[0], DegradeAxis.DICTION); assert [r.severity for r in L]==sorted([r.severity for r in L])
def test_tc07_good_critic_qualifies():
    r=qualify_critic(_good,_MP); assert r.passed and r.win_rate>=WIN_MIN
def test_tc08_blind_critic_fails():
    r=qualify_critic(lambda a,b:"tie",_MP); assert not r.passed and r.win_rate==0.5
def test_tc09_inverted_critic_fails():
    r=qualify_critic(lambda a,b:"b",_MP); assert not r.passed and r.win_rate==0.0
def test_tc10_result_type_and_axes():
    r=qualify_critic(_good,_MP); assert isinstance(r,QualificationResult) and len(r.per_axis)==4
def test_tc11_per_axis_curve_monotone_flag():
    r=qualify_critic(_good,_MP)
    assert all("curve" in d and "monotone" in d for d in r.per_axis.values())
def test_tc12_causality_axis_weakness_detected():
    # 길이/키워드 judge는 인과 단절 못 가림 → 해당 축 평탄(변별 약함) 드러남
    r=qualify_critic(_good,_MP)
    assert r.per_axis["break_causality"]["mean_win"] < r.per_axis["flatten_emotion"]["mean_win"]
def test_tc13_to_dict():
    assert "win_rate" in qualify_critic(_good,_MP).to_dict()
def test_tc14_export():
    import literary_system.critic as C
    assert hasattr(C,"qualify_critic") and hasattr(C,"DegradeAxis")
