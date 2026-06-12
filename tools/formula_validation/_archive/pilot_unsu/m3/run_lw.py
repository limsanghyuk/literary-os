# -*- coding: utf-8 -*-
"""장편(1편) 실측 LW-1~4 — 사전등록 (실행 전 고정)
대상: 60분 드라마 1편의 압축 프록시 = 6씬 미니 에피소드(기-승-전-결+복선 회수), 새 전제.
LW-1 거시(원작): 운수 좋은 날 11씬 원순서 인접 임베딩 일관성이 셔플 100회 분포의 >=90퍼센타일.
LW-2 기능 적용 생성 대조: arm S(StyleDNA literary 컴파일 지시 + KoreanAntiLLMFilter 후처리 + plant→payoff 설계) vs arm P(플레인 생성).
  (a) 덜 AI스러움(인간 작가 같음) 쌍대: S 승 >=4/6  (b) 문학성 쌍대: S 승 >=4/6  (c) 클리셰 점수(코드): S평균 < P평균.
LW-3 거시 복선: arm S에서 plant(s1)→payoff(s6) 임베딩 공명이 s6 대비 전 씬 중 rank<=2. (P는 관찰)
LW-4 공식 정합: 비교주석→Δfitness(H 방식)로 S vs P — S 승 >=4/6.
"""
import sys,json,os,math,random,urllib.request
sys.path.insert(0,"/tmp/hub")
from literary_system.prose.anti_llm_filter import KoreanAntiLLMFilter
from literary_system.style.style_dna_engine import StyleDNAEngine
from literary_system.physics.fitness_score import NarrativeFitnessComponents, NarrativeFitnessScore
from literary_system.physics.coefficient_store import PhysicsCoefficientStore
KEY=os.environ["OPENAI_API_KEY"]; D="/tmp/m3/"
def chat(msgs,model="gpt-4o-mini",temp=0.0,mt=1100):
    b=json.dumps({"model":model,"temperature":temp,"max_tokens":mt,"messages":msgs}).encode()
    r=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=b,headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=120) as x: return json.load(x)["choices"][0]["message"]["content"]
def embed(ts):
    b=json.dumps({"model":"text-embedding-3-small","input":ts}).encode()
    r=urllib.request.Request("https://api.openai.com/v1/embeddings",data=b,headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=120) as x: return [d["embedding"] for d in json.load(x)["data"]]
def cos(a,b):
    n=sum(x*y for x,y in zip(a,b)); return n/(math.sqrt(sum(x*x for x in a))*math.sqrt(sum(y*y for y in b)))
print("[사전등록 OK] LW-1 pct>=90 | LW-2a/b S>=4/6, 2c S<P | LW-3 rank<=2 | LW-4 S>=4/6",flush=True)

# LW-1 (기존 원작 임베딩 재사용, LLM-free)
emb=json.load(open(D+"emb.json"))["A"]; N=len(emb)
def adj(orderv): return sum(cos(emb[orderv[i]],emb[orderv[i+1]]) for i in range(N-1))/(N-1)
orig=adj(list(range(N)))
random.seed(99); shf=[]
for _ in range(100):
    o=list(range(N)); random.shuffle(o); shf.append(adj(o))
pct=sum(1 for x in shf if x<orig)/len(shf)*100
print(f"LW-1: 원순서 인접일관성 {orig:.4f} | 셔플 퍼센타일 {pct:.0f} | {'PASS' if pct>=90 else 'FAIL'}",flush=True)

# 에피소드 전제 (새 작품 — 6씬 60분 압축 프록시)
PREM="1970년대 부산 자갈치시장. 평생 생선 좌판을 지킨 어머니 '순임'과 서울에서 실패하고 돌아온 아들 '동수'. 어머니는 병을 숨기고, 아들은 빚을 숨긴다. 모티프: 어머니가 매일 닦는 낡은 놋숟가락(plant: 씬1, payoff: 씬6 — 아들이 그 숟가락의 의미를 뒤늦게 안다)."
BEATS=["씬1(기): 새벽 좌판. 일상 속에 놋숟가락 모티프를 자연스럽게 심는다.","씬2(승): 아들의 귀향. 모자의 어긋난 대화.","씬3(승): 빚쟁이의 방문. 아들의 거짓말.","씬4(전): 어머니의 병이 드러나는 순간.","씬5(전): 모자의 충돌과 진실의 폭로.","씬6(결): 놋숟가락의 의미가 회수되는 결말. 선언하지 말고 여운으로."]
eng=StyleDNAEngine(); prof=eng.compile("literary"); flt=KoreanAntiLLMFilter()
SDIR=f"문체 지침(엄수): 시점 안정, 짧고 중간 길이 문장 혼합(cadence), 은유 최소, 대사 압축(군더더기 금지), 감정은 선언하지 말고 행동·감각(촉각 우선)으로, 결말은 여운형. 금지어: {', '.join(prof['forbidden'])}. AI 상투구(예: 복잡한 감정이 밀려왔다, 심장이 두근거렸다, 침묵이 흘렀다) 금지."
ep=json.load(open(D+"lw_ep.json")) if os.path.exists(D+"lw_ep.json") else {"S":[],"P":[]}
for k in range(len(ep["S"]),6):
    o=chat([{"role":"system","content":"당신은 한국 드라마 작가다."},{"role":"user","content":f"{PREM}\n\n{BEATS[k]}\n\n{SDIR}\n\n위 지침으로 약 600자 장면을 써라. 지문과 대사 포함."}],temp=0.8)
    res=flt.filter(o.strip())
    ep["S"].append(res.filtered); json.dump(ep,open(D+"lw_ep.json","w")); print(f"S {k+1}/6 (클리셰교체 {res.n_cliches})",flush=True)
