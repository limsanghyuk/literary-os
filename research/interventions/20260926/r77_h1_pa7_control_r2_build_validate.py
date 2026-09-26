#!/usr/bin/env python3
import json,re,hashlib,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[3]
D=ROOT/"research/interventions/20260926/r77_h1_pa7_control_r1"
base=(D/"R77_H1_PA7_CONTROL_R1_FULL_SCREENPLAY.txt").read_text(encoding="utf-8")
ins=json.loads((D/"R77_H1_PA7_CONTROL_R2_UNDERLENGTH_COMPLETION.json").read_text(encoding="utf-8"))["inserts"]
matches=list(re.finditer(r"(?m)^씬\s+(\d+)\.\s*[^\n]*$",base))
parts=[]; cursor=0
for i,m in enumerate(matches):
    nextpos=matches[i+1].start() if i+1<len(matches) else len(base)
    parts.append(base[cursor:nextpos].rstrip())
    sc=str(int(m.group(1)))
    if sc in ins: parts.append("\n\n"+ins[sc].strip()+"\n")
    cursor=nextpos
final="".join(parts)
if cursor<len(base): final+=base[cursor:]
if not final.endswith("\n"): final+="\n"
seqs=[int(x) for x in re.findall(r"(?m)^시퀀스\s+(\d+)\s+—",final)]
scenes=[int(x) for x in re.findall(r"(?m)^씬\s+(\d+)\.",final)]
meta=["R77_","PA7","provider_analog","schema","focus_axis"]
res={
 "schema":"R77_H1_PA7_CONTROL_R2_MECHANICAL_RESULT",
 "date":"2026-09-26",
 "chars":len(final),
 "sha256":hashlib.sha256(final.encode()).hexdigest(),
 "sequences":len(seqs),"scenes":len(scenes),
 "parent_r1_sha256":"10bb42ad080472137107076f3ea456ce7345fca957a43a8f19bf2f6ba1506e12",
 "gates":{
  "chars_ge_40000":len(final)>=40000,
  "sequences_exact_1_to_9":seqs==list(range(1,10)),
  "scenes_exact_1_to_50":scenes==list(range(1,51)),
  "metadata_leak_0":not any(t.lower() in final.lower() for t in meta),
  "duplicate_scene_heading_0":len(scenes)==len(set(scenes))
 }
}
res["status"]="PASS" if all(res["gates"].values()) else "FAIL"
(D/"R77_H1_PA7_CONTROL_R2_FULL_SCREENPLAY.txt").write_text(final,encoding="utf-8")
(D/"R77_H1_PA7_CONTROL_R2_MECHANICAL_RESULT.json").write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(res,ensure_ascii=False,sort_keys=True))
raise SystemExit(0 if res["status"]=="PASS" else 2)
