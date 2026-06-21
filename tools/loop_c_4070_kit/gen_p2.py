# P2 quality pair: chosen=구체/고유 디테일(specific), rejected=평이/상투(generic). 같은 상황·목표길이.
import os,sys,json,glob,random,urllib.request,threading,time,re
KEY=open("/tmp/oai.key").read().strip()
SCN="/sessions/zen-youthful-shannon/mnt/claude/db/corpus_ko/scenes"
OUT=sys.argv[1] if len(sys.argv)>1 else "/tmp/p2_raw.jsonl"
N=int(sys.argv[2]) if len(sys.argv)>2 else 150
TB=float(os.environ.get("TB","36")); WK=16; START=time.time()
random.seed(int(time.time()))
works=glob.glob(SCN+"/*.jsonl"); random.shuffle(works)
GEN=["스릴러","멜로","수사","가족","미스터리","로맨스","사극","의학","코미디"]
def call(situ,genre):
    p=("한국 %s 드라마 한 장면을 두 버전으로. 상황=%s.\n"
       "[GOOD] 구체적·고유 디테일(특정 사물/행동/감각/장소 디테일), 상투어 회피, 인물 고유성.\n"
       "[WEAK] 평이·상투(뻔한 표현, 일반적 묘사, 클리셰), 디테일 없음.\n"
       "두 버전 모두 320~360자, 지문+대사. 형식:\n[GOOD]\n<본문>\n[WEAK]\n<본문>")%(genre,situ)
    body=json.dumps({"model":"gpt-4o-mini","messages":[{"role":"user","content":p}],"temperature":0.85,"max_tokens":700}).encode()
    r=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=body,headers={"Authorization":"Bearer "+KEY,"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(r,timeout=40))["choices"][0]["message"]["content"]
def parse(t):
    m=re.search(r"\[GOOD\](.*?)\[WEAK\](.*)",t,re.S)
    if not m: return None,None
    return m.group(1).strip()[:600], m.group(2).strip()[:600]
lock=threading.Lock(); made=[sum(1 for _ in open(OUT)) if os.path.exists(OUT) else 0]
def wk():
    while True:
        if time.time()-START>TB: return
        with lock:
            if made[0]>=N: return
            i=made[0]; made[0]+=1
        situ=random.choice(["재회","갈등 폭발","결심","비밀 발각","작별","추궁","위로","사고 직후"])
        try: g,w=parse(call(situ,random.choice(GEN)))
        except Exception:
            with lock: made[0]-=1
            continue
        if not g or not w or len(g)<150 or len(w)<150:
            with lock: made[0]-=1
            continue
        with lock: open(OUT,"a").write(json.dumps({"pair_id":"p2_%04d"%i,"work_id":"p2_%04d"%i,"strategy":"p2","chosen":g,"rejected":w},ensure_ascii=False)+"\n")
ts=[threading.Thread(target=wk) for _ in range(WK)]
[t.start() for t in ts]; [t.join() for t in ts]
print("p2:",sum(1 for _ in open(OUT)))
