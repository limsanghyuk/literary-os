#!/usr/bin/env python3
"""6작품(2026-07-03 본연구) 또는 임의 확장 WORKS 리스트에 대해 필드별 PABAK/kappa 층화 분석.
전제: <work>.newfields.jsonl(Claude) + <work>.majority.jsonl(GPT 다수결)가 같은 디렉토리에 존재.
사용: python analyze_full_study.py
(신규 작품 추가 시 WORKS 딕셔너리에 {work_ep_id: 장르명} 한 줄만 추가하면 자동 pooled 재계산됨)
"""
import json, collections

WORKS = {
    "스카이캐슬_01": "사회스릴러(입시)", "스토브리그_01": "스포츠경영", "밀회_01": "불륜멜로",
    "그들이사는세상_01": "가족일일멜로", "W_01": "판타지웹툰", "시크릿가든_01": "로코판타지",
}
BOOL = ["hook_flag","continuity_break","scene_blocks_need"]
NOM = ["episode_role"]; ORD = ["tension_role"]

def load(p):
    d={}
    for l in open(p, encoding='utf-8'):
        if not l.strip(): continue
        r=json.loads(l); d[r["scene_no"]]=r
    return d

def norm_bool(v):
    return v.lower()=="true" if isinstance(v,str) else bool(v)

def pabak(pairs):
    n=len(pairs); po=sum(1 for a,b in pairs if a==b)/n
    return po, 2*po-1

def cohen_kappa(pairs):
    n=len(pairs); po=sum(1 for a,b in pairs if a==b)/n
    ca=collections.Counter(a for a,b in pairs); cb=collections.Counter(b for a,b in pairs)
    cats=set(ca)|set(cb)
    pe=sum((ca.get(c,0)/n)*(cb.get(c,0)/n) for c in cats)
    return po,(po-pe)/(1-pe) if pe<1 else 1.0

def main():
    allpairs=collections.defaultdict(list); per_work={}
    for w in WORKS:
        C=load(f"{w}.newfields.jsonl"); G=load(f"{w}.majority.jsonl")
        common=sorted(set(C)&set(G)); rows={}
        for f in BOOL+NOM+ORD:
            pr=[(C[s].get(f),G[s].get(f)) for s in common if f in C[s] and f in G[s]]
            allpairs[f]+=pr; rows[f]=pr
        per_work[w]=(rows,common)
    n=len(allpairs["hook_flag"])
    print(f"n={n} (pooled, {len(WORKS)}작품)")
    for f in BOOL:
        pr=[(norm_bool(a),norm_bool(b)) for a,b in allpairs[f]]
        po,pb=pabak(pr); print(f"[bool] {f:20s} raw={po:.2f} PABAK={pb:+.2f}")
    for f in NOM+ORD:
        po,k=cohen_kappa(allpairs[f]); print(f"[cat ] {f:20s} raw={po:.2f} kappa={k:+.2f}")
    print()
    for w in WORKS:
        rows,common=per_work[w]
        print(f"-- {w}({WORKS[w]}, n={len(common)}) --")
        for f in BOOL+NOM+ORD:
            pr=rows[f]
            po=sum(1 for a,b in pr if (norm_bool(a)==norm_bool(b) if f in BOOL else a==b))/len(pr)
            print(f"   {f:20s} raw={po:.2f}")

if __name__=="__main__": main()
