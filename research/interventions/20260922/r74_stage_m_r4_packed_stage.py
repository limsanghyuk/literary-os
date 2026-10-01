import base64,gzip,json,importlib.util,pathlib,copy,hashlib,sys

ROOT=pathlib.Path(__file__).resolve().parents[3]
R3=ROOT/"research/interventions/20260922/r74_symmetric_semantic_measurement_bridge_r3.py"
R4=ROOT/"research/interventions/20260922/r74_symmetric_semantic_measurement_bridge_r4.py"
R68=ROOT/"research/interventions/20260920/R68_FRESH_PRIMARY_CASES_R1.json.gz.b64"
R69=ROOT/"research/interventions/20260921/R69_FRESH_PRIMARY_CASES_R1.json.gz.b64"

def loadmod(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def load(path):
    return json.loads(gzip.decompress(base64.b64decode(path.read_text().strip())).decode())

r3=loadmod("r74r3",R3)
r4=loadmod("r74r4",R4)
r68=load(R68); r69=load(R69)

allcases=r68["cases"]+r69["cases"]

# M1-M3 through the legacy/runtime interface retained from frozen R3.
m1_fail=[]
for c in allcases:
    if r4.score_case(copy.deepcopy(c))!=r4.score_case(copy.deepcopy(c)):
        m1_fail.append(c["case_id"])

m2_fail=[]
for c in allcases:
    a=copy.deepcopy(c); b=copy.deepcopy(c)
    a["arm"]="CONTROL"; b["arm"]="TREATMENT"
    if r4.score_case(a)!=r4.score_case(b):
        m2_fail.append(c["case_id"])

m3_fail=[c["case_id"] for c in allcases if not r4.serialization_invariant_case(copy.deepcopy(c))]

# M4 exact R68 F04.
m4_fail=[]; m4_rows=[]
for c in r68["cases"]:
    s=r4.score_case(c)
    pred=s["f04_repetition_group_count"]>0
    exp=bool(c["expected_semantic_repeat"])
    row={"case_id":c["case_id"],"expected":exp,"predicted":pred,"group_count":s["f04_repetition_group_count"]}
    m4_rows.append(row)
    if pred!=exp: m4_fail.append(row)

# M5 exact R69 F06.
m5_fail=[]; m5_rows=[]
for c in r69["cases"]:
    s=r4.score_case(c)
    verdicts=[x["verdict"] for x in s["f06_verdicts"]]
    expected=c["expected_verdict"]
    pred_ok=(any(v=="REDUNDANT_OR_MERGEABLE_SCENE" for v in verdicts)
             if expected=="REDUNDANT_OR_MERGEABLE_SCENE"
             else all(v=="NECESSARY_SEPARATE_SCENE" for v in verdicts))
    row={"case_id":c["case_id"],"expected":expected,"verdicts":verdicts,
         "redundant_count":s["f06_redundant_or_mergeable_count"],"pass":pred_ok}
    m5_rows.append(row)
    if not pred_ok: m5_fail.append(row)

# M6 original fail-closed tests.
m6_tests=[]
bad=copy.deepcopy(r68["cases"][0]); del bad["scene_graph"]["scenes"][0]["transaction_stage"]
try:
    r4.score_case(bad); m6_tests.append(False)
except r4.BridgeUnresolved: m6_tests.append(True)
bad2=copy.deepcopy(r68["cases"][0])
bad2["portfolio"]["obligations"][0].pop("kind",None)
bad2["scene_graph"]["scenes"][0].pop("transaction_kinds",None)
try:
    r4.score_case(bad2); m6_tests.append(False)
except r4.BridgeUnresolved: m6_tests.append(True)
m6=all(m6_tests)

# M7 measurement-only code boundary.
src=R4.read_text().lower()
forbidden=["openai","provider_call","render_screenplay","generate_dialogue","requests.post","httpx"]
m7=all(tok not in src for tok in forbidden)

# M8 packed-stage lossless synthetic topology.
portfolio={
 "obligations":[
   {"id":"E1","kind":"EVENT","owners":["A"],"due":True,"can_defer":False,"depends_on":[]},
   {"id":"I1","kind":"INFORMATION","owners":["A"],"due":True,"can_defer":False,"depends_on":[]},
 ],
 "defer_ids":[],"blocked_ids":[]
}
packed_case={
 "portfolio":portfolio,
 "packed_scene_graph":{"scenes":[
   {"scene_id":"S1","sequence_id":"Q1","atom_ids":["E1:a","I1:a"]},
   {"scene_id":"S2","sequence_id":"Q1","atom_ids":["E1:b","I1:b"]},
 ]},
 "atom_bindings":{"E1:a":"E1","E1:b":"E1","I1:a":"I1","I1:b":"I1"},
 "obligation_stage_plans":{
   "E1":["ENGAGE_EVENT","RESOLVE"],
   "I1":["PROBE_INFORMATION","RESOLVE"]
 },
 "sequence_graph":{"terminal_deferred_ledger":[]}
}
p=r4.score_packed_case(packed_case)
records=p["canonical_records"]
m8=(
 len(records)==2
 and records[0]["obligation_stage_profile"]==(
   ("E1",("ENGAGE_EVENT",)),("I1",("PROBE_INFORMATION",))
 )
 and records[1]["obligation_stage_profile"]==(
   ("E1",("RESOLVE",)),("I1",("RESOLVE",))
 )
 and records[1]["transaction_stage"]=="RESOLVE"
 and set(records[1]["resolved_obligation_ids"])=={"E1","I1"}
)

# M8b one physical scene may carry ADVANCE+RESOLVE for one obligation without loss.
packed_one={
 "portfolio":{"obligations":[{"id":"E1","kind":"EVENT","owners":[],"due":True,"can_defer":False,"depends_on":[]}],
              "defer_ids":[],"blocked_ids":[]},
 "packed_scene_graph":{"scenes":[{"scene_id":"S1","sequence_id":"Q1","atom_ids":["E1:a","E1:b"]}]},
 "atom_bindings":{"E1:a":"E1","E1:b":"E1"},
 "obligation_stage_plans":{"E1":["ENGAGE_EVENT","RESOLVE"]},
 "sequence_graph":{"terminal_deferred_ledger":[]}
}
one=r4.score_packed_case(packed_one)["canonical_records"][0]
m8b=(
 one["obligation_stage_profile"]==(("E1",("ENGAGE_EVENT","RESOLVE")),)
 and one["transaction_stage"]=="MIXED[ENGAGE_EVENT|RESOLVE]"
 and "E1" in one["resolved_obligation_ids"]
 and any(str(x).startswith("ADVANCE:E1:") for x in one["protected_contributions"])
 and "RESOLVE_OBLIGATION:E1" in one["protected_contributions"]
)

# M9 exact backward equivalence to frozen R3 outputs.
m9_fail=[]
for c in allcases:
    if r4.score_case(copy.deepcopy(c)) != r3.score_case(copy.deepcopy(c)):
        m9_fail.append(c["case_id"])

gates={
 "M1_identity_parity":not m1_fail,
 "M2_arm_swap_invariance":not m2_fail,
 "M3_serialization_invariance":not m3_fail,
 "M4_R68_F04_regression_16_of_16":len(m4_fail)==0 and len(m4_rows)==16,
 "M5_R69_F06_regression_16_of_16":len(m5_fail)==0 and len(m5_rows)==16,
 "M6_missing_semantic_fail_closed":m6,
 "M7_code_boundary":m7,
 "M8_packed_stage_lossless_synthetic":m8 and m8b,
 "M9_R3_backward_equivalence_32_of_32":len(m9_fail)==0 and len(allcases)==32,
}
result={
 "schema":"R74_STAGE_M_R4_PACKED_STAGE_RECOVERY_RESULT_R1",
 "status":"PASS" if all(gates.values()) else "FAIL",
 "gates":gates,
 "m1_failures":m1_fail,"m2_failures":m2_fail,"m3_failures":m3_fail,
 "m4_failures":m4_fail,"m5_failures":m5_fail,"m9_failures":m9_fail,
 "m4_rows":m4_rows,"m5_rows":m5_rows,
 "r3_bridge_sha256":hashlib.sha256(R3.read_bytes()).hexdigest(),
 "r4_bridge_sha256":hashlib.sha256(R4.read_bytes()).hexdigest(),
 "r68_dataset_sha256":hashlib.sha256(R68.read_bytes()).hexdigest(),
 "r69_dataset_sha256":hashlib.sha256(R69.read_bytes()).hexdigest(),
}
pathlib.Path("r74_stage_m_r4_result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2))
sys.exit(0 if all(gates.values()) else 3)
