#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUTS={
 "CONTROL":{
  "zip":ROOT/"PA8_D_CONTROL_INDEPENDENT_GENERATION_PACKAGE_R1.zip",
  "files":[
   ROOT/"PA8_D_CONTROL_GENERATOR_READ_FIRST_R1.md",
   ROOT/"PA8_D_CONTROL_GENERATION_PACKET_R1.json",
   ROOT/"PA8_D_CONTROL_GENERATION_PACKET_MANIFEST_R1.json"
  ]},
 "TREATMENT":{
  "zip":ROOT/"PA8_D_TREATMENT_INDEPENDENT_GENERATION_PACKAGE_R1.zip",
  "files":[
   ROOT/"PA8_D_TREATMENT_GENERATOR_READ_FIRST_R1.md",
   ROOT/"PA8_D_TREATMENT_GENERATION_PACKET_R1.json",
   ROOT/"PA8_D_TREATMENT_GENERATION_PACKET_MANIFEST_R1.json"
  ]}
}
MAN=ROOT/"PA8_D_GENERATION_ZIP_MANIFEST_R1.json"

def sha(b): return hashlib.sha256(b).hexdigest()

def build(spec):
    zpath=spec["zip"]
    file_meta=[]
    with zipfile.ZipFile(zpath,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in spec["files"]:
            b=p.read_bytes()
            zi=zipfile.ZipInfo(p.name,date_time=(2026,9,29,0,0,0))
            zi.compress_type=zipfile.ZIP_DEFLATED
            zi.external_attr=0o100644 << 16
            z.writestr(zi,b)
            file_meta.append({"file":p.name,"bytes":len(b),"sha256":sha(b)})
    zb=zpath.read_bytes()
    with zipfile.ZipFile(zpath,"r") as z:
        bad=z.testzip()
        names=z.namelist()
    return {"file":zpath.name,"bytes":len(zb),"sha256":sha(zb),"crc_pass":bad is None,"entries":names,"members":file_meta}

def main():
    result={k:build(v) for k,v in OUTS.items()}
    man={
      "schema":"PA8_D_GENERATION_ZIP_MANIFEST_R1","date":"2026-09-29",
      "status":"PASS" if all(x["crc_pass"] and len(x["entries"])==3 for x in result.values()) else "FAIL",
      "packages":result,
      "control_surface_outputs":0,"treatment_surface_outputs":0,
      "human_target_accessed":False,
      "physical_authority_effect":"NONE",
      "dispatch":"Use each ZIP in a separate fresh generation conversation/context. Never expose the other arm packet/output."
    }
    MAN.write_text(json.dumps(man,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(man,ensure_ascii=False,sort_keys=True))
    raise SystemExit(0 if man["status"]=="PASS" else 1)

if __name__=="__main__": main()
