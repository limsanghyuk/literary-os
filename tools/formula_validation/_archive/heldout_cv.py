import sys,json,math
sys.path.insert(0,"/tmp/rc")
from literary_system.physics.fitness_score import NarrativeFitnessComponents,NarrativeFitnessScore
from literary_system.physics.coefficient_store import PhysicsCoefficientStore
KEYS=["conflict_intensity","scene_energy_ratio","motif_residue_score","curiosity_gradient","reader_surface_score","arc_tension_score"]
def spearman(a,b):
    n=len(a)
    if n<2: return 0
    def rk(x):
        idx=sorted(range(n),key=lambda i:x[i]);r=[0]*n
        for p,i in enumerate(idx):r[i]=p+1
        return r
    ra,rb=rk(a),rk(b);ma=sum(ra)/n;mb=sum(rb)/n
    nu=sum((ra[i]-ma)*(rb[i]-mb) for i in range(n));de=math.sqrt(sum((ra[i]-ma)**2 for i in range(n))*sum((rb[i]-mb)**2 for i in range(n)))
    return nu/de if de else 0
works=[json.loads(l) for l in open("data/corpus_seed/scenes_5works.jsonl")]
def scenes_of(ws):
    out=[]
    for w in ws:
        for s in w["scenes"]:
            out.append(({k:float(s[k]) for k in KEYS}, float(s["quality"])))
    return out
fit=NarrativeFitnessScore(PhysicsCoefficientStore())
def fit_default(c): return fit.calculate(NarrativeFitnessComponents(**c))
# 작품단위 leave-one-out: 4편으로 가중치 학습, 1편(held-out)에 적용
heldF_def=[];heldF_rw=[];heldQ=[]
for i in range(len(works)):
    train=[w for j,w in enumerate(works) if j!=i]; test=[works[i]]
    tr=scenes_of(train)
    corr={k:spearman([c[k] for c,q in tr],[q for c,q in tr]) for k in KEYS}
    wnew={k:max(0.0,corr[k]) for k in KEYS}; tot=sum(wnew.values()) or 1
    for c,q in scenes_of(test):
        heldF_def.append(fit_default(c))
        heldF_rw.append(sum(c[k]*wnew[k] for k in KEYS)/tot*10)
        heldQ.append(q)
print("=== 작품단위 Leave-One-Out 교차검증 (held-out 30씬, 누수 없음) ===")
print(f"held-out 기존가중치 fitness vs 품질  Spearman = {spearman(heldF_def,heldQ):+.3f}")
print(f"held-out 재가중      fitness vs 품질  Spearman = {spearman(heldF_rw,heldQ):+.3f}")
print(f"(참고 in-sample: 기존 0.70 / 재가중 0.73)")
d=spearman(heldF_rw,heldQ)-spearman(heldF_def,heldQ)
print(f"재가중 일반화 효과(held-out 차) = {d:+.3f}  →", "일반화됨(과적합 아님)" if d>=-0.02 else "과적합 의심")
