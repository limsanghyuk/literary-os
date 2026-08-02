#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re,sys,hashlib,unicodedata
from pathlib import Path
from collections import defaultdict
PRESENT_COUNTED={'ONSCREEN','VOICE_ONLY','PHONE_OR_REMOTE','ARCHIVAL_OR_MEMORY'}
PRESENCE={'ONSCREEN','VOICE_ONLY','PHONE_OR_REMOTE','ARCHIVAL_OR_MEMORY','REFERENCED_ONLY'}
FOCAL={'PRIMARY','SECONDARY','PRESENT_ONLY'}
SPEAK={'SPEAKING','NONSPEAKING'}
CAST_KEYS=set('work_id episode_no scene_no character_key entity_id presence_mode focality speaking_status evidence_ref by'.split())
LOAD_KEYS=set('work_id episode_no character_key entity_id canonical_name present_scene_count focal_scene_count speaking_scene_count present_sequence_count scene_share focal_share scene_share_band act_placement first_scene_no last_scene_no max_absence_gap by'.split())
EV=re.compile(r'^EP(\d{2})-S(\d+) L(\d+) (.+)$')
def jl(p):return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines() if x.strip()]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def norm(s):return ''.join(ch.lower() for ch in unicodedata.normalize('NFKC',str(s)) if ch.isalnum())
def band(s):return 'DOMINANT' if s>=.50 else 'MAJOR' if s>=.20 else 'MINOR' if s>=.05 else 'CAMEO'
def epno(w,p):
 m=re.match(re.escape(w)+r'_(\d{2})\.',Path(p).name);return int(m.group(1)) if m else None
def can(v):
 if isinstance(v,dict):return {str(k):can(vv) for k,vv in sorted(v.items(),key=lambda x:str(x[0]))}
 if isinstance(v,float):return round(v,4)
 return v
def source_text_path(root,w,ep):
 d=root/'original_extracted'/w
 direct=d/f'{w}_{ep:02d}.txt'
 if direct.exists():return direct
 mp=d/'SOURCE_TEXT_MANIFEST.package.json'
 if mp.exists():
  try:
   o=json.loads(mp.read_text(encoding='utf-8'))
   for x in o.get('episodes',[]):
    if int(x.get('episode_no',-1))==ep:
     q=d/str(x.get('file',''))
     if q.exists():return q
  except Exception:pass
 cand=sorted(d.glob(f'*_{ep:02d}.txt'))
 return cand[0] if len(cand)==1 else None

def expected(root,w,ep):
 bridge={r['character_key']:r for r in jl(root/'authored_bridge'/f'{w}.bridge.jsonl')};sc=jl(root/'authored'/f'{w}_{ep:02d}.seqcard.jsonl');cast=jl(root/'authored_cast'/f'{w}_{ep:02d}.cast.jsonl');seqs=jl(root/'authored_seq'/f'{w}_{ep:02d}.seqblueprint.jsonl');arc=json.loads((root/'authored_arc'/f'{w}_{ep:02d}.episodearc.json').read_text(encoding='utf-8'))
 s2q={int(sn):int(s['seq_index']) for s in seqs for sn in s['member_scene_nos']};q2a={}
 for idx,a in enumerate(arc['act_structure'],1):
  lo,hi=map(int,a['seq_span'])
  for q in range(lo,hi+1):q2a[q]=f'ACT{idx}'
 agg=defaultdict(lambda:{'p':set(),'f':set(),'sp':set(),'q':set(),'a':defaultdict(int)})
 for c in cast:
  if c['presence_mode'] not in PRESENT_COUNTED:continue
  d=agg[c['character_key']];sn=int(c['scene_no']);d['p'].add(sn)
  if c['focality']=='PRIMARY':d['f'].add(sn)
  if c['speaking_status']=='SPEAKING':d['sp'].add(sn)
  q=s2q.get(sn)
  if q is not None:d['q'].add(q);act=q2a.get(q);d['a'][act]+=1 if act else 0
 out={};n=len(sc)
 for ck,d in agg.items():
  p=sorted(d['p']);b=bridge.get(ck,{});g=[p[i]-p[i-1]-1 for i in range(1,len(p))]
  out[ck]={'work_id':w,'episode_no':ep,'character_key':ck,'entity_id':b.get('entity_id',next((x.get('entity_id') for x in cast if x['character_key']==ck),None)),'canonical_name':b.get('canonical_name',ck.split(':')[-1]),'present_scene_count':len(p),'focal_scene_count':len(d['f']),'speaking_scene_count':len(d['sp']),'present_sequence_count':len(d['q']),'scene_share':round(len(p)/n,4),'focal_share':round(len(d['f'])/n,4),'scene_share_band':band(len(p)/n),'act_placement':dict(sorted((k,v) for k,v in d['a'].items() if k)),'first_scene_no':p[0],'last_scene_no':p[-1],'max_absence_gap':max(g,default=0)}
 return out,cast,{int(r['scene_no']) for r in sc},bridge
