# -*- coding: utf-8 -*-
"""엄격 3층 게이트(우회불가). 인자: work_id (예: 스토브리그).
축B(집계정합) + 필드존재(정확 키셋) + value_shift{from,to} 형태 + turn_class 4버킷
+ 밀도 floor(ratio>=0.11) 를 모두 검사. ERRORS 0 이어야 PASS."""
import json, sys, glob, re, os
BASE="/sessions/upbeat-focused-bohr/mnt/claude/db/seqcard_ko"
SC=f"{BASE}/authored"; SEQ=f"{BASE}/authored_seq"; ARC=f"{BASE}/authored_arc"
CORE_ENUM={"ESTABLISH","ORACLE","INTRO","BOND","CONFLICT","REVERSAL","LOSS","PUNISH",
 "REVELATION","REUNION","RELIEF","ROMANCE","PERIL","RESCUE","DESIRE","HOOK"}
TURN_CLASS={"RISE","FALL","REVEAL","STALL"}
SEQ_KEYS={"seq_id","work_id","episode_no","seq_index","member_scene_nos","scene_span",
 "scene_budget","sequence_intent","goal","obstacle","value_shift","turn_type","turn_class",
 "core_mix","pov_char","place_cluster","runtime_share","by"}
ARC_KEYS={"work_id","episode_no","scene_count","sequence_count","dramatic_question",
 "act_structure","entry_state","exit_state","turning_point","central_conflict_axis",
 "episode_function","core_dist","by"}
FULL_KEYS={"series","episodes_total","scenes_total","sequences_total","logline",
 "central_dramatic_question","theme_statement","protagonist","antagonist","season_structure",
 "macro_turning_points","resolution","open_ending","tone","conflict_persist","series_core_dist","by"}
DENSITY_FLOOR=0.11
work=sys.argv[1]
def jl(f): return [json.loads(l) for l in open(f,encoding="utf-8") if l.strip()]
eps=sorted(int(re.search(rf"{re.escape(work)}_(\d+)\.seqcard",p).group(1))
           for p in glob.glob(f"{SC}/{work}_*.seqcard.jsonl"))
errors=[]; tot_scene=tot_seq=0
for ep in eps:
    scenes=jl(f"{SC}/{work}_{ep:02d}.seqcard.jsonl")
    sf=f"{SEQ}/{work}_{ep:02d}.seqblueprint.jsonl"; af=f"{ARC}/{work}_{ep:02d}.episodearc.json"
    if not os.path.exists(sf): errors.append(f"E{ep} MISSING seqblueprint"); continue
    if not os.path.exists(af): errors.append(f"E{ep} MISSING episodearc"); continue
    seqs=jl(sf); arc=json.load(open(af,encoding="utf-8"))
    sn=sorted(s["scene_no"] for s in scenes); N=len(sn); tot_scene+=N; tot_seq+=len(seqs)
    mem=[]
    for sq in seqs:
        sid=sq.get("seq_id","?")
        miss=SEQ_KEYS-set(sq); extra=set(sq)-SEQ_KEYS
        if miss: errors.append(f"E{ep} {sid} seq MISSING {miss}")
        if extra: errors.append(f"E{ep} {sid} seq EXTRA {extra}")
        mem+=sq.get("member_scene_nos",[])
        vs=sq.get("value_shift")
        if not(isinstance(vs,dict) and "from" in vs and "to" in vs):
            errors.append(f"E{ep} {sid} value_shift shape (must be dict from/to)")
        if sq.get("turn_class") not in TURN_CLASS:
            errors.append(f"E{ep} {sid} turn_class '{sq.get('turn_class')}' not in 4-bucket")
        for c in sq.get("core_mix",[]):
            if c not in CORE_ENUM: errors.append(f"E{ep} {sid} core_mix '{c}' not in enum")
        msn=sq.get("member_scene_nos",[])
        if msn and sq.get("scene_span")!=[min(msn),max(msn)]:
            errors.append(f"E{ep} {sid} scene_span mismatch")
        if sq.get("scene_budget")!=len(msn): errors.append(f"E{ep} {sid} budget")
        if sq.get("work_id")!=f"{work}_{ep:02d}": errors.append(f"E{ep} {sid} work_id FK")
    if sorted(mem)!=sn: errors.append(f"E{ep} I-COVER fail ({len(mem)} vs {N})")
    if len(mem)!=len(set(mem)): errors.append(f"E{ep} I-PARTITION dup")
    if sum(s.get("scene_budget",0) for s in seqs)!=N: errors.append(f"E{ep} I-COUNT")
    amiss=ARC_KEYS-set(arc); aextra=set(arc)-ARC_KEYS
    if amiss: errors.append(f"E{ep} arc MISSING {amiss}")
    if aextra: errors.append(f"E{ep} arc EXTRA {aextra}")
    if arc.get("sequence_count")!=len(seqs): errors.append(f"E{ep} arc seq_count")
    if arc.get("scene_count")!=N: errors.append(f"E{ep} arc scene_count")
    acov=[]
    for a in arc.get("act_structure",[]): acov+=list(range(a["seq_span"][0],a["seq_span"][1]+1))
    if sorted(acov)!=list(range(1,len(seqs)+1)): errors.append(f"E{ep} I-ACT-COVER")
    tp=arc.get("turning_point",{}).get("seq_index")
    if not(isinstance(tp,int) and 1<=tp<=len(seqs)): errors.append(f"E{ep} turning_point range")
fullf=f"{SC}/{work}_full_series_arc.json"
if os.path.exists(fullf):
    full=json.load(open(fullf,encoding="utf-8"))
    fmiss=FULL_KEYS-set(full); fextra=set(full)-FULL_KEYS
    if fmiss: errors.append(f"FULL MISSING {fmiss}")
    if fextra: errors.append(f"FULL EXTRA {fextra}")
    scov=[]
    for m in full.get("season_structure",[]): scov+=list(range(m["episode_span"][0],m["episode_span"][1]+1))
    if sorted(scov)!=eps: errors.append("FULL I-SEASON-COVER fail")
    if full.get("scenes_total")!=tot_scene: errors.append(f"FULL scenes_total {full.get('scenes_total')}!={tot_scene}")
    if full.get("sequences_total")!=tot_seq: errors.append(f"FULL sequences_total {full.get('sequences_total')}!={tot_seq}")
else: errors.append("FULL series_arc MISSING")
ratio=tot_seq/max(tot_scene,1)
if ratio<DENSITY_FLOOR: errors.append(f"DENSITY ratio={ratio:.3f} < floor {DENSITY_FLOOR} (과소분절)")
print(f"[{work}] eps={eps}  scenes={tot_scene} seqs={tot_seq} ratio={ratio:.3f}x")
if errors:
    print(f"ERRORS {len(errors)}:")
    for e in errors[:30]: print("  X",e)
else:
    print("ERRORS 0 — 엄격게이트 ALL PASS")
