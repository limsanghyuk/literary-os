from pathlib import Path
import json,re,hashlib

ROOT=Path('handoff/20260911')
PATCH=json.loads((ROOT/'P07_I4K5R2_ATTEMPT2_SCENE_LOCAL_EXPANSION_PATCH_R1_20260911.json').read_text(encoding='utf-8'))
ARMS={
 'CONTROL':('P07_I4K5R2_CONTROL_WHOLE_EPISODE_PROVISIONAL_ATTEMPT1_20260911.txt','P07_I4K5R2_CONTROL_WHOLE_EPISODE_PROVISIONAL_ATTEMPT2_20260911.txt','control'),
 'TREATMENT':('P07_I4K5R2_TREATMENT_WHOLE_EPISODE_PROVISIONAL_ATTEMPT1_20260911.txt','P07_I4K5R2_TREATMENT_WHOLE_EPISODE_PROVISIONAL_ATTEMPT2_20260911.txt','treatment')
}
FORBIDDEN=['Event Ecology','Control','Treatment','engine','planner','thread','threshold']

def assemble(src, additions, arm):
    text=src.replace('ATTEMPT_1','ATTEMPT_2',1)
    text=text.replace('[END PROVISIONAL ATTEMPT 1', '[END PROVISIONAL ATTEMPT 2')
    # Insert each sealed scene-local expansion immediately before the next scene marker / END marker.
    for n in range(1,51):
        start=text.index(f'S#{n}.')
        if n<50:
            end=text.index(f'S#{n+1}.',start)
        else:
            end=text.index('[END PROVISIONAL',start)
        ins='\n'+additions[str(n)].strip()+'\n\n'
        text=text[:end].rstrip()+ins+text[end:]
    return text

def body(text):
    return text[text.index('S#1.'):text.index('[END PROVISIONAL')].rstrip('\n')

def metrics(path):
    raw=path.read_bytes(); text=raw.decode('utf-8'); b=body(text)
    ids=[int(x) for x in re.findall(r'(?m)^S#(\d+)\.',b)]
    lines=[x.strip() for x in b.splitlines() if len(x.strip())>=80]
    seen=set(); dup=[]
    for x in lines:
        if x in seen and x not in dup: dup.append(x)
        seen.add(x)
    return {
      'file_sha256':hashlib.sha256(raw).hexdigest(),
      'file_bytes':len(raw),
      'body_chars':len(b),
      'scene_count':len(ids),
      'scene_ids':ids,
      'forbidden':{tok:b.count(tok) for tok in FORBIDDEN},
      'CH_id_count':len(re.findall(r'\bCH\d+\b',b)),
      'SQ_id_count':len(re.findall(r'\bSQ\d+\b',b)),
      'exact_long_duplicate_line_count':len(dup),
      'duplicate_examples':dup[:3]
    }

rows={}
for arm,(src_name,out_name,key) in ARMS.items():
    src=(ROOT/src_name).read_text(encoding='utf-8')
    out=assemble(src,PATCH[key],arm)
    (ROOT/out_name).write_text(out,encoding='utf-8')
    rows[arm]=metrics(ROOT/out_name)

gap=abs(rows['CONTROL']['body_chars']-rows['TREATMENT']['body_chars'])/max(rows['CONTROL']['body_chars'],rows['TREATMENT']['body_chars'])
res={'attempt':2,'relative_gap':gap,'rows':rows}
res['mechanical_scale_structure_hygiene_pass']=(
 rows['CONTROL']['body_chars']>=35000 and rows['TREATMENT']['body_chars']>=35000 and gap<=0.10 and
 rows['CONTROL']['scene_ids']==list(range(1,51)) and rows['TREATMENT']['scene_ids']==list(range(1,51)) and
 all(v==0 for v in rows['TREATMENT']['forbidden'].values()) and rows['TREATMENT']['CH_id_count']==0 and rows['TREATMENT']['SQ_id_count']==0 and rows['TREATMENT']['exact_long_duplicate_line_count']==0
)
(ROOT/'P07_I4K5R2_ATTEMPT2_MECHANICAL_METRICS_R1_20260911.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
print('I4K5R2_ATTEMPT2_METRICS='+json.dumps(res,ensure_ascii=False,sort_keys=True))
