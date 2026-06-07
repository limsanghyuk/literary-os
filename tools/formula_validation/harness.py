import sys,json,math
sys.path.insert(0,"/tmp/v745s/repo")
from literary_system.physics.fitness_score import NarrativeFitnessComponents, NarrativeFitnessScore
from literary_system.physics.coefficient_store import PhysicsCoefficientStore
def spearman(a,b):
    n=len(a)
    def rank(x):
        idx=sorted(range(n),key=lambda i:x[i]); r=[0]*n
        for pos,i in enumerate(idx): r[i]=pos+1
        return r
    ra,rb=rank(a),rank(b); ma=sum(ra)/n; mb=sum(rb)/n
    num=sum((ra[i]-ma)*(rb[i]-mb) for i in range(n))
    den=math.sqrt(sum((ra[i]-ma)**2 for i in range(n))*sum((rb[i]-mb)**2 for i in range(n)))
    return num/den if den else 0.0
works=[json.loads(l) for l in open("scenes.jsonl")]
fit=NarrativeFitnessScore(PhysicsCoefficientStore())
F=[];Q=[]
comp_corr={k:[] for k in ["conflict_intensity","scene_energy_ratio","motif_residue_score","curiosity_gradient","reader_surface_score","arc_tension_score"]}
for w in works:
    for s in w["scenes"]:
        comp=NarrativeFitnessComponents(
            conflict_intensity=s["conflict_intensity"],scene_energy_ratio=s["scene_energy_ratio"],
            motif_residue_score=s["motif_residue_score"],curiosity_gradient=s["curiosity_gradient"],
            reader_surface_score=s["reader_surface_score"],arc_tension_score=s["arc_tension_score"])
        F.append(fit.calculate(comp)); Q.append(float(s["quality"]))
        for k in comp_corr: comp_corr[k].append(s[k])
print("=== STAGE 1: 실 fitness 공식 vs 품질판정(proxy GT) ===")
print(f"N(씬)={len(F)}")
print(f"fitness 범위 {min(F):.2f}~{max(F):.2f} (평균 {sum(F)/len(F):.2f}/10)")
print(f"Spearman(fitness, quality) = {spearman(F,Q):+.3f}")
print("--- 컴포넌트별 vs 품질 상관(공식이 무엇에 기대는가) ---")
for k,v in comp_corr.items(): print(f"  {k:22s} {spearman(v,Q):+.3f}")
# DRSE 잔향: 복선 plant-payoff 의미 유사도
try:
    from literary_system.drse.drse_engine import TFIDFSemanticScorer
    sc=TFIDFSemanticScorer(); sims=[]
    for w in works:
        for fp in w.get("foreshadow_pairs",[]):
            sims.append(sc.score(fp["plant"],fp["payoff"]))
    print("\n=== STAGE 2: DRSE 잔향 — 복선 plant↔payoff 의미 정합 ===")
    print(f"복선쌍 N={len(sims)}  평균 sim={sum(sims)/len(sims):.3f}  범위 {min(sims):.2f}~{max(sims):.2f}")
except Exception as ex:
    print("\nDRSE 실행 예외:",ex)
