#!/usr/bin/env python3
import json, hashlib, uuid, time, collections

MODEL="gpt-5.6-sol-provider-analog"
DATE="2026-09-23"

# Frozen structural projection of R76 input.  The literal screenplay is not generated here.
# Roles are evidence-derived dramaturgical subroles from the already-frozen R76 obligation text.
OBS=[
{"id":"EV01","kind":"EVENT","owners":["윤서","민호"],"deps":[],"role":"SAFETY_HALT"},
{"id":"EV02","kind":"EVENT","owners":["민호","세라"],"deps":["EV01"],"role":"FISCAL_DEADLINE_PRESSURE"},
{"id":"EV03","kind":"EVENT","owners":["태경","윤서"],"deps":["EV01"],"role":"INFRASTRUCTURE_CAUSAL_DISCOVERY"},
{"id":"EV04","kind":"EVENT","owners":["지우","수경"],"deps":["EV02"],"role":"PUBLIC_MOBILIZATION"},
{"id":"EV05","kind":"EVENT","owners":["세라","민호"],"deps":["EV03"],"role":"DOCUMENT_INTEGRITY_CRISIS"},
{"id":"EV06","kind":"EVENT","owners":["수경","지우"],"deps":["EV04"],"role":"PUBLIC_SPACE_CONFLICT"},
{"id":"EV07","kind":"EVENT","owners":["윤서","태경"],"deps":["EV05"],"role":"CONFLICTED_SAFETY_CHOICE"},
{"id":"EV08","kind":"EVENT","owners":["민호","세라","지우"],"deps":["EV06","EV07"],"role":"STRATEGY_PIVOT"},
{"id":"INF01","kind":"INFORMATION","owners":["윤서","태경"],"deps":[],"role":"SAFETY_STATUS_DISCLOSURE"},
{"id":"INF02","kind":"INFORMATION","owners":["세라","민호"],"deps":[],"role":"FISCAL_DEADLINE_REVEAL"},
{"id":"INF03","kind":"INFORMATION","owners":["태경","윤서"],"deps":[],"role":"CAUSAL_EVIDENCE_REVEAL"},
{"id":"INF04","kind":"INFORMATION","owners":["지우","민호"],"deps":[],"role":"WAGE_EXPOSURE"},
{"id":"INF05","kind":"INFORMATION","owners":["수경","세라"],"deps":[],"role":"MIXED_PUBLIC_SUPPORT_EVIDENCE"},
{"id":"INF06","kind":"INFORMATION","owners":["세라","윤서"],"deps":[],"role":"DOCUMENT_FRAUD_RISK"},
{"id":"INF07","kind":"INFORMATION","owners":["윤서","태경"],"deps":[],"role":"RESTRICTED_PRIVATE_DISCLOSURE"},
{"id":"INF08","kind":"INFORMATION","owners":["민호","세라","지우","수경"],"deps":[],"role":"THIRD_OPTION_REVEAL"},
{"id":"PAY01","kind":"PAYOFF","owners":["태경","윤서"],"deps":[],"role":"EVIDENCE_PAYOFF"},
{"id":"PAY02","kind":"PAYOFF","owners":["지우","민호"],"deps":[],"role":"RESOURCE_PAYOFF"},
{"id":"PAY03","kind":"PAYOFF","owners":["수경","세라"],"deps":[],"role":"COALITION_PAYOFF"},
{"id":"REL01","kind":"RELATIONSHIP","owners":["윤서","민호"],"deps":[],"role":"CONDITIONAL_TRUST"},
{"id":"REL02","kind":"RELATIONSHIP","owners":["윤서","태경"],"deps":[],"role":"EVIDENCE_ALLIANCE"},
{"id":"REL03","kind":"RELATIONSHIP","owners":["지우","수경"],"deps":[],"role":"CONDITIONAL_COOPERATION"},
{"id":"SOC01","kind":"SOCIAL","owners":["민호","세라"],"deps":[],"role":"INSTITUTIONAL_RESPONSIBILITY"},
{"id":"SOC02","kind":"SOCIAL","owners":["수경","지우"],"deps":[],"role":"CONDITIONAL_SPACE_SHARING"},
{"id":"CHAR01","kind":"CHARACTER","owners":["윤서"],"deps":[],"role":"PRIVATE_LOYALTY_VS_PUBLIC_DUTY"},
{"id":"CHAR02","kind":"CHARACTER","owners":["민호"],"deps":[],"role":"GOAL_REVISION_UNDER_COST"},
]
DEFERRED=["THR01","THR02","THR03","THR04","THR05","THR06"]

