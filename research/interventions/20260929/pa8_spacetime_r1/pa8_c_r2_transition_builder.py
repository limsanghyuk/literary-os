#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SRC=ROOT/"R77_H1_PA8_C_FRESH_EPISODE_ARCHITECTURE_R1.json"
OUT=ROOT/"R77_H1_PA8_C_FRESH_EPISODE_ARCHITECTURE_R2.json"
RECEIPT=ROOT/"PA8_C_R2_BUILD_RECEIPT_R1.json"

LOCS=[
 "B2_STACKS","FREIGHT_ELEVATOR","GROUND_STAGING","SERVER_ROOM",
 "LOADING_DOCK","CONSERVATION_LAB","COURTYARD"
]

def parse_clock(s):
    h,m=map(int,s.split(":")); return h*60+m

def canon(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")

def sha(obj):
    return hashlib.sha256(canon(obj)).hexdigest()

def travel_time(a,b):
    if a==b: return 0
    pair={a,b}
    if pair=={"B2_STACKS","FREIGHT_ELEVATOR"}: return 1
    if "GROUND_STAGING" in pair or "FREIGHT_ELEVATOR" in pair: return 1
    if pair=={"LOADING_DOCK","COURTYARD"}: return 1
    if pair=={"CONSERVATION_LAB","COURTYARD"}: return 1
    return 2

def semantic_projection(d):
    return {
      "work_id":d["work_id"],
      "title":d["title"],
      "premise":d["premise"],
      "principal_cast":d["principal_cast"],
      "hard_state_constraints":d["hard_state_constraints"],
      "sequence_contracts":d["sequence_contracts"],
      "scene_semantics":[
        {"scene":s["scene"],"scene_id":s["scene_id"],"sequence":s["sequence"],
         "function":s["function"],"must_change":s["must_change"]}
        for s in d["scene_contracts"]
      ],
      "due_now":d["due_now"],
      "deferred_open":d["deferred_open"],
      "frozen_blind_sample":d["frozen_blind_sample"],
      "arm_policy":d["arm_policy"]
    }

def main():
    raw=SRC.read_bytes()
    r1=json.loads(raw.decode("utf-8"))
    r2=copy.deepcopy(r1)
    r2["schema"]="R77_H1_PA8_C_FRESH_EPISODE_ARCHITECTURE_R2"
    r2["status"]="R2_TRANSITION_TYPED__PRE_SURFACE__CONTROL_OUTPUTS_0__TREATMENT_OUTPUTS_0"
    r2["parent_r1_sha256"]=hashlib.sha256(raw).hexdigest()

    matrix={}
    for a in LOCS:
        for b in LOCS:
            if a!=b:
                matrix[f"{a}|{b}"]=travel_time(a,b)
    r2["spacetime_travel_minutes"]=matrix
    r2["transition_contract"]={
      "between_scenes":"elapsed gap >= travel_min",
      "at_scene_open":"allowed only when travel_min <= destination scene duration; arrival_offset_min=travel_min",
      "semantic_effect":"NONE__MOVEMENT_TYPING_ONLY"
    }

    last={}
    transition_count=0
    at_open_count=0
    between_count=0
    failures=[]
    for s in r2["scene_contracts"]:
        st=s["spacetime"]
        start=parse_clock(st["clock"])+1440*int(st.get("day",0))
        end=start+int(st["duration_min"])
        loc=st["location_id"]
        trs=[]
        for ent in st.get("participants",[]):
            if ent in last and last[ent]["location"]!=loc:
                prev=last[ent]
                tmin=travel_time(prev["location"],loc)
                gap=start-prev["end"]
                if gap>=tmin:
                    mode="BETWEEN_SCENES"; offset=0; between_count+=1
                elif tmin<=int(st["duration_min"]):
                    mode="AT_SCENE_OPEN"; offset=tmin; at_open_count+=1
                else:
                    failures.append({
                      "entity":ent,"from":prev["location"],"to":loc,
                      "from_scene":prev["scene"],"to_scene":s["scene_id"],
                      "gap_min":gap,"travel_min":tmin,"scene_duration":st["duration_min"]
                    })
                    continue
                trs.append({
                  "entity":ent,"type":"MOVE","from_location":prev["location"],
                  "to_location":loc,"travel_min":tmin,"mode":mode,
                  "arrival_offset_min":offset,
                  "from_scene":prev["scene"]
                })
                transition_count+=1
            last[ent]={"location":loc,"end":end,"scene":s["scene_id"]}
        if trs:
            st["transitions"]=trs

    sem1=semantic_projection(r1)
    sem2=semantic_projection(r2)
    receipt={
      "schema":"PA8_C_R2_BUILD_RECEIPT_R1",
      "date":"2026-09-29",
      "status":"PASS" if not failures and sha(sem1)==sha(sem2) else "FAIL",
      "parent_r1_sha256":hashlib.sha256(raw).hexdigest(),
      "semantic_projection_r1_sha256":sha(sem1),
      "semantic_projection_r2_sha256":sha(sem2),
      "semantic_invariance":sha(sem1)==sha(sem2),
      "transition_count":transition_count,
      "at_scene_open_count":at_open_count,
      "between_scenes_count":between_count,
      "unrepairable_transitions":failures,
      "surface_outputs":0,
      "human_target_accessed":False,
      "authority_effect":"NONE"
    }
    if receipt["status"]=="PASS":
        OUT.write_text(json.dumps(r2,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,ensure_ascii=False,sort_keys=True))
    raise SystemExit(0 if receipt["status"]=="PASS" else 1)

if __name__=="__main__":
    main()
