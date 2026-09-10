from pathlib import Path
import hashlib,re,json
F={
'CONTROL':Path('handoff/20260911/P07_I4K5R2_CONTROL_WHOLE_EPISODE_PROVISIONAL_ATTEMPT1_20260911.txt'),
'TREATMENT':Path('handoff/20260911/P07_I4K5R2_TREATMENT_WHOLE_EPISODE_PROVISIONAL_ATTEMPT1_20260911.txt')}
def body(t):
    return t[t.index('S#1.'):t.index('[END PROVISIONAL')].rstrip('\n')
def sha(b):return hashlib.sha256(b).hexdigest()
R={}
for arm,p in F.items():
    rb=p.read_bytes(); t=rb.decode(); b=body(t)
    lines=[x.strip() for x in b.splitlines() if x.strip()]
    long=[x for x in lines if len(x)>=40]
    dup={x:long.count(x) for x in set(long) if long.count(x)>1}
    R[arm]={
      'file_sha256':sha(rb),'file_bytes':len(rb),'body_chars':len(b),
      'scene_count':len(re.findall(r'(?m)^S#\d+\.',b)),
      'scene_ids':[int(x) for x in re.findall(r'(?m)^S#(\d+)\.',b)],
      'forbidden':{x:b.count(x) for x in ['Event Ecology','thread','engine','planner','Treatment','Control','threshold']},
      'CH_id_count':len(re.findall(r'\bCH\d+\b',b)),
      'SQ_id_count':len(re.findall(r'\bSQ\d+\b',b)),
      'exact_long_duplicate_line_count':len(dup),
      'duplicate_examples':list(dup.items())[:20]
    }
G=abs(R['CONTROL']['body_chars']-R['TREATMENT']['body_chars'])/max(R['CONTROL']['body_chars'],R['TREATMENT']['body_chars'])
print('I4K5R2_ATTEMPT1_METRICS='+json.dumps({'rows':R,'relative_gap':G},ensure_ascii=False,sort_keys=True))
