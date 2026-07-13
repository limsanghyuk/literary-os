#!/usr/bin/env python3
"""EXT6 Phase-1 Gate A (contract §8) + Gate B (contract §9) validator.
Hard gates: both must return ERRORS 0. 100% deterministic, no LLM.
Usage: python ext6_gate_ab.py <seqcard_ko_root> <work> <ep_no>
Exit code = number of ERRORS (0 = pass).
"""
import json, sys, os
from collections import Counter

# ---- contract keysets (exact) ----
BRIDGE_KEYS = {"work_id","character_key","canonical_name","aliases","entity_id",
               "mapping_status","source_registry_ref","source_registry_sha","by"}
CAST_KEYS   = {"work_id","episode_no","scene_no","character_key","entity_id",
               "presence_mode","focality","speaking_status","evidence_ref","by"}
LOAD_KEYS   = {"work_id","episode_no","character_key","entity_id","canonical_name",
               "present_scene_count","focal_scene_count","speaking_scene_count",
               "present_sequence_count","scene_share","focal_share","scene_share_band",
               "act_placement","first_scene_no","last_scene_no","max_absence_gap","by"}
PRESENCE_MODE = {"ONSCREEN","VOICE_ONLY","PHONE_OR_REMOTE","ARCHIVAL_OR_MEMORY","REFERENCED_ONLY"}
FOCALITY      = {"PRIMARY","SECONDARY","PRESENT_ONLY"}
SPEAKING      = {"SPEAKING","NONSPEAKING"}
MAPPING       = {"PROVISIONAL","MAPPED","CONFLICT"}
BANDS         = {"DOMINANT","MAJOR","MINOR","CAMEO"}
PRESENT_MODES = {"ONSCREEN","VOICE_ONLY","PHONE_OR_REMOTE","ARCHIVAL_OR_MEMORY"}

def load_jsonl(p):
    return [json.loads(l) for l in open(p,encoding="utf-8") if l.strip()]

def band(share):
    if share >= 0.50: return "DOMINANT"
    if share >= 0.20: return "MAJOR"
    if share >= 0.05: return "MINOR"
    return "CAMEO"

