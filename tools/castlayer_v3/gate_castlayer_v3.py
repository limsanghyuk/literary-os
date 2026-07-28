#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cast Layer v3 게이트 — BRIDGE-1 / POV-1,2,3. ERRORS>0 이면 비영 종료."""
import json, os, sys, glob, collections

BRIDGE_KEYS = ["work_id","character_key","canonical_name","aliases","entity_id",
               "mapping_status","source_registry_ref","source_registry_sha","by"]
STATUS = {"PROVISIONAL","MAPPED","CONFLICT"}

def gate_bridge(d):
    E=[]; W=[]; n=0; seen=collections.defaultdict(set)
    for fp in sorted(glob.glob(os.path.join(d,"*.bridge.jsonl"))):
        for i,l in enumerate(open(fp,encoding="utf-8"),1):
            l=l.strip()
            if not l: continue
            n+=1; r=json.loads(l); loc=f"{os.path.basename(fp)}:{i}"
            if list(r.keys())!=BRIDGE_KEYS: E.append(f"BRIDGE-1 키셋 불일치 {loc}")
            if r.get("mapping_status") not in STATUS: E.append(f"BRIDGE-1 enum 위반 {loc}")
            if not isinstance(r.get("aliases"),list): E.append(f"BRIDGE-1 aliases 타입 {loc}")
            k=r.get("character_key")
            if k in seen[r.get("work_id")]: E.append(f"BRIDGE-1 grain 중복 {loc} {k}")
            seen[r.get("work_id")].add(k)
            if r.get("mapping_status")=="CONFLICT": W.append(f"BRIDGE-1 CONFLICT {loc} {r.get('canonical_name')}")
    return n,E,W

def gate_pov(path, bridged):
    """POV-1 타입 list[str] / POV-2 bridge FK / POV-3 4개 이상 WARN"""
    E=[]; W=[]; n=0; unresolved=0
    for l in open(path,encoding="utf-8"):
        l=l.strip()
        if not l: continue
        n+=1; r=json.loads(l)
        v=r.get("pov_char")
        if not isinstance(v,list): E.append(f"POV-1 타입 위반 seq={r.get('sequence_id')}"); continue
        if not all(isinstance(x,str) for x in v): E.append(f"POV-1 원소타입 seq={r.get('sequence_id')}")
        for x in v:
            if x not in bridged.get(r.get("work_id_series"),set()):
                unresolved+=1; W.append(f"POV-2 미해결 {r.get('sequence_id')} {x}")
        if len(v)>=4: W.append(f"POV-3 4인이상 {r.get('sequence_id')} n={len(v)}")
    return n,E,W,unresolved

if __name__=="__main__":
    bd=sys.argv[1]; pv=sys.argv[2] if len(sys.argv)>2 else None
    n,E,W=gate_bridge(bd)
    out={"BRIDGE_records":n,"BRIDGE_errors":len(E),"BRIDGE_warns":len(W)}
    if pv and os.path.exists(pv):
        bridged=collections.defaultdict(set)
        for fp in glob.glob(os.path.join(bd,"*.bridge.jsonl")):
            for l in open(fp,encoding="utf-8"):
                r=json.loads(l); bridged[r["work_id"]].add(r["character_key"])
        pn,pE,pW,unres=gate_pov(pv,bridged)
        out.update({"POV_records":pn,"POV_errors":len(pE),"POV_warns":len(pW),"POV_unresolved":unres})
        E+=pE; W+=pW
    out["ERRORS_TOTAL"]=len(E)
    print(json.dumps(out,ensure_ascii=False))
    for e in E[:10]: print("  ERR:",e)
    for w in W[:5]: print("  WARN:",w)
    sys.exit(1 if E else 0)
