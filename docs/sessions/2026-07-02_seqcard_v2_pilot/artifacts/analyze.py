import json, collections, itertools

def load(p):
    d={}
    for l in open(p):
        r=json.loads(l); d[r["scene_no"]]=r
    return d

WORKS=[("싸인_03","싸인_03.newfields.jsonl","싸인_03.gptjudge.jsonl"),
       ("베토벤바이러스_01","베토벤바이러스_01.newfields.jsonl","베토벤바이러스_01.gptjudge.jsonl")]

BOOL=["hook_flag","continuity_break","scene_blocks_need"]
NOM=["episode_role"]
ORD=["tension_role"]
ORDER={"tension_role":["build","peak","release","bridge"]}  # tension not strictly ordinal; use nominal kappa + raw

def cohen_kappa(pairs, cats=None):
    n=len(pairs)
    if n==0: return None
    po=sum(1 for a,b in pairs if a==b)/n
    ca=collections.Counter(a for a,b in pairs); cb=collections.Counter(b for a,b in pairs)
    cats=cats or set([a for a,b in pairs]+[b for a,b in pairs])
    pe=sum((ca.get(c,0)/n)*(cb.get(c,0)/n) for c in cats)
    return po,(po-pe)/(1-pe) if pe<1 else 1.0

def pabak(pairs):
    n=len(pairs); po=sum(1 for a,b in pairs if a==b)/n
    return po, 2*po-1

allpairs=collections.defaultdict(list)
contested=[]
per_work={}
for w,cf,gf in WORKS:
    C=load(cf); G=load(gf); rows={}
    common=sorted(set(C)&set(G))
    for f in BOOL+NOM+ORD:
        pr=[(C[s].get(f),G[s].get(f)) for s in common if f in C[s] and f in G[s]]
        allpairs[f]+=pr
        rows[f]=pr
    per_work[w]=(rows,common,C,G)
    for s in common:
        dis=[f for f in BOOL+NOM+ORD if C[s].get(f)!=G[s].get(f)]
        if len(dis)>=3: contested.append((w,s,dis))

print("="*60)
print("필드별 일치도 (2편 POOLED, n=118씬)")
print("="*60)
def norm_bool(v):
    return bool(v)
for f in BOOL:
    pr=[(norm_bool(a),norm_bool(b)) for a,b in allpairs[f]]
    po,pb=pabak(pr)
    # base rate
    c_pos=sum(1 for a,b in pr if a); g_pos=sum(1 for a,b in pr if b)
    print(f"[bool] {f:20s} raw={po:.2f}  PABAK={pb:+.2f}  (Claude true={c_pos}, GPT true={g_pos}, n={len(pr)})")
for f in NOM:
    po,k=cohen_kappa(allpairs[f])
    print(f"[nom ] {f:20s} raw={po:.2f}  kappa={k:+.2f}  n={len(allpairs[f])}")
for f in ORD:
    po,k=cohen_kappa(allpairs[f])
    print(f"[cat ] {f:20s} raw={po:.2f}  kappa={k:+.2f}  n={len(allpairs[f])}")

print()
print("="*60)
print("작품별 raw 일치도")
print("="*60)
for w,cf,gf in WORKS:
    rows,common,C,G=per_work[w]
    print(f"\n-- {w} (n={len(common)}) --")
    for f in BOOL+NOM+ORD:
        pr=rows[f]; po=sum(1 for a,b in pr if (norm_bool(a)==norm_bool(b) if f in BOOL else a==b))/len(pr)
        print(f"   {f:20s} raw={po:.2f}")

print()
print("="*60)
print(f"쟁점 씬 (3개 이상 필드 불일치): {len(contested)}개 / 118")
print("="*60)
for w,s,dis in contested[:40]:
    print(f"  {w} 씬{s}: {','.join(dis)}")

# confusion for episode_role & tension_role to see systematic drift
print()
print("episode_role 혼동(Claude→GPT 상위 불일치):")
conf=collections.Counter((a,b) for a,b in allpairs["episode_role"] if a!=b)
for (a,b),n in conf.most_common(8): print(f"   {a} → {b}: {n}")
print("tension_role 혼동:")
conf=collections.Counter((a,b) for a,b in allpairs["tension_role"] if a!=b)
for (a,b),n in conf.most_common(8): print(f"   {a} → {b}: {n}")
