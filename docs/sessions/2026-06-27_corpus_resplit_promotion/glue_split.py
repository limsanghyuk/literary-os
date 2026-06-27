#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Char-offset (mid-line) splitter for END-GLUED scene headings the line-boundary
self_split harness cannot separate. Splits full text immediately BEFORE each regex
match. nospace-lossless by construction (no chars dropped). Same outputs as self_split.
usage:
  dry   <ep> '<regex>'   -> stats only (NO write)
  apply <ep> '<regex>'   -> scenes_resplit/<ep>.resplit.jsonl + progress
"""
import json,os,re,sys
CORP="/sessions/upbeat-focused-bohr/mnt/claude/db/corpus_ko"
WD="/sessions/upbeat-focused-bohr/mnt/claude/claude/2026-06-26_sequence_segmentation"
OUT=f"{WD}/scenes_resplit"; PROG=f"{WD}/selfsplit_progress.jsonl"
def nospace(s): return re.sub(r"\s+","",s)
def load_full(ep):
    rows=[json.loads(l) for l in open(f"{CORP}/scenes/{ep}.jsonl",encoding="utf-8") if l.strip()]
    return "".join(r.get("text","") for r in rows), len(rows)
def split_at(full,rx):
    det=re.compile(rx,re.M)
    pos=[m.start() for m in det.finditer(full)]
    pos=sorted(set([0]+[p for p in pos if p>0]))
    segs=[full[pos[i]:(pos[i+1] if i+1<len(pos) else len(full))] for i in range(len(pos))]
    return segs,pos
def stats(ep,rx):
    full,old_n=load_full(ep); segs,pos=split_at(full,rx)
    lossless=nospace("".join(segs))==nospace(full)
    sc=[len(nospace(s)) for s in segs]; mx=max(sc) if sc else 0
    return full,segs,pos,dict(ep=ep,old=old_n,new=len(segs),lossless=lossless,
        max=mx,max_under_4000=mx<4000,n=len(pos))
def cmd(mode,ep,rx):
    full,segs,pos,st=stats(ep,rx)
    print(json.dumps(st,ensure_ascii=False))
    if mode=="dry":
        for s in segs[:6]: print("  HEAD",repr(next((l for l in s.split("\n") if l.strip()),"")[:60]))
        return
    if not st["lossless"]: print("[ABORT] not lossless"); return
    os.makedirs(OUT,exist_ok=True)
    with open(f"{OUT}/{ep}.resplit.jsonl","w",encoding="utf-8") as f:
        for j,seg in enumerate(segs):
            head=next((l for l in seg.split("\n") if l.strip()),"")[:60]
            f.write(json.dumps({"scene_no":j+1,"heading_guess":head,
                "char_len":len(nospace(seg)),"text":seg},ensure_ascii=False)+"\n")
    rec={"ep":ep,"old_scene_n":st["old"],"new_scene_n":st["new"],"lossless":st["lossless"],
         "max_scene_nospace":st["max"],"max_under_4000":st["max"]<4000,
         "in_band_46_84":46<=st["new"]<=84,"n_boundaries":st["n"]}
    prev=[]
    if os.path.exists(PROG):
        prev=[json.loads(l) for l in open(PROG,encoding="utf-8") if l.strip() and json.loads(l).get("ep")!=ep]
    with open(PROG,"w",encoding="utf-8") as f:
        for r in prev: f.write(json.dumps(r,ensure_ascii=False)+"\n")
        f.write(json.dumps(rec,ensure_ascii=False)+"\n")
    status="OK" if (st["lossless"] and st["max"]<4000) else "CHECK"
    print(f"[{status}] {ep} {st['old']}->{st['new']}씬 무손실={st['lossless']} max={st['max']}")
if __name__=="__main__":
    cmd(sys.argv[1],sys.argv[2],sys.argv[3])