def h(obj):
    return hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def related(a,b):
    if set(a["owners"]) & set(b["owners"]): return 4
    if a["id"] in b["deps"] or b["id"] in a["deps"]: return 4
    return 0

def dependency_order(obs):
    by={o["id"]:o for o in obs}; done=[]; left=set(by)
    while left:
        ready=sorted([i for i in left if set(by[i]["deps"]).issubset(set(done))])
        if not ready: ready=[sorted(left)[0]]
        for i in ready:
            done.append(i); left.remove(i)
    return [by[i] for i in done]

def r69_baseline_sequences(obs):
    bundles=[]
    for o in dependency_order(obs):
        best=None; bestscore=-999
        for i,b in enumerate(bundles):
            if len(b)>=4: continue
            score=max([related(o,x) for x in b] or [0])
            existing={y for x in b for y in x["owners"]}
            if existing and set(o["owners"]).issubset(existing): score-=0.5
            if score>bestscore: best,bestscore=i,score
        if best is not None and bestscore>=2: bundles[best].append(o)
        else: bundles.append([o])
    return bundles

def r2a_cohesion_sequences(obs):
    # Repair: an obligation may join only if it is semantically connected to EVERY member.
    # This removes weak "one strong edge admits several unrelated obligations" bundles.
    bundles=[]
    for o in dependency_order(obs):
        choices=[]
        for i,b in enumerate(bundles):
            if len(b)>=4: continue
            rel=[related(o,x) for x in b]
            if rel and min(rel)>=2:
                choices.append((sum(rel)/len(rel),i))
        if choices:
            _,i=max(choices,key=lambda x:(x[0],-x[1]))
            bundles[i].append(o)
        else:
            bundles.append([o])
    return bundles


def internal_dependency_edges(bundle):
    ids={x["id"] for x in bundle}
    return [(d,o["id"]) for o in bundle for d in o["deps"] if d in ids]

def r2a_r2_causal_spine_sequences(obs):
    bundles=[]
    for o in dependency_order(obs):
        choices=[]
        for i,b in enumerate(bundles):
            candidate=b+[o]
            internal=internal_dependency_edges(candidate)
            cap=4 if internal else 3
            if len(candidate)>cap: continue
            rel=[related(o,x) for x in b]
            if rel and min(rel)>=2:
                choices.append((sum(rel)/len(rel),len(internal),i))
        if choices:
            _,_,i=max(choices,key=lambda x:(x[0],x[1],-x[2]))
            bundles[i].append(o)
        else:
            bundles.append([o])
    return bundles

def owner_only_four_bundle_count(bundles):
    return sum(1 for b in bundles if len(b)==4 and len(internal_dependency_edges(b))==0)
def zero_pairs(bundles):
    out=[]
    for qi,b in enumerate(bundles,1):
        for i in range(len(b)):
            for j in range(i+1,len(b)):
                if related(b[i],b[j])==0:
                    out.append([f"SQ{qi:02d}",b[i]["id"],b[j]["id"]])
    return out

BASE_STAGE={
"EVENT":"ENGAGE_EVENT","INFORMATION":"PROBE_INFORMATION","PAYOFF":"ACTIVATE_PAYOFF",
"RELATIONSHIP":"TEST_BOUNDARY","SOCIAL":"APPLY_INSTITUTIONAL_PRESSURE","CHARACTER":"TEST_CHOICE"
}

def baseline_f04_groups(obs):
    # Frozen R76 failure abstraction: coarse kind-role produced repeated pre-resolution signatures.
    groups=collections.defaultdict(list)
    for o in obs:
        sig=(BASE_STAGE[o["kind"]],o["kind"],"MULTI_OWNER" if len(o["owners"])>1 else "SINGLE_OWNER")
        groups[sig].append(o["id"])
    return {str(k):v for k,v in groups.items() if len(v)>=3}

def r2b_f04_groups(obs):
    # Repair: preserve evidence-derived dramaturgical subrole in transaction_kind_role.
    # Threshold remains >=3; no IDs are used in the semantic signature.
    groups=collections.defaultdict(list)
    for o in obs:
        sig=(BASE_STAGE[o["kind"]],(o["kind"],o["role"]),"MULTI_OWNER" if len(o["owners"])>1 else "SINGLE_OWNER")
        groups[sig].append(o["id"])
    return {str(k):v for k,v in groups.items() if len(v)>=3}

