#!/usr/bin/env python3
"""EXT6 V1.2 Phase02 DesignSeed gate — same-version corrected 2026-08-01.
Hard gates: SEED-A/B/C. Evaluation adds deterministic SEED-D center_count,
accuracy, leakage checks. Exit 0 PASS, 1 FAIL, 3 HOLD_SOURCE_REQUIRED.
"""
from __future__ import annotations
import argparse, hashlib, json, re, unicodedata
from pathlib import Path
from collections import Counter, defaultdict

WORK_MODES={'PLAN_DOCUMENT','EP01_02_BLIND','FULL_READ'}
END={'ACHIEVE','ACHIEVE_WITH_COST','FAIL','FAIL_BUT_TRANSFORM','REFUSE','AMBIGUOUS'}
SCOPES={'SOCIAL','INSTITUTIONAL','PHYSICAL','SUPERNATURAL','ECONOMIC','RELATIONAL','PROFESSIONAL','LEGAL','CULTURAL','OTHER'}
COST_TYPES={'IDENTITY','RELATIONSHIP','STATUS','SAFETY','MORAL','MATERIAL','TIME','LIFE','MIXED','NONE','AMBIGUOUS'}
COST_BEARERS={'PROTAGONIST','ALLY','RELATIONSHIP','COMMUNITY','ANTAGONISTIC_FORCE','MULTIPLE','NONE','AMBIGUOUS'}
INDICATORS={'center_count','opposition_persistence','conflict_persist','ending_direction','cost_realized'}
PRESENT_MODES={'ONSCREEN','VOICE_ONLY','PHONE_OR_REMOTE','ARCHIVAL_OR_MEMORY'}
SEED_KEYS=set('work_id derivation_mode read_span evidenced_initial_configuration evidenced_world_constraints evidenced_opening_disturbance judged_logline judged_central_lack judged_governing_question judged_central_opposition_axis judged_ending_direction judged_cost_structure contract_version by'.split())
ADM_KEYS=set('work_id derivation_mode compatible_work_ids compatibility_count alternative_structures specificity_violations verdict'.split())
RUN_KEYS=set('work_id derivation_mode read_span run_id provider model_id source_file_refs source_sha256s downstream_layers_blocked downstream_blocklist cross_provider_outputs_blocked prior_mode_ref sealed_at content_sha256 by'.split())
PRED_KEYS=set('work_id derivation_mode indicator predicted_value observed_value observation_source match corpus_prior by'.split())
CONT_KEYS=set('work_id mode_b_ref mode_c_ref field_level_diff diverged_fields mode_b_prediction_accuracy mode_c_prediction_accuracy leakage_estimate'.split())
NESTED={'initial':set('character_key initial_position initial_relation_axis evidence_ref'.split()),'constraint':set('rule scope evidence_ref'.split()),'disturbance':set('summary scene_no evidence_ref'.split()),'cost':set('cost_type cost_bearer cost_summary'.split()),'alt':set('sketch divergence_point'.split())}
EV_RE=re.compile(r'^EP(?P<ep>\d{2})-S(?P<scene>\d+)\s+L(?P<line>\d+)\s+(?P<quote>.+)$')
NUM_LEAK=re.compile(r'(?:EP\s*\d+|\d+\s*(?:회|화|씬|장면)|S\s*\d+)',re.I)
BAD={'TODO','TBD','PLACEHOLDER','???','N/A','NULL','XXX','미상','보류'}

def norm(s): return re.sub(r'\s+','',unicodedata.normalize('NFKC',str(s))).lower()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def readj(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def readjl(p): return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines() if x.strip()]
def exact(errors,label,obj,keys):
    if not isinstance(obj,dict): errors.append(f'[SEED-A] {label} not object'); return False
    if set(obj)!=keys: errors.append(f'[SEED-A] {label} keyset missing={sorted(keys-set(obj))} extra={sorted(set(obj)-keys)}'); return False
    return True
def require_text(errors,label,v):
    if not isinstance(v,str) or not v.strip() or v.strip().upper() in BAD: errors.append(f'[SEED-A] {label} empty/placeholder')
def locate_source(source_root,root,ref,work,ep):
    cs=[source_root/ref,source_root/'original_extracted'/work/f'{work}_{ep:02d}.txt',root/'original_extracted'/work/f'{work}_{ep:02d}.txt']
    return next((p for p in cs if p.exists()),None)
