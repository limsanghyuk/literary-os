#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical-promotion STAGING builder (CPU-only, non-destructive).
For each resplit episode: remap resplit boundaries (defined by nospace content)
back onto the BYTE-EXACT original corpus full-text, so concatenation stays
byte-identical (=> slide chunks & slide embeddings invariant); only scene
boundaries move. Then re-derive canonical scenes + scene-chunks. Writes to
promotion_staging/ ONLY. Emits parity report + emb-id delta. No corpus mutation."""
import os,re,json,glob,hashlib
CORP="/sessions/upbeat-focused-bohr/mnt/claude/db/corpus_ko"
WD="/sessions/upbeat-focused-bohr/mnt/claude/claude/2026-06-26_sequence_segmentation"
RS=WD+"/scenes_resplit"; STG=WD+"/promotion_staging"
def nospace(s): return re.sub(r"\s+","",s)
def sliding(text,size=1400,ov=150):
    text=re.sub(r'\n{3,}','\n\n',text); out=[];i=0;n=len(text);k=0
    while i<n:
        seg=text[i:i+size]
        if seg.strip(): out.append({"chunk_no":k,"text":seg.strip()}); k+=1
        i+=size-ov
    return out
def remap(old_full, new_nospace_lens):
    """cut old_full (byte-exact) at byte offsets where cumulative nospace count
    reaches each boundary; monotonic (>=), robust to clustering."""
    bounds=[]; c=0
    for L in new_nospace_lens[:-1]:
        c+=L; bounds.append(c)
    cuts=[0]; ns=0; bi=0; i=0; n=len(old_full)
    while i<n and bi<len(bounds):
        if not old_full[i].isspace(): ns+=1
        while bi<len(bounds) and ns>=bounds[bi]:
            cuts.append(i+1); bi+=1
        i+=1
    cuts.append(n)
    return [old_full[cuts[k]:cuts[k+1]] for k in range(len(cuts)-1)]

def main():
    os.makedirs(STG+"/scenes",exist_ok=True); os.makedirs(STG+"/chunks",exist_ok=True)
    files=sorted(glob.glob(RS+"/*.resplit.jsonl"))
    rep=[]; bad=[]
    for f in files:
        wid=os.path.basename(f)[:-len(".resplit.jsonl")]
        scf=CORP+"/scenes/"+wid+".jsonl"
        old=[json.loads(l)["text"] for l in open(scf,errors='ignore') if l.strip()]
        old_full="".join(old)
        rsc=[json.loads(l) for l in open(f,errors='ignore') if l.strip()]
        rsc=[d for d in rsc if len(nospace(d["text"]))>0]   # drop whitespace-only fragments
        new_lens=[len(nospace(d["text"])) for d in rsc]
        if sum(new_lens)!=len(nospace(old_full)):
            bad.append((wid,"nospace-sum-mismatch")); continue
        new_texts=remap(old_full,new_lens)
        # parity: byte-identical full
        if "".join(new_texts)!=old_full:
            bad.append((wid,"remap-not-byte-identical")); continue
        # canonical scenes
        scenes=[]
        for i,t in enumerate(new_texts):
            head=rsc[i].get("heading_guess") or next((l for l in t.split("\n") if l.strip()),"")[:60]
            scenes.append({"work_id":wid,"scene_no":i+1,"heading":head,"text":t,"method":"resplit"})
        # scene-chunks (mirror parse.py: >1500 -> sliding(1400,150) parts)
        sch=[]
        for s in scenes:
            if len(s["text"])<=1500:
                sch.append({"work_id":wid,"scene_no":s["scene_no"],"heading":s["heading"],"text":s["text"]})
            else:
                for p,sub in enumerate(sliding(s["text"],1400,150)):
                    sch.append({"work_id":wid,"scene_no":s["scene_no"],"part":p,"heading":s["heading"],"text":sub["text"]})
        with open(STG+"/scenes/"+wid+".jsonl","w") as o:
            for s in scenes: o.write(json.dumps(s,ensure_ascii=False)+"\n")
        with open(STG+"/chunks/"+wid+".jsonl","w") as o:
            for c in sch: o.write(json.dumps(c,ensure_ascii=False)+"\n")
        # emb id delta (scene ids only; slides invariant since full text identical)
        def scene_ids_from_chunks(path):
            ids=set()
            for l in open(path,errors='ignore'):
                d=json.loads(l)
                if d.get("kind")=="slide": continue
                ids.add(f"{wid}::scene::{d['scene_no']}::{d.get('part',0)}")
            return ids
        old_ids=scene_ids_from_chunks(CORP+"/chunks/"+wid+".jsonl")
        new_ids=set(f"{wid}::scene::{c['scene_no']}::{c.get('part',0)}" for c in sch)
        rep.append(dict(wid=wid,old_scenes=len(old),new_scenes=len(scenes),
            old_scene_chunks=len(old_ids),new_scene_chunks=len(new_ids),
            stale_ids=len(old_ids-new_ids),new_to_embed=len(new_ids-old_ids),
            reused_ids=len(old_ids&new_ids),byte_identical=True))
    json.dump({"episodes":len(rep),"failed":bad,"report":rep},
        open(STG+"/staging_report.json","w"),ensure_ascii=False,indent=1)
    tot_new=sum(r["new_to_embed"] for r in rep); tot_stale=sum(r["stale_ids"] for r in rep)
    tot_reuse=sum(r["reused_ids"] for r in rep)
    print(f"staged={len(rep)} failed={len(bad)} {bad[:5]}")
    print(f"scene-chunks to EMBED(new)={tot_new}  stale-to-prune={tot_stale}  reused={tot_reuse}")
    print(f"all byte-identical full-text => slide embeddings 100% invariant")
main()
