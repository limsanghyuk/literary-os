import os,sys,glob,json,sqlite3,numpy as np
sys.path.insert(0,"experiments"); from meta_gt import META
CACHE="/sessions/upbeat-focused-bohr/emb2"
# scene embeddings per (work,scene) averaged over parts
from collections import defaultdict
acc=defaultdict(lambda:[None,0])
for jf in glob.glob(CACHE+"/shard_*.json"):
    meta=json.load(open(jf)); vecs=np.load(jf[:-5]+".npy")
    for i,cid in enumerate(meta["ids"]):
        if "::scene::" in cid:
            w,_,sn,_=cid.split("::"); k=(w,int(sn))
            a=acc[k]; a[0]=vecs[i] if a[0] is None else a[0]+vecs[i]; a[1]+=1
E={k:(v[0]/v[1]) for k,v in acc.items()}
con=sqlite3.connect("/sessions/upbeat-focused-bohr/scene_features.db");cur=con.cursor()
wids=[r[0] for r in cur.execute("SELECT DISTINCT work_id FROM scene_features").fetchall()]
def cos(a,b):
    na=np.linalg.norm(a);nb=np.linalg.norm(b); return float(a@b/(na*nb)) if na and nb else 0
feats={}
for w in wids:
    rows=list(cur.execute("SELECT scene_no,conflict_intensity,scene_energy_ratio,n_chars,dialogue_ratio FROM scene_features WHERE work_id=? ORDER BY scene_no",(w,)))
    n=len(rows)
    if n<8: continue
    vs=[E.get((w,r[0])) for r in rows]
    conf=[r[1] for r in rows]; en=[r[2] for r in rows]; ln=[r[3] for r in rows]; dl=[r[4] for r in rows]
    pos=[i/(n-1) for i in range(n)]
    def mean(x): return sum(x)/len(x)
    def corr(a,b):
        ma,mb=mean(a),mean(b); na=sum((x-ma)**2 for x in a)**.5; nb=sum((x-mb)**2 for x in b)**.5
        return sum((a[i]-ma)*(b[i]-mb) for i in range(len(a)))/(na*nb) if na*nb else 0
    # callback strength: each scene's max cosine to prior scenes with gap>=3
    cb=[]; cb_late=[]
    cent=np.mean([v for v in vs if v is not None],axis=0) if any(v is not None for v in vs) else None
    coh=[]
    for i in range(n):
        if vs[i] is None: continue
        if cent is not None: coh.append(cos(vs[i],cent))
        prior=[cos(vs[i],vs[j]) for j in range(0,i-2) if vs[j] is not None]
        if prior:
            m=max(prior); cb.append(m)
            if i>=n*0.66: cb_late.append(m)
    feats[w]=dict(
        e_scenelen=mean(ln), e_dialogue=mean(dl), e_energyvar=(sum((x-mean(en))**2 for x in en)/n)**.5,
        e_conf_escalation=corr(conf,pos),
        m_callback=mean(cb) if cb else 0, m_callback_late=mean(cb_late) if cb_late else 0,
        m_coherence=mean(coh) if coh else 0,
        # originals for reference
        o_energy=mean(en), o_conflict=mean(conf),
    )
# tau vs acclaim
mg=[w for w in feats if w in META]
acc_t={w:META[w][1]+META[w][2] for w in mg}
def tau(field):
    c=d=0
    for i in range(len(mg)):
        for j in range(i+1,len(mg)):
            a,b=mg[i],mg[j]; xa,xb=feats[a][field],feats[b][field]; ya,yb=acc_t[a],acc_t[b]
            if xa==xb or ya==yb: continue
            if (xa-xb)*(ya-yb)>0:c+=1
            else:d+=1
    return round((c-d)/(c+d),3) if c+d else 0
print(f"=== 성분 재정의 vs (전문가+관객) Kendall tau, n={len(mg)} ===")
print("  [기존] o_energy   :",tau("o_energy"),"  o_conflict:",tau("o_conflict"))
print("  -- energy 재정의 후보 --")
for f in ["e_scenelen","e_dialogue","e_energyvar","e_conf_escalation"]: print(f"     {f:18}: tau={tau(f)}")
print("  -- motif 재정의 후보 --")
for f in ["m_callback","m_callback_late","m_coherence"]: print(f"     {f:18}: tau={tau(f)}")
json.dump(feats,open("experiments/redefine_feats.json","w"),ensure_ascii=False)
