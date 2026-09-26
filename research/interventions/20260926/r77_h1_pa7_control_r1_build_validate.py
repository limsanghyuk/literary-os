#!/usr/bin/env python3
import json,re,hashlib,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[3]
D=ROOT/"research/interventions/20260926/r77_h1_pa7_control_r1"
parts=[(D/f"R77_H1_PA7_CONTROL_SQ{i:02d}.txt").read_text(encoding="utf-8") for i in range(1,10)]
base="\n\n".join(parts)+"\n"
ins=json.loads((D/"R77_H1_PA7_CONTROL_R1_COMPLETION_INSERTS.json").read_text(encoding="utf-8"))["inserts"]

ms=list(re.finditer(r"(?m)^씬\s+(\d+)\.\s*[^\n]*$",base))
out=[]
for i,m in enumerate(ms):
    start=m.start()
    end=ms[i+1].start() if i+1<len(ms) else len(base)
    chunk=base[start:end].rstrip()
    sc=str(int(m.group(1)))
    if sc in ins:
        chunk += "\n\n"+ins[sc].strip()
    out.append(chunk)
# keep sequence headings by slicing from sequence starts instead of scene-only extraction
# reconstruct from original while inserting before next scene/sequence boundaries
pattern=re.compile(r"(?m)^씬\s+(\d+)\.\s*[^\n]*$")
pos=0; final=[]
for i,m in enumerate(list(pattern.finditer(base))):
    next_start=(list(pattern.finditer(base))[i+1].start() if i+1<len(list(pattern.finditer(base))) else len(base))
# simpler one-pass
matches=list(pattern.finditer(base)); cursor=0; pieces=[]
for idx,m in enumerate(matches):
    nextpos=matches[idx+1].start() if idx+1<len(matches) else len(base)
    # append from cursor through this scene body
    pieces.append(base[cursor:nextpos].rstrip())
    sc=str(int(m.group(1)))
    if sc in ins: pieces.append("\n\n"+ins[sc].strip()+"\n")
    cursor=nextpos
final="".join(pieces)
if cursor < len(base): final+=base[cursor:]
# normalize accidental missing newlines before next scene
final=re.sub(r"(?<!\n)(시퀀스\s+\d+\s+—)",r"\n\n\1",final)
final=re.sub(r"(?<!\n)(씬\s+\d+\.)",r"\n\n\1",final)
if not final.endswith("\n"): final+="\n"

seqs=[int(x) for x in re.findall(r"(?m)^시퀀스\s+(\d+)\s+—",final)]
scenes=[int(x) for x in re.findall(r"(?m)^씬\s+(\d+)\.",final)]
sha=hashlib.sha256(final.encode()).hexdigest()
res={
 "schema":"R77_H1_PA7_CONTROL_R1_MECHANICAL_RESULT",
 "date":"2026-09-26",
 "chars":len(final),"sha256":sha,
 "sequences":len(seqs),"scenes":len(scenes),
 "gates":{
  "chars_ge_40000":len(final)>=40000,
  "sequences_exact_1_to_9":seqs==list(range(1,10)),
  "scenes_exact_1_to_50":scenes==list(range(1,51)),
  "metadata_leak_0":not any(t.lower() in final.lower() for t in ["R77_","PA7","provider_analog","schema","focus_axis"]),
  "duplicate_scene_heading_0":len(scenes)==len(set(scenes))
 }
}
res["status"]="PASS" if all(res["gates"].values()) else "FAIL"
(D/"R77_H1_PA7_CONTROL_R1_FULL_SCREENPLAY.txt").write_text(final,encoding="utf-8")
(D/"R77_H1_PA7_CONTROL_R1_MECHANICAL_RESULT.json").write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(res,ensure_ascii=False,sort_keys=True))
raise SystemExit(0 if res["status"]=="PASS" else 2)
