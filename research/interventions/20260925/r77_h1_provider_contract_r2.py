#!/usr/bin/env python3
import json,re,hashlib,pathlib

FILES=["01_PLANNING_ARTIFACT.md","02_SCREENPLAY.md","03_OUTPUT_ONLY_RECONSTRUCTION.json","04_TEXT_DERIVED_STATE_LEDGER.json"]
REQUIRED=FILES+["05_EXECUTION_RECEIPT.json"]
EXPECTED_MODEL="gpt-5.6-sol"
BANNED_SCREENPLAY_TOKENS=["state_delta","transaction_stage","obligation_id","source_obligation","provider_analog","SCENE_CONTRACT","THREAD_AXIS"]

def sha_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1048576),b""): h.update(b)
    return h.hexdigest()

def strict_split_files(text):
    if not isinstance(text,str): raise ValueError("output text must be string")
    for f in FILES:
        if text.count(f"<<<FILE:{f}>>>")!=1: raise ValueError("start marker count !=1: "+f)
        if text.count(f"<<<END_FILE:{f}>>>")!=1: raise ValueError("end marker count !=1: "+f)
    out={};pos=0
    for f in FILES:
        s=f"<<<FILE:{f}>>>";e=f"<<<END_FILE:{f}>>>"
        si=text.find(s,pos)
        if si<0: raise ValueError("missing/in-order start marker: "+f)
        if text[pos:si].strip(): raise ValueError("non-whitespace outside file envelope before "+f)
        cs=si+len(s);ei=text.find(e,cs)
        if ei<0: raise ValueError("missing end marker: "+f)
        content=text[cs:ei]
        if content.startswith("\r\n"): content=content[2:]
        elif content.startswith("\n"): content=content[1:]
        if content.endswith("\r\n"): content=content[:-2]
        elif content.endswith("\n"): content=content[:-1]
        out[f]=content
        pos=ei+len(e)
    if text[pos:].strip(): raise ValueError("non-whitespace outside final file envelope")
    return out

def validate_response_meta(resp,xrid):
    checks={
      "status_completed":resp.get("status")=="completed",
      "error_null":resp.get("error") is None,
      "incomplete_details_null":resp.get("incomplete_details") is None,
      "model_exact":resp.get("model")==EXPECTED_MODEL,
      "response_id_present":isinstance(resp.get("id"),str) and bool(resp.get("id").strip()),
      "x_request_id_present":isinstance(xrid,str) and bool(xrid.strip())
    }
    return all(checks.values()),checks

def validate_files_dict(files):
    checks={}
    sp=files.get("02_SCREENPLAY.md","")
    checks["screenplay_chars_ge_35000"]=len(sp)>=35000
    seq=len(re.findall(r"(?m)^(?:시퀀스|SEQUENCE)\s*\d+",sp,re.I))
    scenes=len(re.findall(r"(?m)^(?:씬|SCENE)\s*\d+",sp,re.I))
    checks["sequence_count_ge_9"]=seq>=9
    checks["scene_count_ge_45"]=scenes>=45
    checks["screenplay_internal_meta_leak_0"]=not any(tok.lower() in sp.lower() for tok in BANNED_SCREENPLAY_TOKENS)
    for n in ["03_OUTPUT_ONLY_RECONSTRUCTION.json","04_TEXT_DERIVED_STATE_LEDGER.json"]:
        try:
            o=json.loads(files[n]);checks[n+":valid_json_object"]=isinstance(o,dict)
        except Exception:
            checks[n+":valid_json_object"]=False
    return all(checks.values()),checks,{"screenplay_chars":len(sp),"sequence_count":seq,"scene_count":scenes}

