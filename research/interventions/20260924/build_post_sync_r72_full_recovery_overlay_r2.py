#!/usr/bin/env python3
import pathlib, zipfile, hashlib, json, re

ROOT=pathlib.Path(__file__).resolve().parents[3]
OUT=ROOT/"research/interventions/20260924"
ZIP=OUT/"POST_SYNC_R72_FULL_RECOVERY_OVERLAY_R2.zip"
MAN=OUT/"POST_SYNC_R72_FULL_RECOVERY_OVERLAY_MANIFEST_R2.json"

include=set()

# Full recovery context. 20260922 intentionally includes the R74 lineage and its physical-parent context.
for rel in [
    "research/interventions/20260922",
    "research/interventions/20260923",
    "research/interventions/20260924",
    "handoff/20260922",
    "handoff/20260923",
    "handoff/20260924",
]:
    p=ROOT/rel
    if p.exists():
        for f in p.rglob("*"):
            if f.is_file() and f not in {ZIP,MAN}:
                include.add(f)

# Include executable workflow definitions needed to reproduce/verify post-R72 research.
wf=ROOT/".github/workflows"
if wf.exists():
    pats=[
        re.compile(r"r74-",re.I),
        re.compile(r"r76-provider-analog",re.I),
        re.compile(r"r76-vp-b1",re.I),
        re.compile(r"r77-h0",re.I),
        re.compile(r"post-sync-r72",re.I),
    ]
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
    duplicate_count=len(names)-len(set(names))
    encrypted_count=sum(1 for i in z.infolist() if i.flag_bits & 0x1)
    unsafe_count=sum(1 for n in names if n.startswith("/") or ".." in pathlib.PurePosixPath(n).parts)

manifest={
    "schema":"POST_SYNC_R72_FULL_RECOVERY_OVERLAY_MANIFEST_R2",
    "date":"2026-09-24",
    "purpose":"New-session recovery of all durable Hub research/method/result evidence after physical parent SYNC-R72; includes R74-era 20260922 context plus 20260923-24 research and relevant workflows.",
    "physical_parent":"SYNC-R72",
    "physical_authority_change":False,
    "active_runtime":"exact R69",
    "production":"ENG:R47 / LEGACY_R53",
    "runtime_db":"DB59 frozen",
    "research_db":"DB64-R128 research-only",
    "operational_level3":"SUSPENDED__REQUALIFICATION_REQUIRED",
    "formal_latest_scored":"R138",
    "formal_r140":"NOT_STARTED",
    "r74":"CLOSED_NO_EFFICACY_VERDICT__F05_NOT_QUALIFIED",
    "r75":"PARTIAL_PASS__CORE_SCHEMA_CAUSALLY_CONSUMED",
    "r76":"CLOSED_PASS__EXTERNAL_3JUDGE_ABSOLUTE_BROADCAST_QUALITY",
    "r77_h0":"PASS__INFRASTRUCTURE_8_OF_8",
    "r77_h1":"PREREGISTERED__INPUT_CUSTODY_ESTABLISHED__METADATA_CENSUS_NOT_EXECUTED__CAAS_RUNTIME_HOLD__HUMAN_TARGET_ACCESSED_FALSE__PRIMARY_OUTPUTS_0",
    "canonical_start_here":"handoff/20260924/START_HERE_POST_SYNC_R72_FULL_RESEARCH_RECOVERY_R77_H1_HOLD_R3.md",
    "human_target_accessed":False,
    "primary_h1_outputs":0,
    "file_count":len(files),
    "zip_file":ZIP.name,
    "zip_bytes":ZIP.stat().st_size,
    "zip_sha256":hashlib.sha256(ZIP.read_bytes()).hexdigest(),
    "zip_crc_pass":bad is None,
    "duplicate_paths":duplicate_count,
    "encrypted_entries":encrypted_count,
    "unsafe_paths":unsafe_count,
    "included_roots":[
        "research/interventions/20260922",
        "research/interventions/20260923",
        "research/interventions/20260924",
        "handoff/20260922",
        "handoff/20260923",
        "handoff/20260924",
        ".github/workflows selected R74/R76/R77/post-SYNC workflows"
    ],
    "known_historical_gap_note":"Some original per-run R75 JSONs were not individually committed during the live session; a recovered canonical R75 report is included and its durable historical source is R74_R75_R76_PROGRESS_R1.md.",
    "physicalization_note":"This recovery overlay does not replace or mutate the 9 SYNC-R72 physical transports."
}
MAN.write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2),encoding="utf-8")
print(json.dumps(manifest,ensure_ascii=False,sort_keys=True))
if bad is not None or duplicate_count or encrypted_count or unsafe_count:
    raise SystemExit(1)
