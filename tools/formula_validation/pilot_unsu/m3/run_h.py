# -*- coding: utf-8 -*-
"""실험 H (사전등록): 비교 주석 → Δfitness 판정 >=9/11. 절제: 가중 vs 무가중 vs conflict 단독."""
import json,os,random,urllib.request,math,sys
sys.path.insert(0,"/tmp/hub")
from literary_system.physics.fitness_score import NarrativeFitnessComponents, NarrativeFitnessScore
from literary_system.physics.coefficient_store import PhysicsCoefficientStore
KEY=os.environ["OPENAI_API_KEY"]; D="/tmp/m3/"
def chat(msgs,mt=450):
    b=json.dumps({"model":"gpt-4o","temperature":0.0,"max_tokens":mt,"messages":msgs}).encode()
    r=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=b,headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=120) as x: return json.load(x)["choices"][0]["message"]["content"]
SC=[s.strip() for s in open(D+"unsu.txt",encoding="utf-8").read().split("###SCENE###")]
deg=json.load(open(D+"deg.json")); N=11
KEYS=["conflict_intensity","scene_energy_ratio","motif_residue_score","curiosity_gradient","reader_surface_score","arc_tension_score"]
RUB='두 장면 A·B를 비교하여 각각 6개 지표를 0.0~1.0로 평가하라. 차이가 느껴지면 점수에 반드시 차이를 내라. JSON만: {"A":{"conflict_intensity":..,"scene_energy_ratio":..,"motif_residue_score":..,"curiosity_gradient":..,"reader_surface_score":..,"arc_tension_score":..},"B":{...}}'
ca=json.load(open(D+"cmpann.json")) if os.path.exists(D+"cmpann.json") else {}
random.seed(13); order=[random.random()<0.5 for _ in range(N)]
for i in range(N):
    k=str(i)
    if k in ca: continue
    a,b=(SC[i],deg[i]) if order[i] else (deg[i],SC[i])
    o=chat([{"role":"system","content":"당신은 서사 분석가다. JSON만 출력."},{"role":"user","content":RUB+"\n\n[A]\n"+a+"\n\n[B]\n"+b}])
    j=json.loads(o[o.find("{"):o.rfind("}")+1])
    orig,degr=(j["A"],j["B"]) if order[i] else (j["B"],j["A"])
    ca[k]={"orig":orig,"deg":degr}; json.dump(ca,open(D+"cmpann.json","w")); print(f"cmp {i+1}/{N}",flush=True)
fit=NarrativeFitnessScore(PhysicsCoefficientStore())
def F(j): return fit.calculate(NarrativeFitnessComponents(**{k:float(j[k]) for k in KEYS}))
wF=wM=wC=0
for i in range(N):
    o,d=ca[str(i)]["orig"],ca[str(i)]["deg"]
    fo,fd=F(o),F(d); mo,md=sum(float(o[k]) for k in KEYS)/6,sum(float(d[k]) for k in KEYS)/6
    wF+=fo>fd; wM+=mo>md; wC+=float(o["conflict_intensity"])>float(d["conflict_intensity"])
    print(f"s{i+1:2d} fit {fo:.2f}/{fd:.2f} {'W' if fo>fd else ('T' if fo==fd else 'L')}")
def p(w): return sum(math.comb(N,k) for k in range(w,N+1))/2**N
print(f"\n=== H: 가중fitness {wF}/11 (임계9) p={p(wF):.4f} {'PASS' if wF>=9 else 'FAIL'} | 절제: 무가중 {wM}/11, conflict단독 {wC}/11 ===")
json.dump({"wF":wF,"wM":wM,"wC":wC},open(D+"h_final.json","w"))
