# make_pairs.py - scaled loop-C pairs. chosen=masterpiece, rejected=gpt-4o-mini draft. Resumable, time-boxed.
import os, sys, json, glob, random, urllib.request, threading, time

KEY = os.environ["OAI_KEY"]
N = int(sys.argv[1]) if len(sys.argv) > 1 else 280
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/pairs_all.jsonl"
TIME_BUDGET = float(os.environ.get("TIME_BUDGET", "40"))
WORKERS = 12
START = time.time()
random.seed(42)

CORPUS = "/sessions/zen-youthful-shannon/mnt/claude/db/corpus_ko/scenes"
works = glob.glob(CORPUS + "/*.jsonl"); random.shuffle(works)
pool = []
for f in works[:400]:
    base = os.path.basename(f)[:-6]
    for L in open(f, errors="ignore"):
        try: s = json.loads(L)
        except: continue
        t = s.get("text", "")
        if 250 <= len(t) <= 650:
            pool.append(("%s::S%s" % (base, s.get("scene_no", "?")), t))
random.shuffle(pool)

FUNCS = ["setup", "inciting", "rising", "midpoint", "crisis", "climax", "resolution"]
GENRES = ["thriller", "crime", "melo", "romance", "mystery", "family"]

def call(msgs, mt, temp):
    body = json.dumps({"model": "gpt-4o-mini", "messages": msgs, "temperature": temp, "max_tokens": mt}).encode()
    r = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body,
                               headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=40))["choices"][0]["message"]["content"]

def gen(func, genre):
    return call([{"role": "user", "content":
                  "한국 %s 드라마/영화 씬 1개를 산문으로(300~430자, 지문+대사). 기능=%s. 본문만." % (genre, func)}], 520, 0.7)

lock = threading.Lock()
made = [sum(1 for _ in open(OUT)) if os.path.exists(OUT) else 0]

def worker():
    while True:
        if time.time() - START > TIME_BUDGET: return
        with lock:
            if made[0] >= N: return
            idx = made[0]; made[0] += 1
        func = random.choice(FUNCS); genre = random.choice(GENRES)
        try:
            d = gen(func, genre)
        except Exception:
            with lock: made[0] -= 1
            continue
        rid, rtext = pool[idx % len(pool)]
        rec = {"func": func, "genre": genre, "ref_id": rid, "winner": "ref", "draft": d[:600], "ref": rtext[:600]}
        with lock:
            with open(OUT, "a") as o:
                o.write(json.dumps(rec, ensure_ascii=False) + "\n")

ts = [threading.Thread(target=worker) for _ in range(WORKERS)]
[t.start() for t in ts]; [t.join() for t in ts]
print("pairs now = %d (target %d)" % (sum(1 for _ in open(OUT)), N), flush=True)
