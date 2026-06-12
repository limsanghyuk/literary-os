# -*- coding: utf-8 -*-
"""SG 실측 (사전등록 — 실행 전 고정): 실제 드라마 대본(오징어게임 EP9 공식 영문 각본) 첫 검증.
대상: 400자 이상 20씬 (s1,2,3,7,9,11,15,19,20,22,24,26,27,29,30,31,32,33,34,36).
SG-1 쌍대 변별: 원본 vs 강화열화, gpt-4o 강제선택 — >=16/20 (80%).
SG-2 Δfitness: 비교주석→가중 fitness — >=16/20.
SG-3 복선(말 모티프): s19(프런트맨 '너희는 경마장의 말') → s36(기훈 'I'm not a horse')
     임베딩 유사도에서 s36 기준 35씬 중 s19 rank<=3.
SG-4 시퀀스: 36씬 원순서 인접 일관성 >= 셔플 100회의 90퍼센타일.
영문 텍스트이므로 문체 축 해석은 보류(구조·복선·긴장 축 한정)."""
import sys,json,os,math,random,urllib.request
sys.path.insert(0,"/tmp/hub")
from literary_system.physics.fitness_score import NarrativeFitnessComponents, NarrativeFitnessScore
from literary_system.physics.coefficient_store import PhysicsCoefficientStore
KEY=os.environ["OPENAI_API_KEY"]; D="/tmp/sg/"
def chat(msgs,model="gpt-4o-mini",temp=0.0,mt=1400):
    b=json.dumps({"model":model,"temperature":temp,"max_tokens":mt,"messages":msgs}).encode()
    r=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=b,headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=120) as x: return json.load(x)["choices"][0]["message"]["content"]
