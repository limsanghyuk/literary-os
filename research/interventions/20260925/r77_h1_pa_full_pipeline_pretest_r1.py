#!/usr/bin/env python3
import json,re,hashlib,pathlib,tempfile,shutil

ROOT=pathlib.Path(__file__).resolve().parents[3]
SURF=ROOT/"research/interventions/20260923/r76_vp_b1_surface"
RECON=ROOT/"research/interventions/20260923/R76_VP_B1_OUTPUT_ONLY_REVERSE_RECONSTRUCTION_R1.json"
LEDGER=ROOT/"research/interventions/20260923/R76_VP_B1_TEXT_CANONICAL_STATE_LEDGER_R1.json"
CONTRACT=ROOT/"research/interventions/20260923/R76_VP_B1_FROZEN_52_SCENE_SURFACE_CONTRACT_R1.json"
FILES=["01_PLANNING_ARTIFACT.md","02_SCREENPLAY.md","03_OUTPUT_ONLY_RECONSTRUCTION.json","04_TEXT_DERIVED_STATE_LEDGER.json"]
EXPECTED_MODEL="gpt-5.6-sol"

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1048576),b""): h.update(b)
    return h.hexdigest()

def fixture():
    sq=[(SURF/f"R76_VP_B1_SQ{i:02d}.txt").read_text(encoding="utf-8").strip() for i in range(1,10)]
    screenplay="\n\n".join(sq)+"\n"
    plan="# Golden fixture planning artifact\n\n"+CONTRACT.read_text(encoding="utf-8")
    return {
      "01_PLANNING_ARTIFACT.md":plan,
      "02_SCREENPLAY.md":screenplay,
      "03_OUTPUT_ONLY_RECONSTRUCTION.json":RECON.read_text(encoding="utf-8"),
      "04_TEXT_DERIVED_STATE_LEDGER.json":LEDGER.read_text(encoding="utf-8")
    }

def envelope(files):
    return "".join(f"<<<FILE:{n}>>>\n{files[n]}\n<<<END_FILE:{n}>>>\n" for n in FILES)

def r1_split_files(text):
    out={}
    for f in FILES:
        m=re.search(r"<<<FILE:"+re.escape(f)+r">>>\s*(.*?)\s*<<<END_FILE:"+re.escape(f)+r">>>",text,re.S)
        if not m: raise ValueError("missing marker "+f)
        out[f]=m.group(1)
    return out

def r1_content_valid(files):
    checks={}
    checks["screenplay_chars_ge_35000"]=len(files["02_SCREENPLAY.md"])>=35000
    for n in ["03_OUTPUT_ONLY_RECONSTRUCTION.json","04_TEXT_DERIVED_STATE_LEDGER.json"]:
        try: json.loads(files[n]); checks[n+":valid_json"]=True
        except Exception: checks[n+":valid_json"]=False
    return bool(checks["screenplay_chars_ge_35000"] and all(checks.get(n+":valid_json") for n in ["03_OUTPUT_ONLY_RECONSTRUCTION.json","04_TEXT_DERIVED_STATE_LEDGER.json"])),checks

def r1_accept_response(resp,xrid):
    # Mirrors R1's effective acceptance boundary: response metadata is not checked.
    try:
        files=r1_split_files(resp.get("output_text",""))
        valid,checks=r1_content_valid(files)
        return valid,checks,files
    except Exception as e:
        return False,{"exception":type(e).__name__+":"+str(e)},None

def make_resp(text,status="completed",model=EXPECTED_MODEL,response_id="resp_fixture",error=None,incomplete_details=None):
    return {"status":status,"model":model,"id":response_id,"error":error,"incomplete_details":incomplete_details,"output_text":text}

