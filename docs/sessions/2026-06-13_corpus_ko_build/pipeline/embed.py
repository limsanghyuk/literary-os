import os,glob,json,time,urllib.request,numpy as np
ROOT="/sessions/upbeat-focused-bohr/mnt/literary/corpus_ko"
CHK=ROOT+"/chunks"; CACHE=ROOT+"/emb_cache"
KEY=open("/tmp/oai.key").read().strip()
def load_chunks():
    items=[]
    for f in sorted(glob.glob(CHK+"/*.jsonl")):
        for L in open(f,errors='ignore'):
            d=json.loads(L)
            kind=d.get("kind","scene")
            if kind=="slide": cid=f"{d['work_id']}::slide::{d['chunk_no']}"
            else: cid=f"{d['work_id']}::scene::{d['scene_no']}::{d.get('part',0)}"
            t=d.get("text","").strip()
            if t: items.append((cid,kind,d["work_id"],t[:6000]))
    return items
def embed(batch):
    body=json.dumps({"model":"text-embedding-3-small","input":batch}).encode()
    req=urllib.request.Request("https://api.openai.com/v1/embeddings",data=body,
        headers={"Authorization":"Bearer "+KEY,"Content-Type":"application/json"})
    for attempt in range(5):
        try:
            r=json.load(urllib.request.urlopen(req,timeout=60))
            return [e["embedding"] for e in r["data"]]
        except Exception as ex:
            if attempt==4: raise
            time.sleep(3*(attempt+1))
def done_ids():
    s=set()
    for f in glob.glob(CACHE+"/shard_*.json"):
        s.update(json.load(open(f))["ids"])
    return s
def main():
    items=load_chunks()
    have=done_ids()
    todo=[x for x in items if x[0] not in have]
    print(f"total={len(items)} done={len(have)} todo={len(todo)}",flush=True)
    shard=len(glob.glob(CACHE+"/shard_*.json"))
    B=200; i=0
    while i<len(todo):
        chunk=todo[i:i+B]
        vecs=embed([c[3] for c in chunk])
        ids=[c[0] for c in chunk]
        meta=[{"kind":c[1],"work_id":c[2]} for c in chunk]
        np.save(f"{CACHE}/shard_{shard:04d}.npy",np.array(vecs,dtype=np.float32))
        json.dump({"ids":ids,"meta":meta},open(f"{CACHE}/shard_{shard:04d}.json","w"),ensure_ascii=False)
        shard+=1; i+=B
        if shard%5==0: print(f"  embedded {i}/{len(todo)}",flush=True)
    print("EMBED DONE shards=",shard,flush=True)
main()