for k in range(len(ep["P"]),6):
    o=chat([{"role":"system","content":"당신은 한국 드라마 작가다."},{"role":"user","content":f"{PREM}\n\n{BEATS[k]}\n\n약 600자 장면을 써라. 지문과 대사 포함."}],temp=0.8)
    ep["P"].append(o.strip()); json.dump(ep,open(D+"lw_ep.json","w")); print(f"P {k+1}/6",flush=True)

# LW-2c 클리셰 점수 (코드 측정 — score_only는 잔존 클리셰 밀도)
cS=[flt.score_only(t) for t in ep["S"]]; cP=[flt.score_only(t) for t in ep["P"]]
print(f"LW-2c: 클리셰밀도 S평균 {sum(cS)/6:.3f} vs P평균 {sum(cP)/6:.3f} | {'PASS' if sum(cS)<sum(cP) else 'FAIL'}",flush=True)

# LW-2a/b 쌍대 (gpt-4o, 두 질문 1콜)
jd=json.load(open(D+"lw_judge.json")) if os.path.exists(D+"lw_judge.json") else {}
random.seed(21); pos=[random.random()<0.5 for _ in range(6)]
for k in range(6):
    kk=str(k)
    if kk in jd: continue
    a,b=(ep["S"][k],ep["P"][k]) if pos[k] else (ep["P"][k],ep["S"][k])
    o=chat([{"role":"system","content":"당신은 문학 심사위원이다. JSON만 출력."},{"role":"user","content":'같은 장면의 두 버전이다. 두 질문에 답하라. 무승부 금지. JSON: {"human_like":"A"|"B","literary":"A"|"B"} (human_like=어느 쪽이 AI가 아니라 인간 작가가 쓴 것 같은가, literary=어느 쪽이 문학적으로 우수한가)\n\n[A]\n'+a+'\n\n[B]\n'+b}],model="gpt-4o",mt=60)
    j=json.loads(o[o.find("{"):o.rfind("}")+1])
    jd[kk]={"hl_S":(j["human_like"]=="A")==pos[k],"lit_S":(j["literary"]=="A")==pos[k]}
    json.dump(jd,open(D+"lw_judge.json","w")); print(f"judge {k+1}/6",flush=True)
wHL=sum(1 for v in jd.values() if v["hl_S"]); wLIT=sum(1 for v in jd.values() if v["lit_S"])
print(f"LW-2a 덜AI스러움: S {wHL}/6 {'PASS' if wHL>=4 else 'FAIL'} | LW-2b 문학성: S {wLIT}/6 {'PASS' if wLIT>=4 else 'FAIL'}",flush=True)

# LW-3 복선 회수 (arm S, 임베딩)
if not os.path.exists(D+"lw_emb.json"):
    ve=embed(ep["S"]+ep["P"]); json.dump(ve,open(D+"lw_emb.json","w"))
ve=json.load(open(D+"lw_emb.json")); eS,eP=ve[:6],ve[6:]
def rank_plant(e6):
    sims=sorted(((cos(e6[i],e6[5]),i+1) for i in range(5)),reverse=True)
    return {sc:r+1 for r,(s,sc) in enumerate(sims)},sims
rS,simS=rank_plant(eS); rP,_=rank_plant(eP)
print(f"LW-3: armS plant(s1) rank {rS[1]}/5 {'PASS' if rS[1]<=2 else 'FAIL'} (관찰: armP rank {rP[1]}) | simS={[(c,round(s,3)) for s,c in simS]}",flush=True)

# LW-4 비교주석→Δfitness (H 방식, S vs P)
RUB='두 장면 A·B를 비교하여 각각 6개 지표를 0.0~1.0로 평가하라. 차이가 느껴지면 점수에 차이를 내라. JSON만: {"A":{"conflict_intensity":..,"scene_energy_ratio":..,"motif_residue_score":..,"curiosity_gradient":..,"reader_surface_score":..,"arc_tension_score":..},"B":{...}}'
KEYS=["conflict_intensity","scene_energy_ratio","motif_residue_score","curiosity_gradient","reader_surface_score","arc_tension_score"]
fit=NarrativeFitnessScore(PhysicsCoefficientStore())
def F(j): return fit.calculate(NarrativeFitnessComponents(**{k:float(j[k]) for k in KEYS}))
cm=json.load(open(D+"lw_cmp.json")) if os.path.exists(D+"lw_cmp.json") else {}
random.seed(31); pos2=[random.random()<0.5 for _ in range(6)]
for k in range(6):
    kk=str(k)
    if kk in cm: continue
    a,b=(ep["S"][k],ep["P"][k]) if pos2[k] else (ep["P"][k],ep["S"][k])
    o=chat([{"role":"system","content":"당신은 서사 분석가다. JSON만 출력."},{"role":"user","content":RUB+"\n\n[A]\n"+a+"\n\n[B]\n"+b}],model="gpt-4o",mt=450)
    j=json.loads(o[o.find("{"):o.rfind("}")+1])
    s,pp=(j["A"],j["B"]) if pos2[k] else (j["B"],j["A"])
    cm[kk]={"S":s,"P":pp}; json.dump(cm,open(D+"lw_cmp.json","w")); print(f"cmp {k+1}/6",flush=True)
wF=sum(1 for k in range(6) if F(cm[str(k)]["S"])>F(cm[str(k)]["P"]))
print(f"LW-4 Δfitness: S {wF}/6 {'PASS' if wF>=4 else 'FAIL'}",flush=True)
json.dump({"lw1_pct":pct,"cS":cS,"cP":cP,"wHL":wHL,"wLIT":wLIT,"rankS":rS[1],"rankP":rP[1],"wF":wF},open(D+"lw_final.json","w"))
print("ALL-DONE")