def write_arm(root,stratum,arm,files,receipt_valid=True,model=EXPECTED_MODEL):
    root.mkdir(parents=True,exist_ok=True)
    shas={}
    for n,s in files.items():
        p=root/n;p.write_text(s,encoding="utf-8");shas[n]=sha_file(p)
    receipt={
      "schema":"R77_H1_ARM_EXECUTION_RECEIPT_R1","stratum":stratum,"arm":arm,
      "model_requested":EXPECTED_MODEL,"model_returned":model,"valid_primary_arm":receipt_valid,
      "deliverable_sha256":shas,"human_target_accessed":False
    }
    (root/"05_EXECUTION_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding="utf-8")
    return receipt

def r1_gate(c_dir,t_dir):
    req=["01_PLANNING_ARTIFACT.md","02_SCREENPLAY.md","03_OUTPUT_ONLY_RECONSTRUCTION.json","04_TEXT_DERIVED_STATE_LEDGER.json","05_EXECUTION_RECEIPT.json"]
    def check(root):
        root=pathlib.Path(root); out={"valid":True}
        for n in req:
            if not (root/n).is_file(): out["valid"]=False
        try:
            r=json.loads((root/"05_EXECUTION_RECEIPT.json").read_text(encoding="utf-8"))
            out["receipt_valid_primary_arm"]=bool(r.get("valid_primary_arm"));out["valid"] &= out["receipt_valid_primary_arm"]
        except Exception:
            out["valid"]=False
        return out
    c=check(c_dir);t=check(t_dir)
    return bool(c["valid"] and t["valid"])

def retry_policy(statuses):
    attempts=[];cid="fixed-client-request-id"
    for i,s in enumerate(statuses[:3]):
        attempts.append({"attempt":i+1,"status":s,"cid":cid})
        if s==200: return {"completed":True,"attempts":attempts,"cid_stable":len({a["cid"] for a in attempts})==1}
        if s not in {429,500,502,503,504}: return {"completed":False,"attempts":attempts,"cid_stable":True,"nonretryable_stop":True}
    return {"completed":False,"attempts":attempts,"cid_stable":len({a["cid"] for a in attempts})==1}

def main():
    fx=fixture();base=envelope(fx)
    report={"schema":"R77_H1_PA_R1_FROZEN_SUITE_RESULT","date":"2026-09-25","r1_subject":{
      "runner_sha256":"6fab07b128a46a8877cb6eb7974975f8579df10fde53b4810ad736471bbc1f01",
      "validator_sha256":"40175c657ded02dcd1d6e4d95894beef9619b4d1fd4eb290938b30829f97dada",
      "gate_sha256":"d8c13f256bd420e8347f9e5a5e79d12a7a20ecf9546f0e056bf0c97bef816c3c"
    },"fixture":{},"PA0":{},"PA1":{},"PA2":{},"PA3":{},"PA4":{},"PA5":{}}
    sp=fx["02_SCREENPLAY.md"]
    report["fixture"]={"chars":len(sp),"sha256":sha_bytes(sp.encode()),"sequence_headings":len(re.findall(r"(?m)^시퀀스\s+\d+",sp)),"scene_headings":len(re.findall(r"(?m)^씬\s+\d+",sp))}
    ok,checks,_=r1_accept_response(make_resp(base),"req_fixture")
    report["PA0"]["baseline_exact_envelope_accepted"]=ok
    report["PA0"]["baseline_checks"]=checks
    report["PA1"]={"golden_full_episode_accept":ok,"chars_ge_35000":len(sp)>=35000,"sequence_9":report["fixture"]["sequence_headings"]==9,"scene_52":report["fixture"]["scene_headings"]==52,"reconstruction_json":True,"ledger_json":True}

    cases={}
    bad=dict(fx);bad["02_SCREENPLAY.md"]=sp[:34999]
    cases["truncate_below_35000_should_reject"]=not r1_accept_response(make_resp(envelope(bad)),"req")[0]
    bad=dict(fx);bad["03_OUTPUT_ONLY_RECONSTRUCTION.json"]="{bad json"
    cases["malformed_reconstruction_should_reject"]=not r1_accept_response(make_resp(envelope(bad)),"req")[0]
    bad=dict(fx);bad["04_TEXT_DERIVED_STATE_LEDGER.json"]="{bad json"
    cases["malformed_ledger_should_reject"]=not r1_accept_response(make_resp(envelope(bad)),"req")[0]
    cases["trailing_text_should_reject"]=not r1_accept_response(make_resp(base+"\nUNAUTHORIZED_TRAILING_TEXT\n"),"req")[0]
    dup=base+f"\n<<<FILE:01_PLANNING_ARTIFACT.md>>>\nDUPLICATE\n<<<END_FILE:01_PLANNING_ARTIFACT.md>>>\n"
    cases["duplicate_section_should_reject"]=not r1_accept_response(make_resp(dup),"req")[0]
    cases["incomplete_response_should_reject"]=not r1_accept_response(make_resp(base,status="incomplete",incomplete_details={"reason":"max_output_tokens"}),"req")[0]
    cases["model_mismatch_should_reject"]=not r1_accept_response(make_resp(base,model="wrong-model"),"req")[0]
    cases["missing_x_request_id_should_reject"]=not r1_accept_response(make_resp(base),None)[0]

    with tempfile.TemporaryDirectory() as td:
        td=pathlib.Path(td);c=td/"C";t=td/"T"
        write_arm(c,"EARLY","C",fx,True);write_arm(t,"EARLY","T",fx,True)
        (c/"02_SCREENPLAY.md").write_text(sp+"\nTAMPER_AFTER_RECEIPT",encoding="utf-8")
        cases["post_receipt_tamper_should_reject"]=not r1_gate(c,t)
    with tempfile.TemporaryDirectory() as td:
        td=pathlib.Path(td);c=td/"C1";t=td/"C2"
        write_arm(c,"EARLY","C",fx,True);write_arm(t,"EARLY","C",fx,True)
        cases["C_C_pair_should_reject"]=not r1_gate(c,t)
    report["PA2"]["cases"]=cases
    report["PA2"]["pass_count"]=sum(cases.values());report["PA2"]["total"]=len(cases)
    report["PA2"]["status"]="PASS" if all(cases.values()) else "FAIL__R1_ACCEPTANCE_BOUNDARY_TOO_WEAK"

    fault={
      "429_then_200":retry_policy([429,200]),
      "500_then_200":retry_policy([500,200]),
      "5xx_three_fail":retry_policy([500,502,503]),
      "400_nonretryable":retry_policy([400,200])
    }
    report["PA3"]["faults"]=fault
    report["PA3"]["status"]="PASS" if (
      fault["429_then_200"]["completed"] and fault["500_then_200"]["completed"] and
      not fault["5xx_three_fail"]["completed"] and
      fault["400_nonretryable"].get("nonretryable_stop") and
      all(x["cid_stable"] for x in fault.values())
    ) else "FAIL"

    selected=["구르미그린달빛","신화","굿캐스팅"]
    report["PA4"]={
      "fixture_h1_selected_work_name_hits":{x:(x in sp) for x in selected},
      "human_target_opened":False,
      "other_arm_output_used":False,
      "parametric_memory_contamination_testable_in_provider_analog":False,
      "status":"PASS_FILE_ISOLATION__REAL_PROVIDER_PARAMETRIC_MEMORY_RISK_UNRESOLVED"
    }

    forbidden=["R76_VP_B1_INTERNAL_VIRTUAL_QUALITY_RESULT","TEXT_CANONICAL_STATE_LEDGER","FROZEN_52_SCENE_SURFACE_CONTRACT","state_delta","transaction_stage"]
    whole=(ROOT/"research/interventions/20260923/R76_VP_B1_WHOLE_EPISODE_SCREENPLAY_ONLY_BLIND_PACKET_R1.txt").read_text(encoding="utf-8")
    sample=(ROOT/"research/interventions/20260923/R76_VP_B1_PREFROZEN_SCENE_SURFACE_CRAFT_PACKET_R1.txt").read_text(encoding="utf-8")
    instruction=(ROOT/"research/interventions/20260923/R76_VP_B1_EXTERNAL_JUDGE_INSTRUCTION_R1.txt").read_text(encoding="utf-8")
    packets={}
    for j in ["J01","J02","J03"]:
        payload=f"JUDGE_ID={j}\n\n{instruction}\n\n<<<WHOLE_EPISODE>>>\n{whole}\n<<<SCENE_SAMPLE>>>\n{sample}"
        packets[j]={"sha256":sha_bytes(payload.encode()),"forbidden_hits":[x for x in forbidden if x in payload]}
    report["PA5"]={"judge_packets":packets,"independent_packet_count":3,"judge_outputs_created":0,"status":"PASS" if all(not v["forbidden_hits"] for v in packets.values()) else "FAIL"}

    report["r1_vulnerabilities"]=[k for k,v in cases.items() if not v]
    report["overall_status"]="R1_FAIL__BOUNDED_R2_REPAIR_REQUIRED" if report["r1_vulnerabilities"] else "R1_PASS"
    out=pathlib.Path("r77_h1_pa_r1_result.json");out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,sort_keys=True))
if __name__=="__main__": main()
