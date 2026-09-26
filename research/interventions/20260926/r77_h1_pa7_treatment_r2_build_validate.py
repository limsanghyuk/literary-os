#!/usr/bin/env python3
import json,re,hashlib,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[3]
D=ROOT/"research/interventions/20260926/r77_h1_pa7_treatment_r1"
parts=[(D/f"R77_H1_PA7_TREATMENT_SQ{i:02d}.txt").read_text(encoding="utf-8") for i in range(1,10)]
base="\n\n".join(parts)+"\n"
layer_names=["R77_H1_PA7_TREATMENT_R1_COMPLETION_A.json","R77_H1_PA7_TREATMENT_R1_COMPLETION_B.json","R77_H1_PA7_TREATMENT_R1_COMPLETION_C.json","R77_H1_PA7_TREATMENT_R2_COMPLETION_D.json"]
insert_map={}
for fn in layer_names:
    data=json.loads((D/fn).read_text(encoding="utf-8"))["inserts"]
    for sc,txt in data.items():
        insert_map.setdefault(str(int(sc)),[]).append(txt)

lines=base.splitlines(keepends=True)
out=[]; current=None; flushed=set()
scene_re=re.compile(r"^씬\s+(\d+)\.")
seq_re=re.compile(r"^시퀀스\s+\d+\s+—")
def flush():
    global current
    if current and current in insert_map and current not in flushed:
        if out and out[-1].strip(): out.append("\n")
        for txt in insert_map[current]:
            out.append(txt.strip()+"\n\n")
        flushed.add(current)

for line in lines:
    sm=scene_re.match(line); qm=seq_re.match(line)
    if sm or qm: flush()
    if qm: current=None
    if sm: current=str(int(sm.group(1)))
    out.append(line)
flush()
text="".join(out)
if not text.endswith("\n"): text+="\n"
seqs=[int(x) for x in re.findall(r"(?m)^시퀀스\s+(\d+)\s+—",text)]
scenes=[int(x) for x in re.findall(r"(?m)^씬\s+(\d+)\.",text)]
meta=["R77_","PA7","provider_analog","schema","focus_axis","treatment_residual_intervention"]
res={
 "schema":"R77_H1_PA7_TREATMENT_R2_MECHANICAL_RESULT",
 "date":"2026-09-26","chars":len(text),"sha256":hashlib.sha256(text.encode()).hexdigest(),
 "sequences":len(seqs),"scenes":len(scenes),"applied_scene_count":len(flushed),
 "gates":{
  "chars_ge_40000":len(text)>=40000,
  "sequences_exact_1_to_9":seqs==list(range(1,10)),
  "scenes_exact_1_to_50":scenes==list(range(1,51)),
  "all_50_scenes_have_preseal_realization":len(flushed)==50,
  "metadata_leak_0":not any(t.lower() in text.lower() for t in meta),
  "duplicate_scene_heading_0":len(scenes)==len(set(scenes))
 }
}
res["status"]="PASS" if all(res["gates"].values()) else "FAIL"
(D/"R77_H1_PA7_TREATMENT_R2_FULL_SCREENPLAY.txt").write_text(text,encoding="utf-8")
(D/"R77_H1_PA7_TREATMENT_R2_MECHANICAL_RESULT.json").write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(res,ensure_ascii=False,sort_keys=True))
raise SystemExit(0 if res["status"]=="PASS" else 2)
