#!/usr/bin/env python3
import pathlib, shutil, zipfile, hashlib, json
HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/"r76_vp_b1_external_dispatch"
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir()
files={
 "WHOLE_EPISODE_SCREENPLAY_ONLY.txt":HERE/"R76_VP_B1_WHOLE_EPISODE_SCREENPLAY_ONLY_BLIND_PACKET_R1.txt",
 "PREFROZEN_SCENE_SURFACE_CRAFT.txt":HERE/"R76_VP_B1_PREFROZEN_SCENE_SURFACE_CRAFT_PACKET_R1.txt",
 "JUDGE_INSTRUCTION.txt":HERE/"R76_VP_B1_EXTERNAL_JUDGE_INSTRUCTION_R1.txt",
}
manifest={"schema":"R76_VP_B1_EXTERNAL_3JUDGE_DISPATCH_MANIFEST_R1","judges":{}}
for jid in ("J01","J02","J03"):
    d=OUT/jid; d.mkdir()
    for dst,src in files.items():
        shutil.copy2(src,d/dst)
    (d/"JUDGE_ID.txt").write_text(jid+"\n",encoding="utf-8")
    manifest["judges"][jid]={}
    for p in sorted(d.iterdir()):
        manifest["judges"][jid][p.name]={
          "bytes":p.stat().st_size,
          "sha256":hashlib.sha256(p.read_bytes()).hexdigest()
        }
coord=OUT/"COORDINATOR_ONLY"; coord.mkdir()
for name in ("R76_VP_B1_EXTERNAL_3JUDGE_PREREGISTRATION_R1.json",
             "R76_VP_B1_TEXT_CANONICAL_STATE_LEDGER_R1.json",
             "R76_VP_B1_OUTPUT_ONLY_REVERSE_RECONSTRUCTION_R1.json",
             "R76_VP_B1_INTERNAL_VIRTUAL_QUALITY_RESULT_R1.json",
             "R76_VP_B1_MECHANICAL_PASS_REPORT_R1.json"):
    src=HERE/name
    if src.exists(): shutil.copy2(src,coord/name)
(OUT/"MANIFEST.json").write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2),encoding="utf-8")
zip_path=HERE/"R76_VP_B1_EXTERNAL_3JUDGE_DISPATCH_BUNDLE_R1.zip"
with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): z.write(p,p.relative_to(OUT))
print(json.dumps({
 "schema":"R76_VP_B1_EXTERNAL_DISPATCH_BUILD_RESULT_R1",
 "status":"PASS",
 "zip":zip_path.name,
 "bytes":zip_path.stat().st_size,
 "sha256":hashlib.sha256(zip_path.read_bytes()).hexdigest(),
 "judge_packet_identity":len({json.dumps(v,sort_keys=True) for v in manifest["judges"].values()})==1,
 "manifest":manifest
},ensure_ascii=False,sort_keys=True))
