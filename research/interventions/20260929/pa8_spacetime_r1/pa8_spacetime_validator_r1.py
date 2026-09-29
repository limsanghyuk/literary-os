#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASES_PATH = ROOT / "PA8_FROZEN_16_CASES_R1.json"
RESULT_PATH = ROOT / "PA8_A_DETERMINISTIC_RESULT_R1.json"

FORWARD_MODES = {"LINEAR_REALTIME", "MONTAGE"}
NONLINEAR_MODES = {"FLASHBACK", "PARALLEL"}
VALID_MODES = FORWARD_MODES | NONLINEAR_MODES

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def parse_clock(clock: str) -> int:
    h, m = [int(x) for x in clock.split(":")]
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError(f"invalid clock {clock}")
    return h * 60 + m

def abs_min(clock: str, day: int) -> int:
    return int(day) * 1440 + parse_clock(clock)

def scene_start(scene: dict) -> int:
    return abs_min(scene["clock"], scene.get("day", 0))

def scene_end(scene: dict) -> int:
    return scene_start(scene) + int(scene.get("duration_min", 0))

def transition_for(scene: dict, entity: str, kinds: set[str], *, to_location=None, to_container_marker="__ANY__"):
    for t in scene.get("transitions", []):
        if t.get("entity") != entity or t.get("type") not in kinds:
            continue
        if to_location is not None and t.get("to_location") != to_location:
            continue
        if to_container_marker != "__ANY__" and t.get("to_container") != to_container_marker:
            continue
        return t
    return None

def validate_case(case: dict) -> dict:
    violations = []
    last_forward = None
    entity_state = {}
    travel = case.get("travel_minutes", {})

    for scene in case["scenes"]:
        sid = scene["scene"]
        mode = scene["mode"]
        if mode not in VALID_MODES:
            violations.append({"type":"UNKNOWN_TIMELINE_MODE","scene":sid,"detail":mode})
            continue

        start = scene_start(scene)
        end = scene_end(scene)
        clock_m = parse_clock(scene["clock"])
        day = int(scene.get("day", 0))

        # Same-scene physical multi-location.
        seen_locations = {}
        for e in scene.get("entities", []):
            ent = e["entity"]
            loc = e.get("location")
            if ent in seen_locations and seen_locations[ent] != loc:
                violations.append({
                    "type":"ENTITY_MULTI_LOCATION","scene":sid,"entity":ent,
                    "locations":[seen_locations[ent],loc]
                })
            else:
                seen_locations[ent] = loc

        # Forward clock validation. Explicit FLASHBACK/PARALLEL do not advance canonical time.
        if mode in FORWARD_MODES:
            if last_forward is not None:
                prev_clock = last_forward["clock_m"]
                prev_day = last_forward["day"]
                cross_midnight_bad = (
                    day <= prev_day and prev_clock >= 20*60 and clock_m < 4*60
                )
                if cross_midnight_bad:
                    violations.append({
                        "type":"CROSS_MIDNIGHT_NORMALIZATION_ERROR",
                        "scene":sid,
                        "previous_scene":last_forward["scene"],
                        "previous_clock":last_forward["clock"],
                        "current_clock":scene["clock"],
                        "previous_day":prev_day,
                        "current_day":day,
                    })
                elif start < last_forward["end"]:
                    violations.append({
                        "type":"SCENE_CLOCK_REVERSAL","scene":sid,
                        "previous_scene":last_forward["scene"],
                        "previous_end_abs_min":last_forward["end"],
                        "current_start_abs_min":start,
                    })

            # Event framing.
            for ev in scene.get("events", []):
                if ev.get("framing") == "FUTURE":
                    ev_t = abs_min(ev["clock"], ev.get("day", day))
                    if ev_t < start:
                        violations.append({
                            "type":"FUTURE_EVENT_IN_PAST","scene":sid,
                            "event":ev.get("event"),"event_abs_min":ev_t,
                            "scene_start_abs_min":start,
                        })

            # Resource / route / location availability.
            for r in scene.get("resources", []):
                vf = abs_min(r["valid_from"]["clock"], r["valid_from"].get("day", day))
                vt = abs_min(r["valid_to"]["clock"], r["valid_to"].get("day", day))
                if start < vf or end > vt:
                    violations.append({
                        "type":"AVAILABILITY_WINDOW_VIOLATION","scene":sid,
                        "resource":r.get("resource"),"valid_from":vf,"valid_to":vt,
                        "scene_start":start,"scene_end":end,
                    })

            # Cross-scene entity/container/location continuity.
            current_entities = {}
            for e in scene.get("entities", []):
                ent = e["entity"]
                # First assertion wins for state propagation; multi-location is separately invalid.
                if ent in current_entities:
                    continue
                current_entities[ent] = e
                prev = entity_state.get(ent)
                if prev is None:
                    continue

                prev_loc = prev.get("location")
                cur_loc = e.get("location")
                prev_container = prev.get("container")
                cur_container = e.get("container")

                if prev_container != cur_container:
                    tr = transition_for(
                        scene, ent, {"BOARD","EXIT","TRANSFER"},
                        to_container_marker=cur_container
                    )
                    if tr is None:
                        violations.append({
                            "type":"CONTAINER_TRANSITION_BREAK","scene":sid,
                            "entity":ent,"from_container":prev_container,
                            "to_container":cur_container,
                        })

                if prev_loc != cur_loc:
                    tr = transition_for(scene, ent, {"MOVE","TRANSFER"}, to_location=cur_loc)
                    if e.get("location_change_requires_evidence", False) and tr is None:
                        violations.append({
                            "type":"LOCATION_TRANSITION_BREAK","scene":sid,
                            "entity":ent,"from_location":prev_loc,"to_location":cur_loc,
                        })
                    if tr is not None:
                        key = f"{prev_loc}|{cur_loc}"
                        if key in travel:
                            available = start - int(prev["end"])
                            required = int(travel[key])
                            if available < required:
                                violations.append({
                                    "type":"IMPOSSIBLE_TRAVEL","scene":sid,
                                    "entity":ent,"from_location":prev_loc,"to_location":cur_loc,
                                    "available_min":available,"required_min":required,
                                })

            # Advance canonical state only in forward modes.
            for ent, e in current_entities.items():
                entity_state[ent] = {
                    "location":e.get("location"),
                    "container":e.get("container"),
                    "end":end,
                    "scene":sid,
                }
            last_forward = {
                "scene":sid,"clock":scene["clock"],"clock_m":clock_m,
                "day":day,"start":start,"end":end
            }

    types = [v["type"] for v in violations]
    valid = len(violations) == 0
    return {
        "case_id":case["case_id"],
        "expected_valid":bool(case["expected_valid"]),
        "expected_violation":case.get("expected_violation"),
        "actual_valid":valid,
        "violation_types":types,
        "violations":violations,
    }

