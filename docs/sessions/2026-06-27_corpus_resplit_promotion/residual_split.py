#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Residual splitter: corpus already stored N scenes but a FEW are mega-glued blobs.
Preserve every existing boundary; split ONLY oversized scenes internally at heading
matches (char-offset, mid-line ok). nospace-lossless by construction.
usage: dry|apply <ep> '<heading_regex>' [minlen]
"""
import json,os,re,sys
CORP="/sessions/upbeat-focused-bohr/mnt/claude/db/corpus_ko"
WD="/sessions/upbeat-focused-bohr/mnt/claude/claude/2026-06-26_sequence_segmentation"
OUT=f"{WD}/scenes_resplit"; PROG=f"{WD}/selfsplit_progress.jsonl"
def nospace(s): return re.sub(r"\s+","",s)
def load_scenes(ep):
    return [json.loads(l).get("text","") for l in open(f"{CORP}/scenes/{ep}.jsonl",encoding="utf-8") if l.strip()]
def split_scene(text,rx):
    det=re.compile(rx)
    pos=sorted(set([0]+[m.start() for m in det.finditer(text) if m.start()>0]))
    return [text[pos[i]:(pos[i+1] if i+1<len(pos) else len(text))] for i in range(len(pos))]
def run(mode,ep,rx,minlen=2000):
    scenes=load_scenes(ep); out=[]
    for t in scenes:
        if len(nospace(t))>=minlen:
            out.extend(split_scene(t,rx))
        else:
            out.append(t)
    full="".join(scenes)
    lossless=nospace("".join(out))==nospace(full)
    sc=[len(nospace(s)) for s in out]; mx=max(sc) if sc else 0
    st=dict(ep=ep,old=len(scenes),new=len(out),lossless=lossless,max=mx,max_under_4000=mx<4000)
    print(json.dumps(st,ensure_ascii=False))
    if mode=="dry":
        for i in sorted(range(len(out)),key=lambda k:-sc[k])[:5]:
            print("  BIG",sc[i],repr(next((l for l in out[i].split("\n") if l.strip()),"")[:45]))
        return
    if not lossless: print("[ABORT] not lossless"); return
    os.makedirs(OUT,exist_ok=True)
    with open(f"{OUT}/{ep}.resplit.jsonl","w",encoding="utf-8") as f:
        for j,seg in enumerate(out):
            head=next((l for l in seg.split("\n") if l.strip()),"")[:60]
            f.write(json.dumps({"scene_no":j+1,"heading_guess":head,"char_len":len(nospace(seg)),"text":seg},ensure_ascii=False)+"\n")
    rec={"ep":ep,"old_scene_n":len(scenes),"new_scene_n":len(out),"lossless":lossless,
         "max_scene_nospace":mx,"max_under_4000":mx<4000,"in_band_46_84":46<=len(out)<=84,"n_boundaries":len(out)}
    prev=[json.loads(l) for l in open(PROG,encoding="utf-8") if l.strip() and json.loads(l).get("ep")!=ep] if os.path.exists(PROG) else []
    with open(PROG,"w",encoding="utf-8") as f:
        for r in prev: f.write(json.dumps(r,ensure_ascii=False)+"\n")
        f.write(json.dumps(rec,ensure_ascii=False)+"\n")
    print(f"[{'OK' if (lossless and mx<4000) else 'CHECK'}] {ep} {len(scenes)}->{len(out)}씬 무손실={lossless} max={mx}")
if __name__=="__main__":
    ml=int(sys.argv[4]) if len(sys.argv)>4 else 2000
    run(sys.argv[1],sys.argv[2],sys.argv[3],ml)
