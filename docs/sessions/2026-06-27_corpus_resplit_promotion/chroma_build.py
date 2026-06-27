import os,glob,json,sys,time,pickle
import numpy as np
HERE="/sessions/upbeat-focused-bohr/mnt/claude/db/corpus_ko"
CHK=HERE+"/chunks"; CACHE=HERE+"/emb_cache"; OUT=HERE+"/chroma"
DOCPKL="/tmp/chroma_docs.pkl"; DONE="/tmp/chroma_done.txt"
BUDGET=float(sys.argv[1]) if len(sys.argv)>1 else 38.0
t0=time.time()
# docs cache
if os.path.exists(DOCPKL):
    docs=pickle.load(open(DOCPKL,"rb"))
else:
    docs={}
    for f in sorted(glob.glob(CHK+"/*.jsonl")):
        for L in open(f,encoding="utf-8",errors="ignore"):
            d=json.loads(L); kind=d.get("kind","scene")
            cid=f"{d['work_id']}::slide::{d['chunk_no']}" if kind=="slide" else f"{d['work_id']}::scene::{d['scene_no']}::{d.get('part',0)}"
            t=d.get("text","").strip()
            if t: docs[cid]=t[:1800]
    pickle.dump(docs,open(DOCPKL,"wb"))
print("docs",len(docs),"t=%.1f"%(time.time()-t0),flush=True)
import chromadb
client=chromadb.PersistentClient(path=OUT)
cols={n:client.get_or_create_collection(name=n,metadata={"hnsw:space":"cosine"}) for n in ("ko_scenes","ko_slides")}
done=set()
if os.path.exists(DONE): done=set(open(DONE).read().split())
shards=sorted(glob.glob(CACHE+"/shard_*.json"))
todo=[s for s in shards if os.path.basename(s) not in done]
print("shards total",len(shards),"done",len(done),"todo",len(todo),flush=True)
proc=0; added=0
df=open(DONE,"a")
for jf in todo:
    if time.time()-t0>BUDGET: break
    nf=jf[:-5]+".npy"
    if not os.path.exists(nf): df.write(os.path.basename(jf)+"\n"); df.flush(); continue
    meta=json.load(open(jf)); ids=meta["ids"]; mm=meta.get("meta",[{}]*len(ids)); vecs=np.load(nf)
    buf={"ko_scenes":([],[],[]),"ko_slides":([],[],[])}
    for i,cid in enumerate(ids):
        m=mm[i] if i<len(mm) else {}
        kind=m.get("kind") or ("slide" if "::slide::" in cid else "scene")
        n="ko_slides" if kind=="slide" else "ko_scenes"
        b=buf[n]; b[0].append(cid); b[1].append(vecs[i].tolist()); b[2].append(docs.get(cid,""))
    for n,b in buf.items():
        if b[0]: cols[n].upsert(ids=b[0],embeddings=b[1],documents=b[2]); added+=len(b[0])
    df.write(os.path.basename(jf)+"\n"); df.flush(); proc+=1
print("processed_shards",proc,"added",added,"elapsed=%.1f"%(time.time()-t0),"rate=%.1f cid/s"%(added/max(0.1,time.time()-t0)),flush=True)
print("remaining_shards",len(todo)-proc,flush=True)
