#!/usr/bin/env python3
"""EXT6 Phase02 V1.0.2 deterministic gate. Exit 0 PASS, 1 FAIL, 3 HOLD."""
import argparse,hashlib,json,re,sys,unicodedata,math
from pathlib import Path
from collections import Counter,defaultdict
MODES={'EP01_02_BLIND','FULL_READ','PLAN_DOCUMENT'}
PRESENT={'ONSCREEN','VOICE_ONLY','PHONE_OR_REMOTE','ARCHIVAL_OR_MEMORY'}
IND={'center_count','opposition_persistence','conflict_persist','ending_direction','cost_realized'}
END={'ACHIEVE','ACHIEVE_WITH_COST','FAIL','FAIL_BUT_TRANSFORM','REFUSE','AMBIGUOUS'}
SCOPES={'SOCIAL','INSTITUTIONAL','PHYSICAL','SUPERNATURAL','ECONOMIC','RELATIONAL','PROFESSIONAL','LEGAL','CULTURAL','OTHER'}
CT={'IDENTITY','RELATIONSHIP','STATUS','SAFETY','MORAL','MATERIAL','TIME','LIFE','MIXED','NONE','AMBIGUOUS'}
CB={'PROTAGONIST','ALLY','RELATIONSHIP','COMMUNITY','ANTAGONISTIC_FORCE','MULTIPLE','NONE','AMBIGUOUS'}
GENERIC={'사람','사람들','학생','학생들','남자','여자','남학생','여학생','피고인','피고인2','변호사','검사','판사','판사들','배심원','배심원들','배심들','배석들','경찰','형사','교도관','경위','실무관','기자','간호사','의사','의사2','면접관','면접관들','면접관1','면접관2','직원','직원들','손님','주인','아저씨','아줌마','아줌마2','아줌마3','친구','선생','선생님','인동','모두','상대','안내','앵커','아나운서','승객','주민','지원자1','지원자2','동기1','사촌1','사촌2'}
SEED=set('work_id derivation_mode read_span evidenced_initial_configuration evidenced_world_constraints evidenced_opening_disturbance judged_logline judged_central_lack judged_governing_question judged_central_opposition_axis judged_ending_direction judged_cost_structure contract_version by'.split())
ADM=set('work_id derivation_mode compatible_work_ids compatibility_count alternative_structures specificity_violations verdict'.split())
RUN=set('work_id derivation_mode read_span run_id provider model_id source_file_refs source_sha256s downstream_layers_blocked downstream_blocklist cross_provider_outputs_blocked prior_mode_ref sealed_at content_sha256 by'.split())
PRED=set('work_id derivation_mode indicator predicted_value observed_value observation_source match corpus_prior by'.split())
CONT=set('work_id mode_b_ref mode_c_ref field_level_diff diverged_fields mode_b_prediction_accuracy mode_c_prediction_accuracy leakage_estimate'.split())
EV=re.compile(r'^EP(?P<ep>\d{2})-S(?P<sc>\d+)\s+L(?P<ln>\d+)\s+(?P<q>.+)$')
def norm(x):return re.sub(r'\s+','',unicodedata.normalize('NFKC',str(x))).lower()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rj(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def rjl(p):return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines() if x.strip()]
def exact(e,label,o,k):
 if not isinstance(o,dict) or set(o)!=k:e.append(f'[SEED-A] {label} exact-key mismatch');return False
 return True
def corpus(p):
 o=rj(p);w=o.get('works') if isinstance(o,dict) else None
 if not isinstance(w,list):raise ValueError('corpus index missing works')
 s={x.get('work_id') if isinstance(x,dict) else x for x in w};s.discard(None)
 if not s:raise ValueError('corpus index empty')
 return s
def source(root,sroot,ref,w,ep):
 for p in (sroot/ref,sroot/'original_extracted'/w/f'{w}_{ep:02d}.txt',root/'original_extracted'/w/f'{w}_{ep:02d}.txt'):
  if p.exists():return p
