import os,sys,json,glob,random,urllib.request,time
sys.path.insert(0,"experiments"); from meta_gt import META
KEY=open("/tmp/oai.key").read().strip()
random.seed(7)
SCN="scenes"
def pick_scene(w):
    rows=[json.loads(L) for L in open(f"{SCN}/{w}.jsonl",errors='ignore')]
    cands=[r for r in rows if 400<=len(r["text"])<=1400 and not r["heading"].startswith("[block")]
    if not cands: cands=[r for r in rows if len(r["text"])>=300]
    if not cands: return None
    cands.sort(key=lambda r:abs(r["scene_no"]-len(rows)*0.5))  # mid-story
    return cands[0]["text"][:1300]
HIGH=[w for w in META if META[w][1]>=4]
LOW =[w for w in META if META[w][1]<=1]
pairs=[]
for h in HIGH:
    for l in LOW:
        pairs.append((h,l))
random.shuffle(pairs); pairs=pairs[:15]
ROLES={
"구조분석가":"너는 20년차 시나리오 구조 분석 전문가다. 장면의 극적 구조·갈등 설계·정보 통제를 본다.",
"대사전문가":"너는 최고 수준의 대사·서브텍스트 작가다. 대사의 밀도·함축·인물 목소리를 본다.",
"긴장비평가":"너는 장르·긴장 리듬 비평가다. 긴장 조성·페이스·몰입을 본다.",
}
def ask(role_sys,a,b):
    p=(f"두 시나리오 장면이다. 극작 완성도가 더 높은 쪽만 'A' 또는 'B' 한 글자로 답하라(설명 금지).\n\n[장면 A]\n{a}\n\n[장면 B]\n{b}")
    body=json.dumps({"model":"gpt-4o-mini","messages":[{"role":"system","content":role_sys},{"role":"user","content":p}],"temperature":0,"max_tokens":3}).encode()
    req=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=body,headers={"Authorization":"Bearer "+KEY,"Content-Type":"application/json"})
    for t in range(4):
        try:
            r=json.load(urllib.request.urlopen(req,timeout=40)); return r["choices"][0]["message"]["content"].strip().upper()[:1]
        except Exception as e:
            if t==3: return "?"
            time.sleep(2*(t+1))
results=[]; correct=0; done=0
START=time.time()
prev=json.load(open("experiments/poc_panel_results.json")) if os.path.exists("experiments/poc_panel_results.json") else []
seen={(r["high"],r["low"]) for r in prev}; results=prev
for h,l in pairs:
    if (h,l) in seen: continue
    if time.time()-START>34: print("budget",flush=True); break
    sh,sl=pick_scene(h),pick_scene(l)
    if not sh or not sl: continue
    high_is_A=random.random()<0.5
    A,B=(sh,sl) if high_is_A else (sl,sh)
    votes={}
    for role,sysmsg in ROLES.items():
        v=ask(sysmsg,A,B); votes[role]=v
    # majority for high
    high_letter="A" if high_is_A else "B"
    nhigh=sum(1 for v in votes.values() if v==high_letter)
    pick_high = nhigh>=2
    results.append({"high":h,"low":l,"votes":votes,"high_letter":high_letter,"panel_pick_high":pick_high,"n_high_votes":nhigh})
    print(f"  {h[:8]:8} vs {l[:8]:8} | votes={list(votes.values())} highletter={high_letter} -> pick_high={pick_high}",flush=True)
json.dump(results,open("experiments/poc_panel_results.json","w"),ensure_ascii=False,indent=0)
done=len(results)
ch=sum(1 for r in results if r["panel_pick_high"])
print(f"\nPAIRS done={done} | panel picked higher-acclaim: {ch}/{done} = {ch/done:.0%}" if done else "none",flush=True)
