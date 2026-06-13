import os,sys,glob,json,sqlite3,math
sys.path.insert(0,"experiments"); from meta_gt import META
DB="/sessions/upbeat-focused-bohr/scene_features.db"
con=sqlite3.connect(DB);cur=con.cursor()
# work-level aggregation
works={}
for w in [r[0] for r in cur.execute("SELECT DISTINCT work_id FROM scene_features").fetchall()]:
    rows=list(cur.execute("SELECT scene_no,conflict_intensity,scene_energy_ratio,motif_residue_score,curiosity_gradient,dialogue_ratio FROM scene_features WHERE work_id=? ORDER BY scene_no",(w,)))
    n=len(rows)
    if n<8: continue
    conf=[r[1] for r in rows]; en=[r[2] for r in rows]; mo=[r[3] for r in rows]; cu=[r[4] for r in rows]
    def mean(x): return sum(x)/len(x)
    def std(x):
        m=mean(x); return (sum((v-m)**2 for v in x)/len(x))**.5
    # climax build: corr(energy, position)
    pos=[i/(n-1) for i in range(n)]
    def corr(a,b):
        ma,mb=mean(a),mean(b); na=sum((x-ma)**2 for x in a)**.5; nb=sum((x-mb)**2 for x in b)**.5
        return sum((a[i]-ma)*(b[i]-mb) for i in range(len(a)))/(na*nb) if na*nb else 0
    # motif rises toward end? corr(motif,pos)
    works[w]=dict(n=n,conflict_mean=mean(conf),conflict_arc=std(conf),energy_mean=mean(en),
                  energy_arc=std(en),motif_mean=mean(mo),curiosity_mean=mean(cu),
                  climax_build=corr(en,pos),motif_build=corr(mo,pos))
# z-normalize across works
keys=["conflict_mean","conflict_arc","energy_mean","motif_mean","curiosity_mean","climax_build"]
def znorm(field):
    vals=[works[w][field] for w in works]; m=sum(vals)/len(vals); s=(sum((v-m)**2 for v in vals)/len(vals))**.5 or 1
    return {w:(works[w][field]-m)/s for w in works}
Z={k:znorm(k) for k in keys}
for w in works: works[w]["fitness"]=sum(Z[k][w] for k in keys)/len(keys)
# ---- EXP-A FE-7 ----
def kendall(pairs):  # list of (a_rank_metric, b... ) -> use values
    pass
def concordance(items,xf,yf):
    # items: list of work ids with both metrics; xf,yf functions
    c=d=t=0
    L=list(items)
    for i in range(len(L)):
        for j in range(i+1,len(L)):
            xi,xj=xf(L[i]),xf(L[j]); yi,yj=yf(L[i]),yf(L[j])
            if xi==xj or yi==yj: t+=1; continue
            if (xi-xj)*(yi-yj)>0: c+=1
            else: d+=1
    tau=(c-d)/(c+d) if c+d else 0
    return c,d,t,round(c/(c+d),3) if c+d else 0,round(tau,3)
mg=[w for w in works if w in META]
acc_e={w:META[w][1] for w in mg}; acc_a={w:META[w][2] for w in mg}
acc_t={w:META[w][1]+META[w][2] for w in mg}
fit={w:works[w]["fitness"] for w in mg}
print(f"=== EXP-A ★FE-7 (meta-GT works n={len(mg)}) ===")
for label,acc in [("expert",acc_e),("audience",acc_a),("expert+audience",acc_t)]:
    c,d,t,conc,tau=concordance(mg,lambda w:fit[w],lambda w:acc[w])
    print(f"  fitness vs {label:16}: concordance={conc} (C={c} D={d} ties={t}) Kendall_tau={tau}")
# also each single component vs acclaim(total) to see which formula signal aligns
print("  -- per-component vs (expert+audience) --")
for k in keys:
    c,d,t,conc,tau=concordance(mg,lambda w:works[w][k],lambda w:acc_t[w])
    print(f"     {k:14}: conc={conc} tau={tau}")
json.dump({w:works[w] for w in works},open("experiments/work_features.json","w"),ensure_ascii=False,indent=0)
print(f"\n(total works with features: {len(works)})")
