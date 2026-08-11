#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reference builder for PlannerInput V1.1 and RuntimeSceneProjection V1.

This tool creates DERIVED execution files only. It does not alter Stage01-04,
CANONICAL THICK, authority pointers, or canonical manifests.

Example:
  python build_planner_runtime_reference.py \
    --root <EXTRACTED_DB_ROOT> --work 궁 \
    --baseline-sha256 <64hex> --out <STAGING_DIR>

After build, validate staging/integration with validate_planner_runtime.py.
"""
from __future__ import annotations
import argparse,json,hashlib,sys
from pathlib import Path
from collections import defaultdict

PART={'PRIMARY','SECONDARY','SUPPORT','OPPOSITION','WITNESS','OFFSCREEN_CAUSAL'}
def sha_file(p):
 h=hashlib.sha256();
 with open(p,'rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
 return h.hexdigest()
def loadjl(p): return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines() if x.strip()]
def writej(p,o): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def writejl(p,rows): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in rows),encoding='utf-8')
def locate(root):
 root=Path(root).resolve()
 if root.name=='seqcard_ko': return root
 if (root/'seqcard_ko').is_dir(): return root/'seqcard_ko'
 hits=list(root.glob('*/seqcard_ko'))
 if len(hits)==1:return hits[0]
 raise RuntimeError(f'Cannot locate unique seqcard_ko: {len(hits)}')
def kindprio(k): return {'REACTIVATION':9,'CLIFFHANGER':9,'ESCALATION':8,'REVERSAL':8,'HOOK':7,'CALLBACK':6,'LINK':5,'PLANT':4,'CONTINUE':4}.get(k,2)

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--work',required=True); ap.add_argument('--baseline-sha256',required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
 if len(args.baseline_sha256)!=64 or any(c not in '0123456789abcdefABCDEF' for c in args.baseline_sha256): raise SystemExit('--baseline-sha256 must be 64 hex chars')
 seq=locate(args.root); w=args.work; out=Path(args.out).resolve()/w
 tdir=seq/'reinforcement_v1/thick_sequence'/w; tfiles=sorted(tdir.glob('*.thick_sequence.jsonl')); eps=len(tfiles)
 if not eps: raise SystemExit(f'No CANONICAL THICK files for {w}')
 thick_by_ep={}; thread_events=defaultdict(list)
 for tf in tfiles:
  rows=loadjl(tf); ep=rows[0]['episode_no']; thick_by_ep[ep]=rows
  for r in rows:
   for order,p in enumerate(r.get('plant_payoff',[])):
    tid=p.get('thread_id')
    if tid: thread_events[tid].append({'episode_no':ep,'seq_index':r['seq_index'],'order':order,'kind':p.get('kind'),'statement':p.get('statement','')})
 for tid in thread_events: thread_events[tid].sort(key=lambda x:(x['episode_no'],x['seq_index'],x['order']))
 ph={}; rh={}; rcount=0
 for ep in range(1,eps+1):
  cur_arc=seq/'authored_arc'/f'{w}_{ep:02d}.episodearc.json'
  if not cur_arc.exists(): raise SystemExit(f'Missing {cur_arc}')
  if ep==1:
   prev=None; cs=[]; rs=[]; opens=[]; sdebt=[]; cdebt=[]; sh={'baseline_artifact_sha256':args.baseline_sha256.lower()}
  else:
   pa=seq/'authored_arc'/f'{w}_{ep-1:02d}.episodearc.json'; arc=json.loads(pa.read_text(encoding='utf-8'))
   prev={'episode_no':ep-1,'exit_state':arc['exit_state'],'central_conflict_axis':arc['central_conflict_axis'],'episode_function':arc['episode_function']}
   ctmp={}
   for x in loadjl(seq/'authored_chararc'/f'{w}_{ep-1:02d}.chararc.jsonl'): ctmp[x['character']]={'character':x['character'],'state_label':x['state_label'],'state_delta':x['state_delta'],'source_episode':ep-1}
   cs=list(ctmp.values()); rtmp={}
   for x in loadjl(seq/'authored_relarc'/f'{w}_{ep-1:02d}.relarc.jsonl'):
    k=tuple(sorted((x['char_a'],x['char_b']))); rtmp[k]={'char_a':x['char_a'],'char_b':x['char_b'],'relation_state':x['relation_state'],'relation_delta':x['relation_delta'],'source_episode':ep-1}
   rs=list(rtmp.values()); cand=[]
   for tid,evs in thread_events.items():
    hist=[e for e in evs if e['episode_no']<=ep-1]
    if not hist or hist[-1]['kind']=='PAYOFF': continue
    last=hist[-1]; bonus=(18 if tid.startswith(('CHARARC:','RELARC:')) else 0)+(10 if '_local_' not in tid else -12)+(16 if len(hist)>=2 else 0)
    cand.append((last['episode_no']*10+min(len(hist),5)*7+kindprio(last['kind'])+bonus,tid,last))
   cand=sorted(cand,key=lambda x:(-x[0],x[1]))[:24]
   opens=[{'thread_id':tid,'status':'OPEN_AT_PLANNING_BOUNDARY','through_episode':ep-1} for _,tid,_ in cand]
   sdebt=[{'thread':tid,'debt':last['statement'].strip()+' — 직전 회차까지 이 장기축의 결말/회수가 확정되지 않았다.'} for _,tid,last in cand[:8]]
   cdebt=[{'character':x['character'],'debt':f"{x['state_label']}: {x['state_delta']} 대상 회차에서 이 상태가 어떤 선택·변화로 이어질지는 아직 미결이다."} for x in cs]
   sh={'baseline_artifact_sha256':args.baseline_sha256.lower(),'previous_episode_arc_sha256':sha_file(pa)}
  active=[{'thread_id':x['thread_id'],'available_through_episode':ep-1} for x in opens] if ep>1 else []
  cp=seq/'reinforcement_v1/character_pressure'/w/f'{w}_{ep:02d}.character_pressure.jsonl'
  refs={'human_episode_arc':f'authored_arc/{w}_{ep:02d}.episodearc.json','thick_sequence':f'reinforcement_v1/thick_sequence/{w}/{w}_{ep:02d}.thick_sequence.jsonl','character_pressure':f'reinforcement_v1/character_pressure/{w}/{w}_{ep:02d}.character_pressure.jsonl' if cp.exists() else None}
  p={'schema':'DB98_PLANNER_INPUT_RECORD_V1','work_id':w,'episode_no':ep,'previous_exit_state':prev,'character_states':cs,'relationship_states':rs,'unresolved_payoffs':opens,'active_causal_threads':active,'remaining_episode_count':eps-ep,'subplot_debt':sdebt,'character_debt':cdebt,'world_constraints':['기존 Stage01~04, SourceLock, 인간 시퀀스 경계를 보존한다.','대상 회차에서 처음 드러나는 사실을 PlannerInput의 선행 상태에 넣지 않는다.','PlannerInput은 직전 회차까지의 상태와 열린 장기축만 사용하며 미래 회차의 사실을 역류시키지 않는다.','Thick Sequence는 target/runtime context이며 PlannerInput의 선행 사실을 새로 창작하는 근거로 사용하지 않는다.'],'target_refs':refs,'source_hashes':sh}
  pf=out/'planner_input'/f'{w}_{ep:02d}.planner_input.json'; writej(pf,p); ph[pf.name]=sha_file(pf)
  pchars={x['character']:x for x in cs}; runtime=[]; seen=[]
  for tr in thick_by_ep[ep]:
   cast=tr.get('cast',[]); chars=[x['character'] for x in cast]; prim=[x['character'] for x in cast if x.get('participation')=='PRIMARY']; primary=prim[0] if prim else (chars[0] if chars else None); secondary=prim[1:]
   cstates=[{'character':x['character'],'sequence_function':x['desire_or_function'],'participation':x['participation'],'planning_boundary_state':pchars.get(x['character'])} for x in cast]
   notes={x['scene_no']:x for x in tr.get('scene_notes',[])}
   for sc in tr['member_scene_nos']:
    note=notes[sc]; info=[x for x in tr.get('info_shift',[]) if sc in x.get('scene_nos',[])]; pay=[x for x in tr.get('plant_payoff',[]) if sc in x.get('scene_nos',[])]; refs2=[]; keys=set()
    for e in note.get('evidence_refs',[])+tr.get('evidence_refs',[]):
     k=(e.get('kind'),e.get('ref'))
     if k not in keys: keys.add(k); refs2.append(f"{e.get('kind')}:{e.get('ref')}")
    runtime.append({'schema':'DB98_RUNTIME_SCENE_PROJECTION_V1','work_id':w,'episode_no':ep,'scene_no':sc,'seq_id':tr['seq_id'],'characters':chars,'primary_pov':primary,'secondary_pov':secondary,'character_states':cstates,'relationship_states':rs,'event_context':tr['event'],'info_context':info,'plant_payoff_context':pay,'functional_propositions':note['functional_propositions'],'source_refs':refs2}); seen.append(sc)
  sc=loadjl(seq/'authored'/f'{w}_{ep:02d}.seqcard.jsonl'); exp=[x['scene_no'] for x in sc]
  if sorted(seen)!=sorted(exp) or len(set(seen))!=len(seen): raise SystemExit(f'EP{ep}: scene coverage mismatch')
  rf=out/'runtime_scene_projection'/f'{w}_{ep:02d}.runtime_scene_projection.jsonl'; writejl(rf,runtime); rh[rf.name]=sha_file(rf); rcount+=len(runtime)
 manifest={'schema':'DB98_PLANNER_RUNTIME_WORK_MANIFEST_V1','work_id':w,'status':'STAGING_DERIVED_RUNTIME','planner_schema':'DB98_PLANNER_INPUT_RECORD_V1','planner_profile':'PLANNER_INPUT_CANONICAL_PROFILE_V1_1','runtime_schema':'DB98_RUNTIME_SCENE_PROJECTION_V1','planner_episode_files':eps,'runtime_episode_files':eps,'runtime_scene_records':rcount,'planner_hashes':ph,'runtime_hashes':rh,'baseline_artifact_sha256':args.baseline_sha256.lower(),'next_action':'RUN_VALIDATOR_THEN_INTEGRATE'}
 writej(out/'planner_runtime_manifest.json',manifest); print(json.dumps(manifest,ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': sys.exit(main())
