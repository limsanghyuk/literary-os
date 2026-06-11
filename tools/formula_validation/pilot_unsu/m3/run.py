# -*- coding: utf-8 -*-
"""후속 실측 A~E — 사전등록 (실행 전 고정)
A 주석기 상향 분리: gpt-4o 주석 → fitness 원본>열화 >=8/11. PASS=공식 무죄(측정계 문제) FAIL=fitness 재보정 후보
B 패널 sanity: 3페르소나(평론가·문장가·일반독자, 블라인드) 문학성 중앙값, 원본>열화 >=9/11. FAIL=패널 무효
C 공식↔문학성 정합: Spearman(fitness_4o, 패널중앙값) >=0.40 (22씬)
D 생성 위치(관찰): gpt-4o-mini 생성 3씬을 동일 블라인드 풀에 — 패널 기대 순서 명작>생성>열화, 공식이 같은 순서 재현?
E 임베딩 tension: emb 기반 긴장(갈등anchor sim - 평온anchor sim)이 원본>열화 >=8/11 (LF 키워드 tension 대체 근거)
"""
import sys,json,os,math,random,urllib.request
sys.path.insert(0,"/tmp/hub")
from literary_system.physics.fitness_score import NarrativeFitnessComponents, NarrativeFitnessScore
from literary_system.physics.coefficient_store import PhysicsCoefficientStore
KEY=os.environ["OPENAI_API_KEY"]; D="/tmp/m3/"
def chat(msgs,model="gpt-4o-mini",temp=0.0,mt=900):
    b=json.dumps({"model":model,"temperature":temp,"max_tokens":mt,"messages":msgs}).encode()
    r=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=b,headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=120) as x: return json.load(x)["choices"][0]["message"]["content"]
def embed(ts):
    b=json.dumps({"model":"text-embedding-3-small","input":ts}).encode()
    r=urllib.request.Request("https://api.openai.com/v1/embeddings",data=b,headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=120) as x: return [d["embedding"] for d in json.load(x)["data"]]
def ck(name,default): 
    p=D+name; return json.load(open(p)) if os.path.exists(p) else default
def sv(name,obj): json.dump(obj,open(D+name,"w"))
SC=[s.strip() for s in open(D+"unsu.txt",encoding="utf-8").read().split("###SCENE###")]; N=11
print("[사전등록 OK] A>=8/11 B>=9/11 C rho>=0.40 D 관찰 E>=8/11",flush=True)

# 0) 열화 재생성 (강화판 프롬프트, 세션 리셋으로 재생성 — 동일 프로토콜)
deg=ck("deg.json",[])
for i in range(len(deg),N):
    s=SC[i]
    o=chat([{"role":"system","content":"당신은 텍스트 편집기다."},{"role":"user","content":f"다음 장면을 같은 사건·인물 순서 그대로, 약 {len(s)}자 분량으로 다시 써라. 규칙: ①대사를 직접 인용(따옴표)으로 쓰지 말고 전부 무미건조한 간접 서술로 ②감정 묘사·아이러니·상징의 정서 비중 제거 ③감각 디테일을 일반 명사로 ④사건은 빠짐없이 유지.\n\n"+s}],temp=0.3,mt=1400)
    deg.append(o.strip()); sv("deg.json",deg); print(f"deg {i+1}/{N}",flush=True)

# 0b) 생성 3씬 (D용): 씬5·8·11 조건으로 mini가 새로 씀
GENC=[(4,"비 오는 1920년대 경성. 인력거꾼 김 첨지가 학생 손님을 태우고 정거장으로 달리는데, 아픈 아내 생각에 다리가 무거워졌다 가벼워졌다 한다."),
 (7,"선술집. 갑자기 돈을 많이 번 김 첨지가 취해서 호기를 부리다가 돈을 집어던지며 운다."),
 (10,"김 첨지가 설렁탕을 사 들고 집에 돌아왔으나 집 안이 이상하게 조용하다. 아내에게 호통치며 들어가지만.")]
gen=ck("gen.json",[])
for k in range(len(gen),3):
    i,brief=GENC[k]
    o=chat([{"role":"system","content":"당신은 소설가다. 1920년대 경성 배경 한국 단편소설 문체로 쓴다."},{"role":"user","content":f"다음 상황으로 약 {len(SC[i])}자 분량의 소설 장면을 써라. 지문과 대사를 포함하라.\n상황: {brief}"}],temp=0.8,mt=1400)
    gen.append(o.strip()); sv("gen.json",gen); print(f"gen {k+1}/3",flush=True)

# A) gpt-4o 주석 → fitness (25항목: A11+B11+G3, 블라인드 셔플)
RUB="""다음 장면 하나를 읽고 6개 지표를 0.0~1.0로 평가하라. 0.5를 보통 수준으로 삼고 스펙트럼 전체를 써라. JSON만 출력.
{"conflict_intensity":갈등 강도,"scene_energy_ratio":장면 에너지 밀도,"motif_residue_score":모티프/상징 잔향,"curiosity_gradient":다음 궁금증,"reader_surface_score":문장 표면 품질,"arc_tension_score":서사 긴장 기여}"""
items=[("A",i,SC[i]) for i in range(N)]+[("B",i,deg[i]) for i in range(N)]+[("G",k,gen[k]) for k in range(3)]
random.seed(11); random.shuffle(items)
ann=ck("ann4o.json",{})
for k,(c,i,t) in enumerate(items):
    key=f"{c}{i}"
    if key in ann: continue
    o=chat([{"role":"system","content":"당신은 서사 분석가다. JSON만 출력."},{"role":"user","content":RUB+"\n\n[장면]\n"+t}],model="gpt-4o",temp=0.0,mt=200)
    ann[key]=json.loads(o[o.find("{"):o.rfind("}")+1]); sv("ann4o.json",ann); print(f"annA {k+1}/{len(items)}",flush=True)

