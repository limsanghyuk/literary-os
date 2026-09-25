#!/usr/bin/env python3
import pathlib,re,json,hashlib,difflib
ROOT=pathlib.Path(__file__).resolve().parents[3]
TROOT=ROOT/"research/interventions/20260925/r77_h1_pa6_treatment_r1"
CROOT=ROOT/"research/interventions/20260923/r76_vp_b1_surface"

def sha(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()
def norm(s): return re.sub(r"\s+"," ",s).strip()

tparts=[(TROOT/f"R77_H1_PA6_TREATMENT_SQ{i:02d}.txt").read_text(encoding="utf-8") for i in range(1,10)]
cparts=[(CROOT/f"R76_VP_B1_SQ{i:02d}.txt").read_text(encoding="utf-8") for i in range(1,10)]
treatment="\n\n".join(tparts)+"\n"
control="\n\n".join(cparts)+"\n"

seqs=[int(x) for x in re.findall(r"(?m)^시퀀스\s+(\d+)\s+—",treatment)]
scene_iter=list(re.finditer(r"(?m)^씬\s+(\d+)\.\s*([^\n]*)$",treatment))
scenes=[]
for i,m in enumerate(scene_iter):
    end=scene_iter[i+1].start() if i+1<len(scene_iter) else len(treatment)
    body=treatment[m.end():end].strip()
    scenes.append({"scene":int(m.group(1)),"heading":m.group(2).strip(),"body":body})

speakers={"윤서","민호","태경","지우","수경","세라","배우","조명 보조","분장 스태프","냉면집 주인","약국 주인","카페 주인","행사대행 직원","직원","기자","기자2","주민","학생","운전자","시설 담당자(휴대폰)","세라(전화)","민호(무전)","윤서(전화)"}
dialogue_scene_count=0
stage_fail=[]
short_scene=[]
body_hash={}
dups=[]
for s in scenes:
    lines=[x.strip() for x in s["body"].splitlines() if x.strip()]
    if len(norm(s["body"]))<300: short_scene.append(s["scene"])
    if not lines or lines[0] in speakers or len(lines[0])<15: stage_fail.append(s["scene"])
    if any(lines[i] in speakers and i+1<len(lines) for i in range(len(lines)-1)): dialogue_scene_count+=1
    h=sha(norm(s["body"]))
    if h in body_hash: dups.append([body_hash[h],s["scene"]])
    else: body_hash[h]=s["scene"]

meta_tokens=["state_delta","transaction_stage","obligation_id","source_obligation","evaluator","R77_","R76_","SCENE_CONTRACT","THREAD_AXIS","provider_analog","research metadata","schema"]
leaks=[x for x in meta_tokens if x.lower() in treatment.lower()]

# Detect suspicious verbatim reuse: exact normalized lines >=35 chars and SequenceMatcher longest block.
def long_lines(txt):
    return {norm(x) for x in txt.splitlines() if len(norm(x))>=35}
exact_long=sorted(long_lines(treatment)&long_lines(control),key=len,reverse=True)
sm=difflib.SequenceMatcher(None,norm(control),norm(treatment),autojunk=False)
match=sm.find_longest_match()
longest=norm(treatment)[match.b:match.b+match.size]

gates={
 "P1_chars_ge_40000":len(treatment)>=40000,
 "P2_sequence_exact_1_to_9":seqs==list(range(1,10)),
 "P3_scene_exact_1_to_52":[s["scene"] for s in scenes]==list(range(1,53)),
 "P4_dialogue_ge45":dialogue_scene_count>=45,
 "P5_stage_direction_all_scenes":not stage_fail,
 "P6_no_short_scene_under300":not short_scene,
 "P7_metadata_leak_0":not leaks,
 "P8_duplicate_full_scene_0":not dups,
 "P9_no_exact_control_line_ge35":len(exact_long)==0,
 "P10_longest_normalized_overlap_lt120":match.size<120
}
result={
 "schema":"R77_H1_PA6_TREATMENT_R1_MECHANICAL_RESULT",
 "date":"2026-09-25",
 "status":"PASS" if all(gates.values()) else "FAIL",
 "treatment":{"chars":len(treatment),"sha256":sha(treatment),"sequences":len(seqs),"scenes":len(scenes),"dialogue_scenes":dialogue_scene_count},
 "control_reference":{"chars":len(control),"sha256":sha(control)},
 "gates":gates,
 "stage_failures":stage_fail,
 "short_scenes":short_scene,
 "metadata_leaks":leaks,
 "duplicate_scene_bodies":dups,
 "exact_control_lines_ge35":exact_long[:20],
 "longest_normalized_control_overlap":{"chars":match.size,"text":longest[:300]},
 "claim_boundary":"Mechanical/copy-independence gate only; not literary quality or external blind."
}
out=ROOT/"research/interventions/20260925/r77_h1_pa6_treatment_r1"
(out/"R77_H1_PA6_TREATMENT_R1_FULL_SCREENPLAY.txt").write_text(treatment,encoding="utf-8")
(out/"R77_H1_PA6_TREATMENT_R1_MECHANICAL_RESULT.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(result,ensure_ascii=False,sort_keys=True))
raise SystemExit(0 if result["status"]=="PASS" else 2)
