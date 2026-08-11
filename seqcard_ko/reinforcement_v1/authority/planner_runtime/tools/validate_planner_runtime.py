#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Portable validator for DB98 PlannerInput(R5) / RuntimeSceneProjection(R8).

Usage:
  python validate_planner_runtime.py --root <extracted_db_root> --work all --out report.json
  python validate_planner_runtime.py --root <extracted_db_root> --work 궁 --out report.json

This validator does NOT author or repair semantics. It only checks schema,
planning-boundary safety, exact scene coverage, and deterministic parity with
CANONICAL THICK.
"""
from __future__ import annotations
import argparse, json, hashlib, sys
from pathlib import Path

PKEYS=['schema','work_id','episode_no','previous_exit_state','character_states','relationship_states','unresolved_payoffs','active_causal_threads','remaining_episode_count','subplot_debt','character_debt','world_constraints','target_refs','source_hashes']
RKEYS=['schema','work_id','episode_no','scene_no','seq_id','characters','primary_pov','secondary_pov','character_states','relationship_states','event_context','info_context','plant_payoff_context','functional_propositions','source_refs']
PART={'PRIMARY','SECONDARY','SUPPORT','OPPOSITION','WITNESS','OFFSCREEN_CAUSAL'}
CANONICAL12=['경성스캔들','결혼못하는남자','공주가돌아왔다','내이름은김삼순','내여자친구는구미호','난폭한로맨스','강남엄마따라잡기','너의목소리가들려','개와늑대의시간','101번째프로포즈','가을동화','궁']

def sha_file(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def loadjl(p:Path):
    return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]

def locate_seqroot(root:Path)->Path:
    if root.name=='seqcard_ko': return root
    if (root/'seqcard_ko').is_dir(): return root/'seqcard_ko'
    hits=list(root.glob('*/seqcard_ko'))
    if len(hits)==1: return hits[0]
    raise RuntimeError(f'Cannot uniquely locate seqcard_ko under {root}; hits={len(hits)}')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',required=True)
    ap.add_argument('--work',default='all',help='work id, comma-separated ids, or all')
    ap.add_argument('--out',required=True)
    ap.add_argument('--canonical12-only',action='store_true',default=False)
    ap.add_argument('--require-v1-1',action='store_true',default=False,help='Require PlannerInput Canonical Profile V1.1 nested shape (recommended for new/reinforced works)')
    args=ap.parse_args()
    root=Path(args.root).resolve(); seq=locate_seqroot(root); reinf=seq/'reinforcement_v1'
    if args.work=='all':
        pbase=reinf/'planner_input'; rbase=reinf/'runtime_scene_projection'
        pworks={p.name for p in pbase.iterdir() if p.is_dir()} if pbase.exists() else set()
        rworks={p.name for p in rbase.iterdir() if p.is_dir()} if rbase.exists() else set()
        works=sorted(pworks & rworks)
        if args.canonical12_only: works=[w for w in CANONICAL12 if w in works]
    else:
        works=[x.strip() for x in args.work.split(',') if x.strip()]
    report={'schema':'DB98_PLANNER_RUNTIME_PORTABLE_VALIDATION_V1','root':str(root),'seqcard_root':str(seq),'works':{},'errors':[]}
    for w in works:
        errs=[]; warnings=[]
        pdir=reinf/'planner_input'/w; rdir=reinf/'runtime_scene_projection'/w; tdir=reinf/'thick_sequence'/w
        pfiles=sorted(pdir.glob('*.planner_input.json')); rfiles=sorted(rdir.glob('*.runtime_scene_projection.jsonl')); tfiles=sorted(tdir.glob('*.thick_sequence.jsonl'))
        if not pfiles: errs.append('NO_PLANNER_FILES')
        if not rfiles: errs.append('NO_RUNTIME_FILES')
        if not tfiles: errs.append('NO_THICK_FILES')
        eps=len(tfiles)
        if len(pfiles)!=eps: errs.append(f'PLANNER_FILE_COUNT:{len(pfiles)}!={eps}')
        if len(rfiles)!=eps: errs.append(f'RUNTIME_FILE_COUNT:{len(rfiles)}!={eps}')
        runtime_records=expected_scenes=0; nonempty_debt_eps=nonempty_thread_eps=0; profiles=set()
        for ep in range(1,eps+1):
            pf=pdir/f'{w}_{ep:02d}.planner_input.json'; rf=rdir/f'{w}_{ep:02d}.runtime_scene_projection.jsonl'; tf=tdir/f'{w}_{ep:02d}.thick_sequence.jsonl'
            if not (pf.exists() and rf.exists() and tf.exists()): errs.append(f'EP{ep:02d}:MISSING_FILE'); continue
            try: p=json.loads(pf.read_text(encoding='utf-8'))
            except Exception as e: errs.append(f'EP{ep:02d}:PLANNER_PARSE:{e}'); continue
            if list(p.keys())!=PKEYS: errs.append(f'EP{ep:02d}:PLANNER_TOP_KEYS')
            if p.get('schema')!='DB98_PLANNER_INPUT_RECORD_V1' or p.get('work_id')!=w or p.get('episode_no')!=ep: errs.append(f'EP{ep:02d}:PLANNER_ID')
            char_items=p.get('character_states',[]); rel_items=p.get('relationship_states',[]); thread_items=p.get('unresolved_payoffs',[])
            v11_char=all(set(x.keys())=={'character','state_label','state_delta','source_episode'} for x in char_items)
            v11_rel=all(set(x.keys())=={'char_a','char_b','relation_state','relation_delta','source_episode'} for x in rel_items)
            v11_thread=all(set(x.keys())=={'thread_id','status','through_episode'} for x in thread_items)
            planner_profile='V1_1' if v11_char and v11_rel and v11_thread else 'LEGACY_V1_COMPAT'; profiles.add(planner_profile)
            if args.require_v1_1 and planner_profile!='V1_1': errs.append(f'EP{ep:02d}:PLANNER_NESTED_PROFILE_NOT_V1_1')
            if ep==1:
                if p.get('previous_exit_state') is not None or any(p.get(k) for k in ['character_states','relationship_states','unresolved_payoffs','active_causal_threads','subplot_debt','character_debt']): errs.append('EP01:BOUNDARY_NOT_EMPTY')
            else:
                pe=p.get('previous_exit_state')
                if not isinstance(pe,dict) or pe.get('episode_no')!=ep-1: errs.append(f'EP{ep:02d}:PREV_EXIT')
                if planner_profile=='V1_1':
                    if any(x.get('source_episode')!=ep-1 for x in p.get('character_states',[])): errs.append(f'EP{ep:02d}:CHAR_FUTURE_LEAK')
                    if any(x.get('source_episode')!=ep-1 for x in p.get('relationship_states',[])): errs.append(f'EP{ep:02d}:REL_FUTURE_LEAK')
                    if any(x.get('through_episode',10**9)>ep-1 for x in p.get('unresolved_payoffs',[])): errs.append(f'EP{ep:02d}:THREAD_FUTURE_LEAK')
                    if any(x.get('available_through_episode',10**9)>ep-1 for x in p.get('active_causal_threads',[])): errs.append(f'EP{ep:02d}:CAUSAL_FUTURE_LEAK')
                else:
                    if 'LEGACY_PLANNER_PROFILE_NOT_RECERTIFIED_FOR_FUTURE_LEAK' not in warnings: warnings.append('LEGACY_PLANNER_PROFILE_NOT_RECERTIFIED_FOR_FUTURE_LEAK')
                chars=p.get('character_states',[]); rels=p.get('relationship_states',[])
                if len({x.get('character') for x in chars})!=len(chars): errs.append(f'EP{ep:02d}:DUP_CHAR')
                if len({tuple(sorted((x.get('char_a'),x.get('char_b')))) for x in rels})!=len(rels): errs.append(f'EP{ep:02d}:DUP_REL')
                if p.get('unresolved_payoffs') and not p.get('subplot_debt'): errs.append(f'EP{ep:02d}:EMPTY_SUBPLOT_DEBT_WITH_OPEN_THREADS')
                if p.get('character_states') and not p.get('character_debt'): errs.append(f'EP{ep:02d}:EMPTY_CHARACTER_DEBT_WITH_STATES')
                arc=seq/'authored_arc'/f'{w}_{ep-1:02d}.episodearc.json'
                if not arc.exists(): errs.append(f'EP{ep:02d}:PREVIOUS_ARC_MISSING')
                elif planner_profile=='V1_1' and p.get('source_hashes',{}).get('previous_episode_arc_sha256')!=sha_file(arc): errs.append(f'EP{ep:02d}:PREVIOUS_ARC_HASH_MISMATCH')
            if p.get('unresolved_payoffs'): nonempty_thread_eps+=1
            if p.get('subplot_debt') or p.get('character_debt'): nonempty_debt_eps+=1
            refs=p.get('target_refs',{})
            for rk in ['human_episode_arc','thick_sequence']:
                rel=refs.get(rk); rp=seq/rel if rel else None
                if not rel or not rp.exists(): errs.append(f'EP{ep:02d}:TARGET_REF_MISSING:{rk}')
            cp=refs.get('character_pressure')
            if cp is not None and not (seq/cp).exists(): errs.append(f'EP{ep:02d}:TARGET_REF_MISSING:character_pressure')
            try: runtime=loadjl(rf); thick=loadjl(tf)
            except Exception as e: errs.append(f'EP{ep:02d}:JSONL_PARSE:{e}'); continue
            runtime_records += len(runtime)
            scf=seq/'authored'/f'{w}_{ep:02d}.seqcard.jsonl'
            if not scf.exists(): errs.append(f'EP{ep:02d}:SCENECARD_MISSING'); continue
            sc=loadjl(scf); expected_scenes += len(sc)
            scene_to_seq={s:r for r in thick for s in r.get('member_scene_nos',[])}
            expected_scene_nos=[x.get('scene_no') for x in sc]; actual_scene_nos=[x.get('scene_no') for x in runtime]
            if len(runtime)!=len(sc): errs.append(f'EP{ep:02d}:RUNTIME_COUNT:{len(runtime)}!={len(sc)}')
            if sorted(actual_scene_nos)!=sorted(expected_scene_nos) or len(set(actual_scene_nos))!=len(actual_scene_nos): errs.append(f'EP{ep:02d}:SCENE_1_TO_1_COVERAGE')
            pchars={x.get('character'):x for x in p.get('character_states',[])}
            for rr in runtime:
                scno=rr.get('scene_no')
                if list(rr.keys())!=RKEYS: errs.append(f'EP{ep:02d}:RUNTIME_TOP_KEYS:{scno}'); continue
                if rr.get('schema')!='DB98_RUNTIME_SCENE_PROJECTION_V1' or rr.get('work_id')!=w or rr.get('episode_no')!=ep: errs.append(f'EP{ep:02d}:RUNTIME_ID:{scno}')
                tr=scene_to_seq.get(scno)
                if not tr or rr.get('seq_id')!=tr.get('seq_id'): errs.append(f'EP{ep:02d}:SEQ_MEMBERSHIP:{scno}'); continue
                cast=tr.get('cast',[]); chars=[c.get('character') for c in cast]
                if rr.get('characters')!=chars: errs.append(f'EP{ep:02d}:CAST_PARITY:{scno}')
                if rr.get('event_context')!=tr.get('event'): errs.append(f'EP{ep:02d}:EVENT_PARITY:{scno}')
                cexp=[{'character':c.get('character'),'sequence_function':c.get('desire_or_function'),'participation':c.get('participation'),'planning_boundary_state':pchars.get(c.get('character'))} for c in cast]
                if rr.get('character_states')!=cexp: errs.append(f'EP{ep:02d}:CHAR_STATE_PARITY:{scno}')
                if any(x.get('participation') not in PART for x in rr.get('character_states',[])): errs.append(f'EP{ep:02d}:PARTICIPATION_ENUM:{scno}')
                info=[x for x in tr.get('info_shift',[]) if scno in x.get('scene_nos',[])]; pay=[x for x in tr.get('plant_payoff',[]) if scno in x.get('scene_nos',[])]
                if rr.get('info_context')!=info: errs.append(f'EP{ep:02d}:INFO_PARITY:{scno}')
                if rr.get('plant_payoff_context')!=pay: errs.append(f'EP{ep:02d}:PAYOFF_PARITY:{scno}')
                note=next((x for x in tr.get('scene_notes',[]) if x.get('scene_no')==scno),None)
                if not note or rr.get('functional_propositions')!=note.get('functional_propositions'): errs.append(f'EP{ep:02d}:FUNCTIONAL_PROPOSITION_PARITY:{scno}')
                if not rr.get('source_refs'): errs.append(f'EP{ep:02d}:SOURCE_REF_EMPTY:{scno}')
        if eps>2 and nonempty_debt_eps==0:
            if args.require_v1_1 or profiles=={'V1_1'}: errs.append('SEASON_WIDE_DEBT_EMPTY')
            else: warnings.append('LEGACY_SEASON_WIDE_DEBT_EMPTY_REVIEW_REQUIRED')
        if eps>2 and nonempty_thread_eps==0: warnings.append('NO_OPEN_THREAD_AT_ANY_BOUNDARY_REVIEW_SEMANTICALLY')
        wr={'planner_profiles':sorted(profiles),'episodes':eps,'planner_files':len(pfiles),'runtime_files':len(rfiles),'runtime_scene_records':runtime_records,'expected_scenes':expected_scenes,'nonempty_thread_boundaries':nonempty_thread_eps,'nonempty_debt_boundaries':nonempty_debt_eps,'warnings':warnings,'errors':errs,'status':'PASS' if not errs else 'FAIL'}
        report['works'][w]=wr; report['errors'].extend([f'{w}:{e}' for e in errs])
    report['status']='PASS' if not report['errors'] else 'FAIL'
    out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2)); return 0 if report['status']=='PASS' else 1

if __name__=='__main__': sys.exit(main())
