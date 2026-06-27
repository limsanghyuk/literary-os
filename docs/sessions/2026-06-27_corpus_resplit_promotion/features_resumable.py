import os,glob,json,re,sqlite3,time,numpy as np,pickle
from collections import defaultdict
CORP="/sessions/upbeat-focused-bohr/mnt/claude/db/corpus_ko"
SCN=CORP+"/scenes"; CACHE=CORP+"/emb_cache"; FEAT=CORP+"/features"
DB="/sessions/upbeat-focused-bohr/scene_features.db"
DONE="/tmp/feat_done.txt"; EMBPK="/tmp/emb_avg.pkl"
os.makedirs(FEAT,exist_ok=True)
t0=time.time()
# ---- emb dict (cached to disk) ----
if os.path.exists(EMBPK):
    emb=pickle.load(open(EMBPK,'rb'))
else:
    acc=defaultdict(lambda:[None,0])
    for jf in glob.glob(CACHE+"/shard_*.json"):
        meta=json.load(open(jf)); vecs=np.load(jf[:-5]+".npy")
        for i,cid in enumerate(meta["ids"]):
            if "::scene::" in cid:
                w,_,sn,_=cid.split("::"); key=(w,int(sn))
                a=acc[key]; a[0]=vecs[i] if a[0] is None else a[0]+vecs[i]; a[1]+=1
    emb={k:(v[0]/v[1]).astype(np.float32) for k,v in acc.items()}
    pickle.dump(emb,open(EMBPK,'wb')); print("built emb",len(emb),"sec",round(time.time()-t0,1))
def cos(a,b):
    na=np.linalg.norm(a); nb=np.linalg.norm(b)
    return float(a.dot(b)/(na*nb)) if na and nb else 0.0
CONFLICT=re.compile(r'(죽|피|칼|총|싸움|싸운|때리|때려|소리(치|질)|분노|화가|울|비명|공격|도망|쫓|협박|위협|폭|터지|destroy|배신|증오|복수)')
EMO=re.compile(r'[!?]|\.\.\.|…')
DIAL=re.compile(r'^\s*[가-힣A-Za-z][가-힣A-Za-z0-9 ]{0,7}\s*[:：]')
def feats(text):
    lines=[l for l in text.splitlines() if l.strip()]
    n=len(lines) or 1; chars=len(text) or 1
    dial=sum(1 for l in lines if DIAL.match(l))
    short=sum(1 for l in lines if len(l.strip())<14)
    conflict=len(CONFLICT.findall(text))/(chars/100)
    energy=(len(EMO.findall(text))+short)/(chars/100)
    return dict(n_chars=chars,n_lines=n,n_dialogue=dial,dialogue_ratio=round(dial/n,3),
                conflict_intensity=round(conflict,3),scene_energy_ratio=round(energy,3))
done=set(open(DONE).read().split()) if os.path.exists(DONE) else set()
con=sqlite3.connect(DB); cur=con.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS scene_features(work_id TEXT,scene_no INT,heading TEXT,method TEXT,
 n_chars INT,n_lines INT,n_dialogue INT,dialogue_ratio REAL,conflict_intensity REAL,
 scene_energy_ratio REAL,motif_residue_score REAL,curiosity_gradient REAL,
 PRIMARY KEY(work_id,scene_no))""")
allw=sorted(glob.glob(SCN+"/*.jsonl"))
todo=[f for f in allw if os.path.basename(f)[:-6] not in done]
print("works total",len(allw),"done",len(done),"todo",len(todo))
proc=0
df=open(DONE,'a')
for sf in todo:
    if time.time()-t0>36: break
    w=os.path.basename(sf)[:-6]
    scenes=[json.loads(L) for L in open(sf,errors='ignore')]
    prior=[]; out=[]
    for s in scenes:
        sn=s["scene_no"]; F=feats(s["text"]); v=emb.get((w,sn)); motif=cur_g=0.0
        if v is not None and prior:
            sims=[cos(v,pv) for pv in prior if pv is not None]
            if sims: motif=round(sum(sims)/len(sims),3); cur_g=round(1-max(sims),3)
        prior.append(v)
        cur.execute("INSERT OR REPLACE INTO scene_features VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (w,sn,s.get("heading","")[:120],s.get("method",""),F["n_chars"],F["n_lines"],
             F["n_dialogue"],F["dialogue_ratio"],F["conflict_intensity"],F["scene_energy_ratio"],motif,cur_g))
        out.append({"scene_no":sn,**F,"motif_residue_score":motif,"curiosity_gradient":cur_g})
    json.dump(out,open(FEAT+"/"+w+".json","w"),ensure_ascii=False)
    df.write(w+"\n"); df.flush(); proc+=1
con.commit(); con.close()
print("processed_this_run",proc,"elapsed",round(time.time()-t0,1))
