# -*- coding: utf-8 -*-
"""관찰 G: 생성(mini 모작) vs 명작 원본 — 쌍대 강제선택 (씬5·8·11 대응, 위치 무작위, 임계 없는 관찰)"""
import json,os,random,urllib.request
KEY=os.environ["OPENAI_API_KEY"]; D="/tmp/m3/"
def chat(msgs,model="gpt-4o",mt=80):
    b=json.dumps({"model":model,"temperature":0.0,"max_tokens":mt,"messages":msgs}).encode()
    r=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=b,headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=120) as x: return json.load(x)["choices"][0]["message"]["content"]
SC=[s.strip() for s in open(D+"unsu.txt",encoding="utf-8").read().split("###SCENE###")]
gen=json.load(open(D+"gen.json")); IDX=[4,7,10]
random.seed(5)
for k in range(3):
    i=IDX[k]; ofirst=random.random()<0.5
    a,b=(SC[i],gen[k]) if ofirst else (gen[k],SC[i])
    o=chat([{"role":"system","content":"당신은 문학 심사위원이다. JSON만 출력."},
      {"role":"user","content":'같은 상황을 다룬 두 글 중 문학적으로 우수한 쪽을 골라라. 무승부 금지. JSON: {"choice":"A"|"B","reason":"15자 이내"}\n\n[A]\n'+a+'\n\n[B]\n'+b}])
    j=json.loads(o[o.find("{"):o.rfind("}")+1])
    ow=(j["choice"]=="A")==ofirst
    print(f"s{i+1} vs 생성: {'명작W' if ow else '생성W'} ({j.get('reason','')})",flush=True)
