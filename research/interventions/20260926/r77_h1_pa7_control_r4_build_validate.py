#!/usr/bin/env python3
import json,re,hashlib,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[3]
D=ROOT/"research/interventions/20260926/r77_h1_pa7_control_r1"
base=(D/"R77_H1_PA7_CONTROL_R3_FULL_SCREENPLAY.txt").read_text(encoding="utf-8")
obj=json.loads((D/"R77_H1_PA7_CONTROL_R4_FINAL_COMPLETION.json").read_text(encoding="utf-8"))
target=str(obj["scene"]); ins=obj["text"].strip()
matches=list(re.finditer(r"(?m)^씬\s+(\d+)\.\s*[^\n]*$",base))
pieces=[]; cursor=0; inserted=False
for i,m in enumerate(matches):
    nextpos=matches[i+1].start() if i+1<len(matches) else len(base)
    pieces.append(base[cursor:nextpos])
    if str(int(m.group(1)))==target:
        if pieces[-1] and not pieces[-1].endswith("\n"): pieces[-1]+="\n"
        pieces.append("\n"+ins+"\n\n")
        inserted=True
    cursor=nextpos
final="".join(pieces)
if cursor<len(base): final+=base[cursor:]
if not final.endswith("\n"): final+="\n"
seqs=[int(x) for x in re.findall(r"(?m)^시퀀스\s+(\d+)\s+—",final)]
scenes=[int(x) for x in re.findall(r"(?m)^씬\s+(\d+)\.",final)]
meta=["R77_","PA7","provider_analog","schema","focus_axis"]
res={
 "schema":"R77_H1_PA7_CONTROL_R4_FINAL_MECHANICAL_RESULT",
 "date":"2026-09-26",
 "chars":len(final),
 "sha256":hashlib.sha256(final.encode()).hexdigest(),
 "sequences":len(seqs),"scenes":len(scenes),"inserted":inserted,
 "parent_r3_sha256":"caeb702e870e85c073e5fb7e2e67eab9d695e5337938877c0f80e15268ef2f1a",
 "gates":{
  "chars_ge_40000":len(final)>=40000,
  "chars_le_41500":len(final)<=41500,
  "sequences_exact_1_to_9":seqs==list(range(1,10)),
  "scenes_exact_1_to_50":scenes==list(range(1,51)),
  "inserted_once":inserted,
  "metadata_leak_0":not any(t.lower() in final.lower() for t in meta),
  "duplicate_scene_heading_0":len(scenes)==len(set(scenes))
 }
}
res["status"]="PASS" if all(res["gates"].values()) else "FAIL"
(D/"R77_H1_PA7_CONTROL_R4_FULL_SCREENPLAY.txt").write_text(final,encoding="utf-8")
(D/"R77_H1_PA7_CONTROL_R4_MECHANICAL_RESULT.json").write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(res,ensure_ascii=False,sort_keys=True))
raise SystemExit(0 if res["status"]=="PASS" else 2)
