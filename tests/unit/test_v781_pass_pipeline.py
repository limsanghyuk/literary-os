"""test_v781 — 생성 본체 7-pass L4 (V781, ADR-241). TC01~14."""
from literary_system.generation import PassPipeline, GenerationResult, WorkSpec, Beat, SceneBrief, STANDARD_ARC
_PREM={"title":"균열","genre":"thriller","n_episodes":1,"master_theme":"신뢰 붕괴",
       "conflict_axis":"형사 vs 고발자","core_dilemma":"정의와 충성",
       "characters":[{"name":"한도","role":"형사"},{"name":"세진","role":"고발자"},{"name":"국장","role":"권력"}]}
def _gen(b,refs): return f"{b.characters[0]}는 멈췄다. 숨을 골랐다. {' '.join(b.targets['callback_motifs'])}"
def _judge(d,r): return "draft" if len(d)>=len(r) else "ref"
def _ret(b): return [f"명작 {b.scene_id} 긴 참조 텍스트 한 줄 여기"]

def test_tc01_pass1_workspec():
    s=PassPipeline().pass1_premise(_PREM); assert isinstance(s,WorkSpec) and s.title=="균열"
def test_tc02_pass2_seven_beats():
    p=PassPipeline(); s=p.pass1_premise(_PREM); b=p.pass2_causality(s,["a","b","c"])
    assert len(b)==7 and [x.function for x in b]==[f for f,_,_ in STANDARD_ARC]
def test_tc03_pass2_tension_from_curve():
    p=PassPipeline(); s=p.pass1_premise(_PREM); b=p.pass2_causality(s,["a"])
    assert all(0<=x.target_tension<=1 for x in b)
def test_tc04_pass3_briefs():
    p=PassPipeline(); s=p.pass1_premise(_PREM); b=p.pass2_causality(s,["a","b"]); br=p.pass3_scene_brief(s,b)
    assert len(br)==7 and all(isinstance(x,SceneBrief) for x in br)
def test_tc05_pass4_rag_attaches():
    p=PassPipeline(); s=p.pass1_premise(_PREM); br=p.pass3_scene_brief(s,p.pass2_causality(s,["a"]))
    p.pass4_rag(br,_ret); assert all(x.rag_refs for x in br)
def test_tc06_pass5_generate_hook():
    p=PassPipeline(); s=p.pass1_premise(_PREM); br=p.pass3_scene_brief(s,p.pass2_causality(s,["a"]))
    p.pass5_draft(br,_gen); assert all(x.draft and not x.draft.startswith("[STUB") for x in br)
def test_tc07_pass5_stub_when_no_hook():
    p=PassPipeline(); s=p.pass1_premise(_PREM); br=p.pass3_scene_brief(s,p.pass2_causality(s,["a"]))
    p.pass5_draft(br,None); assert all(x.draft.startswith("[STUB") for x in br)
def test_tc08_pass6_gate_flags_stub():
    p=PassPipeline(); s=p.pass1_premise(_PREM); br=p.pass3_scene_brief(s,p.pass2_causality(s,["a"]))
    p.pass5_draft(br,None); issues=p.pass6_gate(br); assert len(issues)>0
def test_tc09_pass6_gate_clean_with_callbacks():
    p=PassPipeline(); s=p.pass1_premise(_PREM); b=p.pass2_causality(s,["비밀","배신","구원"])
    br=p.pass3_scene_brief(s,b); p.pass4_rag(br,_ret); p.pass5_draft(br,_gen)
    issues=p.pass6_gate(br); assert isinstance(issues,list)
def test_tc10_pass7_panel_pairs():
    p=PassPipeline(); s=p.pass1_premise(_PREM); b=p.pass2_causality(s,["a"]); br=p.pass3_scene_brief(s,b)
    p.pass4_rag(br,_ret); p.pass5_draft(br,_gen); panel=p.pass7_panel(br,_judge)
    assert len(panel)==7 and all(x["winner"] in ("draft","ref","tie") for x in panel)
def test_tc11_run_end2end():
    res=PassPipeline().run(_PREM,["비밀","배신","구원"],retrieve=_ret,generate=_gen,judge=_judge)
    assert isinstance(res,GenerationResult) and len(res.briefs)==7 and len(res.panel)==7
def test_tc12_result_to_dict():
    d=PassPipeline().run(_PREM,retrieve=_ret,generate=_gen,judge=_judge).to_dict()
    assert "spec" in d and "beats" in d and "panel" in d
def test_tc13_loop_c_pairs_from_panel():
    # Pass7 패널이 loop-C 선호쌍(winner+draft+ref) 형태 제공
    res=PassPipeline().run(_PREM,retrieve=_ret,generate=_gen,judge=_judge)
    pairs=[p for p in res.panel if p["winner"] in ("draft","ref")]
    assert all("draft" in p and "ref" in p and "func" in p for p in pairs)
def test_tc14_export():
    import literary_system.generation as G
    assert hasattr(G,"PassPipeline") and hasattr(G,"SceneBrief")
