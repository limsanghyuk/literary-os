#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path
from collections import defaultdict

PRESENT={'ONSCREEN','VOICE_ONLY','PHONE_OR_REMOTE','ARCHIVAL_OR_MEMORY'}
CAST_KEYS=set('work_id episode_no scene_no character_key entity_id presence_mode focality speaking_status evidence_ref by'.split())
LOAD_KEYS=set('work_id episode_no character_key entity_id canonical_name present_scene_count focal_scene_count speaking_scene_count present_sequence_count scene_share focal_share scene_share_band act_placement first_scene_no last_scene_no max_absence_gap by'.split())

def jl(p): return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines() if x.strip()]
def band(s): return 'DOMINANT' if s>=.50 else 'MAJOR' if s>=.20 else 'MINOR' if s>=.05 else 'CAMEO'
def epno(work,p):
 m=re.match(re.escape(work)+r'_(\d{2})\.',Path(p).name); return int(m.group(1)) if m else None

def canonical(v):
 if isinstance(v,dict): return {str(k):canonical(vv) for k,vv in sorted(v.items(),key=lambda x:str(x[0]))}
 if isinstance(v,float): return round(v,4)
 return v

def expected(root,work,ep):
 bridge={r['character_key']:r for r in jl(root/'authored_bridge'/f'{work}.bridge.jsonl')}
 sc=jl(root/'authored'/f'{work}_{ep:02d}.seqcard.jsonl'); cast=jl(root/'authored_cast'/f'{work}_{ep:02d}.cast.jsonl')
 seqs=jl(root/'authored_seq'/f'{work}_{ep:02d}.seqblueprint.jsonl'); arc=json.loads((root/'authored_arc'/f'{work}_{ep:02d}.episodearc.json').read_text(encoding='utf-8'))
 s2q={int(sn):int(s['seq_index']) for s in seqs for sn in s['member_scene_nos']}
 q2a={}
 for idx,a in enumerate(arc['act_structure'],1):
  lo,hi=map(int,a['seq_span'])
  for q in range(lo,hi+1):q2a[q]=f'ACT{idx}'
 agg=defaultdict(lambda:{'p':set(),'f':set(),'sp':set(),'q':set(),'a':defaultdict(int)})
 for c in cast:
  if c['presence_mode'] not in PRESENT:continue
  d=agg[c['character_key']];sn=int(c['scene_no'])
  if sn not in d['p']:
   d['p'].add(sn);q=s2q.get(sn)
   if q is not None:
    d['q'].add(q);act=q2a.get(q)
    if act is not None:d['a'][act]+=1
  if c['focality']=='PRIMARY':d['f'].add(sn)
  if c['speaking_status']=='SPEAKING':d['sp'].add(sn)
 out=[];n=len(sc)
 for ck,d in agg.items():
  p=sorted(d['p']);b=bridge.get(ck,{})
  gaps=[p[i]-p[i-1]-1 for i in range(1,len(p))]
  out.append({'work_id':work,'episode_no':ep,'character_key':ck,'entity_id':b.get('entity_id',next((x.get('entity_id') for x in cast if x['character_key']==ck),None)),'canonical_name':b.get('canonical_name',ck.split(':')[-1]),'present_scene_count':len(p),'focal_scene_count':len(d['f']),'speaking_scene_count':len(d['sp']),'present_sequence_count':len(d['q']),'scene_share':round(len(p)/n,4),'focal_share':round(len(d['f'])/n,4),'scene_share_band':band(len(p)/n),'act_placement':dict(sorted(d['a'].items())),'first_scene_no':p[0],'last_scene_no':p[-1],'max_absence_gap':max(gaps,default=0)})
 return {r['character_key']:r for r in out},cast,{int(r['scene_no']) for r in sc},bridge

def run(root,work):
 errors=[];counts={'episodes':0,'cast_rows':0,'load_rows':0,'A6_present_focal_mismatch':0,'A7_other_mismatch':0}
 eps=sorted(epno(work,p) for p in (root/'authored').glob(f'{work}_*.seqcard.jsonl') if epno(work,p) is not None)
 for ep in eps:
  exp,cast,scenes,bridge=expected(root,work,ep); counts['episodes']+=1;counts['cast_rows']+=len(cast)
  seen=set()
  for i,c in enumerate(cast,1):
   if set(c)!=CAST_KEYS:errors.append(f'EP{ep:02d} cast row {i} keyset')
   if c.get('work_id')!=work or int(c.get('episode_no',-1))!=ep:errors.append(f'EP{ep:02d} cast grain row {i}')
   if int(c.get('scene_no',-1)) not in scenes:errors.append(f'EP{ep:02d} cast scene FK row {i}')
   if c.get('character_key') not in bridge:errors.append(f'EP{ep:02d} cast bridge FK {c.get("character_key")}')
   key=(c.get('scene_no'),c.get('character_key'))
   if key in seen:errors.append(f'EP{ep:02d} duplicate cast grain {key}')
   seen.add(key)
  lp=root/'derived_character_load'/f'{work}_{ep:02d}.load.jsonl'; actual=jl(lp);counts['load_rows']+=len(actual)
  amap={r['character_key']:r for r in actual}
  if set(amap)!=set(exp):errors.append(f'EP{ep:02d} load character set mismatch')
  for ck,e in exp.items():
   a=amap.get(ck)
   if not a:continue
   if set(a)!=LOAD_KEYS:errors.append(f'EP{ep:02d} load keyset {ck}')
   for k,v in e.items():
    if canonical(a.get(k))!=canonical(v):
     if k in {'present_scene_count','focal_scene_count'}:counts['A6_present_focal_mismatch']+=1
     else:counts['A7_other_mismatch']+=1
     errors.append(f'EP{ep:02d} {ck} {k}: {a.get(k)!r} != {v!r}')
 status='PASS' if not errors else 'FAIL'
 return {'schema':'EXT6_PHASE01_DERIVED_GATE_REPORT_V1_0_1','work_id':work,'status':status,'errors':errors,'counts':counts,'rules':{'present_modes':sorted(PRESENT),'referenced_only_counted':False,'focality':'PRIMARY_ONLY','act_key_comparison':'STRING_NORMALIZED'}},0 if not errors else 1

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--work',required=True);ap.add_argument('--json-out');a=ap.parse_args()
 r,c=run(Path(a.root),a.work);s=json.dumps(r,ensure_ascii=False,indent=2)
 if a.json_out:Path(a.json_out).write_text(s+'\n',encoding='utf-8')
 print(s);raise SystemExit(c)
if __name__=='__main__':main()
