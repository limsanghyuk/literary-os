from __future__ import annotations
from collections import Counter
from copy import deepcopy
import hashlib, json

KINDS=("EVENT","THREAD","RELATIONSHIP","CHARACTER","INFORMATION","SOCIAL","PAYOFF")
HUMAN_PRIOR={
  "source":"DB64_R108_61WORK_SOURCE_GROUNDED_CENSUS",
  "works":61,"episodes":1160,
  "source_sequence_total":10853,"source_scene_total":73639,
  "episode_sequence_p10":6,"episode_sequence_median":9,"episode_sequence_p90":14,
  "episode_scene_p10":46,"episode_scene_median":62,"episode_scene_p90":81,
  "sequence_scene_p10":3,"sequence_scene_median":7,"sequence_scene_p90":10,
  "note":"distributional prior only; never a fixed generation quota or target-episode donor"
}

def _h(v): return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def _norm(row,kind,index):
    r=deepcopy(row if isinstance(row,dict) else {"statement":str(row)})
    oid=str(r.get("id") or r.get("obligation_id") or f"{kind[:3]}-{index:03d}")
    owners=r.get("owners") or r.get("owner_ids") or ([r.get("owner")] if r.get("owner") else [])
    return {"id":oid,"kind":kind,"owners":[str(x) for x in owners if x not in (None,"")],
            "depends_on":[str(x) for x in (r.get("depends_on") or r.get("dependencies") or [])],
            "pressure":float(r.get("pressure",r.get("priority",.5))),
            "due":bool(r.get("due",r.get("due_now",True))),
            "can_defer":bool(r.get("can_defer",not r.get("due",False))),
            "statement":r.get("statement") or r.get("goal") or oid,
            "relationship_pair":deepcopy(r.get("relationship_pair")),"group_refs":deepcopy(r.get("group_refs") or []),
            "event_ref":r.get("event_ref"),"payoff_ref":r.get("payoff_ref"),"source":r}

def compile_obligation_portfolio(episode_input):
    src=deepcopy(episode_input or {}); obs=[]
    for kind in KINDS:
        for i,row in enumerate(src.get(kind.lower()+"_obligations") or [],1): obs.append(_norm(row,kind,i))
    ids=[x["id"] for x in obs]
    if len(ids)!=len(set(ids)): raise ValueError("duplicate obligation ids")
    due=[x for x in obs if x["due"] or not x["can_defer"]]; deferred=[x for x in obs if x not in due]
    return {"schema":"AdaptiveObligationPortfolioR2","obligations":obs,"due_obligations":due,"deferred_obligations":deferred,
            "due_ids":[x["id"] for x in due],"defer_ids":[x["id"] for x in deferred],
            "owner_ids":sorted({y for x in obs for y in x["owners"]}),"human_prior":deepcopy(HUMAN_PRIOR),"hash":_h(obs)}

def _rel(a,b):
    if set(a["owners"]) & set(b["owners"]): return 3
    if a["id"] in b["depends_on"] or b["id"] in a["depends_on"]: return 3
    if a.get("event_ref") and a.get("event_ref")==b.get("event_ref"): return 2
    if a.get("relationship_pair") and a.get("relationship_pair")==b.get("relationship_pair"): return 2
    if set(a.get("group_refs") or []) & set(b.get("group_refs") or []): return 1
    return 0

def _order(obs):
    by={o["id"]:o for o in obs}; pending=set(by); done=set(); out=[]
    while pending:
        ready=[by[i] for i in pending if set(by[i]["depends_on"]).issubset(done | (set(by)-pending))] or [by[i] for i in pending]
        ready.sort(key=lambda o:(-o["pressure"],o["id"])); x=ready[0]; out.append(x);pending.remove(x["id"]);done.add(x["id"])
    return out

