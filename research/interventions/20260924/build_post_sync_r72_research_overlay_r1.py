#!/usr/bin/env python3
# rebuild includes latest 20260924 handoff R2
import pathlib, zipfile, hashlib, json

ROOT=pathlib.Path(__file__).resolve().parents[3]
OUT=ROOT/"research/interventions/20260924"
zip_path=OUT/"POST_SYNC_R72_R74_R77_RESEARCH_OVERLAY_R1.zip"

include=[]
for rel in [
    "research/interventions/20260923",
    "research/interventions/20260924",
    "handoff/20260923",
    "handoff/20260924",
    "handoff/20260924",
]:
    p=ROOT/rel
    if p.exists():
        for f in sorted(p.rglob("*")):
            if f.is_file() and f.name != zip_path.name:
                include.append(f)

with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for f in include:
        z.write(f,f.relative_to(ROOT))

manifest={
    "schema":"POST_SYNC_R72_R74_R77_RESEARCH_OVERLAY_MANIFEST_R1",
    "date":"2026-09-24",
    "physical_parent":"SYNC-R72",
    "physical_authority_change":False,
    "reason":"Research overlay only while SYNC-R72 raw-byte custody is unavailable.",
    "r76":"CLOSED_PASS__EXTERNAL_3JUDGE",
    "r77_h0":"PASS__INFRASTRUCTURE_8_OF_8",
    "r77_h1":"PREREGISTERED__TARGET_NOT_OPENED__OUTPUTS_0",
    "r77_h1":"PREREGISTERED__INPUT_CUSTODY_ESTABLISHED__EXECUTION_HOLD__HUMAN_TARGET_ACCESSED_FALSE",
    "file_count":len(include),
    "zip_file":zip_path.name,
    "zip_bytes":zip_path.stat().st_size,
    "zip_sha256":hashlib.sha256(zip_path.read_bytes()).hexdigest(),
}
(OUT/"POST_SYNC_R72_R74_R77_RESEARCH_OVERLAY_MANIFEST_R1.json").write_text(
    json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2),encoding="utf-8")
print(json.dumps(manifest,ensure_ascii=False,sort_keys=True))
