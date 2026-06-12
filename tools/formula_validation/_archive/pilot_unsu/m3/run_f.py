# -*- coding: utf-8 -*-
"""실험 F (사전등록): 쌍대 강제선택. 같은 씬의 원본/열화를 블라인드 A/B로 제시(위치 무작위),
gpt-4o가 '더 문학적으로 우수한 쪽'을 강제 선택. 임계: 원본 승 >=8/11.
가설: 절대 채점(B실험 5/11 FAIL)의 둔감이 원인이면 비교 판단은 통과한다."""
import json,os,random,urllib.request,math
KEY=os.environ["OPENAI_API_KEY"]; D="/tmp/m3/"
def chat(msgs,model="gpt-4o",temp=0.0,mt=120):
    b=json.dumps({"model":model,"temperature":temp,"max_tokens":mt,"messages":msgs}).encode()
    r=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=b,headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=120) as x: return json.load(x)["choices"][0]["message"]["content"]
SC=[s.strip() for s in open(D+"unsu.txt",encoding="utf-8").read().split("###SCENE###")]
deg=json.load(open(D+"deg.json")); N=11
fc=json.load(open(D+"fc.json")) if os.path.exists(D+"fc.json") else {}
random.seed(3)
order=[random.random()<0.5 for _ in range(N)]  # True=원본이 A 위치
for i in range(N):
    k=str(i)
    if k in fc: continue
    a,b=(SC[i],deg[i]) if order[i] else (deg[i],SC[i])
    o=chat([{"role":"system","content":"당신은 문학 심사위원이다. JSON만 출력."},
      {"role":"user","content":'같은 사건을 다룬 두 글 중 문학적으로 우수한 쪽을 골라라. 무승부 금지. JSON: {"choice":"A"|"B","reason":"15자 이내"}\n\n[A]\n'+a+'\n\n[B]\n'+b}],mt=80)
    j=json.loads(o[o.find("{"):o.rfind("}")+1])
    win = (j["choice"]=="A")==order[i]
    fc[k]={"orig_win":win,"reason":j.get("reason","")}; json.dump(fc,open(D+"fc.json","w"))
    print(f"fc s{i+1}: {'원본W' if win else '열화W'} ({j.get('reason','')})",flush=True)
w=sum(1 for v in fc.values() if v["orig_win"])
p=sum(math.comb(N,k) for k in range(w,N+1))/2**N
print(f"\n=== F 쌍대선택: 원본 승 {w}/11 (임계8) p={p:.4f} {'PASS' if w>=8 else 'FAIL'} ===")
