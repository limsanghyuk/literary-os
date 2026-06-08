import sys,json,math,sqlite3
sys.path.insert(0,"/tmp/rh")
from literary_system.physics.fitness_score import NarrativeFitnessComponents,NarrativeFitnessScore
from literary_system.physics.coefficient_store import PhysicsCoefficientStore
KEYS=["conflict_intensity","scene_energy_ratio","motif_residue_score","curiosity_gradient","reader_surface_score","arc_tension_score"]
def spearman(a,b):
    n=len(a)
    def rk(x):
        idx=sorted(range(n),key=lambda i:x[i]);r=[0]*n
        for p,i in enumerate(idx):r[i]=p+1
        return r
    ra,rb=rk(a),rk(b);ma=sum(ra)/n;mb=sum(rb)/n
    nu=sum((ra[i]-ma)*(rb[i]-mb) for i in range(n));de=math.sqrt(sum((ra[i]-ma)**2 for i in range(n))*sum((rb[i]-mb)**2 for i in range(n)))
    return nu/de if de else 0
# 1) 트라이스토어 ③ 피처테이블 (재)구축
works=[json.loads(l) for l in open("data/corpus_seed/scenes_5works.jsonl")]
con=sqlite3.connect(":memory:");cur=con.cursor()
cur.execute("CREATE TABLE scenes(work TEXT,sid TEXT,"+",".join(f"{k} REAL" for k in KEYS)+",quality REAL)")
for w in works:
    for s in w["scenes"]:
        cur.execute("INSERT INTO scenes VALUES(?,?,"+",".join("?"*7)+")",(w["title"],s["sid"],*[float(s[k]) for k in KEYS],float(s["quality"])))
con.commit()
# 2) 하니스가 피처테이블에서 직접 읽어 공식 적용
rows=list(cur.execute("SELECT "+",".join(KEYS)+",quality FROM scenes"))
fit=NarrativeFitnessScore(PhysicsCoefficientStore())
F=[];Q=[];comp={k:[] for k in KEYS}
for r in rows:
    vals=dict(zip(KEYS,r[:6])); q=r[6]
    F.append(fit.calculate(NarrativeFitnessComponents(**vals))); Q.append(q)
    for k in KEYS: comp[k].append(vals[k])
print(f"[연결] 피처테이블(SQLite) → 공식 하니스: N={len(F)}")
print(f"  기존 가중치 fitness vs 품질 Spearman = {spearman(F,Q):+.3f}")
corr={k:spearman(comp[k],Q) for k in KEYS}; wnew={k:max(0.0,corr[k]) for k in KEYS}; tot=sum(wnew.values())
Fnew=[sum(comp[k][i]*wnew[k] for k in KEYS)/tot*10 for i in range(len(Q))]
print(f"  상관기반 재가중 fitness vs 품질 Spearman = {spearman(Fnew,Q):+.3f}")
print("  컴포넌트 상관:", {k:round(corr[k],2) for k in KEYS})
print("=> 트라이스토어 ③ 피처테이블이 공식 검증 하니스의 입력으로 직결(SQL 질의→공식→상관).")
