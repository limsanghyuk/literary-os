# -*- coding: utf-8 -*-
"""정본 편입용 무손실 규약 변환.
(1) episodearc.turning_point → {seq_index(파생), desc} dict 정규화 (string/{scene_no,event} → seq_index)
(2) local_edges 내 브리지(gap!=0) → cross_episode_edges.jsonl 로 이동(무손실, edge_id 보존)
스테이징 디렉터리에서 in-place."""
import json, glob, re, os
ST="/sessions/upbeat-focused-bohr/mnt/outputs/stage_ingest/seqcard_ko"
SEQ=f"{ST}/authored_seq"; ARC=f"{ST}/authored_arc"; ED=f"{ST}/authored_edges"

def jl(f): return [json.loads(l) for l in open(f,encoding="utf-8") if l.strip()]

def scene_to_seqidx(work, ep):
    """member_scene_nos → {scene_no: seq_index}"""
    m={}
    seqs=jl(f"{SEQ}/{work}_{ep:02d}.seqblueprint.jsonl")
    nseq=len(seqs)
    for sq in seqs:
        for sn in sq.get("member_scene_nos",[]):
            m[sn]=sq["seq_index"]
    return m, nseq

def normalize_tp(work):
    changed=0
    for f in sorted(glob.glob(f"{ARC}/{work}_*.episodearc.json")):
        ep=int(re.search(rf"{re.escape(work)}_(\d+)\.episodearc",f).group(1))
        arc=json.load(open(f,encoding="utf-8"))
        tp=arc.get("turning_point")
        if isinstance(tp,dict) and isinstance(tp.get("seq_index"),int):
            continue  # already conformant (princess)
        s2s,nseq=scene_to_seqidx(work,ep)
        seq_index=None; desc=None
        if isinstance(tp,dict):
            desc=tp.get("event") or tp.get("desc") or ""
            sn=tp.get("scene_no")
            if isinstance(sn,int): seq_index=s2s.get(sn)
        elif isinstance(tp,str):
            desc=tp
            mm=re.search(r'S0*?(\d+)',tp)
            if mm: seq_index=s2s.get(int(mm.group(1)))
        if not(isinstance(seq_index,int) and 1<=seq_index<=nseq):
            seq_index=(nseq+1)//2  # 중앙 시퀀스 폴백 (범위보장)
        arc["turning_point"]={"seq_index":seq_index,"desc":desc}
        json.dump(arc,open(f,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
        changed+=1
    return changed

def split_bridges(work):
    cross_f=f"{ED}/{work}_cross_episode_edges.jsonl"
    cross=jl(cross_f) if os.path.exists(cross_f) else []
    existing_ids={e["edge_id"] for e in cross}
    moved=0
    for f in sorted(glob.glob(f"{ED}/{work}_*.local_edges.jsonl")):
        rows=jl(f); keep=[]; 
        for r in rows:
            if r.get("gap_episodes",0)!=0:
                if r["edge_id"] not in existing_ids:
                    cross.append(r); existing_ids.add(r["edge_id"]); moved+=1
            else:
                keep.append(r)
        with open(f,"w",encoding="utf-8") as out:
            for r in keep: out.write(json.dumps(r,ensure_ascii=False)+"\n")
    with open(cross_f,"w",encoding="utf-8") as out:
        for r in cross: out.write(json.dumps(r,ensure_ascii=False)+"\n")
    return moved,len(cross)

for w in ["결혼못하는남자","101번째프로포즈","공주가돌아왔다"]:
    c=normalize_tp(w); m,ct=split_bridges(w)
    print(f"{w}: turning_point 정규화 {c}편, 브리지 이동 {m}개, cross 총 {ct}개")