def validate_arm_dir(root,expected_stratum=None,expected_arm=None):
    root=pathlib.Path(root);out={"root":str(root),"valid":True,"checks":{},"files":{}}
    missing=[n for n in REQUIRED if not (root/n).is_file()]
    out["missing"]=missing;out["checks"]["required_files_present"]=not missing
    if missing: out["valid"]=False; return out
    try: receipt=json.loads((root/"05_EXECUTION_RECEIPT.json").read_text(encoding="utf-8"))
    except Exception as e:
        out["valid"]=False;out["checks"]["receipt_json_valid"]=False;out["error"]=str(e);return out
    out["receipt"]=receipt
    out["checks"]["receipt_json_valid"]=True
    for n in FILES:
        got=sha_file(root/n);out["files"][n]={"sha256":got,"bytes":(root/n).stat().st_size}
        exp=(receipt.get("deliverable_sha256") or {}).get(n)
        out["checks"]["hash_match:"+n]=(got==exp)
        if got!=exp: out["valid"]=False
    sp=(root/"02_SCREENPLAY.md").read_text(encoding="utf-8")
    try:
        rec=json.loads((root/"03_OUTPUT_ONLY_RECONSTRUCTION.json").read_text(encoding="utf-8"))
        led=json.loads((root/"04_TEXT_DERIVED_STATE_LEDGER.json").read_text(encoding="utf-8"))
    except Exception: rec=led=None
    mechanics={
      "screenplay_chars_ge_35000":len(sp)>=35000,
      "sequence_count_ge_9":len(re.findall(r"(?m)^(?:시퀀스|SEQUENCE)\s*\d+",sp,re.I))>=9,
      "scene_count_ge_45":len(re.findall(r"(?m)^(?:씬|SCENE)\s*\d+",sp,re.I))>=45,
      "reconstruction_json_object":isinstance(rec,dict),
      "ledger_json_object":isinstance(led,dict),
      "receipt_valid_primary_arm":receipt.get("valid_primary_arm") is True,
      "human_target_not_accessed":receipt.get("human_target_accessed") is False,
      "model_requested_exact":receipt.get("model_requested")==EXPECTED_MODEL,
      "model_returned_exact":receipt.get("model_returned")==EXPECTED_MODEL,
      "response_status_completed":receipt.get("response_status")=="completed",
      "response_id_present":bool(receipt.get("response_id")),
      "x_request_id_present":bool(receipt.get("x_request_id")),
      "client_request_id_present":bool(receipt.get("client_request_id")),
      "reasoning_high":receipt.get("reasoning_effort")=="high",
      "tools_disabled":receipt.get("tools_enabled") is False,
      "store_false":receipt.get("store") is False
    }
    if expected_stratum is not None: mechanics["expected_stratum"]=receipt.get("stratum")==expected_stratum
    if expected_arm is not None: mechanics["expected_arm"]=receipt.get("arm")==expected_arm
    out["checks"].update(mechanics)
    if not all(mechanics.values()): out["valid"]=False
    return out

def validate_stratum_pair(c_dir,t_dir):
    c=validate_arm_dir(c_dir);t=validate_arm_dir(t_dir)
    checks={
      "C_valid":c["valid"],"T_valid":t["valid"],
      "same_stratum":c.get("receipt",{}).get("stratum")==t.get("receipt",{}).get("stratum") and c.get("receipt",{}).get("stratum") in {"EARLY","MIDDLE","LATE"},
      "arms_exact_C_T":{c.get("receipt",{}).get("arm"),t.get("receipt",{}).get("arm")}=={"C","T"},
      "same_model":c.get("receipt",{}).get("model_returned")==t.get("receipt",{}).get("model_returned")==EXPECTED_MODEL,
      "same_reasoning":c.get("receipt",{}).get("reasoning_effort")==t.get("receipt",{}).get("reasoning_effort")=="high",
      "same_max_output_tokens":c.get("receipt",{}).get("max_output_tokens")==t.get("receipt",{}).get("max_output_tokens")
    }
    return {"schema":"R77_H1_STRATUM_SEAL_GATE_R2","C":c,"T":t,"checks":checks,"reveal_human_target_allowed":all(checks.values())}