def run(root, work, ep):
    wid=f"{work}_{ep:02d}"
    E=[]  # errors
    def err(gate,code,msg): E.append(f"[{gate}][{code}] {msg}")

    # ---- load inputs ----
    sc   = load_jsonl(f"{root}/authored/{wid}.seqcard.jsonl")
    scene_nos = {int(r["scene_no"]) for r in sc}
    episode_scene_count = len(sc)
    bridge = load_jsonl(f"{root}/authored_bridge/{work}.bridge.jsonl")
    cast   = load_jsonl(f"{root}/authored_cast/{wid}.cast.jsonl")
    load   = load_jsonl(f"{root}/derived_character_load/{wid}.load.jsonl")
    audit_p= f"{root}/_ext6_audit/{wid}.castcoverage.json"
    audit  = json.load(open(audit_p,encoding="utf-8")) if os.path.exists(audit_p) else None
    bridge_keys = {r["character_key"] for r in bridge}

    # ================= GATE A =================
    # A1 exact keyset
    for r in bridge:
        if set(r)!=BRIDGE_KEYS: err("A","A1","bridge keyset mismatch: "+str(set(r)^BRIDGE_KEYS))
    for r in cast:
        if set(r)!=CAST_KEYS: err("A","A1","cast keyset mismatch sc%s: %s"%(r.get('scene_no'),set(r)^CAST_KEYS))
    for r in load:
        if set(r)!=LOAD_KEYS: err("A","A1","load keyset mismatch %s: %s"%(r.get('character_key'),set(r)^LOAD_KEYS))
    # A2 enum domains
    for r in bridge:
        if r["mapping_status"] not in MAPPING: err("A","A2","bad mapping_status "+str(r["mapping_status"]))
    for r in cast:
        if r["presence_mode"] not in PRESENCE_MODE: err("A","A2","bad presence_mode "+str(r["presence_mode"]))
        if r["focality"] not in FOCALITY: err("A","A2","bad focality "+str(r["focality"]))
        if r["speaking_status"] not in SPEAKING: err("A","A2","bad speaking_status "+str(r["speaking_status"]))
    for r in load:
        if r["scene_share_band"] not in BANDS: err("A","A2","bad band "+str(r["scene_share_band"]))
    # A3 type checks
    for r in cast:
        if not isinstance(r["scene_no"],int): err("A","A3","cast scene_no not int")
        if not isinstance(r["episode_no"],int): err("A","A3","cast episode_no not int")
    for r in bridge:
        if not isinstance(r["aliases"],list): err("A","A3","aliases not list")
    for r in load:
        if not isinstance(r["act_placement"],dict): err("A","A3","act_placement not dict")
        for k in ("scene_share","focal_share"):
            if not isinstance(r[k],(int,float)): err("A","A3",f"{k} not number")
    # A4 grain uniqueness: (scene_no, character_key) unique in cast
    gc=Counter((r["scene_no"],r["character_key"]) for r in cast)
    for kk,n in gc.items():
        if n>1: err("A","A4","dup grain %s x%d"%(str(kk),n))
    # A5 FK: cast/load character_key must exist in bridge; cast scene_no in seqcard
    for r in cast:
        if r["character_key"] not in bridge_keys: err("A","A5","cast char_key not in bridge: "+r["character_key"])
        if int(r["scene_no"]) not in scene_nos: err("A","A5","cast scene_no not in seqcard: %s"%r["scene_no"])
    for r in load:
        if r["character_key"] not in bridge_keys: err("A","A5","load char_key not in bridge: "+r["character_key"])
    # A6 COUNT parity: load rows == distinct present-mode char_keys in cast
    present_keys={r["character_key"] for r in cast if r["presence_mode"] in PRESENT_MODES}
    if len(load)!=len(present_keys): err("A","A6","load rows %d != present char_keys %d"%(len(load),len(present_keys)))
    # A7 recalc: re-derive load from cast and diff
    from collections import defaultdict
    seqbp = load_jsonl(f"{root}/authored_seq/{wid}.seqblueprint.jsonl")
    arc   = json.load(open(f"{root}/authored_arc/{wid}.episodearc.json",encoding="utf-8"))
    s2si={}
    for sb in seqbp:
        for sn in sb["member_scene_nos"]: s2si[int(sn)]=int(sb["seq_index"])
    si2act={}
    for a in arc["act_structure"]:
        lo,hi=a["seq_span"]
        for i in range(int(lo),int(hi)+1): si2act[i]=a["act"]
    agg=defaultdict(lambda:{"p":set(),"f":set(),"sp":set(),"si":set(),"ac":defaultdict(int)})
    for c in cast:
        if c["presence_mode"] in PRESENT_MODES:
            ck=c["character_key"]; sn=int(c["scene_no"]); d=agg[ck]
            if sn not in d["p"]:
                d["p"].add(sn); si=s2si.get(sn)
                if si is not None:
                    d["si"].add(si); ac=si2act.get(si)
                    if ac: d["ac"][ac]+=1
            if c.get("focality")=="PRIMARY": d["f"].add(sn)
            if c.get("speaking_status")=="SPEAKING": d["sp"].add(sn)
    load_by={r["character_key"]:r for r in load}
    for ck,d in agg.items():
        pres=sorted(d["p"])
        if not pres: continue
        gap=0
        for i in range(1,len(pres)): gap=max(gap,pres[i]-pres[i-1]-1)
        exp={"present_scene_count":len(pres),"focal_scene_count":len(d["f"]),
             "speaking_scene_count":len(d["sp"]),"present_sequence_count":len(d["si"]),
             "scene_share":round(len(pres)/episode_scene_count,4),
             "focal_share":round(len(d["f"])/episode_scene_count,4),
             "first_scene_no":pres[0],"last_scene_no":pres[-1],"max_absence_gap":gap}
        exp["scene_share_band"]=band(exp["scene_share"])
        r=load_by.get(ck)
        if not r: err("A","A7","missing load row for "+ck); continue
        for k,v in exp.items():
            if r[k]!=v: err("A","A7",f"{ck}.{k} got {r[k]} expect {v}")
        if dict(d["ac"])!=r["act_placement"]: err("A","A7",f"{ck}.act_placement got {r['act_placement']} expect {dict(d['ac'])}")

    # ================= GATE B =================
    # B1 scene existence already covered by A5; assert cast covers only real scenes
    # B2 presence evidence: every cast row needs non-empty evidence_ref
    for r in cast:
        if not r.get("evidence_ref") or not str(r["evidence_ref"]).strip():
            err("B","B2","empty evidence_ref sc%s %s"%(r["scene_no"],r["character_key"]))
    # B3 evidence not raw dialogue dump: evidence_ref must be a reference token, not long prose
    for r in cast:
        ev=str(r.get("evidence_ref",""))
        if len(ev)>240: err("B","B3","evidence_ref too long (raw-text?) sc%s %s"%(r["scene_no"],r["character_key"]))
    # B4 no fixed skeleton: character set must vary across scenes (not identical every scene)
    per_scene=defaultdict(set)
    for r in cast: per_scene[int(r["scene_no"])].add(r["character_key"])
    sigs={frozenset(v) for v in per_scene.values()}
    if len(per_scene)>=5 and len(sigs)==1:
        err("B","B4","identical cast in every scene (fixed skeleton?)")
    # B5 no placeholder tokens
    BAD={"TODO","TBD","PLACEHOLDER","???","N/A","NULL","XXX"}
    for r in cast+bridge+load:
        for k,v in r.items():
            if isinstance(v,str) and v.strip().upper() in BAD:
                err("B","B5",f"placeholder token in {k}: {v}")
    # B6 CastCoverageLedger union completeness
    if audit is None:
        err("B","B6","missing CastCoverageLedger "+audit_p)
    else:
        anno=set(map(int,audit.get("annotated_scene_nos",[])))
        empt=set(map(int,audit.get("empty_cast_scene_nos",[])))
        unre=set(map(int,audit.get("unresolved_scene_nos",[])))
        union=anno|empt|unre
        if union!=scene_nos:
            err("B","B6","coverage union != all scenes; missing=%s extra=%s"%(sorted(scene_nos-union),sorted(union-scene_nos)))
        if anno & empt: err("B","B6","scene both annotated and empty: "+str(sorted(anno&empt)))
        # annotated scenes must actually have cast rows
        annotated_have=set(per_scene.keys())
        if anno-annotated_have: err("B","B6","annotated scenes with no cast rows: "+str(sorted(anno-annotated_have)))
        if unre: err("B","B6","unresolved scenes remain (must be 0 at freeze): "+str(sorted(unre)))

    # ---- report ----
    print(f"[gate] {wid}: bridge={len(bridge)} cast={len(cast)} load={len(load)} scenes={episode_scene_count}")
    if E:
        print(f"ERRORS {len(E)}")
        for e in E[:80]: print("  "+e)
    else:
        print("ERRORS 0  (Gate A + Gate B PASS)")
    return len(E)

if __name__=="__main__":
    n=run(sys.argv[1], sys.argv[2], int(sys.argv[3]))
    sys.exit(n)
