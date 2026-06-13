import sys,json
sys.path.insert(0,"experiments"); from meta_gt import META
W=json.load(open("experiments/work_features.json"))
keys=["conflict_mean","conflict_arc","energy_mean","motif_mean","curiosity_mean","climax_build"]
mg=[w for w in W if w in META]
# z-normalize components across meta-GT works
Z={}
for k in keys:
    vals=[W[w][k] for w in mg]; m=sum(vals)/len(vals); s=(sum((v-m)**2 for v in vals)/len(vals))**.5 or 1
    Z[k]={w:(W[w][k]-m)/s for w in mg}
acc={w:META[w][1]+META[w][2] for w in mg}
def tau_comp(train,k):  # kendall tau of component k vs acclaim over 'train' works
    c=d=0
    for i in range(len(train)):
        for j in range(i+1,len(train)):
            a,b=train[i],train[j]
            xa,xb=Z[k][a],Z[k][b]; ya,yb=acc[a],acc[b]
            if xa==xb or ya==yb: continue
            if (xa-xb)*(ya-yb)>0:c+=1
            else:d+=1
    return (c-d)/(c+d) if c+d else 0
def score(w,wt): return sum(wt[k]*Z[k][w] for k in keys)
def pair_conc(test_pairs,wt):
    c=d=0
    for a,b in test_pairs:
        sa,sb=score(a,wt),score(b,wt); ya,yb=acc[a],acc[b]
        if ya==yb or sa==sb: continue
        if (sa-sb)*(ya-yb)>0:c+=1
        else:d+=1
    return c,d
# baseline equal weights
eq={k:1 for k in keys}
allpairs=[(mg[i],mg[j]) for i in range(len(mg)) for j in range(i+1,len(mg))]
c,d=pair_conc(allpairs,eq); print(f"baseline equal-weight   concordance={c/(c+d):.3f}")
# in-sample fitted (weights = tau on all)
wt_all={k:tau_comp(mg,k) for k in keys}
c,d=pair_conc(allpairs,wt_all); print(f"fitted (in-sample)      concordance={c/(c+d):.3f}  weights={ {k:round(v,2) for k,v in wt_all.items()} }")
# leave-one-out CV
cc=dd=0
for h in mg:
    train=[w for w in mg if w!=h]
    wt={k:tau_comp(train,k) for k in keys}
    test=[(h,o) for o in train]
    c,d=pair_conc(test,wt); cc+=c; dd+=d
print(f"LOO-CV (out-of-sample)  concordance={cc/(cc+dd):.3f}  (정직: 과적합 여부)")
print(f"\n해석: 가중치 부호 = {[ (k,round(wt_all[k],2)) for k in keys ]}")
