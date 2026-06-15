# ④ 최고 전문 작가 에이전트 = human-GT 대체. 명성차 씬쌍 판정 → 객관정확도 + critic패널 일치율
import os,sys,json,glob,random,urllib.request,time,re
sys.path.insert(0,"experiments"); from meta_gt_v2 import META2
KEY=open("/tmp/oai.key").read().strip(); random.seed(5)
HIGH=[w for w in META2 if META2[w][1]>=4]; LOW=[w for w in META2 if META2[w][1]<=1]
def scene(w):
    f=f"scenes/{w}.jsonl"
    if not os.path.exists(f): return None
    c=[json.loads(L) for L in open(f,errors='ignore')]
    c=[r for r in c if 400<=len(r["text"])<=1200 and not r["heading"].startswith("[block")]
    return random.choice(c)["text"][:1100] if c else None
def call(model,sysm,usr,mt,temp):
    msgs=[{"role":"system","content":sysm},{"role":"user","content":usr}]
    p={"model":model,"messages":msgs}
    if model.startswith("gpt-5"):p["max_completion_tokens"]=mt
    else:p["max_tokens"]=mt;p["temperature"]=temp
    r=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=json.dumps(p).encode(),
        headers={"Authorization":"Bearer "+KEY,"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(r,timeout=50))["choices"][0]["message"]["content"]
def parse(r):
    m=re.search(r"(?:WINNER|승자)\s*[:：]?\s*(A|B)",r,re.I); return m.group(1).upper() if m else "B"
WRITER="당신은 칸·백상 수상 경력의 20년차 최고 드라마/영화 극작가다. 서사 구조·서브텍스트·대사 함축·인물 진정성을 본다."
PANEL="3인 패널(문학평론가·드라마투르그·일반시청자) 블라인드 다수결."
pairs=[]
for h in HIGH:
    for l in LOW: pairs.append((h,l))
random.shuffle(pairs); pairs=pairs[:8]
res=json.load(open("experiments/writer_gt.json")) if os.path.exists("experiments/writer_gt.json") else []
seen={(r["h"],r["l"]) for r in res}
START=time.time()
for h,l in pairs:
    if (h,l) in seen: continue
    if time.time()-START>33: break
    sh,sl=scene(h),scene(l)
    if not sh or not sl: continue
    hi_is_A=random.random()<0.5
    A,B=(sh,sl) if hi_is_A else (sl,sh)
    q=f"두 씬 중 극작 완성도 높은 쪽. 마지막 줄 'WINNER: A' 또는 'WINNER: B'.\n[A]\n{A}\n\n[B]\n{B}"
    wa=parse(call("gpt-4o",WRITER,q,250,0.2))      # 작가 에이전트
    pa=parse(call("gpt-4o-mini",PANEL,q,200,0.2))  # critic 패널
    hl="A" if hi_is_A else "B"
    res.append({"h":h,"l":l,"writer_correct":wa==hl,"panel_correct":pa==hl,"agree":wa==pa})
    print(f"  {h[:6]} vs {l[:6]}: 작가{'O' if wa==hl else 'X'} 패널{'O' if pa==hl else 'X'} 일치{'O' if wa==pa else 'X'}",flush=True)
json.dump(res,open("experiments/writer_gt.json","w"),ensure_ascii=False)
n=len(res)
if n:
    wc=sum(r["writer_correct"] for r in res); pc=sum(r["panel_correct"] for r in res); ag=sum(r["agree"] for r in res)
    print(f"\nn={n} | 작가에이전트 정확도 {wc}/{n} | critic패널 {pc}/{n} | 작가-패널 일치 {ag}/{n}",flush=True)