def corpus_from_index(path):
    o=readj(path); works=o.get('works') if isinstance(o,dict) else None
    if not isinstance(works,list): raise ValueError('corpus index missing works list')
    out=set()
    for x in works:
        if isinstance(x,dict) and isinstance(x.get('work_id'),str): out.add(x['work_id'])
        elif isinstance(x,str): out.add(x)
    if not out: raise ValueError('corpus index has no work ids')
    return out

def recompute_center(root,work):
    scene_keys=set()
    for p in (root/'authored').glob(f'{work}_*.seqcard.jsonl'):
        m=re.match(re.escape(work)+r'_(\d{2})\.seqcard\.jsonl$',p.name)
        if not m: continue
        ep=int(m.group(1))
        for r in readjl(p): scene_keys.add((ep,int(r['scene_no'])))
    present=defaultdict(set)
    for p in (root/'authored_cast').glob(f'{work}_*.cast.jsonl'):
        for r in readjl(p):
            if r.get('presence_mode') in PRESENT_MODES:
                present[r['character_key']].add((int(r['episode_no']),int(r['scene_no'])))
    if not scene_keys: raise ValueError('no SceneCards for center_count')
    shares={k:len(v)/len(scene_keys) for k,v in present.items()}
    centers={k:s for k,s in shares.items() if s>=.20}
    return len(scene_keys),shares,centers

def expected_verdict(n): return 'TOO_SPECIFIC' if n==0 else 'ADMISSIBLE' if n<=9 else 'REVIEW' if n<=29 else 'TOO_VAGUE'

def recompute_opposition(root,work,centers):
    bridge={r['character_key']:r['canonical_name'] for r in readjl(root/'authored_bridge'/f'{work}.bridge.jsonl')}
    top=[k for k,_ in sorted(centers.items(),key=lambda kv:-kv[1])[:2]]
    names={bridge.get(k,k.split(':')[-1]) for k in top}
    states=[];episodes=set()
    for p in sorted((root/'authored_relarc').glob(f'{work}_*.relarc.jsonl')):
        m=re.match(re.escape(work)+r'_(\d{2})\.relarc\.jsonl$',p.name)
        if not m: continue
        ep=int(m.group(1)); rr=[r for r in readjl(p) if {r.get('char_a'),r.get('char_b')}==names]
        if rr: episodes.add(ep);states.extend((ep,r.get('relation_state')) for r in rr)
    total=len(list((root/'authored').glob(f'{work}_*.seqcard.jsonl')));ratio=len(episodes)/total if total else 0
    observed='HIGH' if ratio>=.75 and states and states[0][1]!=states[-1][1] else 'LOW'
    return observed,{'center_pair':sorted(names),'episode_coverage':len(episodes),'episodes_total':total,'coverage_ratio':round(ratio,4),'first_state':states[0][1] if states else None,'last_state':states[-1][1] if states else None}

def recompute_conflict(root,work):
    import math
    fa=readj(root/'authored'/f'{work}_full_series_arc.json');n=int(fa['episodes_total']);ss=fa.get('season_structure',[])
    first=min(int(x['episode_span'][0]) for x in ss);last=max(int(x['episode_span'][1]) for x in ss)
    observed='SEASON_LONG' if first<=max(2,math.ceil(n*.25)) and last==n else 'LIMITED'
    return observed,{'first_episode':first,'last_episode':last,'episodes_total':n}

def verify_terminal_audit(root,work):
    p=root/'validation'/'phase02_indicator_evidence'/f'{work}.indicator_evidence.json'
    if not p.exists(): raise ValueError('terminal indicator evidence audit missing')
    a=readj(p);corpus=[]
    for src in a.get('sources',[]):
        sp=root.parent/src['path'] if str(src['path']).startswith('seqcard_ko/') else root/src['path']
        if not sp.exists(): raise ValueError(f'audit source missing {src["path"]}')
        if sha(sp)!=src['sha256']: raise ValueError(f'audit source SHA mismatch {src["path"]}')
        if sp.suffix=='.jsonl': corpus.extend(json.dumps(r,ensure_ascii=False) for r in readjl(sp))
        else: corpus.append(sp.read_text(encoding='utf-8'))
    joined='\n'.join(corpus)
    for phrase in a.get('decision',{}).get('support_phrases',[]):
        if phrase not in joined: raise ValueError(f'audit support phrase missing: {phrase}')
    if a.get('status')!='PASS': raise ValueError('terminal indicator audit not PASS')
    return a

