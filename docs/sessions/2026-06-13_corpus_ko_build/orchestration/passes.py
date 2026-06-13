"""Pass1~3: 거시설계 → 인과비트맵 → 씬브리프. (Pass4 RAG~Pass7 패널은 후속)"""
import json, os
from schema import WorkSpec, Beat, SceneBrief

_HERE=os.path.dirname(__file__)
def _genre_curves():
    p=os.path.join(_HERE,"..","experiments","exp_cb.json")
    try: return json.load(open(p))["genre_curves"]
    except Exception: return {}
GC=_genre_curves()
def t_ideal(genre,pos):
    cur=GC.get(genre) or GC.get("drama") or [0.5]*20
    return round(cur[min(int(pos*len(cur)),len(cur)-1)],3)

# 표준 7기능 아크 (정규위치, 인과부모)
ARC=[("setup",0.04,None),("inciting",0.12,"setup"),("rising",0.30,"inciting"),
     ("midpoint",0.50,"rising"),("crisis",0.68,"midpoint"),("climax",0.85,"crisis"),
     ("resolution",0.96,"climax")]

def pass1_premise(premise:dict)->WorkSpec:
    """IN: {title,genre,n_episodes,master_theme,conflict_axis,core_dilemma,characters[]}
       OUT: WorkSpec. (LLM 확장 훅: arc_summary·characters want/flaw 보강 지점)"""
    return WorkSpec(
        title=premise["title"], genre=premise["genre"], n_episodes=premise.get("n_episodes",1),
        master_theme=premise["master_theme"], conflict_axis=premise["conflict_axis"],
        core_dilemma=premise["core_dilemma"], characters=premise["characters"],
        arc_summary=premise.get("arc_summary", f"{premise['master_theme']}를 축으로 {premise['conflict_axis']} 대립이 {premise['core_dilemma']}로 수렴"))

def pass2_causality(spec:WorkSpec, motifs:list)->list:
    """IN: WorkSpec + 모티프 후보. OUT: Beat[] (심기/회수 분배 + 장르 T_ideal)."""
    beats=[]
    for i,(fn,pos,parent) in enumerate(ARC):
        plant = motifs[:2] if fn in ("setup","inciting") else (motifs[2:3] if fn=="rising" else [])
        payoff = motifs[:1] if fn=="climax" else (motifs[1:2] if fn=="resolution" else [])
        intent={"setup":"세계·인물·결핍 제시","inciting":"균형을 깨는 사건",
                "rising":"갈등 상승·정보 통제","midpoint":"판을 뒤집는 전환",
                "crisis":"최저점·딜레마 직면","climax":"핵심 대결·선택",
                "resolution":"여파·잔향(미해소 여지)"}[fn]
        beats.append(Beat(beat_id=f"B{i+1:02d}",function=fn,pos=pos,causal_parent=parent,
                          intent=intent,plant_motifs=plant,payoff_motifs=payoff,
                          target_tension=t_ideal(spec.genre,pos)))
    return beats

def pass3_scene_brief(spec:WorkSpec, beats:list)->list:
    """IN: WorkSpec+Beat[]. OUT: SceneBrief[] (tension_band·callback·등장인물 결선)."""
    briefs=[]; names=[c["name"] for c in spec.characters]
    for k,b in enumerate(beats):
        tt=b.target_tension
        # 비트 위치에 따라 주요 인물 배치(데모: 주연 우선)
        chars=names[:2] if b.function in("setup","resolution") else names[:3]
        briefs.append(SceneBrief(
            scene_id=f"{spec.title}::S{k+1:02d}", beat_id=b.beat_id,
            slug={"location":"TBD(LLM/RAG)","time":"낮","int_ext":"실내"},
            characters=chars, dramatic_function=b.function,
            targets={"tension_band":[round(max(0,tt-0.12),2),round(min(1,tt+0.12),2)],
                     "conflict_intensity_min":0.2 if b.function in("crisis","climax") else 0.0,
                     "callback_motifs":b.payoff_motifs}))
    return briefs
