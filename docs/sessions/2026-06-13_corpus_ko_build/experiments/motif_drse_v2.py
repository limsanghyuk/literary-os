# DRSE v3 — mecab 명사 모티프 사전 + 콜백 타이밍 지표
import os,glob,json,sys
from collections import Counter
from mecab import MeCab
m=MeCab()
sys.path.insert(0,"experiments")
try: from meta_gt_v2 import META2
except: META2={}
STOP=set("사람 남자 여자 엄마 아빠 순간 소리 화면 자막 모습 생각 마음 표정 얼굴 시선 시간 장면 우리 당신 그녀 이때 그때 지금 오늘 내일 여기 저기 자신 자기 정도 동안 모두 무슨 누구 이것 그것 말 일 것 수 때 안 앞 위 옆 속 곳 중 등 점 채 뿐 데 듯 만 더 좀 또 다 단 거 게 걸 줄 적 척".split())
SCN="scenes"
def nouns(t):
    try: return [w for w in m.nouns(t) if len(w)>=2 and w not in STOP]
    except: return []
wf={}
for sf in sorted(glob.glob(SCN+"/*.jsonl")):
    w=os.path.basename(sf)[:-6]
    scenes=[json.loads(L) for L in open(sf,errors='ignore')]
    n=len(scenes)
    if n<12: continue
    sct=[set(nouns(s["text"])) for s in scenes]
    df=Counter()
    for st in sct:
        for tk in st: df[tk]+=1
    motif={tk for tk,c in df.items() if 3<=c<n*0.5}
    seen=set(); traj=[]
    for st in sct:
        mk=st&motif
        traj.append(len(mk&seen)/len(mk) if mk else 0.0)
        seen|=mk
    def seg(a,lo,hi): 
        s=a[int(len(a)*lo):int(len(a)*hi)]; return sum(s)/len(s) if s else 0
    recurrence=sum(traj)/len(traj)
    mid=seg(traj,0.4,0.6); last=seg(traj,0.8,1.0)
    climax_payoff=last-mid                      # 후반 콜백 집중(페이오프 타이밍)
    # build corr
    mp=(n-1)/2; ma=sum(traj)/n
    na=sum((x-ma)**2 for x in traj)**.5; nb=sum((i-mp)**2 for i in range(n))**.5
    build=sum((traj[i]-ma)*(i-mp) for i in range(n))/(na*nb) if na*nb else 0
    wf[w]=dict(recurrence=recurrence,build=build,climax_payoff=climax_payoff,richness=len(motif)/n,n_motif=len(motif))
# trajectory summary
bs=[wf[w]["build"] for w in wf]
print(f"=== DRSE v3 (mecab 명사 사전) ===")
print(f"  잔향 위치상관 평균={sum(bs)/len(bs):.3f} (정규식판 0.761)")
print(f"  climax_payoff>0 작품={sum(1 for w in wf if wf[w]['climax_payoff']>0)/len(wf):.0%}")
# acclaim correlation
mg=[w for w in wf if w in META2]
def z(d):
    v=list(d.values());mm=sum(v)/len(v);s=(sum((x-mm)**2 for x in v)/len(v))**.5 or 1
    return {k:(d[k]-mm)/s for k in d}
aud=z({w:META2[w][0] for w in mg}); exp=z({w:META2[w][1] for w in mg}); acc={w:aud[w]+exp[w] for w in mg}
def tau(field):
    c=d=0
    for i in range(len(mg)):
        for j in range(i+1,len(mg)):
            a,b=mg[i],mg[j];xa,xb=wf[a][field],wf[b][field];ya,yb=acc[a],acc[b]
            if xa==xb or ya==yb:continue
            c+=((xa-xb)*(ya-yb)>0);d+=((xa-xb)*(ya-yb)<0)
    return round((c-d)/(c+d),3)
print(f"\n  명성상관(n={len(mg)}):")
for f in ["recurrence","richness","climax_payoff","build"]:
    print(f"     drse_{f:14}: tau={tau(f)}")
json.dump(wf,open("experiments/drse_v3_feats.json","w"),ensure_ascii=False)
