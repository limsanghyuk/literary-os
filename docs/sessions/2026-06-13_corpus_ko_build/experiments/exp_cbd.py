import os,sys,json,sqlite3
sys.path.insert(0,"experiments"); from meta_gt import META
con=sqlite3.connect("/sessions/upbeat-focused-bohr/scene_features.db");cur=con.cursor()
wids=[r[0] for r in cur.execute("SELECT DISTINCT work_id FROM scene_features").fetchall()]
def mean(x): return sum(x)/len(x) if x else 0
def resample(vals,bins=20):
    n=len(vals)
    if n<bins: 
        return [vals[min(int(i*n/bins),n-1)] for i in range(bins)]
    out=[]
    for b in range(bins):
        a=int(b*n/bins); c=int((b+1)*n/bins); out.append(mean(vals[a:c]) or vals[a])
    return out
series={}; motif_build=[]
for w in wids:
    rows=list(cur.execute("SELECT scene_energy_ratio,motif_residue_score FROM scene_features WHERE work_id=? ORDER BY scene_no",(w,)))
    if len(rows)<12: continue
    en=[r[0] for r in rows]; mo=[r[1] for r in rows]
    series[w]=(resample(en),resample(mo))
    # motif_build corr with position
    n=len(mo); pos=list(range(n)); 
    mm=mean(mo);mp=mean(pos); na=sum((x-mm)**2 for x in mo)**.5; nb=sum((x-mp)**2 for x in pos)**.5
    if na*nb: motif_build.append((w,sum((mo[i]-mm)*(pos[i]-mp) for i in range(n))/(na*nb)))
# ---- EXP-C genre tension curves ----
from collections import defaultdict
gen=defaultdict(list)
for w,(en,mo) in series.items():
    if w in META: gen[META[w][0]].append(en)
print("=== EXP-C F-24/25 장르별 긴장곡선 (scene_energy, 20 normalized bins) ===")
gmeans={}
for g,curves in sorted(gen.items()):
    if len(curves)<3: continue
    avg=[mean([c[b] for c in curves]) for b in range(20)]
    # normalize 0-1 within curve for shape comparison
    lo,hi=min(avg),max(avg); norm=[(v-lo)/(hi-lo) if hi>lo else 0 for v in avg]
    gmeans[g]=norm
    # describe: peak position, start vs end
    peak=norm.index(max(norm))
    print(f"  {g:9} (n={len(curves):2}) peak@bin{peak:2}/20  start={norm[0]:.2f} mid={norm[10]:.2f} end={norm[19]:.2f}")
# between-genre divergence: avg pairwise curve distance
gl=list(gmeans); 
import itertools
if len(gl)>=2:
    dists=[sum(abs(gmeans[a][b]-gmeans[c][b]) for b in range(20))/20 for a,c in itertools.combinations(gl,2)]
    print(f"  -> genre curves mean pairwise L1 distance = {mean(dists):.3f} (>0.1 = genres differ in shape)")
# ---- EXP-B DRSE motif residue trajectory ----
mb=[v for _,v in motif_build]
print("\n=== EXP-B DRSE 잔향 정렬 ===")
print(f"  motif_residue vs position corr: mean={mean(mb):.3f} (양수=후반 잔향 누적/콜백)  works={len(mb)}")
pos_share=sum(1 for v in mb if v>0)/len(mb)
print(f"  share of works with rising motif_residue: {pos_share:.1%}")
# top callback works
mb_sorted=sorted(motif_build,key=lambda x:-x[1])[:6]
print("  최고 잔향누적 작품:",[(w,round(v,2)) for w,v in mb_sorted])
json.dump({"genre_curves":gmeans,"motif_build":dict(motif_build)},open("experiments/exp_cb.json","w"),ensure_ascii=False)
