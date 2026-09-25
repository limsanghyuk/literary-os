#!/usr/bin/env python3
import os,re,json,hashlib,random,pathlib,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[3]
CROOT=ROOT/"research/interventions/20260923/r76_vp_b1_surface"
TFILE=ROOT/"research/interventions/20260925/r77_h1_pa6_treatment_r1/R77_H1_PA6_TREATMENT_R1_FULL_SCREENPLAY.txt"
OUT=ROOT/"pa6_external_dispatch"
OUT.mkdir(exist_ok=True)

CONTROL="\n\n".join((CROOT/f"R76_VP_B1_SQ{i:02d}.txt").read_text(encoding="utf-8") for i in range(1,10))+"\n"
TREATMENT=TFILE.read_text(encoding="utf-8")
CSHA=hashlib.sha256(CONTROL.encode()).hexdigest()
TSHA=hashlib.sha256(TREATMENT.encode()).hexdigest()
assert CSHA=="7b35fa2418f07382b52d5e93403e3da555539e1c96747cca98e3227e5c4c3ee4"
assert TSHA=="f2e5b113881dbcd43383beff388d349ef340ffe6c8bc60986f733e5eaa086f4a"

WHOLE_AXES=[
"EPISODE_PREMISE_COHERENCE","CAUSAL_SEQUENCE_PROGRESSION","THREAD_AND_SUBPLOT_INTEGRATION",
"CHARACTER_RELATIONSHIP_TRAJECTORY","INFORMATION_TOPOLOGY_DRAMATIZATION",
"SCENE_NECESSITY_AND_DISTINCT_FUNCTION","ESCALATION_PACING","CLOSURE_DEFERRED_BALANCE"]
SURFACE_AXES=[
"DIALOGUE_SUBTEXT","CHARACTER_VOICE","RELATIONSHIP_STATUS_PRESSURE","PHYSICALIZATION_ACTION",
"PACING_ESCALATION_TIME_PRESSURE","ENSEMBLE_WORLD_SPECIFICITY","INFORMATION_DRAMATIZATION",
"KOREAN_SPOKEN_NATURALNESS","SCENE_OPENING_VISUALIZATION","PERFORMANCE_DIRECTION_QUALITY",
"ACTION_DIALOGUE_BINDING","EMOTION_EXTERNALIZATION","CINEMATIC_READABILITY","DIRECTION_DETAIL_ECONOMY"]
SCENES=[7,15,30,32,39,41]
CRITICAL=[
"INTERNAL_SCHEMA_OR_RESEARCH_META_LEAK","IMPORTANT_STATE_CHANGE_WITHOUT_SCREEN_VISIBLE_CARRIER",
"EXPOSITORY_EMOTION_STATE_DIALOGUE_AS_DOMINANT_CRAFT","SEVERE_CHARACTER_VOICE_COLLAPSE",
"MAJOR_CAUSAL_OR_CONTINUITY_BREAK","DIRECTION_BLOAT_THAT_REPEATS_DIALOGUE_OR_STATE"]

def extract_scenes(text):
    ms=list(re.finditer(r"(?m)^씬\s+(\d+)\.\s*([^\n]*)$",text))
    out={}
    for i,m in enumerate(ms):
        end=ms[i+1].start() if i+1<len(ms) else len(text)
        out[int(m.group(1))]=text[m.start():end].strip()
    return out
C_SC=extract_scenes(CONTROL);T_SC=extract_scenes(TREATMENT)
assert sorted(C_SC)==list(range(1,53)) and sorted(T_SC)==list(range(1,53))