def core_run(cases_doc: dict) -> dict:
    rows = [validate_case(c) for c in cases_doc["cases"]]
    positives = [r for r in rows if not r["expected_valid"]]
    negatives = [r for r in rows if r["expected_valid"]]

    tp = sum(1 for r in positives if (not r["actual_valid"]) and r["expected_violation"] in r["violation_types"])
    fn = len(positives) - tp
    tn = sum(1 for r in negatives if r["actual_valid"])
    fp = len(negatives) - tn
    expected_specific = sum(
        1 for r in positives
        if r["expected_violation"] in r["violation_types"]
    )

    return {
        "schema":"PA8_A_DETERMINISTIC_CORE_RESULT_R1",
        "case_count":len(rows),
        "positive_count":len(positives),
        "negative_count":len(negatives),
        "tp":tp,"tn":tn,"fp":fp,"fn":fn,
        "expected_specific_detection":expected_specific,
        "positive_detection":f"{tp}/{len(positives)}",
        "negative_correct_non_detection":f"{tn}/{len(negatives)}",
        "cases":rows,
        "gates":{
            "positive_8_of_8":tp == 8,
            "negative_8_of_8":tn == 8,
            "false_positive_0":fp == 0,
            "false_negative_0":fn == 0,
            "specific_violation_class_8_of_8":expected_specific == 8,
        }
    }

def main():
    cases_bytes = CASES_PATH.read_bytes()
    cases_doc = json.loads(cases_bytes.decode("utf-8"))
    first = core_run(cases_doc)
    second = core_run(cases_doc)
    deterministic = first == second
    gates = dict(first["gates"])
    gates["deterministic_rerun_identical"] = deterministic
    gates["research_only_boundary"] = True

    result = {
        "schema":"R77_H1_PA8_A_EPISODE_SPACETIME_CONTINUITY_RESULT_R1",
        "date":"2026-09-29",
        "status":"PASS" if all(gates.values()) else "FAIL",
        "parent_physical_authority":"SYNC-R74",
        "active_runtime_effect":"NONE__EXACT_R69_UNCHANGED",
        "production_effect":"NONE__ENG_R47_LEGACY_R53_UNCHANGED",
        "runtime_db_effect":"NONE__DB59_FROZEN_UNCHANGED",
        "human_target_accessed":False,
        "h1_primary_outputs":0,
        "cases_sha256":sha256_bytes(cases_bytes),
        "validator_sha256":sha256_bytes(Path(__file__).read_bytes()),
        "gates":gates,
        "metrics":{
            "tp":first["tp"],"tn":first["tn"],"fp":first["fp"],"fn":first["fn"],
            "positive_detection":first["positive_detection"],
            "negative_correct_non_detection":first["negative_correct_non_detection"],
            "expected_specific_detection":first["expected_specific_detection"],
        },
        "case_results":first["cases"],
        "claim_boundary":"Qualifies only the deterministic research-level within-episode spacetime predicate. It does not modify or qualify exact R69 runtime, Production, DB59, Level-3, Formal R140, or real-provider H1.",
        "next_if_pass":"PA8-B causal integration: bind the qualified predicate between Episode Architecture and Scene Contract in a research candidate and prove positive/negative propagation before any 40K surface generation."
    }
    RESULT_PATH.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)

if __name__ == "__main__":
    main()
