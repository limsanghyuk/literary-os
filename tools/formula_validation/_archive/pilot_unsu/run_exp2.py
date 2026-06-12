# -*- coding: utf-8 -*-
"""실험 2 (탐색적 후속 — 실험 1의 사전등록 변경 아님, 별도 사전등록)
가설: 실험 1 H1 실패는 조작 약화(열화문이 원 대사를 그대로 보존) 때문이다.
조작 강화: 대사 직접인용 금지(간접서술 전환)·상징의 정서 비중 제거. 임계 동일: 원본 우위 >=8/11.
A군 주석은 실험 1 것을 재사용(동일 루브릭·동일 모델·temp0).
"""
import sys, json, os, math, urllib.request, random
sys.path.insert(0, "/tmp/hub")
from literary_system.physics.fitness_score import NarrativeFitnessComponents, NarrativeFitnessScore
from literary_system.physics.coefficient_store import PhysicsCoefficientStore
KEY=os.environ["OPENAI_API_KEY"]
def chat(messages, temp=0.0, max_tok=1400):
    body=json.dumps({"model":"gpt-4o-mini","temperature":temp,"max_tokens":max_tok,"messages":messages}).encode()
    req=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=body,
        headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=120) as r: return json.load(r)["choices"][0]["message"]["content"]
scenes=[s.strip() for s in open("/tmp/mode2/unsu.txt",encoding="utf-8").read().split("###SCENE###")]
N=len(scenes)
print(f"[실험2 사전등록] 강화 열화 vs 원본, 임계 >=8/{N}", flush=True)
CK="/tmp/mode2/degraded2.json"
deg=json.load(open(CK)) if os.path.exists(CK) else []
for i in range(len(deg),N):
    s=scenes[i]
    out=chat([{"role":"system","content":"당신은 텍스트 편집기다. 지시만 수행한다."},
      {"role":"user","content":f"다음 장면을 같은 사건·인물 순서 그대로, 약 {len(s)}자 분량으로 다시 써라. 규칙: ①대사를 직접 인용(따옴표)으로 쓰지 말고 전부 무미건조한 간접 서술로 바꿔라 ②감정 묘사·아이러니·상징의 정서적 비중을 제거하라 ③감각적 디테일을 일반 명사로 치환하라 ④사건 자체는 빠짐없이 유지하라.\n\n"+s}],temp=0.3)
    deg.append(out.strip()); json.dump(deg,open(CK,"w")); print(f"  deg2 {i+1}/{N} ({len(out)}c)",flush=True)
CK2="/tmp/mode2/ann2.json"
ann2=json.load(open(CK2)) if os.path.exists(CK2) else {}
RUBRIC="""다음 장면 하나를 읽고 6개 지표를 0.0~1.0로 평가하라. JSON만 출력.
{"conflict_intensity": 갈등의 강도, "scene_energy_ratio": 장면의 에너지 보존(처짐 없이 밀도 유지), "motif_residue_score": 모티프/상징이 잔향을 남기는 정도, "curiosity_gradient": 다음이 궁금해지는 정도, "reader_surface_score": 문장 표면 품질(생동감·구체성), "arc_tension_score": 서사 긴장 기여도}"""
order=list(range(N)); random.seed(7); random.shuffle(order)
for k,i in enumerate(order):
    if str(i) in ann2: continue
    out=chat([{"role":"system","content":"당신은 서사 분석가다. JSON만 출력한다."},
      {"role":"user","content":RUBRIC+"\n\n[장면]\n"+deg[i]}],temp=0.0,max_tok=200)
    ann2[str(i)]=json.loads(out[out.find("{"):out.rfind("}")+1]); json.dump(ann2,open(CK2,"w"))
    print(f"  ann2 {k+1}/{N}",flush=True)
annA=json.load(open("/tmp/mode2/ann.json"))
fit=NarrativeFitnessScore(PhysicsCoefficientStore())
def F(j): return fit.calculate(NarrativeFitnessComponents(**{k:j[k] for k in ["conflict_intensity","scene_energy_ratio","motif_residue_score","curiosity_gradient","reader_surface_score","arc_tension_score"]}))
wins=0; rows=[]
for i in range(N):
    fa,fb=F(annA[f"A{i}"]),F(ann2[str(i)])
    wins+=fa>fb; rows.append((i+1,fa,fb))
    print(f"  s{i+1:2d}  원본 {fa:.2f}  강화열화 {fb:.2f}  Δ{fa-fb:+.2f}")
p=sum(math.comb(N,k) for k in range(wins,N+1))/2**N
print(f"\n=== 실험2 H1': 원본 우위 {wins}/{N} (임계 8) | p={p:.4f} | {'PASS' if wins>=8 else 'FAIL'} ===")
json.dump({"rows":rows,"wins":wins,"p":p},open("/tmp/mode2/results2.json","w"))
