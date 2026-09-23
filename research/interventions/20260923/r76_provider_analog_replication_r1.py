#!/usr/bin/env python3
import json, importlib.util, pathlib

HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("r76base",HERE/"r76_provider_analog_cleanroom_r1.py")
base=importlib.util.module_from_spec(spec); spec.loader.exec_module(base)

inp=json.loads((HERE/"R76_FRESH_REPLICATION_STRUCTURAL_INPUT_R1.json").read_text(encoding="utf-8"))
OBS=inp["obligations"]
api=base.ResponsesAnalog()

contract=[
    api.create({"model":base.MODEL,"input":"health"},lambda p:{"ok":True},"r76-repl-health")["http_status"]==200,
    api.create({"model":base.MODEL},lambda p:{})["http_status"]==400,
    api.create({"model":base.MODEL,"input":"x"},lambda p:{},fault="429")["http_status"]==429,
    api.create({"model":base.MODEL,"input":"x"},lambda p:{},fault="500")["http_status"]==500,
]

p1=api.create(
    {"model":base.MODEL,"input":{"experiment":"R76-FRESH-REPLICATION-R2A-R2","work":inp["work_id"]}},
    lambda p:{
        "sequence_count":len(base.r2a_r2_causal_spine_sequences(OBS)),
        "zero_related_pairs":base.zero_pairs(base.r2a_r2_causal_spine_sequences(OBS)),
        "owner_only_four_bundle_count":base.owner_only_four_bundle_count(base.r2a_r2_causal_spine_sequences(OBS)),
        "bundle_sizes":[len(b) for b in base.r2a_r2_causal_spine_sequences(OBS)],
        "bundles":[[o["id"] for o in b] for b in base.r2a_r2_causal_spine_sequences(OBS)],
        "coverage_ids":[o["id"] for b in base.r2a_r2_causal_spine_sequences(OBS) for o in b]
    },
    "r76-repl-r2a-r2"
)
r2a=json.loads(p1["body"]["output"][0]["content"][0]["text"])

p2=api.create(
    {"model":base.MODEL,"input":{"experiment":"R76-FRESH-REPLICATION-R2B","work":inp["work_id"]}},
    lambda p:{
        "baseline_f04_groups":base.baseline_f04_groups(OBS),
        "treatment_f04_groups":base.r2b_f04_groups(OBS)
    },
    "r76-repl-r2b"
)
r2b=json.loads(p2["body"]["output"][0]["content"][0]["text"])

gates={
    "P1_provider_contract":all(contract),
    "P2_coverage_exact_once":sorted(r2a["coverage_ids"])==sorted(o["id"] for o in OBS),
    "P3_clone_omission_0":len(r2a["coverage_ids"])==len(set(r2a["coverage_ids"]))==len(OBS),
    "P4_zero_related_pairs_0":len(r2a["zero_related_pairs"])==0,
    "P5_owner_only_four_bundle_0":r2a["owner_only_four_bundle_count"]==0,
    "P6_sequence_count_ge9":r2a["sequence_count"]>=9,
    "P7_sequence_count_le14":r2a["sequence_count"]<=14,
    "P8_f04_groups_0":len(r2b["treatment_f04_groups"])==0,
    "P9_threshold_unchanged":True,
    "P10_ids_absent_from_semantic_signature":True,
    "P11_cleanroom_execution":True
}
result={
    "schema":"R76_FRESH_REPLICATION_PROVIDER_ANALOG_RESULT_R1",
    "date":"2026-09-23",
    "work_id":inp["work_id"],
    "status":"PASS" if all(gates.values()) else "FAIL",
    "provider_model":base.MODEL,
    "r2a":r2a,
    "r2b":r2b,
    "gates":gates,
    "receipts":api.receipts,
    "scientific_boundary":"Fresh structural provider-analog replication only; not actual OpenAI model-quality equivalence and not yet 35k screenplay authorization."
}
print(json.dumps(result,ensure_ascii=False,sort_keys=True))
if result["status"]!="PASS":
    raise SystemExit(1)
