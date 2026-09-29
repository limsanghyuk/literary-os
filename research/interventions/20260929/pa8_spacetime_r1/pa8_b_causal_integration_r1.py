#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
FIXTURE=ROOT/"PA8_B_FROZEN_CAUSAL_FIXTURE_R1.json"
OUT=ROOT/"PA8_B_CAUSAL_INTEGRATION_RESULT_R1.json"

CONSUMED_FIELDS=(
    "scene","earliest_start","latest_start","duration_min","predecessor",
    "min_gap_after_predecessor","resource_window","future_event_time"
)

def canon(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")

def sha(obj):
    return hashlib.sha256(canon(obj)).hexdigest()

def compile_provider_input(doc):
    # Deliberately excludes metadata/research notes.
    return {
        "schema":"PA8_B_PROVIDER_INPUT_R1",
        "semantic_payload":copy.deepcopy(doc["semantic_payload"]),
        "spacetime_contract":[
            {k:copy.deepcopy(row[k]) for k in CONSUMED_FIELDS if k in row}
            for row in doc["schedule"]
        ]
    }

def schedule(doc):
    by_scene={}
    scheduled=[]
    for row in doc["schedule"]:
        sid=row["scene"]
        candidate=int(row["earliest_start"])
        pred=row.get("predecessor")
        if pred:
            if pred not in by_scene:
                return {"status":"REPLAN_REQUIRED","reason":"MISSING_PREDECESSOR","scene":sid,"schedule":scheduled}
            candidate=max(candidate,by_scene[pred]["end"]+int(row.get("min_gap_after_predecessor",0)))

        # A future event must still be future at scene start.
        if "future_event_time" in row and int(row["future_event_time"]) < candidate:
            return {
                "status":"REPLAN_REQUIRED","reason":"FUTURE_EVENT_IN_PAST","scene":sid,
                "candidate_start":candidate,"future_event_time":int(row["future_event_time"]),
                "schedule":scheduled
            }

        if candidate > int(row["latest_start"]):
            return {"status":"REPLAN_REQUIRED","reason":"NO_FEASIBLE_START","scene":sid,"candidate_start":candidate,"schedule":scheduled}

        end=candidate+int(row["duration_min"])
        win=row.get("resource_window")
        if win is not None and (candidate < int(win["from"]) or end > int(win["to"])):
            return {
                "status":"REPLAN_REQUIRED","reason":"AVAILABILITY_WINDOW_VIOLATION","scene":sid,
                "candidate_start":candidate,"candidate_end":end,
                "window":copy.deepcopy(win),"schedule":scheduled
            }

        rec={"scene":sid,"start":candidate,"end":end}
        by_scene[sid]=rec
        scheduled.append(rec)
    return {"status":"SCHEDULED","reason":"NONE","schedule":scheduled}

def apply_variant(base, spec):
    d=copy.deepcopy(base)
    if "metadata" in spec:
        d["metadata"]=copy.deepcopy(spec["metadata"])
    m=spec.get("mutate")
    if m:
        for row in d["schedule"]:
            if row["scene"]==m["scene"]:
                row[m["field"]]=copy.deepcopy(m["value"])
                break
        else:
            raise KeyError(m["scene"])
    return d

def one_run(fx):
    semantic_hash=sha(fx["semantic_payload"])
    base={
        "semantic_payload":copy.deepcopy(fx["semantic_payload"]),
        "metadata":copy.deepcopy(fx["baseline"]["metadata"]),
        "schedule":copy.deepcopy(fx["baseline"]["schedule"])
    }
    base_input=compile_provider_input(base)
    base_sched=schedule(base)
    base_rec={
        "provider_input_sha256":sha(base_input),
        "schedule_sha256":sha(base_sched),
        "schedule":base_sched,
        "semantic_sha256":semantic_hash
    }

    variants={}
    for name,spec in fx["variants"].items():
        v=apply_variant(base,spec)
        inp=compile_provider_input(v)
        sch=schedule(v)
        variants[name]={
            "provider_input_sha256":sha(inp),
            "schedule_sha256":sha(sch),
            "schedule":sch,
            "semantic_sha256":sha(v["semantic_payload"]),
            "provider_changed":sha(inp)!=base_rec["provider_input_sha256"],
            "schedule_changed":sha(sch)!=base_rec["schedule_sha256"]
        }

    gates={
        "C1_RELEVANT_EARLIEST_START_SHIFT":(
            variants["C1_RELEVANT_EARLIEST_START_SHIFT"]["provider_changed"]
            and variants["C1_RELEVANT_EARLIEST_START_SHIFT"]["schedule_changed"]
            and variants["C1_RELEVANT_EARLIEST_START_SHIFT"]["schedule"]["status"]=="SCHEDULED"
        ),
        "C2_RELEVANT_TRAVEL_GAP_SHIFT":(
            variants["C2_RELEVANT_TRAVEL_GAP_SHIFT"]["provider_changed"]
            and variants["C2_RELEVANT_TRAVEL_GAP_SHIFT"]["schedule_changed"]
            and variants["C2_RELEVANT_TRAVEL_GAP_SHIFT"]["schedule"]["status"]=="SCHEDULED"
        ),
        "C3_RELEVANT_AVAILABILITY_CONFLICT":(
            variants["C3_RELEVANT_AVAILABILITY_CONFLICT"]["provider_changed"]
            and variants["C3_RELEVANT_AVAILABILITY_CONFLICT"]["schedule_changed"]
            and variants["C3_RELEVANT_AVAILABILITY_CONFLICT"]["schedule"]["status"]=="REPLAN_REQUIRED"
            and variants["C3_RELEVANT_AVAILABILITY_CONFLICT"]["schedule"]["reason"]=="AVAILABILITY_WINDOW_VIOLATION"
        ),
        "C4_PA7_LIKE_DEADLINE_CONFLICT":(
            variants["C4_PA7_LIKE_DEADLINE_CONFLICT"]["provider_changed"]
            and variants["C4_PA7_LIKE_DEADLINE_CONFLICT"]["schedule_changed"]
            and variants["C4_PA7_LIKE_DEADLINE_CONFLICT"]["schedule"]["status"]=="REPLAN_REQUIRED"
            and variants["C4_PA7_LIKE_DEADLINE_CONFLICT"]["schedule"]["reason"]=="FUTURE_EVENT_IN_PAST"
        ),
        "N1_IRRELEVANT_METADATA_INVARIANCE":(
            not variants["N1_IRRELEVANT_METADATA_SHIFT"]["provider_changed"]
            and not variants["N1_IRRELEVANT_METADATA_SHIFT"]["schedule_changed"]
        ),
        "N2_SEMANTIC_INVARIANCE":all(v["semantic_sha256"]==semantic_hash for v in variants.values())
    }
    return {
        "semantic_sha256":semantic_hash,
        "baseline":base_rec,
        "variants":variants,
        "gates":gates
    }

def main():
    raw=FIXTURE.read_bytes()
    fx=json.loads(raw.decode("utf-8"))
    a=one_run(fx)
    b=one_run(fx)
    deterministic=(a==b)
    gates=dict(a["gates"])
    gates["DETERMINISTIC_RERUN_IDENTICAL"]=deterministic
    gates["RESEARCH_ONLY_BOUNDARY"]=True
    result={
        "schema":"R77_H1_PA8_B_CAUSAL_INTEGRATION_RESULT_R1",
        "date":"2026-09-29",
        "status":"PASS" if all(gates.values()) else "FAIL",
        "parent":"PA8-A PASS",
        "parent_physical_authority":"SYNC-R74",
        "fixture_sha256":hashlib.sha256(raw).hexdigest(),
        "implementation_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "gates":gates,
        "evidence":a,
        "adoption_chain":"value change -> consumer compiled input -> provider-input hash -> downstream schedule/replan hash",
        "active_runtime_effect":"NONE__EXACT_R69_UNCHANGED",
        "production_effect":"NONE",
        "runtime_db_effect":"NONE",
        "physical_package_effect":"NONE__RESEARCH_ONLY",
        "human_target_accessed":False,
        "h1_primary_outputs":0,
        "next_if_pass":"PA8-C fresh synthetic episode architecture with ESCC fields frozen before any surface generation."
    }
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    raise SystemExit(0 if result["status"]=="PASS" else 1)

if __name__=="__main__":
    main()
