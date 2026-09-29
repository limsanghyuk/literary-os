#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
ARCH=ROOT/"R77_H1_PA8_C_FRESH_EPISODE_ARCHITECTURE_R1.json"
OUT=ROOT/"PA8_C_ARCHITECTURE_PREFLIGHT_RESULT_R1.json"

def parse_clock(s):
    h,m=map(int,s.split(":")); return h*60+m

def sha_bytes(b): return hashlib.sha256(b).hexdigest()

def main():
    raw=ARCH.read_bytes()
    d=json.loads(raw.decode("utf-8"))
    issues=[]
    scenes=d["scene_contracts"]

    ids=[s["scene_id"] for s in scenes]
    expected=[f"SC{i:02d}" for i in range(1,51)]
    if ids!=expected:
        issues.append({"type":"SCENE_ID_OR_COUNT","actual_count":len(ids)})

    seqs=[s["sequence"] for s in scenes]
    if sorted(set(seqs))!=list(range(1,10)):
        issues.append({"type":"SEQUENCE_SET","actual":sorted(set(seqs))})

    prev_end=None
    prev_id=None
    for s in scenes:
        st=s["spacetime"]
        start=parse_clock(st["clock"])+1440*int(st.get("day",0))
        end=start+int(st["duration_min"])
        if st.get("timeline_mode")=="LINEAR_REALTIME" and prev_end is not None and start < prev_end:
            issues.append({"type":"SCENE_CLOCK_REVERSAL","scene":s["scene_id"],"previous_scene":prev_id,"start":start,"previous_end":prev_end})
        if st.get("timeline_mode")=="LINEAR_REALTIME":
            prev_end=end; prev_id=s["scene_id"]

        for r in st.get("resources",[]):
            vf=parse_clock(r["valid_from"]["clock"])+1440*int(r["valid_from"].get("day",0))
            vt=parse_clock(r["valid_to"]["clock"])+1440*int(r["valid_to"].get("day",0))
            if start < vf or end > vt:
                issues.append({"type":"AVAILABILITY_WINDOW_VIOLATION","scene":s["scene_id"],"resource":r["resource"],"start":start,"end":end,"valid_from":vf,"valid_to":vt})

        for ev in st.get("future_events",[]):
            et=parse_clock(ev["clock"])+1440*int(ev.get("day",0))
            if et < start:
                issues.append({"type":"FUTURE_EVENT_IN_PAST","scene":s["scene_id"],"event":ev["event"],"event_time":et,"scene_start":start})

    # Architecture endpoint.
    first_start=parse_clock(scenes[0]["spacetime"]["clock"])
    last_st=scenes[-1]["spacetime"]
    last_end=parse_clock(last_st["clock"])+int(last_st["duration_min"])
    if (first_start,last_end)!=(108,212):
        issues.append({"type":"EPISODE_CLOCK_BOUNDARY","first_start":first_start,"last_end":last_end})

    # Frozen sample must exist and remain unique.
    sample=d.get("frozen_blind_sample",[])
    if len(sample)!=6 or len(set(sample))!=6 or any(x not in ids for x in sample):
        issues.append({"type":"BLIND_SAMPLE_INVALID","sample":sample})

    # Detect consecutive physical-location jumps with no elapsed gap for the same participant.
    # This is diagnostic at PA8-C R1: it reveals where explicit transition typing is still required.
    last_seen={}
    transition_gaps=[]
    for s in scenes:
        st=s["spacetime"]
        start=parse_clock(st["clock"])
        end=start+int(st["duration_min"])
        loc=st["location_id"]
        for ent in st.get("participants",[]):
            if ent in last_seen:
                p=last_seen[ent]
                if p["location"]!=loc:
                    gap=start-p["end"]
                    transition_gaps.append({"entity":ent,"from":p["location"],"to":loc,"from_scene":p["scene"],"to_scene":s["scene_id"],"gap_min":gap})
                    if gap<=0:
                        issues.append({"type":"UNTYPED_ZERO_GAP_LOCATION_JUMP","entity":ent,"from":p["location"],"to":loc,"from_scene":p["scene"],"to_scene":s["scene_id"],"gap_min":gap})
            last_seen[ent]={"location":loc,"end":end,"scene":s["scene_id"]}

    result={
        "schema":"PA8_C_ARCHITECTURE_PREFLIGHT_RESULT_R1",
        "date":"2026-09-29",
        "architecture_sha256":sha_bytes(raw),
        "status":"PASS" if not issues else "FAIL",
        "scene_count":len(scenes),
        "sequence_count":len(set(seqs)),
        "episode_start":"01:48",
        "episode_end":"03:32",
        "issues":issues,
        "transition_gap_diagnostics":transition_gaps,
        "surface_outputs":0,
        "human_target_accessed":False,
        "authority_effect":"NONE",
        "next_if_fail":"Preserve R1 and preregister/freeze an R2 architecture repair before any surface output. Repair only explicit transition/time typing; do not change premise/due-deferred/scene semantic functions.",
        "next_if_pass":"Proceed to PA8-D paired >=40K surface generation under frozen architecture."
    }
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    raise SystemExit(0 if result["status"]=="PASS" else 1)

if __name__=="__main__":
    main()
