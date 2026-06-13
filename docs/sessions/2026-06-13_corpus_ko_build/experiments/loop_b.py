# 중간루프 B 프로토타입: 패널(보상)→fitness 재가중→객관 명성으로 전이검증
import os,sys,json,glob,random,urllib.request,time
sys.path.insert(0,"experiments"); from meta_gt_v2 import META2
KEY=open("/tmp/oai.key").read().strip(); random.seed(11)
W=json.load(open("experiments/work_features.json")); RF=json.load(open("experiments/redefine_feats.json"))
pool=[w for w in META2 if w in W and w in RF]
def scene(w):
    rows=[json.loads(L) for L in open(f"scenes/{w}.jsonl",errors='ignore')]
    c=[r for r in rows if 400<=len(r["text"])<=1300 and not r["heading"].startswith("[block")]
    c.sort(key=lambda r:abs(r["scene_no"]-len(rows)*0.5))
    return c[0]["text"][:1200] if c else (rows[len(rows)//2]["text"][:1200] if rows else "")
ROLES={"구조":"시나리오 구조 전문가","대사":"대사·서브텍스트 전문가","긴장":"장르·긴장 비평가"}
def ask(sysmsg,a,b):
    p=f"두 장면 중 극작 완성도 높은 쪽만 'A'/'B'로.\n[A]\n{a}\n\n[B]\n{b}"
    body=json.dumps({"model":"gpt-4o-mini","messages":[{"role":"system","content":sysmsg},{"role":"user","content":p}],"temperature":0,"max_tokens":2}).encode()
    r=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=body,headers={"Authorization":"Bearer "+KEY,"Content-Type":"application/json"})
    for t in range(4):
        try: return json.load(urllib.request.urlopen(r,timeout=40))["choices"][0]["message"]["content"].strip().upper()[:1]
        except: 
            if t==3: return "?"
            time.sleep(2)
# build pairs (spanning acclaim)
random.shuffle(pool)
pairs=[(pool[i],pool[i+1]) for i in range(0,min(40,len(pool)-1),2)]
res=json.load(open("experiments/loop_b_pairs.json")) if os.path.exists("experiments/loop_b_pairs.json") else []
seen={(r["a"],r["b"]) for r in res}
START=time.time()
for a,b in pairs:
    if (a,b) in seen: continue
    if time.time()-START>34: print("budget",flush=True);break
    sa,sb=scene(a),scene(b)
    if not sa or not sb: continue
    A_is_a=random.random()<0.5
    X,Y=(sa,sb) if A_is_a else (sb,sa)
    votes=[ask(s,X,Y) for s in ROLES.values()]
    apick=sum(1 for v in votes if v==("A" if A_is_a else "B"))
    res.append({"a":a,"b":b,"votes":votes,"panel_pref_a":apick>=2})
    print(f"  {a[:6]} vs {b[:6]}: panel_pref_a={apick>=2}",flush=True)
json.dump(res,open("experiments/loop_b_pairs.json","w"),ensure_ascii=False)
print("pairs collected:",len(res),flush=True)