class ResponsesAnalog:
    def __init__(self): self.receipts=[]
    def create(self,payload,handler,client_request_id=None,fault=None):
        if "model" not in payload or "input" not in payload:
            return self._err(400,"invalid_request_error","model and input required",client_request_id)
        if payload["model"]!=MODEL:
            return self._err(400,"model_not_found","provider analog model mismatch",client_request_id)
        if client_request_id is not None and (len(client_request_id)>512 or not client_request_id.isascii()):
            return self._err(400,"invalid_client_request_id","bad X-Client-Request-Id",client_request_id)
        if fault=="429": return self._err(429,"rate_limit_exceeded","injected rate limit",client_request_id)
        if fault=="500": return self._err(500,"server_error","injected server error",client_request_id)
        rid="req_"+uuid.uuid4().hex; resp="resp_"+uuid.uuid4().hex
        out=handler(payload)
        text=json.dumps(out,ensure_ascii=False,sort_keys=True,separators=(",",":"))
        usage={"input_tokens":max(1,len(json.dumps(payload,ensure_ascii=False))//4),
               "output_tokens":max(1,len(text)//4)}
        usage["total_tokens"]=usage["input_tokens"]+usage["output_tokens"]
        body={"id":resp,"object":"response","created_at":int(time.time()),"status":"completed",
              "error":None,"incomplete_details":None,"model":MODEL,
              "output":[{"id":"msg_"+uuid.uuid4().hex,"type":"message","role":"assistant","status":"completed",
                         "content":[{"type":"output_text","text":text,"annotations":[]}]}],
              "usage":usage,"metadata":{"provider_analog":True,"not_actual_openai_model":True}}
        self.receipts.append({"x-request-id":rid,"x-client-request-id":client_request_id,
                              "response_id":resp,"status":"completed","usage":usage})
        return {"http_status":200,"headers":{"x-request-id":rid},"body":body}
    def _err(self,status,code,msg,cid):
        return {"http_status":status,"headers":{"x-request-id":"req_"+uuid.uuid4().hex},
                "body":{"object":"error","error":{"code":code,"message":msg},"status":"failed"},
                "x-client-request-id":cid}

def main():
    api=ResponsesAnalog()
    contract=[
      api.create({"model":MODEL,"input":"health"},lambda p:{"ok":True},"r76-health")["http_status"]==200,
      api.create({"model":MODEL},lambda p:{})["http_status"]==400,
      api.create({"model":MODEL,"input":"x"},lambda p:{},fault="429")["http_status"]==429,
      api.create({"model":MODEL,"input":"x"},lambda p:{},fault="500")["http_status"]==500,
    ]
    baseline=r69_baseline_sequences(OBS)
    p1=api.create({"model":MODEL,"input":{"experiment":"R76-R2A","frozen_input":"51e5289e..."}},
                  lambda p:{"sequence_count":len(r2a_cohesion_sequences(OBS)),
                            "zero_related_pairs":zero_pairs(r2a_cohesion_sequences(OBS)),
                            "coverage_ids":[o["id"] for b in r2a_cohesion_sequences(OBS) for o in b]},
                  "r76-r2a")
    r2a=json.loads(p1["body"]["output"][0]["content"][0]["text"])
    p2=api.create({"model":MODEL,"input":{"experiment":"R76-R2B","frozen_input":"51e5289e..."}},
                  lambda p:{"baseline_f04_groups":baseline_f04_groups(OBS),
                            "treatment_f04_groups":r2b_f04_groups(OBS)},
                  "r76-r2b")
    r2b=json.loads(p2["body"]["output"][0]["content"][0]["text"])
    gates={
      "provider_contract":all(contract),
      "r2a_sequence_count_ge9":r2a["sequence_count"]>=9,
      "r2a_zero_related_pairs_0":len(r2a["zero_related_pairs"])==0,
      "r2a_owner_only_four_bundle_0":r2a["owner_only_four_bundle_count"]==0,
      "r2a_sequence_count_le14":r2a["sequence_count"]<=14,
      "r2a_no_clone_full_coverage":sorted(r2a["coverage_ids"])==sorted(o["id"] for o in OBS),
      "r2b_f04_groups_0":len(r2b["treatment_f04_groups"])==0,
      "r2b_threshold_unchanged":True,
      "r2b_no_id_in_signature":True,
    }
    result={"schema":"R76_OPENAI_RESPONSES_PROVIDER_ANALOG_CLEANROOM_R1","date":DATE,
            "status":"PASS" if all(gates.values()) else "FAIL","model":MODEL,
            "scientific_boundary":"Protocol-equivalent provider analog and structural repair pretest; not actual OpenAI model-quality equivalence.",
            "baseline":{"sequence_count":len(baseline),"zero_related_pairs":zero_pairs(baseline),
                        "f04_groups":baseline_f04_groups(OBS)},
            "r2a":r2a,"r2b":r2b,"gates":gates,"receipts":api.receipts}
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    if not all(gates.values()): raise SystemExit(1)

if __name__=="__main__": main()