def plan_sequences(portfolio,broadcast_mode=True):
    due=_order(portfolio.get("due_obligations") or [])
    if not due: raise ValueError("at least one due/nondeferrable obligation required")
    bundles=[]
    for o in due:
        best=None;score=-99
        for i,b in enumerate(bundles):
            if len(b)>=3: continue
            s=max((_rel(o,x) for x in b),default=0)
            same=set(y for x in b for y in x["owners"])
            if same and set(o["owners"]).issubset(same): s-=.5
            if s>score: score=s;best=i
        if best is not None and score>=1: bundles[best].append(o)
        else: bundles.append([o])
    floor=HUMAN_PRIOR["episode_sequence_median"] if broadcast_mode else 1
    while len(bundles)<floor:
        i=max(range(len(bundles)),key=lambda j:(sum(x["pressure"] for x in bundles[j])+len(bundles[j]),-j))
        b=bundles[i]
        if len(b)>1: moved=[b.pop()]
        else:
            x=b[0]; moved=[{**deepcopy(x),"id":x["id"]+f"#RETURN{len(bundles)+1}","source_obligation_id":x["id"],"kind":"RETURN_PRESSURE","depends_on":[x["id"]],"pressure":x["pressure"]*.6}]
        bundles.insert(i+1,moved)
    deferred=portfolio.get("deferred_obligations") or []
    seqs=[]
    for i,b in enumerate(bundles,1):
        base=[x.get("source_obligation_id",x["id"]) for x in b]; owners=sorted({y for x in b for y in x["owners"]}); kinds=sorted({x["kind"] for x in b})
        touches=[]
        for d in deferred:
            if any(_rel(x,d)>=1 for x in b): touches.append(d["id"])
        seqs.append({"sequence_id":f"SQ{i:02d}","order":i,"obligation_ids":base,"obligation_kinds":kinds,"owner_ids":owners,
                     "deferred_pressure_ids":sorted(set(touches)),"multi_owner":len(owners)>=2,"multi_kind":len(kinds)>=2,
                     "state_delta_required":True,"entry_pressure":round(sum(x["pressure"] for x in b)/len(b),3),
                     "weave_reason":"RELATED_MULTI_OBLIGATION" if len(b)>1 else "INDEPENDENT_OBLIGATION_ADVANCE",
                     "exit_pressure_rule":"MUST_CHANGE_STATE_OR_REFRAME_NEXT_OBLIGATION"})
    touched={x for s in seqs for x in s["deferred_pressure_ids"]}
    terminal_defer=[d["id"] for d in deferred if d["id"] not in touched]
    return {"schema":"AdaptiveSequenceArchitectureR2","sequence_count":len(seqs),"sequences":seqs,
            "terminal_deferred_ledger":terminal_defer,"human_prior":deepcopy(HUMAN_PRIOR)}

def plan_scenes(seq_plan,portfolio,broadcast_mode=True):
    by={o["id"]:o for o in portfolio["obligations"]}; plans=[]
    for seq in seq_plan["sequences"]:
        obs=[by[x] for x in seq["obligation_ids"] if x in by]
        kinds=len({o["kind"] for o in obs}) or 1; owners=len({y for o in obs for y in o["owners"]}) or 1; deps=len({d for o in obs for d in o["depends_on"]})
        pressure=sum(o["pressure"] for o in obs) or seq["entry_pressure"]
        n=max(2,min(12,2+len(obs)+kinds+(owners>=2)+(deps>0)+(pressure>=1.5)+min(2,len(seq["deferred_pressure_ids"]))))
        plans.append({"sequence_id":seq["sequence_id"],"scene_count":int(n),"obligation_ids":seq["obligation_ids"],"owner_ids":seq["owner_ids"],"kinds":seq["obligation_kinds"],"deferred_pressure_ids":seq["deferred_pressure_ids"]})
    floor=HUMAN_PRIOR["episode_scene_p10"] if broadcast_mode else 1
    total=sum(x["scene_count"] for x in plans)
    while total<floor:
        i=max(range(len(plans)),key=lambda j:(2*len(plans[j]["obligation_ids"])+len(plans[j]["owner_ids"])+len(plans[j]["kinds"])+len(plans[j]["deferred_pressure_ids"]),-plans[j]["scene_count"],-j))
        plans[i]["scene_count"]+=1; total+=1
    scenes=[]
    for p in plans:
        for j in range(1,p["scene_count"]+1):
            oid=p["obligation_ids"][(j-1)%len(p["obligation_ids"])]
            second=p["obligation_ids"][j%len(p["obligation_ids"])] if len(p["obligation_ids"])>1 and j%3==0 else None
            tx=[oid]+([second] if second and second!=oid else [])
            scenes.append({"scene_id":f"{p['sequence_id']}-SC{j:02d}","sequence_id":p["sequence_id"],"transaction_obligation_ids":tx,
                           "deferred_pressure_ids":p["deferred_pressure_ids"] if j in {1,p["scene_count"]} else [],
                           "owner_ids":p["owner_ids"],"pre_state_ref":"PREVIOUS_OUTPUT","state_delta_required":True,"physicalization_required":True,
                           "exit_pressure":"CAUSE_REACTION_CHOICE_INFORMATION_RELATION_OR_SOCIAL_CHANGE",
                           "merge_test":"REMOVAL_MUST_WEAKEN_CAUSAL_RELATIONAL_INFORMATION_SOCIAL_OR_DEBT_PROGRESS"})
    for i,s in enumerate(scenes):
        s["downstream_consumer_ref"]=scenes[i+1]["scene_id"] if i+1<len(scenes) else "EPISODE_EXIT_STATE"
    return {"schema":"AdaptiveScenePlanR2","scene_count":len(scenes),"sequence_scene_counts":{p["sequence_id"]:p["scene_count"] for p in plans},"scenes":scenes}

