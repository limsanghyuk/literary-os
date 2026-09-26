#!/usr/bin/env python3
import json,re,hashlib,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[3]
TD=ROOT/"research/interventions/20260926/r77_h1_pa7_treatment_r1"
CD=ROOT/"research/interventions/20260926/r77_h1_pa7_control_r1"
parts=[(TD/f"R77_H1_PA7_TREATMENT_SQ{i:02d}.txt").read_text(encoding="utf-8") for i in range(1,10)]
base="\n\n".join(parts)+"\n"
layer_names=[
"R77_H1_PA7_TREATMENT_R1_COMPLETION_A.json",
"R77_H1_PA7_TREATMENT_R1_COMPLETION_B.json",
"R77_H1_PA7_TREATMENT_R1_COMPLETION_C.json",
"R77_H1_PA7_TREATMENT_R2_COMPLETION_D.json",
"R77_H1_PA7_TREATMENT_R3_COMPLETION_E.json"]
insert_map={}
for fn in layer_names:
    data=json.loads((TD/fn).read_text(encoding="utf-8"))["inserts"]
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
treatment="".join(out)
if not treatment.endswith("\n"): treatment+="\n"

control=(CD/"R77_H1_PA7_CONTROL_R4_FULL_SCREENPLAY.txt").read_text(encoding="utf-8")

def parse_scenes(txt):
    ms=list(re.finditer(r"(?m)^씬\s+(\d+)\.\s*[^\n]*$",txt))
    out={}
    for i,m in enumerate(ms):
        end=ms[i+1].start() if i+1<len(ms) else len(txt)
        out[int(m.group(1))]=re.sub(r"\s+"," ",txt[m.start():end]).strip()
    return out

seqs=[int(x) for x in re.findall(r"(?m)^시퀀스\s+(\d+)\s+—",treatment)]
scenes=[int(x) for x in re.findall(r"(?m)^씬\s+(\d+)\.",treatment)]
ts=parse_scenes(treatment); cs=parse_scenes(control)
identical=[i for i in range(1,51) if ts.get(i)==cs.get(i)]
meta=["R77_","PA7","provider_analog","schema","focus_axis","treatment_residual_intervention"]
diff=abs(len(treatment)-len(control))
pct=diff/min(len(treatment),len(control))
res={
 "schema":"R77_H1_PA7_TREATMENT_R3_FINAL_MECHANICAL_RESULT",
 "date":"2026-09-26",
 "treatment":{"chars":len(treatment),"sha256":hashlib.sha256(treatment.encode()).hexdigest(),"sequences":len(seqs),"scenes":len(scenes)},
 "control_reference":{"chars":len(control),"sha256":hashlib.sha256(control.encode()).hexdigest()},
 "matched_length":{"absolute_diff":diff,"pct_of_shorter":pct},
 "applied_scene_count":len(flushed),
 "identical_full_scenes":identical,
 "gates":{
  "treatment_chars_ge_40000":len(treatment)>=40000,
  "treatment_chars_le_42000":len(treatment)<=42000,
  "control_chars_ge_40000":len(control)>=40000,
  "matched_length_diff_le_10pct":pct<=0.10,
  "sequences_exact_1_to_9":seqs==list(range(1,10)),
  "scenes_exact_1_to_50":scenes==list(range(1,51)),
  "all_50_scenes_have_preseal_realization":len(flushed)==50,
  "metadata_leak_0":not any(t.lower() in treatment.lower() for t in meta),
  "duplicate_scene_heading_0":len(scenes)==len(set(scenes)),
  "treatment_control_sha_different":hashlib.sha256(treatment.encode()).hexdigest()!=hashlib.sha256(control.encode()).hexdigest(),
  "identical_full_scene_0":len(identical)==0
 }
}
res["status"]="PASS" if all(res["gates"].values()) else "FAIL"
(TD/"R77_H1_PA7_TREATMENT_R3_FINAL_SCREENPLAY.txt").write_text(treatment,encoding="utf-8")
(TD/"R77_H1_PA7_TREATMENT_R3_FINAL_MECHANICAL_RESULT.json").write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(res,ensure_ascii=False,sort_keys=True))
raise SystemExit(0 if res["status"]=="PASS" else 2)
