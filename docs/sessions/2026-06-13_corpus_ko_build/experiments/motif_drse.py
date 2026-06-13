# DRSE v2 — 재등장 모티프 사전 기반 잔향(임베딩유사 폐기)
import os,glob,json,re,sqlite3
from collections import Counter,defaultdict
ROOT="."; SCN="scenes"
STOP=set("그리고 그러나 그래서 하지만 그때 이때 다시 사람 남자 여자 엄마 아빠 순간 갑자기 조용 모두 우리 당신 자막 소리 화면 목소리 그녀 그들 자신 자기 마치 약간 정도 무슨 어디 누구 이것 그것 저것 여기 저기 지금 오늘 내일 그냥 진짜 정말 도대체 이렇게 그렇게 어떻게 우리들 너희 인서트 컷 시간 장면 표정 얼굴 시선 모습 생각 마음 이제 아주 너무 조금 가득 향해 동안 앞에 위로 아래 안에 밖에 사이 서로".split())
TOK=re.compile(r'[가-힣]{2,4}')
def tokens(t): return [w for w in TOK.findall(t) if w not in STOP]
con=sqlite3.connect("/sessions/upbeat-focused-bohr/scene_features.db");cur=con.cursor()
import sys; sys.path.insert(0,"experiments")
try: from meta_gt_v2 import META2
except: META2={}
W=json.load(open("experiments/work_features.json")); RF=json.load(open("experiments/redefine_feats.json"))
res_build=[]; workfeat={}
for sf in sorted(glob.glob(SCN+"/*.jsonl")):
    w=os.path.basename(sf)[:-6]
    scenes=[json.loads(L) for L in open(sf,errors='ignore')]
    n=len(scenes)
    if n<12: continue
    sc_tokens=[set(tokens(s["text"])) for s in scenes]
    df=Counter()
    for st in sc_tokens:
        for tk in st: df[tk]+=1
    # motif dict: appears in >=3 scenes and < 50% of scenes
    motif={tk for tk,c in df.items() if c>=3 and c< n*0.5}
    # residue trajectory: fraction of scene's motif tokens already established earlier
    seen=set(); traj=[]
    for k,st in enumerate(sc_tokens):
        mk=st & motif
        if mk:
            est=mk & seen
            traj.append(len(est)/len(mk))
        else: traj.append(0.0)
        seen|=mk
    # callback build = corr(traj, position)
    def corr(a):
        m=len(a); 
        if m<3: return 0
        mp=(m-1)/2; ma=sum(a)/m
        na=sum((x-ma)**2 for x in a)**.5; nb=sum((i-mp)**2 for i in range(m))**.5
        return sum((a[i]-ma)*(i-mp) for i in range(m))/(na*nb) if na*nb else 0
    cb=corr(traj)
    recurrence=sum(traj)/len(traj)
    richness=len(motif)/n
    res_build.append((w,cb))
    workfeat[w]=dict(drse_recurrence=recurrence,drse_richness=richness,drse_build=cb,n=n,n_motif=len(motif))
# trajectory result
cb=[v for _,v in res_build]
print("=== DRSE v2 모티프-사전 잔향 ===")
print(f"  motif_residue vs 위치 corr 평균={sum(cb)/len(cb):.3f} (이전 임베딩기반 0.009)")
print(f"  후반 잔향 누적 작품 비율={sum(1 for x in cb if x>0)/len(cb):.1%}")
top=sorted(res_build,key=lambda x:-x[1])[:6]
print("  최고 콜백누적:",[(w,round(v,2)) for w,v in top])
# acclaim correlation (vs v2 GT combined)
mg=[w for w in workfeat if w in META2]
if mg:
    def z(d):
        v=list(d.values());m=sum(v)/len(v);s=(sum((x-m)**2 for x in v)/len(v))**.5 or 1
        return {k:(d[k]-m)/s for k in d}
    aud=z({w:META2[w][0] for w in mg}); exp=z({w:META2[w][1] for w in mg})
    acc={w:aud[w]+exp[w] for w in mg}
    def tau(field):
        c=d=0
        for i in range(len(mg)):
            for j in range(i+1,len(mg)):
                a,b=mg[i],mg[j];xa,xb=workfeat[a][field],workfeat[b][field];ya,yb=acc[a],acc[b]
                if xa==xb or ya==yb:continue
                c+=((xa-xb)*(ya-yb)>0);d+=((xa-xb)*(ya-yb)<0)
        return round((c-d)/(c+d),3)
    print(f"\n  명성상관(vs 관객+전문가, n={len(mg)}): drse_recurrence tau={tau('drse_recurrence')}  drse_richness tau={tau('drse_richness')}  (이전 callback tau -0.05)")
json.dump(workfeat,open("experiments/drse_v2_feats.json","w"),ensure_ascii=False)
