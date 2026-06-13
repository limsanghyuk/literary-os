import os,glob,json,re,urllib.request,time
ROOT="."; TXT="txt"
KEY=open("/tmp/oai.key").read().strip()
nkg=json.load(open("nkg.json"))
targets=[r["work"] for r in json.load(open("qc_report.json")) if "NO_CHARS" in r["flags"]]
def sample(t):
    return t[:6000]+"\n...\n"+t[len(t)//2:len(t)//2+4000]
def ask(name,txt):
    prompt=("다음은 한국 영화/드라마 시나리오 일부다. 등장하는 주요 인물(사람 이름/호칭)만 "
            "JSON 배열로 출력하라. 설명 없이 [\"이름\",...] 형식. 장소/사물/추상어 제외.\n\n"+sample(txt))
    body=json.dumps({"model":"gpt-4o-mini","messages":[{"role":"user","content":prompt}],
                     "temperature":0,"max_tokens":300}).encode()
    req=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=body,
        headers={"Authorization":"Bearer "+KEY,"Content-Type":"application/json"})
    r=json.load(urllib.request.urlopen(req,timeout=60))
    return r["choices"][0]["message"]["content"]
import sys
START=time.time()
done=0
for w in targets:
    if nkg.get(w,{}).get("char_method")=="llm": continue
    if time.time()-START>36: print("budget",flush=True);break
    p=f"{TXT}/{w}.txt"
    if not os.path.exists(p): continue
    txt=open(p,errors='ignore').read()
    try:
        raw=ask(w,txt)
        m=re.search(r'\[.*\]',raw,re.S); names=json.loads(m.group(0)) if m else []
    except Exception as e: print("ERR",w,str(e)[:50],flush=True);continue
    # ground: keep names appearing >=3 times
    grounded=[]
    for nm in names:
        nm=str(nm).strip()
        if 2<=len(nm)<=6 and txt.count(nm)>=3: grounded.append(nm)
    grounded=sorted(set(grounded),key=lambda x:-txt.count(x))[:12]
    e=nkg.get(w,{}); e["characters"]=grounded; e["n_characters"]=len(grounded); e["char_method"]="llm"
    nkg[w]=e; done+=1
    print(f"  {w}: {grounded[:6]}",flush=True)
json.dump(nkg,open("nkg.json","w"),ensure_ascii=False,indent=0)
print("llm-extracted this run:",done,flush=True)
