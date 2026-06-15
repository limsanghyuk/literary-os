import os,glob,json,re,sqlite3,numpy as np,math
ROOT="/sessions/upbeat-focused-bohr/mnt/literary/corpus_ko"
SCN=ROOT+"/scenes"; CACHE=ROOT+"/emb_cache"; FEAT=ROOT+"/features"
os.makedirs(FEAT,exist_ok=True)
# 1) load scene embeddings: avg parts per (work,scene)
from collections import defaultdict
acc=defaultdict(lambda:[None,0])
for jf in glob.glob(CACHE+"/shard_*.json"):
    meta=json.load(open(jf)); vecs=np.load(jf[:-5]+".npy")
    for i,cid in enumerate(meta["ids"]):
        if "::scene::" in cid:
            w,_,sn,_=cid.split("::"); key=(w,int(sn))
            a=acc[key]; a[0]=vecs[i] if a[0] is None else a[0]+vecs[i]; a[1]+=1
emb={k:(v[0]/v[1]) for k,v in acc.items()}
def cos(a,b):
    na=np.linalg.norm(a); nb=np.linalg.norm(b)
    return float(a.dot(b)/(na*nb)) if na and nb else 0.0
# lexicons
CONFLICT=re.compile(r'(죽|피|칼|총|싸움|싸운|때리|때려|소리(치|질)|분노|화가|울|비명|공격|도망|쫓|협박|위협|폭|터지|destroy|배신|증오|복수)')
EMO=re.compile(r'[!?]|\.\.\.|…')
DIAL=re.compile(r'^\s*[가-힣A-Za-z][가-힣A-Za-z0-9 ]{0,7}\s*[:：]')
SPEAK=re.compile(r'^\s*([가-힣]{2,5})\s*[:：(]')
def feats(text):
    lines=[l for l in text.splitlines() if l.strip()]
    n=len(lines) or 1; chars=len(text) or 1
    dial=sum(1 for l in lines if DIAL.match(l))
    short=sum(1 for l in lines if len(l.strip())<14)
    conflict=len(CONFLICT.findall(text))/(chars/100)        # per 100 chars
    energy=(EMO.findall(text).__len__()+short)/(chars/100)   # punctuation+short-line tempo
    dialr=dial/n
    return dict(n_chars=chars,n_lines=n,n_dialogue=dial,dialogue_ratio=round(dialr,3),
                conflict_intensity=round(conflict,3),scene_energy_ratio=round(energy,3))
# 2) build table
con=sqlite3.connect("/sessions/upbeat-focused-bohr/scene_features.db"); cur=con.cursor()
cur.execute("DROP TABLE IF EXISTS scene_features")
cur.execute("""CREATE TABLE scene_features(work_id TEXT,scene_no INT,heading TEXT,method TEXT,
 n_chars INT,n_lines INT,n_dialogue INT,dialogue_ratio REAL,conflict_intensity REAL,
 scene_energy_ratio REAL,motif_residue_score REAL,curiosity_gradient REAL,
 PRIMARY KEY(work_id,scene_no))""")
rows=0; perwork={}
for sf in sorted(glob.glob(SCN+"/*.jsonl")):
    w=os.path.basename(sf)[:-6]
    scenes=[json.loads(L) for L in open(sf,errors='ignore')]
    prior=[]; out=[]
    for s in scenes:
        sn=s["scene_no"]; F=feats(s["text"])
        v=emb.get((w,sn))
        motif=cur_g=0.0
        if v is not None and prior:
            sims=[cos(v,pv) for pv in prior if pv is not None]
            if sims:
                motif=round(sum(sims)/len(sims),3)          # echo of prior scenes
                cur_g=round(1-max(sims),3)                   # novelty vs most-similar prior
        prior.append(v)
        rec=(w,sn,s.get("heading","")[:120],s.get("method",""),F["n_chars"],F["n_lines"],
             F["n_dialogue"],F["dialogue_ratio"],F["conflict_intensity"],F["scene_energy_ratio"],
             motif,cur_g)
        cur.execute("INSERT OR REPLACE INTO scene_features VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",rec)
        out.append({"scene_no":sn,**F,"motif_residue_score":motif,"curiosity_gradient":cur_g}); rows+=1
    json.dump(out,open(FEAT+"/"+w+".json","w"),ensure_ascii=False)
    perwork[w]=len(out)
con.commit()
cur.execute("SELECT COUNT(*),COUNT(DISTINCT work_id) FROM scene_features"); print("rows,works:",cur.fetchone())
cur.execute("SELECT ROUND(AVG(conflict_intensity),3),ROUND(AVG(scene_energy_ratio),3),ROUND(AVG(motif_residue_score),3),ROUND(AVG(curiosity_gradient),3) FROM scene_features WHERE motif_residue_score>0")
print("avg conflict/energy/motif/curiosity:",cur.fetchone())
con.close(); print("rows=",rows)