instruction="""You are an independent blind evaluator of two complete Korean broadcast-drama screenplay realizations, SCRIPT A and SCRIPT B.

INDEPENDENCE
- Use only this packet.
- Do not search the Literary OS project, GitHub, prior conversations, hidden plans, model identity, or any other judge output.
- Do not guess which script is newer, baseline, treatment, or preferred by the coordinator.
- Judge the finished screenplay text itself.
- Preserve your first complete schema-valid judgment. Do not revise scores to make either side win.

TASK 1 — WHOLE EPISODE
Score SCRIPT A and SCRIPT B independently from 1 to 10 on every WHOLE_EPISODE_AXIS.
Use integer or one decimal.

TASK 2 — PRE-FROZEN SCENE SAMPLE
For SC07, SC15, SC30, SC32, SC39, SC41, score each script from 1 to 10 on every SURFACE_AXIS.

Interpretation reminders:
- DIALOGUE_SUBTEXT: pressure, evasion, negotiation, withholding or choice rather than direct state explanation.
- CHARACTER_VOICE: distinct diction, sentence shape, role logic, avoidance pattern and conflict strategy.
- PHYSICALIZATION_ACTION: important changes carried by playable action, gaze/expression, hands, props, blocking, silence, failed action or spatial change.
- KOREAN_SPOKEN_NATURALNESS: speakable Korean TV-drama dialogue, not summary/policy/research prose.
- SCENE_OPENING_VISUALIZATION: scene begins with a concrete visual/action condition.
- PERFORMANCE_DIRECTION_QUALITY: directions give playable actor behavior and emotional flow without abstractly naming emotion.
- ACTION_DIALOGUE_BINDING: speech changes or is changed by simultaneous action rather than running as detachable dialogue.
- EMOTION_EXTERNALIZATION: emotion is inferable from performance/action instead of explained directly.
- DIRECTION_DETAIL_ECONOMY: detailed enough to stage, but does not merely repeat what dialogue already says.

TASK 3 — OUTPUT-ONLY RECONSTRUCTION
For each script independently reconstruct, only from the screenplay:
- episode premise
- major threads
- functional sequence progression
- relationship trajectories
- resolved due-now material
- deferred/open material
Mark reconstructed items EVIDENCED or INFERRED.

TASK 4 — CRITICAL VIOLATIONS
Flag only clearly evidenced violations using the supplied labels. Give scene evidence.

TASK 5 — BLIND PAIRED PREFERENCE
Choose A, B, or TIE separately for:
- whole_episode_preference
- surface_craft_preference
Explain with concrete screenplay evidence, not speculation about system/model identity.

Return JSON only and conform to the output schema in this packet.
"""

schema={
 "judge_id":"J01",
 "scripts":{
  "A":{
   "whole_episode_scores":{a:0 for a in WHOLE_AXES},
   "scene_scores":{f"SC{x:02d}":{a:0 for a in SURFACE_AXES} for x in SCENES},
   "reconstruction":{
    "episode_premise":[],"major_threads":[],"sequence_functions":[],
    "relationship_trajectories":[],"resolved_due_now":[],"deferred_open":[]
   },
   "critical_violations":[],
   "strengths":[],"weaknesses":[]
  },
  "B":{
   "whole_episode_scores":{a:0 for a in WHOLE_AXES},
   "scene_scores":{f"SC{x:02d}":{a:0 for a in SURFACE_AXES} for x in SCENES},
   "reconstruction":{
    "episode_premise":[],"major_threads":[],"sequence_functions":[],
    "relationship_trajectories":[],"resolved_due_now":[],"deferred_open":[]
   },
   "critical_violations":[],
   "strengths":[],"weaknesses":[]
  }
 },
 "paired":{
  "whole_episode_preference":"A|B|TIE",
  "surface_craft_preference":"A|B|TIE",
  "paired_reasoning_evidence":[]
 },
 "overall_notes":""
}

secret=os.environ.get("MAPPING_SECRET","")
run_id=os.environ.get("GITHUB_RUN_ID","")
if not secret: raise SystemExit("mapping secret unavailable")
seed=int.from_bytes(hashlib.sha256((secret+"|"+run_id+"|"+TSHA+"|"+CSHA).encode()).digest()[:8],"big")
rng=random.Random(seed)
judges=["J01","J02","J03"]
treatment_positions=["A","A","B"]
rng.shuffle(treatment_positions)
mapping={}
for j,tpos in zip(judges,treatment_positions):
    mapping[j]={"treatment_position":tpos,"control_position":"B" if tpos=="A" else "A"}

