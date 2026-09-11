from pathlib import Path
import hashlib, json, re

ROOT = Path('handoff/20260911')
SRC = ROOT / 'i4k5r3_attempt2' / 'control_final'
OUT = Path('_i4k5r3_a2_materialized_control')
EXP_PATH = ROOT / 'P07_I4K5R3_ATTEMPT2_SHARED_SCENE_CONTEXT_EXPANSION_R1_20260911.json'

exp_obj = json.loads(EXP_PATH.read_text(encoding='utf-8'))
exp = {int(k): v for k, v in exp_obj['expansions'].items()}
assert sorted(exp) == list(range(1, 51))
assert exp_obj['shared_between_arms'] is True
assert exp_obj['dialogue_lines'] == 0

files = sorted(SRC.glob('P07_I4K5R3_A2F_CONTROL_SQ*_SC*.txt'))
assert len(files) == 10, len(files)
OUT.mkdir(exist_ok=True)
scene_ids_all=[]
insertions=0
rows=[]
body_total=0
logical=[]

scene_header = re.compile(r'(?m)^S#(\d+)\.[^\n]*\n\n')

def sha(b): return hashlib.sha256(b).hexdigest()

for p in files:
    text=p.read_text(encoding='utf-8')
    ids=[int(x) for x in re.findall(r'(?m)^S#(\d+)\.', text)]
    assert len(ids)==5, (p,ids)
    scene_ids_all.extend(ids)
    pos=0
    parts=[]
    for m in scene_header.finditer(text):
        sid=int(m.group(1))
        parts.append(text[pos:m.end()])
        parts.append(exp[sid] + '\n\n')
        pos=m.end()
        insertions += 1
    parts.append(text[pos:])
    out=''.join(parts)
    outp=OUT / p.name.replace('A2F_CONTROL','A2M_CONTROL')
    outp.write_text(out, encoding='utf-8')
    first=re.search(r'(?m)^S#\d+\.',out)
    end=out.rfind('[END ATTEMPT2 FINAL CONTROL SEQUENCE')
    assert first and end>first.start(), p
    body=out[first.start():end].rstrip('\n')
    body_total += len(body)
    logical.append(body)
    rows.append({'source':p.name,'output':outp.name,'output_sha256':sha(out.encode('utf-8')),'body_chars':len(body),'scene_ids':ids})

assert scene_ids_all==list(range(1,51))
assert insertions==50
logical_text='\n\n'.join(logical)
metrics={
  'class':'READ_ONLY_DETERMINISTIC_SHARED_CONTEXT_MATERIALIZATION_NO_QUALITY',
  'source_commit':'4f8e70ad89c7d533171830adb3e66a7477217c8f',
  'source_dir':str(SRC),
  'expansion_file':str(EXP_PATH),
  'expansion_canonical_sha256':sha(json.dumps(exp_obj['expansions'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')),
  'expansion_total_chars':sum(len(v) for v in exp.values()),
  'segment_count':len(files),
  'scene_count':len(scene_ids_all),
  'scene_ids_exact_1_50':scene_ids_all==list(range(1,51)),
  'expansion_insertions':insertions,
  'body_chars':body_total,
  'body_ge_35000':body_total>=35000,
  'logical_join_sha256':sha(logical_text.encode('utf-8')),
  'rows':rows,
}
Path('_i4k5r3_a2_materialized_control_metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2,sort_keys=True),encoding='utf-8')
print(json.dumps(metrics,ensure_ascii=False,sort_keys=True))
