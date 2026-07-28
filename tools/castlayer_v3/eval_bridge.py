import json,glob,os,collections,sys
LOC="/tmp/work87/seqcard_ko/seqcard_ko"; HUB="/tmp/hub/seqcard_ko"; BOOT="/tmp/cl3/out/advisory_bridge"
def surf(bfile):
    S={}
    for l in open(bfile,encoding="utf-8"):
        b=json.loads(l); S[b["canonical_name"]]=set([b["canonical_name"]])|set(b.get("aliases") or [])
    return S
def goldmap(bfile):
    """gold character_key -> canonical_name"""
    m={}
    for l in open(bfile,encoding="utf-8"):
        b=json.loads(l); m[b["character_key"]]=b.get("canonical_name") or b["character_key"]
    return m
def ev(S, castglob, gmap):
    tp=fp=fn=0
    for cf in sorted(glob.glob(castglob)):
        ep=os.path.basename(cf).split(".")[0]
        scf=f"{LOC}/authored/{ep}.seqcard.jsonl"
        if not os.path.exists(scf): continue
        G=collections.defaultdict(set)
        for l in open(cf,encoding="utf-8"):
            r=json.loads(l); G[str(r.get('scene_id') or r.get('scene_no'))].add(gmap.get(r["character_key"],r["character_key"]))
        for l in open(scf,encoding="utf-8"):
            c=json.loads(l); sid=str(c.get('scene_id') or c.get('scene_no'))
            t=" ".join(str(v) for v in c.values())
            pred={k for k,ns in S.items() if any(n in t for n in ns)}
            g=G.get(sid,set()); tp+=len(pred&g); fp+=len(pred-g); fn+=len(g-pred)
    p=tp/(tp+fp) if tp+fp else 0; r=tp/(tp+fn) if tp+fn else 0
    return dict(TP=tp,FP=fp,FN=fn,P=round(p,3),R=round(r,3),F1=round(2*p*r/(p+r),3) if p+r else 0)
print("비밀의숲_01  부트스트랩명부:", ev(surf(f"{BOOT}/비밀의숲.bridge.jsonl"), f"{HUB}/authored_cast/비밀의숲_01.cast.jsonl", goldmap(f"{HUB}/authored_bridge/비밀의숲.bridge.jsonl")))
print("돌아온일지매 부트스트랩명부:", ev(surf(f"{BOOT}/돌아온일지매.bridge.jsonl"), f"{LOC}/authored_cast/돌아온일지매_*.cast.jsonl", goldmap(f"{LOC}/authored_bridge/돌아온일지매.bridge.jsonl")))
# 명부 자체 커버리지: gold canonical 중 부트스트랩이 표면형으로 잡는 비율
for w,gb in [("비밀의숲",f"{HUB}/authored_bridge/비밀의숲.bridge.jsonl"),("돌아온일지매",f"{LOC}/authored_bridge/돌아온일지매.bridge.jsonl")]:
    g=set(goldmap(gb).values()); b=surf(f"{BOOT}/{w}.bridge.jsonl")
    allsurf=set().union(*b.values()) if b else set()
    hit=sum(1 for n in g if n in b or n in allsurf)
    print(f"  {w} 명부 인물 포괄: gold {len(g)}명 중 {hit}명 ({hit/len(g):.1%}), 부트스트랩 {len(b)}명")