def reverse_reconstruction(portfolio,seq_plan,scene_plan):
    due=set(portfolio["due_ids"]); defer=set(portfolio["defer_ids"])
    seq_due={x for s in seq_plan["sequences"] for x in s["obligation_ids"]}; scene_due={x for s in scene_plan["scenes"] for x in s["transaction_obligation_ids"]}
    defer_touched={x for s in scene_plan["scenes"] for x in s.get("deferred_pressure_ids",[])} | set(seq_plan.get("terminal_deferred_ledger") or [])
    return {"due_recoverable":due.issubset(seq_due) and due.issubset(scene_due),"deferred_preserved":defer.issubset(defer_touched) and not bool(defer & scene_due),
            "missing_due_from_sequences":sorted(due-seq_due),"missing_due_from_scenes":sorted(due-scene_due),"lost_deferred":sorted(defer-defer_touched)}

def validate(portfolio,seq_plan,scene_plan,broadcast_mode=True):
    issues=[]; rr=reverse_reconstruction(portfolio,seq_plan,scene_plan); seqs=seq_plan["sequences"]
    if not rr["due_recoverable"]: issues.append("DUE_OBLIGATION_LOSS")
    if not rr["deferred_preserved"]: issues.append("DEFERRED_DEBT_LOSS_OR_FALSE_FULFILLMENT")
    if broadcast_mode and len(seqs)<HUMAN_PRIOR["episode_sequence_median"]: issues.append("BROADCAST_SEQUENCE_DEPTH")
    if broadcast_mode and scene_plan["scene_count"]<HUMAN_PRIOR["episode_scene_p10"]: issues.append("BROADCAST_SCENE_DEPTH")
    multi=sum(1 for s in seqs if s["multi_kind"] or s["multi_owner"])
    if len(seqs)>=6 and multi/len(seqs)<.25: issues.append("INSUFFICIENT_WEAVING")
    avail=set(portfolio["owner_ids"]); counts=Counter(x for s in seqs for x in s["owner_ids"])
    if len(avail)>=3 and counts and max(counts.values())/len(seqs)>.75: issues.append("OWNER_CONCENTRATION_GT75")
    vals=list(scene_plan["sequence_scene_counts"].values())
    if len(vals)>=5 and len(set(vals))==1: issues.append("UNIFORM_SEQUENCE_SCENE_GRID")
    return {"pass":not issues,"issues":issues,"reverse":rr,"metrics":{"sequence_count":len(seqs),"scene_count":scene_plan["scene_count"],"weaving_fraction":round(multi/max(1,len(seqs)),3),"scene_range":[min(vals),max(vals)],"deferred_count":len(portfolio["defer_ids"])}}

def compile_adaptive_episode_architecture(episode_input,broadcast_mode=True):
    p=compile_obligation_portfolio(episode_input); s=plan_sequences(p,broadcast_mode); sc=plan_scenes(s,p,broadcast_mode); v=validate(p,s,sc,broadcast_mode)
    return {"portfolio":p,"sequence_plan":s,"scene_plan":sc,"validation":v,"architecture_hash":_h({"p":p,"s":s,"sc":sc})}
