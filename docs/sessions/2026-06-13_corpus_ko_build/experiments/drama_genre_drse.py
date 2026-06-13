import os,glob,json,sqlite3,re
from collections import defaultdict
con=sqlite3.connect("/sessions/upbeat-focused-bohr/scene_features.db");cur=con.cursor()
# 드라마 시리즈 → 장르
DGEN={"신사의품격":"romcom","위대한유산":"romcom","귀여운여인":"romance","궁":"romance","넌어느별에서왔니":"romance",
"넌내게반했어":"romcom","밤이면밤마다":"romance","어느멋진날":"melo","여우야뭐하니":"romcom","역전의여왕":"romcom",
"옥탑방고양이":"romcom","원더풀라이프":"romcom","장난스런키스":"romcom","장밋빛인생":"melo","두번째프러포즈":"melo",
"알게될거야":"melo","네자매이야기":"melo","트리플":"drama","태양의후예":"action","적도의남자":"thriller",
"개와늑대의시간":"action","강적들":"crime","별순검S1":"crime","별순검S2":"crime"}
def series(w):
    m=re.match(r'(태후|신품)',w)
    if w.startswith("태후"): return "태양의후예"
    for s in DGEN:
        if w.startswith(s): return s
    if re.match(r'^\d+부$',w): return "신사의품격"  # 신품 episodes named N부
    return None
wids=[r[0] for r in cur.execute("SELECT DISTINCT work_id FROM scene_features").fetchall()]
def mean(x): return sum(x)/len(x) if x else 0
def resample(v,b=20):
    n=len(v)
    return [mean(v[int(i*n/b):int((i+1)*n/b)]) or v[min(int(i*n/b),n-1)] for i in range(b)]
gen=defaultdict(list); drse_build=defaultdict(list)
for w in wids:
    s=series(w)
    if not s: continue
    g=DGEN.get(s)
    rows=list(cur.execute("SELECT scene_energy_ratio,motif_residue_score FROM scene_features WHERE work_id=? ORDER BY scene_no",(w,)))
    if len(rows)<12: continue
    en=[r[0] for r in rows]; mo=[r[1] for r in rows]
    gen[g].append(resample(en))
    n=len(mo);mp=(n-1)/2;ma=mean(mo)
    na=sum((x-ma)**2 for x in mo)**.5;nb=sum((i-mp)**2 for i in range(n))**.5
    if na*nb: drse_build[g].append(sum((mo[i]-ma)*(i-mp) for i in range(n))/(na*nb))
print("=== 드라마 장르별 긴장곡선 (에피소드 단위, 20분位) ===")
gm={}
for g,curves in sorted(gen.items()):
    if len(curves)<5: continue
    avg=[mean([c[b] for c in curves]) for b in range(20)]
    lo,hi=min(avg),max(avg); nrm=[(v-lo)/(hi-lo) if hi>lo else 0 for v in avg]
    gm[g]=nrm
    peak=nrm.index(max(nrm))
    print(f"  {g:9}(n={len(curves):3}ep) peak@bin{peak:2} start={nrm[0]:.2f} mid={nrm[10]:.2f} **end={nrm[19]:.2f}**")
print("\n=== 영화 vs 드라마 결말 비교 (핵심 가설: 드라마=클리프행어로 끝 높음) ===")
# 영화 곡선 로드
fc=json.load(open("experiments/exp_cb.json"))["genre_curves"]
for g in ["romance","melo","crime","thriller","action"]:
    fe=fc.get(g,[0]*20); de=gm.get(g)
    if de: print(f"  {g:9}: 영화 end={fe[19]:.2f}  vs  드라마 end={de[19]:.2f}")
print("\n=== 드라마 DRSE 잔향 누적(motif build) 장르별 ===")
for g,v in sorted(drse_build.items()):
    if len(v)>=5: print(f"  {g:9}: build={mean(v):.3f} (n={len(v)})")
json.dump({"drama_curves":gm},open("experiments/drama_curves.json","w"),ensure_ascii=False)
