# -*- coding: utf-8 -*-
"""사용법: python3 merge.py <작품명> <회차2자리>
authored/<작품>_<NN>.part*.json 을 모아 정본 JSONL 의 6개 내용 필드만 교체.
좌표(seq_id/seq_index/member_scene_nos/evidence_refs/source_hashes/by/
info subject·mode·scene_nos/plant kind·thread_id·scene_nos/scene_no) 는 전수 불변 검사.
명제 개수도 씬별로 정확히 일치해야 한다. 하나라도 어긋나면 아무것도 쓰지 않고 종료(1).
출력: rework/<작품>/out/<작품>_<NN>.thick_sequence.jsonl
"""
import json, io, sys, os, glob, copy
BASE='/sessions/compassionate-eager-lovelace/mnt/claude'
W,EP=sys.argv[1],sys.argv[2]
SRC='%s/db/seqcard_ko/reinforcement_v1/thick_sequence/%s/%s_%s.thick_sequence.jsonl'%(BASE,W,W,EP)
OUT='%s/rework/%s/out/%s_%s.thick_sequence.jsonl'%(BASE,W,W,EP)
A={}
for p in sorted(glob.glob('%s/rework/authored/%s_%s.part*.json'%(BASE,W,EP))):
    A.update(json.load(io.open(p,encoding='utf-8')))
recs=[json.loads(l) for l in io.open(SRC,encoding='utf-8') if l.strip()]
errs=[];out=[]
for r in recs:
    sid=r['seq_id']
    if sid not in A: errs.append('MISSING authored %s'%sid); out.append(r); continue
    a=A[sid]; n=copy.deepcopy(r)
    n['event']=a['event']
    if len(a['cast'])!=len(r.get('cast',[])): errs.append('cast len %s %d!=%d'%(sid,len(a['cast']),len(r.get('cast',[]))))
    else:
        for i,c in enumerate(n['cast']): c['desire_or_function']=a['cast'][i]
    ish=n.get('info_shift',[])
    if len(a['info_before'])!=len(ish) or len(a['info_after'])!=len(ish):
        errs.append('info len %s %d/%d!=%d'%(sid,len(a['info_before']),len(a['info_after']),len(ish)))
    else:
        for i,x in enumerate(ish): x['before']=a['info_before'][i]; x['after']=a['info_after'][i]
    pp=n.get('plant_payoff',[])
    if len(a['plant'])!=len(pp): errs.append('plant len %s %d!=%d'%(sid,len(a['plant']),len(pp)))
    else:
        for i,x in enumerate(pp): x['statement']=a['plant'][i]
    for sn in n.get('scene_notes',[]):
        k=str(sn['scene_no'])
        if k not in a['props']: errs.append('prop missing %s scene %s'%(sid,k)); continue
        if len(a['props'][k])!=len(sn['functional_propositions']):
            errs.append('prop count %s s%s %d!=%d'%(sid,k,len(a['props'][k]),len(sn['functional_propositions'])))
        else: sn['functional_propositions']=a['props'][k]
    out.append(n)
KEYS=['schema','work_id','episode_no','seq_id','seq_index','member_scene_nos','evidence_refs','source_hashes','by']
J=lambda x: json.dumps(x,ensure_ascii=False)
for o,r in zip(out,recs):
    for k in KEYS:
        if J(o.get(k))!=J(r.get(k)): errs.append('COORD %s %s'%(r['seq_id'],k))
    for i,(x,y) in enumerate(zip(o.get('cast',[]),r.get('cast',[]))):
        for k in ('character','participation','evidence_refs'):
            if J(x.get(k))!=J(y.get(k)): errs.append('COORD cast %s %d %s'%(r['seq_id'],i,k))
    for i,(x,y) in enumerate(zip(o.get('info_shift',[]),r.get('info_shift',[]))):
        for k in ('subject','mode','scene_nos','evidence_refs'):
            if J(x.get(k))!=J(y.get(k)): errs.append('COORD info %s %d %s'%(r['seq_id'],i,k))
    for i,(x,y) in enumerate(zip(o.get('plant_payoff',[]),r.get('plant_payoff',[]))):
        for k in ('kind','thread_id','scene_nos','existing_refs','evidence_refs'):
            if J(x.get(k))!=J(y.get(k)): errs.append('COORD plant %s %d %s'%(r['seq_id'],i,k))
    for i,(x,y) in enumerate(zip(o.get('scene_notes',[]),r.get('scene_notes',[]))):
        for k in ('scene_no','evidence_refs'):
            if J(x.get(k))!=J(y.get(k)): errs.append('COORD sn %s %d %s'%(r['seq_id'],i,k))
if errs:
    print('ERRORS %d'%len(errs))
    for e in errs[:40]: print(' ',e)
    sys.exit(1)
os.makedirs(os.path.dirname(OUT),exist_ok=True)
with io.open(OUT,'w',encoding='utf-8') as f:
    for o in out: f.write(json.dumps(o,ensure_ascii=False)+'\n')
print('OK %s seq=%d -> %s'%(W+'_'+EP,len(out),OUT))
