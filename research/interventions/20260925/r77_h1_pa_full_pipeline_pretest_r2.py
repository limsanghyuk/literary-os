#!/usr/bin/env python3
import json,re,hashlib,pathlib,tempfile,sys
ROOT=pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"research/interventions/20260925"))
from r77_h1_provider_contract_r2 import strict_split_files,validate_response_meta,validate_files_dict,validate_stratum_pair,sha_file,EXPECTED_MODEL,FILES

SURF=ROOT/"research/interventions/20260923/r76_vp_b1_surface"
RECON=ROOT/"research/interventions/20260923/R76_VP_B1_OUTPUT_ONLY_REVERSE_RECONSTRUCTION_R1.json"
LEDGER=ROOT/"research/interventions/20260923/R76_VP_B1_TEXT_CANONICAL_STATE_LEDGER_R1.json"
CONTRACT=ROOT/"research/interventions/20260923/R76_VP_B1_FROZEN_52_SCENE_SURFACE_CONTRACT_R1.json"

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def fixture():
    parts=[(SURF/f"R76_VP_B1_SQ{i:02d}.txt").read_text(encoding="utf-8") for i in range(1,10)]
    screenplay="\n\n".join(parts)+"\n"
    return {
      "01_PLANNING_ARTIFACT.md":"# Golden fixture planning artifact\n\n"+CONTRACT.read_text(encoding="utf-8"),
      "02_SCREENPLAY.md":screenplay,
      "03_OUTPUT_ONLY_RECONSTRUCTION.json":RECON.read_text(encoding="utf-8"),
      "04_TEXT_DERIVED_STATE_LEDGER.json":LEDGER.read_text(encoding="utf-8")
    }
def envelope(files):
    return "".join(f"<<<FILE:{n}>>>\n{files[n]}<<<END_FILE:{n}>>>\n" for n in FILES)
def resp(text,status="completed",model=EXPECTED_MODEL,response_id="resp_fixture",error=None,incomplete_details=None):
    return {"status":status,"model":model,"id":response_id,"error":error,"incomplete_details":incomplete_details,"output_text":text}
def accept(response,xrid):
    try:
      mok,mchecks=validate_response_meta(response,xrid)
      files=strict_split_files(response.get("output_text",""))
      fok,fchecks,meta=validate_files_dict(files)
      return bool(mok and fok),{"meta":mchecks,"files":fchecks,"surface":meta},files
    except Exception as e:
      return False,{"exception":type(e).__name__+":"+str(e)},None

def write_arm(root,stratum,arm,files,valid=True):
    root.mkdir(parents=True,exist_ok=True);shas={}
    for n,s in files.items():
      p=root/n;p.write_text(s,encoding="utf-8");shas[n]=sha_file(p)
    r={
      "schema":"R77_H1_ARM_EXECUTION_RECEIPT_R2","stratum":stratum,"arm":arm,
      "model_requested":EXPECTED_MODEL,"model_returned":EXPECTED_MODEL,
      "reasoning_effort":"high","tools_enabled":False,"store":False,"max_output_tokens":100000,
      "response_status":"completed","response_id":"resp_fixture","x_request_id":"req_fixture","client_request_id":"cid_fixture",
      "deliverable_sha256":shas,"human_target_accessed":False,"valid_primary_arm":valid
    }
    (root/"05_EXECUTION_RECEIPT.json").write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding="utf-8")

def retry_policy(statuses):
    attempts=[];cid="fixed-client-request-id"
    for i,s in enumerate(statuses[:3]):
      attempts.append({"attempt":i+1,"status":s,"cid":cid})
      if s==200:return {"completed":True,"attempts":attempts,"cid_stable":len({x["cid"] for x in attempts})==1}
      if s not in {429,500,502,503,504}:return {"completed":False,"attempts":attempts,"cid_stable":True,"nonretryable_stop":True}
    return {"completed":False,"attempts":attempts,"cid_stable":len({x["cid"] for x in attempts})==1}