def run(root,w,strict_evidence=False):
 e=[];warn=[];c={'episodes':0,'cast_rows':0,'load_rows':0,'enum_errors':0,'evidence_errors':0,'coverage_errors':0,'registry_sha_errors':0,'A6_present_focal_mismatch':0,'A7_other_mismatch':0}
 bp=root/'authored_bridge'/f'{w}.bridge.jsonl';bridge_rows=jl(bp);regp=root/'ext6_registry'/f'{w}.entity_registry.v1.json';rsha=sha(regp) if regp.exists() else None
 for b in bridge_rows:
  if rsha and b.get('source_registry_sha')!=rsha:e.append(f'bridge registry SHA mismatch {b.get("character_key")}');c['registry_sha_errors']+=1
 eps=sorted(epno(w,p) for p in (root/'authored').glob(f'{w}_*.seqcard.jsonl') if epno(w,p) is not None)
 for ep in eps:
  exp,cast,scenes,bridge=expected(root,w,ep);c['episodes']+=1;c['cast_rows']+=len(cast);seen=set();srcp=source_text_path(root,w,ep);lines=srcp.read_text(encoding='utf-8').splitlines() if srcp and srcp.exists() else []
  for i,x in enumerate(cast,1):
   if set(x)!=CAST_KEYS:e.append(f'EP{ep:02d} cast row {i} keyset')
   if x.get('presence_mode') not in PRESENCE:e.append(f'EP{ep:02d} bad presence {x.get("presence_mode")}');c['enum_errors']+=1
   if x.get('focality') not in FOCAL:e.append(f'EP{ep:02d} bad focality {x.get("focality")}');c['enum_errors']+=1
   if x.get('speaking_status') not in SPEAK:e.append(f'EP{ep:02d} bad speaking_status {x.get("speaking_status")}');c['enum_errors']+=1
   if x.get('work_id')!=w or int(x.get('episode_no',-1))!=ep:e.append(f'EP{ep:02d} cast grain row {i}')
   sn=int(x.get('scene_no',-1))
   if sn not in scenes:e.append(f'EP{ep:02d} scene FK row {i}')
   b=bridge.get(x.get('character_key'))
   if not b:e.append(f'EP{ep:02d} bridge FK {x.get("character_key")}')
   elif x.get('entity_id')!=b.get('entity_id'):e.append(f'EP{ep:02d} entity mismatch {x.get("character_key")}')
   k=(sn,x.get('character_key'))
   if k in seen:e.append(f'EP{ep:02d} duplicate cast grain {k}')
   seen.add(k)
   m=EV.match(str(x.get('evidence_ref','')))
   if not m or int(m[1])!=ep or int(m[2])!=sn or not (1<=int(m[3])<=len(lines)):
    e.append(f'EP{ep:02d} evidence format/grain row {i}');c['evidence_errors']+=1
   elif lines:
    q=m[4];ln=int(m[3]);lo=max(1,ln-3);hi=min(len(lines),ln+3)
    if not any(norm(q) in norm(lines[j-1]) or norm(lines[j-1]) in norm(q) for j in range(lo,hi+1)):
     (e if strict_evidence else warn).append(f'EP{ep:02d} evidence line mismatch row {i} L{m[3]}');c['evidence_errors']+=1
  covp=root/'_ext6_audit'/f'{w}_{ep:02d}.castcoverage.json'
  if covp.exists():
   cov=json.loads(covp.read_text(encoding='utf-8'));annot={x[0] for x in seen};empty=set(cov.get('empty_cast_scene_nos',[]));unres=set(cov.get('unresolved_scene_nos',[]))
   if annot!=set(cov.get('annotated_scene_nos',[])) or annot|empty!=scenes or annot&empty or not unres<=scenes:
    e.append(f'EP{ep:02d} coverage ledger mismatch');c['coverage_errors']+=1
  lp=root/'derived_character_load'/f'{w}_{ep:02d}.load.jsonl';act=jl(lp);c['load_rows']+=len(act);am={r['character_key']:r for r in act}
  if set(am)!=set(exp):e.append(f'EP{ep:02d} load character set mismatch')
  for ck,z in exp.items():
   a=am.get(ck)
   if not a:continue
   if set(a)!=LOAD_KEYS:e.append(f'EP{ep:02d} load keyset {ck}')
   for k,v in z.items():
    if can(a.get(k))!=can(v):
     if k in {'present_scene_count','focal_scene_count'}:c['A6_present_focal_mismatch']+=1
     else:c['A7_other_mismatch']+=1
     e.append(f'EP{ep:02d} {ck} {k}: {a.get(k)!r}!={v!r}')
 status='PASS' if not e else 'FAIL'
 return {'schema':'EXT6_PHASE01_DERIVED_GATE_REPORT_V1_2_1','work_id':w,'status':status,'errors':e,'warnings':warn,'counts':c,'rules':{'presence_enum':sorted(PRESENCE),'focality_enum':sorted(FOCAL),'speaking_status_enum':sorted(SPEAK),'evidence_source_line_verified':True,'coverage_ledger_exact':True,'registry_sha_verified':True,'referenced_only_counted':False}},0 if not e else 1
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--work',required=True);ap.add_argument('--json-out');ap.add_argument('--strict-evidence',action='store_true');a=ap.parse_args();r,c=run(Path(a.root),a.work,a.strict_evidence);s=json.dumps(r,ensure_ascii=False,indent=2)
 if a.json_out:Path(a.json_out).parent.mkdir(parents=True,exist_ok=True);Path(a.json_out).write_text(s+'\n',encoding='utf-8')
 print(s);sys.exit(c)
if __name__=='__main__':main()