def run(root,work,mode,source_root,phase,corpus_index):
    errors=[];holds=[];warnings=[];counts={}
    try: works=corpus_from_index(corpus_index)
    except Exception as e: works=set();holds.append(f'[SEED-A] corpus index unavailable: {e}')
    seed_p=root/'advisory_seed'/f'{work}.{mode}.seed.json';adm_p=root/'advisory_seed_admissibility'/f'{work}.{mode}.adm.json';run_p=root/'advisory_seed_runs'/f'{work}.{mode}.run.json'
    missing=[str(p) for p in (seed_p,adm_p,run_p) if not p.exists()]
    if missing: return {'schema':'EXT6_PHASE02_SEED_GATE_REPORT_V1_0_1','work_id':work,'derivation_mode':mode,'phase':phase,'status':'FAIL','errors':['missing '+x for x in missing],'holds':holds,'warnings':[],'counts':{}},1
    seed,adm,manifest=readj(seed_p),readj(adm_p),readj(run_p)
    exact(errors,'seed',seed,SEED_KEYS);exact(errors,'admissibility',adm,ADM_KEYS);exact(errors,'run',manifest,RUN_KEYS)
    if any(x.get('work_id')!=work for x in (seed,adm,manifest)): errors.append('[SEED-A] work grain mismatch')
    if any(x.get('derivation_mode')!=mode for x in (seed,adm,manifest)): errors.append('[SEED-A] mode grain mismatch')
    span=seed.get('read_span')
    if not isinstance(span,list) or span!=sorted(set(span)) or not all(isinstance(x,int) and x>0 for x in span): errors.append('[SEED-A] read_span invalid');span=[]
    if mode=='EP01_02_BLIND' and span!=[1,2]: errors.append('[SEED-A] blind span must [1,2]')
    if manifest.get('read_span')!=span: errors.append('[SEED-A] manifest span mismatch')
    bp=root/'authored_bridge'/f'{work}.bridge.jsonl';bridge=readjl(bp) if bp.exists() else [];bkeys={r.get('character_key') for r in bridge};scenes={}
    for ep in span:
        p=root/'authored'/f'{work}_{ep:02d}.seqcard.jsonl'
        if p.exists(): scenes[ep]={int(r['scene_no']) for r in readjl(p)}
    refs=[];init=seed.get('evidenced_initial_configuration')
    if not isinstance(init,list) or not init: errors.append('[SEED-A] initial configuration empty')
    else:
        for i,x in enumerate(init):
            if exact(errors,f'initial[{i}]',x,NESTED['initial']):
                require_text(errors,f'initial[{i}].character_key',x['character_key']);require_text(errors,f'initial[{i}].position',x['initial_position']);require_text(errors,f'initial[{i}].axis',x['initial_relation_axis'])
                if bkeys and x['character_key'] not in bkeys: errors.append(f'[SEED-A] bridge FK missing {x["character_key"]}')
                refs.append(x['evidence_ref'])
    cons=seed.get('evidenced_world_constraints')
    if not isinstance(cons,list) or not cons: errors.append('[SEED-A] constraints empty')
    else:
        for i,x in enumerate(cons):
            if exact(errors,f'constraint[{i}]',x,NESTED['constraint']):
                require_text(errors,f'constraint[{i}].rule',x['rule'])
                if x['scope'] not in SCOPES: errors.append(f'[SEED-A] invalid scope {x["scope"]}')
                refs.append(x['evidence_ref'])
    dist=seed.get('evidenced_opening_disturbance')
    if exact(errors,'opening disturbance',dist,NESTED['disturbance']):
        require_text(errors,'disturbance.summary',dist['summary'])
        if not isinstance(dist['scene_no'],int) or dist['scene_no']<1: errors.append('[SEED-A] disturbance.scene_no invalid')
        refs.append(dist['evidence_ref'])
    for k in ('judged_logline','judged_central_lack','judged_governing_question','judged_central_opposition_axis','contract_version','by'): require_text(errors,k,seed.get(k))
    if seed.get('judged_ending_direction') not in END: errors.append('[SEED-A] invalid ending direction')
    cost=seed.get('judged_cost_structure')
    if exact(errors,'cost',cost,NESTED['cost']):
        if cost['cost_type'] not in COST_TYPES: errors.append('[SEED-A] invalid cost_type')
        if cost['cost_bearer'] not in COST_BEARERS: errors.append('[SEED-A] invalid cost_bearer')
        require_text(errors,'cost_summary',cost['cost_summary'])
    judged=' '.join(str(seed.get(k,'')) for k in ('judged_logline','judged_central_lack','judged_governing_question','judged_central_opposition_axis','judged_cost_structure'))
    if NUM_LEAK.search(judged): errors.append('[SEED-C] numbered structure leakage')
    if 'evidence_ref' in judged: errors.append('[SEED-B] evidence wrapper in judged block')
    nj=norm(judged)
    for r in bridge:
        n=norm(r.get('canonical_name',''))
        if len(n)>=2 and n in nj: errors.append(f'[SEED-C] proper name leakage {r.get("canonical_name")}');break
    ids=adm.get('compatible_work_ids')
    if not isinstance(ids,list) or len(ids)!=len(set(ids)): errors.append('[SEED-A] compatible_work_ids invalid');ids=[]
    else:
        if work in ids: errors.append('[SEED-C] compatible_work_ids contains self')
        if adm.get('compatibility_count')!=len(ids): errors.append('[SEED-A] compatibility_count mismatch')
        if works:
            miss=set(ids)-works
            if miss: errors.append(f'[SEED-A] corpus IDs missing {sorted(miss)}')
        exp=expected_verdict(len(ids))
        if adm.get('verdict')!=exp: errors.append(f'[SEED-C] verdict {adm.get("verdict")} expected {exp}')
        if adm.get('verdict')!='ADMISSIBLE': errors.append('[SEED-C] seal requires ADMISSIBLE')
    alts=adm.get('alternative_structures')
    if not isinstance(alts,list) or len(alts)<3: errors.append('[SEED-C] alternative structures <3')
    else:
        for i,x in enumerate(alts):
            if exact(errors,f'alternative[{i}]',x,NESTED['alt']): require_text(errors,f'alternative[{i}].sketch',x['sketch']);require_text(errors,f'alternative[{i}].divergence_point',x['divergence_point'])
    if adm.get('specificity_violations')!=[]: errors.append('[SEED-C] specificity violations not empty')
    if sha(seed_p)!=manifest.get('content_sha256'): errors.append('[SEED-A] seed content SHA mismatch')
    src_refs=manifest.get('source_file_refs');src_hash=manifest.get('source_sha256s')
    if not isinstance(src_refs,list) or not isinstance(src_hash,dict) or set(src_refs)!=set(src_hash): errors.append('[SEED-A] source hash map invalid');src_refs=[];src_hash={}
    if mode=='EP01_02_BLIND':
        if manifest.get('downstream_layers_blocked') is not True: errors.append('[SEED-C] downstream block false')
        if manifest.get('cross_provider_outputs_blocked') is not True: errors.append('[SEED-C] provider block false')
        block=' '.join(map(str,manifest.get('downstream_blocklist',[]))).lower()
        for token in ('characterarc','relationshiparc','fullseriesarc','stage04','seed full_read'):
            if token not in block: errors.append(f'[SEED-C] blocklist missing {token}')
        if manifest.get('prior_mode_ref') not in (None,''): errors.append('[SEED-C] blind prior ref must null')
    elif mode=='FULL_READ':
        if 'EP01_02_BLIND' not in str(manifest.get('prior_mode_ref')): errors.append('[SEED-C] full read prior blind ref missing')
        prior=root/str(manifest.get('prior_mode_ref','')).removeprefix('seqcard_ko/')
        if not prior.exists(): errors.append('[SEED-C] prior blind manifest missing')
    if source_root is None: holds.append('[SEED-B] --source-root required')
    else:
        source_cache={}
        for ref in src_refs:
            m=re.search(r'_(\d{2})(?:\D|$)',Path(ref).stem);ep=int(m.group(1)) if m else (span[0] if span else 1);p=locate_source(source_root,root,ref,work,ep)
            if not p: errors.append(f'[SEED-B] source missing {ref}');continue
            if src_hash.get(ref)!=sha(p): errors.append(f'[SEED-B] source SHA mismatch {ref}')
            source_cache[ep]=p.read_text(encoding='utf-8').splitlines()
        for ev in refs:
            mm=EV_RE.match(str(ev).strip())
            if not mm: errors.append(f'[SEED-B] evidence format {ev}');continue
            ep,sc,ln=int(mm['ep']),int(mm['scene']),int(mm['line']);quote=mm['quote']
            if ep not in span: errors.append(f'[SEED-B] evidence outside span EP{ep:02d}')
            if ep in scenes and sc not in scenes[ep]: errors.append(f'[SEED-A] scene FK missing EP{ep:02d}-S{sc}')
            ls=source_cache.get(ep)
            if not ls: continue
            q=norm(quote);lo=max(1,ln-3);hi=min(len(ls),ln+3)
            if len(q)<8: errors.append('[SEED-B] evidence quote too short')
            elif not any(q in norm(ls[i-1]) or norm(ls[i-1]) in q for i in range(lo,hi+1)): errors.append(f'[SEED-B] line mismatch EP{ep:02d} L{ln}')
    if phase=='evaluate':
        pred_p=root/'derived_seed_prediction'/f'{work}.pred.jsonl';cont_p=root/'derived_seed_contamination'/f'{work}.contam.json'
        if not pred_p.exists() or not cont_p.exists(): errors.append('[SEED-D] evaluation records missing')
        else:
            pred=readjl(pred_p)
            for r in pred:
                exact(errors,'prediction',r,PRED_KEYS)
                if r.get('indicator') not in INDICATORS or r.get('by')!='derived_deterministic': errors.append('[SEED-A] prediction invalid')
            for m in ('EP01_02_BLIND','FULL_READ'):
                c=Counter(r.get('indicator') for r in pred if r.get('derivation_mode')==m)
                if set(c)!=INDICATORS or any(v!=1 for v in c.values()): errors.append(f'[SEED-A] prediction indicators incomplete {m}')
            try:
                total,shares,centers=recompute_center(root,work);observed=len(centers);opposition,opdetail=recompute_opposition(root,work,centers);conflict,cfdetail=recompute_conflict(root,work);terminal=verify_terminal_audit(root,work)
                observed_map={'center_count':observed,'opposition_persistence':opposition,'conflict_persist':conflict,'ending_direction':terminal['ending_direction'],'cost_realized':terminal['cost_realized']}
                counts['center_count_recomputed']=observed;counts['season_scene_count']=total;counts['center_shares']={k:round(v,4) for k,v in centers.items()};counts['opposition_recomputed']=opposition;counts['opposition_detail']=opdetail;counts['conflict_recomputed']=conflict;counts['conflict_detail']=cfdetail;counts['terminal_audit']='PASS'
                for r in pred:
                    ind=r.get('indicator');exp=observed_map.get(ind)
                    if r.get('observed_value')!=exp: errors.append(f'[SEED-D] observed_value mismatch {r.get("derivation_mode")} {ind}: got {r.get("observed_value")} expected {exp}')
                    if r.get('match')!=(r.get('predicted_value')==exp): errors.append(f'[SEED-D] prediction match mismatch {r.get("derivation_mode")} {ind}')
            except Exception as e: errors.append(f'[SEED-D] indicator recompute failed: {e}')
            acc={}
            for m in ('EP01_02_BLIND','FULL_READ'):
                rr=[bool(r['match']) for r in pred if r.get('derivation_mode')==m];acc[m]=round(sum(rr)/len(rr),4) if rr else None
            cont=readj(cont_p);exact(errors,'contamination',cont,CONT_KEYS)
            if cont.get('mode_b_prediction_accuracy')!=acc['EP01_02_BLIND']: errors.append('[SEED-D] mode_b accuracy mismatch')
            if cont.get('mode_c_prediction_accuracy')!=acc['FULL_READ']: errors.append('[SEED-D] mode_c accuracy mismatch')
            calc=round(acc['FULL_READ']-acc['EP01_02_BLIND'],4)
            if cont.get('leakage_estimate')!=calc: errors.append('[SEED-D] leakage mismatch')
            counts.update(mode_b_prediction_accuracy=acc['EP01_02_BLIND'],mode_c_prediction_accuracy=acc['FULL_READ'],leakage_estimate=calc)
    counts.update(evidence_refs=len(refs),alternative_structures=len(alts) if isinstance(alts,list) else 0,compatible_works=len(ids))
    status='FAIL' if errors else 'HOLD_SOURCE_REQUIRED' if holds else 'PASS';code=1 if errors else 3 if holds else 0
    return {'schema':'EXT6_PHASE02_SEED_GATE_REPORT_V1_0_1','work_id':work,'derivation_mode':mode,'phase':phase,'status':status,'errors':errors,'holds':holds,'warnings':warnings,'counts':counts},code

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--work',required=True);ap.add_argument('--mode',required=True,choices=sorted(WORK_MODES));ap.add_argument('--source-root');ap.add_argument('--corpus-index',required=True);ap.add_argument('--phase',choices=['seal','evaluate'],default='seal');ap.add_argument('--json-out')
    a=ap.parse_args();report,code=run(Path(a.root),a.work,a.mode,Path(a.source_root) if a.source_root else None,a.phase,Path(a.corpus_index));out=json.dumps(report,ensure_ascii=False,indent=2)
    if a.json_out:
        p=Path(a.json_out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(out+'\n',encoding='utf-8')
    print(out);raise SystemExit(code)
if __name__=='__main__':main()
