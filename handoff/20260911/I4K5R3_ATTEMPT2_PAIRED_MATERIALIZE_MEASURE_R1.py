from pathlib import Path
import hashlib, json, re, shutil

BASE = Path('handoff/20260911/i4k5r3_attempt2')
EXP_PATH = Path('handoff/20260911/P07_I4K5R3_ATTEMPT2_SHARED_SCENE_CONTEXT_EXPANSION_R1_20260911.json')
OUT = Path('_i4k5r3_a2_paired')
FORBIDDEN = ['Event Ecology','PSSB','shared upstream','scene plan','Treatment','Control','threshold','downstream_decision_owner','future_thread_owner']

def sha256(b): return hashlib.sha256(b).hexdigest()

def body(text):
    m = re.search(r'(?m)^S#\d+\.', text)
    if not m: raise RuntimeError('missing scene header')
    e = text.rfind('[END ATTEMPT2')
    if e < 0: raise RuntimeError('missing END marker')
    return text[m.start():e].rstrip('\n')

def materialize_arm(label, source_dir):
    files = sorted(Path(source_dir).glob('*.txt'))
    if len(files) != 10: raise RuntimeError(f'{label} expected 10 segments, got {len(files)}')
    exp_doc = json.loads(EXP_PATH.read_text(encoding='utf-8'))
    exps = {int(k):v for k,v in exp_doc['expansions'].items()}
    if sorted(exps) != list(range(1,51)): raise RuntimeError('expansion ids not exact 1..50')
    outdir = OUT / label.lower()
    outdir.mkdir(parents=True, exist_ok=True)
    rows=[]; bodies=[]; scene_ids=[]; inserted=[]
    for p in files:
        text = p.read_text(encoding='utf-8')
        ids = [int(x) for x in re.findall(r'(?m)^S#(\d+)\.', body(text))]
        new = text
        # Replace from high to low offsets so insertions do not disturb earlier locations.
        matches = list(re.finditer(r'(?m)^S#(\d+)\.[^\n]*\n', new))
        for m in reversed(matches):
            sid = int(m.group(1))
            para = exps[sid]
            pos = m.end()
            if new[pos:pos+1] == '\n': pos += 1
            new = new[:pos] + para + '\n\n' + new[pos:]
            inserted.append(sid)
        q = outdir / p.name
        q.write_text(new, encoding='utf-8')
        b = body(new)
        bodies.append(b); scene_ids.extend(ids)
        rows.append({'source':p.name,'source_sha256':sha256(p.read_bytes()),'materialized_sha256':sha256(q.read_bytes()),'materialized_body_chars':len(b),'scene_ids':ids})
    logical='\n\n'.join(bodies)
    lines=[x.strip() for x in logical.splitlines() if x.strip()]
    long=[x for x in lines if len(x)>=40]
    counts={}
    for x in long: counts[x]=counts.get(x,0)+1
    dups={x:n for x,n in counts.items() if n>1}
    return {
      'segment_count':len(files),'scene_count':len(scene_ids),'scene_ids':scene_ids,
      'scene_ids_exact_1_50':scene_ids==list(range(1,51)),
      'insertions':len(inserted),'inserted_ids_exact_1_50':sorted(inserted)==list(range(1,51)),
      'body_chars':sum(len(x) for x in bodies),'logical_join_sha256':sha256(logical.encode()),
      'forbidden_internal_meta_literals':{x:sum(b.count(x) for b in bodies) for x in FORBIDDEN},
      'CH_id_count':sum(len(re.findall(r'\bCH\d+\b',b)) for b in bodies),
      'SQ_id_count':sum(len(re.findall(r'\bSQ\d+\b',b)) for b in bodies),
      'exact_long_duplicate_line_count':len(dups),'duplicate_examples':list(dups.items())[:20],
      'segments':rows
    }

if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir()
exp_bytes = EXP_PATH.read_bytes()
exp_doc=json.loads(exp_bytes.decode('utf-8'))
canon=json.dumps({str(i):exp_doc['expansions'][str(i)] for i in range(1,51)},ensure_ascii=False,separators=(',',':')).encode('utf-8')
R={
 'CONTROL':materialize_arm('CONTROL', BASE/'control_final'),
 'TREATMENT':materialize_arm('TREATMENT', BASE/'treatment_final')
}
gap=abs(R['CONTROL']['body_chars']-R['TREATMENT']['body_chars'])/max(R['CONTROL']['body_chars'],R['TREATMENT']['body_chars'])
metrics={
 'measurement_class':'READ_ONLY_DETERMINISTIC_PRESCORE_NO_QUALITY',
 'shared_expansion_file_sha256':sha256(exp_bytes),
 'shared_expansion_canonical_map_sha256':sha256(canon),
 'shared_expansion_chars':sum(len(exp_doc['expansions'][str(i)]) for i in range(1,51)),
 'rows':R,
 'relative_gap':gap,'relative_gap_percent':gap*100,
 'gates':{
   'control_ge_35000':R['CONTROL']['body_chars']>=35000,
   'treatment_ge_35000':R['TREATMENT']['body_chars']>=35000,
   'gap_le_0_10':gap<=0.10,
   'control_10_segments':R['CONTROL']['segment_count']==10,
   'treatment_10_segments':R['TREATMENT']['segment_count']==10,
   'control_scene_ids_exact':R['CONTROL']['scene_ids_exact_1_50'],
   'treatment_scene_ids_exact':R['TREATMENT']['scene_ids_exact_1_50'],
   'control_insertions_exact':R['CONTROL']['insertions']==50 and R['CONTROL']['inserted_ids_exact_1_50'],
   'treatment_insertions_exact':R['TREATMENT']['insertions']==50 and R['TREATMENT']['inserted_ids_exact_1_50'],
   'treatment_forbidden_zero':sum(R['TREATMENT']['forbidden_internal_meta_literals'].values())==0,
   'treatment_CH_SQ_zero':R['TREATMENT']['CH_id_count']==0 and R['TREATMENT']['SQ_id_count']==0,
   'treatment_exact_long_duplicate_zero':R['TREATMENT']['exact_long_duplicate_line_count']==0
 }
}
(OUT/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(metrics,ensure_ascii=False,sort_keys=True))