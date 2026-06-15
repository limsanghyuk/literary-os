import os,glob,json,numpy as np,chromadb
ROOT="/sessions/upbeat-focused-bohr/mnt/literary/corpus_ko"
CACHE=ROOT+"/emb_cache"; CHK=ROOT+"/chunks"
# id -> text
txt={}
for f in glob.glob(CHK+"/*.jsonl"):
    for L in open(f,errors='ignore'):
        d=json.loads(L); k=d.get("kind","scene")
        cid=f"{d['work_id']}::slide::{d['chunk_no']}" if k=="slide" else f"{d['work_id']}::scene::{d['scene_no']}::{d.get('part',0)}"
        txt[cid]=d.get("text","")[:1800]
client=chromadb.PersistentClient(path="/sessions/upbeat-focused-bohr/chroma_build")
cs=client.get_or_create_collection("ko_scenes",metadata={"hnsw:space":"cosine"})
cl=client.get_or_create_collection("ko_slides",metadata={"hnsw:space":"cosine"})
mark="/sessions/upbeat-focused-bohr/.chroma_added"; added=set(open(mark).read().split()) if os.path.exists(mark) else set()
shards=sorted(glob.glob(CACHE+"/shard_*.npy"))
import time;START=time.time()
for sp in shards:
    sid=os.path.basename(sp)[:-4]
    if sid in added: continue
    if time.time()-START>34: print("time budget",flush=True); break
    vecs=np.load(sp); meta=json.load(open(sp[:-4]+".json"))
    ids=meta["ids"]; ms=meta["meta"]
    Si=[i for i,m in enumerate(ms) if m["kind"]!="slide"]; Li=[i for i,m in enumerate(ms) if m["kind"]=="slide"]
    if Si:
        cs.add(ids=[ids[i] for i in Si],embeddings=[vecs[i].tolist() for i in Si],
               documents=[txt.get(ids[i],"") for i in Si],
               metadatas=[{"work_id":ms[i]["work_id"]} for i in Si])
    if Li:
        cl.add(ids=[ids[i] for i in Li],embeddings=[vecs[i].tolist() for i in Li],
               documents=[txt.get(ids[i],"") for i in Li],
               metadatas=[{"work_id":ms[i]["work_id"]} for i in Li])
    added.add(sid); open(mark,"w").write("\n".join(sorted(added)))
print(f"added shards={len(added)}/{len(shards)} | scenes={cs.count()} slides={cl.count()}",flush=True)