# B) 문학성 패널 3페르소나 (mini, 블라인드 동일 풀)
PERS={"critic":"당신은 엄격한 문학평론가다. 주제의 깊이·아이러니·구조를 본다.","stylist":"당신은 문장가다. 리듬·이미지·디테일의 질을 본다.","reader":"당신은 일반 독자다. 몰입과 감동을 본다."}
pan=ck("panel.json",{})
for k,(c,i,t) in enumerate(items):
    key=f"{c}{i}"
    if key in pan and len(pan[key])==3: continue
    pan.setdefault(key,{})
    for pid,sysm in PERS.items():
        if pid in pan[key]: continue
        o=chat([{"role":"system","content":sysm+" JSON만 출력."},{"role":"user","content":"다음 장면의 문학성을 0.0~10.0로 평가하라. 5.0=평범한 습작. JSON: {\"literariness\": 점수}\n\n[장면]\n"+t}],temp=0.0,mt=60)
        pan[key][pid]=json.loads(o[o.find("{"):o.rfind("}")+1])["literariness"]; sv("panel.json",pan)
    print(f"panel {k+1}/{len(items)}",flush=True)

# E) 임베딩 tension
emb=ck("emb.json",None)
if emb is None:
    anchors=["서로의 목적이 충돌하고 긴장이 고조되어 파국을 예감하게 하는 장면","아무 갈등 없이 평온하고 단조롭게 일상이 흘러가는 장면"]
    vecs=embed([SC[i] for i in range(N)]+[deg[i] for i in range(N)]+anchors)
    emb={"A":vecs[:N],"B":vecs[N:2*N],"anc":vecs[2*N:]}; sv("emb.json",emb); print("emb done",flush=True)

# ===== 분석 =====
def cos(a,b):
    n=sum(x*y for x,y in zip(a,b)); return n/(math.sqrt(sum(x*x for x in a))*math.sqrt(sum(y*y for y in b)))
fit=NarrativeFitnessScore(PhysicsCoefficientStore())
def F(j): return fit.calculate(NarrativeFitnessComponents(**{k:float(j[k]) for k in ["conflict_intensity","scene_energy_ratio","motif_residue_score","curiosity_gradient","reader_surface_score","arc_tension_score"]}))
def med(d): v=sorted(d.values()); return v[1]
def spear(a,b):
    n=len(a)
    def rk(x):
        idx=sorted(range(n),key=lambda i:x[i]); r=[0]*n
        for p,i in enumerate(idx): r[i]=p+1
        return r
    ra,rb=rk(a),rk(b); ma=sum(ra)/n; mb=sum(rb)/n
    num=sum((ra[i]-ma)*(rb[i]-mb) for i in range(n))
    den=math.sqrt(sum((x-ma)**2 for x in ra)*sum((x-mb)**2 for x in rb))
    return num/den if den else 0
fa=[F(ann[f"A{i}"]) for i in range(N)]; fb=[F(ann[f"B{i}"]) for i in range(N)]; fg=[F(ann[f"G{k}"]) for k in range(3)]
pa=[med(pan[f"A{i}"]) for i in range(N)]; pb=[med(pan[f"B{i}"]) for i in range(N)]; pg=[med(pan[f"G{k}"]) for k in range(3)]
wA=sum(1 for i in range(N) if fa[i]>fb[i]); wB=sum(1 for i in range(N) if pa[i]>pb[i])
tA=[cos(emb["A"][i],emb["anc"][0])-cos(emb["A"][i],emb["anc"][1]) for i in range(N)]
tB=[cos(emb["B"][i],emb["anc"][0])-cos(emb["B"][i],emb["anc"][1]) for i in range(N)]
wE=sum(1 for i in range(N) if tA[i]>tB[i])
rho=spear(fa+fb,pa+pb)
def p_sign(w,n): return sum(math.comb(n,k) for k in range(w,n+1))/2**n
print("\n===== 결과 =====")
for i in range(N): print(f"s{i+1:2d} fit {fa[i]:.2f}/{fb[i]:.2f} {'W' if fa[i]>fb[i] else ' '} | 패널 {pa[i]:.1f}/{pb[i]:.1f} | embT {tA[i]:+.3f}/{tB[i]:+.3f}")
print(f"A 주석기상향: {wA}/11 (임계8) p={p_sign(wA,11):.3f} {'PASS' if wA>=8 else 'FAIL'}")
print(f"B 패널sanity: {wB}/11 (임계9) {'PASS' if wB>=9 else 'FAIL'}")
print(f"C 공식↔문학성: rho={rho:+.3f} (임계0.40) {'PASS' if rho>=0.4 else 'FAIL'}")
print(f"D 생성위치: 패널 명작{sum(pa)/N:.2f} 생성{sum(pg)/3:.2f} 열화{sum(pb)/N:.2f} | 공식 {sum(fa)/N:.2f}/{sum(fg)/3:.2f}/{sum(fb)/N:.2f}")
print(f"E embTension: {wE}/11 (임계8) {'PASS' if wE>=8 else 'FAIL'}")
sv("final.json",{"fa":fa,"fb":fb,"fg":fg,"pa":pa,"pb":pb,"pg":pg,"tA":tA,"tB":tB,"wA":wA,"wB":wB,"wE":wE,"rho":rho})
