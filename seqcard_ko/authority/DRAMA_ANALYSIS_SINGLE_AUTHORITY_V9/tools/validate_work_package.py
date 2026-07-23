#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from collections import Counter
from pathlib import Path
CORE=set("ESTABLISH ORACLE INTRO BOND CONFLICT REVERSAL LOSS PUNISH REVELATION REUNION RELIEF ROMANCE PERIL RESCUE DESIRE HOOK".split())
TURN_MAP={"RISE":"RISE","BOND":"RISE","PUNISH":"RISE","FALL":"FALL","LOSS":"FALL","REVEAL":"REVEAL","ORACLE":"REVEAL","REVERSAL":"REVEAL","STALL":"STALL","HOOK":"STALL","CONFLICT":"STALL"}
def load_json(p): return json.loads(p.read_text(encoding='utf-8'))
def load_jsonl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def exact_keys(obj, keys, label, errors):
    if set(obj)!=set(keys): errors.append(f'{label}: exact keys mismatch {sorted(set(obj)^set(keys))}')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--authority-root',default=None); args=ap.parse_args()
    root=Path(args.root); errors=[]; warnings=[]; all_scenes={}
    scfiles=sorted((root/'authored').glob('*.seqcard.jsonl'))
    if not scfiles: errors.append('no SceneCard files')
    for p in scfiles:
        rows=load_jsonl(p); wid=rows[0]['work_id'] if rows else p.stem
        exact=["work_id","scene_no","heading","title","intent_gist","core","core2","skin","by"]
        for j,r in enumerate(rows,1):
            exact_keys(r,exact,f'{p.name}:{j}',errors)
            if r.get('scene_no')!=j: errors.append(f'{p.name}: ordinal {r.get("scene_no")} != {j}')
            if r.get('core') not in CORE or (r.get('core2') is not None and r.get('core2') not in CORE): errors.append(f'{p.name}:{j} core')
        if len({r['title'] for r in rows})!=len(rows): errors.append(f'{p.name}: duplicate title')
        if len({r['intent_gist'] for r in rows})!=len(rows): errors.append(f'{p.name}: duplicate intent')
        all_scenes[wid]={r['scene_no']:r for r in rows}
        meta=p.with_name(p.name.replace('.seqcard.jsonl','.episode_meta.json'))
        if not meta.exists(): errors.append(f'{p.name}: missing episode meta')
        else:
            m=load_json(meta); exact_keys(m,["work_id","scene_count","core_dist","episode_function","by"],meta.name,errors)
            if m.get('scene_count')!=len(rows): errors.append(f'{meta.name}: scene_count')
            dist=Counter()
            for r in rows:
                dist[r['core']]+=1
                if r['core2']: dist[r['core2']]+=1
            if dict(dist)!=m.get('core_dist'): errors.append(f'{meta.name}: core_dist')
    for p in sorted((root/'authored_seq').glob('*.seqblueprint.jsonl')):
        rows=load_jsonl(p)
        if not rows: errors.append(f'{p.name}: empty'); continue
        wid=rows[0]['work_id']; scenes=all_scenes.get(wid,{}); seen=[]; rt=0
        exact=["seq_id","work_id","episode_no","seq_index","member_scene_nos","scene_span","scene_budget","sequence_intent","goal","obstacle","value_shift","turn_type","turn_class","core_mix","pov_char","place_cluster","runtime_share","by"]
        for j,r in enumerate(rows,1):
            exact_keys(r,exact,f'{p.name}:{j}',errors); ms=r['member_scene_nos']; seen+=ms; rt+=r['runtime_share']
            if r['seq_index']!=j: errors.append(f'{p.name}: seq index')
            if ms!=list(range(ms[0],ms[-1]+1)): errors.append(f'{p.name}:{j} non-contiguous')
            if r['scene_span']!=[ms[0],ms[-1]] or r['scene_budget']!=len(ms): errors.append(f'{p.name}:{j} span/budget')
            if TURN_MAP.get(r['turn_type'])!=r['turn_class']: errors.append(f'{p.name}:{j} turn map')
            actual=set()
            for n in ms:
                if n not in scenes: errors.append(f'{p.name}:{j} missing scene {n}'); continue
                actual.add(scenes[n]['core']);
                if scenes[n]['core2']: actual.add(scenes[n]['core2'])
            if not set(r['core_mix']).issubset(actual): errors.append(f'{p.name}:{j} core_mix')
        if sorted(seen)!=list(range(1,len(scenes)+1)) or len(seen)!=len(set(seen)): errors.append(f'{p.name}: coverage/partition')
        if not math.isclose(rt,1.0,abs_tol=1e-6): errors.append(f'{p.name}: runtime {rt}')
        if len(rows)/max(1,len(scenes))<0.11: errors.append(f'{p.name}: density below 0.11')
    for p in sorted((root/'authored_arc').glob('*.episodearc.json')):
        r=load_json(p); wid=r['work_id']; scenes=all_scenes.get(wid,{})
        seqp=root/'authored_seq'/p.name.replace('.episodearc.json','.seqblueprint.jsonl'); seqs=load_jsonl(seqp) if seqp.exists() else []
        exact_keys(r,["work_id","episode_no","scene_count","sequence_count","dramatic_question","act_structure","entry_state","exit_state","turning_point","central_conflict_axis","episode_function","core_dist","by"],p.name,errors)
        if r['scene_count']!=len(scenes) or r['sequence_count']!=len(seqs): errors.append(f'{p.name}: counts')
        cover=[]
        for a in r['act_structure']: cover+=list(range(a['seq_span'][0],a['seq_span'][1]+1))
        if cover!=list(range(1,len(seqs)+1)): errors.append(f'{p.name}: act tiling')
        if r['turning_point']['seq_index'] not in range(1,len(seqs)+1): errors.append(f'{p.name}: turning FK')
    for sub,suffix in [('authored_chararc','.chararc.jsonl'),('authored_relarc','.relarc.jsonl')]:
        for p in sorted((root/sub).glob('*'+suffix)):
            for r in load_jsonl(p):
                if r['work_id'] not in all_scenes or r['trigger_scene_no'] not in all_scenes[r['work_id']]: errors.append(f'{p.name}: trigger FK')
    for p in sorted((root/'authored_edges').glob('*.local_edges.jsonl')):
        for r in load_jsonl(p):
            scenes=all_scenes.get(r['work_id'],{})
            if r['src_episode_no']!=r['tgt_episode_no'] or r['gap_episodes']!=0 or r['edge_type']!='causal': errors.append(f'{p.name}:{r["edge_id"]} local contract')
            if r['src_scene_no'] not in scenes or r['tgt_scene_no'] not in scenes: errors.append(f'{p.name}:{r["edge_id"]} scene FK')
            elif r['label']!=scenes[r['tgt_scene_no']]['core']: errors.append(f'{p.name}:{r["edge_id"]} target core')
    for p in sorted((root/'authored_edges').glob('*.payoff_candidates.jsonl')):
        for r in load_jsonl(p):
            if r['work_id'] not in all_scenes or r['scene_no'] not in all_scenes[r['work_id']]: errors.append(f'{p.name}:{r["candidate_id"]} FK')
    audits=list((root/'semantic_audits').glob('*.json')) if (root/'semantic_audits').exists() else []
    for p in audits:
        a=load_json(p)
        if not a.get('source_reopened'): errors.append(f'{p.name}: source not reopened')
        if a.get('author_run_id')==a.get('audit_run_id'): errors.append(f'{p.name}: author/audit run identical')
    verdict='PASS' if not errors else 'FAIL'
    print(json.dumps({'schema':'DRAMA_VALIDATION_REPORT_V9','errors':errors,'warnings':warnings,'counts':{'episodes':len(scfiles),'scenes':sum(len(x) for x in all_scenes.values())},'verdict':verdict},ensure_ascii=False,indent=2))
    return 0 if verdict=='PASS' else 1
if __name__=='__main__': raise SystemExit(main())