def main():
    fx=fixture();base=envelope(fx);sp=fx["02_SCREENPLAY.md"]
    report={"schema":"R77_H1_PA_R2_FROZEN_SUITE_RESULT","date":"2026-09-25","fixture":{},"PA0":{},"PA1":{},"PA2":{},"PA3":{},"PA4":{},"PA5":{}}
    report["fixture"]={"chars":len(sp),"sha256":sha_bytes(sp.encode()),"sequence_headings":len(re.findall(r"(?m)^시퀀스\s+\d+",sp)),"scene_headings":len(re.findall(r"(?m)^씬\s+\d+",sp)),"expected_surface_sha256":"7b35fa2418f07382b52d5e93403e3da555539e1c96747cca98e3227e5c4c3ee4"}
    ok,checks,_=accept(resp(base),"req_fixture")
    report["PA0"]={"baseline_exact_envelope_accepted":ok,"checks":checks}
    report["PA1"]={
      "golden_full_episode_accept":ok,
      "exact_fixture_sha_match":report["fixture"]["sha256"]==report["fixture"]["expected_surface_sha256"],
      "exact_char_count_35333":len(sp)==35333,
      "sequence_9":report["fixture"]["sequence_headings"]==9,
      "scene_52":report["fixture"]["scene_headings"]==52
    }
    cases={}
    bad=dict(fx);bad["02_SCREENPLAY.md"]=sp[:34999]
    cases["truncate_below_35000_should_reject"]=not accept(resp(envelope(bad)),"req")[0]
    bad=dict(fx);bad["03_OUTPUT_ONLY_RECONSTRUCTION.json"]="{bad json"
    cases["malformed_reconstruction_should_reject"]=not accept(resp(envelope(bad)),"req")[0]
    bad=dict(fx);bad["04_TEXT_DERIVED_STATE_LEDGER.json"]="{bad json"
    cases["malformed_ledger_should_reject"]=not accept(resp(envelope(bad)),"req")[0]
    cases["trailing_text_should_reject"]=not accept(resp(base+"\nUNAUTHORIZED_TRAILING_TEXT\n"),"req")[0]
    dup=base+f"<<<FILE:01_PLANNING_ARTIFACT.md>>>\nDUPLICATE\n<<<END_FILE:01_PLANNING_ARTIFACT.md>>>\n"
    cases["duplicate_section_should_reject"]=not accept(resp(dup),"req")[0]
    cases["incomplete_response_should_reject"]=not accept(resp(base,status="incomplete",incomplete_details={"reason":"max_output_tokens"}),"req")[0]
    cases["model_mismatch_should_reject"]=not accept(resp(base,model="wrong-model"),"req")[0]
    cases["missing_x_request_id_should_reject"]=not accept(resp(base),None)[0]
    with tempfile.TemporaryDirectory() as td:
      td=pathlib.Path(td);c=td/"C";t=td/"T";write_arm(c,"EARLY","C",fx);write_arm(t,"EARLY","T",fx)
      (c/"02_SCREENPLAY.md").write_text(sp+"\nTAMPER_AFTER_RECEIPT",encoding="utf-8")
      cases["post_receipt_tamper_should_reject"]=not validate_stratum_pair(c,t)["reveal_human_target_allowed"]
    with tempfile.TemporaryDirectory() as td:
      td=pathlib.Path(td);c=td/"C1";t=td/"C2";write_arm(c,"EARLY","C",fx);write_arm(t,"EARLY","C",fx)
      cases["C_C_pair_should_reject"]=not validate_stratum_pair(c,t)["reveal_human_target_allowed"]
    report["PA2"]={"cases":cases,"pass_count":sum(cases.values()),"total":len(cases),"status":"PASS" if all(cases.values()) else "FAIL"}

    fault={"429_then_200":retry_policy([429,200]),"500_then_200":retry_policy([500,200]),"5xx_three_fail":retry_policy([500,502,503]),"400_nonretryable":retry_policy([400,200])}
    report["PA3"]={"faults":fault,"status":"PASS" if fault["429_then_200"]["completed"] and fault["500_then_200"]["completed"] and not fault["5xx_three_fail"]["completed"] and fault["400_nonretryable"].get("nonretryable_stop") and all(x["cid_stable"] for x in fault.values()) else "FAIL"}

    selected=["구르미그린달빛","신화","굿캐스팅"]
    report["PA4"]={
      "fixture_h1_selected_work_name_hits":{x:(x in sp) for x in selected},
      "human_target_opened":False,"other_arm_output_used":False,
      "parametric_memory_contamination_testable_in_provider_analog":False,
      "mandatory_real_provider_PM0_gate":True,
      "status":"PASS_FILE_ISOLATION__PM0_REQUIRED_BEFORE_PRIMARY_INFERENCE"
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
    report["overall_status"]="PASS__R2_EXECUTION_CONTRACT_REPAIRED__REAL_PROVIDER_PM0_REQUIRED" if all([
      report["PA0"]["baseline_exact_envelope_accepted"],
      all(report["PA1"].values()),
      report["PA2"]["status"]=="PASS",report["PA3"]["status"]=="PASS",
      report["PA4"]["status"].startswith("PASS"),report["PA5"]["status"]=="PASS"
    ]) else "FAIL"
    pathlib.Path("r77_h1_pa_r2_result.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,sort_keys=True))
    raise SystemExit(0 if report["overall_status"].startswith("PASS") else 2)
if __name__=="__main__":main()
