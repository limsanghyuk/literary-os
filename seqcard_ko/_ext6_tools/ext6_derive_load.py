#!/usr/bin/env python3
"""EXT6 Phase-1 CharacterLoad deterministic derivation (contract §5/§6).
Reads CastPresence + SceneCard + SequenceBlueprint + EpisodeArc + EntityBridge,
emits derived_character_load/<work>_NN.load.jsonl. 100% deterministic, no LLM.
Usage: python ext6_derive_load.py <seqcard_ko_root> <work> <ep_no>
"""
import json, sys, os
from collections import defaultdict

PRESENT_MODES = {"ONSCREEN","VOICE_ONLY","PHONE_OR_REMOTE","ARCHIVAL_OR_MEMORY"}  # REFERENCED_ONLY excluded from counts
BANDS = [(0.50,"DOMINANT"),(0.20,"MAJOR"),(0.05,"MINOR"),(0.0,"CAMEO")]

def band(share):
    for th,name in BANDS:
        if share >= th: return name
    return "CAMEO"

def load_jsonl(p):
    return [json.loads(l) for l in open(p,encoding="utf-8") if l.strip()]

def derive(root, work, ep):
    wid = f"{work}_{ep:02d}"
    sc = load_jsonl(f"{root}/authored/{wid}.seqcard.jsonl")
    episode_scene_count = len(sc)
    cast = load_jsonl(f"{root}/authored_cast/{wid}.cast.jsonl")
    seqbp = load_jsonl(f"{root}/authored_seq/{wid}.seqblueprint.jsonl")
    arc = json.load(open(f"{root}/authored_arc/{wid}.episodearc.json",encoding="utf-8"))
    bridge = {r["character_key"]: r for r in load_jsonl(f"{root}/authored_bridge/{work}.bridge.jsonl")}

    # scene_no -> seq_index (via member_scene_nos)
    scene2seqidx = {}
    for sb in seqbp:
        for sn in sb["member_scene_nos"]:
            scene2seqidx[int(sn)] = int(sb["seq_index"])
    # seq_index -> act name (via act_structure seq_span)
    seqidx2act = {}
    for a in arc["act_structure"]:
        lo,hi = a["seq_span"]
        for i in range(int(lo),int(hi)+1):
            seqidx2act[i] = a["act"]

    per = defaultdict(lambda: {"present":set(),"focal":set(),"speaking":set(),"seqidx":set(),"acts":defaultdict(int)})
    for c in cast:
        ck = c["character_key"]; sn=int(c["scene_no"])
        if c["presence_mode"] in PRESENT_MODES:
            d = per[ck]
            if sn not in d["present"]:
                d["present"].add(sn)
                si = scene2seqidx.get(sn)
                if si is not None:
                    d["seqidx"].add(si)
                    act = seqidx2act.get(si)
                    if act: d["acts"][act]+=1
            if c.get("focality")=="PRIMARY": d["focal"].add(sn)
            if c.get("speaking_status")=="SPEAKING": d["speaking"].add(sn)

    out=[]
    for ck,d in per.items():
        pres=sorted(d["present"])
        if not pres: continue
        psc=len(pres); ss=round(psc/episode_scene_count,4); fs=round(len(d["focal"])/episode_scene_count,4)
        gap=0
        for i in range(1,len(pres)): gap=max(gap,pres[i]-pres[i-1]-1)
        br=bridge.get(ck,{})
        out.append({
            "work_id":work,"episode_no":ep,"character_key":ck,
            "entity_id":br.get("entity_id"),"canonical_name":br.get("canonical_name",ck.split(":")[-1]),
            "present_scene_count":psc,"focal_scene_count":len(d["focal"]),
            "speaking_scene_count":len(d["speaking"]),"present_sequence_count":len(d["seqidx"]),
            "scene_share":ss,"focal_share":fs,"scene_share_band":band(ss),
            "act_placement":dict(d["acts"]),"first_scene_no":pres[0],"last_scene_no":pres[-1],
            "max_absence_gap":gap,"by":"derived_deterministic"})
    out.sort(key=lambda r:(-r["present_scene_count"], r["character_key"]))
    od=f"{root}/derived_character_load"; os.makedirs(od,exist_ok=True)
    op=f"{od}/{wid}.load.jsonl"
    with open(op,"w",encoding="utf-8") as f:
        for r in out: f.write(json.dumps(r,ensure_ascii=False)+"\n")
    print(f"[derive] {wid}: {len(out)} load rows, scene_count={episode_scene_count} -> {op}")
    return op

if __name__=="__main__":
    derive(sys.argv[1], sys.argv[2], int(sys.argv[3]))
