# -*- coding: utf-8 -*-
"""LW-5 (사전등록): 문체 목표 달성도 분리 — '감정을 선언하지 않고 행동·감각으로 보여주는 절제된 저온 문체'에
어느 쪽이 가까운가 (선호와 무관). 임계: S >=4/6. PASS+2a/b FAIL 조합이면 '기능은 작동, 심판이 화려체 선호' 해석."""
import json,os,random,urllib.request
KEY=os.environ["OPENAI_API_KEY"]; D="/tmp/m3/"
def chat(msgs,mt=60):
    b=json.dumps({"model":"gpt-4o","temperature":0.0,"max_tokens":mt,"messages":msgs}).encode()
    r=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=b,headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=120) as x: return json.load(x)["choices"][0]["message"]["content"]
ep=json.load(open(D+"lw_ep.json"))
res=json.load(open(D+"lw5.json")) if os.path.exists(D+"lw5.json") else {}
random.seed(41); pos=[random.random()<0.5 for _ in range(6)]
for k in range(6):
    kk=str(k)
    if kk in res: continue
    a,b=(ep["S"][k],ep["P"][k]) if pos[k] else (ep["P"][k],ep["S"][k])
    o=chat([{"role":"system","content":"당신은 문체 분석가다. JSON만 출력."},
      {"role":"user","content":'질문: 두 글 중 "감정을 직접 선언하지 않고 행동·감각·사물로 보여주는 절제된 저온 문체"에 더 가까운 쪽은? 선호가 아니라 문체 특성만 판단하라. 무승부 금지. JSON: {"closer":"A"|"B"}\n\n[A]\n'+a+'\n\n[B]\n'+b}])
    j=json.loads(o[o.find("{"):o.rfind("}")+1])
    res[kk]=(j["closer"]=="A")==pos[k]; json.dump(res,open(D+"lw5.json","w"))
    print(f"lw5 {k+1}/6: {'S' if res[kk] else 'P'}",flush=True)
w=sum(1 for v in res.values() if v)
print(f"=== LW-5 문체 달성도: S {w}/6 (임계4) {'PASS' if w>=4 else 'FAIL'} ===")
