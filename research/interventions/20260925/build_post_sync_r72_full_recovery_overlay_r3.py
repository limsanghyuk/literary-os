#!/usr/bin/env python3
import pathlib, zipfile, hashlib, json, re

ROOT=pathlib.Path(__file__).resolve().parents[3]
OUT=ROOT/"research/interventions/20260925"
OUT.mkdir(parents=True,exist_ok=True)
ZIP=OUT/"POST_SYNC_R72_FULL_RECOVERY_OVERLAY_R3.zip"
MAN=OUT/"POST_SYNC_R72_FULL_RECOVERY_OVERLAY_MANIFEST_R3.json"

include=set()
for rel in [
    "research/interventions/20260922",
    "research/interventions/20260923",
    "research/interventions/20260924",
    "research/interventions/20260925",
    "research/operations/20260925",
    "handoff/20260922",
    "handoff/20260923",
    "handoff/20260924",
    "handoff/20260925",
]:
    p=ROOT/rel
    if p.exists():
        for f in p.rglob("*"):
            if f.is_file() and f not in {ZIP,MAN} and "__pycache__" not in f.parts:
                include.add(f)

for rel in [
    "handoff/CURRENT_HANDOFF_POINTER.md",
    "handoff/CURRENT_NEXT_RESEARCH_POINTER.md",
    "handoff/CURRENT_SESSION_RECOVERY_POINTER.md",
    "handoff/CURRENT_DATABASE_RESEARCH_POINTER.md",
]:
    p=ROOT/rel
    if p.exists(): include.add(p)

wf=ROOT/".github/workflows"
if wf.exists():
    pats=[re.compile(r"r74-",re.I),re.compile(r"r76-provider-analog",re.I),
          re.compile(r"r76-vp-b1",re.I),re.compile(r"r77-h0",re.I),
          re.compile(r"post-sync-r72",re.I)]
    for f in wf.iterdir():
        if f.is_file() and any(p.search(f.name) for p in pats):
            include.add(f)

files=sorted(include,key=lambda p:str(p.relative_to(ROOT)))
with zipfile.ZipFile(ZIP,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for f in files:
        z.write(f,f.relative_to(ROOT))

with zipfile.ZipFile(ZIP) as z:
    bad=z.testzip()
    names=z.namelist()
    dup=len(names)-len(set(names))
    enc=sum(1 for i in z.infolist() if i.flag_bits & 1)
    unsafe=sum(1 for n in names if n.startswith("/") or ".." in pathlib.PurePosixPath(n).parts)

manifest={
 "schema":"POST_SYNC_R72_FULL_RECOVERY_OVERLAY_MANIFEST_R3",
 "date":"2026-09-25",
 "physical_parent":"SYNC-R72",
 "physical_authority_change":False,
 "active_runtime":"exact R69",
 "production":"ENG:R47 / LEGACY_R53",
 "runtime_db":"DB59 frozen",
 "research_db":"DB64-R131 research-only",
 "operational_level3":"SUSPENDED__REQUALIFICATION_REQUIRED",
 "formal_latest_scored":"R138",
 "formal_r140":"NOT_STARTED",
 "r74":"CLOSED_NO_EFFICACY_VERDICT__F05_NOT_QUALIFIED",
 "r75":"PARTIAL_PASS__CORE_SCHEMA_CAUSALLY_CONSUMED",
 "r76":"CLOSED_PASS__EXTERNAL_3JUDGE_ABSOLUTE_BROADCAST_QUALITY",
 "r77_h0":"PASS__INFRASTRUCTURE_8_OF_8",
 "r77_h1":"CENSUS_SELECTION_PAST_ONLY_SEALED__GENERATOR_DISPATCH_READY__C_T_NOT_STARTED__HUMAN_TARGET_UNOPENED",
 "canonical_start_here":"handoff/20260925/START_HERE_POST_SYNC_R72_R77_H1_DB64_R131_RESEARCH_AUTHORITY_R5.md",
 "human_target_accessed":False,
 "primary_h1_outputs":0,
 "file_count":len(files),
 "zip_file":ZIP.name,
 "zip_bytes":ZIP.stat().st_size,
 "zip_sha256":hashlib.sha256(ZIP.read_bytes()).hexdigest(),
 "zip_crc_pass":bad is None,
 "duplicate_paths":dup,
 "encrypted_entries":enc,
 "unsafe_paths":unsafe,
 "included_roots":[
  "research/interventions/20260922-20260925",
  "research/operations/20260925",
  "handoff/20260922-20260925",
  "handoff/CURRENT_* pointers",
  ".github/workflows selected R74/R76/R77/post-SYNC workflows"
 ],
 "private_input_note":"Human screenplay Past-Only packages and DB64 raw research-data bytes are intentionally not embedded in this public Hub overlay; only their sealed hashes/custody records are included."
}
MAN.write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2),encoding="utf-8")
print(json.dumps(manifest,ensure_ascii=False,sort_keys=True))
if bad is not None or dup or enc or unsafe: raise SystemExit(1)
