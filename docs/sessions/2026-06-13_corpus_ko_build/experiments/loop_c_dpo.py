# Lean loop-C 측정 + DPO 선호쌍 수집 (생성 vs 실명작, 경량·재개)
import os,sys,json,glob,random,urllib.request,time
KEY=open("/tmp/oai.key").read().strip(); random.seed()
OUT="experiments/dpo_pairs.jsonl"
# 레퍼런스 풀: 명작 부분집합만(빠름)
REFW=["살인의추억","올드보이","마더","곡성","추격자","신세계","밀양","미생05","미생10","시그널","국제시장","암살","태후08","역전의여왕05"]
pool=[]
for w in REFW:
    f=f"scenes/{w}.jsonl"
    if not os.path.exists(f): continue
    for L in open(f,errors='ignore'):
        s=json.loads(L); t=s.get("text","")
        if 250<=len(t)<=650: pool.append((f"{w}::S{s['scene_no']}",t))
def call(msgs,mt,temp):
    body=json.dumps({"model":"gpt-4o-mini","messages":msgs,"temperature":temp,"max_tokens":mt}).encode()
    r=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=body,headers={"Authorization":"Bearer "+KEY,"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(r,timeout=50))["choices"][0]["message"]["content"]
FUNCS=["setup","inciting","rising","midpoint","crisis","climax"]
GENRES=["thriller","crime","melo","romance"]
def gen(func,genre):
    return call([{"role":"user","content":f"한국 {genre} 드라마/영화 씬 1개를 산문으로(300~430자, 지문+대사). 기능={func}. 본문만."}],520,0.7)
def panel(draft,ref):
    swap=random.random()<0.5
    A,B=(ref,draft) if swap else (draft,ref)
    r=call([{"role":"system","content":"3인 패널(문학평론가·드라마투르그·일반시청자) 블라인드 다수결."},
            {"role":"user","content":f"두 씬 A/B 중 서사적 완성도 높은 쪽. 마지막 줄 'WINNER: A' 또는 'WINNER: B'.\n[A]\n{A}\n\n[B]\n{B}"}],200,0.2)
    import re; m=re.search(r"WINNER\s*[:：]\s*(A|B)",r,re.I); w=m.group(1).upper() if m else "B"
    draft_is="B" if swap else "A"
    return "draft" if w==draft_is else "ref"
done=sum(1 for _ in open(OUT)) if os.path.exists(OUT) else 0
START=time.time(); new=0
with open(OUT,"a") as o:
    while time.time()-START<35:
        func=random.choice(FUNCS); genre=random.choice(GENRES)
        d=gen(func,genre); rid,rtext=random.choice(pool)
        win=panel(d,rtext)
        o.write(json.dumps({"func":func,"genre":genre,"ref_id":rid,"winner":win,
                            "draft":d[:600],"ref":rtext[:600]},ensure_ascii=False)+"\n"); o.flush()
        new+=1; print(f"  {func}/{genre} vs {rid[:10]} → {win} 승",flush=True)
tot=sum(1 for _ in open(OUT)); dwin=sum(1 for L in open(OUT) if json.loads(L)["winner"]=="draft")
print(f"\n누적 선호쌍 {tot} (이번 {new}) | 생성 승 {dwin}/{tot} = {dwin/tot:.0%} (실명작 풀 {len(pool)}씬)",flush=True)
