# P3 anti-LLM craft pairs: chosen=show-don't-tell, rejected=tell. One call returns both (same situation, target length).
import os,sys,json,glob,random,urllib.request,threading,time,re
KEY=open("/tmp/oai.key").read().strip()
SCN="/sessions/zen-youthful-shannon/mnt/claude/db/corpus_ko/scenes"
OUT=sys.argv[1] if len(sys.argv)>1 else "/tmp/p3_raw.jsonl"
N=int(sys.argv[2]) if len(sys.argv)>2 else 60
TB=float(os.environ.get("TB","38")); WK=16; START=time.time()
random.seed(int(time.time()))
works=glob.glob(SCN+"/*.jsonl"); random.shuffle(works)
GEN=["스릴러","멜로","수사","가족","미스터리","로맨스","사극","의학"]
FUN=["도입","상승","위기","절정","전환","해소"]
def call(situ,genre,fun):
    p=("한국 %s 드라마 한 장면을 두 가지 버전으로 써라. 상황=%s, 기능=%s.\n"
       "[SHOW] 보여주기(show, don't tell): 지문·행동·정적·감각으로 감정을 '드러내되 명시하지 마라'. 감정단어 금지.\n"
       "[TELL] 말하기(tell): 같은 상황을 평이하게, 감정을 직접 서술하고 설명조로.\n"
       "두 버전 모두 320~360자. 형식:\n[SHOW]\n<본문>\n[TELL]\n<본문>")%(genre,situ,fun)
    body=json.dumps({"model":"gpt-4o-mini","messages":[{"role":"user","content":p}],"temperature":0.8,"max_tokens":700}).encode()
    r=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=body,headers={"Authorization":"Bearer "+KEY,"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(r,timeout=40))["choices"][0]["message"]["content"]
def parse(t):
    m=re.search(r"\[SHOW\](.*?)\[TELL\](.*)",t,re.S)
    if not m: return None,None
    return m.group(1).strip()[:600], m.group(2).strip()[:600]
lock=threading.Lock(); made=[sum(1 for _ in open(OUT)) if os.path.exists(OUT) else 0]
def wk():
    while True:
        if time.time()-START>TB: return
        with lock:
            if made[0]>=N: return
            i=made[0]; made[0]+=1
        f=works[i%len(works)]; w=os.path.basename(f)[:-6]
        situ=random.choice(["재회","배신 발각","이별 직전","비밀 누설","대치","고백","상실","추격 후 정적"])
        try:
            show,tell=parse(call(situ,random.choice(GEN),random.choice(FUN)))
        except Exception:
            with lock: made[0]-=1
            continue
        if not show or not tell or len(show)<150 or len(tell)<150:
            with lock: made[0]-=1
            continue
        rec={"pair_id":"p3_%04d"%i,"work_id":"p3_%04d"%i,"strategy":"p3","chosen":show,"rejected":tell}
        with lock: open(OUT,"a").write(json.dumps(rec,ensure_ascii=False)+"\n")
ts=[threading.Thread(target=wk) for _ in range(WK)]
[t.start() for t in ts]; [t.join() for t in ts]
print("p3 누적:",sum(1 for _ in open(OUT)))
