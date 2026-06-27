#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HOME apply orchestrator for canonical promotion of 205 resplit episodes.
Run AT HOME where /tmp/oai.key (OpenAI text-embedding-3-small) is available.
Steps: backup -> swap scenes+chunks -> embed NEW scene ids -> prune stale ->
features -> nkg -> chroma -> 6-store parity check. Idempotent backup guard.

usage:
  python3 promote_apply.py backup     # 1. backup the 205 original scenes/chunks/features
  python3 promote_apply.py swap        # 2. copy staging scenes+chunks into corpus_ko
  python3 promote_apply.py prune       # 4. drop stale scene emb ids from emb_cache shards
  python3 promote_apply.py verify      # 6-store parity report
  # embed / features / nkg / chroma use the EXISTING corpus_ko scripts:
  #   python3 embed.py                  # 3. incremental: embeds only new scene::part ids
  #   python3 features.py               # 5. regen structural+motif/curiosity for swapped eps
  #   python3 nkg.py                    # corpus-wide knowledge graph
  #   python3 rebuild_chroma_local.py   # vector store
"""
import os,sys,re,json,glob,shutil
CORP="/sessions/upbeat-focused-bohr/mnt/claude/db/corpus_ko"   # adjust at home if needed
STG=os.path.dirname(os.path.abspath(__file__))+"/promotion_staging"
BAK=os.path.dirname(os.path.abspath(__file__))+"/promotion_backup"
def wids(): return [os.path.basename(f)[:-len(".jsonl")] for f in glob.glob(STG+"/scenes/*.jsonl")]
def backup():
    for sub in ("scenes","chunks","features"):
        os.makedirs(f"{BAK}/{sub}",exist_ok=True)
    n=0
    for w in wids():
        for sub,ext in (("scenes",".jsonl"),("chunks",".jsonl"),("features",".json")):
            src=f"{CORP}/{sub}/{w}{ext}"; dst=f"{BAK}/{sub}/{w}{ext}"
            if os.path.exists(src) and not os.path.exists(dst):
                shutil.copy2(src,dst); n+=1
    print(f"[backup] {n} files -> {BAK}  (idempotent; existing backups kept)")
def swap():
    if not os.path.isdir(BAK+"/scenes"): sys.exit("[ABORT] run backup first")
    n=0
    for w in wids():
        shutil.copy2(f"{STG}/scenes/{w}.jsonl",f"{CORP}/scenes/{w}.jsonl")
        shutil.copy2(f"{STG}/chunks/{w}.jsonl",f"{CORP}/chunks/{w}.jsonl")
        n+=1
    print(f"[swap] {n} episodes' scenes+chunks copied into corpus_ko. Now run embed.py.")
def referenced_scene_ids():
    ids=set()
    for f in glob.glob(CORP+"/chunks/*.jsonl"):
        for l in open(f,errors='ignore'):
            d=json.loads(l)
            if d.get("kind")=="slide": ids.add(f"{d['work_id']}::slide::{d['chunk_no']}")
            else: ids.add(f"{d['work_id']}::scene::{d['scene_no']}::{d.get('part',0)}")
    return ids
def prune():
    ref=referenced_scene_ids(); removed=0; kept=0
    for jf in glob.glob(CORP+"/emb_cache/shard_*.json"):
        nf=jf[:-5]+".npy"
        if not os.path.exists(nf): continue
        import numpy as np
        meta=json.load(open(jf)); arr=np.load(nf)
        keep=[i for i,cid in enumerate(meta["ids"]) if cid in ref]
        if len(keep)==len(meta["ids"]): kept+=len(keep); continue
        removed+=len(meta["ids"])-len(keep)
        meta2={k:( [meta[k][i] for i in keep] if isinstance(meta.get(k),list) and len(meta[k])==len(arr) else meta[k]) for k in meta}
        meta2["ids"]=[meta["ids"][i] for i in keep]
        np.save(nf,arr[keep]); json.dump(meta2,open(jf,"w"),ensure_ascii=False)
        kept+=len(keep)
    print(f"[prune] removed {removed} stale scene emb ids; kept {kept}. (run AFTER embed.py)")
def verify():
    s=len(glob.glob(CORP+"/scenes/*.jsonl")); c=len(glob.glob(CORP+"/chunks/*.jsonl")); fe=len(glob.glob(CORP+"/features/*.json"))
    ref=referenced_scene_ids()
    have=set()
    for jf in glob.glob(CORP+"/emb_cache/shard_*.json"): have.update(json.load(open(jf))["ids"])
    missing=ref-have; orphan=have-ref
    print(f"[verify] scenes={s} chunks={c} features={fe}")
    print(f"[verify] chunk ids={len(ref)} embedded={len(have)} | MISSING(need embed)={len(missing)} ORPHAN(prune)={len(orphan)}")
    if missing: print("  sample missing:",list(missing)[:5])
{ "backup":backup,"swap":swap,"prune":prune,"verify":verify }.get(sys.argv[1] if len(sys.argv)>1 else "verify",verify)()
