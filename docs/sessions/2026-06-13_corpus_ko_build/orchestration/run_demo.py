import sys,os,json
sys.path.insert(0,os.path.dirname(__file__))
from passes import pass1_premise, pass2_causality, pass3_scene_brief
from schema import dump
PREMISE={
 "title":"균열","genre":"thriller","n_episodes":1,
 "master_theme":"정의와 복수의 경계",
 "conflict_axis":"진실을 쫓는 형사 vs 조직을 지키려는 내부자",
 "core_dilemma":"법을 지킬 것인가, 정의를 위해 법을 넘을 것인가",
 "characters":[{"name":"강도훈","role":"주인공/형사","want":"진실규명","flaw":"분노조절"},
               {"name":"서민재","role":"적대자/내부자","want":"조직보호","flaw":"가족집착"},
               {"name":"윤하경","role":"조력자/검사","want":"기소","flaw":"불신"}]}
MOTIFS=["낡은 회중시계","빗속 골목","무전기 잡음"]
spec=pass1_premise(PREMISE)
beats=pass2_causality(spec,MOTIFS)
briefs=pass3_scene_brief(spec,beats)
out={"workspec":dump(spec),"beats":[dump(b) for b in beats],"scene_briefs":[dump(s) for s in briefs]}
json.dump(out,open(os.path.join(os.path.dirname(__file__),"demo_output.json"),"w"),ensure_ascii=False,indent=1)
print("WorkSpec:",spec.title,"|",spec.genre,"|",spec.conflict_axis)
print(f"\nBeats ({len(beats)}):")
for b in beats: print(f"  {b.beat_id} {b.function:10} pos={b.pos} T_ideal={b.target_tension} plant={b.plant_motifs} payoff={b.payoff_motifs}")
print(f"\nSceneBriefs ({len(briefs)}) — 일부:")
for s in briefs[:4]:
    print(f"  {s.scene_id} [{s.dramatic_function}] tension_band={s.targets['tension_band']} callback={s.targets['callback_motifs']} chars={s.characters}")
print("\n→ demo_output.json 저장")
