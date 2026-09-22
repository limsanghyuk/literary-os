import base64,gzip,json,importlib.util,pathlib,copy,hashlib,sys

ROOT=pathlib.Path(__file__).resolve().parents[3]
BRIDGE=ROOT/"research/interventions/20260922/r74_symmetric_semantic_measurement_bridge_r2.py"
R68=ROOT/"research/interventions/20260920/R68_FRESH_PRIMARY_CASES_R1.json.gz.b64"
R69=ROOT/"research/interventions/20260921/R69_FRESH_PRIMARY_CASES_R1.json.gz.b64"

def loadmod():
    spec=importlib.util.spec_from_file_location("r74b",BRIDGE)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
def load(path):
    return json.loads(gzip.decompress(base64.b64decode(path.read_text().strip())).decode())

b=loadmod(); r68=load(R68); r69=load(R69)

# M1 identity parity over all historical regression cases
m1_fail=[]
for dataset in (r68["cases"],r69["cases"]):
    for c in dataset:
        a=b.score_case(copy.deepcopy(c)); z=b.score_case(copy.deepcopy(c))
        if a!=z: m1_fail.append(c["case_id"])

# M2 arm-swap invariance: arm labels are ignored
m2_fail=[]
for dataset in (r68["cases"],r69["cases"]):
    for c in dataset:
        ca=copy.deepcopy(c); cb=copy.deepcopy(c)
        ca["arm"]="CONTROL"; cb["arm"]="TREATMENT"
        if b.score_case(ca)!=b.score_case(cb): m2_fail.append(c["case_id"])

# M3 serialization invariance
m3_fail=[c["case_id"] for c in r68["cases"]+r69["cases"] if not b.serialization_invariant_case(copy.deepcopy(c))]

# M4 exact R68 16-case regression
m4_rows=[]; m4_fail=[]
for c in r68["cases"]:
    s=b.score_case(c)
    pred=s["f04_repetition_group_count"]>0
    exp=bool(c["expected_semantic_repeat"])
    row={"case_id":c["case_id"],"expected":exp,"predicted":pred,"group_count":s["f04_repetition_group_count"]}
    m4_rows.append(row)
    if pred!=exp: m4_fail.append(row)

# M5 exact R69 16-case regression
m5_rows=[]; m5_fail=[]
for c in r69["cases"]:
    s=b.score_case(c)
    verdicts=[x["verdict"] for x in s["f06_verdicts"]]
    expected=c["expected_verdict"]
    if expected=="REDUNDANT_OR_MERGEABLE_SCENE":
        pred_ok=any(v=="REDUNDANT_OR_MERGEABLE_SCENE" for v in verdicts)
    else:
        pred_ok=all(v=="NECESSARY_SEPARATE_SCENE" for v in verdicts)
    row={"case_id":c["case_id"],"expected":expected,"verdicts":verdicts,
         "redundant_count":s["f06_redundant_or_mergeable_count"],"pass":pred_ok}
    m5_rows.append(row)
    if not pred_ok: m5_fail.append(row)

# M6 missing-semantic fail-closed
m6_tests=[]
bad=copy.deepcopy(r68["cases"][0])
del bad["scene_graph"]["scenes"][0]["transaction_stage"]
try:
    b.score_case(bad); m6_tests.append(False)
except b.BridgeUnresolved: m6_tests.append(True)
bad2=copy.deepcopy(r68["cases"][0])
bad2["portfolio"]["obligations"][0].pop("kind",None)
bad2["scene_graph"]["scenes"][0].pop("transaction_kinds",None)
try:
    b.score_case(bad2); m6_tests.append(False)
except b.BridgeUnresolved: m6_tests.append(True)
m6=all(m6_tests)

# M7 code boundary
src=BRIDGE.read_text()
forbidden=["openai","provider_call","render_screenplay","generate_dialogue","requests.post","httpx"]
m7=all(tok not in src.lower() for tok in forbidden)

gates={
 "M1_identity_parity":not m1_fail,
 "M2_arm_swap_invariance":not m2_fail,
 "M3_serialization_invariance":not m3_fail,
 "M4_R68_F04_regression_16_of_16":len(m4_fail)==0 and len(m4_rows)==16,
 "M5_R69_F06_regression_16_of_16":len(m5_fail)==0 and len(m5_rows)==16,
 "M6_missing_semantic_fail_closed":m6,
 "M7_code_boundary":m7,
}
result={
 "schema":"R74_STAGE_M_CLEAN_RESULT_R1",
 "status":"PASS" if all(gates.values()) else "FAIL",
 "gates":gates,
 "m1_failures":m1_fail,"m2_failures":m2_fail,"m3_failures":m3_fail,
 "m4_failures":m4_fail,"m5_failures":m5_fail,
 "m4_rows":m4_rows,"m5_rows":m5_rows,
 "bridge_sha256":hashlib.sha256(BRIDGE.read_bytes()).hexdigest(),
 "r68_dataset_sha256":hashlib.sha256(R68.read_bytes()).hexdigest(),
 "r69_dataset_sha256":hashlib.sha256(R69.read_bytes()).hexdigest(),
}
pathlib.Path("r74_stage_m_clean_result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2))
sys.exit(0 if all(gates.values()) else 3)