for j in judges:
    jdir=OUT/j
    jdir.mkdir(parents=True,exist_ok=True)
    tpos=mapping[j]["treatment_position"]
    A=TREATMENT if tpos=="A" else CONTROL
    B=CONTROL if tpos=="A" else TREATMENT
    Asc=T_SC if tpos=="A" else C_SC
    Bsc=C_SC if tpos=="A" else T_SC
    packet=instruction
    packet+="\n\nWHOLE_EPISODE_AXES\n"+"\n".join(WHOLE_AXES)
    packet+="\n\nSURFACE_AXES\n"+"\n".join(SURFACE_AXES)
    packet+="\n\nCRITICAL_VIOLATIONS\n"+"\n".join(CRITICAL)
    packet+="\n\n================ SCRIPT A ================\n\n"+A
    packet+="\n\n================ SCRIPT B ================\n\n"+B
    packet+="\n\n================ PRE-FROZEN SCENE SAMPLE: SCRIPT A ================\n"
    for sc in SCENES: packet+=f"\n\n--- A SC{sc:02d} ---\n{Asc[sc]}"
    packet+="\n\n================ PRE-FROZEN SCENE SAMPLE: SCRIPT B ================\n"
    for sc in SCENES: packet+=f"\n\n--- B SC{sc:02d} ---\n{Bsc[sc]}"
    forbidden=["Treatment","Control","R76","R77","PA6","provider-analog",TSHA,CSHA,"TEXT_DERIVED_STATE_LEDGER","PLANNING_ARTIFACT"]
    hits=[x for x in forbidden if x.lower() in packet.lower()]
    if hits: raise SystemExit(f"packet leak {j}: {hits}")
    p=jdir/f"{j}_BLIND_PACKET.txt"
    p.write_text(packet,encoding="utf-8")
    sch=json.loads(json.dumps(schema));sch["judge_id"]=j
    (jdir/f"{j}_OUTPUT_SCHEMA.json").write_text(json.dumps(sch,ensure_ascii=False,indent=2),encoding="utf-8")
    manifest={
      "schema":"PA6_BLIND_JUDGE_PACKET_MANIFEST_R1","judge_id":j,
      "packet_sha256":hashlib.sha256(packet.encode()).hexdigest(),
      "packet_chars":len(packet),"scene_sample":SCENES,
      "mapping_present":False,"forbidden_hit_count":0
    }
    (jdir/f"{j}_PACKET_MANIFEST.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")

coord={
 "schema":"R77_H1_PA6_COORDINATOR_MAPPING_R1",
 "date":"2026-09-25","run_id":run_id,
 "mapping":mapping,
 "treatment_surface_sha256":TSHA,
 "control_surface_sha256":CSHA,
 "reveal_rule":"DO NOT OPEN OR DISCLOSE TO JUDGES. Reveal only after all three schema-valid raw judgments are hash-sealed."
}
(OUT/"COORDINATOR_MAPPING_R1.json").write_text(json.dumps(coord,ensure_ascii=False,indent=2),encoding="utf-8")
summary={"judges":{}}
for j in judges:
    mf=json.loads((OUT/j/f"{j}_PACKET_MANIFEST.json").read_text())
    summary["judges"][j]=mf
summary["mapping_artifact_present"]=True
summary["mapping_not_in_judge_packets"]=True
summary["status"]="PASS__3_BLIND_PACKETS_BUILT__LEAK_0"
(OUT/"DISPATCH_BUILD_RECEIPT_R1.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"status":summary["status"],"judge_packet_hashes":{j:summary["judges"][j]["packet_sha256"] for j in judges}},sort_keys=True))