def embed(ts):
    out=[]
    for i in range(0,len(ts),16):
        b=json.dumps({"model":"text-embedding-3-small","input":ts[i:i+16]}).encode()
        r=urllib.request.Request("https://api.openai.com/v1/embeddings",data=b,headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"})
        with urllib.request.urlopen(r,timeout=120) as x: out+=[d["embedding"] for d in json.load(x)["data"]]
    return out
def cos(a,b):
    n=sum(x*y for x,y in zip(a,b)); return n/(math.sqrt(sum(x*x for x in a))*math.sqrt(sum(y*y for y in b)))
SC=json.load(open(D+"scenes.json")); ALL=SC["all"]; BIG=SC["big_idx"]; NB=len(BIG)
print(f"[사전등록 OK] SG-1>=16/{NB} SG-2>=16/{NB} SG-3 s19 rank<=3 SG-4 pct>=90",flush=True)

# 열화 (영문 — 동일 강화 프로토콜)
deg=json.load(open(D+"deg.json")) if os.path.exists(D+"deg.json") else {}
for si in BIG:
    k=str(si)
    if k in deg: continue
    s=ALL[si-1]
    o=chat([{"role":"system","content":"You are a text editor. Follow instructions only."},
      {"role":"user","content":f"Rewrite the following screenplay scene keeping the same events and characters in the same order, about {len(s)} characters. Rules: 1) Convert all quoted dialogue into flat indirect narration (no quotation marks). 2) Remove emotional description, irony, and the emotional weight of symbols. 3) Replace sensory details with generic nouns. 4) Keep every event; do not summarize.\n\n"+s}],temp=0.3)
    deg[k]=o.strip(); json.dump(deg,open(D+"deg.json","w")); print(f"deg s{si}",flush=True)

# SG-1 쌍대 선택
fc=json.load(open(D+"fc.json")) if os.path.exists(D+"fc.json") else {}
random.seed(456); order={str(si):random.random()<0.5 for si in BIG}
for si in BIG:
    k=str(si)
    if k in fc: continue
    a,b=(ALL[si-1],deg[k]) if order[k] else (deg[k],ALL[si-1])
    o=chat([{"role":"system","content":"You are a literary judge. Output JSON only."},
      {"role":"user","content":'Two versions of the same scene. Choose the one that is superior as dramatic writing. No ties. JSON: {"choice":"A"|"B"}\n\n[A]\n'+a+'\n\n[B]\n'+b}],model="gpt-4o",mt=30)
    j=json.loads(o[o.find("{"):o.rfind("}")+1])
    fc[k]=(j["choice"]=="A")==order[k]; json.dump(fc,open(D+"fc.json","w")); print(f"fc s{si}: {'W' if fc[k] else 'L'}",flush=True)

# SG-2 비교주석→Δfitness
KEYS=["conflict_intensity","scene_energy_ratio","motif_residue_score","curiosity_gradient","reader_surface_score","arc_tension_score"]
RUB='Compare scenes A and B. Rate each on 6 metrics 0.0-1.0. If you sense a difference, reflect it in the scores. JSON only: {"A":{"conflict_intensity":..,"scene_energy_ratio":..,"motif_residue_score":..,"curiosity_gradient":..,"reader_surface_score":..,"arc_tension_score":..},"B":{...}}'
cm=json.load(open(D+"cmp.json")) if os.path.exists(D+"cmp.json") else {}
random.seed(457); o2={str(si):random.random()<0.5 for si in BIG}
for si in BIG:
    k=str(si)
    if k in cm: continue
    a,b=(ALL[si-1],deg[k]) if o2[k] else (deg[k],ALL[si-1])
    o=chat([{"role":"system","content":"You are a narrative analyst. Output JSON only."},{"role":"user","content":RUB+"\n\n[A]\n"+a+"\n\n[B]\n"+b}],model="gpt-4o",mt=450)
    j=json.loads(o[o.find("{"):o.rfind("}")+1])
    s_,d_=(j["A"],j["B"]) if o2[k] else (j["B"],j["A"])
    cm[k]={"o":s_,"d":d_}; json.dump(cm,open(D+"cmp.json","w")); print(f"cmp s{si}",flush=True)
fit=NarrativeFitnessScore(PhysicsCoefficientStore())
def F(j): return fit.calculate(NarrativeFitnessComponents(**{k:float(j[k]) for k in KEYS}))
w1=sum(1 for k in fc if fc[k]); w2=sum(1 for k in cm if F(cm[k]["o"])>F(cm[k]["d"]))

# SG-3/4 임베딩
if not os.path.exists(D+"emb.json"):
    json.dump(embed(ALL),open(D+"emb.json","w")); print("emb done",flush=True)
E=json.load(open(D+"emb.json")); N=len(E)
sims=sorted(((cos(E[i],E[35]),i+1) for i in range(35)),reverse=True)
rank={sc:r+1 for r,(s,sc) in enumerate(sims)}
def adj(o): return sum(cos(E[o[i]],E[o[i+1]]) for i in range(N-1))/(N-1)
orig=adj(list(range(N))); random.seed(99)
shf=[]
for _ in range(100):
    o=list(range(N)); random.shuffle(o); shf.append(adj(o))
pct=sum(1 for x in shf if x<orig)
def p(w,n): return sum(math.comb(n,k) for k in range(w,n+1))/2**n
print(f"\n=== SG-1 쌍대: {w1}/{NB} (임계16) p={p(w1,NB):.5f} {'PASS' if w1>=16 else 'FAIL'}")
print(f"=== SG-2 Δfitness: {w2}/{NB} (임계16) p={p(w2,NB):.5f} {'PASS' if w2>=16 else 'FAIL'}")
print(f"=== SG-3 복선(말): s19 rank {rank.get(19)} (임계<=3) {'PASS' if rank.get(19,99)<=3 else 'FAIL'} | top5={[(sc,round(s,3)) for s,sc in sims[:5]]}")
print(f"=== SG-4 시퀀스: 원순서 {orig:.4f} pct={pct} (임계90) {'PASS' if pct>=90 else 'FAIL'}")
json.dump({"w1":w1,"w2":w2,"NB":NB,"rank19":rank.get(19),"pct":pct,"top5":[(sc,s) for s,sc in sims[:5]]},open(D+"final.json","w"))
print("ALL-DONE")
