#!/usr/bin/env python3
import json, hashlib, pathlib, sys

ROOT=pathlib.Path(__file__).resolve().parent
PREREG=ROOT/"R77_H0_HUMAN_NEXT_EPISODE_PROSPECTIVE_BENCHMARK_PREREGISTRATION_R1.json"
SCHEMA=ROOT/"R77_H0_TYPED_EPISODE_POSITION_CONTRACT_R1.json"
CUTOFF=ROOT/"R77_H0_PAST_ONLY_CUTOFF_CONTRACT_R1.json"

def h(b): return hashlib.sha256(b).hexdigest()

def validate_row(row, cutoff):
    req=["work_id","field_path","source_episode_min","source_episode_max","source_refs","derived_from_future","derivation_stage"]
    missing=[k for k in req if k not in row]
    if missing:
        return False, "MISSING_PROVENANCE:"+",".join(missing)
    if not isinstance(row["source_episode_max"],int):
        return False, "BAD_EPISODE_MAX"
    if row["source_episode_max"]>cutoff:
        return False, "FUTURE_EPISODE_SOURCE"
    if row["derived_from_future"] is not False:
        return False, "FUTURE_DERIVATION"
    if not row["source_refs"]:
        return False, "EMPTY_SOURCE_REFS"
    return True, "PASS"

fixtures=[
 {"id":"EARLY_SAFE","cutoff":1,"row":{"work_id":"W1","field_path":"thread.T01.state","source_episode_min":1,"source_episode_max":1,"source_refs":["EP01:SC07"],"derived_from_future":False,"derivation_stage":"past_only"}},
 {"id":"MIDDLE_SAFE","cutoff":5,"row":{"work_id":"W2","field_path":"relationship.A_B","source_episode_min":1,"source_episode_max":5,"source_refs":["EP02:SC03","EP05:SC18"],"derived_from_future":False,"derivation_stage":"past_only"}},
 {"id":"LATE_SAFE","cutoff":12,"row":{"work_id":"W3","field_path":"payoff_debt.P4","source_episode_min":3,"source_episode_max":12,"source_refs":["EP03:SC11","EP12:SC29"],"derived_from_future":False,"derivation_stage":"past_only"}},
 {"id":"EARLY_TARGET_LEAK","cutoff":1,"row":{"work_id":"W1","field_path":"thread.T01.payoff","source_episode_min":1,"source_episode_max":2,"source_refs":["EP02:SC10"],"derived_from_future":False,"derivation_stage":"bad"}},
 {"id":"MIDDLE_DERIVED_LEAK","cutoff":5,"row":{"work_id":"W2","field_path":"summary.hidden","source_episode_min":1,"source_episode_max":5,"source_refs":["EP01-EP05"],"derived_from_future":True,"derivation_stage":"full_series_summary"}},
 {"id":"UNKNOWN_PROVENANCE","cutoff":12,"row":{"work_id":"W3","field_path":"relationship.C_D","source_episode_min":1,"source_refs":["EP07:SC08"],"derived_from_future":False,"derivation_stage":"unknown"}}
]
expected={
 "EARLY_SAFE":True,"MIDDLE_SAFE":True,"LATE_SAFE":True,
 "EARLY_TARGET_LEAK":False,"MIDDLE_DERIVED_LEAK":False,"UNKNOWN_PROVENANCE":False
}
results=[]
for f in fixtures:
    ok,reason=validate_row(f["row"],f["cutoff"])
    results.append({"id":f["id"],"accepted":ok,"reason":reason,"expected":expected[f["id"]],"pass":ok==expected[f["id"]]})

schema=json.loads(SCHEMA.read_text(encoding="utf-8"))
prereg=json.loads(PREREG.read_text(encoding="utf-8"))
cutoff_contract=json.loads(CUTOFF.read_text(encoding="utf-8"))

typed_gate = (
    len(schema["series_position"])>=8 and
    "PILOT_OPENING" in schema["series_position"] and
    "FINALE" in schema["series_position"] and
    "THREAD_PAYOFF" in schema["material_portfolio"] and
    "EXIT_STATE" in schema["scene_contract_required"]
)
strata_gate=[x["id"] for x in prereg["strata"]]==["EARLY","MIDDLE","LATE"]
custody_gate="physically and semantically hidden" in prereg["arms"]["H"]
fixture_gate=all(x["pass"] for x in results)

gates={
 "H0_1_TYPED_SCHEMA_COMPLETE":typed_gate,
 "H0_2_THREE_POSITION_STRATA_FROZEN":strata_gate,
 "H0_3_HUMAN_TARGET_CUSTODY_RULE_FROZEN":custody_gate,
 "H0_4_SAFE_FIXTURES_ACCEPTED":all(x["accepted"] for x in results if x["id"].endswith("_SAFE")),
 "H0_5_TARGET_FUTURE_FIXTURE_BLOCKED":not next(x["accepted"] for x in results if x["id"]=="EARLY_TARGET_LEAK"),
 "H0_6_DERIVED_FUTURE_FIXTURE_BLOCKED":not next(x["accepted"] for x in results if x["id"]=="MIDDLE_DERIVED_LEAK"),
 "H0_7_UNKNOWN_PROVENANCE_FAIL_CLOSED":not next(x["accepted"] for x in results if x["id"]=="UNKNOWN_PROVENANCE"),
 "H0_8_FIXTURE_EXPECTATIONS_EXACT":fixture_gate
}
out={
 "schema":"R77_H0_INFRASTRUCTURE_QUALIFICATION_RESULT_R1",
 "status":"PASS" if all(gates.values()) else "FAIL",
 "gates":gates,
 "fixture_results":results,
 "source_hashes":{
   PREREG.name:h(PREREG.read_bytes()),
   SCHEMA.name:h(SCHEMA.read_bytes()),
   CUTOFF.name:h(CUTOFF.read_bytes())
 },
 "primary_human_target_outputs":0,
 "human_target_accessed":False,
 "claim_boundary":"Infrastructure qualification only; no human target episode has been inspected or generated against."
}
ev=ROOT/"r77_h0_evidence"
ev.mkdir(exist_ok=True)
(ev/"R77_H0_INFRASTRUCTURE_QUALIFICATION_RESULT_R1.json").write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2),encoding="utf-8")
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
sys.exit(0 if out["status"]=="PASS" else 1)
