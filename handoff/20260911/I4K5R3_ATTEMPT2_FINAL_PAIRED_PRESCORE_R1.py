from pathlib import Path
import hashlib, json, re, shutil

BASE=Path('handoff/20260911/i4k5r3_attempt2')
SHARED=Path('handoff/20260911/P07_I4K5R3_ATTEMPT2_SHARED_SCENE_CONTEXT_EXPANSION_R1_20260911.json')
PSSB=Path('handoff/20260911/P07_I4K5R3_ATTEMPT2_TREATMENT_PSSB_BINDING_MAP_R1_20260911.json')
OUT=Path('_i4k5r3_a2_final_prescore')
FORBIDDEN=['Event Ecology','PSSB','shared upstream','scene plan','Treatment','Control','threshold','downstream_decision_owner','future_thread_owner']

def H(b): return hashlib.sha256(b).hexdigest()
def get_body(t):
    m=re.search(r'(?m)^S#\d+\.',t)
    if not m: raise RuntimeError('missing scene header')
    e=t.rfind('[END ATTEMPT2')
    if e<0: raise RuntimeError('missing END')
    return t[m.start():e].rstrip('\n')

def mat(label, src, pssb=False):
    shared={int(k):v for k,v in json.loads(SHARED.read_text(encoding='utf-8'))['expansions'].items()}
    binds={int(k):v for k,v in json.loads(PSSB.read_text(encoding='utf-8'))['bindings'].items()} if pssb else {}
    if sorted(shared)!=list(range(1,51)): raise RuntimeError('shared ids')
    if pssb and sorted(binds)!=list(range(1,51)): raise RuntimeError('pssb ids')
    files=sorted(Path(src).glob('*.txt'))
    if len(files)!=10: raise RuntimeError((label,len(files)))
    od=OUT/label.lower(); od.mkdir(parents=True,exist_ok=True)
    bodies=[]; ids=[]; shins=[]; pins=[]; rows=[]
    for p in files:
        t=p.read_text(encoding='utf-8')
        src_ids=[int(x) for x in re.findall(r'(?m)^S#(\d+)\.',get_body(t))]
        ms=list(re.finditer(r'(?m)^S#(\d+)\.[^\n]*\n',t))
        for m in reversed(ms):
            sid=int(m.group(1)); pos=m.end()
            if t[pos:pos+1]=='\n': pos+=1
            ins=shared[sid]+'\n\n'; shins.append(sid)
            if pssb:
                ins+=binds[sid]+'\n\n'; pins.append(sid)
            t=t[:pos]+ins+t[pos:]
        q=od/p.name; q.write_text(t,encoding='utf-8')
        b=get_body(t); bodies.append(b); ids.extend(src_ids)
        rows.append({'name':p.name,'source_sha256':H(p.read_bytes()),'materialized_sha256':H(q.read_bytes()),'body_chars':len(b),'scene_ids':src_ids})
    logical='\n\n'.join(bodies)
    lines=[x.strip() for x in logical.splitlines() if x.strip()]
    long=[x for x in lines if len(x)>=40]; cc={}
    for x in long: cc[x]=cc.get(x,0)+1
    dups={x:n for x,n in cc.items() if n>1}
    return {
      'segments':rows,'segment_count':len(files),'scene_count':len(ids),'scene_ids':ids,
      'scene_ids_exact_1_50':ids==list(range(1,51)),
      'shared_insertions':len(shins),'shared_ids_exact':sorted(shins)==list(range(1,51)),
      'pssb_insertions':len(pins),'pssb_ids_exact':(sorted(pins)==list(range(1,51))) if pssb else True,
      'body_chars':sum(map(len,bodies)),'logical_join_sha256':H(logical.encode()),
      'forbidden_internal_meta_literals':{x:sum(b.count(x) for b in bodies) for x in FORBIDDEN},
      'CH_id_count':sum(len(re.findall(r'\bCH\d+\b',b)) for b in bodies),
      'SQ_id_count':sum(len(re.findall(r'\bSQ\d+\b',b)) for b in bodies),
      'exact_long_duplicate_line_count':len(dups),'duplicate_examples':list(dups.items())[:20]
    }

if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir()
S=json.loads(SHARED.read_text(encoding='utf-8')); P=json.loads(PSSB.read_text(encoding='utf-8'))
R={'CONTROL':mat('CONTROL',BASE/'control_final',False),'TREATMENT':mat('TREATMENT',BASE/'treatment_final',True)}
gap=abs(R['CONTROL']['body_chars']-R['TREATMENT']['body_chars'])/max(R['CONTROL']['body_chars'],R['TREATMENT']['body_chars'])
metrics={
 'measurement_class':'FINAL_ATTEMPT2_PRESCORE_MECHANICAL_NO_QUALITY',
 'shared_context_chars':sum(len(S['expansions'][str(i)]) for i in range(1,51)),
 'treatment_pssb_binding_chars':sum(len(P['bindings'][str(i)]) for i in range(1,51)),
 'shared_context_file_sha256':H(SHARED.read_bytes()),'pssb_map_file_sha256':H(PSSB.read_bytes()),
 'rows':R,'relative_gap':gap,'relative_gap_percent':gap*100,
 'gates':{
  'control_ge_35000':R['CONTROL']['body_chars']>=35000,
  'treatment_ge_35000':R['TREATMENT']['body_chars']>=35000,
  'gap_le_0_10':gap<=0.10,
  'control_10_segments':R['CONTROL']['segment_count']==10,'treatment_10_segments':R['TREATMENT']['segment_count']==10,
  'control_scene_ids_exact':R['CONTROL']['scene_ids_exact_1_50'],'treatment_scene_ids_exact':R['TREATMENT']['scene_ids_exact_1_50'],
  'control_shared_50':R['CONTROL']['shared_insertions']==50 and R['CONTROL']['shared_ids_exact'],
  'treatment_shared_50':R['TREATMENT']['shared_insertions']==50 and R['TREATMENT']['shared_ids_exact'],
  'treatment_pssb_50':R['TREATMENT']['pssb_insertions']==50 and R['TREATMENT']['pssb_ids_exact'],
  'treatment_forbidden_zero':sum(R['TREATMENT']['forbidden_internal_meta_literals'].values())==0,
  'treatment_CH_SQ_zero':R['TREATMENT']['CH_id_count']==0 and R['TREATMENT']['SQ_id_count']==0,
  'treatment_exact_long_duplicate_zero':R['TREATMENT']['exact_long_duplicate_line_count']==0
 }
}
(OUT/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(metrics,ensure_ascii=False,sort_keys=True))