def centers(root,w):
 scenes=set();pres=defaultdict(set)
 for p in (root/'authored').glob(f'{w}_*.seqcard.jsonl'):
  m=re.match(re.escape(w)+r'_(\d{2})\.seqcard\.jsonl$',p.name)
  if m:
   ep=int(m.group(1));scenes|={(ep,int(x['scene_no'])) for x in rjl(p)}
 for p in (root/'authored_cast').glob(f'{w}_*.cast.jsonl'):
  for x in rjl(p):
   if x.get('presence_mode') in PRESENT:pres[x['character_key']].add((int(x['episode_no']),int(x['scene_no'])))
 if not scenes:raise ValueError('no scenes')
 shares={k:len(v)/len(scenes) for k,v in pres.items()};c={k:v for k,v in shares.items() if v>=.2}
 return len(scenes),c
def opposition(root,w,c):
 br=rjl(root/'authored_bridge'/f'{w}.bridge.jsonl');alias={};coll={}
 names={x['character_key']:x['canonical_name'] for x in br}
 for x in br:
  for n in [x.get('canonical_name')]+list(x.get('aliases') or []):
   if not n:continue
   z=norm(n);k=x['character_key']
   if z in alias and alias[z]!=k:coll.setdefault(z,set()).update((alias[z],k))
   else:alias[z]=k
 pair=set(k for k,_ in sorted(c.items(),key=lambda q:-q[1])[:2]);states=[];eps=set();unres=0
 for p in sorted((root/'authored_relarc').glob(f'{w}_*.relarc.jsonl')):
  m=re.match(re.escape(w)+r'_(\d{2})\.relarc\.jsonl$',p.name)
  if not m:continue
  ep=int(m.group(1))
  for x in rjl(p):
   a=alias.get(norm(x.get('char_a','')));b=alias.get(norm(x.get('char_b','')))
   if a is None or b is None:unres+=1;continue
   if {a,b}==pair:eps.add(ep);states.append((ep,x.get('relation_state')))
 total=len(list((root/'authored').glob(f'{w}_*.seqcard.jsonl')));ratio=len(eps)/total if total else 0
 val='HIGH' if ratio>=.75 and states and states[0][1]!=states[-1][1] else 'LOW'
 return val,{'center_pair_keys':sorted(pair),'center_pair':[names.get(k,k) for k in sorted(pair)],'coverage':len(eps),'episodes_total':total,'coverage_ratio':round(ratio,4),'unresolved_relation_records':unres,'alias_collisions':{k:sorted(v) for k,v in coll.items()}}
def conflict(root,w):
 o=rj(root/'authored'/f'{w}_full_series_arc.json');n=int(o['episodes_total']);ss=o['season_structure'];a=min(int(x['episode_span'][0]) for x in ss);b=max(int(x['episode_span'][1]) for x in ss)
 return ('SEASON_LONG' if a<=max(2,math.ceil(n*.25)) and b==n else 'LIMITED'),{'first':a,'last':b,'episodes_total':n}
def terminal(root,w):
 p=root/'validation'/'phase02_indicator_evidence'/f'{w}.indicator_evidence.json'
 if not p.exists():raise ValueError('terminal audit missing')
 o=rj(p);text=[]
 for s in o.get('sources',[]):
  q=root.parent/s['path'] if str(s['path']).startswith('seqcard_ko/') else root/s['path']
  if not q.exists() or sha(q)!=s['sha256']:raise ValueError('terminal audit source/hash mismatch')
  text+=([q.read_text(encoding='utf-8')] if q.suffix!='.jsonl' else [json.dumps(x,ensure_ascii=False) for x in rjl(q)])
 joined='\n'.join(text)
 if o.get('status')!='PASS' or any(x not in joined for x in o.get('decision',{}).get('support_phrases',[])):raise ValueError('terminal audit unsupported')
 return o
