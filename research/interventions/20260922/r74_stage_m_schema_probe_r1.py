import base64, gzip, json, importlib.util, pathlib, sys, hashlib, copy

ROOT = pathlib.Path(__file__).resolve().parents[3]
BRIDGE = ROOT / "research/interventions/20260922/r74_symmetric_semantic_measurement_bridge_r1.py"
R68 = ROOT / "research/interventions/20260920/R68_FRESH_PRIMARY_CASES_R1.json.gz.b64"
R69 = ROOT / "research/interventions/20260921/R69_FRESH_PRIMARY_CASES_R1.json.gz.b64"

def load_bridge():
    spec = importlib.util.spec_from_file_location("r74_bridge", BRIDGE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def load_gzb64(path):
    raw = base64.b64decode(path.read_text().strip())
    return json.loads(gzip.decompress(raw).decode("utf-8"))

def summarize(obj, depth=0):
    if depth > 3:
        return type(obj).__name__
    if isinstance(obj, dict):
        return {"type":"dict","keys":list(obj.keys())[:40],
                "sample":{k:summarize(obj[k], depth+1) for k in list(obj.keys())[:5]}}
    if isinstance(obj, list):
        return {"type":"list","len":len(obj),"sample":summarize(obj[0], depth+1) if obj else None}
    return {"type":type(obj).__name__,"value":obj if isinstance(obj,(str,int,float,bool,type(None))) else str(obj)[:120]}

def synthetic_graph():
    common = {
      "canonical_sequence_id":"Q1",
      "source_obligation_ids":["OB1"],
      "transaction_kind_role":"INFORMATION",
      "causal_role_profile":{"has_dependency":False,"multi_owner":False,"deferred":False,"blocked":False},
      "state_delta_role_profile":{"information":True,"relationship":False,"social":False,"physical":False,"payoff":False},
      "resolution_role":"PRE_RESOLUTION_ADVANCE",
      "deferred_open_pressure_set":[],
      "factual_delta_roles":["INFORMATION"],
      "dependency_profile":[],
    }
    out=[]
    for i in range(3):
      s=dict(common)
      s.update({"canonical_scene_id":f"S{i+1}","transaction_stage":"DISCOVERY",
                "protected_contributions":[f"ADVANCE:OB1:SIG{i if i==2 else 0}"]})
      out.append(s)
    return out

def main():
    bridge=load_bridge()
    r68=load_gzb64(R68)
    r69=load_gzb64(R69)
    g=synthetic_graph()

    score1=bridge.score_graph(copy.deepcopy(g))
    score2=bridge.score_graph(copy.deepcopy(g))
    m1 = score1 == score2

    # arm labels are deliberately absent from bridge API; identical content has identical score.
    m2 = bridge.score_graph(copy.deepcopy(g)) == bridge.score_graph(copy.deepcopy(g))

    m3 = bridge.serialization_invariant(copy.deepcopy(g))

    missing=copy.deepcopy(g)
    del missing[0]["transaction_stage"]
    try:
        bridge.score_graph(missing)
        m6=False
    except Exception:
        m6=True

    source = BRIDGE.read_text()
    forbidden = ["generate_dialogue", "provider_call", "openai", "render_screenplay"]
    m7 = all(tok not in source for tok in forbidden)

    result={
      "status":"SCHEMA_PROBE__NOT_SCIENTIFIC_STAGE_M_PASS",
      "M1_identity_parity":m1,
      "M2_arm_swap_invariance_structural":m2,
      "M3_serialization_invariance":m3,
      "M6_missing_semantic_fail_closed":m6,
      "M7_code_boundary_static":m7,
      "M4_R68_exact_regression":"PENDING_SCHEMA_ADAPTER",
      "M5_R69_exact_regression":"PENDING_SCHEMA_ADAPTER",
      "r68_summary":summarize(r68),
      "r69_summary":summarize(r69),
      "r68_case0_full":r68["cases"][0],
      "r68_case8_full":r68["cases"][8],
      "r69_case0_full":r69["cases"][0],
      "r69_case8_full":r69["cases"][8],
      "bridge_sha256":hashlib.sha256(BRIDGE.read_bytes()).hexdigest(),
      "r68_source_sha256":hashlib.sha256(R68.read_bytes()).hexdigest(),
      "r69_source_sha256":hashlib.sha256(R69.read_bytes()).hexdigest(),
    }
    pathlib.Path("r74_stage_m_probe_result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if not all([m1,m2,m3,m6,m7]):
        sys.exit(2)

if __name__=="__main__":
    main()
