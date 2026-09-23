#!/usr/bin/env python3
import json, re, hashlib, uuid, time, pathlib, sys

ROOT=pathlib.Path(__file__).resolve().parent
SURFACE=ROOT/"r76_vp_b1_surface"
FILES=[SURFACE/f"R76_VP_B1_SQ{i:02d}.txt" for i in range(1,10)]
MODEL="gpt-5.6-sol-chatgpt-virtual-provider"
CLIENT_REQUEST_ID="r76-vp-b1-surface-r1"

def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def normalize_body(s):
    return re.sub(r"\s+"," ",s).strip()

missing=[str(p) for p in FILES if not p.exists()]
if missing:
    print(json.dumps({"schema":"R76_VP_B1_MECHANICAL_RESULT_R1","status":"FAIL_MISSING_FILES","missing":missing},ensure_ascii=False))
    raise SystemExit(1)

parts=[p.read_text(encoding="utf-8") for p in FILES]
combined="\n\n".join(parts)+"\n"

seq_heads=re.findall(r"(?m)^시퀀스\s+(\d+)\s+—",combined)
scene_iter=list(re.finditer(r"(?m)^씬\s+(\d+)\.\s*([^\n]*)$",combined))
scene_nums=[int(m.group(1)) for m in scene_iter]

# Extract scene bodies.
scenes=[]
for i,m in enumerate(scene_iter):
    start=m.end()
    end=scene_iter[i+1].start() if i+1<len(scene_iter) else len(combined)
    body=combined[start:end].strip()
    scenes.append({"scene_no":int(m.group(1)),"heading_tail":m.group(2).strip(),"body":body})

metadata_tokens=[
    "state_delta","transaction_stage","obligation_id","source_obligation","evaluator",
    "R76_","R75_","R74_","SCENE_CONTRACT","THREAD_AXIS","provider_analog",
    "research metadata","schema"
]
leaks=[]
for tok in metadata_tokens:
    if tok.lower() in combined.lower():
        leaks.append(tok)

speakers={
    "윤서","민호","태경","지우","수경","세라","직원","배우","주민","운전자",
    "조명 보조","카페 주인","시설 담당자(휴대폰)","기자"
}
dialogue_scene_count=0
stage_direction_fail=[]
empty_scenes=[]
for s in scenes:
    body=s["body"]
    compact=re.sub(r"\s+","",body)
    if len(compact)<80:
        empty_scenes.append(s["scene_no"])
    lines=[x.strip() for x in body.splitlines() if x.strip()]
    if not lines:
        stage_direction_fail.append(s["scene_no"])
        continue
    # First prose line after heading must be narrative/stage direction, not a speaker cue.
    if lines[0] in speakers or len(lines[0])<20:
        stage_direction_fail.append(s["scene_no"])
    has_dialogue=False
    for i,line in enumerate(lines[:-1]):
        if line in speakers and lines[i+1]:
            has_dialogue=True
            break
    if has_dialogue:
        dialogue_scene_count+=1

body_hashes={}
duplicates=[]
for s in scenes:
    h=sha(normalize_body(s["body"]))
    if h in body_hashes:
        duplicates.append([body_hashes[h],s["scene_no"]])
    else:
        body_hashes[h]=s["scene_no"]

gates={
    "B1_char_count_ge35000":len(combined)>=35000,
    "B2_sequence_headings_9":[int(x) for x in seq_heads]==list(range(1,10)),
    "B3_scene_headings_52":scene_nums==list(range(1,53)),
    "B4_internal_metadata_leak_0":len(leaks)==0,
    "B5_empty_scene_0":len(empty_scenes)==0,
    "B6_stage_direction_all_scenes":len(stage_direction_fail)==0,
    "B7_dialogue_ge45_scenes":dialogue_scene_count>=45,
    "B8_numbering_monotonic":scene_nums==sorted(scene_nums) and len(set(scene_nums))==52,
    "B9_exact_duplicate_scene_bodies_0":len(duplicates)==0,
}

output_sha=sha(combined)
request_id="req_"+uuid.uuid4().hex
response_id="resp_"+uuid.uuid4().hex
receipt={
    "request":{
        "model":MODEL,
        "input":{"surface_contract":"R76_VP_B1_FROZEN_52_SCENE_SURFACE_CONTRACT_R1",
                 "sequence_files":[p.name for p in FILES]},
        "metadata":{"work_id":"SYNTH_R76_BREAKWATER_THEATER","virtual_provider":True}
    },
    "response":{
        "id":response_id,
        "object":"response",
        "created_at":int(time.time()),
        "status":"completed",
        "model":MODEL,
        "output":[{"type":"message","role":"assistant","status":"completed",
                   "content":[{"type":"output_text","text_sha256":output_sha}]}],
        "usage":{
            "input_tokens":None,
            "output_tokens":None,
            "total_tokens":None,
            "accounting_boundary":"No actual OpenAI API token accounting; virtual provider surface authored in ChatGPT session."
        },
        "metadata":{"virtual_provider":True,"not_actual_openai_api":True}
    },
    "headers":{
        "x-request-id":request_id,
        "X-Client-Request-Id":CLIENT_REQUEST_ID
    }
}
gates["B10_output_hash_and_virtual_receipt"]=bool(output_sha and response_id and request_id)

result={
    "schema":"R76_VP_B1_MECHANICAL_RESULT_R1",
    "date":"2026-09-23",
    "status":"PASS" if all(gates.values()) else "FAIL",
    "scientific_boundary":"Virtual Provider Surface Pretest only; not actual OpenAI API or literary-quality qualification.",
    "char_count":len(combined),
    "sequence_count":len(seq_heads),
    "scene_count":len(scenes),
    "dialogue_scene_count":dialogue_scene_count,
    "metadata_leaks":leaks,
    "empty_scenes":empty_scenes,
    "stage_direction_failures":stage_direction_fail,
    "duplicate_scene_bodies":duplicates,
    "surface_sha256":output_sha,
    "gates":gates,
    "receipt":receipt
}

outdir=ROOT/"r76_vp_b1_evidence"
outdir.mkdir(exist_ok=True)
(outdir/"R76_VP_B1_FULL_SCREENPLAY_R1.txt").write_text(combined,encoding="utf-8")
(outdir/"R76_VP_B1_MECHANICAL_RESULT_R1.json").write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2),encoding="utf-8")
(outdir/"R76_VP_B1_VIRTUAL_PROVIDER_RECEIPT_R1.json").write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2),encoding="utf-8")

print(json.dumps(result,ensure_ascii=False,sort_keys=True))
if result["status"]!="PASS":
    raise SystemExit(1)