def verdict(n):return 'TOO_SPECIFIC' if n==0 else 'ADMISSIBLE' if n<=9 else 'REVIEW' if n<=29 else 'TOO_VAGUE'
def run(root,w,mode,sroot,cidx,phase):
 e=[];h=[];warn=[];count={}
 try:works=corpus(cidx)
 except Exception as x:works=set();h.append(f'[SEED-A] corpus index unavailable: {x}')
 sp=root/'advisory_seed'/f'{w}.{mode}.seed.json';ap=root/'advisory_seed_admissibility'/f'{w}.{mode}.adm.json';rp=root/'advisory_seed_runs'/f'{w}.{mode}.run.json'
 if not all(p.exists() for p in (sp,ap,rp)):return {'schema':'EXT6_PHASE02_SEED_GATE_REPORT_V1_0_2','work_id':w,'derivation_mode':mode,'phase':phase,'status':'FAIL','errors':['missing records'],'holds':h,'warnings':warn,'counts':count},1
 s,a,m=rj(sp),rj(ap),rj(rp);exact(e,'seed',s,SEED);exact(e,'admissibility',a,ADM);exact(e,'run',m,RUN)
 if any(x.get('work_id')!=w or x.get('derivation_mode')!=mode for x in (s,a,m)):e.append('[SEED-A] grain mismatch')
 span=s.get('read_span')
 if not isinstance(span,list) or span!=sorted(set(span)):e.append('[SEED-A] read_span invalid');span=[]
 if mode=='EP01_02_BLIND' and span!=[1,2]:e.append('[SEED-A] blind span invalid')
 if m.get('read_span')!=span:e.append('[SEED-A] manifest span mismatch')
 br=rjl(root/'authored_bridge'/f'{w}.bridge.jsonl');bkeys={x['character_key'] for x in br};refs=[]
 for x in s.get('evidenced_initial_configuration',[]):
  if set(x)!=set('character_key initial_position initial_relation_axis evidence_ref'.split()):e.append('[SEED-A] initial exact-key mismatch')
  else:
   if x['character_key'] not in bkeys:e.append('[SEED-A] bridge FK missing')
   refs.append(x['evidence_ref'])
 for x in s.get('evidenced_world_constraints',[]):
  if set(x)!=set('rule scope evidence_ref'.split()) or x.get('scope') not in SCOPES:e.append('[SEED-A] world constraint invalid')
  else:refs.append(x['evidence_ref'])
 d=s.get('evidenced_opening_disturbance',{})
 if set(d)!=set('summary scene_no evidence_ref'.split()):e.append('[SEED-A] disturbance invalid')
 else:refs.append(d['evidence_ref'])
 if s.get('judged_ending_direction') not in END:e.append('[SEED-A] ending enum invalid')
 cost=s.get('judged_cost_structure',{})
 if set(cost)!=set('cost_type cost_bearer cost_summary'.split()) or cost.get('cost_type') not in CT or cost.get('cost_bearer') not in CB:e.append('[SEED-A] cost invalid')
 judged=' '.join(str(s.get(k,'')) for k in ('judged_logline','judged_central_lack','judged_governing_question','judged_central_opposition_axis','judged_cost_structure'));nj=norm(judged)
 for x in br:
  n=x.get('canonical_name','')
  if n not in GENERIC and len(norm(n))>=2 and norm(n) in nj:e.append(f'[SEED-C] proper name leakage {n}');break
 ids=a.get('compatible_work_ids',[])
 if not isinstance(ids,list) or len(ids)!=len(set(ids)):e.append('[SEED-A] compatible list invalid');ids=[]
 if w in ids:e.append('[SEED-C] compatible list contains self')
 if a.get('compatibility_count')!=len(ids):e.append('[SEED-A] compatibility count mismatch')
 if works and set(ids)-works:e.append('[SEED-A] corpus FK missing')
 if a.get('verdict')!=verdict(len(ids)) or a.get('verdict')!='ADMISSIBLE':e.append('[SEED-C] admissibility verdict invalid')
 if len(a.get('alternative_structures',[]))<3:e.append('[SEED-C] alternatives <3')
 if a.get('specificity_violations')!=[]:e.append('[SEED-C] specificity violations')
 if sha(sp)!=m.get('content_sha256'):e.append('[SEED-A] seed SHA mismatch')
 if mode=='EP01_02_BLIND':
  if m.get('downstream_layers_blocked') is not True or m.get('cross_provider_outputs_blocked') is not True or m.get('prior_mode_ref') not in (None,''):e.append('[SEED-C] blind boundary invalid')
 if mode=='FULL_READ' and 'EP01_02_BLIND' not in str(m.get('prior_mode_ref')):e.append('[SEED-C] prior blind missing')
 refs2=m.get('source_file_refs',[]);hm=m.get('source_sha256s',{})
 if sroot is None:h.append('[SEED-B] --source-root required')
 else:
  cache={}
  for ref in refs2:
   z=re.search(r'_(\d{2})(?:\D|$)',Path(ref).stem);ep=int(z.group(1)) if z else 1;q=source(root,sroot,ref,w,ep)
   if not q:e.append(f'[SEED-B] source missing {ref}')
   elif hm.get(ref)!=sha(q):e.append(f'[SEED-B] source SHA mismatch {ref}')
   else:cache[ep]=q.read_text(encoding='utf-8').splitlines()
  for ref in refs:
   z=EV.match(str(ref))
   if not z:e.append('[SEED-B] evidence format');continue
   ep,ln=int(z['ep']),int(z['ln']);q=norm(z['q']);lines=cache.get(ep,[]);lo=max(1,ln-3);hi=min(len(lines),ln+3)
   if ep not in span:e.append('[SEED-B] evidence outside span')
   if lines and not any(q in norm(lines[i-1]) or norm(lines[i-1]) in q for i in range(lo,hi+1)):e.append('[SEED-B] evidence line mismatch')
 if phase=='evaluate':
  pp=root/'derived_seed_prediction'/f'{w}.pred.jsonl';cp=root/'derived_seed_contamination'/f'{w}.contam.json'
  if not pp.exists() or not cp.exists():e.append('[SEED-D] evaluation missing')
  else:
   pr=rjl(pp);co=rj(cp);exact(e,'contamination',co,CONT)
   for x in pr:exact(e,'prediction',x,PRED)
   for md in ('EP01_02_BLIND','FULL_READ'):
    cc=Counter(x.get('indicator') for x in pr if x.get('derivation_mode')==md)
    if set(cc)!=IND or any(v!=1 for v in cc.values()):e.append('[SEED-A] indicators incomplete')
   try:
    total,c=centers(root,w);op,od=opposition(root,w,c);cf,cd=conflict(root,w);te=terminal(root,w);obs={'center_count':len(c),'opposition_persistence':op,'conflict_persist':cf,'ending_direction':te['ending_direction'],'cost_realized':te['cost_realized']}
    count.update(center_count_recomputed=len(c),season_scene_count=total,center_shares={k:round(v,4) for k,v in c.items()},opposition_recomputed=op,opposition_detail=od,conflict_recomputed=cf,conflict_detail=cd,terminal_audit='PASS')
    for x in pr:
     v=obs[x['indicator']]
     if x['observed_value']!=v:e.append(f"[SEED-D] observed_value mismatch {x['derivation_mode']} {x['indicator']}")
     if x['match']!=(x['predicted_value']==v):e.append('[SEED-D] match mismatch')
   except Exception as x:e.append(f'[SEED-D] recompute failed: {x}')
   acc={md:round(sum(x['match'] for x in pr if x['derivation_mode']==md)/5,4) for md in ('EP01_02_BLIND','FULL_READ')};leak=round(acc['FULL_READ']-acc['EP01_02_BLIND'],4)
   if co.get('mode_b_prediction_accuracy')!=acc['EP01_02_BLIND'] or co.get('mode_c_prediction_accuracy')!=acc['FULL_READ'] or co.get('leakage_estimate')!=leak:e.append('[SEED-D] accuracy/leakage mismatch')
   count.update(mode_b_prediction_accuracy=acc['EP01_02_BLIND'],mode_c_prediction_accuracy=acc['FULL_READ'],leakage_estimate=leak)
 count.update(evidence_refs=len(refs),alternative_structures=len(a.get('alternative_structures',[])),compatible_works=len(ids))
 status='FAIL' if e else 'HOLD_SOURCE_REQUIRED' if h else 'PASS';return {'schema':'EXT6_PHASE02_SEED_GATE_REPORT_V1_0_2','work_id':w,'derivation_mode':mode,'phase':phase,'status':status,'errors':e,'holds':h,'warnings':warn,'counts':count},(1 if e else 3 if h else 0)
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--work',required=True);p.add_argument('--mode',required=True,choices=sorted(MODES));p.add_argument('--source-root');p.add_argument('--corpus-index',required=True);p.add_argument('--phase',choices=['seal','evaluate'],default='seal');p.add_argument('--json-out');a=p.parse_args();o,c=run(Path(a.root),a.work,a.mode,Path(a.source_root) if a.source_root else None,Path(a.corpus_index),a.phase);s=json.dumps(o,ensure_ascii=False,indent=2)
 if a.json_out:q=Path(a.json_out);q.parent.mkdir(parents=True,exist_ok=True);q.write_text(s+'\n',encoding='utf-8')
 print(s);sys.exit(c)
if __name__=='__main__':main()
