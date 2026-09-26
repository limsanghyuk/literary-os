#!/usr/bin/env python3
import json,re,hashlib,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[3]
D=ROOT/"research/interventions/20260926/r77_h1_pa7_treatment_r1"
parts=[(D/f"R77_H1_PA7_TREATMENT_SQ{i:02d}.txt").read_text(encoding="utf-8") for i in range(1,10)]
text="\n\n".join(parts)+"\n"
ins={}
for name in ["A","B","C"]:
    ins.update(json.loads((D/f"R77_H1_PA7_TREATMENT_R1_COMPLETION_{name}.json").read_text(encoding="utf-8"))["inserts"])
for sc in sorted([int(k) for k in ins], reverse=True):
    start=re.search(rf"(?m)^씬\s+0*{sc}\.\s*[^\n]*$",text)
    if not start: raise SystemExit(f"scene start missing {sc}")
    if sc<50:
        nxt=re.search(rf"(?m)^씬\s+0*{sc+1}\.\s*[^\n]*$",text[start.end():])
        if not nxt: raise SystemExit(f"next scene missing {sc+1}")
        pos=start.end()+nxt.start()
    else:
        pos=len(text)
    text=text[:pos].rstrip()+"\n\n"+ins[str(sc)].strip()+"\n\n"+text[pos:].lstrip("\n")
if not text.endswith("\n"): text+="\n"
seqs=[int(x) for x in re.findall(r"(?m)^시퀀스\s+(\d+)\s+—",text)]
scenes=[int(x) for x in re.findall(r"(?m)^씬\s+(\d+)\.",text)]
meta=["R77_","PA7","provider_analog","schema","focus_axis","treatment_residual_intervention"]
res={"schema":"R77_H1_PA7_TREATMENT_R1_MECHANICAL_RESULT","date":"2026-09-26",
"chars":len(text),"sha256":hashlib.sha256(text.encode()).hexdigest(),"sequences":len(seqs),"scenes":len(scenes),
"gates":{"chars_ge_40000":len(text)>=40000,"sequences_exact_1_to_9":seqs==list(range(1,10)),
"scenes_exact_1_to_50":scenes==list(range(1,51)),"metadata_leak_0":not any(t.lower() in text.lower() for t in meta),
"duplicate_scene_heading_0":len(scenes)==len(set(scenes))}}
res["status"]="PASS" if all(res["gates"].values()) else "FAIL"
(D/"R77_H1_PA7_TREATMENT_R1_FULL_SCREENPLAY.txt").write_text(text,encoding="utf-8")
(D/"R77_H1_PA7_TREATMENT_R1_MECHANICAL_RESULT.json").write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(res,ensure_ascii=False,sort_keys=True))
raise SystemExit(0 if res["status"]=="PASS" else 2)
