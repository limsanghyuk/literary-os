#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
R1=ROOT/"R77_H1_PA8_C_FRESH_EPISODE_ARCHITECTURE_R1.json"
R2=ROOT/"R77_H1_PA8_C_FRESH_EPISODE_ARCHITECTURE_R2.json"
OUT=ROOT/"PA8_C_R2_PREFLIGHT_RESULT_R1.json"

def parse_clock(s):
    h,m=map(int,s.split(":")); return h*60+m

def canon(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")

def sha(obj):
    return hashlib.sha256(canon(obj)).hexdigest()

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
    r1=json.loads(R1.read_text(encoding="utf-8"))
    raw2=R2.read_bytes()
    r2=json.loads(raw2.decode("utf-8"))
    issues=[]
    scenes=r2["scene_contracts"]
    ids=[s["scene_id"] for s in scenes]
    if ids != [f"SC{i:02d}" for i in range(1,51)]:
        issues.append({"type":"SCENE_ID_OR_COUNT","count":len(ids)})
    if sorted(set(s["sequence"] for s in scenes)) != list(range(1,10)):
        issues.append({"type":"SEQUENCE_SET"})

    sem1=sha(semantic_projection(r1))
    sem2=sha(semantic_projection(r2))
    if sem1!=sem2:
        issues.append({"type":"SEMANTIC_PROJECTION_CHANGED","r1":sem1,"r2":sem2})

    matrix=r2.get("spacetime_travel_minutes",{})
    prev_end=None
    last={}
    typed_moves=0
    for s in scenes:
        st=s["spacetime"]
        start=parse_clock(st["clock"])+1440*int(st.get("day",0))
        end=start+int(st["duration_min"])
        if prev_end is not None and start < prev_end:
            issues.append({"type":"SCENE_CLOCK_REVERSAL","scene":s["scene_id"],"start":start,"previous_end":prev_end})
        prev_end=end

        for r in st.get("resources",[]):
            vf=parse_clock(r["valid_from"]["clock"])+1440*int(r["valid_from"].get("day",0))
            vt=parse_clock(r["valid_to"]["clock"])+1440*int(r["valid_to"].get("day",0))
            if start<vf or end>vt:
                issues.append({"type":"AVAILABILITY_WINDOW_VIOLATION","scene":s["scene_id"],"resource":r["resource"]})

        for ev in st.get("future_events",[]):
            et=parse_clock(ev["clock"])+1440*int(ev.get("day",0))
            if et<start:
                issues.append({"type":"FUTURE_EVENT_IN_PAST","scene":s["scene_id"],"event":ev["event"]})

        trs={t["entity"]:t for t in st.get("transitions",[])}
        loc=st["location_id"]
        for ent in st.get("participants",[]):
            if ent in last and last[ent]["location"]!=loc:
                p=last[ent]
                tr=trs.get(ent)
                if tr is None:
                    issues.append({"type":"UNTYPED_LOCATION_CHANGE","scene":s["scene_id"],"entity":ent,"from":p["location"],"to":loc})
                else:
                    typed_moves+=1
                    if tr.get("from_location")!=p["location"] or tr.get("to_location")!=loc:
                        issues.append({"type":"TRANSITION_ENDPOINT_MISMATCH","scene":s["scene_id"],"entity":ent})
                    key=f"{p['location']}|{loc}"
                    expected=matrix.get(key)
                    if expected is None:
                        issues.append({"type":"MISSING_TRAVEL_TIME","scene":s["scene_id"],"entity":ent,"key":key})
                    elif int(tr.get("travel_min",-1))!=int(expected):
                        issues.append({"type":"TRAVEL_TIME_MISMATCH","scene":s["scene_id"],"entity":ent})
                    gap=start-p["end"]
                    mode=tr.get("mode")
                    if mode=="BETWEEN_SCENES":
                        if gap < int(tr["travel_min"]) or int(tr.get("arrival_offset_min",0))!=0:
                            issues.append({"type":"INVALID_BETWEEN_SCENES_TRANSITION","scene":s["scene_id"],"entity":ent,"gap":gap})
                    elif mode=="AT_SCENE_OPEN":
                        if int(tr["travel_min"])>int(st["duration_min"]):
                            issues.append({"type":"IMPOSSIBLE_AT_OPEN_TRANSITION","scene":s["scene_id"],"entity":ent})
                        if int(tr.get("arrival_offset_min",-1)) < int(tr["travel_min"]):
                            issues.append({"type":"ARRIVAL_OFFSET_TOO_SMALL","scene":s["scene_id"],"entity":ent})
                    else:
                        issues.append({"type":"UNKNOWN_TRANSITION_MODE","scene":s["scene_id"],"entity":ent,"mode":mode})
            last[ent]={"location":loc,"end":end,"scene":s["scene_id"]}

    first=parse_clock(scenes[0]["spacetime"]["clock"])
    last_end=parse_clock(scenes[-1]["spacetime"]["clock"])+int(scenes[-1]["spacetime"]["duration_min"])
    if first!=108 or last_end!=212:
        issues.append({"type":"EPISODE_CLOCK_BOUNDARY","first":first,"last_end":last_end})

    result={
      "schema":"PA8_C_R2_PREFLIGHT_RESULT_R1",
      "date":"2026-09-29",
      "status":"PASS" if not issues else "FAIL",
      "r2_sha256":hashlib.sha256(raw2).hexdigest(),
      "semantic_projection_r1_sha256":sem1,
      "semantic_projection_r2_sha256":sem2,
      "semantic_invariance":sem1==sem2,
      "scene_count":len(scenes),
      "sequence_count":len(set(s["sequence"] for s in scenes)),
      "typed_location_transitions":typed_moves,
      "issues":issues,
      "surface_outputs":0,
      "human_target_accessed":False,
      "active_runtime_effect":"NONE__EXACT_R69_UNCHANGED",
      "physical_package_effect":"NONE__RESEARCH_ONLY",
      "next_if_pass":"PA8-D paired >=40K provider-analog surface generation under frozen R2 architecture.",
      "next_if_fail":"Preserve R2 and repair only the newly exposed spacetime typing defect before any surface output."
    }
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    raise SystemExit(0 if result["status"]=="PASS" else 1)

if __name__=="__main__":
    main()
