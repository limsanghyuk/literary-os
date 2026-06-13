# 교정 루프B: 씬 단위 — 패널이 씬쌍 판정 → 씬-스코어러(scene_features 가중) 학습
import os,sys,json,glob,random,sqlite3,urllib.request,time
KEY=open("/tmp/oai.key").read().strip(); random.seed(23)
con=sqlite3.connect("/sessions/upbeat-focused-bohr/scene_features.db");cur=con.cursor()
FEATS=["conflict_intensity","scene_energy_ratio","motif_residue_score","curiosity_gradient","dialogue_ratio"]
# scene pool: works with features, scenes 450-1200 chars
wids=[r[0] for r in cur.execute("SELECT DISTINCT work_id FROM scene_features").fetchall()]
# load scene text
def scene_text(w,sn):
    for L in open(f"scenes/{w}.jsonl",errors='ignore'):
        d=json.loads(L)
        if d["scene_no"]==sn: return d["text"]
    return ""
# build candidate scenes (work, scene_no, features, len)
cand=[]
for w,sn,nc,ci,se,mo,cu,dr in cur.execute(f"SELECT work_id,scene_no,n_chars,{','.join(FEATS)} FROM scene_features WHERE n_chars BETWEEN 450 AND 1200"):
    cand.append((w,sn,{"conflict_intensity":ci,"scene_energy_ratio":se,"motif_residue_score":mo,"curiosity_gradient":cu,"dialogue_ratio":dr}))
random.shuffle(cand)
pairs=[(cand[i],cand[i+1]) for i in range(0,80,2)]  # up to 40 pairs
ROLES=["시나리오 구조 전문가","대사·서브텍스트 전문가","장르·긴장 비평가"]
def ask(sysmsg,a,b):
    p=f"두 장면 중 극작 완성도가 높은 쪽만 'A'/'B'로.\n[A]\n{a}\n\n[B]\n{b}"
    body=json.dumps({"model":"gpt-4o-mini","messages":[{"role":"system","content":sysmsg},{"role":"user","content":p}],"temperature":0,"max_tokens":2}).encode()
    r=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=body,headers={"Authorization":"Bearer "+KEY,"Content-Type":"application/json"})
    for t in range(4):
        try:return json.load(urllib.request.urlopen(r,timeout=40))["choices"][0]["message"]["content"].strip().upper()[:1]
        except:
            if t==3:return "?"
            time.sleep(2)
res=json.load(open("experiments/scene_lb.json")) if os.path.exists("experiments/scene_lb.json") else []
seen={(r["aw"],r["asn"],r["bw"],r["bsn"]) for r in res}
START=time.time()
for (aw,asn,af),(bw,bsn,bf) in pairs:
    if (aw,asn,bw,bsn) in seen: continue
    if time.time()-START>34: print("budget",flush=True);break
    ta,tb=scene_text(aw,asn)[:1100],scene_text(bw,bsn)[:1100]
    if len(ta)<200 or len(tb)<200: continue
    Aa=random.random()<0.5
    X,Y=(ta,tb) if Aa else (tb,ta)
    votes=[ask(s,X,Y) for s in ROLES]
    apick=sum(1 for v in votes if v==("A" if Aa else "B"))
    res.append({"aw":aw,"asn":asn,"af":af,"bw":bw,"bsn":bsn,"bf":bf,"a_wins":apick>=2,"votes":votes})
    print(f"  {aw[:6]}#{asn} vs {bw[:6]}#{bsn}: a_wins={apick>=2}",flush=True)
json.dump(res,open("experiments/scene_lb.json","w"),ensure_ascii=False)
print("scene pairs:",len(res),flush=True)
