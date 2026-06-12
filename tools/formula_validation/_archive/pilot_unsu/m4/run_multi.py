# -*- coding: utf-8 -*-
"""다작품 재현 (사전등록): 동백꽃(김유정 1936)·메밀꽃 필 무렵(이효석 1936) — 각 9씬, PD 확인.
F' 쌍대 강제선택(원본 vs 강화열화): 작품당 원본 승 >=8/9 (80% 상회).
H' 비교주석→가중 Δfitness: 작품당 >=8/9.
운수 좋은 날 결과(F 11/11·H 11/11)의 작품 간 일반화 검증."""
import sys,json,os,math,random,urllib.request
sys.path.insert(0,"/tmp/hub")
from literary_system.physics.fitness_score import NarrativeFitnessComponents, NarrativeFitnessScore
from literary_system.physics.coefficient_store import PhysicsCoefficientStore
KEY=os.environ["OPENAI_API_KEY"]; D="/tmp/m4/"
def chat(msgs,model="gpt-4o-mini",temp=0.0,mt=1300):
    b=json.dumps({"model":model,"temperature":temp,"max_tokens":mt,"messages":msgs}).encode()
    r=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=b,headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=120) as x: return json.load(x)["choices"][0]["message"]["content"]
WORKS={"dongbaek":"dongbaek.txt","memil":"memil.txt"}
KEYS=["conflict_intensity","scene_energy_ratio","motif_residue_score","curiosity_gradient","reader_surface_score","arc_tension_score"]
fit=NarrativeFitnessScore(PhysicsCoefficientStore())
def F(j): return fit.calculate(NarrativeFitnessComponents(**{k:float(j[k]) for k in KEYS}))
print("[사전등록 OK] 작품당 F'>=8/9, H'>=8/9",flush=True)
summary={}
for wid,fn in WORKS.items():
    SC=[s.strip() for s in open(D+fn,encoding="utf-8").read().split("PARA")]; N=len(SC)
    # 열화 (강화 프로토콜 동일)
    dp=D+wid+"_deg.json"; deg=json.load(open(dp)) if os.path.exists(dp) else []
    for i in range(len(deg),N):
        s=SC[i]
        o=chat([{"role":"system","content":"당신은 텍스트 편집기다."},{"role":"user","content":f"다음 장면을 같은 사건·인물 순서 그대로, 약 {len(s)}자 분량으로 다시 써라. 규칙: ①대사를 직접 인용(따옴표)으로 쓰지 말고 전부 무미건조한 간접 서술로 ②감정 묘사·아이러니·상징의 정서 비중 제거 ③감각 디테일을 일반 명사로 ④사건은 빠짐없이 유지.\n\n"+s}],temp=0.3)
        deg.append(o.strip()); json.dump(deg,open(dp,"w")); print(f"{wid} deg {i+1}/{N}",flush=True)
    # F' 쌍대 선택
    fp=D+wid+"_fc.json"; fc=json.load(open(fp)) if os.path.exists(fp) else {}
    random.seed(hash(wid)%1000); order=[random.random()<0.5 for _ in range(N)]
    for i in range(N):
        k=str(i)
        if k in fc: continue
        a,b=(SC[i],deg[i]) if order[i] else (deg[i],SC[i])
        o=chat([{"role":"system","content":"당신은 문학 심사위원이다. JSON만 출력."},{"role":"user","content":'같은 사건을 다룬 두 글 중 문학적으로 우수한 쪽을 골라라. 무승부 금지. JSON: {"choice":"A"|"B"}\n\n[A]\n'+a+'\n\n[B]\n'+b}],model="gpt-4o",mt=30)
        j=json.loads(o[o.find("{"):o.rfind("}")+1])
        fc[k]=(j["choice"]=="A")==order[i]; json.dump(fc,open(fp,"w")); print(f"{wid} fc {i+1}/{N}",flush=True)
    # H' 비교주석→Δfitness
    cp=D+wid+"_cmp.json"; cm=json.load(open(cp)) if os.path.exists(cp) else {}
    random.seed(hash(wid)%997); o2=[random.random()<0.5 for _ in range(N)]
    RUB='두 장면 A·B를 비교하여 각각 6개 지표를 0.0~1.0로 평가하라. 차이가 느껴지면 점수에 차이를 내라. JSON만: {"A":{"conflict_intensity":..,"scene_energy_ratio":..,"motif_residue_score":..,"curiosity_gradient":..,"reader_surface_score":..,"arc_tension_score":..},"B":{...}}'
    for i in range(N):
        k=str(i)
        if k in cm: continue
        a,b=(SC[i],deg[i]) if o2[i] else (deg[i],SC[i])
        o=chat([{"role":"system","content":"당신은 서사 분석가다. JSON만 출력."},{"role":"user","content":RUB+"\n\n[A]\n"+a+"\n\n[B]\n"+b}],model="gpt-4o",mt=450)
        j=json.loads(o[o.find("{"):o.rfind("}")+1])
        s_,d_=(j["A"],j["B"]) if o2[i] else (j["B"],j["A"])
        cm[k]={"o":s_,"d":d_}; json.dump(cm,open(cp,"w")); print(f"{wid} cmp {i+1}/{N}",flush=True)
    wf=sum(1 for k in fc if fc[k]); wh=sum(1 for i in range(N) if F(cm[str(i)]["o"])>F(cm[str(i)]["d"]))
    def p(w,n): return sum(math.comb(n,k) for k in range(w,n+1))/2**n
    summary[wid]={"F":wf,"H":wh,"N":N,"pF":p(wf,N),"pH":p(wh,N)}
    print(f"== {wid}: F' {wf}/{N} (p={p(wf,N):.4f}) {'PASS' if wf>=8 else 'FAIL'} | H' {wh}/{N} (p={p(wh,N):.4f}) {'PASS' if wh>=8 else 'FAIL'}",flush=True)
json.dump(summary,open(D+"multi_final.json","w"))
print("ALL-DONE",summary)
