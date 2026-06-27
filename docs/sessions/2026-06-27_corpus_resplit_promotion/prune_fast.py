import os,json,glob,numpy as np
CORP="/sessions/upbeat-focused-bohr/mnt/claude/db/corpus_ko"
def ref_ids():
    ids=set()
    for f in glob.glob(CORP+"/chunks/*.jsonl"):
        for l in open(f,errors='ignore'):
            d=json.loads(l)
            if d.get("kind")=="slide": ids.add(f"{d['work_id']}::slide::{d['chunk_no']}")
            else: ids.add(f"{d['work_id']}::scene::{d['scene_no']}::{d.get('part',0)}")
    return ids
ref=ref_ids()
# Phase 1: cheap json scan -> which shards have orphans
targets=[]
for jf in glob.glob(CORP+"/emb_cache/shard_*.json"):
    meta=json.load(open(jf))
    if any(cid not in ref for cid in meta["ids"]): targets.append(jf)
print("shards_with_orphans",len(targets))
# Phase 2: rewrite only those, atomically (tmp+rename)
removed=0
for jf in targets:
    nf=jf[:-5]+".npy"
    if not os.path.exists(nf): continue
    meta=json.load(open(jf)); arr=np.load(nf)
    keep=[i for i,cid in enumerate(meta["ids"]) if cid in ref]
    removed+=len(meta["ids"])-len(keep)
    meta2={k:([meta[k][i] for i in keep] if isinstance(meta.get(k),list) and len(meta[k])==len(arr) else meta[k]) for k in meta}
    meta2["ids"]=[meta["ids"][i] for i in keep]
    np.save(nf+".tmp.npy",arr[keep]); os.replace(nf+".tmp.npy",nf)
    json.dump(meta2,open(jf+".tmp","w"),ensure_ascii=False); os.replace(jf+".tmp",jf)
print("removed",removed,"rewrote",len(targets))
